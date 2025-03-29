#### Note: Run the program using Java 17 or above.

## Build JAR

`mvn package`

Requires to have [maven](https://maven.apache.org/install.html) installed.

## Program arguments

Usage: <main class> [-v] [-a=<alpha>] [-fd=<fileNameDb>] [-fm=<fileNameMeta>]
[-k=<k>] [-t=<t>]\
-a, --alpha=<alpha>      Smoothing parameter alpha\
-fd, --file-db=<fileNameDb> File path for db/sequences\
-fm, --file-meta=<fileNameMeta> File path for meta\
-k, --contextWidth=<k>   Context width\
-t, --top=<t>            Top t results\
-v, --verbose Verbose output(true, false)

## Example arguments

### Basic

`java -jar target/tai-1.0-SNAPSHOT.jar -fm ../sequences/meta.txt -fd ../sequences/db.txt`

### Advanced

`java -jar target/tai-1.0-SNAPSHOT.jar -fm ../sequences/meta.txt -fd ../sequences/db.txt -a 0.01 -k 13 -t 10`