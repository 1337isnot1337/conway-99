// Complete induced high-vertex graph census for fixed empty-root packings.
// Only necessary degree and common-neighbor upper bounds are imposed.
#include <algorithm>
#include <array>
#include <bit>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

using Clock = std::chrono::steady_clock;

struct Deadline {};

struct Search {
    int id, k;
    std::array<unsigned, 10> masks{}, adjacency{};
    std::array<std::array<int, 6>, 10> root_counts{};
    std::array<std::array<int, 10>, 10> overlap{};
    std::vector<std::pair<int, int>> edges;
    std::array<std::uint64_t, 31> histogram{};
    std::uint64_t nodes = 0, graphs = 0, rejected_inclusions = 0;
    Clock::time_point deadline;

    Search(int identifier, std::vector<unsigned> input, Clock::time_point stop)
        : id(identifier), k(static_cast<int>(input.size())), deadline(stop) {
        if (k > 10) throw std::runtime_error("more than ten high vertices");
        for (int a = 0; a < k; ++a) {
            masks[a] = input[a];
            if (masks[a] >= 64 || std::popcount(masks[a]) < 3)
                throw std::runtime_error("invalid high mask");
            for (int b = 0; b < a; ++b) {
                overlap[a][b] = overlap[b][a] = std::popcount(masks[a] & masks[b]);
                if (overlap[a][b] > 2) throw std::runtime_error("invalid outside pair overlap");
                if (overlap[a][b] <= 1) edges.emplace_back(b, a);
            }
        }
        for (int i = 0; i < 6; ++i) for (int j = 0; j < i; ++j) {
            int common = 0;
            for (int a = 0; a < k; ++a) common += ((masks[a] >> i) & (masks[a] >> j) & 1u);
            if (common > 2) throw std::runtime_error("invalid root pair quota");
        }
        // Edges sharing a root site consume a matching slot immediately.
        std::sort(edges.begin(), edges.end(), [&](auto first, auto second) {
            int r1 = overlap[first.first][first.second], r2 = overlap[second.first][second.second];
            return r1 != r2 ? r1 > r2 : first < second;
        });
    }

    bool pair_valid(int a, int b) const {
        if (a == b) return true;
        int common = overlap[a][b] + std::popcount(adjacency[a] & adjacency[b]);
        int cap = ((adjacency[a] >> b) & 1u) ? 1 : 2;
        return common <= cap;
    }

    bool add(int a, int b) {
        if (std::popcount(adjacency[a]) + 1 > 14 - std::popcount(masks[a]) ||
            std::popcount(adjacency[b]) + 1 > 14 - std::popcount(masks[b])) return false;
        for (int i = 0; i < 6; ++i) {
            if (root_counts[a][i] + int((masks[b] >> i) & 1u) > (((masks[a] >> i) & 1u) ? 1 : 2)) return false;
            if (root_counts[b][i] + int((masks[a] >> i) & 1u) > (((masks[b] >> i) & 1u) ? 1 : 2)) return false;
        }
        adjacency[a] |= 1u << b;
        adjacency[b] |= 1u << a;
        for (int c = 0; c < k; ++c) if (!pair_valid(a, c) || !pair_valid(b, c)) {
            adjacency[a] &= ~(1u << b);
            adjacency[b] &= ~(1u << a);
            return false;
        }
        for (int i = 0; i < 6; ++i) {
            root_counts[a][i] += (masks[b] >> i) & 1u;
            root_counts[b][i] += (masks[a] >> i) & 1u;
        }
        return true;
    }

    void remove(int a, int b) {
        adjacency[a] &= ~(1u << b);
        adjacency[b] &= ~(1u << a);
        for (int i = 0; i < 6; ++i) {
            root_counts[a][i] -= (masks[b] >> i) & 1u;
            root_counts[b][i] -= (masks[a] >> i) & 1u;
        }
    }

    void search(std::size_t next, int chosen) {
        ++nodes;
        if ((nodes & 4095u) == 0 && Clock::now() >= deadline) throw Deadline{};
        if (next == edges.size()) {
            ++graphs;
            ++histogram[chosen];
            return;
        }
        auto [a, b] = edges[next];
        if (add(a, b)) {
            search(next + 1, chosen + 1);
            remove(a, b);
        } else ++rejected_inclusions;
        search(next + 1, chosen);
    }

    void write(std::ostream& stream, bool complete) const {
        stream << "{\"atom_orbit\":" << id << ",\"high_vertices\":" << k
               << ",\"eligible_edges\":" << edges.size()
               << ",\"complete\":" << (complete ? "true" : "false")
               << ",\"graphs\":" << graphs << ",\"visited_nodes\":" << nodes
               << ",\"rejected_inclusions\":" << rejected_inclusions << ",\"edge_histogram\":[";
        for (std::size_t e = 0; e <= edges.size(); ++e) {
            if (e) stream << ',';
            stream << histogram[e];
        }
        stream << "]}";
    }
};

int main(int argc, char** argv) {
    if (argc != 4) return 2;
    std::ifstream input(argv[1]);
    std::ofstream output(argv[2]);
    double seconds = std::stod(argv[3]);
    if (!input || !output || seconds <= 0 || seconds > 60) return 2;
    int records;
    input >> records;
    if (records != 249) return 2;
    const auto started = Clock::now();
    const auto deadline = started + std::chrono::duration_cast<Clock::duration>(std::chrono::duration<double>(seconds));
    bool complete = true;
    int completed = 0;
    std::uint64_t graphs = 0, nodes = 0;
    output << "{\"records\":[";
    for (int r = 0; r < records; ++r) {
        int id, k;
        input >> id >> k;
        if (!input || id != r || k < 0 || k > 10) return 2;
        std::vector<unsigned> masks(k);
        for (auto& mask : masks) input >> mask;
        if (!input) return 2;
        Search search(id, masks, deadline);
        bool finished = true;
        try { search.search(0, 0); }
        catch (const Deadline&) { finished = false; complete = false; }
        if (r) output << ',';
        search.write(output, finished);
        output.flush();
        graphs += search.graphs;
        nodes += search.nodes;
        if (!finished) break;
        ++completed;
    }
    output << "],\"complete\":" << (complete ? "true" : "false")
           << ",\"completed_atom_orbits\":" << completed << ",\"graphs\":" << graphs
           << ",\"visited_nodes\":" << nodes << ",\"seconds\":"
           << std::chrono::duration<double>(Clock::now() - started).count() << "}\n";
    return complete ? 0 : 3;
}
