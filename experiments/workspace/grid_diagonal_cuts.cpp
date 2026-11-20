// Check the seven exterior cell counts on every subset of a marked diagonal half.
#include <array>
#include <bit>
#include <cstdint>
#include <cstdio>
#include <vector>

int minimum_squares(int total) {
    int q = total / 10;
    int r = total % 10;
    return 10*q*q + r*(2*q+1);
}

int main() {
    // The complementary subset has the same excess above its minimum.
    constexpr unsigned limit = 1U << 19;
    std::vector<int> base(limit), interaction(limit), boundary(limit);
    for (unsigned set = 0; set < limit; ++set) {
        int a = std::popcount(set & 1023U);
        int b = std::popcount(set >> 10);
        int m = a+b;
        base[set] = 9*m + 2*m*m - a*a - b*b - 2*minimum_squares(m)
                    - 2*minimum_squares(a+2*b) - 2*minimum_squares(2*a+b)
                    - minimum_squares(2*m);
    }
    std::uint8_t h[20][20];
    for (int index = 0; ; ++index) {
        auto size = std::fread(h, 1, sizeof(h), stdin);
        if (!size) return std::ferror(stdin) ? 1 : 0;
        if (size != sizeof(h)) return 1;
        std::array<unsigned, 20> adjacent{}, first{}, second{};
        for (int i = 0; i < 20; ++i) {
            for (int j = i+1; j < 20; ++j) {
                if (h[i][j]) {
                    adjacent[i] |= 1U << j;
                    adjacent[j] |= 1U << i;
                }
                int w = h[i][j];
                for (int k = 0; k < 20; ++k) w += h[i][k]*h[k][j];
                if (w > 2) return 1;
                if (w >= 1) {
                    first[i] |= 1U << j;
                    first[j] |= 1U << i;
                }
                if (w == 2) {
                    second[i] |= 1U << j;
                    second[j] |= 1U << i;
                }
            }
        }
        unsigned small_cut = 0;
        bool rejected = false;
        for (unsigned set = 1; set < limit; ++set) {
            int vertex = std::countr_zero(set);
            unsigned rest = set & (set-1);
            interaction[set] = interaction[rest] + 2*(std::popcount(rest & first[vertex])
                                                     + std::popcount(rest & second[vertex]));
            boundary[set] = boundary[rest] + 3-2*std::popcount(rest & adjacent[vertex]);
            if (boundary[set] <= 2) small_cut = set;
            int excess = base[set]-interaction[set];
            if (excess < 0) {
                std::printf("%d %u %d\n", index, set, excess);
                rejected = true;
                break;
            }
        }
        if (!rejected && small_cut) std::printf("%d %u 0\n", index, small_cut);
    }
}
