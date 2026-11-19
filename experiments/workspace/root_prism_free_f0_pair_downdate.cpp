// Complete exact two-column classification from compressed component-pair types.
// All products are signed int64; the bound certificate is checked by the driver
// before compilation/execution. No SAT call and no full-column pair export.

#include <algorithm>
#include <array>
#include <cassert>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <string>
#include <utility>
#include <vector>

using i64 = std::int64_t;

struct Type {
    int id, reverse, p[3], q[3], intersection[3], local, motif;
    i64 aa, cc, ac, multiplicity;
    int p_code, q_code, overlap;
};

void put_u32(std::ofstream& out, std::uint32_t x) {
    for (int k = 0; k < 4; ++k) out.put(static_cast<char>((x >> (8*k)) & 255));
}

template <std::size_t N>
void array_json(const std::array<i64,N>& a) {
    std::cout << '[';
    for (std::size_t i = 0; i < N; ++i) {
        if (i) std::cout << ',';
        std::cout << a[i];
    }
    std::cout << ']';
}

int main(int argc, char** argv) {
    assert(argc == 4);
    const auto started = std::chrono::steady_clock::now();
    const double seconds = std::stod(argv[3]);
    assert(seconds > 0 && seconds <= 120);
    auto elapsed = [&]() {
        return std::chrono::duration<double>(std::chrono::steady_clock::now()-started).count();
    };
    std::ifstream input(argv[1]);
    std::ofstream predicates(argv[2],std::ios::binary);
    assert(input && predicates);
    int size;
    i64 D, minimum_n, maximum_n;
    input >> size >> D >> minimum_n >> maximum_n;
    assert(size == 36134 && D == 4577040 && minimum_n == 2240036 && maximum_n == 3242772);
    std::vector<Type> types(size);
    std::array<std::array<std::vector<int>,27>,27> groups;
    i64 component_pairs = 0;
    for (int i = 0; i < size; ++i) {
        Type& a = types[i];
        input >> a.id >> a.reverse;
        for (int& x : a.p) input >> x;
        for (int& x : a.q) input >> x;
        input >> a.aa >> a.cc >> a.ac;
        for (int& x : a.intersection) input >> x;
        input >> a.local >> a.motif >> a.multiplicity;
        assert(input && a.id == i && a.reverse >= 0 && a.reverse < size);
        assert(a.p[0]+a.p[1]+a.p[2] == 3 && a.q[0]+a.q[1]+a.q[2] == 3);
        for (int x : a.p) assert(x >= 0 && x <= 2);
        for (int x : a.q) assert(x >= 0 && x <= 2);
        for (int x : a.intersection) assert(x >= 0 && x <= 2);
        assert(a.aa > 0 && a.aa <= 858218 && a.cc > 0 && a.cc <= 858218);
        assert(a.ac >= -342896 && a.ac <= 858218);
        assert((a.local == 0 || a.local == 1) && (a.motif == 0 || a.motif == 1));
        assert(a.multiplicity > 0 && a.multiplicity <= 230400);
        a.p_code = 9*a.p[0]+3*a.p[1]+a.p[2];
        a.q_code = 9*a.q[0]+3*a.q[1]+a.q[2];
        a.overlap = a.intersection[0]+a.intersection[1]+a.intersection[2];
        assert(a.overlap <= 3);
        groups[a.p_code][a.q_code].push_back(i);
        component_pairs += a.multiplicity;
    }
    std::string tail;
    assert(!(input >> tail) && component_pairs == 230400);
    for (const Type& a : types) {
        const Type& r = types[a.reverse];
        assert(r.reverse == a.id && r.multiplicity == a.multiplicity);
        assert(r.aa == a.cc && r.cc == a.aa && r.ac == a.ac);
        for (int f = 0; f < 3; ++f)
            assert(r.p[f] == a.q[f] && r.q[f] == a.p[f] && r.intersection[f] == a.intersection[f]);
        assert(r.local == a.local && r.motif == a.motif);
    }
    std::array<i64,32> all_weight{}, negative_weight{}, all_types{}, negative_types{};
    i64 combinations = 0, weighted = 0, self_weight = 0, self_types = 0;
    i64 duplicate_negative_weight = 0, canonical_new = 0, expanded_new_types = 0, new_unordered = 0;
    i64 minimum_cross = std::numeric_limits<i64>::max(), maximum_cross = std::numeric_limits<i64>::min();
    i64 minimum_det = std::numeric_limits<i64>::max(), maximum_det = std::numeric_limits<i64>::min();
    i64 minimum_new_det = 0;
    std::pair<int,int> minimum_new_ids{-1,-1};
    std::vector<std::pair<int,int>> samples;
    bool complete = true;
    int groups_finished = 0;
    for (int p = 0; p < 27 && complete; ++p) for (int q = 0; q < 27 && complete; ++q) {
        if (groups[p][q].empty()) continue;
        assert(!groups[26-p][26-q].empty());
        for (int ia : groups[p][q]) {
            if (elapsed() >= seconds) { complete = false; break; }
            const Type& a = types[ia];
            i64 norm_p = 0, norm_q = 0, dot = 0;
            for (int f = 0; f < 3; ++f) {
                norm_p += (a.p[f]-1)*(a.p[f]-1);
                norm_q += (a.q[f]-1)*(a.q[f]-1);
                dot += (a.p[f]-1)*(a.q[f]-1);
            }
            assert((norm_p == 0 || norm_p == 2) && (norm_q == 0 || norm_q == 2) && dot >= -2 && dot <= 2);
            for (int ib : groups[26-p][26-q]) {
                const Type& b = types[ib];
                const i64 nh = 2*(a.aa+b.aa)-D/60-(D/36)*norm_p;
                const i64 nk = 2*(a.cc+b.cc)-D/60-(D/36)*norm_q;
                const i64 cross = 2*(a.ac+b.ac)-D/60-(D/36)*dot;
                assert(nh >= minimum_n && nh <= maximum_n && nk >= minimum_n && nk <= maximum_n);
                assert(cross >= -1702148 && cross <= 3610868);
                assert(cross*cross <= nh*nk);
                const i64 determinant = (D-nh)*(D-nk)-cross*cross;
                const i64 weight = a.multiplicity*b.multiplicity;
                ++combinations;
                weighted += weight;
                minimum_cross = std::min(minimum_cross,cross);
                maximum_cross = std::max(maximum_cross,cross);
                minimum_det = std::min(minimum_det,determinant);
                maximum_det = std::max(maximum_det,determinant);
                if (a.overlap == 3 && b.overlap == 3) {
                    ++self_types;
                    self_weight += weight;
                    if (determinant < 0) duplicate_negative_weight += weight;
                    continue;
                }
                const bool same_component = a.overlap == 3 || b.overlap == 3;
                const bool triple_overlap = a.overlap+b.overlap >= 3;
                const bool local_quota_one = a.local || b.local;
                const bool cross_quota_one = (a.intersection[0]*b.intersection[0]+a.intersection[1]*b.intersection[1]
                                               +a.intersection[2]*b.intersection[2]) > 0;
                const bool motif = a.motif || b.motif;
                const int mask = same_component+2*triple_overlap+4*local_quota_one+8*cross_quota_one+16*motif;
                ++all_types[mask];
                all_weight[mask] += weight;
                if (determinant >= 0) continue;
                ++negative_types[mask];
                negative_weight[mask] += weight;
                if (mask != 0) continue;
                if (determinant < minimum_new_det) {
                    minimum_new_det = determinant;
                    minimum_new_ids = {ia,ib};
                }
                if (std::make_pair(ia,ib) > std::make_pair(a.reverse,b.reverse)) continue;
                const i64 orbit = (ia == a.reverse && ib == b.reverse) ? 1 : 2;
                assert((orbit*weight)%2 == 0);
                ++canonical_new;
                expanded_new_types += orbit;
                new_unordered += orbit*weight/2;
                put_u32(predicates,ia);
                put_u32(predicates,ib);
                if (samples.size() < 8) samples.push_back({ia,ib});
            }
        }
        if (complete) ++groups_finished;
        predicates.flush();
        assert(predicates);
        std::cout << std::setprecision(17)
                  << "{\"stage\":\"group\",\"p_code\":" << p << ",\"q_code\":" << q
                  << ",\"completed\":" << (complete ? "true" : "false")
                  << ",\"type_combinations\":" << combinations << ",\"weighted_ordered_pairs\":" << weighted
                  << ",\"self_ordered_pairs\":" << self_weight
                  << ",\"new_negative_ordered_pairs\":" << negative_weight[0]
                  << ",\"canonical_new_predicates\":" << canonical_new
                  << ",\"elapsed_seconds\":" << elapsed() << "}" << std::endl;
    }
    if (complete) {
        assert(combinations == 33578176 && weighted == 1534132224 && self_weight == 39168);
        assert(expanded_new_types == negative_types[0] && 2*new_unordered == negative_weight[0]);
        i64 count = self_weight;
        for (int m = 0; m < 32; ++m) {
            count += all_weight[m];
            assert(all_weight[m]%2 == 0 && negative_weight[m]%2 == 0);
        }
        assert(count == weighted);
    }
    std::cout << "{\"status\":\"" << (complete ? "COMPLETE" : "INCOMPLETE") << "\",\"groups_finished\":" << groups_finished
              << ",\"type_combinations\":" << combinations << ",\"weighted_ordered_pairs\":" << weighted
              << ",\"self_type_combinations\":" << self_types << ",\"self_ordered_pairs\":" << self_weight
              << ",\"negative_duplicate_self_columns\":" << duplicate_negative_weight
              << ",\"all_nonself_ordered_counts_by_mask\":";
    array_json(all_weight);
    std::cout << ",\"negative_nonself_ordered_counts_by_mask\":";
    array_json(negative_weight);
    std::cout << ",\"all_nonself_type_counts_by_mask\":";
    array_json(all_types);
    std::cout << ",\"negative_nonself_type_counts_by_mask\":";
    array_json(negative_types);
    std::cout << ",\"canonical_new_predicates\":" << canonical_new
              << ",\"new_unordered_full_column_pairs\":" << new_unordered
              << ",\"observed_cross_numerator_range\":[" << minimum_cross << ',' << maximum_cross << ']'
              << ",\"observed_determinant_range\":[" << minimum_det << ',' << maximum_det << ']'
              << ",\"minimum_new_determinant\":" << minimum_new_det
              << ",\"minimum_new_type_ids\":[" << minimum_new_ids.first << ',' << minimum_new_ids.second << ']'
              << ",\"first_new_predicate_samples\": [";
    for (std::size_t i = 0; i < samples.size(); ++i) {
        if (i) std::cout << ',';
        std::cout << '[' << samples[i].first << ',' << samples[i].second << ']';
    }
    std::cout << "],\"elapsed_seconds\":" << elapsed() << "}" << std::endl;
    return complete ? 0 : 2;
}
