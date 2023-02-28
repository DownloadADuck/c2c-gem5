
int main(void) {
    int i;
    // char s[] = {'h', 'e', 'l', 'l', 'o', ' ', 'w', 'o', 'r', 'l', 'd'};

    volatile char s[] = {1, 2, 3, 4, 5, 6};

    for (i = 0; i < sizeof(s); ++i) {
       s[i]++; 
    }
    return 0;
}
