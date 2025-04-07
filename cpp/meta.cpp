#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <unordered_map>
#include <unordered_set>
#include <algorithm>
#include <cmath>
#include <memory>
#include <chrono>
#include <iomanip>

#ifdef _OPENMP
#include <omp.h>
#endif

struct Args {
    std::string data;
    std::string sequence;
    size_t context = 2;
    double alpha = 1.0;
    size_t top = 20;
    bool verbose = false;
    bool csv = false;
};

Args parseArgs(int argc, char** argv) {
    Args args;
    for (int i = 1; i < argc; i++) {
        std::string arg = argv[i];
        if (arg == "-d" || arg == "--data" ) {
            args.data = argv[++i];
        } else if (arg == "-s" ||arg == "--sequence" ) {
            args.sequence = argv[++i];
        } else if (arg == "-k" ||arg == "--context" ) {
            args.context = std::stoul(argv[++i]);
        } else if (arg == "-a" ||arg == "--alpha" ) {
            args.alpha = std::stod(argv[++i]);
        } else if (arg == "-t" ||arg == "--top" ) {
            args.top = std::stoul(argv[++i]);
        } else if (arg == "-v" ||arg == "--verbose") {
            args.verbose = true;
        } else if (arg == "-c" ||arg == "--csv") {
            args.csv = true;
        }
    }
    return args;
}

std::vector<std::pair<std::string, std::string>> parse_database(const std::string &text) {
    std::vector<std::pair<std::string, std::string>> records;
    size_t start = 0;

    while (start < text.size() && text[start] != '@') {
        start++;
    }
    if (start < text.size() && text[start] == '@') {
        start++;
    }

    while (start < text.size()) {
        size_t next_at = text.find('@', start);
        std::string segment = (next_at == std::string::npos)
            ? text.substr(start)
            : text.substr(start, next_at - start);

        size_t newline = segment.find('\n');
        std::string name = (newline == std::string::npos)
            ? segment
            : segment.substr(0, newline);
        std::string seq_raw = (newline == std::string::npos)
            ? ""
            : segment.substr(newline + 1);

        std::string sequence;
        for (char c : seq_raw) {
            if (c == 'A' || c == 'T' || c == 'C' || c == 'G') {
                sequence.push_back(c);
            }
        }
        records.emplace_back(name, sequence);

        if (next_at == std::string::npos) break;
        start = next_at + 1;
    }
    return records;
}

void print_log(const std::string &message) {
    auto now = std::chrono::system_clock::now();
    auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(
                  now.time_since_epoch()) % 1000;
    std::time_t t = std::chrono::system_clock::to_time_t(now);
    std::tm tm = *std::localtime(&t);
    std::cout << std::put_time(&tm, "%H:%M:%S")
              << ":" << std::setfill('0') << std::setw(3) << ms.count()
              << " " << message << std::endl;
}

void print_table(const std::vector<std::pair<std::string, double>> &res, size_t top, bool csv) {
    if (csv) {
        for (size_t i = 0; i < std::min(top, res.size()); i++) {
            std::cout << res[i].second << "\t" << res[i].first << "\n";
        }
        return;
    }

    const int NRC_WIDTH = 6;
    const int IDENTIFIER_WIDTH = 50;
    std::cout << std::string(NRC_WIDTH + 2, '=') << " " << std::string(IDENTIFIER_WIDTH + 2, '=') << std::endl;
    std::cout << std::setw(NRC_WIDTH + 2) << "NRC" << " " << std::setw(IDENTIFIER_WIDTH + 2) << "Identifier" << std::endl;
    std::cout << std::string(NRC_WIDTH + 2, '-') << " " << std::string(IDENTIFIER_WIDTH + 2, '-') << std::endl;

    // im too lazy to do a prettier print might ask chatgpt to gen this
    for (size_t i = 0; i < std::min(top, res.size()); i++) {
        std::string name = res[i].first;
        if (name.size() > IDENTIFIER_WIDTH)
            name = name.substr(0, IDENTIFIER_WIDTH);
        std::cout << std::setw(NRC_WIDTH + 2) << std::fixed << std::setprecision(4) << res[i].second << " "
                  << std::setw(IDENTIFIER_WIDTH + 2) << name << std::endl;
    }
    std::cout << std::string(NRC_WIDTH + 2, '=') << " " << std::string(IDENTIFIER_WIDTH + 2, '=') << std::endl;
}

class Model {
public:
    size_t ko;
    double alpha;
    double const_term;
    // Table: maps context (string) to a pair: (map of next-char counts, total count)
    std::unordered_map<std::string, std::pair<std::unordered_map<char, size_t>, size_t>> table;

    Model(const std::string &text, size_t ko, double alpha)
        : ko(ko), alpha(alpha) {
        std::unordered_set<char> alphabet;
        for (char c : text) {
            alphabet.insert(c);
        }
        const_term = alpha * static_cast<double>(alphabet.size());
        table = build_table(text, ko);
    }

    static std::unordered_map<std::string, std::pair<std::unordered_map<char, size_t>, size_t>>
    build_table(const std::string &text, size_t ko) {
        std::unordered_map<std::string, std::pair<std::unordered_map<char, size_t>, size_t>> table;
        if (text.size() <= ko) return table;
        for (size_t i = 0; i < text.size() - ko ; i++) {
            std::string context = text.substr(i, ko);
            char next_char = text[i + ko];
            auto &entry = table[context];
            entry.first[next_char] += 1;
            entry.second += 1;
        }
        return table;
    }

    double estimate_bits(const std::string &text) const {
        double sum = 0.0;
        const double log2_const = std::log(2.0);
        if (text.size() <= ko) return 0.0;
        for (size_t i = 0; i <= text.size() - ko - 1; i++) {
            std::string context = text.substr(i, ko);
            char next_char = text[i + ko];
            size_t count = 0;
            size_t total = 0;
            auto it = table.find(context);
            if (it != table.end()) {
                auto &pair_val = it->second;
                auto it2 = pair_val.first.find(next_char);
                if (it2 != pair_val.first.end()) {
                    count = it2->second;
                }
                total = pair_val.second;
            }
            double numerator = static_cast<double>(count) + alpha;
            double denominator = static_cast<double>(total) + const_term;
            sum += std::log(numerator / denominator);
        }
        return -sum / log2_const;
    }

    double nrc(const std::string &x) const {
        if (x.size() <= ko) return 0.0;
        double content = estimate_bits(x);
        double length_x = static_cast<double>(x.size());
        std::unordered_set<char> alphabet_x(x.begin(), x.end());
        double alphabet_size = static_cast<double>(alphabet_x.size());
        double denominator = length_x * std::log2(alphabet_size);
        return (denominator <= 0.0) ? 0.0 : content / denominator;
    }
};

int main(int argc, char **argv) {
    Args args = parseArgs(argc, argv);
    if (args.data.empty() || args.sequence.empty()) {
        std::cerr << "Usage: " << argv[0] << " --data <data_file> --sequence <sequence_file> [--context <num>] [--alpha <value>] [--top <num>] [--verbose] [--csv]" << std::endl;
        return 1;
    }

    std::ifstream db_file(args.data, std::ios::binary);
    if (!db_file) {
        std::cerr << "Failed to open file: " << args.data << std::endl;
        return 1;
    }
    std::stringstream db_buffer;
    db_buffer << db_file.rdbuf();
    std::string db_text = db_buffer.str();

    auto sequences = parse_database(db_text);
    if (args.verbose) {
        print_log("[INFO] Database: loaded " + std::to_string(sequences.size()) + " sequences");
    }

    std::ifstream seq_file(args.sequence, std::ios::binary);
    if (!seq_file) {
        std::cerr << "Failed to open file: " << args.sequence << std::endl;
        return 1;
    }
    std::stringstream seq_buffer;
    seq_buffer << seq_file.rdbuf();
    std::string seq_text = seq_buffer.str();

    std::string sequence_bytes;
    for (char c : seq_text) {
        if (c == 'A' || c == 'T' || c == 'C' || c == 'G') {
            sequence_bytes.push_back(c);
        }
    }

    Model model(sequence_bytes, args.context, args.alpha);
    if (args.verbose) {
        print_log("[INFO] Model: created with depth " + std::to_string(args.context) +
                  " and alpha " + std::to_string(args.alpha));
    }

    // Calculate NRC for each sequence in the database in parallel with omp.
    std::vector<std::pair<std::string, double>> nrcs(sequences.size());
    #pragma omp parallel for schedule(static)
    for (size_t i = 0; i < sequences.size(); i++) {
        double nrc_value = model.nrc(sequences[i].second);
        nrcs[i] = { sequences[i].first, nrc_value };
    }

    std::sort(nrcs.begin(), nrcs.end(), [](const auto &a, const auto &b) {
        return a.second < b.second;
    });

    if (args.verbose) {
        print_log("[INFO] Similarity: calculated for " + std::to_string(nrcs.size()) + " sequences");
    }

    print_table(nrcs, args.top, args.csv);

    return 0;
}
