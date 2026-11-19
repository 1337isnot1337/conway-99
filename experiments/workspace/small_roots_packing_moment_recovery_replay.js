"use strict";

function replaySmallRootDistributions(prepared,result,point,checkerBlob) {
  "use strict";
  function assert(ok,message) { if(!ok) throw Error(message); }
  function equal(a,b) { return JSON.stringify(a)===JSON.stringify(b); }
  function popcount(n) { let total=0; while(n) { total+=n&1; n>>>=1; } return total; }
  function gcd(a,b) { while(b) { const r=a%b; a=b; b=r; } return a; }
  function choose(values,k,callback) {
    const selected=[];
    function visit(start) {
      if(selected.length===k) { callback(selected.slice()); return; }
      for(let j=start;j<=values.length-(k-selected.length);j++) {
        selected.push(values[j]); visit(j+1); selected.pop();
      }
    }
    visit(0);
  }
  function extension(root,masks) {
    const rows=root.slice();
    for(let j=0;j<masks.length;j++) {
      rows.push(masks[j]);
      for(let i=0;i<6;i++) if(masks[j]&(1<<i)) rows[i]|=1<<(6+j);
    }
    return rows;
  }
  function violates(rows) {
    for(let i=0;i<rows.length;i++) for(let j=i+1;j<rows.length;j++) {
      if(popcount(rows[i]&rows[j])+((rows[i]>>j)&1)>2) return true;
    }
    return false;
  }
  const expectedSource="34085dd6833ab816968ede0ba4637e44713b37fc";
  assert(prepared.source_git_blob===expectedSource && result.source_git_blob===expectedSource,"source binding");
  assert(prepared.status==="POINT_INDEPENDENT_COMPLETE_SMALL_ROOT_PREPARATION_PASS","preparation status");
  assert(result.status==="EXACT_ALL_SMALL_ROOT_MOMENT_DISTRIBUTIONS","result status");
  assert(equal(prepared.bindings,result.bindings),"input bindings");
  assert(prepared.bindings.point_git_blob==="c881dae3be05cf289fcc45a99d72c405ac863c46","point identity");
  assert(prepared.roots.length===32 && result.roots.length===32 && result.complete_roots===32,"complete roots");
  assert(!prepared.count_point_loaded && !prepared.optimizer_called && !result.optimizer_called,"execution scope");
  assert(!result.full_graph_existence_resolved,"graph scope");
  assert(point.exact_count_and_held_cut_witness && point.x521_zero && point.required_zeros_hold,"point scope");
  assert(point.induced_counts.length===48965,"count dimensions");
  assert(point.induced_counts.every(n=>Number.isSafeInteger(n)&&n>=0),"integer counts");
  const counts=point.induced_counts.map(BigInt);
  const typeAut=new Map();
  for(const group of prepared.catalogue_fingerprint_groups) {
    assert(group.literal_classes.length===1 && group.catalogue_types.length===1 && group.singleton_identification,"singleton fingerprint");
    const aut=prepared.literal_graph_classes[group.literal_classes[0]].automorphisms;
    assert(aut===group.common_automorphisms && Number.isSafeInteger(aut) && aut>0,"automorphism binding");
    assert(!typeAut.has(group.catalogue_types[0]),"unique type");
    typeAut.set(group.catalogue_types[0],BigInt(aut));
  }
  assert(typeAut.size===294,"catalogue types");
  const contexts=prepared.literal_product_rows;
  assert(contexts.length===2450 && contexts.every((c,i)=>c.context===i),"product inventory");
  const universal=Array.from({length:64},(_,i)=>i).filter(m=>popcount(m)>=3);
  const maskIndex=new Map(universal.map((m,i)=>[m,i]));
  function atomCode(masks) {
    return masks.reduce((code,m)=>code|(1n<<BigInt(maskIndex.get(m))),0n);
  }
  let individual=0,quotient=0,rawTotal=0,zeroTotal=0,fiveTotal=0,partitionsTotal=0;
  const rootReports=[];
  for(let rootIndex=0;rootIndex<32;rootIndex++) {
    const p=prepared.roots[rootIndex],r=result.roots[rootIndex],n=p.monomials.length;
    assert(r.root_type===p.root_type && r.status==="EXACT_NONNEGATIVE_ATOM_DISTRIBUTION","root alignment");
    assert(r.atom_count===n && r.orbit_count===p.orbits.length,"root dimensions");
    assert(r.atom_moments.length===n && r.atom_weights.length===n,"vector sizes");
    assert(r.negative_weights===0 && r.negative_certificates.length===0,"no omitted negative");
    const high=universal.filter(m=>!violates(extension(p.root_rows,[m])));
    assert(equal(high,p.high_masks),"full high-mask domain");
    const codes=p.monomials.map((m,i)=>{
      assert(m.atom_index===i,"atom order");
      const c=atomCode(m.masks);
      assert(c===BigInt(m.global_atom_code),"atom code");
      return c;
    });
    assert(codes[0]===0n && new Set(codes.map(String)).size===n,"empty and distinct atoms");
    const byCode=new Map(codes.map((c,i)=>[c.toString(),i]));
    const weights=r.atom_weights.map(BigInt),moments=r.atom_moments.map(BigInt);
    assert(weights.every(w=>w>=0n),"nonnegative exact weights");
    const g=BigInt(r.labelled_root_mass);
    assert(g===BigInt(p.actual_root_automorphisms.length)*counts[p.root_type] && moments[0]===g,"root mass");
    assert(weights.reduce((s,w)=>s+w,0n)===g,"total weight");
    if(g===0n) assert(weights.every(w=>w===0n)&&moments.every(m=>m===0n),"zero-root moments");
    for(let i=0;i<n;i++) {
      const monomial=p.monomials[i];
      let normalized=null;
      for(const partition of monomial.product_partitions) {
        const raw=new Map();
        for(const id of partition) {
          assert(contexts[id].root_type===p.root_type,"product root");
          for(const [type,c] of contexts[id].catalogue_multiplicities) {
            raw.set(type,(raw.get(type)||0n)+BigInt(c));
          }
        }
        const sorted=[...raw].sort((a,b)=>a[0]-b[0]).map(([t,c])=>[t,c.toString()]);
        if(normalized===null) normalized=sorted;
        else assert(equal(normalized,sorted),"all product partitions");
        partitionsTotal++;
      }
      assert(equal(normalized,monomial.labelled_embedding_form.map(([t,c])=>[t,String(c)])),"labelled form");
      const induced=normalized.map(([t,c])=>[t,(BigInt(c)*typeAut.get(t)).toString()]);
      assert(equal(induced,monomial.induced_count_form.map(([t,c])=>[t,String(c)])),"induced form");
      const value=induced.reduce((s,[t,c])=>s+BigInt(c)*counts[t],0n);
      assert(value===moments[i],"direct induced moment");
      let actual=0n;
      for(let j=0;j<n;j++) if((codes[i]&codes[j])===codes[i]) actual+=weights[j];
      assert(actual===value,"exact moment equation");
      individual++;
    }
    let raw=0,zeros=0,fives=0;
    for(let k=0;k<=4;k++) choose(high,k,masks=>{
      raw++;
      const code=atomCode(masks),invalid=violates(extension(p.root_rows,masks));
      assert(invalid===!byCode.has(code.toString()),"complete supported/zero domain");
      if(invalid) {
        zeros++;
        let value=0n;
        for(let j=0;j<n;j++) if((code&codes[j])===code) value+=weights[j];
        assert(value===0n,"unsupported monomial zero");
      }
    });
    choose(high,5,masks=>{ assert(violates(extension(p.root_rows,masks)),"five-class impossibility"); fives++; });
    assert(raw===p.raw_monomials && zeros===p.unsupported_zero_witnesses.length && fives===p.five_class_subsets_checked,"scope counts");
    const orbitWeights=p.orbits.map(o=>o.members.reduce((s,i)=>s+weights[i],0n));
    assert(equal(orbitWeights.map(String),r.orbit_weights),"orbit masses");
    for(let q=0;q<p.orbits.length;q++) {
      const orbit=p.orbits[q];
      assert(orbit.members.length===orbit.size,"orbit size");
      assert(orbit.members.every(i=>weights[i]===weights[orbit.representative] && moments[i]===moments[orbit.representative]),"orbit invariance");
      const lhs=p.quotient_coefficients[q].reduce((s,c,j)=>s+BigInt(c)*orbitWeights[j],0n);
      assert(lhs===BigInt(orbit.size)*moments[orbit.representative],"quotient equation");
      quotient++;
    }
    const positive=weights.filter(w=>w>0n).length,zero=n-positive;
    assert(positive===r.positive_weights && zero===r.zero_weights,"sign counts");
    let common=g; for(const w of weights) common=gcd(common,w);
    rootReports.push({
      root_type:p.root_type,labelled_root_mass:g.toString(),atoms:n,orbits:p.orbits.length,
      positive_atoms:positive,zero_atoms:zero,
      unnormalized_common_gcd:common.toString(),
      reduced_probability_denominator:(common?g/common:0n).toString()
    });
    rawTotal+=raw; zeroTotal+=zeros; fiveTotal+=fives;
  }
  assert(individual===1035 && quotient===492 && rawTotal===4975 && zeroTotal===3940 && fiveTotal===3987,"complete global counts");
  return {
    status:"INDEPENDENT_ARTIFACT_REPLAY_PASS",
    checker_git_blob:checkerBlob||null,
    bindings:{
      query_source_git_blob:expectedSource,
      preparation_git_blob:"537b722f2dd4f964c5fa053d5398e41c60b4ed9d",
      result_git_blob:"c87f5b759a000f0fa2a8ad197bf6a82b9fc538c4",
      point_git_blob:"c881dae3be05cf289fcc45a99d72c405ac863c46"
    },
    roots:rootReports,
    summary:{
      roots:32,positive_mass_roots:rootReports.filter(r=>r.labelled_root_mass!=="0").length,
      zero_mass_roots:rootReports.filter(r=>r.labelled_root_mass==="0").length,
      atoms:individual,positive_atoms:rootReports.reduce((s,r)=>s+r.positive_atoms,0),
      zero_atoms:rootReports.reduce((s,r)=>s+r.zero_atoms,0),quotient_equations:quotient,
      raw_presence_monomials:rawTotal,unsupported_zero_monomials:zeroTotal,
      five_mask_exclusions:fiveTotal,product_partitions_replayed:partitionsTotal
    },
    independence:"No query import or Mobius inversion is used. The supplied nonnegative weights are checked against every direct induced form, every presence and quotient equation, and a fresh literal cap census. Product rows and automorphism factors are the hash-bound prepared certificate; their generation is not independently repeated here.",
    optimizer_called:false,full_graph_existence_resolved:false
  };
}

if(typeof module!=="undefined"&&module.exports) {
  module.exports={replaySmallRootDistributions};
  if(require.main===module) {
    const fs=require("fs"),crypto=require("crypto");
    const expected=[
      "537b722f2dd4f964c5fa053d5398e41c60b4ed9d",
      "c87f5b759a000f0fa2a8ad197bf6a82b9fc538c4",
      "c881dae3be05cf289fcc45a99d72c405ac863c46"
    ];
    function blob(file) {
      const data=fs.readFileSync(file);
      return crypto.createHash("sha1").update("blob "+data.length+"\0").update(data).digest("hex");
    }
    const paths=process.argv.slice(2);
    if(paths.length!==3)throw Error("Usage: node replay.js preparation.json result.json point.json");
    paths.forEach((p,i)=>{if(blob(p)!==expected[i])throw Error("Input blob mismatch "+i);});
    const [prepared,result,point]=paths.map(p=>JSON.parse(fs.readFileSync(p,"utf8")));
    const report=replaySmallRootDistributions(prepared,result,point,blob(__filename));
    console.log(JSON.stringify(report,null,2));
  }
}
