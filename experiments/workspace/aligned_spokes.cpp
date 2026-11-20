// Test the twenty matchings between spokes of two full axes when all
// matchings respect the partition by the sign of the full axis.
#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>
#include <iostream>
#include <limits>
#include <set>
#include <utility>
#include <vector>
using namespace std;

using Matrix = array<array<int, 5>, 5>;
using Integer = int64_t;

Matrix canonical(const Matrix& p) {
    Matrix best = p;
    array<int, 5> perm{0, 1, 2, 3, 4};
    do {
        for (int sign : {-1, 1}) for (bool transpose : {false, true}) {
            Matrix image{};
            for (int i = 0; i < 5; ++i) for (int j = 0; j < 5; ++j)
                image[i][j] = sign * (transpose ? p[perm[j]][perm[i]] : p[perm[i]][perm[j]]);
            best = min(best, image);
        }
    } while (next_permutation(perm.begin(), perm.end()));
    return best;
}

void balanced_arrays(Matrix& p, int i, int& count, set<Matrix>& representatives) {
    if (i == 5) {
        for (int j = 0; j < 5; ++j) {
            int sum = 0;
            for (auto& row : p) sum += row[j];
            if (sum) return;
        }
        ++count;
        representatives.insert(canonical(p));
        return;
    }
    for (int a = 0; a < 5; ++a) for (int b = 0; b < a; ++b) {
        if (a == i || b == i) continue;
        for (int j = 0; j < 5; ++j)
            p[i][j] = j == i ? 0 : (j == a || j == b ? 1 : -1);
        balanced_arrays(p, i + 1, count, representatives);
    }
}

// Fraction-free symmetric elimination, extended by one row at a time.
// Each saved element is a bordered minor of the positive pivot block.
// Intermediate products use 128 bits. Check divisibility and the range of
// the resulting minors before saving them.
struct PsdPrefix {
    Integer diagonal[10]{}, multiplier[10][10]{};
    int pivot[10]{}, zero[10]{}, rank = 0, nullity = 0;

    static Integer reduce(Integer a, Integer b, Integer c, Integer d, Integer divisor) {
        __int128 value = __int128(a) * b - __int128(c) * d;
        assert(value % divisor == 0);
        value /= divisor;
        assert(value >= numeric_limits<Integer>::min() && value <= numeric_limits<Integer>::max());
        return static_cast<Integer>(value);
    }

    bool append(int n, const int* row) {
        Integer v[10]{};
        copy(row, row + n + 1, v);
        for (int r = 0; r < rank; ++r) {
            int p = pivot[r];
            Integer previous = r ? diagonal[r - 1] : 1;
            Integer x = v[p];
            auto update = [&](int h) {
                v[h] = reduce(diagonal[r], v[h], x, multiplier[r][h], previous);
            };
            for (int t = r + 1; t < rank; ++t) update(pivot[t]);
            for (int t = 0; t < nullity; ++t)
                if (zero[t] > p) update(zero[t]);
            v[n] = reduce(diagonal[r], v[n], x, x, previous);
            multiplier[r][n] = x;
        }
        if (v[n] < 0) return false;
        for (int t = 0; t < nullity; ++t)
            if (v[zero[t]] != 0) return false;
        if (v[n] == 0) zero[nullity++] = n;
        else {
            pivot[rank] = n;
            diagonal[rank++] = v[n];
        }
        return true;
    }
};

bool high_sector_passes(const Matrix& p) {
    PsdPrefix state{};
    for (int i = 0; i < 5; ++i) {
        int row[5]{};
        for (int j = 0; j <= i; ++j) {
            row[j] = i == j ? 9 : 0;
            for (int k = 0; k < 5; ++k) row[j] -= p[i][k] * p[j][k];
        }
        if (!state.append(i, row)) return false;
    }
    return true;
}

struct Contact {
    // For each of the five independent three-point blocks on the left,
    // specify the contacted coordinate and its incidence sign.
    array<int, 5> coordinate{}, sign{};
};

Contact contact(const Matrix& p, int j, int bit, int code) {
    Contact c;
    for (int i = 0, offset = 0; i < 5; ++i) {
        if (i == j) {
            c.coordinate[i] = 2;
            c.sign[i] = 1;
        } else {
            c.coordinate[i] = bit ^ int(p[i][j] < 0);
            c.sign[i] = (code >> (2 * offset + bit) & 1) ? -1 : 1;
            ++offset;
        }
    }
    return c;
}

int schur(const Contact& x, const Contact& y, int initial) {
    int value = initial;
    for (int i = 0; i < 5; ++i)
        value -= (x.coordinate[i] == y.coordinate[i] ? 4 : -1) * x.sign[i] * y.sign[i];
    return value;
}

using PairBlock = array<signed char, 4>;
static PairBlock blocks[5][5][256][256];

void prepare(const Matrix& p) {
    Contact contacts[5][256][2];
    for (int j = 0; j < 5; ++j) for (int m = 0; m < 256; ++m)
        for (int s = 0; s < 2; ++s) contacts[j][m][s] = contact(p, j, s, m);
    for (int j = 0; j < 5; ++j) for (int k = 0; k <= j; ++k)
        for (int m = 0; m < 256; ++m) for (int n = 0; n < 256; ++n)
            for (int s = 0; s < 2; ++s) for (int t = 0; t < 2; ++t) {
                int initial = j == k ? (s == t ? 30 : 10) : 0;
                blocks[j][k][m][n][2*s+t] =
                    schur(contacts[j][m][s], contacts[k][n][t], initial);
            }
}

void extend(int j, array<int, 5>& chosen, const PsdPrefix& prefix, array<int64_t, 5>& counts) {
    for (int m = 0; m < 256; ++m) {
        // Switch the sign at every site of group i. With group 0 fixed this
        // independently normalizes the four positive-bit contacts of Y_0.
        if (j == 0 && (m & 0x55)) continue;
        PsdPrefix next = prefix;
        bool ok = true;
        for (int s = 0; s < 2 && ok; ++s) {
            int row[10]{};
            for (int k = 0; k < j; ++k) for (int t = 0; t < 2; ++t)
                row[2*k+t] = blocks[j][k][m][chosen[k]][2*s+t];
            for (int t = 0; t <= s; ++t)
                row[2*j+t] = blocks[j][j][m][m][2*s+t];
            ok = next.append(2*j+s, row);
        }
        if (!ok) continue;
        ++counts[j];
        chosen[j] = m;
        if (j < 4) extend(j + 1, chosen, next, counts);
    }
}

int main() {
    Matrix initial{};
    set<Matrix> representatives;
    int count = 0, tested = 0;
    balanced_arrays(initial, 0, count, representatives);
    assert(count == 216 && representatives.size() == 4);
    for (const auto& p : representatives) {
        if (!high_sector_passes(p)) continue;
        ++tested;
        prepare(p);
        array<int, 5> chosen{};
        array<int64_t, 5> counts{};
        extend(0, chosen, PsdPrefix{}, counts);
        cout << "PSD prefixes";
        for (auto n : counts) cout << ' ' << n;
        cout << '\n';
        assert(counts.back() == 0);
    }
    assert(tested == 2);
    cout << "216 balanced arrays, four orbits, zero aligned interfaces.\n";
}
