from pathlib import Path
from fractions import Fraction
from collections import Counter
from math import lcm
import argparse, hashlib, json
import numpy as np
from flint import fmpz_mat

parser = argparse.ArgumentParser(description='Replay the frozen refined 200-row witness with exact arithmetic, without an optimizer.')
parser.add_argument('--root', type=Path, required=True, help='Repository root containing the frozen artifacts')
args = parser.parse_args()
root = args.root.resolve()
assert root.is_dir()
logs = root / 'experiments/logs/moments-and-counts'
bindings = {
 'result': ('order10-high-graph-refined-query01.json', 'c2fb0a86acb2a311114a48a2589be7017a3cb3e426fee4a96f99b2b5ce3385ea'),
 'preparation': ('order10-high-graph-refined-query-preparation.json', '3ca0eb7504fb587a5ed69ee6083c3ca92b93be1f86ce8727f075a860af889199'),
 'arrays': ('order10-high-graph-refined-query-arrays.npz', 'db71229051f4ddce3423fad017e9788fd18549312f537e7fbcb8e406df360272'),
 'moments': ('order10-high-mask-graph-moments01.json', '43bde72fa777410a73732d418530a6a853a39740a1b7bcfc591d78977ad4cc3d'),
 'point': ('prism-zero-order10-all-flags-x521-face-loop01-round0-rounded-counts.json', '0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df')
}
contents = {}
for name, (path, expected) in bindings.items():
 raw = (logs / path).read_bytes()
 assert hashlib.sha256(raw).hexdigest() == expected
 if name != 'arrays': contents[name] = json.loads(raw)
result, prepared, moments, point = (contents[k] for k in ('result','preparation','moments','point'))
assert result['status'] == 'EXACT_REFINED_DECORATED_MOMENT_WITNESS'
assert result['exact_finite_witness'] and not result['exact_separator']
assert result['preparation_sha256'] == bindings['preparation'][1]
assert result['model_sha256'] == prepared['model']['exact_and_numerical_model_sha256']
assert result['numeric']['backend_run_calls'] == 1
with np.load(logs / bindings['arrays'][0], allow_pickle=False) as archive:
 arrays = {k: archive[k] for k in archive.files}
assert set(arrays) == set(prepared['array_sha256'])
for name, array in arrays.items():
 assert not array.dtype.hasobject
 assert hashlib.sha256(array.tobytes(order='C')).hexdigest() == prepared['array_sha256'][name]
C = arrays['coefficients']
assert C.shape == (200,17920)
b = moments['quotient_rhs']
assert len(b) == len(moments['rows']) == 200
for i, row in enumerate(moments['rows']):
 assert sum(coefficient * point['induced_counts'][t] for t, coefficient in row['direct_induced_count_form']) == b[i]
proof = result['exact_primal']
weights = proof['weights']
assert len(weights) == len(proof['representative_graphs']) == len(proof['support_filter_checks']) == 200
assert len({j for j,_,_ in weights}) == 200
assert all(type(j) is type(n) is type(d) is int and 0 <= j < 17920 and n > 0 and d > 0 for j,n,d in weights)
assert hashlib.sha256(json.dumps(weights,sort_keys=True,separators=(',',':')).encode()).hexdigest() == proof['weights_sha256']
D = lcm(*(d for _,_,d in weights))
assert D == proof['common_weight_denominator'] == 988761395399693539
scaled = [(j,n*(D//d)) for j,n,d in weights]
for i in range(200):
 assert sum(int(C[i,j])*n for j,n in scaled) == int(b[i])*D
assert sum(n for _,n in scaled) == b[0]*D == proof['total_mass']*D
retained = set(map(int, arrays['retained_full_graph_columns']))
checks = {c['full_graph_column']:c for c in proof['support_filter_checks']}
population = Counter()
for position, graph in enumerate(proof['representative_graphs']):
 j,_,_ = weights[position]
 assert graph['distinct_column'] == j
 full = graph['full_graph_column']
 assert full == int(arrays['retained_full_representatives'][j]) and full in retained
 assert graph['old_distinct_feature_column'] == int(arrays['old_feature_columns'][j])
 a = graph['core_plus_high_adjacency_rows']
 n = len(a); k = n-6
 assert k == len(graph['high_masks'])
 population[k] += 1
 for i in range(n):
  assert 0 <= a[i] < (1<<n) and not (a[i] & (1<<i)) and a[i].bit_count() <= 14
  for h in range(n):
   assert ((a[i]>>h)&1) == ((a[h]>>i)&1)
  for h in range(i+1,n):
   assert (a[i]&a[h]).bit_count()+((a[i]>>h)&1) <= 2
 assert all((a[i]&63)==0 for i in range(6))
 assert [a[6+i]&63 for i in range(k)] == graph['high_masks']
 assert [[i,h] for i in range(k) for h in range(i+1,k) if (a[6+i]>>(6+h))&1] == graph['high_edges']
 saved = checks[full]
 computed_polynomials = []
 for kind in (0,1):
  P = [[(27*(i==h)-9*((a[i]>>h)&1)+1 if kind==0 else 44*(i==h)+11*((a[i]>>h)&1)-2) for h in range(n)] for i in range(n)]
  coefficients = list(map(int,fmpz_mat([[-x for x in row] for row in P]).charpoly()))
  assert len(coefficients)==n+1 and coefficients[-1]==1 and all(c>=0 for c in coefficients)
  computed_polynomials.append(coefficients)
 assert computed_polynomials == saved['det_tI_plus_projector_coefficients']
 G = [[12*(i==h)-((a[i]>>h)&1)-(a[i]&a[h]).bit_count()+2 for h in range(n)] for i in range(n)]
 v = [-1]*6+[1]*k
 first = sum(v[i]*G[i][i] for i in range(n))
 second = sum(v[i]*G[i][h]*v[h] for i in range(n) for h in range(n))
 outside = 99-n; shift = first//outside
 gap = second-(2*shift+1)*first+shift*(shift+1)*outside
 literal = {'core_adjacency_rows':a,'integer_core_vector':v,'outside_population':outside,'integer_shift':shift,'first_moment':first,'second_moment':second,'twice_shifted_polynomial_sum':gap}
 assert gap >= 0 and literal == saved['integer_incidence_certificate']
print(json.dumps({
 'status':'EXACT_REFINED_MOMENT_WITNESS_PORTABLE_REPLAY_PASS',
 'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
 'bindings':bindings,
 'exact_positive_weights':200,'all_original_200_moment_rows_checked':True,
 'common_denominator':str(D),'total_mass':proof['total_mass'],
 'retained_full_support_graphs_checked':200,'literal_core_caps_checked':200,
 'exact_principal_projector_characteristic_polynomials_recomputed':400,
 'shifted_integer_incidence_certificates_recomputed':200,
 'support_high_population_histogram':dict(sorted(population.items())),
 'filesystem_history_assertions_used':False,
 'all_full_domain_exclusion_certificates_replayed_in_this_audit':False,
 'original_feature_domain_or_census_rebuilt':False,
 'optimizer_called':False,'checkout_files_written':False,
 'graph_existence_resolved':False
},indent=2))

