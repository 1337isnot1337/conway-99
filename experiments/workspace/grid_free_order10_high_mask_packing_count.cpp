// Count pair-capacity packings of all >=3-neighbor classes on six sites.
// This program stores no atom list and makes no outside-adjacency choice.

#include <array>
#include <chrono>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
using Clock = std::chrono::steady_clock;
constexpr std::uint64_t weighted_subset_bound = 15159780;

void require(bool value, const char* message) {
    if (!value) throw std::runtime_error(message);
}

int bits(unsigned value) { return __builtin_popcount(value); }

std::uint16_t pair_mask(unsigned mask) {
    unsigned result = 0;
    int at = 0;
    for (int i = 0; i < 6; ++i) {
        for (int j = i+1; j < 6; ++j, ++at) {
            if ((mask & (1U << i)) && (mask & (1U << j))) result |= 1U << at;
        }
    }
    require(at == 15, "pair coordinate count");
    return static_cast<std::uint16_t>(result);
}

struct Census {
    const std::vector<std::uint16_t>& masks;
    Clock::time_point deadline;
    bool bounded;
    bool timed_out = false;
    std::uint64_t nodes = 0;
    std::uint64_t candidate_tests = 0;
    std::uint64_t rejected_candidates = 0;
    std::array<std::uint64_t, 11> population{};
    std::array<std::uint64_t, 31> pair_consumption{};

    bool visit(std::size_t first, std::uint16_t once, std::uint16_t twice, int size) {
        require(size <= 10, "population exceeds total pair capacity");
        require((twice & once) == twice, "twice must be contained in once");
        const int used = bits(once)+bits(twice);
        require(used >= 3*size && used <= 30, "pair consumption invariant");
        ++nodes;
        ++population[static_cast<std::size_t>(size)];
        ++pair_consumption[static_cast<std::size_t>(used)];
        require(nodes <= weighted_subset_bound, "weighted subset upper bound");
        if (bounded && (nodes & 4095U) == 0 && Clock::now() >= deadline) {
            timed_out = true;
            return false;
        }
        for (std::size_t i = first; i < masks.size(); ++i) {
            ++candidate_tests;
            const std::uint16_t support = masks[i];
            if ((support & twice) != 0) {
                ++rejected_candidates;
                continue;
            }
            const auto new_once = static_cast<std::uint16_t>(once | support);
            const auto new_twice = static_cast<std::uint16_t>(twice | (once & support));
            if (!visit(i+1, new_once, new_twice, size+1)) return false;
        }
        return true;
    }
};

std::array<std::uint64_t, 11> literal_control(const std::vector<std::uint16_t>& masks) {
    require(masks.size() == 12, "tiny control size");
    std::array<std::uint64_t, 11> result{};
    for (unsigned selected = 0; selected < (1U << 12); ++selected) {
        bool valid = true;
        for (int pair = 0; pair < 15; ++pair) {
            int used = 0;
            for (int i = 0; i < 12; ++i) {
                if ((selected & (1U << i)) && (masks[static_cast<std::size_t>(i)] & (1U << pair))) ++used;
            }
            if (used > 2) valid = false;
        }
        if (valid) {
            const int size = bits(selected);
            require(size <= 10, "tiny population bound");
            ++result[static_cast<std::size_t>(size)];
        }
    }
    return result;
}

template <typename Range> void array_json(const Range& values) {
    std::cout << '[';
    bool first = true;
    for (auto value : values) {
        if (!first) std::cout << ',';
        first = false;
        std::cout << value;
    }
    std::cout << ']';
}
}  // namespace

int main(int argc, char** argv) {
    try {
        require(argc == 2, "one integer deadline argument required");
        const int seconds = std::stoi(argv[1]);
        require(seconds > 0 && seconds <= 10, "maximum count deadline is ten seconds");
        const auto started = Clock::now();
        std::vector<unsigned> high;
        std::vector<std::uint16_t> supports;
        for (unsigned mask = 0; mask < 64; ++mask) {
            if (bits(mask) < 3) continue;
            high.push_back(mask);
            supports.push_back(pair_mask(mask));
            require(bits(supports.back()) == bits(mask)*(bits(mask)-1)/2, "pair-mask weight");
        }
        require(high.size() == 42, "complete high-mask domain");
        const std::vector<std::uint16_t> tiny(supports.begin(), supports.begin()+12);
        Census control{tiny, Clock::time_point{}, false};
        require(control.visit(0, 0, 0, 0), "unbounded tiny control finished");
        require(control.population == literal_control(tiny), "tiny literal quota comparison");
        Census census{supports, started+std::chrono::seconds(seconds), true};
        const bool complete = census.visit(0, 0, 0, 0);
        require(complete == !census.timed_out, "completion status");
        std::uint64_t total = 0, consumption_total = 0;
        for (auto value : census.population) total += value;
        for (auto value : census.pair_consumption) consumption_total += value;
        require(total == census.nodes && consumption_total == census.nodes, "histogram totals");
        if (complete) require(census.nodes == 1+census.candidate_tests-census.rejected_candidates,
                              "every accepted transition creates exactly one child");
        const double elapsed = std::chrono::duration<double>(Clock::now()-started).count();
        std::cout << "{\"complete\":" << (complete ? "true" : "false")
                  << ",\"timed_out\":" << (census.timed_out ? "true" : "false")
                  << ",\"requested_seconds\":" << seconds
                  << ",\"elapsed_seconds\":" << std::setprecision(17) << elapsed
                  << ",\"high_masks\":";
        array_json(high);
        std::cout << ",\"pair_masks\":";
        array_json(supports);
        std::cout << ",\"pair_quotas\":[2,2,2,2,2,2,2,2,2,2,2,2,2,2,2]"
                  << ",\"packings_visited\":" << census.nodes
                  << ",\"candidate_tests\":" << census.candidate_tests
                  << ",\"rejected_candidates\":" << census.rejected_candidates
                  << ",\"population_size_counts\":";
        array_json(census.population);
        std::cout << ",\"pair_consumption_counts\":";
        array_json(census.pair_consumption);
        std::cout << ",\"tiny_control_subsets\":4096,\"tiny_control_population_counts\":";
        array_json(control.population);
        std::cout << ",\"empty_packing_included\":true,\"atom_list_stored\":false,"
                     "\"outside_adjacency_imposed\":false,\"symmetry_quotient_used\":false}\n";
        return 0;
    } catch (const std::exception& problem) {
        std::cerr << "packing count error: " << problem.what() << '\n';
        return 2;
    }
}
