"""Read-only full-column lattice audit of the refined decorated model.

Orbit-total embedding masses have unit 720. The retained matrix contains
a unit-triangular 200-column minor, so its full integer column lattice is
Z^200. This does not assert nonnegative integer feasibility.
"""
from pathlib import Path
import hashlib, json, sys
import numpy as np

root=Path(sys.argv[1]).resolve()
logs=root/'experiments/logs/moments-and-counts'
bindings={
 'refined_arrays':('order10-high-graph-refined-query-arrays.npz','db71229051f4ddce3423fad017e9788fd18549312f537e7fbcb8e406df360272'),
 'original_arrays':('order10-high-mask-graph-features-arrays.npz','bd2971d442d8fb0a0059f946b93e4e11046c211bf77b6f1a128694f8792cc68e'),
 'moments':('order10-high-mask-graph-moments01.json','43bde72fa777410a73732d418530a6a853a39740a1b7bcfc591d78977ad4cc3d'),
 'point':('prism-zero-order10-all-flags-x521-face-loop01-round0-rounded-counts.json','0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df')
}
for name,(path,expected) in bindings.items():
 assert hashlib.sha256((logs/path).read_bytes()).hexdigest()==expected,name
with np.load(logs/bindings['refined_arrays'][0],allow_pickle=False) as saved:
 refined={k:saved[k] for k in saved.files}
with np.load(logs/bindings['original_arrays'][0],allow_pickle=False) as saved:
 original={k:saved[k] for k in saved.files}
moments=json.loads((logs/bindings['moments'][0]).read_text())
point=json.loads((logs/bindings['point'][0]).read_text())
C=refined['coefficients']
minor_columns=refined['unimodular_minor_columns']
assert C.shape==(200,17920) and np.issubdtype(C.dtype,np.integer)
assert len(minor_columns)==200 and len(set(map(int,minor_columns)))==200
assert np.array_equal(refined['old_feature_columns'][minor_columns],original['unimodular_minor_columns'])
minor=C[:,minor_columns]
assert np.array_equal(minor,original['coefficients'][:,original['unimodular_minor_columns']])
degree=original['row_free_vertices']
assert len(degree)==200 and set(map(int,degree))==set(range(5))
assert np.all(np.diag(minor)==1)
zero_conditions=0
for i in range(200):
 for j in range(200):
  if int(degree[i])>int(degree[j]) or (int(degree[i])==int(degree[j]) and i!=j):
   assert int(minor[i,j])==0
   zero_conditions+=1
order=sorted(range(200),key=lambda i:(int(degree[i]),i))
for i in range(200):
 assert int(minor[order[i],order[i]])==1
 for j in range(i): assert int(minor[order[i],order[j]])==0
retained=set(map(int,refined['retained_full_graph_columns']))
full_minor=refined['retained_full_representatives'][minor_columns]
assert all(int(c) in retained for c in full_minor)
rhs=[]
coefficient_divisibility=[]
for i,row in enumerate(moments['rows']):
 orbit=int(row['root_label_orbit_size'])
 assert orbit>0 and 720%orbit==0
 decorated_stabilizer=720//orbit
 aut=int(row['catalogue_automorphism_order'])
 assert aut%decorated_stabilizer==0
 coefficient=orbit*aut
 assert row['direct_induced_count_form']==[[row['catalogue_type'],coefficient]]
 assert coefficient%720==0
 value=sum(c*point['induced_counts'][t] for t,c in row['direct_induced_count_form'])
 assert value==moments['quotient_rhs'][i] and value%720==0
 rhs.append(value//720)
 coefficient_divisibility.append(coefficient//720)
assert len(rhs)==200 and rhs[0]==101287494
report={
 'status':'EXACT_FULL_COLUMN_LATTICE_IS_Z200',
 'bindings':bindings,
 'model_shape':[200,17920],
 'labelled_root_orbit_mass_unit':720,
 'normalized_rhs_integral':True,
 'all_200_rhs_coefficients_divisible_before_substituting_counts':True,
 'normalized_rhs':rhs,
 'normalized_induced_coefficients':coefficient_divisibility,
 'retained_unimodular_minor_columns':list(map(int,minor_columns)),
 'minor_surviving_full_graph_columns':list(map(int,full_minor)),
 'simultaneous_degree_order':order,
 'row_free_vertices':list(map(int,degree)),
 'verified_zero_conditions':zero_conditions,
 'determinant':1,
 'column_lattice_index':1,
 'smith_invariants':[1]*200,
 'new_lattice_congruence_obstruction':False,
 'nonnegative_integer_feasibility_claimed':False,
 'positive_rational_support_restricted_to':False,
 'optimizer_called':False,'source_query_imported':False,
 'full_domain_or_feature_products_rebuilt':False,'checkout_files_written':False,
 'scope':'Every integer RHS belongs to the full column lattice. Nonnegative integer membership is a separate semigroup problem. The denominator of one positive support does not create a full-column modular obstruction.'
}
print(json.dumps(report,indent=2))
