#include <stdio.h>
#include <assert.h>
#include <math.h>
#include <stdlib.h>

int main(int argc, char *argv[])
{
    int n;
    if (sscanf(argv[1], "%i", &n) != 1) {
        return -1;
    }

    // main i/o-loop
    for (int i = 0; i < n; i++)
    {
        // read input
        int input;
        scanf("%d", &input);
        if (input == 0) {
            return 0;
        }
        printf("%d \n", input);
    }
    return 0;
}