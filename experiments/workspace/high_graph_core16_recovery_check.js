"use strict";

/* Standalone recovery checker. No dependencies or input files.
   In an SRG(99,14,1,2), G=12I-B-B^2+2J is the exterior incidence Gram.
   For integer v, (v^T G v-v^T diag(G))/2 is a sum of binom(z,2)
   over integer exterior column sums z. Here every such z lies in [-6,10].
   This program checks all 31 empty/single-edge cores literally. */

function runCore16RecoveryAudit() {
  function assert(ok, message) { if (!ok) throw new Error(message); }
  function popcount(x) { let n=0; for (;x;x&=x-1) n++; return n; }
  const masks = [7,11,21,26,28,38,41,44,49,50];
  const rootDegrees = Array.from({length:6}, (_,i) =>
    masks.reduce((s,m)=>s+((m>>i)&1),0));
  const rootPairs=[];
  for(let i=0;i<6;i++) for(let j=i+1;j<6;j++)
    rootPairs.push({pair:[i,j],count:masks.reduce((s,m)=>
      s+((m>>i)&1)*((m>>j)&1),0)});
  assert(masks.every(m=>popcount(m)===3),"non-triple mask");
  assert(rootDegrees.every(d=>d===5),"root degree");
  assert(rootPairs.every(x=>x.count===2),"root pair multiplicity");
  const overlaps={};
  const eligible=[];
  for(let i=0;i<10;i++) for(let j=i+1;j<10;j++) {
    const n=popcount(masks[i]&masks[j]);
    overlaps[n]=(overlaps[n]||0)+1;
    if(n<=1) eligible.push([i,j]);
  }
  assert(overlaps[1]===30 && overlaps[2]===15,"overlap census");
  const attachmentValues=[];
  for(let z=-6;z<=10;z++) {
    const value=z*(z-1)/2;
    assert(Number.isSafeInteger(value)&&value>=0,"integer column inequality");
    attachmentValues.push({z,value});
  }
  function audit(edges) {
    const B=Array.from({length:16},()=>Array(16).fill(0));
    masks.forEach((m,j)=>{
      for(let i=0;i<6;i++) if((m>>i)&1) B[i][6+j]=B[6+j][i]=1;
    });
    for(const [a,b] of edges) B[6+a][6+b]=B[6+b][6+a]=1;
    const B2=Array.from({length:16},(_,i)=>Array.from({length:16},(_,j)=>
      B[i].reduce((s,x,k)=>s+x*B[k][j],0)));
    assert(B.every((row,i)=>row.every((a,j)=>i===j||B2[i][j]+a<=2)),
      "visible common-neighbor cap");
    const G=B.map((row,i)=>row.map((a,j)=>
      12*(i===j?1:0)-a-B2[i][j]+2));
    const v=Array.from({length:16},(_,i)=>i<6?-1:1);
    const first=v.reduce((s,x,i)=>s+x*G[i][i],0);
    const second=v.reduce((s,x,i)=>
      s+x*G[i].reduce((t,g,j)=>t+g*v[j],0),0);
    const highDegrees=Array.from({length:10},(_,i)=>
      B[6+i].slice(6).reduce((s,a)=>s+a,0));
    const wedges=highDegrees.reduce((s,d)=>s+d*(d-1)/2,0);
    const halfGap=(second-first)/2;
    assert(first===56-2*edges.length,"first moment formula");
    assert(second===44+8*edges.length-2*wedges,"second moment formula");
    assert(halfGap===5*edges.length-wedges-6,"integer Gram formula");
    assert(Number.isSafeInteger(halfGap)&&halfGap<0,"negative certificate");
    return {
      high_edges:edges,high_degrees:highDegrees,
      core_adjacency_rows:B.map(row=>row.reduce((s,a,j)=>s+a*2**j,0)),
      vector:v,first_moment:first,second_moment:second,
      half_gap:halfGap,visible_caps_pass:true
    };
  }
  const cases=[audit([]),...eligible.map(edge=>audit([edge]))];
  assert(cases.length===31,"case census");
  assert(cases[0].first_moment===56&&cases[0].second_moment===44,"empty case");
  assert(cases.slice(1).every(x=>x.first_moment===54&&x.second_moment===52),
    "single-edge cases");
  return {
    status:"EXACT_31_INDUCED_CORE_EXCLUSIONS",
    complete_for_stated_empty_or_single_edge_domain:true,
    graph_parameters:{v:99,k:14,lambda:1,mu:2},
    masks,root_degrees:rootDegrees,root_pair_multiplicities:rootPairs,
    high_mask_overlap_counts:overlaps,
    eligible_single_edges:eligible,
    attachment_polynomial_values:attachmentValues,
    gram_identity:"G=12I-B-B^2+2J=XX^T",
    integer_inequality:"(v^T G v-v^T diag(G))/2=sum_outside binom(v^T h,2)>=0",
    closed_form:"5e(H)-sum_a binom(d_H(a),2)-6",
    cases,
    scope:"These 31 labelled induced cores are excluded. This is not a proof of nonexistence of SRG(99,14,1,2), and it does not recover the unavailable refined moment witness."
  };
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { runCore16RecoveryAudit };
  if (require.main === module) console.log(JSON.stringify(runCore16RecoveryAudit(), null, 2));
}
