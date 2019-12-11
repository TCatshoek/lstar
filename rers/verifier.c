#include <stdio.h>
#include <stdlib.h>

void __VERIFIER_error(int);

void __VERIFIER_error(int i) {
    fprintf(stderr, "error_%d ", i);
    exit(-1);
}