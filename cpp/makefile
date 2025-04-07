COMPILER=g++
FILE=meta.cpp

meta:
	${COMPILER} ${FILE} -Wall -Wextra -o3 -fopenmp -lm -march=native -mtune=native -flto -ffast-math -fomit-frame-pointer -funroll-loops -o meta

meta_debug:
	${COMPILER} ${FILE} -Wall -Wextra -ggdb -lm -o meta_debug

clean:
	rm -rf meta meta_debug

all: clean meta meta_debug