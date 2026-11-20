// Complete the 44 far vertices opposite a grid after transporting its coordinates.
#include "central_grid_axes.hpp"
#include <algorithm>
#include <array>
#include <bit>
#include <cassert>
#include <cstdint>
#include <iostream>
#include <fstream>
#include <string>
#include <map>
#include <utility>
#include <vector>

using central_grid::Mask;
using central_grid::Graph;
using central_grid::Case;
using central_grid::opposite;
using central_grid::used_quota;
using Permutation = std::array<int, 4>;
using Edge = std::pair<int, int>;
using Edges = std::vector<Edge>;
using Choices = std::vector<Edges>;
constexpr int max_missing = 5;
int missing = 3;
bool signs_first = false;
bool four_cycle = false;
std::array<int,44> coordinate{};
std::array<Mask,4> coordinate_masks{};
std::array<std::array<int,max_missing>,4> coordinate_buckets{};
Mask peripheral_grid_points;
std::array<int,10> labels;
central_grid::AxisSigns near_axes;

std::vector<Permutation> permutations;
std::array<int, 24> inverse;
std::array<std::array<int, 3>, 10> neighbors;
std::map<std::pair<int, int>, Choices> off_diagonal;
std::map<int, Choices> diagonal;

// The four leading labels follow the missing cycle in cyclic order when
// deviations are nonzero. Fix site names within each cell by coordinate.
void set_coordinates(const std::array<int,4>& deviation) {
    coordinate_masks.fill(0);
    std::array<int,4> sizes{};
    for (int i = 0; i < 11; ++i) {
        int site = 0;
        for (int x = 0; x < 4; ++x) {
            int count = 1;
            if (four_cycle && i < 4) count += (i % 2 ? -1 : 1) * deviation[x];
            for (int k = 0; k < count; ++k) {
                int v = 4*i + site++;
                coordinate[v] = x;
                if (i < 10) coordinate_masks[x] |= Mask{1} << v;
                if (i < missing) coordinate_buckets[x][sizes[x]++] = v;
            }
        }
        assert(site == 4);
    }
    for (int n : sizes) assert(n == missing);
}

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

    // Each coordinate class has the same total number of missing vertices.
    int internal_pairs = missing*(missing-1)/2;
    for (int mask = 0; mask < (1 << internal_pairs); ++mask) {
        Edges edges;
        int degree = 0, index = 0;
        for (int i = 0; i < missing; ++i) for (int j = i+1; j < missing; ++j) {
            if (mask & (1 << index)) {
                edges.emplace_back(i,j);
                degree += (1 << (3*i)) + (1 << (3*j));
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

// Index only the bipartite degree margins that actually occur. This avoids
// constructing all 2^25 graphs on a five-by-five coordinate block.
const Choices& bipartite_graphs(int left, int right) {
    auto [it,fresh] = off_diagonal.try_emplace(std::pair{left,right});
    if (!fresh) return it->second;
    std::array<int,max_missing> remaining{};
    for (int j = 0; j < missing; ++j) remaining[j] = (right >> (3*j)) & 7;
    Edges chosen;
    auto extend = [&](auto&& self, int i) -> void {
        if (i == missing) {
            if (std::all_of(remaining.begin(), remaining.end(), [](int x) { return x == 0; }))
                it->second.push_back(chosen);
            return;
        }
        int degree = (left >> (3*i)) & 7;
        for (unsigned mask = 0; mask < (1u << missing); ++mask) {
            if (std::popcount(mask) != degree) continue;
            bool possible = true;
            for (int j = 0; j < missing; ++j) {
                int rest = remaining[j] - ((mask >> j) & 1);
                if (rest < 0 || rest > missing-i-1) possible = false;
            }
            if (!possible) continue;
            auto size = chosen.size();
            for (int j = 0; j < missing; ++j) if ((mask >> j) & 1) {
                --remaining[j];
                chosen.emplace_back(i,j);
            }
            self(self,i+1);
            for (int j = 0; j < missing; ++j) if ((mask >> j) & 1) ++remaining[j];
            chosen.resize(size);
        }
    };
    extend(extend,0);
    return it->second;
}

bool restrict_degrees = false;
std::array<std::array<bool,1 << (3*max_missing)>,11> degree_prefixes{};

bool read_degrees(const char* path) {
    std::ifstream input(path);
    for (auto& allowed : degree_prefixes) {
        int count;
        if (!(input >> count) || count < 1) return false;
        while (count--) {
            std::array<int,max_missing> full{};
            for (int j = 0; j < missing; ++j) {
                if (!(input >> full[j]) || full[j] < 0 || full[j] > 4) return false;
            }
            auto record = [&](auto&& self, int j, int code) -> void {
                if (j == missing) {
                    allowed[code] = true;
                    return;
                }
                for (int d = 0; d <= full[j]; ++d) self(self,j+1,code+(d << (3*j)));
            };
            record(record,0,0);
        }
    }
    return true;
}

bool degree_possible(int vertex, Mask row) {
    int code = 0;
    for (int i = 0; i < missing; ++i) {
        int value = std::popcount(row & (Mask{15} << (4*i)));
        code |= value << (3*i);
    }
    return degree_prefixes[vertex/4][code];
}

bool permits_edge(const Graph& graph, int x, int y) {
    if (restrict_degrees &&
        ((y < 4*missing && !degree_possible(x, graph[x] | (Mask{1} << y))) ||
         (x < 4*missing && !degree_possible(y, graph[y] | (Mask{1} << x))))) return false;
    if (std::popcount(graph[x] & graph[y]) >= 2) return false;
    for (auto [a,b] : {Edge{x,y}, Edge{y,x}}) {
        for (Mask row = graph[a]; row; row &= row-1) {
            if (used_quota(graph, b, std::countr_zero(row)) >= 2) return false;
        }
    }
    return true;
}

void fill_blocks(int id, const Graph& graph, const std::vector<Choices>& blocks,
                 std::size_t position, std::array<int,max_missing> internal,
                 const std::array<Mask,5>* signs = nullptr) {
    if (position == blocks.size()) {
        if (signs) {
            near_axes.write(id,graph,*signs);
            return;
        }
        if (missing >= 4) {
            near_axes.complete(id,graph);
            return;
        }
        std::cout << id;
        for (int i = 0; i < 44; ++i) std::cout << ' ' << graph[i];
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
        if (possible) fill_blocks(id,next,blocks,position+1,count,signs);
    }
}

void missing_union(int id, const Graph& graph) {
    if (four_cycle) {
        for (int i = 0; i < missing; ++i) {
            std::array<Mask,2> grids{};
            int k = 0;
            for (int j : neighbors[i]) if (j >= missing) grids[k++] = Mask{15} << (4*j);
            assert(k == 2);
            // Sites with the same coordinate in a cell are interchangeable.
            for (int v = 4*i+1; v < 4*i+4; ++v) if (coordinate[v-1] == coordinate[v]) {
                if ((graph[v-1] & grids[0]) == (graph[v] & grids[0]) &&
                    (graph[v-1] & grids[1]) > (graph[v] & grids[1])) return;
            }
        }
    }
    if (missing >= 4 && !four_cycle && !near_axes.permits_maps(graph)) return;
    int need[4*max_missing][4] = {};
    for (int t = 0; t < 4*missing; ++t) {
        for (int x = 0; x < 4; ++x) need[t][x] = 1+(x == opposite[0][coordinate[t]]);
        for (Mask row = graph[t] & peripheral_grid_points; row; row &= row-1) {
            if (--need[t][coordinate[std::countr_zero(row)]] < 0) return;
        }
    }
    std::vector<Choices> blocks;
    for (int a = 0; a < 4; ++a) for (int b = a; b < 4; ++b) {
        int left = 0, right = 0;
        for (int i = 0; i < missing; ++i) {
            left += need[coordinate_buckets[a][i]][b] << (3*i);
            right += need[coordinate_buckets[b][i]][a] << (3*i);
        }
        const auto& patterns = a == b ? diagonal[left] : bipartite_graphs(left,right);
        Choices choices;
        for (const auto& pattern : patterns) {
            Edges edges;
            for (auto [i,j] : pattern) {
                int x = coordinate_buckets[a][i], y = coordinate_buckets[b][j];
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
    if (four_cycle && !near_axes.permits_maps(graph)) return;
    if (!signs_first) {
        fill_blocks(id,graph,blocks,0,{});
        return;
    }
    near_axes.with_near_vertices(graph,[&](const Graph& signed_graph, const auto& signs) {
        std::vector<Choices> restricted;
        for (const auto& block : blocks) {
            Choices choices;
            for (const auto& pattern : block) {
                if (std::all_of(pattern.begin(),pattern.end(),[&](const Edge& e) {
                    return permits_edge(signed_graph,e.first,e.second);
                })) choices.push_back(pattern);
            }
            if (choices.empty()) return;
            restricted.push_back(std::move(choices));
        }
        std::sort(restricted.begin(), restricted.end(), [](const auto& a, const auto& b) {
            return a.size() < b.size();
        });
        fill_blocks(id,signed_graph,restricted,0,{},&signs);
    });
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
    if (missing >= 4) near_axes.prepare(labels,state,missing,coordinate_masks);
    Graph graph{};
    for (int i = 0; i < 10; ++i) for (int x = 0; x < 4; ++x) add_edge(graph,4*i+x,40+coordinate[4*i+x]);
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
                for (int v = 4*j; v < 4*j+4; ++v) if (coordinate[v] == x) sources.push_back(v);
            } else {
                int y = permutations[inverse[state[i][1+k]]][x];
                auto it = std::find(targets.begin(),targets.end(),y);
                assert(it != targets.end());
                targets.erase(it);
            }
        }
        assert(sources.size() == targets.size());
        if (sources.empty()) continue;
        std::sort(targets.begin(),targets.end());
        Choices choices;
        do {
            Edges edges;
            for (std::size_t j = 0; j < sources.size(); ++j) {
                edges.emplace_back(sources[j],4*i+targets[j]);
            }
            bool canonical = true;
            for (std::size_t k = 1; k < sources.size(); ++k) {
                int cell = sources[k]/4;
                if (sources[k-1]/4 != cell) continue;
                // Order equal-coordinate sites by their image in the first grid.
                auto first = std::find_if(neighbors[cell].begin(), neighbors[cell].end(),
                                          [](int j) { return j >= missing; });
                if (i == *first && targets[k-1] > targets[k]) canonical = false;
            }
            if (canonical) choices.push_back(std::move(edges));
        } while (std::next_permutation(targets.begin(),targets.end()));
        slots.push_back(std::move(choices));
    }
    std::sort(slots.begin(), slots.end(), [](const auto& a, const auto& b) {
        return a.size() < b.size();
    });
    fill_maps(id,graph,slots,0);
}

int main(int argc, char** argv) {
    if (argc > 1 && std::string(argv[argc-1]) == "--signs-first") {
        signs_first = true;
        --argc;
    }
    if (argc > 1 && std::string(argv[argc-1]) == "--four-cycle") {
        four_cycle = true;
        --argc;
    }
    if (argc > 3) return 1;
    if (argc >= 2) missing = std::stoi(argv[1]);
    if (missing < 3 || missing > max_missing) return 1;
    if (argc == 3) {
        if (!read_degrees(argv[2])) return 1;
        restrict_degrees = true;
    }
    peripheral_grid_points = ((Mask{1} << 40)-1) ^ ((Mask{1} << (4*missing))-1);
    std::ios::sync_with_stdio(false);
    initialize();

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
    std::vector<std::array<int,4>> profiles(1);
    if (four_cycle) {
        if (missing != 4 || labels[0] != 3 || labels[1] != 6 ||
            labels[2] != 12 || labels[3] != 9) return 1;
        profiles.clear();
        for (int a = -1; a <= 1; ++a) for (int b = -1; b <= 1; ++b)
            for (int c = -1; c <= 1; ++c) {
                int d = -a-b-c;
                if (d >= -1 && d <= 1) profiles.push_back({a,b,c,d});
            }
        assert(profiles.size() == 19);
    }
    int id;
    while (std::cin >> id) {
        Case state{};
        for (int i = missing; i < 10; ++i) for (auto& entry : state[i]) {
            if (!(std::cin >> entry)) return 1;
        }
        for (std::size_t j = 0; j < profiles.size(); ++j) {
            set_coordinates(profiles[j]);
            complete(id*profiles.size()+j,state);
        }
    }
    if (missing >= 4 && !signs_first) {
        std::cerr << "Far graphs " << near_axes.far_graphs << ", separately feasible axes "
                  << near_axes.separate_axes << ", simultaneous labelings " << near_axes.labelings << '\n';
    }
    return 0;
}
