#include <stdio.h>
#include <stdlib.h>
#include <assert.h>

extern char shouldstop;

void __VERIFIER_error(int);

void __VERIFIER_error(int i) {
    shouldstop = 1;
}