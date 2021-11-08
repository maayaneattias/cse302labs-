#include <stdio.h>
#include <stdint.h>
void __bx_print_int(int64_t x)
{
    printf("%ld\n", x); /* same as lab 3 (except for name) */
}
/* note: booleans are converted into int64_ts when
being passed by value to function calls: more on that
next week */
void __bx_print_bool(int64_t x)
{
    /* boolean encoding: 0 is false, everything else is true */
    printf("%s\n", x == 0 ? "false" : "true");
}