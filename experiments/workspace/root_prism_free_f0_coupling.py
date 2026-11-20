"""Exact split-component coupling domains and a fractional self-control.

No optimizer is used. The fractional point fixes the first incidence,
but averages the second incidence over a six-element fiber-fixing group.
It is not a point of the smaller fixed-both-design matching model.
"""
import argparse
from collections import Counter
import gzip
from itertools import combinations, permutations
import json
from math import lcm
from pathlib import Path
import time

import root_prism_free_f0_components as components
import root_prism_free_f0_pair_clauses as motifs


ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT/'experiments/logs/root-prism-free'
RESULT = LOGS/'f0-incidence-case00-run01/result.json'
RESULT_SHA = '64d5411e04764b0d7e7157c47b67d759e536a401fee8fe36e274943f2fda4abf'
PAIR_CERTIFICATE = LOGS/'f0-pair-clauses.json.gz'
PAIR_SHA = '47e9d8f518fab10aee604f33df1f22c97b0d201a1af4180e4307553e4857672f'
digest,canonical = motifs.digest,components.canonical


def profile(triple):
    return tuple(sum(vertex//6 == fiber for vertex in triple) for fiber in range(3))


def complement(counts):
    return tuple(2-value for value in counts)


def load():
    catalogue = motifs.load()
    assert digest(RESULT) == RESULT_SHA
    result = json.loads(RESULT.read_text())
    assert result['case'] == 0 and result['status'].startswith('SAT;')
    assert digest(PAIR_CERTIFICATE) == PAIR_SHA
    conflicts = json.loads(gzip.decompress(PAIR_CERTIFICATE.read_bytes()))
    assert conflicts['source_sha256'] == digest(Path(motifs.__file__))
    domain = catalogue['representatives'][0]['domain']
    selected = result['incidence_witness']['selected_columns']
    assert selected == sorted(set(selected)) and len(selected) == 60
    check_design(domain,selected,conflicts['representatives'][0])
    return catalogue,domain,selected,conflicts['representatives'][0]


def check_design(domain,selected,conflicts):
    triples = [domain['signature_domain'][i] for i in selected]
    assert len({tuple(h) for h in triples}) == 60
    assert all(sum(i in h and j in h for h in triples) == domain['Gram'][i][j]
               for i in range(18) for j in range(i,18))
    counts = Counter(map(profile,triples))
    assert counts[(1,1,1)] == 24
    assert all(value == 6 for p,value in counts.items() if p != (1,1,1))
    selected = set(selected)
    assert all(not set(record['columns']) <= selected
               for kind in ('F_conflicts','prism_conflicts') for record in conflicts[kind])


def joined_core(first,second):
    """The three central vertices are shared; shell blocks are disjoint."""
    rows = [0]*39
    for which,domain in enumerate((first,second)):
        image = list(range(3))+[3+18*which+i for i in range(18)]
        for i,row in enumerate(domain['core_rows']):
            for j in range(i+1,21):
                if row >> j & 1:
                    components.edge(rows,image[i],image[j])
    assert [row.bit_count() for row in rows] == [14]*3+[4]*36
    assert components.caps(rows)
    gram = [[12*(i == j)+2-(rows[i] & rows[j]).bit_count()-(rows[i] >> j & 1)
             for j in range(39)] for i in range(39)]
    assert all(value == 0 for row in gram[:3] for value in row)
    assert all(gram[3+i][3+j] == first['Gram'][i][j]
               and gram[21+i][21+j] == second['Gram'][i][j]
               and gram[3+i][21+j] == 2-(i//6 == j//6)
               for i in range(18) for j in range(18))
    return rows,gram


def paired_domain(first,second):
    return [(i,j) for i,a in enumerate(first) for j,b in enumerate(second)
            if profile(b) == complement(profile(a))]


def full_signature(first,second):
    return [3+i for i in first]+[21+j for j in second]


def fixed_problem():
    catalogue,domain,selected,conflicts = load()
    design = [domain['signature_domain'][i] for i in selected]
    pairs = paired_domain(design,design)
    assert len(pairs) == 792
    core,gram = joined_core(domain,domain)
    columns = [full_signature(design[a],design[b]) for a,b in pairs]
    masks = [sum(1 << site for site in column) for column in columns]
    assert all(mask.bit_count() == 6 for mask in masks)
    for mask in masks:
        assert all(((row | (1 << i)) & mask).bit_count() <= 2 for i,row in enumerate(core))
    return domain,selected,design,pairs,columns,core,gram


def group(domain,description):
    first,pool,qs = components.input_domain()
    p,r,q = description
    matchings = (first,pool[p],pool[r],qs[q])
    group = [list(image) for image in permutations(range(6))
             if all(image[m[i]] == m[image[i]] for m in matchings for i in range(6))]
    assert len(group) == 6
    for image in group:
        core_image = list(range(3))+[3+6*f+image[i] for f in range(3) for i in range(6)]
        assert components.permute(domain['core_rows'],core_image) == tuple(domain['core_rows'])
    assert all({image[i] for image in group} == set(range(6)) for i in range(6))
    return group


def fractional_control(catalogue,domain,selected,conflicts):
    signatures = domain['signature_domain']
    position = {tuple(h):i for i,h in enumerate(signatures)}
    actions = group(domain,catalogue['representatives'][0]['description'])
    multiplicities,images = Counter(),[]
    for image in actions:
        transported = sorted(position[tuple(sorted(6*(i//6)+image[i % 6] for i in signatures[s]))]
                             for s in selected)
        check_design(domain,transported,conflicts)
        images.append(transported)
        multiplicities.update(transported)
    counts = Counter(profile(signatures[s]) for s in selected)
    assert all(counts[p] == counts[complement(p)] for p in counts)
    denominator = lcm(*(len(actions)*value for value in counts.values()))
    assert denominator == 144
    weighted = []
    for first_index,source in enumerate(selected):
        target = complement(profile(signatures[source]))
        factor = denominator//(len(actions)*counts[target])
        assert factor*len(actions)*counts[target] == denominator
        for second,multiplicity in sorted(multiplicities.items()):
            if profile(signatures[second]) == target:
                weighted.append([first_index,second,factor*multiplicity])
    core,gram = joined_core(domain,domain)
    actual = [[0]*39 for _ in range(39)]
    row_sums,col_sums,packing = Counter(),Counter(),Counter()
    for first,second,weight in weighted:
        assert weight > 0
        row_sums[first] += weight
        col_sums[second] += weight
        sites = full_signature(signatures[selected[first]],signatures[second])
        mask = sum(1 << v for v in sites)
        assert all(((row | (1 << i)) & mask).bit_count() <= 2 for i,row in enumerate(core))
        for i in sites:
            for j in sites:
                actual[i][j] += weight
        for triple in combinations(sites,3):
            packing[triple] += weight
    assert len(row_sums) == 60 and set(row_sums.values()) == {denominator}
    assert max(col_sums.values()) <= denominator
    assert actual == [[denominator*value for value in row] for row in gram]
    assert max(packing.values()) <= denominator
    assert all(col_sums.get(record['columns'][0],0)+col_sums.get(record['columns'][1],0) <= denominator
               for kind in ('F_conflicts','prism_conflicts') for record in conflicts[kind])
    return {'status':'exact fractional fixed-first/all-second-domain Gram and packing control',
            'denominator':denominator,'positive_weight_count':len(weighted),
            'second_domain_triples_used':len(col_sums),'weights':weighted,
            'fiber_fixing_actions':actions,'transported_second_designs':images,
            'full39_Gram_entries_checked':1521,'all60_first_row_sums_hold':True,
            'second_triple_multiplicity_at_most_one':True,
            'core_triple_packing_max_numerator':max(packing.values()),
            'core_triple_packing_inequalities_checked':len(packing),
            'second_component_motif_inequalities_hold':True,
            'point_of_fixed_both60_design_model':False,
            'binary_feasibility_claimed':False}


def domain_counts(catalogue,first_domain,selected):
    first_counts = Counter(map(profile,first_domain['signature_domain']))
    chosen_counts = Counter(profile(first_domain['signature_domain'][i]) for i in selected)
    records = []
    for index,record in enumerate(catalogue['representatives']):
        counts = Counter(map(profile,record['domain']['signature_domain']))
        for alignment in permutations(range(3)):
            aligned = Counter()
            for old,count in counts.items():
                new = [0]*3
                for fiber in range(3):
                    new[alignment[fiber]] = old[fiber]
                aligned[tuple(new)] += count
            direct = sum(value*aligned[complement(p)] for p,value in first_counts.items())
            fixed = sum(value*aligned[complement(p)] for p,value in chosen_counts.items())
            records.append({'second_representative':index,'second_fiber_image':list(alignment),
                            'direct39_paired_columns':direct,'fixed_first_assignment_columns':fixed})
    return records


def result():
    started=time.monotonic()
    catalogue,domain,selected,conflicts=load()
    design=[domain['signature_domain'][i] for i in selected]
    direct=paired_domain(domain['signature_domain'],domain['signature_domain'])
    fixed=paired_domain(design,domain['signature_domain'])
    both=paired_domain(design,design)
    assert (len(direct),len(fixed),len(both)) == (39168,5472,792)
    core,gram=joined_core(domain,domain)
    for a,b in direct:
        mask=sum(1 << i for i in full_signature(domain['signature_domain'][a],domain['signature_domain'][b]))
        assert all(((row | (1 << i)) & mask).bit_count() <= 2 for i,row in enumerate(core))
    counts=domain_counts(catalogue,domain,selected)
    fraction=fractional_control(catalogue,domain,selected,conflicts)
    # A different, uniform matching of only the two fixed60-designs does
    # not give the cross Gram. It is not the fractional control above.
    profile_counts=Counter(map(profile,design))
    uniform=[[0]*18 for _ in range(18)]
    for a,b in both:
        weight=24//profile_counts[profile(design[b])]
        for i in design[a]:
            for j in design[b]:
                uniform[i][j] += weight
    defects=sum(uniform[i][j] != 24*(2-(i//6 == j//6)) for i in range(18) for j in range(18))
    assert defects == 167
    return {'status':'complete coupling domains and exact fractional self-control; no optimizer',
            'source_sha256':digest(Path(__file__)),'component_source_sha256':digest(Path(components.__file__)),
            'motif_source_sha256':digest(Path(motifs.__file__)),
            'domain_certificate_sha256':motifs.DOMAIN_SHA,'pair_certificate_sha256':PAIR_SHA,
            'fixed_incidence_result':str(RESULT.relative_to(ROOT)),'fixed_incidence_result_sha256':RESULT_SHA,
            'scope':'conditional split18+18 shell; first component0 with one fixed SAT incidence',
            'joined39_core_rows':[str(row) for row in core],'joined39_Gram':gram,
            'cross_Gram_formula':'2J minus the three same-fiber J6 blocks',
            'first_selected_domain_indices':selected,'fixed_design':design,
            'self_pair_domain_sizes':{'direct':len(direct),'fixed_first':len(fixed),'fixed_both':len(both)},
            'fixed_both_pairs':[list(pair) for pair in both],
            'all66_second_components_and_all6_fiber_alignments':counts,
            'fractional_control':fraction,'fixed_both_uniform_matching_cross_defects':defects,
            'optimizer_called':False,'fixed_both_binary_feasibility_decided':False,
            'whole_component_or_split_case_excluded':False,
            'elapsed_seconds_for_information_only':time.monotonic()-started}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--certificate',required=True,type=Path)
    parser.add_argument('--replay',action='store_true')
    args=parser.parse_args()
    actual=result()
    if args.replay:
        saved=json.loads(gzip.decompress(args.certificate.read_bytes()))
        actual['elapsed_seconds_for_information_only']=saved['elapsed_seconds_for_information_only']
        assert actual == saved
    else:
        assert not args.certificate.exists()
        args.certificate.write_bytes(gzip.compress(canonical(actual)+b'\n',mtime=0))
    print(json.dumps({'status':'PASS: coupling equations, domains and exact fractional control',
                      'mode':'replay' if args.replay else 'generation',
                      'self_pair_domain_sizes':actual['self_pair_domain_sizes'],
                      'partner_alignment_cases':len(actual['all66_second_components_and_all6_fiber_alignments']),
                      'fractional_positive_weights':actual['fractional_control']['positive_weight_count'],
                      'fractional_denominator':actual['fractional_control']['denominator'],
                      'fixed_both_model_feasible_claimed':False,'optimizer_called':False},indent=2),flush=True)
