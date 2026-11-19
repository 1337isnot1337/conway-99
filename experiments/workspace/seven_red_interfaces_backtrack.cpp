// Direct finite interface census.  No SAT/CNF or spectral assumptions.
// All root matchings are identity; every other rook isomorphism is tested
// against the visible off-diagonal inequalities A^2+A <= 2.
#include <algorithm>
#include <array>
#include <bit>
#include <cassert>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <numeric>
#include <string>
#include <vector>

using Perm = std::array<int, 9>;
using Word = std::uint64_t;
using Clock = std::chrono::steady_clock;

bool rook(int a, int b) {
    return a != b && (a / 3 == b / 3 || a % 3 == b % 3);
}

struct Maps {
    std::vector<Perm> allowed;
    std::array<int, 11> inverse{};
    bool triangle[11][11][11]{};
    int identity = -1, automorphisms = 0;
    Maps() {
        Perm p; std::iota(p.begin(), p.end(), 0);
        do {
            bool ok = true;
            for (int x = 0; x < 9 && ok; ++x)
                for (int y = x + 1; y < 9; ++y)
                    if (rook(x, y) != rook(p[x], p[y])) { ok = false; break; }
            if (!ok) continue;
            ++automorphisms;
            bool permitted = true;
            for (int x = 0; x < 9; ++x) if (rook(x, p[x])) permitted = false;
            if (permitted) allowed.push_back(p);
        } while (std::next_permutation(p.begin(), p.end()));
        assert(automorphisms == 72 && allowed.size() == 11);
        for (int a = 0; a < 11; ++a) {
            Perm inv;
            for (int x = 0; x < 9; ++x) inv[allowed[a][x]] = x;
            auto found = std::find(allowed.begin(), allowed.end(), inv);
            assert(found != allowed.end()); inverse[a] = int(found - allowed.begin());
            bool same = true;
            for (int x = 0; x < 9; ++x) same &= allowed[a][x] == x;
            if (same) identity = a;
        }
        assert(identity >= 0);
        for (int a = 0; a < 11; ++a) for (int b = 0; b < 11; ++b)
            for (int c = 0; c < 11; ++c) {
                bool ok = true;
                for (int x = 0; x < 9; ++x)
                    if (rook(x, allowed[c][allowed[b][allowed[a][x]]])) ok = false;
                triangle[a][b][c] = ok;
            }
    }
};

struct Search {
    const Maps& maps;
    int bases, order;
    std::array<Word, 54> adjacency{};
    int chosen[6][6];
    std::vector<std::array<int, 2>> edges;
    std::vector<int> labels;
    std::vector<std::vector<int>> solutions;
    std::array<std::uint64_t, 11> visits{}, attempts{}, rejected{};
    std::uint64_t total_nodes = 0;
    Clock::time_point deadline;
    bool interrupted = false, stop_on_solution = false, found = false;

    Search(const Maps& m, int b, Clock::time_point end): maps(m), bases(b), order(9*b), deadline(end) {
        for (auto& row : chosen) for (int& value : row) value = -1;
        for (int i = 0; i < bases; ++i)
            for (int x = 0; x < 9; ++x) for (int y = 0; y < 9; ++y)
                if (rook(x, y)) adjacency[9*i+x] |= Word(1) << (9*i+y);
        for (int j = 1; j < bases; ++j) {
            insert(0, j, maps.identity);
            for (int i = 1; i < j; ++i) edges.push_back({i, j});
        }
        labels.assign(edges.size(), -1);
    }

    void insert(int i, int j, int a) {
        assert(chosen[i][j] == -1 && chosen[j][i] == -1);
        chosen[i][j] = a; chosen[j][i] = maps.inverse[a];
        for (int x = 0; x < 9; ++x) {
            int u = 9*i+x, v = 9*j+maps.allowed[a][x];
            adjacency[u] |= Word(1) << v; adjacency[v] |= Word(1) << u;
        }
    }

    void erase(int i, int j, int a) {
        for (int x = 0; x < 9; ++x) {
            int u = 9*i+x, v = 9*j+maps.allowed[a][x];
            adjacency[u] &= ~(Word(1) << v); adjacency[v] &= ~(Word(1) << u);
        }
        chosen[i][j] = chosen[j][i] = -1;
    }

    bool visible_ok(int i, int j) const {
        // Only rows belonging to these two bases changed.  All other
        // pair products retain the previously checked value.
        for (int u = 0; u < order; ++u) {
            if (u/9 != i && u/9 != j) continue;
            for (int v = 0; v < order; ++v) {
                if (v/9 == u/9) continue;
                if ((v/9 == i || v/9 == j) && v < u) continue;
                int value = std::popcount(adjacency[u] & adjacency[v])
                          + int(adjacency[u] >> v & Word(1));
                if (value > 2) return false;
            }
        }
        return true;
    }

    bool triangles_ok(int i, int j) const {
        for (int k = 0; k < bases; ++k) {
            if (k == i || k == j || chosen[j][k] < 0 || chosen[k][i] < 0) continue;
            if (!maps.triangle[chosen[i][j]][chosen[j][k]][chosen[k][i]]) return false;
        }
        return true;
    }

    void verify_complete() const {
        for (int u = 0; u < order; ++u) {
            assert(std::popcount(adjacency[u]) == bases+3);
            for (int v = u+1; v < order; ++v)
                assert(std::popcount(adjacency[u] & adjacency[v])
                       + int(adjacency[u] >> v & Word(1)) <= 2);
        }
        for (int i = 0; i < bases; ++i) for (int j = i+1; j < bases; ++j)
            assert(triangles_ok(i, j));
    }

    void visit(int depth) {
        if (interrupted || (found && stop_on_solution)) return;
        if ((++total_nodes & 255u) == 0 && Clock::now() >= deadline) {
            interrupted = true; return;
        }
        ++visits[depth];
        if (depth == int(edges.size())) {
            verify_complete(); solutions.push_back(labels); found = true; return;
        }
        int i = edges[depth][0], j = edges[depth][1];
        for (int a = 0; a < 11; ++a) {
            if (interrupted || (found && stop_on_solution)) break;
            ++attempts[depth]; insert(i, j, a); labels[depth] = a;
            bool good = visible_ok(i, j);
            if (good) {
                // This is an independent assertion, not an extra pruning
                // assumption: the visible bound implies every closed
                // triangle has a no-rook-neighbor holonomy.
                assert(triangles_ok(i, j)); visit(depth+1);
            } else ++rejected[depth];
            erase(i, j, a); labels[depth] = -1;
        }
    }
};

template<class T> void array_json(std::ostream& out, const T& data) {
    out << '['; bool first = true;
    for (const auto& x : data) { if (!first) out << ','; first = false; out << x; }
    out << ']';
}

void census_json(std::ostream& out, const Maps& maps, const Search& five, double seconds) {
    out << "{\"bases\":5,\"complete\":" << (five.interrupted ? "false" : "true")
        << ",\"status\":\"" << (five.interrupted ? "UNKNOWN" : "complete_local_census") << "\""
        << ",\"rook_automorphisms\":" << maps.automorphisms << ",\"allowed_maps\":[";
    for (int a = 0; a < 11; ++a) { if (a) out << ','; array_json(out, maps.allowed[a]); }
    out << "],\"edge_order\":[";
    for (unsigned i = 0; i < five.edges.size(); ++i) { if (i) out << ','; array_json(out, five.edges[i]); }
    out << "],\"assignments\":[";
    for (unsigned i = 0; i < five.solutions.size(); ++i) { if (i) out << ','; array_json(out, five.solutions[i]); }
    out << "],\"assignment_count\":" << five.solutions.size() << ",\"visits_by_depth\":";
    array_json(out, five.visits);
    out << ",\"attempts_by_depth\":"; array_json(out, five.attempts);
    out << ",\"rejected_by_depth\":"; array_json(out, five.rejected);
    out << ",\"seconds\":" << seconds << "}\n";
}

int main(int argc, char** argv) {
    assert(argc == 4);
    double budget = std::stod(argv[1]);
    auto begin = Clock::now();
    auto deadline = begin + std::chrono::duration_cast<Clock::duration>(std::chrono::duration<double>(budget));
    Maps maps;
    Search five(maps, 5, deadline);
    five.visit(0);
    double five_seconds = std::chrono::duration<double>(Clock::now()-begin).count();
    { std::ofstream output(argv[2]); assert(output); census_json(output, maps, five, five_seconds); }
    std::cout << "five-base assignments " << five.solutions.size()
              << "; complete " << !five.interrupted << "; seconds " << five_seconds << '\n' << std::flush;
    Search six(maps, 6, deadline); six.stop_on_solution = true;
    std::uint64_t seeds_completed = 0;
    if (!five.interrupted) {
        for (const auto& seed : five.solutions) {
            if (Clock::now() >= deadline) { six.interrupted = true; break; }
            for (unsigned k = 0; k < seed.size(); ++k) {
                auto edge = six.edges[k]; six.insert(edge[0], edge[1], seed[k]); six.labels[k] = seed[k];
            }
            six.visit(6);
            for (int k = int(seed.size())-1; k >= 0; --k) {
                auto edge = six.edges[k]; six.erase(edge[0], edge[1], seed[k]); six.labels[k] = -1;
            }
            if (six.interrupted || six.found) break;
            ++seeds_completed;
        }
    } else six.interrupted = true;
    bool complete = !six.interrupted && !six.found && seeds_completed == five.solutions.size();
    std::ofstream output(argv[3]); assert(output);
    output << "{\"bases\":6,\"complete\":" << (complete ? "true" : "false")
           << ",\"status\":\"" << (six.found ? "local_witness" : complete ? "exhaustive_no_local_assignment" : "UNKNOWN")
           << "\",\"five_base_seeds\":" << five.solutions.size()
           << ",\"seeds_completed\":" << seeds_completed << ",\"visits_by_depth\":";
    array_json(output, six.visits);
    output << ",\"attempts_by_depth\":"; array_json(output, six.attempts);
    output << ",\"rejected_by_depth\":"; array_json(output, six.rejected);
    output << ",\"witnesses\":[";
    for (unsigned i = 0; i < six.solutions.size(); ++i) { if (i) output << ','; array_json(output, six.solutions[i]); }
    double elapsed = std::chrono::duration<double>(Clock::now()-begin).count();
    output << "],\"seconds\":" << elapsed << "}\n";
    std::cout << "six-base status " << (six.found ? "local_witness" : complete ? "exhaustive_no_local_assignment" : "UNKNOWN")
              << "; seeds " << seeds_completed << "; seconds " << elapsed << '\n';
}
