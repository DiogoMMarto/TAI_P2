#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <string.h>
#include <stdint.h>
#include <math.h>
#include <time.h>

#define mulH 31     
#define PH   4294967029     // large prime
#define SEED 8589934621

#define INITIAL_CAPACITY 2048
#define INITIAL_CAPACITY_ARRAY 8
#define LOAD_FACTOR 0.6
#define LOAD_FACTOR_2 0.8
#define GROWTH_FACTOR 2

typedef struct {
    char* data;
    char* sequence;
    int depth;
    double alpha;
    int top;
} Args;

Args default_args() {
    Args args;
    args.data = NULL;
    args.sequence = NULL;
    args.depth = 2;
    args.alpha = 1.0;
    args.top = 20;
    return args;
}

typedef struct {
    char* key;
    uint32_t hash;
    uint32_t size;
    uint32_t capacity;
    uint32_t total;
    uint32_t a;
    uint32_t t;
    uint32_t c;
    uint32_t g;
} HashEntry;

typedef struct {
    HashEntry* entries;
    uint32_t context_length;
    uint32_t capacity;
    uint32_t size;
} HashTable;

typedef struct {
    char* sequence;
    char* name;
    double nrc;
    uint32_t size_seq;
} DBEntry;

typedef struct {
    DBEntry *db;     
    uint32_t start; 
    uint32_t end;  
    HashTable *table;   
    double alpha;  
} ThreadData;

uint32_t hash(const char *data, uint32_t length) {
    uint64_t hash = 0;
    uint64_t* data64 = (uint64_t*)data;
    uint32_t i = 0;
    for (; i + sizeof(uint64_t) <= length; i+=sizeof(uint64_t)) {
        hash = ((hash * mulH) + *data64++) % PH;
    }
    for(; i < length; i++) { // this works well bcs at the end we still scramble a bit
        hash = ((hash * mulH) + data[i]) % PH;
    }
    return ((hash * mulH) + hash) % PH; 
}

uint64_t strcmpDepth(const char* a, const char* b, uint32_t depth) {
    uint32_t i = 0;
    const uint64_t* a64 = (uint64_t*)a;
    const uint64_t* b64 = (uint64_t*)b;
    for(;i + sizeof(uint64_t) <= depth; i+=sizeof(uint64_t), a64++, b64++){
        if(*a64 != *b64) return 1;
    };
    int shift_amt = 8*(8 - depth % 8)*(i >= (depth-depth%8));
    if(shift_amt == 64) return 0;
    uint64_t mask = -1ull >> shift_amt;
    return (*a64 & mask ) - (*b64 & mask);
}

uint32_t probe(HashTable* table,  uint32_t h , char* key) {
    uint64_t index = h % table->capacity;
    uint32_t i = 1;
    while (table->entries[index].key && table->entries[index].hash != h && strcmpDepth(table->entries[index].key, key,table->context_length) != 0) {
        index = (index + i) % table->capacity;
        i++;
    }   
    return index; 
}

HashTable* create_hashtable(uint32_t context_length) {
    HashTable* table = malloc(sizeof(HashTable));
    table->context_length = context_length;
    table->capacity = INITIAL_CAPACITY;
    table->size = 0;
    table->entries = calloc(INITIAL_CAPACITY, sizeof(HashEntry));
    return table;
}

void hashtable_resize(HashTable* table) {
    uint32_t new_capacity = table->capacity * GROWTH_FACTOR;
    HashEntry* new_entries = calloc(new_capacity, sizeof(HashEntry));
    for (uint32_t i = 0; i < table->capacity; i++) {
        HashEntry* entry = &table->entries[i];
        if (entry->key != NULL) {
            uint64_t index = entry->hash % new_capacity;
            uint32_t j = 1;
            while (new_entries[index].key && new_entries[index].hash != entry->hash && strcmpDepth(new_entries[index].key, entry->key,table->context_length) != 0) {
                index = (index + j) % new_capacity;
                j++;
            }
            new_entries[index]= *entry;
        }
    }
    free(table->entries);
    table->entries = new_entries;
    table->capacity = new_capacity;
}

uint32_t* map_key(HashEntry* e , char c) {
    if(c == 'A') return &e->a;
    if(c == 'T') return &e->t;
    if(c == 'C') return &e->c;
    if(c == 'G') return &e->g;
    return NULL;
}

void hashtable_increment(HashTable* table, char* key) {
    if (table->size >= table->capacity * LOAD_FACTOR) {
        hashtable_resize(table);
    }
    uint32_t h = hash(key, table->context_length);
    uint64_t index = probe(table, h, key);
    HashEntry* entry = &table->entries[index];
    if (!entry->key) {
        table->size++;
        entry->key = key;
        entry->hash = h;
        entry->size = 0;
        entry->capacity = INITIAL_CAPACITY_ARRAY;
        entry->total = 0;
        entry->a = 0;
        entry->t = 0;
        entry->c = 0;
        entry->g = 0;
    } 
    entry->total++;
    char last_char = key[table->context_length];
    uint32_t* char_entry = map_key(entry, last_char);
    if (char_entry == NULL) {
        printf("Error: Invalid character '%c' in key %d\n", last_char, last_char);
        exit(1);
    }
    (*char_entry)++;
}

int hashtable_get(HashTable* table, char* key, uint32_t* sum) {
    uint32_t h = hash(key, table->context_length);
    uint64_t index = probe(table, h, key);
    if (!table->entries[index].key) {
        return 0;
    }
    char last_char = key[table->context_length];
    *sum = table->entries[index].total;
    return *(map_key(&table->entries[index], last_char));
}

void hashtable_free(HashTable* table) {
    free(table->entries);
    free(table);
}

Args parse_agrs(int argc, char* argv[]){
    Args args = default_args();
    if (argc < 2) {
        printf("Usage: %s -d <data_file> -s <sequence_file> [-k <depth>] [-a <alpha>] [-t <top>] [-v] [-csv]\n", argv[0]);
        printf("Options:\n");
        printf("  -d <data_file>     Path to the data file\n");
        printf("  -s <sequence_file> Path to the sequence file\n");
        printf("  -k <depth>         Context depth (default: 2)\n");
        printf("  -a <alpha>         Alpha parameter (default: 1.0)\n");
        printf("  -t <top>           Number of top results to display (default: 20)\n");
        printf("  -v                 Verbose output\n");
        printf("  -csv               Output in CSV format\n");
        exit(1);
    }

    for (int i = 1; i < argc;) {
        if (strcmp(argv[i], "-d") == 0 || strcmp(argv[i], "--data") == 0) {
            if (i + 1 >= argc) {
                printf("Missing value for %s\n", argv[i]);
                exit(1);
            }
            args.data = argv[++i];
        } else if (strcmp(argv[i], "-s") == 0 || strcmp(argv[i], "--sequence") == 0) {
            if (i + 1 >= argc) {
                printf("Missing value for %s\n", argv[i]);
                exit(1);
            }
            args.sequence = argv[++i];
        } else if (strcmp(argv[i], "-k") == 0 || strcmp(argv[i],"--context") == 0) {
            if (i + 1 >= argc) {
                printf("Missing value for %s\n", argv[i]);
                exit(1);
            }
            args.depth = atoi(argv[++i]);
        } else if (strcmp(argv[i], "-a" ) == 0 || strcmp(argv[i],"--alpha") == 0) {
            if (i + 1 >= argc) {
                printf("Missing value for %s\n", argv[i]);
                exit(1);
            }
            args.alpha = atof(argv[++i]);
        } else if (strcmp(argv[i], "-t") == 0 || strcmp(argv[i],"--top") == 0) {
            if (i + 1 >= argc) {
                printf("Missing value for %s\n", argv[i]);
                exit(1);
            }
            args.top = atoi(argv[++i]);
        } else {
            printf("Unknown option: %s\n", argv[i]);
            exit(1);
        }
        i++;
    }
    return args;
}

char* read_file(const char* file_path, uint32_t* size) {
    FILE* file = fopen(file_path, "rb");
    if(file == NULL) {
        printf("Could not open file: %s\n", file_path);
        exit(1);
    }

    fseek(file, 0, SEEK_END);
    uint32_t file_size = ftell(file);
    *size = file_size;
    fseek(file, 0, SEEK_SET);

    char* buffer = (char*)malloc(file_size + 1);
    if(buffer == NULL) {
        printf("Could not allocate memory for file: %s\n", file_path);
        exit(1);
    }

    fread(buffer, file_size, 1, file);
    buffer[file_size] = '\0';

    fclose(file);
    return buffer;
}

char* filter(char* text, uint32_t* size) {
    char* filtered = (char*)malloc(*size + 1);
    uint32_t j = 0;
    for (uint32_t i = 0; i < *size; i++) {
        if (text[i] == 'A' || text[i] == 'C' || text[i] == 'G' || text[i] == 'T') {
            filtered[j++] = text[i];
        }
    }
    filtered[j] = '\0';
    *size = j;
    return filtered;
}

DBEntry* parse_db(char* text, uint32_t text_size, uint32_t* size) {
    uint32_t count = 0;
    for (uint32_t i = 0; text[i] != '\0'; i++) {
        if (text[i] == '@') {
            count++;
        }
    }

    *size = count;
    DBEntry* db = (DBEntry*)malloc(count * sizeof(DBEntry));
    
    char* cursor = text;
    cursor++; // skip first '@'
    count = 0;
    while (*cursor != '\0') {
        DBEntry* entry = &db[count++];

        char* next_line = strchr(cursor, '\n');
        if (next_line) {
            *next_line = '\0';
        }

        entry->name = cursor;
        cursor = next_line + 1; 

        char *next_at = strchr(cursor, '@');
        if (next_at) {
            *next_at = '\0';
        }
        if (next_at >= text + text_size || next_at < text) {
            next_at = text + text_size -1;
        }
        
        entry->size_seq = next_at - cursor+1;
        entry->sequence = filter(cursor, &entry->size_seq);
        cursor = next_at + 1;
        entry->nrc = 0;
    }

    return db;
}

HashTable* build_model(char* text, uint32_t size, int ko){
    if (ko < 0) {
        printf("Depth must be non-negative\n");
        exit(1);
    }
    uint32_t context_length = ko;
    uint32_t max_i = size - context_length;
    
    HashTable* table = create_hashtable(context_length);

    for(uint32_t i = 0; i < max_i; i++){
        char* context = text + i;
        hashtable_increment(table, context);
    }

    return table;
}

double estimate_bits(char* text, HashTable* model, double alpha){
    double const_term = alpha * 4; // 4 is the size of the alphabet
    double sum_total = 0;
    uint32_t max_i = strlen(text) - model->context_length;
    for (uint32_t i = 0; i < max_i; i++) {
        char* context = text + i;
        uint32_t total = 0;
        uint32_t count = hashtable_get(model, context, &total);
        double symbol_length = log((count + alpha) / (total + const_term));
        sum_total += symbol_length;
    }
    return -sum_total / log(2); // bits per symbol
}

double nrc(DBEntry* entry, HashTable* table, double alpha) {
    if (entry->nrc != 0) {
        return entry->nrc;
    }
    double bits = estimate_bits(entry->sequence, table, alpha);
    return bits / ((entry->size_seq) * 2); 
}

int compare_nrc(const void* a, const void* b) {
    DBEntry* entry_a = (DBEntry*)a;
    DBEntry* entry_b = (DBEntry*)b;
    if (entry_a->nrc < entry_b->nrc) {
        return -1;
    } else if (entry_a->nrc > entry_b->nrc) {
        return 1;
    } else {
        return 0;
    }
}

void* thread_func(void *arg) {
    ThreadData *data = (ThreadData*)arg;
    for (uint32_t i = data->start; i < data->end; i++) {
        data->db[i].nrc = nrc(&data->db[i], data->table, data->alpha);
    }
    return NULL;
}

int main(int argc, char* argv[]){
    Args args = parse_agrs(argc, argv);
    if (args.data == NULL) {
        printf("Data file is required\n");
        exit(1);
    }

    if (args.sequence == NULL) {
        printf("Sequence file is required\n");
        exit(1);
    }

    uint32_t seq_size = 0;
    char* seq_text = read_file(args.sequence, &seq_size);
    char* filtered_seq = filter(seq_text, &seq_size);
    free(seq_text);
    seq_text = filtered_seq;

    HashTable* table = build_model(seq_text, seq_size, args.depth);

    uint32_t size = 0;
    char* db_text = read_file(args.data, &size);
    uint32_t db_size = 0;
    DBEntry* db = parse_db(db_text, size, &db_size);

    int num_threads = 16; 
    pthread_t threads[num_threads];
    ThreadData thread_data[num_threads];

    uint32_t chunk_size = db_size / num_threads;
    uint32_t remainder = db_size % num_threads;

    uint32_t start = 0;
    for (int t = 0; t < num_threads; t++) {
        thread_data[t].db = db;
        thread_data[t].table = table;
        thread_data[t].alpha = args.alpha;
        thread_data[t].start = start;
        thread_data[t].end = start + chunk_size + (t < (int)remainder ? 1 : 0);
        start = thread_data[t].end;
        if (pthread_create(&threads[t], NULL, thread_func, &thread_data[t]) != 0) {
            perror("pthread_create");
            free(db);
            exit(EXIT_FAILURE);
        }
    }

    for (int t = 0; t < num_threads; t++) {
        pthread_join(threads[t], NULL);
    }

    qsort(db, db_size, sizeof(DBEntry), compare_nrc);

    for (int i = 0; i < args.top; i++) {
        printf("%f\t%s\n", db[i].nrc, db[i].name);
    }
}