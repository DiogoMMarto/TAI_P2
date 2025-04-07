const std = @import("std");
const math = std.math;
const mem = std.mem;
const Allocator = std.mem.Allocator;
const ArrayList = std.ArrayList;

const INITIAL_CAPACITY = 2048;
const LOAD_FACTOR = 0.6;
const GROWTH_FACTOR = 2;

const Args = struct {
    data_path: ?[]const u8,
    sequence_path: ?[]const u8,
    depth: usize = 2,
    alpha: f64 = 1.0,
    top: usize = 20,
};

const DBEntry = struct {
    name: []const u8,
    sequence: []const u8,
    nrc: f64 = 0.0,
};

const Counts = struct {
    a: u32 = 0,
    t: u32 = 0,
    c: u32 = 0,
    g: u32 = 0,
    total: u32 = 0,
};

const HashEntry = struct {
    key: ?[]const u8 = null,
    hash: u32,
    total: u32,
    a: u32,
    t: u32,
    c: u32,
    g: u32,
};

const HashTable = struct {
    entries: []HashEntry,
    key_length: usize,
    capacity: usize,
    size: usize,
    allocator: Allocator,

    fn init(allocator: Allocator, key_length: usize) !*HashTable {
        const entries = try allocator.alloc(HashEntry, INITIAL_CAPACITY);
        for (entries) |*entry| {
            entry.* = .{
                .key = null,
                .hash = 0,
                .total = 0,
                .a = 0,
                .t = 0,
                .c = 0,
                .g = 0,
            };
        }
        const table = try allocator.create(HashTable);
        table.* = .{
            .entries = entries,
            .key_length = key_length,
            .capacity = INITIAL_CAPACITY,
            .size = 0,
            .allocator = allocator,
        };
        return table;
    }

    fn deinit(self: *HashTable) void {
        self.allocator.free(self.entries);
        self.allocator.destroy(self);
    }

    fn resize(self: *HashTable) !void {
        const new_capacity = self.capacity * GROWTH_FACTOR;
        var new_entries = try self.allocator.alloc(HashEntry, new_capacity);
        for (new_entries) |*entry| {
            entry.* = .{
                .key = null,
                .hash = 0,
                .total = 0,
                .a = 0,
                .t = 0,
                .c = 0,
                .g = 0,
            };
        }

        for (self.entries) |*old_entry| {
            if (old_entry.key == null) continue;
            const h = old_entry.hash;
            var index = h % new_capacity;
            var i: u32 = 1;
            while (new_entries[index].key != null) {
                index = (index + i) % new_capacity;
                i += 1;
            }
            new_entries[index] = old_entry.*;
        }

        self.allocator.free(self.entries);
        self.entries = new_entries;
        self.capacity = new_capacity;
    }

    fn probe(self: *HashTable, h: u32, key: []const u8) usize {
        var index = @as(usize, h) % self.capacity;
        var i: u32 = 1;
        while (self.entries[index].key != null and
            (self.entries[index].hash != h or !mem.eql(u8, self.entries[index].key.?, key)))
        {
            index = (index + i) % self.capacity;
            i += 1;
        }
        return index;
    }

    fn hash(key: []const u8) u32 {
        const mulH: u64 = 31;
        const PH: u64 = 4294967029;
        var h: u64 = 0;
        var i: usize = 0;
        while (i + 8 <= key.len) : (i += 8) {
            const chunk = mem.readInt(u64, key[i..][0..8],.little);
            h = (h *% mulH + chunk) % PH;
        }
        while (i < key.len) : (i += 1) {
            h = (h *% mulH + key[i]) % PH;
        }
        h = (h *% mulH + h) % PH;
        return @truncate(h);
    }

    pub fn get(self: *HashTable, key: []const u8, last_char: u8, out_sum: *u32) u32 {
        const h = hash(key);
        const index = probe(self, h, key[0..self.key_length]);
        const entry = &self.entries[index];

        if (entry.key == null) {
            return 0;
        }

        out_sum.* = entry.total;
        return switch (last_char) {
            'A' => entry.a,
            'T' => entry.t,
            'C' => entry.c,
            'G' => entry.g,
            else => 0,
        };
    }

    fn increment(self: *HashTable, last_char: u8, key: []const u8) !void {
        if (@as(f64, @floatFromInt(self.size)) >= @as(f64, @floatFromInt(self.capacity)) * LOAD_FACTOR) {
            try self.resize();
        }
        const h = hash(key);
        const index = self.probe(h, key);
        const entry = &self.entries[index];

        if (entry.key == null) {
            entry.key = key;
            entry.hash = h;
            entry.total = 0;
            entry.a = 0;
            entry.t = 0;
            entry.c = 0;
            entry.g = 0;
            self.size += 1;
        }

        entry.total += 1;
        switch (last_char) {
            'A' => entry.a += 1,
            'T' => entry.t += 1,
            'C' => entry.c += 1,
            'G' => entry.g += 1,
            else => return error.InvalidCharacter,
        }
    }
};

fn readAndFilterFile(allocator: Allocator, path: []const u8) ![]const u8 {
    const data = try std.fs.cwd().readFileAlloc(allocator, path, std.math.maxInt(usize));
    var filtered = ArrayList(u8).init(allocator);
    defer filtered.deinit();
    for (data) |c| {
        if (c == 'A' or c == 'T' or c == 'C' or c == 'G') {
            try filtered.append(c);
        }
    }
    return filtered.toOwnedSlice();
}

fn parseDBEntries(allocator: Allocator, data: []const u8) ![]DBEntry {
    var entries = ArrayList(DBEntry).init(allocator);
    defer entries.deinit();

    var chunks = std.mem.splitSequence(u8, data, "@");
    _ = chunks.next(); // Skip first empty

    while (chunks.next()) |chunk| {
        var lines = std.mem.splitSequence(u8, chunk, "\n");
        const name = lines.next() orelse continue;
        var seq = ArrayList(u8).init(allocator);
        defer seq.deinit();

        while (lines.next()) |line| {
            if (line.len == 0 or line[0] == '@') break;
            for (line) |c| {
                if (c == 'A' or c == 'T' or c == 'C' or c == 'G') {
                    try seq.append(c);
                }
            }
        }

        try entries.append(.{
            .name = name,
            .sequence = try seq.toOwnedSlice(),
        });
    }

    return entries.toOwnedSlice();
}

fn buildModel(allocator: Allocator, sequence: []const u8, depth: usize) !*HashTable {
    const key_length = depth;
    if (sequence.len < key_length) return error.SequenceTooShort;

    var arena = std.heap.ArenaAllocator.init(allocator);

    var map = try HashTable.init(arena.allocator(), key_length);
    const max_i = sequence.len - key_length ;

    for (0..max_i) |i| {
        const key_slice = sequence[i..i + key_length];
        const last_char = sequence[i + key_length ];
        // const key = try arena.allocator().dupe(u8, key_slice);
        try map.increment(last_char,key_slice);
    }
    return map; 
}

fn estimateBits(sequence: []const u8, map: *HashTable, alpha: f64) f64 {
    const key_length = map.key_length;
    const max_i = sequence.len - key_length;
    var sum: f64 = 0.0;
    const alpha4 = alpha * 4.0;
    for (0..max_i) |i| {
        const key = sequence[i..i + key_length];
        const last_char = sequence[i + key_length];
        var total: u32 = 0;
        const count = map.get(key, last_char, &total);
        sum += @log(( @as(f64, @floatFromInt(count)) + alpha) / ( @as(f64, @floatFromInt(total)) + alpha4 )); 
    }

    return -sum / @log(2.0);
}

fn computeNRC(entry: *DBEntry, map: *HashTable, alpha: f64) void {
    const bits = estimateBits(entry.sequence, map, alpha);
    entry.nrc = bits / (@as(f64, @floatFromInt(entry.sequence.len)) * 2.0);
}

fn parseArgs(allocator: Allocator) !Args {
    var args = Args{
        .data_path = undefined,
        .sequence_path = undefined,
    };
    var arg_iter = try std.process.argsWithAllocator(allocator);
    defer arg_iter.deinit();

    _ = arg_iter.next(); // Skip executable name

    while (arg_iter.next()) |arg| {
        if (mem.eql(u8, arg, "-d")) {
            args.data_path = try allocator.dupe(u8, arg_iter.next() orelse return error.MissingValue);
        } else if (mem.eql(u8, arg, "-s")) {
            args.sequence_path = try allocator.dupe(u8, arg_iter.next() orelse return error.MissingValue);
        } else if (mem.eql(u8, arg, "-k")) {
            args.depth = try std.fmt.parseInt(usize, arg_iter.next() orelse return error.MissingValue, 10);
        } else if (mem.eql(u8, arg, "-a")) {
            args.alpha = try std.fmt.parseFloat(f64, arg_iter.next() orelse return error.MissingValue);
        } else if (mem.eql(u8, arg, "-t")) {
            args.top = try std.fmt.parseInt(usize, arg_iter.next() orelse return error.MissingValue, 10);
        } else {
            std.debug.print("Unknown option: {s}\n", .{arg});
            return error.InvalidOption;
        }
    }

    if (args.data_path == null or args.sequence_path == null) {
        return error.MissingRequiredArgs;
    }

    return args;
}

pub fn main() !void {
    var gpa = std.heap.GeneralPurposeAllocator(.{}){};
    const allocator = gpa.allocator();
    defer _ = gpa.deinit();

    const args = try parseArgs(allocator);
    defer {
        if (args.data_path) |data_path| allocator.free(data_path);
        if (args.sequence_path) |sequence_path| allocator.free(sequence_path);
    }
    const seq_data = try readAndFilterFile(allocator, args.sequence_path orelse return error.MissingSequencePath);
    defer allocator.free(seq_data);

    var model = try buildModel(allocator, seq_data, args.depth);
    defer model.deinit();

    const db_data = try std.fs.cwd().readFileAlloc(allocator, args.data_path orelse return error.MissingDataPath, std.math.maxInt(usize));
    defer allocator.free(db_data);

    var entries = try parseDBEntries(allocator, db_data);
    defer {
        for (entries) |e| allocator.free(e.sequence);
        allocator.free(entries);
    }

    for (entries) |*entry| {
        computeNRC(entry, model, args.alpha);
    }

    std.sort.heap(DBEntry, entries, {}, struct {
        fn lessThan(_: void, a: DBEntry, b: DBEntry) bool {
            return a.nrc < b.nrc;
        }
    }.lessThan);

    const top = @min(args.top, entries.len);
    for (entries[0..top]) |entry| {
        std.debug.print("{d:.6}\t{s}\n", .{entry.nrc, entry.name});
    }
}