// Exact exterior incidence for the six-grid common-witness configuration.
#include <algorithm>
#include <array>
#include <bit>
#include <cassert>
#include <cstdint>
#include <iostream>
#include <numeric>
#include <vector>

using Mask = std::uint64_t;
template<int N> using Graph = std::array<Mask, N>;

template<int N, int G>
class Incidence {
    static constexpr int columns = 1 + N*(N+1)/2;
    const Graph<N>& adjacency;
    const std::array<Mask, G>& grids;
    std::array<int, N> membership{};
    std::array<Mask, N> compatible{};
    std::array<Mask, 1 << G> available{};
    int index[N][N];
    std::array<int, columns> need{}, left{};
    std::array<std::vector<int>, columns> options;
    std::vector<std::vector<int>> covers;
    std::vector<Mask> supports;
    std::vector<int> value, trail;

    void add_signature(Mask selected) {
        // A selected point can see at most one other mark, and every point at most two.
        Mask once = 0, twice = 0;
        for (Mask bits = selected; bits; bits &= bits-1) {
            Mask neighbors = adjacency[std::countr_zero(bits)];
            if (neighbors & twice) return;
            twice |= neighbors & once;
            once |= neighbors;
        }
        if (twice & selected) return;
        // Two exterior vertices with the same three marks would have three common neighbors.
        assert(std::popcount(selected) >= 3);
        int var = static_cast<int>(supports.size());
        supports.push_back(selected);
        std::vector<int> hits{0};
        for (Mask bits = selected; bits; bits &= bits-1) {
            int i = std::countr_zero(bits);
            for (Mask tail = bits; tail; tail &= tail-1)
                hits.push_back(index[i][std::countr_zero(tail)]);
        }
        for (int col : hits) options[col].push_back(var);
        covers.push_back(std::move(hits));
    }

    void signatures(int occupied, Mask allowed, Mask selected) {
        constexpr int all = (1 << G)-1;
        if (occupied == all) {
            add_signature(selected);
            return;
        }
        int next = std::countr_zero(static_cast<unsigned>(all ^ occupied));
        for (Mask bits = grids[next] & allowed; bits; bits &= bits-1) {
            int i = std::countr_zero(bits);
            int filled = occupied | membership[i];
            signatures(filled, allowed & available[filled] & compatible[i], selected | (Mask(1) << i));
        }
    }

    bool assign(int var, int sign) {
        if (value[var] != -1) return value[var] == sign;
        trail.push_back(var);
        value[var] = sign;
        bool ok = true;
        for (int col : covers[var]) {
            --left[col];
            need[col] -= sign;
            if (need[col] < 0 || need[col] > left[col]) ok = false;
        }
        if (!ok || !sign) return ok;
        // Any incompatible second signature occurs in a marked-point column of the first.
        for (int col : covers[var]) {
            if (!col) continue;
            for (int other : options[col]) {
                if (other == var || value[other] == 0) continue;
                if (std::popcount(supports[var] & supports[other]) >= 3 && !assign(other, 0))
                    return false;
            }
        }
        return true;
    }

    void undo(std::size_t checkpoint) {
        while (trail.size() > checkpoint) {
            int var = trail.back();
            trail.pop_back();
            for (int col : covers[var]) {
                ++left[col];
                need[col] += value[var];
            }
            value[var] = -1;
        }
    }

public:
    Incidence(const Graph<N>& a, const std::array<Mask, G>& sets, int degree, int outside)
        : adjacency(a), grids(sets) {
        int col = 1;
        need[0] = outside;
        for (int i = 0; i < N; ++i) {
            for (int j = i; j < N; ++j) {
                int target = (i == j ? degree : 2 - int((a[i] >> j) & 1))
                             - std::popcount(a[i] & a[j]);
                assert(target >= 0);
                index[i][j] = index[j][i] = col;
                need[col++] = target;
                if (target) {
                    compatible[i] |= Mask(1) << j;
                    compatible[j] |= Mask(1) << i;
                }
            }
            for (int g = 0; g < G; ++g)
                if ((grids[g] >> i) & 1) membership[i] |= 1 << g;
            assert(membership[i] != 0);
        }
        for (int set = 0; set < (1 << G); ++set)
            for (int i = 0; i < N; ++i)
                if (!(membership[i] & set)) available[set] |= Mask(1) << i;
        signatures(0, available[0], 0);
        value.assign(supports.size(), -1);
        for (int i = 0; i < columns; ++i) left[i] = static_cast<int>(options[i].size());
    }

    bool feasible() {
        int best = -1;
        bool changed;
        do {
            changed = false;
            best = -1;
            int best_size = 1000000000;
            for (int col = 0; col < columns; ++col) {
                int k = need[col], n = left[col];
                if (k < 0 || k > n) return false;
                if (n == 0) continue;
                if (k == 0 || k == n) {
                    for (int var : options[col])
                        if (value[var] == -1 && !assign(var, k != 0)) return false;
                    changed = true;
                } else {
                    int size = std::min(k, n-k) == 1 ? n : n*(n-1)/2;
                    if (size < best_size) {
                        best = col;
                        best_size = size;
                    }
                }
            }
        } while (changed);
        if (best == -1) return true;

        // Branch on the first variable in the column with the less frequent value.
        int sign = need[best] <= left[best]-need[best];
        auto original = trail.size();
        for (int var : options[best]) {
            if (value[var] != -1) continue;
            auto checkpoint = trail.size();
            if (assign(var, sign) && feasible()) return true;
            undo(checkpoint);
            if (!assign(var, 1-sign)) break;
        }
        undo(original);
        return false;
    }
};

void positive_control() {
    // In the ordinary rook graph mark two rows and one column, or the transpose.
    // Both exterior vertices see three distinct marks, one in each chosen line.
    for (int first = 0; first < 3; ++first) for (int second = 0; second < 3; ++second)
    for (int transpose = 0; transpose < 2; ++transpose) {
        std::vector<int> points;
        std::array<Mask,3> grid{};
        for (int v = 0; v < 9; ++v) {
            int r = v/3, c = v%3;
            if (transpose) std::swap(r,c);
            if (r == first && c != second) continue;
            Mask bit = Mask(1) << points.size();
            if (r == (first+1)%3) grid[0] |= bit;
            if (r == (first+2)%3) grid[1] |= bit;
            if (c == second) grid[2] |= bit;
            points.push_back(v);
        }
        Graph<7> a{};
        for (int i = 0; i < 7; ++i) for (int j = 0; j < 7; ++j) {
            int x = points[i], y = points[j];
            if (i != j && (x/3 == y/3 || x%3 == y%3)) a[i] |= Mask(1) << j;
        }
        Incidence<7,3> test(a, grid, 4, 2);
        assert(test.feasible());
    }
    std::cout << "All 18 seven-point marked rook controls retain an exterior incidence.\n";
}

using Core = Graph<38>;
using Five = std::array<Mask,5>;

bool within_quotas(const Core& a, Mask active) {
    for (Mask bits = active; bits; bits &= bits-1) {
        int i = std::countr_zero(bits);
        if (std::popcount(a[i]) > 14) return false;
        for (Mask later = bits & (bits-1); later; later &= later-1) {
            int j = std::countr_zero(later);
            if (std::popcount(a[i] & a[j]) + int((a[i] >> j) & 1) > 2) return false;
        }
    }
    return true;
}

int main() {
    positive_control();
    std::array<Mask,6> grids;
    Five inner;
    for (auto& x : grids) std::cin >> x;
    for (auto& x : inner) std::cin >> x;
    std::array<std::vector<Core>,2> pages;
    for (int side = 0; side < 2; ++side) {
        int start = 28 + 5*side;
        for (int id = 0; id < 11520; ++id) {
            Core page{};
            for (int i = 0; i < 5; ++i) {
                Mask row;
                std::cin >> row;
                page[start+i] = row | (inner[i] << start);
                for (; row; row &= row-1) page[std::countr_zero(row)] |= Mask(1) << (start+i);
            }
            pages[side].push_back(page);
        }
    }

    int bases = 0, cases = 0;
    constexpr Mask initial = (Mask(1) << 28)-1;
    Core a{};
    while (std::cin >> a[0]) {
        for (int i = 1; i < 28; ++i) std::cin >> a[i];
        assert(std::cin);
        ++bases;
        std::array<std::vector<Core>,2> possible;
        for (int side = 0; side < 2; ++side) {
            Mask active = initial | (Mask(31) << (28+5*side));
            for (Core page : pages[side]) {
                for (int i = 0; i < 28; ++i) page[i] |= a[i];
                if (within_quotas(page, active)) possible[side].push_back(page);
            }
        }
        for (const auto& p : possible[0]) for (Core q : possible[1]) {
            for (int i = 0; i < 38; ++i) q[i] |= p[i];
            if (!within_quotas(q, (Mask(1) << 38)-1)) continue;
            ++cases;
            Incidence<38,6> test(q, grids, 14, 61);
            if (test.feasible()) {
                std::cerr << "An exterior incidence survived at base " << bases << '\n';
                return 1;
            }
        }
    }
    assert(bases == 117 && cases == 919143);
    std::cout << "117 marked bases, 919143 locally consistent six-grid cores, zero exterior incidences.\n";
}
