// Enumerate the signed near vertices once the central matchings fix coordinates.
#pragma once

#include <algorithm>
#include <array>
#include <bit>
#include <cstdint>
#include <iostream>
#include <vector>

namespace central_grid {

using Mask = std::uint64_t;
using Graph = std::array<Mask, 54>;
using Case = std::array<std::array<int, 4>, 10>;
inline constexpr int opposite[3][4] = {{1,0,3,2}, {2,3,0,1}, {3,2,1,0}};

inline int used_quota(const Graph& graph, int x, int y) {
    return std::popcount(graph[x] & graph[y]) + ((graph[x] >> y) & 1);
}

class AxisSigns {
    using Signs = std::array<Mask, 2>;
    using Domains = std::array<std::vector<Signs>, 5>;
    std::array<Mask, 5> incident{};
    std::array<int, 10> labels{};
    Domains initial, after_maps;
    std::array<Mask,4> coordinate_masks{};

    void make_choices(int a, const Case& state, int missing,
                      const std::array<int,4>& cells, int k, Mask positive) {
        if (k == 4) {
            for (int x = 0; x < 4; ++x) {
                // Each central coordinate has two common neighbors with each sign.
                if (std::popcount(positive & coordinate_masks[x]) != 2) return;
            }
            initial[a].push_back({positive, incident[a]^positive});
            return;
        }
        int i = cells[k];
        for (int color = 0; color < 3; ++color) {
            if (i >= missing && color == state[i][0]) continue;
            Mask pair = 1 | (1 << opposite[color][0]);
            make_choices(a, state, missing, cells, k+1, positive | (pair << (4*i)));
            // The two names of an axis can be interchanged on the whole graph.
            if (k) make_choices(a, state, missing, cells, k+1, positive | ((15^pair) << (4*i)));
        }
    }

    bool filter(const Graph& graph, const Domains& before, Domains& after) const {
        std::array<Mask, 40> saturated{};
        for (int i = 0; i < 40; ++i) for (int j = 0; j < i; ++j) {
            if ((labels[i/4] & labels[j/4]) && used_quota(graph,i,j) >= 2) {
                saturated[i] |= Mask{1} << j;
                saturated[j] |= Mask{1} << i;
            }
        }
        for (int a = 0; a < 5; ++a) {
            after[a].clear();
            for (const Signs& signs : before[a]) {
                bool possible = true;
                for (int i = 0; i < 40; ++i) {
                    bool member = (incident[a] >> i) & 1;
                    // A member already uses one quota unit for each sign, from
                    // its near edge or the common near mate on this axis.
                    int limit = member ? 1 : 2;
                    bool negative = !((signs[0] >> i) & 1);
                    if (std::popcount(graph[i] & signs[0]) > limit ||
                        std::popcount(graph[i] & signs[1]) > limit ||
                        (member && (saturated[i] & signs[negative]))) {
                        possible = false;
                        break;
                    }
                }
                if (possible) after[a].push_back(signs);
            }
            if (after[a].empty()) return false;
        }
        return true;
    }

    template<class Visitor>
    void select(const Domains& choices, const std::array<int,5>& order,
                int k, std::array<Mask,5>& selected, Visitor& visit) const {
        if (k == 5) {
            visit(selected);
            return;
        }
        int a = order[k];
        for (const Signs& signs : choices[a]) {
            bool possible = true;
            for (int j = 0; j < k; ++j) {
                // In the unique cell on these axes all four sign pairs occur.
                if (std::popcount(signs[0] & selected[order[j]]) != 1) {
                    possible = false;
                    break;
                }
            }
            if (possible) {
                selected[a] = signs[0];
                select(choices,order,k+1,selected,visit);
            }
        }
    }

    template<class Visitor>
    void each(const Domains& choices, Visitor visit) const {
        std::array<int,5> order = {0,1,2,3,4};
        std::sort(order.begin(), order.end(), [&](int a, int b) {
            return choices[a].size() < choices[b].size();
        });
        std::array<Mask,5> selected{};
        select(choices,order,0,selected,visit);
    }

public:
    std::uint64_t far_graphs = 0, separate_axes = 0, labelings = 0;

    void prepare(const std::array<int,10>& pairs, const Case& state, int missing,
                 const std::array<Mask,4>& coordinates) {
        coordinate_masks = coordinates;
        labels = pairs;
        for (int a = 0; a < 5; ++a) {
            incident[a] = 0;
            std::array<int,4> cells{};
            int k = 0;
            for (int i = 0; i < 10; ++i) if (labels[i] & (1 << a)) {
                cells[k++] = i;
                incident[a] |= Mask{15} << (4*i);
            }
            initial[a].clear();
            make_choices(a,state,missing,cells,0,0);
        }
    }

    bool permits_maps(const Graph& graph) {
        return filter(graph,initial,after_maps);
    }

    void complete(int id, const Graph& graph) {
        ++far_graphs;
        Domains remaining;
        if (!filter(graph,after_maps,remaining)) return;
        ++separate_axes;
        each(remaining,[&](const auto& selected) { write(id,graph,selected); });
    }

    void write(int id, const Graph& graph, const std::array<Mask,5>& selected) {
        ++labelings;
        std::cout << id;
        for (int i = 0; i < 44; ++i) std::cout << ' ' << (graph[i] & ((Mask{1} << 44)-1));
        for (Mask positive : selected) std::cout << ' ' << positive;
        std::cout << '\n';
    }

    template<class Visitor>
    void with_near_vertices(const Graph& base, Visitor visit) {
        each(after_maps,[&](const std::array<Mask,5>& selected) {
            Graph graph = base;
            for (int a = 0; a < 5; ++a) {
                int positive = 44+2*a;
                graph[positive] = selected[a] | (Mask{1} << (positive+1));
                graph[positive+1] = (incident[a]^selected[a]) | (Mask{1} << positive);
                for (Mask row = incident[a]; row; row &= row-1) {
                    int i = std::countr_zero(row);
                    int sign = ((selected[a] >> i) & 1) ? positive : positive+1;
                    graph[i] |= Mask{1} << sign;
                }
            }
            visit(graph,selected);
        });
    }

};

}  // namespace central_grid
