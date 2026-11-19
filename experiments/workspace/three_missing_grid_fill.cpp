// Complete the 44 far vertices opposite a central grid with three missing cells.
#include <algorithm>
#include <array>
#include <bit>
#include <cassert>
#include <cstdint>
#include <iostream>
#include <map>
#include <utility>
#include <vector>

using Mask = std::uint64_t;
using Graph = std::array<Mask, 44>;
using Permutation = std::array<int, 4>;
using Edge = std::pair<int, int>;
using Edges = std::vector<Edge>;
using Choices = std::vector<Edges>;
using Case = std::array<std::array<int, 4>, 10>;

constexpr int missing = 3;
constexpr Mask peripheral_grid_points = ((Mask{1} << 40)-1) ^ ((Mask{1} << 12)-1);
constexpr int opposite[3][4] = {{1,0,3,2}, {2,3,0,1}, {3,2,1,0}};

std::vector<Permutation> permutations;
std::array<int, 24> inverse;
std::array<std::array<int, 3>, 10> neighbors;
std::map<std::pair<int, int>, Choices> off_diagonal;
std::map<int, Choices> diagonal;

void initialize() {
    Permutation p = {0,1,2,3};
    do {
        permutations.push_back(p);
    } while (std::next_permutation(p.begin(), p.end()));
    for (int j = 0; j < 24; ++j) {
        Permutation back;
        for (int i = 0; i < 4; ++i) back[permutations[j][i]] = i;
        inverse[j] = std::find(permutations.begin(), permutations.end(), back)-permutations.begin();
    }

    // A coordinate occurs once in each of the three missing cells.
    // Index the simple 3-by-3 bipartite graphs, and the graphs within a triple.
    for (int mask = 0; mask < 512; ++mask) {
        Edges edges;
        int rows = 0, cols = 0;
        for (int i = 0; i < 3; ++i) for (int j = 0; j < 3; ++j) {
            if (mask & (1 << (3*i+j))) {
                edges.emplace_back(i,j);
                rows += 1 << (2*i);
                cols += 1 << (2*j);
            }
        }
        off_diagonal[{rows,cols}].push_back(edges);
    }
    for (int mask = 0; mask < 8; ++mask) {
        Edges edges;
        int degree = 0, index = 0;
        for (int i = 0; i < 3; ++i) for (int j = i+1; j < 3; ++j) {
            if (mask & (1 << index)) {
                edges.emplace_back(i,j);
                degree += (1 << (2*i)) + (1 << (2*j));
            }
            ++index;
        }
        diagonal[degree].push_back(edges);
    }
}

void add_edge(Graph& graph, int x, int y) {
    graph[x] |= Mask{1} << y;
    graph[y] |= Mask{1} << x;
}

int used_quota(const Graph& graph, int x, int y) {
    return std::popcount(graph[x] & graph[y]) + ((graph[x] >> y) & 1);
}

bool permits_edge(const Graph& graph, int x, int y) {
    if (std::popcount(graph[x] & graph[y]) >= 2) return false;
    for (auto [a,b] : {Edge{x,y}, Edge{y,x}}) {
        for (Mask row = graph[a]; row; row &= row-1) {
            if (used_quota(graph, b, std::countr_zero(row)) >= 2) return false;
        }
    }
    return true;
}

void fill_blocks(int id, const Graph& graph, const std::vector<Choices>& blocks,
                 std::size_t position, std::array<int, 3> internal) {
    if (position == blocks.size()) {
        std::cout << id;
        for (Mask row : graph) std::cout << ' ' << row;
        std::cout << '\n';
        return;
    }
    for (const Edges& edges : blocks[position]) {
        auto next = graph;
        auto count = internal;
        bool possible = true;
        for (auto [a,b] : edges) {
            if ((a/4 == b/4 && ++count[a/4] > 2) || !permits_edge(next,a,b)) {
                possible = false;
                break;
            }
            add_edge(next,a,b);
        }
        if (possible) fill_blocks(id,next,blocks,position+1,count);
    }
}

void missing_union(int id, const Graph& graph) {
    int need[12][4] = {};
    for (int t = 0; t < 12; ++t) {
        for (int x = 0; x < 4; ++x) need[t][x] = 1+(x == opposite[0][t%4]);
        for (Mask row = graph[t] & peripheral_grid_points; row; row &= row-1) {
            if (--need[t][std::countr_zero(row)%4] < 0) return;
        }
    }
    std::vector<Choices> blocks;
    for (int a = 0; a < 4; ++a) for (int b = a; b < 4; ++b) {
        int left = 0, right = 0;
        for (int i = 0; i < 3; ++i) {
            left += need[4*i+a][b] << (2*i);
            right += need[4*i+b][a] << (2*i);
        }
        const auto& patterns = a == b ? diagonal[left] : off_diagonal[{left,right}];
        Choices choices;
        for (const auto& pattern : patterns) {
            Edges edges;
            for (auto [i,j] : pattern) {
                int x = 4*i+a, y = 4*j+b;
                if (!permits_edge(graph,x,y)) break;
                edges.emplace_back(x,y);
            }
            if (edges.size() == pattern.size()) choices.push_back(edges);
        }
        if (choices.empty()) return;
        if (choices.size() > 1 || !choices.front().empty()) blocks.push_back(std::move(choices));
    }
    std::sort(blocks.begin(), blocks.end(), [](const auto& a, const auto& b) {
        return a.size() < b.size();
    });
    fill_blocks(id,graph,blocks,0,{});
}

void fill_maps(int id, const Graph& graph, const std::vector<Choices>& slots, std::size_t position) {
    if (position == slots.size()) {
        missing_union(id,graph);
        return;
    }
    for (const Edges& edges : slots[position]) {
        auto next = graph;
        bool possible = true;
        for (auto [a,b] : edges) {
            if (!permits_edge(next,a,b)) {
                possible = false;
                break;
            }
            add_edge(next,a,b);
        }
        if (possible) fill_maps(id,next,slots,position+1);
    }
}

void complete(int id, const Case& state) {
    Graph graph{};
    for (int i = 0; i < 10; ++i) for (int x = 0; x < 4; ++x) add_edge(graph,4*i+x,40+x);
    for (int i = missing; i <= 10; ++i) {
        int color = i == 10 ? 0 : state[i][0];
        for (int x = 0; x < 4; ++x) for (int y = x+1; y < 4; ++y) {
            if (y != opposite[color][x]) add_edge(graph,4*i+x,4*i+y);
        }
    }
    for (int i = missing; i < 10; ++i) for (int k = 0; k < 3; ++k) {
        int j = neighbors[i][k];
        if (j <= i) continue;
        const auto& p = permutations[state[i][1+k]];
        for (int x = 0; x < 4; ++x) add_edge(graph,4*i+x,4*j+p[x]);
    }
    for (int i = 0; i < 44; ++i) for (int j = 0; j < i; ++j) {
        if (used_quota(graph,i,j) > 2) return;
    }

    std::vector<Choices> slots;
    for (int i = missing; i < 10; ++i) for (int x = 0; x < 4; ++x) {
        std::vector<int> targets = {x,opposite[0][x],opposite[state[i][0]][x]};
        std::vector<int> sources;
        for (int k = 0; k < 3; ++k) {
            int j = neighbors[i][k];
            if (j < missing) {
                sources.push_back(j);
            } else {
                int y = permutations[inverse[state[i][1+k]]][x];
                auto it = std::find(targets.begin(),targets.end(),y);
                assert(it != targets.end());
                targets.erase(it);
            }
        }
        if (sources.empty()) continue;
        std::sort(targets.begin(),targets.end());
        Choices choices;
        do {
            Edges edges;
            for (std::size_t j = 0; j < sources.size(); ++j) {
                edges.emplace_back(4*sources[j]+x,4*i+targets[j]);
            }
            choices.push_back(std::move(edges));
        } while (std::next_permutation(targets.begin(),targets.end()));
        slots.push_back(std::move(choices));
    }
    std::sort(slots.begin(), slots.end(), [](const auto& a, const auto& b) {
        return a.size() < b.size();
    });
    fill_maps(id,graph,slots,0);
}

int main() {
    std::ios::sync_with_stdio(false);
    initialize();
    int labels[10];
    for (int& label : labels) {
        int a,b;
        if (!(std::cin >> a >> b)) return 1;
        label = (1 << a) | (1 << b);
    }
    for (int i = 0; i < 10; ++i) {
        int k = 0;
        for (int j = 0; j < 10; ++j) if (!(labels[i] & labels[j])) neighbors[i][k++] = j;
        assert(k == 3);
    }
    int id;
    while (std::cin >> id) {
        Case state{};
        for (int i = missing; i < 10; ++i) for (auto& entry : state[i]) {
            if (!(std::cin >> entry)) return 1;
        }
        complete(id,state);
    }
    return 0;
}
