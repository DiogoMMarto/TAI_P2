# TAI_P2

This project provides implementations in multiple programming languages. Below are the instructions to compile and run the program on Linux for each language.

## General Usage

The program can be executed with the following command:
```
./meta -s ../sequences/meta.txt -d ../sequences/db.txt -k 17 -a 1
```

Replace the arguments as needed for your specific use case.

---

## Language Implementations

### C/C++

#### Compilation
To compile the C/C++ implementation, use `gcc` or `g++`:
```bash
gcc -o meta meta.c
# or
g++ -o meta meta.cpp
```

#### Execution
Run the compiled binary:
```bash
./meta -s ../sequences/meta.txt -d ../sequences/db.txt -k 17 -a 1
```

#### Compiler Installation
Follow the [GCC Installation Guide](https://gcc.gnu.org/install/) to install the GCC compiler.

---

### Java

#### Compilation
To compile the Java implementation, use `javac`:
```bash
javac Meta.java
```

#### Execution
Run the compiled Java program:
```bash
java Meta -s ../sequences/meta.txt -d ../sequences/db.txt -k 17 -a 1
```

#### Compiler Installation
Follow the [OpenJDK Installation Guide](https://openjdk.org/install/) to install the Java compiler.

---

### Python

#### Execution
Python scripts do not require compilation. Run the script directly:
```bash
python3 meta.py -s ../sequences/meta.txt -d ../sequences/db.txt -k 17 -a 1
```

#### Interpreter Installation
Follow the [Python Installation Guide](https://www.python.org/downloads/) to install Python.

---

### Rust

#### Compilation
To compile the Rust implementation, use `cargo`:
```bash
cargo build --release
```

The compiled binary will be located in the `target/release/` directory.

#### Execution
Run the compiled binary:
```bash
./target/release/meta -s ../sequences/meta.txt -d ../sequences/db.txt -k 17 -a 1
```

#### Compiler Installation
Follow the [Rust Installation Guide](https://www.rust-lang.org/tools/install) to install the Rust compiler.

---

### Go

#### Compilation
To compile the Go implementation, use `go build`:
```bash
go build -o meta meta.go
```

#### Execution
Run the compiled binary:
```bash
./meta -s ../sequences/meta.txt -d ../sequences/db.txt -k 17 -a 1
```

#### Compiler Installation
Follow the [Go Installation Guide](https://go.dev/doc/install) to install the Go compiler.

---

### Notes
- Ensure all dependencies are installed for each language before compiling or running the program.
- Use the provided example command to test the program with sample input files.
