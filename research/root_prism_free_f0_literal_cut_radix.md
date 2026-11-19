# Exact signed-radix encoding of literal Boolean cuts

This package proves and tests an exact integer encoding of one inequality
\[
\sum_i c_i x_i\le r,\qquad x_i\in\{0,1\},
\]
where the coefficients and right side can exceed signed 64-bit range. It does not load or transport the original 4,416-row archive. The utility and controls use only V8 integer arithmetic; no native solver or native model validator was run.

## Definition

Let \(n\) be the number of nonzero terms. The utility accepts at most 480 binary variables and requires sorted, distinct literal IDs and canonical decimal strings for every coefficient and the right side. It rejects explicit zero terms.

Choose \(B=2^b\), with \(1\le b\le30\), and
\[
S_{\max}=\max\left(0,r-\sum_i\min(0,c_i)\right).
\]
Choose the smallest \(L\ge1\) such that
\[
\max\bigl(\max_i|c_i|,\ |r|,\ S_{\max}\bigr)<B^L.
\]
The default base is \(2^{30}\), and the default and maximum digit limit is 128. Exceeding the declared limit is an error. Exact powers of \(B\) require another digit.

Write the signed canonical digit expansions
\[
c_i=\sum_{j=0}^{L-1}d_{ij}B^j,\qquad
r=\sum_{j=0}^{L-1}e_jB^j,
\]
where \(d_{ij}=\operatorname{sgn}(c_i)\operatorname{digit}_j(|c_i|)\), and similarly for \(e_j\). In particular, each nonzero digit has the sign of its original integer and absolute value less than \(B\).

Introduce \(L\) integer slack digits \(0\le s_j\le B-1\), and \(L-1\) integer carries
\[
-(n+2)\le k_j\le n+2\quad(1\le j<L).
\]
The endpoints are the constants \(k_0=k_L=0\). For each limb impose
\[
\sum_i d_{ij}x_i+s_j+k_j-Bk_{j+1}=e_j.
\]

All native coefficients and domains are emitted as decimal strings. The original large integers occur only in proof metadata and arbitrary-precision calculations, never as coefficients of the emitted native rows.

## Soundness

Multiply limb \(j\) by \(B^j\) and sum. Every internal carry cancels:
\[
\sum_{j=0}^{L-1}B^j(k_j-Bk_{j+1})=k_0-B^Lk_L=0.
\]
Consequently,
\[
\sum_i c_i x_i+S=r,\qquad S=\sum_{j=0}^{L-1}s_jB^j\ge0.
\]
Thus every integral solution of the limb system satisfies the original inequality.

Both zero endpoint carries are necessary. Leaving a final carry free would replace equality by a condition allowing an unrecorded multiple of \(B^L\).

## Completeness and the carry bound

For a satisfying Boolean assignment set
\[
S=r-\sum_i c_i x_i.
\]
Then \(0\le S\le S_{\max}<B^L\), so \(S\) has unique ordinary base-\(B\) digits \(s_0,\ldots,s_{L-1}\).

Set \(t_j=\sum_i d_{ij}x_i+s_j-e_j\). The full integer equality gives \(\sum_jB^jt_j=0\). Therefore
\[
k_j=\frac{\sum_{h<j}B^ht_h}{B^j}
\]
is an integer: its numerator is the negative of a sum divisible by \(B^j\). It obeys \(k_0=k_L=0\) and
\[
k_{j+1}=\frac{t_j+k_j}{B}.
\]

Let \(C=n+2\). Assuming \(|k_j|\le C\), the recurrence numerator is at most
\[
n(B-1)+(B-1)+C+(B-1)=CB.
\]
It is at least
\[
-n(B-1)-C-(B-1)=-((n+1)B+1)\ge-CB.
\]
Hence \(|k_{j+1}|\le C\), beginning with \(k_0=0\).

This proves completeness. It also proves uniqueness of the auxiliary assignment for each satisfying Boolean input: the slack integer is fixed, its digits are unique, and the carry recurrence is unique. Constant rows, including negative constant rows, are covered without a special relaxation.

## Native arithmetic bounds

For a limb, the sum of absolute term bounds over the declared variable box is at most
\[
n(B-1)+(B-1)+C+BC=(2n+3)B+1.
\]
Including the absolute right side gives
\[
(2n+4)B.
\]
At \(n\le480\), \(B\le2^{30}\), this is at most
\[
964\cdot2^{30}=1{,}035{,}087{,}118{,}336<2^{40}.
\]
The expression's activity width is also below \(2^{41}\). The utility records the exact lower and upper activities for every emitted row and checks its own conservative bound.

The official OR-Tools v9.15 validator checks conservative linear-expression activities and variable-domain endpoints against stricter bounds than merely fitting individual coefficients in int64. It also checks a global sum of variable-domain magnitudes and widths. These are separate checks in the [official validator source](https://or-tools.github.io/docs/cpp/cp__model__checker_8cc_source.html), in ValidateIntegerVariable, PossibleIntegerOverflow and ValidateCpModel.

The new variables contribute exactly
\[
L(B-1)+2(n+2)(L-1)
\]
to that global domain sum. The utility checks the contribution of its own row. An integrating builder must add the contributions from every encoded row and from all pre-existing variables, then run the native validator on the actual serialized model. This package has not performed that full-model validation.

A three-limb row adds three equalities and five auxiliary variables. Twelve such rows add 36 equalities and 60 auxiliary variables. Selecting small original rows for direct native inequalities is an external builder decision and does not change this encoding.

## API and bindings

The source evaluates to an object exposing canonical, sha256 and bindSource. A caller hashes the exact frozen utility source independently, compares the hash to its expected source binding, and then uses bindSource(sourceSha256). Binding a string by itself is provenance metadata; it is not a substitute for checking which source bytes were evaluated.

The bound API is:

- encodeRow(row, options): construct the signed-digit rows and domains.
- verifyEncoding(encoding, expectedRow, expectedOptions): verify against an external original row. The original row is mandatory. Options can also be supplied externally.
- completeWitness(encoding, binaryValues): return the unique auxiliary assignment for a satisfying input, or ORIGINAL_ROW_VIOLATED with no witness.
- checkWitness(encoding, binaryValues, auxiliaryValues): check exact binary values, auxiliary domains, every limb equality and the original arbitrary-precision inequality.

The default options are binaryCount=480, binaryOffset=0, firstAux=480, baseBits=30 and maxDigits=128. A supplied firstAux must follow the binary ID interval. In an existing model, the integrating caller must additionally set firstAux to the actual next unused native ID.

The utility allocates slack IDs first, then internal carry IDs. next_aux_id is firstAux+2L-1. It rejects overlap with the binary interval and an allocation beyond the conservative signed-32-bit native ID limit. Each subsequent row must start at or after the preceding next_aux_id.

Each encoding binds its source SHA-256, canonical original-row SHA-256, exact original decimal coefficients, parameters, variable layout and arithmetic audit. The verifier does not call the encoder or its digit extraction function. It independently checks digit signs and ranges, variable layout and domains, then contracts the emitted equations with powers of \(B\). Original coefficients and the right side must reconstruct exactly, each slack coefficient must become \(B^j\), and every internal carry must cancel.

The completeWitness and checkWitness convenience functions revalidate the original row embedded in the encoding. Production acceptance must first call verifyEncoding with the authoritative externally bound original row and must retain the final direct arbitrary-precision original-row check.

## Completed synthetic controls

Utility source SHA-256:

e484e0e374e5579c75f3bfe9bdac2fa837acf75525d42d6c8f231a560856446c

Control source SHA-256:

50453251663287a33196c78df5f078ea8ff78cce98f2f8297943249f587cf7ad

The one declared 30-second control run completed in 6.073 seconds:

- 1,750 complete small signed rows at bases 2 and 4, with all 14,000 Boolean assignments checked: 7,950 satisfy and 6,050 violate the original row.
- A separate direct enumeration of native auxiliary domains for 236 one- or two-limb rows: 944 Boolean inputs and 21,688 auxiliary assignments. Exactly one auxiliary witness exists for each of the 538 satisfying inputs, and none for the others. This test does not use the witness constructor or checker to decide native feasibility.
- Seven large signed rows and all 56 Boolean assignments, including coefficients up to 202 bits and a 151-bit right side.
- 33 zero-variable constant rows.
- Literal-offset controls, strict radix-power boundaries and a 480-term native activity check.
- Rejection of 18 malformed inputs, 22 encoding mutations and seven witness mutations. These include coefficient signs, carry signs, slack domains, endpoint terms, missing limbs, aliasing, wrong original/source bindings and changed binary inputs.

The supplied coefficient 151115862703648029875148 has 78 bits. The result reports its measured length.

## Remaining integration obligations

The arithmetic theorem and controls establish the declared encoding. They do not establish a full-model transport, native runtime validation, a satisfying literal selection, or an exclusion. The original 4,416-row data was not read in this run. A future builder must bind that archive, preserve every literal row and original ID, allocate globally fresh auxiliary IDs, verify each encoding against its authoritative row, check the global native-domain budget and validate the actual model. Any returned candidate must still pass direct original integer arithmetic.
