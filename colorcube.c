#include <stdio.h>
// This was written by Tene, of http://allalone.org fame.


int rgb(int r, int g, int b) {
    return 16 + r*36 + g*6 + b;
}
void main() {
    for (int r = 0; r < 6; r++) {
        for (int g = 0; g < 6; g++) {
            for (int b = 0; b < 6; b++) {
                for (int bgr = 0; bgr < 6; bgr++) {
                    for (int bgg = 0; bgg < 6; bgg++) {
                        for (int bgb = 0; bgb < 6; bgb++) {
                            printf("\e[38;5;%dm\e[48;5;%dm#\e[0m", rgb(r,g,b), rgb(bgr,bgg,bgb));
                        }
                    }
                    printf("\n");
                }
            }
        }
        printf("\n");
    }
}
