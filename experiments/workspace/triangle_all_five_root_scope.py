"""Complete point-independent five-root intersecting-triangle class census."""
import argparse
from collections import Counter
from itertools import combinations,combinations_with_replacement
from math import factorial
import json
from pathlib import Path
import time

import triangle_incidence_projector_moments as base
import triangle_projector_intersecting_root_scope_v2 as old

BASE_SHA="1e7a8b7380314d6dfd8ff05954a13662bc011378f5759ad675ec1bc281fa19e9"
OLD_SOURCE_SHA="d25c7cfdb94fa79f0100990752a3c941011dd62e230c02b71472657f715f1b65"
OLD_SCOPE_SHA="78e62efc423f7acd498368207607c5dfc5572dd1840accebe46c38141aeb331f"
OLD_ROOTS=[26,27,28,32,33,34,35,37]


def one_root(rid,root,aut,previous,deadline):
    automorphisms=old.literal_automorphisms(root)
    assert len(automorphisms)==int(aut)
    classes=[];rejections=Counter();attempted=0
    for size in (1,2,3):
        for vertices in combinations(range(5),size):
            inside=sum(1<<i for i in vertices)
            allowed=[m for m in range(32) if m&inside==inside]
            for masks in combinations_with_replacement(allowed,3-size):
                attempted+=1
                if attempted%256==0:
                    base.check_time(deadline)
                rows=old.extension(root,inside,masks)
                if rows is None:
                    rejections["triangle_prescription"]+=1
                    continue
                if not base.cap_valid(rows):
                    rejections["visible_caps"]+=1
                    continue
                assert tuple(vertices)+tuple(range(5,len(rows))) in base.triangles(rows)
                stabilizer=1
                for count in Counter(masks).values():
                    stabilizer*=factorial(count)
                classes.append({"root_intersection_mask":inside,"outside_masks":list(masks),
                                "literal_rows":list(rows),"outside_label_stabilizer":stabilizer})
    keys=[(c["root_intersection_mask"],tuple(c["outside_masks"])) for c in classes]
    assert len(keys)==len(set(keys))
    assert len(classes)+sum(rejections.values())==attempted
    if rid in previous:
        prior=previous[rid]
        assert prior["root_rows"]==list(root)
        assert [(c["root_intersection_mask"],tuple(c["outside_masks"])) for c in prior["classes"]]==keys
        assert [c["literal_rows"] for c in prior["classes"]]==[c["literal_rows"] for c in classes]
    profile=Counter(len(c["outside_masks"]) for c in classes)
    lower=len(classes)*(len(classes)+1)//2
    pairs={(a,b):(profile[a]*profile[b] if a!=b else profile[a]*(profile[a]+1)//2)
           for a in range(3) for b in range(a,3)}
    assert sum(pairs.values())==lower
    bound=sum(count*old.completion_bound(a,b) for (a,b),count in pairs.items())
    return {"root_type":rid,"root_rows":list(root),"root_order":5,
            "root_automorphisms":int(aut),"literal_root_automorphisms":automorphisms,
            "core_triangles":[list(t) for t in base.triangles(root)],
            "previous_eight_Q_root_domain":rid in previous,
            "classes":classes,"class_count":len(classes),"lower_entries":lower,
            "outside_vertex_profile":dict(profile),
            "outside_stabilizer_profile":dict(Counter(c["outside_label_stabilizer"] for c in classes)),
            "attempted_classes":attempted,"rejections":dict(rejections),
            "partial_injection_and_free_edge_candidate_bound":bound,
            "largest_pair_union_order":9}


def summarize(roots):
    return {"roots":len(roots),"classes":sum(r["class_count"] for r in roots),
            "maximum_block":max((r["class_count"] for r in roots),default=0),
            "lower_entries_per_kernel":sum(r["lower_entries"] for r in roots),
            "candidate_union_bound":sum(r["partial_injection_and_free_edge_candidate_bound"] for r in roots)}


def run(args):
    assert 0<args.seconds<=30 and not args.output.exists()
    start=time.monotonic();deadline=start+args.seconds
    assert base.digest(Path(base.__file__).read_bytes())==BASE_SHA
    assert base.digest(Path(old.__file__).read_bytes())==OLD_SOURCE_SHA
    raw=args.old_scope.read_bytes();assert base.digest(raw)==OLD_SCOPE_SHA
    scope=json.loads(raw)
    previous={d["root_type"]:d for d in scope["roots"] if d["root_order"]==5}
    assert sorted(previous)==OLD_ROOTS
    graphs,levels,aut,_=base.load_catalogue(args.catalogue)
    report={"status":"INCOMPLETE","source_sha256":base.digest(Path(__file__).read_bytes()),
            "base_source_sha256":BASE_SHA,"prior_source_sha256":OLD_SOURCE_SHA,
            "prior_scope_sha256":OLD_SCOPE_SHA,"catalogue_sha256":base.CATALOGUE_SHA,
            "roots":[],"complete_all_21_root_coverage":False,
            "count_point_loaded":False,"pair_products_generated":False,
            "optimizer_called":False,"host_graph_symmetry_assumed":False}
    try:
        assert list(levels[5])==list(range(17,38))
        for rid in levels[5]:
            base.check_time(deadline)
            report["roots"].append(one_root(rid,graphs[rid],aut[rid],previous,deadline))
        allroots=report["roots"];oldroots=[r for r in allroots if r["previous_eight_Q_root_domain"]]
        newroots=[r for r in allroots if not r["previous_eight_Q_root_domain"]]
        assert len(oldroots)==8 and len(newroots)==13
        assert all(r["core_triangles"] for r in oldroots)
        assert all(not r["core_triangles"] for r in newroots)
        assert summarize(oldroots)["classes"]==257 and summarize(oldroots)["candidate_union_bound"]==108481
        assert next(r for r in allroots if not any(r["root_rows"]))["class_count"]==205
        report.update(status="COMPLETE_ALL_21_FIVE_ROOT_INTERSECTING_TRIANGLE_CLASS_SCOPE",
                      complete_all_21_root_coverage=True,
                      full_summary=summarize(allroots),previous_Q_root_summary=summarize(oldroots),
                      incremental_root_summary=summarize(newroots),
                      all_allowed_classes_retained=True,point_dependent_pruning=False,
                      normalization="Ordered labelled products divided by the product of outside-mask factorial stabilizers after collecting induced types; root labels are retained.")
    except Exception as error:
        report.update(status="INCOMPLETE_NO_FULL_SCOPE_CLAIM",error_type=type(error).__name__,error_message=str(error))
        raise
    finally:
        report["seconds"]=time.monotonic()-start
        args.output.write_text(json.dumps(report,indent=2)+"\n")
        print(json.dumps({k:v for k,v in report.items() if k!="roots"},indent=2))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--catalogue",type=Path,required=True)
    p.add_argument("--old-scope",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--seconds",type=float,default=10)
    run(p.parse_args())


if __name__=="__main__":
    main()
