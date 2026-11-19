/-
  Kernel-Checked Level-7 Modular-Form Rank Exclusions for Conway's 99-Graph (`srg(99, 14, 1, 2)`).

  Stock Lean 4 `Init` only (tested on Lean 4.35.0, zero external dependencies):
  - zero floats, zero `sorry`, zero warnings, constructive `[propext, Quot.sound]` (or zero axioms).
  - Run with `lean --trust=0 lean/Conway99LevelSeven.lean`.

  Summary:
  1. Computes all 15 weight-22 Gamma_0(7) eta-quotient basis q-series
       `f_j = q^j * theta(q) * prod (1 - q^k)^(49 - 4j) * prod (1 - q^(7k))^(4j - 7)`
     through Fourier order 14 inside Lean's kernel.
  2. Checks all five rank-44 positive control lattices `theta^6 E_4^(4-s) E_{4,7}^s` (`s = 0..4`)
     and their Fricke involution transforms `7^(3 + r/2 - 2j) f_(14 - j)` through order 14.
  3. Checks that all 35 triples of one side of the complementary Fano point-block incidence
     generate all 14 core vertices under same-side common-neighbor closure (`L_7 <= 990` input).
  4. Unifies the level-7 dual refutations into one order-10 exact integer functional `(wL, wK)`
     cancelling all 15 basis forms identically (`unified_dual_cancels_all_15_basis_forms`).
  5. Proves `conway99_no_even_rank_le_30` (excluding every even rank `r = 2 * p <= 30`, including
     `r = 28` and `r = 30`, from the three elementary base dual floors `K_2 >= 462`,
     `K_3 >= 24948`, `K_4 >= 1386`) and `conway99_no_rank_32` (excluding `r = 32` from the
     5-site sparse dual floors `K_4 >= 1398474`, `K_5 >= 18001368`).
-/

namespace Conway99.LevelSeven

set_option maxRecDepth 16384

/-- Truncation order `N = 14` (polynomials of length `15`, coefficients `q^0 .. q^14`),
    matching all 15 basis forms `f_0 .. f_14` of weight-22 modular forms on `Gamma_0(7)`. -/
def maxOrder : Nat := 14
def polyLen : Nat := maxOrder + 1

def coeffAt (p : List Int) (i : Nat) : Int :=
  match p, i with
  | [], _ => 0
  | x :: _, 0 => x
  | _ :: xs, k + 1 => coeffAt xs k

def polyMulTerm (a b : List Int) (i : Nat) : Int :=
  let rec go (j : Nat) (acc : Int) : Int :=
    match j with
    | 0 => acc + coeffAt a 0 * coeffAt b i
    | k + 1 => go k (acc + coeffAt a (k + 1) * coeffAt b (i - (k + 1)))
  go i 0

def polyMul (a b : List Int) : List Int :=
  (List.range polyLen).map (fun i => polyMulTerm a b i)

def polyPow (a : List Int) : Nat → List Int
  | 0 => 1 :: List.replicate maxOrder 0
  | k + 1 => polyMul (polyPow a k) a

/-- Linear-time `O(k)` binomial coefficient `C(n, k)` via structural recursion on `k`. -/
def binomNat (n : Nat) : Nat → Nat
  | 0 => 1
  | k + 1 =>
      if k + 1 > n then 0
      else (binomNat n k * (n - k)) / (k + 1)

/-- Coefficient of `q^(k*i)` in `(1 - q^k)^exp` for signed integer `exp`. -/
def factorCoeff (exp : Int) (i : Nat) : Int :=
  if 0 ≤ exp then
    let eNat := exp.toNat
    let c : Int := (binomNat eNat i : Int)
    if i % 2 == 0 then c else -c
  else
    let mNat := (-exp).toNat
    (binomNat (i + mNat - 1) i : Int)

def sparseFactorPoly (k : Nat) (exp : Int) : List Int :=
  (List.range polyLen).map (fun deg =>
    if k > 0 && deg % k == 0 then factorCoeff exp (deg / k) else 0)

def intEqBool (a b : Int) : Bool :=
  if a = b then true else false

/-- `theta(q) = sum_{x, y in Z} q^(x^2 + x*y + 2*y^2)` through `q^14`, computed directly over
    all integer lattice points `(x, y)` with `|y| <= 2` and `|x| <= 4` (since `(x + y/2)^2 + 7y^2/4 <= 14`). -/
def thetaCoeff (n : Nat) : Int :=
  let ys : List Int := [-2, -1, 0, 1, 2]
  let xs : List Int := [-4, -3, -2, -1, 0, 1, 2, 3, 4]
  ys.foldl (fun acc y =>
    xs.foldl (fun acc2 x =>
      if x * x + x * y + 2 * y * y = (n : Int) then acc2 + 1 else acc2
    ) acc
  ) 0

def thetaSeries : List Int :=
  (List.range polyLen).map thetaCoeff

/-- Apply `prod_{k = t, 2t, ... <= 14} (1 - q^k)^exp` to `q`. -/
def mulEtaPower (t : Nat) (exp : Int) (q : List Int) : List Int :=
  let ks := (List.range polyLen).filter (fun k => k >= t && t > 0 && k % t == 0)
  ks.foldl (fun acc k => polyMul acc (sparseFactorPoly k exp)) q

/-- Basis form `f_j = q^j * theta(q) * prod (1 - q^k)^(49 - 4j) * prod (1 - q^(7k))^(4j - 7)`
    for `j in 0..14`, truncated to `q^0 .. q^14`. -/
def etaBasisForm (j : Nat) : List Int :=
  let exp1 : Int := 49 - 4 * (j : Int)
  let exp7 : Int := 4 * (j : Int) - 7
  let q1 := mulEtaPower 1 exp1 thetaSeries
  let q2 := mulEtaPower 7 exp7 q1
  (List.replicate j 0 ++ q2).take polyLen

def etaBasis : List (List Int) :=
  (List.range 15).map etaBasisForm

/-- Exact Eisenstein series `E_4(q)` and `E_4(q^7)` through `q^14` for positive control verification. -/
def sigma3 (n : Nat) : Int :=
  ((List.range n).map (fun d => d + 1)).foldl
    (fun acc d => if n % d == 0 then acc + (d * d * d : Int) else acc) 0

def e4Series : List Int :=
  1 :: ((List.range maxOrder).map (fun k => 240 * sigma3 (k + 1)))

def e47Series : List Int :=
  (List.range polyLen).map (fun i => if i % 7 == 0 then coeffAt e4Series (i / 7) else 0)

def pow7 : Nat → Int
  | 0 => 1
  | k + 1 => 7 * pow7 k

/-- Unified exact order-10 integer dual functional `(wL, wK)` at base rank `r = 30`.
    `wL` is negative on upper-bounded shells (`L_0..L_8`) and `+1` on `L_10 >= 0`;
    `wK` is positive on all dual shells `K_0..K_5`. -/
def wLList : List (Nat × Int) :=
  [ (0, -56706285), (1, -16133402), (2, -4305675), (3, -1064463),
    (4, -239525),   (5, -47795),    (6, -8100),    (7, -1075),
    (8, -89),       (10, 1) ]

def wKList : List (Nat × Int) :=
  [ (0, 932253), (1, 246829), (2, 37963), (3, 4071), (4, 292), (5, 11) ]

/-- Integer-scaled basis dot product at index `j in 0..14`:
    `7^10 * sum_i wL_i * f_j[i] + sum_i wK_i * 7^(28 - 2j) * f_{14 - j}[i]`. -/
def dualBasisCheck (j : Nat) : Int :=
  let fj := etaBasisForm j
  let fDual := etaBasisForm (14 - j)
  let sL := wLList.foldl (fun acc (i, w) => acc + w * coeffAt fj i) 0
  let sK := wKList.foldl (fun acc (i, w) => acc + w * coeffAt fDual i) 0
  pow7 10 * sL + pow7 (28 - 2 * j) * sK

/-- 1. Exact Kernel-Checked Basis Cancellation Theorem:
    All 15 weight-22 Gamma_0(7) basis forms cancel identically under the unified order-10
    integer dual functional `(wL, wK)`. -/
theorem unified_dual_cancels_all_15_basis_forms :
    ∀ j ∈ List.range 15, dualBasisCheck j = 0 := by
  decide

/-- 2. Positive Control Theorem (5 Rank-44 Explicit Lattices `theta^6 E_4^(4-s) E_{4,7}^s`):
    Verifies directly inside Lean's kernel that the computed `etaBasis` and Fricke involution
    `7^(3 + r/2 - 2j)` reproduce all 5 known rank-44 lattice pairs `(L_s, K_s)` at `r = 6 + 8s`
    (`s = 0..4`) through order 14. -/
def basisAt (basis : List (List Int)) (j : Nat) : List Int :=
  match basis, j with
  | [], _ => []
  | x :: _, 0 => x
  | _ :: xs, k + 1 => basisAt xs k

def extractCoordsAux (basis : List (List Int)) : Nat → Nat → List Int → List Int
  | _, 0, _ => []
  | j, remSteps + 1, rem =>
      let x := coeffAt rem j
      let bj := basisAt basis j
      let nextRem := (List.range polyLen).map (fun i => coeffAt rem i - x * coeffAt bj i)
      x :: extractCoordsAux basis (j + 1) remSteps nextRem

def extractCoords15 (basis : List (List Int)) (target : List Int) : List Int :=
  extractCoordsAux basis 0 15 target

def verifyRank44Control (s : Nat) : Bool :=
  let basis := etaBasis
  let th6 := polyPow thetaSeries 6
  let lhs := polyMul th6 (polyMul (polyPow e4Series (4 - s)) (polyPow e47Series s))
  let dual := polyMul th6 (polyMul (polyPow e4Series s) (polyPow e47Series (4 - s)))
  let coords := extractCoords15 basis lhs
  let rHalf := 3 + 4 * s
  let recOk := (List.range polyLen).all (fun i =>
    let recL := (List.range 15).foldl (fun acc j => acc + coeffAt coords j * coeffAt (basisAt basis j) i) 0
    intEqBool recL (coeffAt lhs i))
  let frickeOk := (List.range polyLen).all (fun i =>
    let lhsScaled := pow7 22 * coeffAt dual i
    let rhsScaled := (List.range 15).foldl (fun acc j =>
      acc + pow7 (25 + rHalf - 2 * j) * coeffAt coords j * coeffAt (basisAt basis (14 - j)) i) 0
    intEqBool lhsScaled rhsScaled)
  recOk && frickeOk

theorem rank44_five_positive_controls_verified :
    verifyRank44Control 0 = true ∧
    verifyRank44Control 1 = true ∧
    verifyRank44Control 2 = true ∧
    verifyRank44Control 3 = true ∧
    verifyRank44Control 4 = true := by
  decide

/-- 3. Kernel-Checked 35 Fano-Complement Triples Closure Theorem:
    On the 14-vertex complementary Fano point-block incidence (`blocks[s] = {s+2,s+4,s+5,s+6} mod 7`),
    every one of the 35 triples of points on one side generates all 14 core vertices under
    repeated same-side common-neighbor closure (supporting the `L_7 <= 990` norm-14 upper bound). -/
def fanoAdj (u v : Nat) : Bool :=
  if u < 7 && v >= 7 && v < 14 then
    let b := v - 7
    let diff := (u + 7 - b) % 7
    diff == 2 || diff == 4 || diff == 5 || diff == 6
  else if v < 7 && u >= 7 && u < 14 then
    let b := u - 7
    let diff := (v + 7 - b) % 7
    diff == 2 || diff == 4 || diff == 5 || diff == 6
  else
    false

def closureStep (seen : List Nat) : List Nat :=
  let allVerts := List.range 14
  let added := allVerts.filter (fun z =>
    !(seen.contains z) &&
    seen.any (fun x =>
      seen.any (fun y =>
        x < y && (x / 7 == y / 7) && fanoAdj x z && fanoAdj y z)))
  seen ++ added

def closureN : Nat → List Nat → List Nat
  | 0, s => s
  | k + 1, s => closureN k (closureStep s)

def all35TriplesGenerateCore : Bool :=
  (List.range 7).all (fun a =>
    (List.range 7).all (fun b =>
      (List.range 7).all (fun c =>
        if a < b && b < c then
          (closureN 6 [a, b, c]).length == 14
        else true)))

theorem fano_complement_35_triples_closure :
    all35TriplesGenerateCore = true := by
  decide

/-!
  4. Abstract Integer-Scaled Farkas Refutation Soundness & Universal Rank Exclusions (`r <= 30`, `r = 32`).
-/

/-- Evaluate primal shell coefficient `L_i = sum_{j=0}^{14} c(j) * f_j[i]`. -/
def evalL (c : Nat → Int) (i : Nat) : Int :=
  (List.range 15).foldl (fun acc j => acc + c j * coeffAt (etaBasisForm j) i) 0

/-- Evaluate integer-scaled Fricke dual shell coefficient at even rank `r = 2 * p`:
    equals `7^(25 - p) * K_i` for every `p <= 25`. -/
def evalKScaled (c : Nat → Int) (i : Nat) : Int :=
  (List.range 15).foldl (fun acc j => acc + c j * (pow7 (28 - 2 * j) * coeffAt (etaBasisForm (14 - j)) i)) 0

private theorem foldl_add_linear (xs : List Nat) (f g : Nat → Int) (init : Int) :
    xs.foldl (fun acc x => acc + (f x + g x)) init =
      xs.foldl (fun acc x => acc + f x) init + xs.foldl (fun acc x => acc + g x) 0 := by
  induction xs generalizing init with
  | nil => simp
  | cons a tl ih =>
      simp only [List.foldl_cons]
      have h1 := ih (init + (f a + g a))
      have h2 : tl.foldl (fun acc x => acc + f x) (init + (f a + g a)) =
          tl.foldl (fun acc x => acc + f x) (init + f a) + g a := by
        have shift : ∀ (ys : List Nat) (z1 z2 : Int),
            ys.foldl (fun acc x => acc + f x) (z1 + z2) =
              ys.foldl (fun acc x => acc + f x) z1 + z2 := by
          intro ys
          induction ys with
          | nil => intro z1 z2; rfl
          | cons y yt ihy =>
              intro z1 z2
              simp only [List.foldl_cons]
              have hre : z1 + z2 + f y = (z1 + f y) + z2 := by omega
              rw [hre, ihy]
        have hre2 : init + (f a + g a) = (init + f a) + g a := by omega
        rw [hre2, shift]
      have h3 : tl.foldl (fun acc x => acc + g x) (0 + g a) =
          g a + tl.foldl (fun acc x => acc + g x) 0 := by
        have shiftg : ∀ (ys : List Nat) (z1 z2 : Int),
            ys.foldl (fun acc x => acc + g x) (z1 + z2) =
              ys.foldl (fun acc x => acc + g x) z1 + z2 := by
          intro ys
          induction ys with
          | nil => intro z1 z2; rfl
          | cons y yt ihy =>
              intro z1 z2
              simp only [List.foldl_cons]
              have hre : z1 + z2 + g y = (z1 + g y) + z2 := by omega
              rw [hre, ihy]
        rw [shiftg tl 0 (g a)]
        omega
      omega

private theorem foldl_const_zero (xs : List Nat) (f : Nat → Int)
    (hz : ∀ x ∈ xs, f x = 0) :
    xs.foldl (fun acc x => acc + f x) 0 = 0 := by
  induction xs with
  | nil => rfl
  | cons a tl ih =>
      simp only [List.foldl_cons]
      have ha : f a = 0 := hz a (List.Mem.head tl)
      have htl : ∀ x ∈ tl, f x = 0 := fun x hx => hz x (List.Mem.tail a hx)
      rw [ha, Int.add_zero]
      exact ih htl

private theorem foldl_mul_left (xs : List Nat) (k : Int) (f : Nat → Int) :
    k * xs.foldl (fun acc x => acc + f x) 0 = xs.foldl (fun acc x => acc + k * f x) 0 := by
  have aux : ∀ (ys : List Nat) (init : Int),
      k * ys.foldl (fun acc x => acc + f x) init =
        ys.foldl (fun acc x => acc + k * f x) (k * init) := by
    intro ys
    induction ys with
    | nil => intro init; rfl
    | cons y yt ihy =>
        intro init
        simp only [List.foldl_cons]
        rw [ihy (init + f y), Int.mul_add]
  have h := aux xs 0
  rw [Int.mul_zero] at h
  exact h

private theorem dual_linear_combination_zero (c : Nat → Int) :
    pow7 10 * (wLList.foldl (fun acc (i, w) => acc + w * evalL c i) 0) +
      wKList.foldl (fun acc (i, w) => acc + w * evalKScaled c i) 0 = 0 := by
  have hSwap : ∀ (ws : List (Nat × Int)) (M : Nat → Nat → Int),
      ws.foldl (fun acc (i, w) => acc + w * (List.range 15).foldl (fun a j => a + c j * M j i) 0) 0 =
      (List.range 15).foldl (fun a j => a + c j * ws.foldl (fun acc (i, w) => acc + w * M j i) 0) 0 := by
    intro ws M
    have aux : ∀ (us : List (Nat × Int)) (init : Int) (accJ : Nat → Int),
        (init = (List.range 15).foldl (fun a j => a + c j * accJ j) 0) →
        us.foldl (fun acc (i, w) => acc + w * (List.range 15).foldl (fun a j => a + c j * M j i) 0) init =
        (List.range 15).foldl (fun a j => a + c j * us.foldl (fun acc (i, w) => acc + w * M j i) (accJ j)) 0 := by
      intro us
      induction us with
      | nil =>
          intro init accJ hinit
          simpa using hinit
      | cons p tl ih =>
          rcases p with ⟨i, w⟩
          intro init accJ hinit
          simp only [List.foldl_cons]
          apply ih (init + w * (List.range 15).foldl (fun a j => a + c j * M j i) 0)
            (fun j => accJ j + w * M j i)
          rw [hinit, foldl_mul_left (List.range 15) w (fun j => c j * M j i)]
          have hlin := foldl_add_linear (List.range 15)
            (fun j => c j * accJ j) (fun j => w * (c j * M j i)) 0
          have hdist : ∀ j, c j * (accJ j + w * M j i) = c j * accJ j + w * (c j * M j i) := by
            intro j
            rw [Int.mul_add]
            have hc : c j * (w * M j i) = w * (c j * M j i) := by
              simp only [Int.mul_left_comm]
            rw [hc]
          have hcongr : (List.range 15).foldl (fun a j => a + c j * (accJ j + w * M j i)) 0 =
              (List.range 15).foldl (fun a j => a + (c j * accJ j + w * (c j * M j i))) 0 := by
            congr 1
            funext a j
            rw [hdist j]
          rw [hcongr, hlin]
    exact aux ws 0 (fun _ => 0) (by
      symm
      exact foldl_const_zero (List.range 15) (fun j => c j * 0) (fun j _ => Int.mul_zero (c j)))
  have hL := hSwap wLList (fun j i => coeffAt (etaBasisForm j) i)
  have hK := hSwap wKList (fun j i => pow7 (28 - 2 * j) * coeffAt (etaBasisForm (14 - j)) i)
  change pow7 10 * (wLList.foldl (fun acc (i, w) => acc + w * (List.range 15).foldl (fun a j => a + c j * coeffAt (etaBasisForm j) i) 0) 0) +
      wKList.foldl (fun acc (i, w) => acc + w * (List.range 15).foldl (fun a j => a + c j * (pow7 (28 - 2 * j) * coeffAt (etaBasisForm (14 - j)) i)) 0) 0 = 0
  rw [hL, hK, foldl_mul_left (List.range 15) (pow7 10)]
  have hcomb := foldl_add_linear (List.range 15)
    (fun j => pow7 10 * (c j * wLList.foldl (fun acc (i, w) => acc + w * coeffAt (etaBasisForm j) i) 0))
    (fun j => c j * wKList.foldl (fun acc (i, w) => acc + w * (pow7 (28 - 2 * j) * coeffAt (etaBasisForm (14 - j)) i)) 0) 0
  rw [← hcomb]
  apply foldl_const_zero (List.range 15)
  intro j hj
  have hfactorK :
      wKList.foldl (fun acc (i, w) => acc + w * (pow7 (28 - 2 * j) * coeffAt (etaBasisForm (14 - j)) i)) 0 =
      pow7 (28 - 2 * j) * wKList.foldl (fun acc (i, w) => acc + w * coeffAt (etaBasisForm (14 - j)) i) 0 := by
    have auxK : ∀ (us : List (Nat × Int)) (init : Int),
        us.foldl (fun acc (i, w) => acc + w * (pow7 (28 - 2 * j) * coeffAt (etaBasisForm (14 - j)) i))
          (pow7 (28 - 2 * j) * init) =
        pow7 (28 - 2 * j) * us.foldl (fun acc (i, w) => acc + w * coeffAt (etaBasisForm (14 - j)) i) init := by
      intro us
      induction us with
      | nil => intro init; rfl
      | cons p tl ih =>
          rcases p with ⟨i, w⟩
          intro init
          simp only [List.foldl_cons]
          have h1 : pow7 (28 - 2 * j) * init + w * (pow7 (28 - 2 * j) * coeffAt (etaBasisForm (14 - j)) i) =
              pow7 (28 - 2 * j) * (init + w * coeffAt (etaBasisForm (14 - j)) i) := by
            rw [Int.mul_add]
            have hc : w * (pow7 (28 - 2 * j) * coeffAt (etaBasisForm (14 - j)) i) =
                pow7 (28 - 2 * j) * (w * coeffAt (etaBasisForm (14 - j)) i) := by
              simp only [Int.mul_left_comm]
            rw [hc]
          rw [h1, ih]
    have h0 := auxK wKList 0
    rw [Int.mul_zero] at h0
    exact h0
  rw [hfactorK]
  have hzero := unified_dual_cancels_all_15_basis_forms j hj
  unfold dualBasisCheck at hzero
  have hre :
      pow7 10 * (c j * wLList.foldl (fun acc (i, w) => acc + w * coeffAt (etaBasisForm j) i) 0) +
      c j * (pow7 (28 - 2 * j) * wKList.foldl (fun acc (i, w) => acc + w * coeffAt (etaBasisForm (14 - j)) i) 0) =
      c j * (pow7 10 * wLList.foldl (fun acc (i, w) => acc + w * coeffAt (etaBasisForm j) i) 0 +
             pow7 (28 - 2 * j) * wKList.foldl (fun acc (i, w) => acc + w * coeffAt (etaBasisForm (14 - j)) i) 0) := by
    rw [Int.mul_add]
    have h1 : pow7 10 * (c j * wLList.foldl (fun acc (i, w) => acc + w * coeffAt (etaBasisForm j) i) 0) =
        c j * (pow7 10 * wLList.foldl (fun acc (i, w) => acc + w * coeffAt (etaBasisForm j) i) 0) := by
      simp only [Int.mul_left_comm]
    rw [h1]
  rw [hre, hzero, Int.mul_zero]

private theorem pow7_pos (k : Nat) : 1 ≤ pow7 k := by
  induction k with
  | zero => decide
  | succ m ih =>
      change 1 ≤ 7 * pow7 m
      omega

/-- 5. Universal Even-Rank `r = 2 * p <= 30` (including `r = 28` and `r = 30`) Exclusion Theorem:
    No integer basis coordinate vector `c` can satisfy the Conway-99 elementary shell bounds
    (`L_0 = 1, L_1..L_6 = 0, L_7 <= 990, L_8 <= 148995, L_10 >= 0`,
    `K_0 = 1, K_1 >= 0, K_2 >= 462, K_3 >= 24948, K_4 >= 1386, K_5 >= 0`) for any `p <= 15`. -/
theorem conway99_no_even_rank_le_30
    (p : Nat) (_hp : p ≤ 15) (c : Nat → Int) (K : Nat → Int)
    (hFricke : ∀ i, evalKScaled c i = pow7 (15 - p) * pow7 10 * K i)
    (hL0 : evalL c 0 = 1)
    (hL1 : evalL c 1 = 0) (hL2 : evalL c 2 = 0) (hL3 : evalL c 3 = 0)
    (hL4 : evalL c 4 = 0) (hL5 : evalL c 5 = 0) (hL6 : evalL c 6 = 0)
    (hL7 : evalL c 7 ≤ 990) (hL8 : evalL c 8 ≤ 148995) (hL10 : 0 ≤ evalL c 10)
    (hK0 : K 0 = 1) (hK1 : 0 ≤ K 1) (hK2 : 462 ≤ K 2)
    (hK3 : 24948 ≤ K 3) (hK4 : 1386 ≤ K 4) (hK5 : 0 ≤ K 5) :
    False := by
  have hzero := dual_linear_combination_zero c
  simp only [wLList, wKList, List.foldl_cons, List.foldl_nil, hFricke] at hzero
  have hP7_ge1 : 1 ≤ pow7 (15 - p) := pow7_pos (15 - p)
  have hP10_pos : 0 < pow7 10 := by decide
  have hL_ge : -71031090 ≤
      0 + (-56706285) * evalL c 0 + (-16133402) * evalL c 1 + (-4305675) * evalL c 2 +
      (-1064463) * evalL c 3 + (-239525) * evalL c 4 + (-47795) * evalL c 5 +
      (-8100) * evalL c 6 + (-1075) * evalL c 7 + (-89) * evalL c 8 + 1 * evalL c 10 := by
    omega
  have hK_raw : 120439179 ≤
      932253 * K 0 + 246829 * K 1 + 37963 * K 2 + 4071 * K 3 + 292 * K 4 + 11 * K 5 := by
    omega
  have hK_factor :
      0 + 932253 * (pow7 (15 - p) * pow7 10 * K 0) +
      246829 * (pow7 (15 - p) * pow7 10 * K 1) +
      37963 * (pow7 (15 - p) * pow7 10 * K 2) +
      4071 * (pow7 (15 - p) * pow7 10 * K 3) +
      292 * (pow7 (15 - p) * pow7 10 * K 4) +
      11 * (pow7 (15 - p) * pow7 10 * K 5) =
      pow7 10 * (pow7 (15 - p) *
        (932253 * K 0 + 246829 * K 1 + 37963 * K 2 + 4071 * K 3 + 292 * K 4 + 11 * K 5)) := by
    repeat rw [Int.mul_add]
    have s0 : 932253 * (pow7 (15 - p) * pow7 10 * K 0) = pow7 10 * (pow7 (15 - p) * (932253 * K 0)) := by
      simp only [Int.mul_assoc, Int.mul_left_comm, Int.mul_comm]
    have s1 : 246829 * (pow7 (15 - p) * pow7 10 * K 1) = pow7 10 * (pow7 (15 - p) * (246829 * K 1)) := by
      simp only [Int.mul_assoc, Int.mul_left_comm, Int.mul_comm]
    have s2 : 37963 * (pow7 (15 - p) * pow7 10 * K 2) = pow7 10 * (pow7 (15 - p) * (37963 * K 2)) := by
      simp only [Int.mul_assoc, Int.mul_left_comm, Int.mul_comm]
    have s3 : 4071 * (pow7 (15 - p) * pow7 10 * K 3) = pow7 10 * (pow7 (15 - p) * (4071 * K 3)) := by
      simp only [Int.mul_assoc, Int.mul_left_comm, Int.mul_comm]
    have s4 : 292 * (pow7 (15 - p) * pow7 10 * K 4) = pow7 10 * (pow7 (15 - p) * (292 * K 4)) := by
      simp only [Int.mul_assoc, Int.mul_left_comm, Int.mul_comm]
    have s5 : 11 * (pow7 (15 - p) * pow7 10 * K 5) = pow7 10 * (pow7 (15 - p) * (11 * K 5)) := by
      simp only [Int.mul_assoc, Int.mul_left_comm, Int.mul_comm]
    rw [s0, s1, s2, s3, s4, s5]
    omega
  rw [hK_factor] at hzero
  rw [← Int.mul_add] at hzero
  have hK_scaled : 120439179 ≤
      pow7 (15 - p) * (932253 * K 0 + 246829 * K 1 + 37963 * K 2 + 4071 * K 3 + 292 * K 4 + 11 * K 5) := by
    have hdiff : 0 ≤ (pow7 (15 - p) - 1) * 120439179 := Int.mul_nonneg (by omega) (by decide)
    rw [Int.sub_mul, Int.one_mul] at hdiff
    have hdiff2 : 0 ≤ pow7 (15 - p) *
        ((932253 * K 0 + 246829 * K 1 + 37963 * K 2 + 4071 * K 3 + 292 * K 4 + 11 * K 5) - 120439179) :=
      Int.mul_nonneg (by omega) (by omega)
    rw [Int.mul_sub] at hdiff2
    omega
  have hsum_pos : 0 <
      (0 + (-56706285) * evalL c 0 + (-16133402) * evalL c 1 + (-4305675) * evalL c 2 +
       (-1064463) * evalL c 3 + (-239525) * evalL c 4 + (-47795) * evalL c 5 +
       (-8100) * evalL c 6 + (-1075) * evalL c 7 + (-89) * evalL c 8 + 1 * evalL c 10) +
      pow7 (15 - p) * (932253 * K 0 + 246829 * K 1 + 37963 * K 2 + 4071 * K 3 + 292 * K 4 + 11 * K 5) := by
    omega
  have hprod_pos := Int.mul_pos hP10_pos hsum_pos
  omega

/-- 6. Rank `r = 32` (`p = 16`) Exclusion Theorem using the 5-Site Sparse Dual Floors
    (`K_2 >= 462, K_3 >= 24948, K_4 >= 1398474, K_5 >= 18001368`):
    Produces exact integer contradiction `0 >= 7^9 * 229186293 > 0`. -/
theorem conway99_no_rank_32
    (c : Nat → Int) (K : Nat → Int)
    (hFricke : ∀ i, evalKScaled c i = pow7 9 * K i)
    (hL0 : evalL c 0 = 1)
    (hL1 : evalL c 1 = 0) (hL2 : evalL c 2 = 0) (hL3 : evalL c 3 = 0)
    (hL4 : evalL c 4 = 0) (hL5 : evalL c 5 = 0) (hL6 : evalL c 6 = 0)
    (hL7 : evalL c 7 ≤ 990) (hL8 : evalL c 8 ≤ 148995) (hL10 : 0 ≤ evalL c 10)
    (hK0 : K 0 = 1) (hK1 : 0 ≤ K 1) (hK2 : 462 ≤ K 2)
    (hK3 : 24948 ≤ K 3) (hK4 : 1398474 ≤ K 4) (hK5 : 18001368 ≤ K 5) :
    False := by
  have hzero := dual_linear_combination_zero c
  simp only [wLList, wKList, List.foldl_cons, List.foldl_nil, hFricke] at hzero
  have hP9_pos : 0 < pow7 9 := by decide
  have hP10_eq : pow7 10 = pow7 9 * 7 := by decide
  have hL_ge : -71031090 ≤
      0 + (-56706285) * evalL c 0 + (-16133402) * evalL c 1 + (-4305675) * evalL c 2 +
      (-1064463) * evalL c 3 + (-239525) * evalL c 4 + (-47795) * evalL c 5 +
      (-8100) * evalL c 6 + (-1075) * evalL c 7 + (-89) * evalL c 8 + 1 * evalL c 10 := by
    omega
  have hK_raw : 726403923 ≤
      932253 * K 0 + 246829 * K 1 + 37963 * K 2 + 4071 * K 3 + 292 * K 4 + 11 * K 5 := by
    omega
  have hK_factor :
      0 + 932253 * (pow7 9 * K 0) + 246829 * (pow7 9 * K 1) +
      37963 * (pow7 9 * K 2) + 4071 * (pow7 9 * K 3) +
      292 * (pow7 9 * K 4) + 11 * (pow7 9 * K 5) =
      pow7 9 * (932253 * K 0 + 246829 * K 1 + 37963 * K 2 + 4071 * K 3 + 292 * K 4 + 11 * K 5) := by
    repeat rw [Int.mul_add]
    have s0 : 932253 * (pow7 9 * K 0) = pow7 9 * (932253 * K 0) := by simp only [Int.mul_left_comm]
    have s1 : 246829 * (pow7 9 * K 1) = pow7 9 * (246829 * K 1) := by simp only [Int.mul_left_comm]
    have s2 : 37963 * (pow7 9 * K 2) = pow7 9 * (37963 * K 2) := by simp only [Int.mul_left_comm]
    have s3 : 4071 * (pow7 9 * K 3) = pow7 9 * (4071 * K 3) := by simp only [Int.mul_left_comm]
    have s4 : 292 * (pow7 9 * K 4) = pow7 9 * (292 * K 4) := by simp only [Int.mul_left_comm]
    have s5 : 11 * (pow7 9 * K 5) = pow7 9 * (11 * K 5) := by simp only [Int.mul_left_comm]
    rw [s0, s1, s2, s3, s4, s5]
    omega
  rw [hK_factor, hP10_eq, Int.mul_assoc, ← Int.mul_add] at hzero
  have hsum_pos : 0 <
      7 * (0 + (-56706285) * evalL c 0 + (-16133402) * evalL c 1 + (-4305675) * evalL c 2 +
           (-1064463) * evalL c 3 + (-239525) * evalL c 4 + (-47795) * evalL c 5 +
           (-8100) * evalL c 6 + (-1075) * evalL c 7 + (-89) * evalL c 8 + 1 * evalL c 10) +
      (932253 * K 0 + 246829 * K 1 + 37963 * K 2 + 4071 * K 3 + 292 * K 4 + 11 * K 5) := by
    omega
  have hprod_pos := Int.mul_pos hP9_pos hsum_pos
  omega

end Conway99.LevelSeven
