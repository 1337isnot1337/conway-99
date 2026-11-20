// Exact edge-fiber bound for tree-normalized covers of K3,3.
// This tests a necessary condition for the common triangle system when
// seven all-red grids leave 36 vertices, each in two internal triangles.
// A surviving cover is only a partial combinatorial object, not an SRG.
#include <algorithm>
#include <array>
#include <bit>
#include <cassert>
#include <cstdlib>
#include <iostream>
#include <map>
#include <numeric>
#include <string>
#include <vector>

using Mask = unsigned;

struct Side {
    std::vector<Mask> fibers;
    std::vector<std::array<int, 3>> partitions;
    std::array<int, 12> occurrence{};
};

Side side_partitions(const std::vector<Mask>& neighbors, int sheets) {
    const int n = 3 * sheets;
    const Mask full = (1u << n) - 1;
    static const std::vector<Mask> choices = [&]() {
        std::vector<Mask> result;
        for (Mask subset = 0; subset <= full; ++subset)
            if (std::popcount(subset) == sheets) result.push_back(subset);
        return result;
    }();
    std::vector<Mask> possible;
    for (Mask subset : choices) {
        Mask united = 0;
        for (int v = 0; v < n; ++v)
            if (subset >> v & 1u) united |= neighbors[v];
        if (united == full) possible.push_back(subset);
    }
    std::vector<int> index(1u << n, -1);
    for (int i = 0; i < int(possible.size()); ++i) index[possible[i]] = i;
    Side result;
    std::vector<bool> used(possible.size());
    for (int i = 0; i < int(possible.size()); ++i) {
        for (int j = i + 1; j < int(possible.size()); ++j) {
            if (possible[i] & possible[j]) continue;
            int k = index[full ^ possible[i] ^ possible[j]];
            if (k <= j) continue;
            result.partitions.push_back({i, j, k});
            used[i] = used[j] = used[k] = true;
        }
    }
    for (int i = 0; i < int(possible.size()); ++i) {
        if (!used[i]) continue;
        result.fibers.push_back(possible[i]);
        for (int v = 0; v < n; ++v)
            if (possible[i] >> v & 1u) ++result.occurrence[v];
    }
    assert(!result.partitions.empty());
    return result;
}

std::vector<int> component_sizes(const std::vector<Mask>& left,
                                 const std::vector<Mask>& right) {
    int n = int(left.size());
    std::vector<bool> seen(2 * n);
    std::vector<int> sizes;
    for (int v = 0; v < 2 * n; ++v) {
        if (seen[v]) continue;
        std::vector<int> todo{v};
        seen[v] = true;
        for (unsigned pos = 0; pos < todo.size(); ++pos) {
            int u = todo[pos];
            Mask mask = u < n ? left[u] : right[u - n];
            int offset = u < n ? n : 0;
            for (int w = 0; w < n; ++w) {
                if (!(mask >> w & 1u) || seen[offset + w]) continue;
                seen[offset + w] = true;
                todo.push_back(offset + w);
            }
        }
        sizes.push_back(int(todo.size()));
    }
    std::sort(sizes.begin(), sizes.end());
    return sizes;
}

template<class T> void array_json(const T& data) {
    std::cout << '[';
    bool first = true;
    for (const auto& v : data) {
        if (!first) std::cout << ',';
        first = false;
        std::cout << v;
    }
    std::cout << ']';
}

int main(int argc, char** argv) {
    int sheets = 4;
    if (argc == 2) sheets = std::atoi(argv[1]);
    assert(sheets == 3 || sheets == 4);
    std::vector<std::vector<int>> permutations;
    std::vector<int> p(sheets);
    std::iota(p.begin(), p.end(), 0);
    do { permutations.push_back(p); }
    while (std::next_permutation(p.begin(), p.end()));
    int q = int(permutations.size());
    int n = 3 * sheets;
    std::map<std::vector<int>, int> components;
    std::map<int, int> bounds;
    int examined = 0;
    bool first_survivor = true;
    std::cout << "{\"sheets\":" << sheets << ",\"survivors\":[";
    for (int code = 0; code < q * q * q * q; ++code) {
        int current = code;
        std::array<int, 4> voltages;
        for (int i = 3; i >= 0; --i) {
            voltages[i] = current % q;
            current /= q;
        }
        std::vector<Mask> left(n), right(n);
        for (int i = 0; i < 3; ++i) for (int j = 0; j < 3; ++j) {
            const auto& perm = permutations[(i && j) ? voltages[2 * (i - 1) + j - 1] : 0];
            for (int sheet = 0; sheet < sheets; ++sheet) {
                int u = sheets * i + sheet, v = sheets * j + perm[sheet];
                left[u] |= 1u << v;
                right[v] |= 1u << u;
            }
        }
        for (int i = 0; i < n; ++i) {
            assert(std::popcount(left[i]) == 3 && std::popcount(right[i]) == 3);
        }
        auto sizes = component_sizes(left, right);
        ++components[sizes];
        ++examined;
        if (sizes.size() != 1) continue;
        Side a = side_partitions(left, sheets), b = side_partitions(right, sheets);
        int bound = 100000, edge_left = -1, edge_right = -1;
        for (int u = 0; u < n; ++u) for (int v = 0; v < n; ++v) {
            if (!(left[u] >> v & 1u)) continue;
            int count = a.occurrence[u] * b.occurrence[v];
            if (count < bound) {
                bound = count;
                edge_left = u;
                edge_right = v;
            }
        }
        assert(bound > 0);
        ++bounds[bound];
        // Three sheets need8 projections, four sheets need7. A shared
        // edge fiber would give two exterior vertices >=3 common neighbors.
        if (bound >= 11 - sheets) {
            if (!first_survivor) std::cout << ',';
            first_survivor = false;
            std::cout << "{\"voltages\":";
            array_json(voltages);
            std::cout << ",\"fiber_bound\":" << bound
                      << ",\"left_partitions\":" << a.partitions.size()
                      << ",\"right_partitions\":" << b.partitions.size()
                      << ",\"edge\":[" << edge_left << ',' << n + edge_right << "]}";
        }
        if (code % 10000 == 0)
            std::cerr << "examined " << code << " of " << q*q*q*q << '\n';
    }
    std::cout << "],\"complete\":true,\"normalized_covers\":" << examined
              << ",\"component_histogram\":[";
    bool first = true;
    for (const auto& [sizes, count] : components) {
        if (!first) std::cout << ',';
        first = false;
        std::cout << "{\"sizes\":";
        array_json(sizes);
        std::cout << ",\"count\":" << count << '}';
    }
    std::cout << "],\"connected_fiber_bound_histogram\":[";
    first = true;
    for (const auto& [bound, count] : bounds) {
        if (!first) std::cout << ',';
        first = false;
        std::cout << "{\"bound\":" << bound << ",\"count\":" << count << '}';
    }
    std::cout << "]}\n";
}
