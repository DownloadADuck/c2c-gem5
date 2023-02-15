#include <iostream>
#include <vector>

int main() {
    // Two input vectors
    std::vector<int> vec1 {1, 2, 3};
    std::vector<int> vec2 {4, 5, 6};

    // Result vector
    std::vector<int> result(vec1.size());

    // Add
    for (int i = 0; i < vec1.size(); i++) {
        result[i] = vec1[i] + vec2[i];
    }

    return 0;
}