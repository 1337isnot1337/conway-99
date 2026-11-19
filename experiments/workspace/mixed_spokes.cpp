// Exact Schur-complement search for signed four-point matching templates.
#include <algorithm>
#include <array>
#include <bit>
#include <cassert>
#include <cstdint>
#include <iostream>
#include <numeric>
#include <vector>
#include <boost/multiprecision/cpp_int.hpp>
using namespace std;
using Wide = __int128;
using DoubleWide = boost::multiprecision::int256_t;

struct Prefix {
    // Four high characters and up to ten low characters. Every stored
    // entry is a minor; Hadamard gives (75 sqrt(14))^14 < 2^115.
    Wide d[14]{}, factor[14][14]{};
    int pivot[14]{}, zero[14]{}, rank = 0, nullity = 0;

    static Wide update(Wide a, Wide b, Wide c, Wide d, Wide previous) {
        Wide x, y, numerator;
        if (!__builtin_mul_overflow(a, b, &x) && !__builtin_mul_overflow(c, d, &y)
            && !__builtin_sub_overflow(x, y, &numerator))
            return numerator / previous;
        return static_cast<Wide>((DoubleWide(a)*b - DoubleWide(c)*d) / previous);
    }

    bool append(int n, const int* row) {
        Wide v[14]{};
        copy(row, row+n+1, v);
        for (int r = 0; r < rank; ++r) {
            int p = pivot[r];
            Wide previous = r ? d[r-1] : 1, x = v[p];
            auto apply = [&](int h) { v[h] = update(d[r], v[h], x, factor[r][h], previous); };
            for (int t = r+1; t < rank; ++t) apply(pivot[t]);
            for (int t = 0; t < nullity; ++t) if (zero[t] > p) apply(zero[t]);
            v[n] = update(d[r], v[n], x, x, previous);
            factor[r][n] = x;
        }
        if (v[n] < 0) return false;
        for (int t = 0; t < nullity; ++t) if (v[zero[t]]) return false;
        if (!v[n]) zero[nullity++] = n;
        else { pivot[rank] = n; d[rank++] = v[n]; }
        return true;
    }
};

// A target character pulls back to one signed character in each disjoint
// source square. A zero code denotes an absent contact. The code 4 denotes
// the diagonal spoke contact produced by eliminating a near-axis difference.
struct Column { int j, character; array<int,5> pullback{}; };
using Images = array<int,3>;
using Domains = array<array<unsigned,5>,5>;

array<Images,24> actions() {
    array<Images,24> result{};
    array<int,4> p{0,1,2,3};
    int k = 0;
    do {
        for (unsigned a=1; a<=3; ++a) for (unsigned b=1; b<=3; ++b) {
            int inner = 0;
            for (unsigned x=0; x<4; ++x)
                inner += (popcount(x & a) + popcount(unsigned(p[x]) & b)) % 2 ? -1 : 1;
            if (inner) result[k][b-1] = inner > 0 ? int(a) : -int(a);
        }
        ++k;
    } while (next_permutation(p.begin(), p.end()));
    return result;
}

int gram(const Column& a, const Column& b, bool positive) {
    int value = 0;
    if (a.character == b.character) {
        if (!a.character && a.j != b.j) value = positive ? -16 : -9;
        if (a.j == b.j) value = a.character == 2 ? (positive ? 40 : 75) : (positive ? 64 : 36);
    }
    const array<int,3> weights = positive ? array<int,3>{5,6,10} : array<int,3>{5,6,3};
    for (int i=0; i<5; ++i) {
        int x=a.pullback[i], y=b.pullback[i];
        if (!x || !y || (x==4 && y==4)) continue;
        if (x==4 || y==4) {
            int z = x==4 ? y : x;
            if (abs(z)==2) value += (positive ? 4 : -3) * (z>0 ? 1 : -1);
        } else if (abs(x)==abs(y))
            value -= weights[abs(x)-1] * ((x>0)==(y>0) ? 1 : -1);
    }
    return value;
}

struct Search {
    array<Images,24> perms = actions();
    Domains domain;
    vector<Column> cols;
    array<vector<array<int,2>>,5> options;
    array<int,5> high{}, order{0,1,2,3,4};
    array<int,14> selected{};
    array<vector<signed char>,2> grams;
    array<uint64_t,5> counts{};

    explicit Search(const Domains& input) : domain(input) {}

    void columns(int j, int i, array<Column,3>& col) {
        if (i==5) {
            if (options[j].empty()) { high[j] = cols.size(); cols.push_back(col[0]); }
            else assert(cols[high[j]].pullback == col[0].pullback);
            int n=cols.size();
            options[j].push_back({n,n+1});
            cols.push_back(col[1]); cols.push_back(col[2]);
            return;
        }
        if (i==j) { col[1].pullback[i]=4; columns(j,i+1,col); return; }
        for (unsigned h=domain[i][j]; h; h&=h-1) {
            auto image=perms[countr_zero(h)];
            for (int k=0;k<3;++k) col[k].pullback[i]=image[k];
            columns(j,i+1,col);
        }
    }

    bool add(array<Prefix,2>& state, int n, int id) {
        selected[n]=id;
        for (int k=0;k<2;++k) {
            int row[14]{};
            for (int t=0;t<=n;++t) row[t]=grams[k][size_t(id)*cols.size()+selected[t]];
            if (!state[k].append(n,row)) return false;
        }
        return true;
    }

    void visit(int depth, const array<Prefix,2>& parent) {
        int n=4+2*depth;
        for (auto option : options[order[depth]]) {
            auto state=parent;
            if (!add(state,n,option[0]) || !add(state,n+1,option[1])) continue;
            ++counts[depth];
            if (depth<4) visit(depth+1,state);
        }
    }

    void run() {
        for (int j=0; j<5; ++j) {
            array<Column,3> col{{{j,0},{j,1},{j,2}}};
            columns(j,0,col);
        }
        stable_sort(order.begin(),order.end(),[&](int a,int b){return options[a].size()<options[b].size();});
        // First test only the distinguished signs. These columns do not
        // depend on any remaining free bijection.
        for (bool positive : {true,false}) {
            Prefix test{};
            for (int j=0;j<5;++j) {
                int row[5]{};
                for (int i=0;i<=j;++i) row[i]=gram(cols[high[i]],cols[high[j]],positive);
                if (!test.append(j,row)) return;
            }
        }
        size_t size=cols.size();
        for (int k=0;k<2;++k) {
            grams[k].resize(size*size);
            for (size_t i=0;i<size;++i) for (size_t j=0;j<=i;++j) {
                int v=gram(cols[i],cols[j],bool(k));
                assert(abs(v)<=120);
                grams[k][i*size+j]=grams[k][j*size+i]=v;
            }
        }
        array<Prefix,2> state{};
        for (int j=0;j<4;++j) { bool ok=add(state,j,high[j]); assert(ok); }
        visit(0,state);
    }
};

int main() {
    Domains domain{};
    int templates=0;
    array<uint64_t,5> totals{};
    while (cin >> domain[0][0]) {
        for (int i=1;i<25;++i)
            if (!(cin >> domain[i/5][i%5])) return 1;
        Search search(domain); search.run();
        ++templates;
        for (int i=0;i<5;++i) totals[i]+=search.counts[i];
    }
    cout << templates << " templates; retained prefixes";
    for (auto n:totals) cout << ' ' << n;
    cout << '\n';
    return 0;
}
