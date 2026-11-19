(() => {
"use strict";
const SCHEMA = "conway99.f0.triangle-schur-independent-cold.v1";
function insist(ok, message) { if (!ok) throw Error(message); }
function equal(a,b,message) { insist(JSON.stringify(a) === JSON.stringify(b), message); }
function safe(x,message) { insist(Number.isSafeInteger(x),message); return x; }
function bits(x) { let n=0; while(x){x&=x-1;n++;} return n; }
function orderedTriple(s,n) {
 insist(Array.isArray(s)&&s.length===3,"signature length");
 let mask=0,last=-1;
 for(const v of s){insist(Number.isInteger(v)&&v>last&&v<n,"signature order/range");mask|=1<<v;last=v;}
 return mask;
}
const PERMUTATIONS=[];
(function build(p,used){
 if(p.length===3){let sign=1;for(let i=0;i<3;i++)for(let j=i+1;j<3;j++)if(p[i]>p[j])sign=-sign;
  PERMUTATIONS.push([p.slice(),BigInt(sign)]);return;}
 for(let j=0;j<3;j++)if(!(used&(1<<j))){p.push(j);build(p,used|(1<<j));p.pop();}
})([],0);
function determinant(m) {
 insist(m.length===9,"3x3 determinant length");
 let result=0n;
 for(const [p,sign] of PERMUTATIONS)result+=sign*m[p[0]]*m[3+p[1]]*m[6+p[2]];
 return result;
}
function bareiss(m) {
 const a=Array.from({length:3},(_,i)=>m.slice(3*i,3*i+3));
 let sign=1n,previous=1n;
 for(let k=0;k<2;k++){
  let pivot=k;while(pivot<3&&a[pivot][k]===0n)pivot++;
  if(pivot===3)return 0n;
  if(pivot!==k){[a[pivot],a[k]]=[a[k],a[pivot]];sign=-sign;}
  const p=a[k][k];
  for(let i=k+1;i<3;i++)for(let j=k+1;j<3;j++){
   const numerator=p*a[i][j]-a[i][k]*a[k][j];
   insist(numerator%previous===0n,"Bareiss exact division");a[i][j]=numerator/previous;
  }
  for(let i=k+1;i<3;i++)a[i][k]=0n;
  previous=p;
 }
 return sign*a[2][2];
}
function lowerGraph(n,edges) {
 const width=Math.ceil(n/32),lower=Array.from({length:n},()=>new Uint32Array(width));
 for(const e of edges){
  insist(e.length===2&&Number.isInteger(e[0])&&Number.isInteger(e[1])&&e[0]>=0&&e[0]<e[1]&&e[1]<n,"graph edge");
  insist((lower[e[1]][e[0]>>>5]&(1<<(e[0]&31)))===0,"duplicate graph edge");
  lower[e[1]][e[0]>>>5]|=1<<(e[0]&31);
 }
 return lower;
}
function enumerate(lower,visit,tick,progress) {
 const n=lower.length,width=Math.ceil(n/32);
 for(let c=0;c<n;c++){
  tick();
  for(let wb=0;wb<width;wb++){
   let bs=lower[c][wb]>>>0;
   while(bs){
    const bit=bs&-bs,b=32*wb+31-Math.clz32(bit);bs=(bs&(bs-1))>>>0;
    insist(b<c,"lower-neighbor orientation");
    for(let wa=0;wa<=Math.floor(b/32);wa++){
     let common=(lower[b][wa]&lower[c][wa])>>>0;
     while(common){
      const low=common&-common,a=32*wa+31-Math.clz32(low);common=(common&(common-1))>>>0;
      insist(a<b,"common-lower-neighbor orientation");visit(a,b,c);
     }
    }
   }
  }
  progress(c+1);
 }
}
function zeroHits(ids,zeroRows) {
 insist(ids.length===3&&ids.every(v=>Number.isInteger(v)&&v>=0),"triangle edge IDs");
 return ids.filter(v=>zeroRows.has(v)).map(v=>zeroRows.get(v));
}
function controls() {
 const start=Date.now();let matrices=0,graphs=0,large=0;
 for(let code=0;code<15625;code++){
  let c=code,v=[];for(let j=0;j<6;j++){v.push(BigInt(c%5-2));c=Math.floor(c/5);}
  const [a,b,c0,d,e,f]=v,m=[a,d,e,d,b,f,e,f,c0];
  insist(determinant(m)===bareiss(m),"exhaustive determinant control");matrices++;
 }
 const largeMatrices=[
  [1n<<100n,3n,-7n,3n,(1n<<101n)+1n,9n,-7n,9n,(1n<<102n)-1n],
  [0n,1n<<100n,7n,1n<<100n,0n,5n,7n,5n,11n],
  [1n<<100n,2n<<100n,3n<<100n,2n<<100n,4n<<100n,6n<<100n,3n<<100n,6n<<100n,9n<<100n]
 ];
 for(const m of largeMatrices){insist(determinant(m)===bareiss(m),"large exact determinant");large++;}
 insist(determinant([1n,0n,0n,0n,1n,0n,0n,0n,1n])===1n,"identity determinant");
 insist(determinant([2n,-1n,-1n,-1n,2n,-1n,-1n,-1n,2n])===0n,"singular PSD determinant");
 insist(determinant([3n,-2n,-2n,-2n,3n,-2n,-2n,-2n,3n])===-25n,"positive proper minors negative determinant");
 const pairs=[];for(let a=0;a<4;a++)for(let b=a+1;b<4;b++)pairs.push([a,b]);
 for(let mask=0;mask<64;mask++){
  const edges=pairs.filter((_,i)=>mask&(1<<i)),lower=lowerGraph(4,edges),got=[];
  enumerate(lower,(a,b,c)=>got.push([a,b,c]),()=>{},()=>{});
  got.sort((u,v)=>u[0]-v[0]||u[1]-v[1]||u[2]-v[2]);
  const edgeSet=new Set(edges.map(e=>e.join(","))),wanted=[];
  for(let a=0;a<4;a++)for(let b=a+1;b<4;b++)for(let c=b+1;c<4;c++)
   if(edgeSet.has([a,b].join(","))&&edgeSet.has([a,c].join(","))&&edgeSet.has([b,c].join(",")))wanted.push([a,b,c]);
  equal(got,wanted,"exhaustive graph control");graphs++;
 }
 const crossVertices=[0,1,30,31,32,33,62,63,64],crossEdges=[];
 for(let i=0;i<crossVertices.length;i++)for(let j=i+1;j<crossVertices.length;j++)
  if((i+j)%3!==0)crossEdges.push([crossVertices[i],crossVertices[j]]);
 const crossSet=new Set(crossEdges.map(e=>e.join(","))),got=[];
 enumerate(lowerGraph(65,crossEdges),(a,b,c)=>got.push([a,b,c]),()=>{},()=>{});
 got.sort((u,v)=>u[0]-v[0]||u[1]-v[1]||u[2]-v[2]);
 const want=[];for(let a=0;a<65;a++)for(let b=a+1;b<65;b++)for(let c=b+1;c<65;c++)
  if(crossSet.has([a,b].join(","))&&crossSet.has([a,c].join(","))&&crossSet.has([b,c].join(",")))want.push([a,b,c]);
 equal(got,want,"31/32 and 63/64 boundaries");
 for(let mask=0;mask<8;mask++){
  const z=new Map();for(let i=0;i<3;i++)if(mask&(1<<i))z.set(i,{edge_id:i});
  equal(zeroHits([0,1,2],z).map(r=>r.edge_id),[0,1,2].filter(i=>mask&(1<<i)),"zero disposition control");
 }
 let rejects=0;for(const f of [()=>zeroHits([0,-1,2],new Map()),()=>lowerGraph(4,[[0,1],[0,1]]),()=>orderedTriple([1,1,2],18)]){
  try{f();}catch(e){rejects++;}
 }insist(rejects===3,"invalid input controls");
 return {status:"PASS_SMALL_INDEPENDENT_CONTROLS",symmetric_integer_matrices:matrices,large_integer_matrices:large,
  maximum_control_entry_bits:104,explicit_named_determinants:3,all_four_vertex_graphs:graphs,
  cross_word_graphs:1,zero_edge_masks:8,invalid_inputs_rejected:rejects,case_triangles_enumerated:0,seconds:(Date.now()-start)/1000};
}
function loadInputs(configurationText,payload,codec,sourceText,codecText,tick) {
 const cfg=JSON.parse(configurationText),hash=s=>codec.sha256(codec.utf8(s));
 insist(cfg.schema==="conway99.f0.triangle-schur-independent-cold.configuration.v1","configuration schema");
 insist(cfg.limits.maximum_ms===60000&&cfg.limits.maximum_report_bytes===67108864&&cfg.limits.maximum_nonpositive_records===50000,"fixed limits");
 insist(hash(sourceText)===cfg.source.sha256&&codec.utf8(sourceText).length===cfg.source.bytes&&codec.gitBlob(codec.utf8(sourceText))===cfg.source.git_blob,"source binding");
 insist(hash(codecText)===cfg.codec.sha256&&codec.gitBlob(codec.utf8(codecText))===cfg.codec.git_blob,"codec binding");
 const data={},bindings={};
 for(const name of ["domain","kernels","overlay","audit","forward"]){
  tick();const b=cfg.inputs[name];insist(b&&typeof payload[name]==="string","input payload");
  let raw;
  if(b.encoding==="gzip-base64"){
   const compressed=codec.base64(payload[name]);
   insist(compressed.length===b.archive_bytes&&codec.sha256(compressed)===b.archive_sha256&&codec.gitBlob(compressed)===b.git_blob,"archive binding "+name);
   raw=codec.gunzip(compressed,cfg.limits.maximum_report_bytes);
  }else{
   insist(b.encoding==="utf-8","input encoding");raw=codec.utf8(payload[name]);
   insist(codec.gitBlob(raw)===b.git_blob,"raw Git binding "+name);
  }
  insist(raw.length===b.raw_bytes&&codec.sha256(raw)===b.raw_sha256,"raw input binding "+name);
  data[name]=JSON.parse(codec.ascii(raw));bindings[name]={...b};
 }
 tick();
 const {domain:d,kernels:k,overlay:o,audit:a,forward:f}=data;
 insist(d.complete_signature_count===480&&d.signature_domain.length===480&&d.row_targets.length===480&&d.possible_neighbor_signature_ids.length===480,"domain dimensions");
 insist(d.complete_possible_edge_count===68394,"domain edge scope");
 insist(k.kernels.length===2&&a.families.length===2,"kernel family count");
 for(const name of ["plus","minus"]){
  const family=k.kernels.find(q=>q.family===name),audit=a.families.find(q=>q.family===name);
  insist(family&&audit&&family.diagonal_x.length===480&&family.off_diagonal_Z.length===114960,"kernel dimensions");
  insist(family.primitive_kernel_sha256===audit.primitive_kernel_sha256&&audit.all_115440_full_vs_old_kernel_entries_checked===true,"accepted kernel audit");
 }
 insist(a.status==="PASS: exact full-core Schur corrections; no point query"&&a.signature_count===480,"audit status");
 insist(o.status==="COMPLETE_LITERAL_PRISM_ZEROS_AND_CORE_PAIR_CLIQUES"&&o.zero_rows.length===1884,"zero premise scope");
 insist(f.schema==="conway99.f0.exterior-triangle-schur-census.v1"&&f.status==="COMPLETE_EXACT_TRIANGLE_PRINCIPAL_MINOR_CENSUS","forward record status");
 insist(f.source_sha256===cfg.forward_producer_sha256&&f.families.length===2,"forward source binding");
 return {cfg,data,bindings,configuration_sha256:hash(configurationText),source_sha256:cfg.source.sha256};
}
function prepare(configurationText,payload,codec,sourceText,codecText) {
 const start=Date.now(),tick=()=>insist(Date.now()-start<15000,"preparation 15-second bound");
 const loaded=loadInputs(configurationText,payload,codec,sourceText,codecText,tick);
 const report=controls();tick();
 return {schema:SCHEMA,status:"PREPARED_BINDINGS_AND_SMALL_CONTROLS_ONLY",source_sha256:loaded.source_sha256,
  configuration_sha256:loaded.configuration_sha256,inputs:loaded.bindings,controls:report,
  full_case_domain_reconstructed:false,case_minors_evaluated:0,case_triangles_enumerated:0,optimizer_calls:0,
  main_requires_separate_source_gate:true,seconds:(Date.now()-start)/1000};
}
function reconstructDomain(d,tick) {
 const n=480,core=d.component_core_rows,adj=d.component_adjacency_rows;
 insist(core.length===21&&adj.length===18,"literal core dimensions");
 for(let i=0;i<21;i++){
  safe(core[i],"core row integer");insist(core[i]>=0&&core[i]<(1<<21)&&!(core[i]&(1<<i)),"core graph range/diagonal");
  for(let j=0;j<21;j++)insist(!!(core[i]&(1<<j))===!!(core[j]&(1<<i)),"core symmetry");
 }
 for(let i=0;i<18;i++)insist(adj[i]===(core[i+3]>>>3),"core18 induced map");
 const masks=d.signature_domain.map(s=>orderedTriple(s,18));
 insist(new Set(masks).size===n,"signature uniqueness");
 const quotas=masks.map((mask,a)=>Array.from({length:18},(_,i)=>{
  const q=2-((mask>>>i)&1)-bits(mask&adj[i]);
  insist(q>=0&&q<=2&&q===d.row_targets[a][i],"literal mixed quota");return q;
 }));
 const pairIndex=new Int32Array(n*n).fill(-1),edgeIndex=new Int32Array(n*n).fill(-1),edges=[],disjoint=[];
 const neighbors=Array.from({length:n},()=>[]);
 let pair=0;
 for(let a=0;a<n;a++){
  tick();insist(quotas[a].reduce((u,v)=>u+v,0)===24,"mixed quota sum");
  for(let b=a+1;b<n;b++){
   pairIndex[a*n+b]=pairIndex[b*n+a]=pair++;
   const eligible=bits(masks[a]&masks[b])<=1&&d.signature_domain[b].every(i=>quotas[a][i]>0)&&d.signature_domain[a].every(i=>quotas[b][i]>0);
   if(eligible){
    const e=edges.length;edges.push([a,b]);edgeIndex[a*n+b]=edgeIndex[b*n+a]=e;neighbors[a].push(b);neighbors[b].push(a);
    if((masks[a]&masks[b])===0)disjoint.push([a,b]);
   }
  }
 }
 insist(pair===114960&&edges.length===d.complete_possible_edge_count,"complete pair-domain size");
 for(let a=0;a<n;a++)equal(neighbors[a],d.possible_neighbor_signature_ids[a],"saved eligible-neighbor row "+a);
 return {n,masks,edges,disjoint,pairIndex,edgeIndex,lower:lowerGraph(n,disjoint)};
}
function familyData(k,a,domain,codec,tick) {
 const n=domain.n,divisor=safe(k.common_numerator_divisor,"kernel divisor");
 insist(divisor>0,"positive kernel divisor");
 const divide=x=>{safe(x,"integer kernel coefficient");insist(x%divisor===0,"primitive division");return x/divisor;};
 const diagonal=k.diagonal_x.map(divide),off=k.off_diagonal_Z.map(divide),y=divide(k.Y),canonical=[];
 insist(diagonal.every(v=>v>0),"all one-dimensional minors positive");
 for(let i=0;i<n;i++)for(let j=i;j<n;j++)canonical.push(i===j?diagonal[i]:off[domain.pairIndex[i*n+j]]);
 canonical.push(y);
 const hash=codec.sha256(codec.utf8(JSON.stringify(canonical)));
 insist(hash===k.primitive_kernel_sha256&&hash===a.primitive_kernel_sha256,"full primitive coefficient hash");
 const db=diagonal.map(BigInt),eb=off.map(v=>BigInt(v)+BigInt(y)),minors=[],negative=[];
 let minimum=null,zero=0;
 for(let e=0;e<domain.edges.length;e++){
  if((e&1023)===0)tick();
  const [i,j]=domain.edges[e],v=eb[domain.pairIndex[i*n+j]],m=db[i]*db[j]-v*v;
  minors.push(m);if(minimum===null||m<minimum)minimum=m;
  if(m<0n)negative.push([i,j,m.toString()]);else if(m===0n)zero++;
 }
 return {family:k.family,hash,diagonal:db,edgeOff:eb,minors,negativePairs:negative,zeroPairs:zero,minimumPair:minimum,
  counts:{negative_proper_minor:0,negative_determinant:0,zero_determinant:0,positive_determinant:0},
  minimum:null,maximum:null,records:[]};
}
function exportFamily(f,codec) {
 const records=f.records.slice().sort((u,v)=>u[0]-v[0]||u[1]-v[1]||u[2]-v[2]);
 return {family:f.family,primitive_kernel_sha256:f.hash,negative_eligible_edge_pairs:f.negativePairs,
  zero_eligible_edge_minors:f.zeroPairs,minimum_eligible_edge_minor:f.minimumPair===null?null:f.minimumPair.toString(),counts:f.counts,
  minimum_triangle_determinant:f.minimum===null?null:f.minimum.toString(),maximum_triangle_determinant:f.maximum===null?null:f.maximum.toString(),
  nonpositive_determinant_records_with_nonnegative_proper_minors:records,
  nonpositive_records_sha256:codec.sha256(codec.utf8(JSON.stringify(records)))};
}
function disposition(plus,domain,overlay,codec,tick) {
 const hash=codec.sha256(codec.utf8(JSON.stringify(domain.edges)));
 insist(hash===overlay.complete_edge_order_sha256,"complete eligible-edge ordering");
 const zeroRows=new Map();
 for(let i=0;i<overlay.zero_rows.length;i++){
  const r=overlay.zero_rows[i],e=r.edge_id;
  insist(Number.isInteger(e)&&e>=0&&e<domain.edges.length&&!zeroRows.has(e),"unique literal zero edge");
  insist(r.native_row_index===163070+i&&r.variable_index===540+e,"native literal zero location");
  insist(r.witness.kind==="P"&&r.witness.edge_id===e,"literal zero witness kind and ID");
  equal(r.witness.pair,domain.edges[e],"literal zero endpoints");
  zeroRows.set(e,{edge_id:e,native_row_index:r.native_row_index,variable_index:r.variable_index,witness_index:r.witness_index});
 }
 const ledger=[],retained=[];
 for(let index=0;index<plus.nonpositive_determinant_records_with_nonnegative_proper_minors.length;index++){
  if((index&255)===0)tick();
  const r=plus.nonpositive_determinant_records_with_nonnegative_proper_minors[index];
  insist(BigInt(r[3])<0n,"negative-only disposition scope");
  const [a,b,c]=r,ids=[domain.edgeIndex[a*480+b],domain.edgeIndex[a*480+c],domain.edgeIndex[b*480+c]],hits=zeroHits(ids,zeroRows);
  const item={record_id:index,triangle:[a,b,c],edge_ids:ids,zero_premises:hits};
  if(hits.length)item.disposition="OLD_LITERAL_EDGE_ZERO";
  else{item.disposition="NOT_REJECTED_BY_LITERAL_EDGE_ZERO";retained.push(index);}
  ledger.push(item);
 }
 return {scope:"Only the 1884 previously proved literal edge zeros",complete_edge_order_sha256:hash,
  old_literal_edge_zero:ledger.length-retained.length,not_rejected_by_literal_edge_zero:retained.length,
  tested_triangles:ledger.length,ledger,retained_record_ids:retained,
  ledger_sha256:codec.sha256(codec.utf8(JSON.stringify(ledger))),
  other_native_or_prism_constraints_tested:false,logical_independence_claimed:false};
}
function run(configurationText,payload,codec,sourceText,codecText) {
 const started=Date.now(),progress={completed_maximum_vertex_exclusive:0,triangles:0,last_triangle:null};
 let loaded=null,domain=null,families=[],exported=[],zeroDisposition=null,error=null,complete=false;
 const tick=()=>{if(Date.now()-started>=60000)throw Error("COOPERATIVE_60_SECOND_LIMIT");};
 try{
  loaded=loadInputs(configurationText,payload,codec,sourceText,codecText,tick);
  domain=reconstructDomain(loaded.data.domain,tick);
  for(const name of ["plus","minus"])families.push(familyData(loaded.data.kernels.kernels.find(f=>f.family===name),
   loaded.data.audit.families.find(f=>f.family===name),domain,codec,tick));
  enumerate(domain.lower,(a,b,c)=>{
   if((progress.triangles&255)===0)tick();
   const n=domain.n,ab=domain.pairIndex[a*n+b],ac=domain.pairIndex[a*n+c],bc=domain.pairIndex[b*n+c];
   const ea=domain.edgeIndex[a*n+b],eb=domain.edgeIndex[a*n+c],ec=domain.edgeIndex[b*n+c];
   insist(ea>=0&&eb>=0&&ec>=0,"triangle eligible IDs");
   for(const f of families){
    const A=f.diagonal[a],B=f.diagonal[b],C=f.diagonal[c],D=f.edgeOff[ab],E=f.edgeOff[ac],F=f.edgeOff[bc];
    const det=determinant([A,D,E,D,B,F,E,F,C]),proper=[f.minors[ea],f.minors[eb],f.minors[ec]];
    if(f.minimum===null||det<f.minimum)f.minimum=det;if(f.maximum===null||det>f.maximum)f.maximum=det;
    if(proper.some(v=>v<0n)){f.counts.negative_proper_minor++;continue;}
    if(det<0n)f.counts.negative_determinant++;else if(det===0n)f.counts.zero_determinant++;else f.counts.positive_determinant++;
    if(det<=0n){
     insist(families.reduce((s,q)=>s+q.records.length,0)<loaded.cfg.limits.maximum_nonpositive_records,"nonpositive record limit");
     f.records.push([a,b,c,det.toString(),...proper.map(String)]);
    }
   }
   progress.triangles++;progress.last_triangle=[a,b,c];
  },tick,c=>{progress.completed_maximum_vertex_exclusive=c;});
  tick();exported=families.map(f=>exportFamily(f,codec));
  const forward=loaded.data.forward;
  insist(forward.selectors===domain.n&&forward.original_eligible_edges===domain.edges.length&&forward.pairwise_disjoint_signature_edges===domain.disjoint.length&&forward.pairwise_disjoint_eligible_triangles===progress.triangles,"forward complete domain counts");
  for(const f of exported){
   const saved=forward.families.find(q=>q.family===f.family);insist(saved,"saved family");
   for(const key of ["primitive_kernel_sha256","negative_eligible_edge_pairs","zero_eligible_edge_minors","minimum_eligible_edge_minor","counts","minimum_triangle_determinant","maximum_triangle_determinant","nonpositive_determinant_records_with_nonnegative_proper_minors"])
    equal(f[key],saved[key],"complete forward family comparison "+f.family+"/"+key);
  }
  tick();zeroDisposition=disposition(exported.find(f=>f.family==="plus"),domain,loaded.data.overlay,codec,tick);
  insist(zeroDisposition.old_literal_edge_zero===loaded.cfg.expected_disposition.old_literal_edge_zero&&zeroDisposition.not_rejected_by_literal_edge_zero===loaded.cfg.expected_disposition.not_rejected_by_literal_edge_zero,"independent literal-zero disposition counts");
  tick();complete=true;
 }catch(e){error=String(e&&e.message?e.message:e);}
 if(!exported.length)exported=families.map(f=>exportFamily(f,codec));
 const result={schema:SCHEMA,status:complete?"PASS_COMPLETE_INDEPENDENT_CENSUS_AND_LITERAL_ZERO_DISPOSITION":"UNACCEPTED_PARTIAL_OR_MISMATCH",
  complete,source_sha256:loaded?loaded.source_sha256:null,configuration_sha256:codec.sha256(codec.utf8(configurationText)),
  input_bindings:loaded?loaded.bindings:null,progress,
  selectors:domain?domain.n:null,original_eligible_edges:domain?domain.edges.length:null,
  pairwise_disjoint_signature_edges:domain?domain.disjoint.length:null,
  pairwise_disjoint_eligible_triangles:progress.triangles,families:exported,literal_zero_disposition:zeroDisposition,
  error,seconds:(Date.now()-started)/1000,maximum_ms:60000,
  enumeration:"largest vertex, middle lower neighbor, intersection of both lower-neighbor bitsets",
  determinants:"all six permutation terms evaluated as BigInt in both families",
  scope:"All pairwise-disjoint triangles of the frozen complete eligible-pair domain; accepted full21 kernels are premises",
  overlapping_signature_triangles_enumerated:false,kernel_inverse_recomputed:false,old_zero_edges_removed_before_census:false,
  producer_or_classifier_math_executed:false,optimizer_calls:0,graph_constructed:false,whole_component_excluded:false};
 const bytes=codec.utf8(JSON.stringify(result)).length;
 insist(bytes<=67108864,"terminal report byte limit");
 return result;
}
return {controls,prepare,run};
})()
