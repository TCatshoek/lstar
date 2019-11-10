#include <stdio.h>
#include <assert.h>

void __VERIFIER_error(int);

void __VERIFIER_error(int i) {
    fprintf(stderr, "error_%d ", i);
    assert(0);
}