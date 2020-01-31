#include <stdio.h>
#include <stdlib.h>

extern void reset();

void __VERIFIER_error(int);

void __VERIFIER_error(int i) {
    fprintf(stderr, "error_%d ", i);
    reset();
}
