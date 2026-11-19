(() => {
"use strict";
const FORMAT=["a","b","edge_id_or_minus1","signature_overlap","fiber_profile_dot","B_ab_at_y0_n0","determinants_y0_by_n","determinants_y1_by_n_or_null","allowed_n_bitmask_y0","allowed_n_bitmask_y1"];
const LIMIT=90000,SAFE=9007199254740991n;
function insist(ok,message){if(!ok)throw Error(message);}
function canonical(v){if(Array.isArray(v))return "["+v.map(canonical).join(",")+"]";if(v!==null&&typeof v==="object")return "{"+Object.keys(v).sort().map(k=>JSON.stringify(k)+":"+canonical(v[k])).join(",")+"}";return JSON.stringify(v);}
function equal(a,b,message){insist(canonical(a)===canonical(b),message);}
function integer(x,message){insist(Number.isSafeInteger(x),message);return BigInt(x);}
function number(x){insist(x>=-SAFE&&x<=SAFE,"safe report integer");return Number(x);}
function reference(a,b,message){for(const k of ["path","bytes","sha256","git_blob"])insist(a&&b&&a[k]===b[k],message+" "+k);}
function archiveReference(a,b,message){for(const k of ["path","archive_bytes","archive_sha256","archive_git_blob","raw_bytes","raw_sha256"])insist(a&&b&&a[k]===b[k],message+" "+k);}
function floorDiv(a,b){insist(b>0n,"positive divisor");const q=a/b,r=a%b;return r<0n?q-1n:q;}
function ceilDiv(a,b){return -floorDiv(-a,b);}
function sqrtFloor(n){insist(n>=0n,"nonnegative radicand");if(n<2n)return n;let x=1n<<BigInt(Math.ceil(n.toString(2).length/2));for(;;){const y=(x+n/x)/2n;if(y>=x)return x;x=y;}}
function intervalMask(product,base,cap,step=180n){
 const r=sqrtFloor(product);let lo=ceilDiv(-r-base,step),hi=floorDiv(r-base,step),mask=0;
 if(lo<0n)lo=0n;if(hi>BigInt(cap))hi=BigInt(cap);
 for(let n=lo;n<=hi;n++)mask|=1<<Number(n);
 return mask;
}
function expanded(z,s,y,n,dot){return 2n*z-360n+180n*BigInt(s)+180n*BigInt(n)-900n*BigInt(y)+30n*BigInt(dot);}
function rowDecisions(allowed,edge){
 return {edge_zero:edge&&allowed[1]===0,pair_cover:allowed[0]===0&&(!edge||allowed[1]===0),forced_edge:edge&&allowed[0]===0&&allowed[1]!==0};
}
function controls(){
 let roots=0,divisions=0,intervals=0,scalings=0,assignments=0,mutations=0;
 for(let n=0;n<=4096;n++){const q=sqrtFloor(BigInt(n));insist(q===BigInt(Math.floor(Math.sqrt(n))),"small square root");roots++;}
 const r=(1n<<65n)+17n;for(const n of [r*r-1n,r*r,r*r+1n]){const q=sqrtFloor(n);insist(q*q<=n&&(q+1n)*(q+1n)>n,"large square root");roots++;}
 for(let a=-200;a<=200;a++)for(const b of [1,2,3,7,180]){insist(floorDiv(BigInt(a),BigInt(b))===BigInt(Math.floor(a/b))&&ceilDiv(BigInt(a),BigInt(b))===BigInt(Math.ceil(a/b)),"signed integer division");divisions++;}
 for(let a=1;a<=5;a++)for(let b=1;b<=5;b++)for(let base=-20;base<=20;base++)for(let cap=0;cap<=3;cap++)for(const step of [1n,7n,180n]){
  let direct=0;for(let n=0;n<=cap;n++){const v=BigInt(base)+step*BigInt(n);if(BigInt(a*b)-v*v>=0n)direct|=1<<n;}
  insist(intervalMask(BigInt(a*b),BigInt(base),cap,step)===direct,"integer interval versus complete minors");intervals++;
 }
 for(const z of [-677n,0n,577n])for(let s=0;s<=2;s++)for(let y=0;y<=1;y++)for(let n=0;n<=2-s-y;n++)for(let dot=0;dot<=6;dot++){
  insist(expanded(z,s,y,n,dot)===2n*(z-540n*BigInt(y))-180n*BigInt(2-s-n-y)+30n*BigInt(dot),"expanded B identity");scalings++;
 }
 for(let mask=0;mask<4;mask++)for(let a=0;a<2;a++)for(let b=0;b<2;b++)for(let y=0;y<2;y++){
  if(y>a||y>b)continue;const d=rowDecisions([mask&1,mask&2],true);
  const pass=(!d.edge_zero||y===0)&&(!d.pair_cover||a+b<=1)&&(!d.forced_edge||y>=a+b-1);
  insist(pass===(!(a&&b)||Boolean(mask&(1<<y))),"full guarded-row truth table");assignments++;
 }
 const ref={path:"p",bytes:3,sha256:"s",git_blob:"g"};
 reference({...ref,mode:"100644"},{...ref,historical:true},"extra metadata allowed");
 for(const key of Object.keys(ref)){let caught=false;try{reference({...ref,[key]:null},ref,"mutation");}catch(e){caught=true;}insist(caught,"reference mutation rejected");mutations++;}
 const huge=(1n<<54n)+7n;insist(huge*huge-(huge-1n)*(huge+1n)===1n,"exact large determinant");
 return {status:"PASS_INDEPENDENT_INTEGER_INTERVAL_SCALING_AND_GUARD_CONTROLS",square_roots:roots,signed_divisions:divisions,interval_masks:intervals,expanded_scalings:scalings,activated_assignments:assignments,reference_mutations_rejected:mutations,extra_metadata_reference_control:true,bigint_boundary:true,production_inputs_used:false,optimizer_calls:0,native_model_builds:0};
}
function verifyAuthority(cfg,parsed){
 const fc=parsed.forward_configuration,fin=parsed.finalization,gate=parsed.forward_gate,forward=parsed.forward,ctl=parsed.forward_controls;
 insist(fc.schema==="conway99.f0.spectral-gap-pair-configuration.v1","forward configuration");
 for(const [field,name] of [["source","forward_source"],["runner","forward_runner"],["theorem","theorem"],["theorem_review","theorem_review"],["source_review","forward_source_review"],["controls","forward_controls"],["accepted_direct_audit","audit"]])reference(fc[field],cfg.texts[name],"forward "+field);
 reference(fc.codec,cfg.sources.codec,"forward codec");
 const oldLimits={census_ms:30000,wrapper_ms:60000,maximum_input_raw_bytes:67108864,maximum_report_bytes:33554432,automatic_retries:0};
 equal(fc.limits,oldLimits,"forward limits");insist(fc.inputs.length===3,"three forward archives");
 ["domain","kernels","overlay"].forEach((name,i)=>archiveReference(fc.inputs[i],cfg.archives[name],"forward archive "+name));
 insist(fc.scope.signature_pairs===114960&&fc.scope.eligible_edges===68394&&fc.scope.adjacency_zero_always===true&&fc.scope.adjacency_one_only_original_eligible===true&&fc.scope.literal_zeros_only_for_disposition===true,"forward universe");
 insist(ctl.schema==="conway99.f0.spectral-gap-pair-controls.v1"&&ctl.result.status==="PASS_PROFILE_IDENTITY_SCALING_AND_ACTIVATION_CONTROLS"&&ctl.main_run===false,"forward controls");
 reference(ctl.source,cfg.texts.forward_source,"control source");
 equal(ctl.result,{status:"PASS_PROFILE_IDENTITY_SCALING_AND_ACTIVATION_CONTROLS",fiber_profile_pairs:49,scaled_states:1323,activated_guard_cases:16,explicit_minors:3,bigint_boundary_control:true},"complete control receipt");
 insist(gate.schema==="conway99.f0.spectral-gap-pair-root-gate.v1"&&gate.status==="AUTHORIZED_ONE_BOUNDED_COMPLETE_PAIR_STATE_CENSUS"&&gate.runs_authorized===1,"forward root gate");
 for(const [field,name] of [["configuration","forward_configuration"],["source","forward_source"],["runner","forward_runner"],["theorem","theorem"],["independent_math_review","theorem_review"],["independent_source_review","forward_source_review"],["controls","forward_controls"]])reference(gate[field],cfg.texts[name],"gate "+field);
 equal(gate.limits,oldLimits,"gate limits");
 insist(fin.schema==="conway99.f0.spectral-gap-pair-finalization.v1"&&fin.status==="COMPLETE_WITHIN_CENSUS_SERIALIZATION_AND_BYTE_LIMITS","complete forward finalization");
 for(const [field,name] of [["source","forward_source"],["configuration","forward_configuration"],["root_gate","forward_gate"],["report","forward"]])reference(fin[field],cfg.texts[name],"finalization "+field);
 equal(fin.limits,oldLimits,"finalization limits");insist(fin.inputs.length===3,"finalization archives");
 ["domain","kernels","overlay"].forEach((name,i)=>{archiveReference(fin.inputs[i],cfg.archives[name],"final archive "+name);insist(fin.inputs[i].archive_and_raw_reverified===true,"forward archive verified");});
 insist(Number.isFinite(fin.seconds)&&fin.seconds>=0&&fin.seconds*1000<60000&&fin.serialized_bytes===cfg.texts.forward.bytes&&fin.publication_hashing_in_timed_main===false,"forward finalization bounds");
 insist(forward.schema==="conway99.f0.spectral-gap-pair-census.v1"&&forward.status==="COMPLETE_FORWARD_PAIR_AND_INTEGER_COMMON_NEIGHBOR_CENSUS","forward terminal");
 insist(Number.isFinite(forward.seconds)&&forward.seconds>=0&&forward.seconds*1000<30000&&forward.maximum_ms===30000,"forward arithmetic bound");
 for(const v of [forward,fin])insist(v.optimizer_calls===0&&v.native_model_builds===0&&v.whole_component_excluded===false,"forward scope");
 insist(forward.graph_constructed===false&&forward.old_literal_zeros_used_only_for_disposition===true&&forward.pair_covers_not_compared_to_old_rows===true&&forward.forced_adjacencies_not_compared_to_old_rows===true,"forward qualifications");
 insist(parsed.audit.status==="PASS: exact full-core Schur corrections; no point query"&&parsed.audit.families[0].family==="plus"&&parsed.audit.families[0].all_115440_full_vs_old_kernel_entries_checked===true,"accepted direct audit");
 insist(parsed.theorem_review.status==="PASS_MATHEMATICAL_NECESSITY"&&parsed.theorem_review.complete_subject_read===true,"independent theorem review");
 reference(parsed.theorem_review.subject,cfg.texts.theorem,"reviewed theorem");
 insist(parsed.forward_source_review.status==="PASS_SOURCE_BOUND_COMPLETE_PAIR_STATE_CENSUS_REVIEW","forward source review");
 reference(parsed.forward_source_review.source,cfg.texts.forward_source,"reviewed source");
}
function reconstruct(domain,kernels,overlay,codec,tick){
 const h=domain.signature_domain,core=domain.component_core_rows,N=480;
 insist(Array.isArray(h)&&h.length===N&&core.length===21,"domain dimensions");
 for(let i=0;i<21;i++){integer(core[i],"core row");insist(core[i]>=0&&core[i]<2**21&&((core[i]>>>i)&1)===0,"core bits");for(let j=0;j<21;j++)insist(((core[i]>>>j)&1)===((core[j]>>>i)&1),"symmetric core");}
 for(let i=0;i<3;i++)for(let j=0;j<3;j++)insist(((core[i]>>>j)&1)===Number(i!==j),"central triangle");
 const C=Array.from({length:18},(_,i)=>Array.from({length:18},(_,j)=>(core[i+3]>>>(j+3))&1));
 const fiber=Array.from({length:18},(_,j)=>{const f=[];for(let i=0;i<3;i++)if((core[j+3]>>>i)&1)f.push(i);insist(f.length===1,"unique central neighbor");return f[0];});
 for(let i=0;i<3;i++)insist(fiber.filter(x=>x===i).length===6,"six sites per fiber");
 for(let i=0;i<18;i++){insist(C[i].reduce((a,b)=>a+b,0)===3,"cubic component");for(let f=0;f<3;f++)insist(C[i].reduce((s,v,j)=>s+v*(fiber[j]===f),0)===1,"one neighbor per fiber");}
 equal(C.map(row=>row.reduce((s,v,j)=>s+v*2**j,0)),domain.component_adjacency_rows,"component rows");
 const sites=h.map(t=>{insist(t.length===3&&t.every((v,i)=>Number.isInteger(v)&&v>=0&&v<18&&(i===0||t[i-1]<v)),"ordered weight-three signature");const v=Array(18).fill(0);for(const j of t)v[j]=1;return v;});
 insist(new Set(h.map(t=>t.join(","))).size===N,"unique signatures");
 const quota=sites.map(v=>C.map((row,i)=>2-v[i]-row.reduce((s,x,j)=>s+x*v[j],0)));
 insist(quota.every(row=>row.every(x=>Number.isInteger(x)&&x>=0&&x<=2)),"nonnegative mixed quotas");
 equal(quota,domain.row_targets,"all mixed quotas");
 const eta=h.map(t=>{const p=[0,0,0];for(const j of t)p[fiber[j]]++;insist(p.every(x=>x>=0&&x<=2),"fiber profile");return p;});
 equal(eta,kernels.fiber_counts,"accepted profile table");
 const plus=kernels.kernels.find(v=>v.family==="plus");insist(plus&&plus.Schur_coefficient_denominator===60&&plus.common_numerator_divisor===1&&plus.Y===-540&&plus.diagonal_x.length===N&&plus.off_diagonal_Z.length===114960,"plus kernel");
 const slots=new Int32Array(N*N),off=new Int32Array(N*N);slots.fill(-1);let p=0;const primitive=[];
 for(let a=0;a<N;a++){integer(plus.diagonal_x[a],"kernel diagonal");primitive.push(plus.diagonal_x[a]);for(let b=a+1;b<N;b++){const z=plus.off_diagonal_Z[p];integer(z,"kernel pair");insist(Math.abs(z)<2**31,"small coefficient transport");slots[a*N+b]=p;off[a*N+b]=z;primitive.push(z);p++;}}
 primitive.push(-540);insist(p===114960&&codec.sha256(codec.utf8(JSON.stringify(primitive)))==="91017b1ad1ea6ff3433e91030586ec820f939a158f8cf3aab0cbf77e4ef574ed","complete primitive kernel hash");
 const eligible=[];
 for(let b=1;b<N;b++){if((b&31)===0)tick();for(let a=0;a<b;a++){let s=0;for(const j of h[a])s+=sites[b][j];if(s<=1&&h[a].every(j=>quota[b][j]>0)&&h[b].every(j=>quota[a][j]>0))eligible.push([a,b]);}}
 eligible.sort((a,b)=>a[0]-b[0]||a[1]-b[1]);
 insist(eligible.length===68394&&codec.sha256(codec.utf8(JSON.stringify(eligible)))==="411052a41a473bb7199fe277516fb60c54018dec120309622a499229579791bb","complete eligible edge order");
 const edges=new Int32Array(N*N);edges.fill(-1);const neighbors=Array.from({length:N},()=>[]);
 eligible.forEach(([a,b],e)=>{edges[a*N+b]=e;neighbors[a].push(b);neighbors[b].push(a);});
 for(const row of neighbors)row.sort((a,b)=>a-b);equal(neighbors,domain.possible_neighbor_signature_ids,"complete saved neighbor lists");
 insist(overlay.complete_edge_order_sha256==="411052a41a473bb7199fe277516fb60c54018dec120309622a499229579791bb","overlay namespace");
 const zeros=new Set();for(const row of overlay.zero_rows){insist(Number.isInteger(row.edge_id)&&row.edge_id>=0&&row.edge_id<68394&&!zeros.has(row.edge_id),"unique valid old zero");zeros.add(row.edge_id);}
 insist(zeros.size===1884,"complete old zero family");
 const diagonal=eta.map((v,a)=>{const norm=v.reduce((s,x)=>s+x*x,0);insist(norm===3||norm===5,"profile norm");const d=2n*BigInt(plus.diagonal_x[a])-540n+30n*BigInt(norm);insist(d>=1042n&&d<=2086n,"positive integer diagonal");return d;});
 return {h,core,sites,eta,slots,off,edges,zeros,diagonal};
}
function replay(data,forward,tick,progress){
 const {h,core,sites,eta,slots,off,edges,zeros,diagonal}=data,N=480;
 equal(eta,forward.eta,"all saved eta");equal(diagonal.map(number),forward.diagonal,"all saved diagonals");equal(forward.record_format,FORMAT,"record schema");
 insist(forward.complete_pair_state_records.length===114960,"complete saved records");
 const counts={pairs:0,eligible_edges:0,states:0,negative_minor:0,zero_minor:0,positive_minor:0},hist={},edgeZero=[],pairCover=[],forcedEdge=[],restricted=[];
 const edgeNeedsTriangle=[],pairCommonCapOne=[],gramCovers=[],seen=new Uint8Array(114960);
 let minimum=null,maximum=null,intervalChecks=0;
 for(let b=1;b<N;b++){
  tick();progress.completed_larger_endpoint_exclusive=b;
  for(let a=0;a<b;a++){
   const address=a*N+b,p=slots[address],e=edges[address];insist(p>=0&&!seen[p],"independent pair coverage");seen[p]=1;
   let s=0;for(const j of h[a])s+=sites[b][j];const etaDot=eta[a].reduce((q,x,i)=>q+x*eta[b][i],0),z=BigInt(off[address]);
   const values=[[],e<0?null:[]],allowed=[0,0],product=diagonal[a]*diagonal[b];
   if(e>=0)counts.eligible_edges++;
   for(let y=0;y<=1;y++){
    if(y&&e<0)continue;const cap=2-s-y;insist(cap>=0&&cap<=2,"complete conservative count interval");
    for(let n=0;n<=cap;n++){
     const v=expanded(z,s,y,n,etaDot),det=product-v*v;values[y].push(number(det));counts.states++;
     if(det<0n)counts.negative_minor++;else{allowed[y]|=1<<n;if(det===0n)counts.zero_minor++;else counts.positive_minor++;}
     if(minimum===null||det<minimum)minimum=det;if(maximum===null||det>maximum)maximum=det;
    }
    const independent=intervalMask(product,expanded(z,s,y,0,etaDot),cap);
    insist(independent===allowed[y],"independent integer-square-root allowed interval");intervalChecks++;
   }
   const row=[a,b,e,s,etaDot,number(expanded(z,s,0,0,etaDot)),values[0],values[1],allowed[0],allowed[1]];
   equal(row,forward.complete_pair_state_records[p],"complete pair record "+a+","+b);
   const key=s+":"+(e>=0?1:0)+":"+allowed[0]+":"+allowed[1];hist[key]=(hist[key]||0)+1;
   const decision=rowDecisions(allowed,e>=0);
   if(decision.edge_zero)edgeZero.push([a,b,e,zeros.has(e)]);
   if(decision.pair_cover){
    pairCover.push([a,b,e]);const common=h[a].filter(j=>sites[b][j]);
    insist(common.length===2,"cover shared pair");const [i,j]=common;let knownCommon=0;
    for(let k=0;k<21;k++)knownCommon+=((core[i+3]>>>k)&1)*((core[j+3]>>>k)&1);
    const gram=2-knownCommon-((core[i+3]>>>(j+3))&1);
    insist(gram===1,"existing unit Gram cover witness");gramCovers.push([a,b,i,j,gram]);
   }
   if(decision.forced_edge)forcedEdge.push([a,b,e]);
   if(values[0].some(x=>x<0)||(values[1]&&values[1].some(x=>x<0)))restricted.push(p);
   if(e>=0&&allowed[1]===2)edgeNeedsTriangle.push([a,b,e,zeros.has(e)]);
   if(s===0&&(allowed[0]!==0||allowed[1]!==0)&&(allowed[0]&4)===0)pairCommonCapOne.push([a,b,e]);
   counts.pairs++;progress.pairs=counts.pairs;progress.states=counts.states;
  }
 }
 progress.completed_larger_endpoint_exclusive=N;
 insist(seen.every(x=>x===1)&&counts.pairs===114960&&counts.eligible_edges===68394&&counts.states===405426,"complete independent enumeration");
 insist(counts.negative_minor+counts.zero_minor+counts.positive_minor===counts.states,"state sign accounting");
 for(const rows of [edgeZero,pairCover,forcedEdge,gramCovers,edgeNeedsTriangle,pairCommonCapOne])rows.sort((a,b)=>a[0]-b[0]||a[1]-b[1]);restricted.sort((a,b)=>a-b);
 equal(counts,forward.counts,"all forward counts");equal(hist,forward.state_mask_histogram,"all state-mask classes");
 equal(edgeZero,forward.edge_zero_rows,"every edge-zero row and old-zero disposition");equal(pairCover,forward.selector_pair_cover_rows,"every selector cover");equal(forcedEdge,forward.forced_adjacency_rows,"every forced adjacency");equal(restricted,forward.pairs_with_any_rejected_integer_state,"every restricted pair index");
 insist(minimum.toString()===forward.minimum_determinant&&maximum.toString()===forward.maximum_determinant,"determinant extrema");
 const old=edgeZero.filter(r=>r[3]).length;insist(old===forward.edge_zeros_already_literal&&edgeZero.length-old===forward.edge_zeros_not_in_literal_zero_family,"complete literal-zero disposition");
 tick();
 return {counts,minimum_determinant:minimum.toString(),maximum_determinant:maximum.toString(),state_mask_histogram:hist,independent_integer_interval_checks:intervalChecks,
  edge_zero_rows:edgeZero,selector_pair_cover_rows:pairCover,forced_adjacency_rows:forcedEdge,
  edge_zeros_already_literal:old,edge_zeros_outside_literal_family:edgeZero.length-old,
  selector_covers_existing_unit_gram_witnesses:gramCovers,edge_present_requires_one_common_exterior_neighbor:edgeNeedsTriangle,
  overlap_zero_selected_pair_common_exterior_neighbor_cap_one:pairCommonCapOne,pairs_with_rejected_states:restricted.length};
}
function run(bundle,codec,configurationText){
 const started=Date.now(),result={report:null,text:null,finalization:null},progress={phase:"binding",pairs:0,states:0,completed_larger_endpoint_exclusive:1};
 let cfg=null,configurationSha=null;const bindings={texts:{},archives:{},sources:{}};
 function tick(){insist(Date.now()-started<LIMIT,"independent complete replay deadline");}
 function bindText(text,ref,label){insist(typeof text==="string","text input "+label);const b=codec.utf8(text);insist(b.length===ref.bytes&&codec.sha256(b)===ref.sha256&&codec.gitBlob(b)===ref.git_blob,"exact text binding "+label);return text;}
 try{
  cfg=JSON.parse(configurationText);configurationSha=codec.sha256(codec.utf8(configurationText));
  insist(cfg.schema==="conway99.f0.spectral-gap-pair-independent-cold-configuration.v1","cold configuration");
  equal(cfg.limits,{maximum_ms:90000,maximum_input_raw_bytes:16777216,maximum_report_bytes:1048576,automatic_retries:0},"cold finite limits");
  equal(Object.keys(cfg.sources).sort(),["codec","self"],"cold source set");
  for(const name of ["self","codec"]){bindText(bundle.sources[name],cfg.sources[name],"source "+name);bindings.sources[name]=cfg.sources[name];tick();}
  const names=["audit","forward","finalization","forward_configuration","forward_gate","forward_controls","forward_source","forward_runner","theorem","theorem_review","forward_source_review","cold_controls"];
  equal(Object.keys(cfg.texts).sort(),names.slice().sort(),"cold text set");
  const parsed={};for(const name of names){const text=bindText(bundle.texts[name],cfg.texts[name],name);bindings.texts[name]=cfg.texts[name];if(!["forward_source","forward_runner","theorem"].includes(name))parsed[name]=JSON.parse(text);tick();}
  insist(parsed.cold_controls.schema==="conway99.f0.spectral-gap-pair-independent-cold-controls.v1"&&parsed.cold_controls.result.status==="PASS_INDEPENDENT_INTEGER_INTERVAL_SCALING_AND_GUARD_CONTROLS"&&parsed.cold_controls.main_run===false,"accepted cold controls");
  reference(parsed.cold_controls.source,cfg.sources.self,"cold controls source");
  equal(parsed.cold_controls.result,{status:"PASS_INDEPENDENT_INTEGER_INTERVAL_SCALING_AND_GUARD_CONTROLS",square_roots:4100,signed_divisions:2005,interval_masks:12300,expanded_scalings:189,activated_assignments:20,reference_mutations_rejected:4,extra_metadata_reference_control:true,bigint_boundary:true,production_inputs_used:false,optimizer_calls:0,native_model_builds:0},"complete cold controls receipt");
  verifyAuthority(cfg,parsed);
  equal(Object.keys(cfg.archives).sort(),["domain","kernels","overlay"],"three cold archives");
  const decoded={};for(const name of ["domain","kernels","overlay"]){
   const ref=cfg.archives[name],archive=codec.base64(bundle.archives[name]);
   insist(archive.length===ref.archive_bytes&&codec.sha256(archive)===ref.archive_sha256&&codec.gitBlob(archive)===ref.archive_git_blob,"exact archive binding "+name);
   const raw=codec.gunzip(archive,cfg.limits.maximum_input_raw_bytes);insist(raw.length===ref.raw_bytes&&codec.sha256(raw)===ref.raw_sha256,"exact raw binding "+name);
   decoded[name]=JSON.parse(codec.ascii(raw));bindings.archives[name]={...ref,archive_and_raw_reverified:true};tick();
  }
  progress.phase="independent_domain_reconstruction";const data=reconstruct(decoded.domain,decoded.kernels,decoded.overlay,codec,tick);
  progress.phase="complete_reverse_pair_order_replay";const mathematical=replay(data,parsed.forward,tick,progress);
  equal(mathematical.counts,cfg.expected_counts,"frozen complete counts");
  equal({edge_zeros:mathematical.edge_zero_rows.length,already_literal:mathematical.edge_zeros_already_literal,outside_literal:mathematical.edge_zeros_outside_literal_family,selector_covers:mathematical.selector_pair_cover_rows.length,forced_adjacencies:mathematical.forced_adjacency_rows.length,restricted_pairs:mathematical.pairs_with_rejected_states,edge_present_requires_n1:mathematical.edge_present_requires_one_common_exterior_neighbor.length,extra_overlap_zero_cap1:mathematical.overlap_zero_selected_pair_common_exterior_neighbor_cap_one.length},cfg.expected_deductions,"complete deductions and dispositions");
  progress.phase="complete";
  result.report={schema:"conway99.f0.spectral-gap-pair-independent-cold.v1",status:"PASS_COMPLETE_INDEPENDENT_SPECTRAL_GAP_PAIR_CENSUS",complete:true,
   source:cfg.sources.self,configuration_sha256:configurationSha,input_bindings:bindings,forward:cfg.texts.forward,forward_finalization:cfg.texts.finalization,
   progress,mathematical,all114960_saved_pair_records_checked:true,all405426_saved_integer_determinants_checked:true,
   different_pair_order:"larger endpoint outermost",expanded_B_expression_used:true,allowed_masks_independently_checked_by_integer_square_root_intervals:true,
   full_original_edge_namespace_and_every_neighbor_list_reconstructed:true,all_old_literal_zero_dispositions_checked:true,
   all_six_selector_covers_already_implied_by_unit_Gram_rows:true,graph_or_component_excluded:false,
   newness_of_rows_against_all_existing_constraints_not_claimed:true,producer_or_runner_math_executed:false,
   optimizer_calls:0,native_model_builds:0,seconds:(Date.now()-started)/1000};
  result.text=JSON.stringify(result.report)+"\n";insist(result.text.length<=cfg.limits.maximum_report_bytes,"cold serialized report size");
  for(let i=0;i<result.text.length;i++)insist(result.text.charCodeAt(i)<128,"ASCII cold report byte count");tick();
  result.finalization={schema:"conway99.f0.spectral-gap-pair-independent-cold-finalization.v1",status:"PASS_COMPLETE_COLD_AND_SERIALIZATION_WITHIN_BOUND",
   source:cfg.sources.self,configuration_sha256:configurationSha,seconds:(Date.now()-started)/1000,serialized_report_bytes:result.text.length,maximum_ms:LIMIT,
   report_sha256_to_be_bound_after_timed_main:true,publication_hashing_in_timed_main:false,optimizer_calls:0,native_model_builds:0,automatic_retries:0};
 }catch(error){
  result.finalization={schema:"conway99.f0.spectral-gap-pair-independent-cold-finalization.v1",status:"UNACCEPTED_INDEPENDENT_COLD_FAILURE_NO_AUTOMATIC_RETRY",
   error:String(error),progress,seconds:(Date.now()-started)/1000,configuration_sha256:configurationSha,source:cfg?cfg.sources.self:null,
   report_returned:result.report!==null,serialized_report_retained:result.text!==null,input_bindings:bindings,optimizer_calls:0,native_model_builds:0,automatic_retries:0};
 }
 return result;
}
return {controls,run};
})()
