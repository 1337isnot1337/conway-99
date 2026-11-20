(() => {
"use strict";
function need(ok,message){if(!ok)throw Error(message);}
function pop(x){let n=0;while(x){x&=x-1;n++;}return n;}
function pairId(a,b){need(a<b,"ordered pair");return a*(959-a)/2+b-a-1;}
function dot(a,b){return a.reduce((s,x,i)=>s+x*b[i],0);}
function off(z,s,y,n,etaDot){return 2*(z-540*y)-180*(2-s-n-y)+30*etaDot;}
function determinant(a,b,c){return BigInt(a)*BigInt(b)-BigInt(c)*BigInt(c);}
function controls(){
 const profiles=[];for(let a=0;a<=2;a++)for(let b=0;b<=2;b++)for(let c=0;c<=2;c++)if(a+b+c===3)profiles.push([a,b,c]);
 let fiberPairs=0,states=0,guards=0;
 for(const a of profiles)for(const b of profiles){
  const ac=a.map(x=>2-x),bc=b.map(x=>2-x);
  need(dot(a,b)===dot(ac,bc),"complementary profile Gram identity");fiberPairs++;
 }
 for(const z of [-677,0,577])for(let s=0;s<=2;s++)for(let y=0;y<=1;y++)for(let n=0;n<=2-s-y;n++)for(const p of profiles)for(const q of profiles){
  const value=off(z,s,y,n,dot(p,q)),expanded=2*z-360+180*s+180*n-900*y+30*dot(p,q);
  need(value===expanded,"integer scaling expansion");states++;
 }
 // All possible allowed y-state masks and endpoint-activated Boolean assignments.
 for(let mask=0;mask<4;mask++)for(let a=0;a<2;a++)for(let b=0;b<2;b++)for(let y=0;y<2;y++){
  if(y>a||y>b)continue;
  const feasible=!(a&&b)||Boolean(mask&(1<<y));
  if(!feasible)continue;guards++;
  if(!(mask&2))need(y===0,"edge-zero activation guard");
  if(mask===0)need(a+b<=1,"selector pair-cover guard");
  if(!(mask&1))need(y>=a+b-1,"forced-adjacency guard");
 }
 need(determinant(2,3,1)===5n&&determinant(1,1,1)===0n&&determinant(1,1,2)===-3n,"explicit principal minors");
 const large=9007199254740993n;
 need(large*large-(large-1n)*(large+1n)===1n,"BigInt exceeds safe-integer boundary");
 return {status:"PASS_PROFILE_IDENTITY_SCALING_AND_ACTIVATION_CONTROLS",fiber_profile_pairs:fiberPairs,scaled_states:states,activated_guard_cases:guards,explicit_minors:3,bigint_boundary_control:true};
}
function run(domain,kernels,overlay,sha256Text){
 const start=Date.now(),maximumMs=30000,tick=()=>need(Date.now()-start<maximumMs,"spectral pair census deadline");
 const h=domain.signature_domain,core=domain.component_core_rows,C=domain.component_adjacency_rows;
 need(h.length===480&&core.length===21&&C.length===18,"dimensions");
 const plus=kernels.kernels.find(k=>k.family==="plus");
 need(plus&&plus.Schur_coefficient_denominator===60&&plus.common_numerator_divisor===1&&plus.Y===-540,"plus full-core scaling");
 need(plus.diagonal_x.length===480&&plus.off_diagonal_Z.length===114960,"complete kernel sizes");
 need(plus.diagonal_x.concat(plus.off_diagonal_Z).every(Number.isSafeInteger),"integer kernel");
 const primitive=[];
 for(let a=0;a<480;a++)for(let b=a;b<480;b++)primitive.push(a===b?plus.diagonal_x[a]:plus.off_diagonal_Z[pairId(a,b)]);
 primitive.push(-540);
 need(sha256Text(JSON.stringify(primitive))==="91017b1ad1ea6ff3433e91030586ec820f939a158f8cf3aab0cbf77e4ef574ed","accepted primitive kernel value hash");
 for(let i=0;i<18;i++)need(C[i]===(core[i+3]>>>3)&&pop(C[i])===3,"component adjacency");
 const masks=h.map(t=>{need(t.length===3&&new Set(t).size===3&&t.every(i=>Number.isInteger(i)&&i>=0&&i<18),"signature");return t.reduce((s,i)=>s|(1<<i),0);});
 need(new Set(masks).size===480,"distinct signatures");
 const q=masks.map(m=>Array.from({length:18},(_,i)=>2-((m>>>i)&1)-pop(m&C[i])));
 need(JSON.stringify(q)===JSON.stringify(domain.row_targets),"all quotas recomputed");
 const eta=h.map(t=>core.slice(0,3).map(row=>t.reduce((s,j)=>s+((row>>>(j+3))&1),0)));
 for(let j=0;j<18;j++)need(core.slice(0,3).reduce((s,row)=>s+((row>>>(j+3))&1),0)===1,"core fiber partition");
 need(JSON.stringify(eta)===JSON.stringify(kernels.fiber_counts),"all fiber profiles rebound");
 for(const p of eta)need(p.reduce((s,x)=>s+x,0)===3&&p.every(x=>x>=0&&x<=2),"allowed profile");
 const edges=[],neighbors=Array.from({length:480},()=>[]),edgeIds=new Int32Array(114960);edgeIds.fill(-1);
 for(let a=0;a<480;a++)for(let b=a+1;b<480;b++){
  if(pop(masks[a]&masks[b])<=1&&h[a].every(i=>q[b][i]>0)&&h[b].every(i=>q[a][i]>0)){
   edgeIds[pairId(a,b)]=edges.length;edges.push([a,b]);neighbors[a].push(b);neighbors[b].push(a);
  }
 }
 need(edges.length===68394&&sha256Text(JSON.stringify(edges))==="411052a41a473bb7199fe277516fb60c54018dec120309622a499229579791bb","complete eligible namespace");
 need(JSON.stringify(neighbors)===JSON.stringify(domain.possible_neighbor_signature_ids),"every saved neighbor list");
 need(overlay.complete_edge_order_sha256==="411052a41a473bb7199fe277516fb60c54018dec120309622a499229579791bb","zero overlay edge order");
 const zeros=new Set(overlay.zero_rows.map(r=>r.edge_id));need(zeros.size===1884,"accepted zero count");
 const diagonal=plus.diagonal_x.map((v,a)=>2*v-540+30*dot(eta[a],eta[a]));
 need(diagonal.every(x=>Number.isSafeInteger(x)&&x>=1042&&x<=2086),"positive diagonal bound");
 const records=[],edgeZero=[],pairCover=[],forcedEdge=[],restrictedStates=[],hist={};
 const counts={pairs:0,eligible_edges:0,states:0,negative_minor:0,zero_minor:0,positive_minor:0};
 let minimum=null,maximum=null,edgeNegativeAll=0;
 for(let a=0;a<480;a++){
  tick();
  for(let b=a+1;b<480;b++){
   const p=pairId(a,b),s=pop(masks[a]&masks[b]),e=edgeIds[p],etaDot=dot(eta[a],eta[b]),values=[[],null],allowed=[0,0];
   if(e>=0){values[1]=[];counts.eligible_edges++;}
   for(let y=0;y<=1;y++){
    if(y===1&&e<0)continue;
    for(let n=0;n<=2-s-y;n++){
     const bab=off(plus.off_diagonal_Z[p],s,y,n,etaDot),det=determinant(diagonal[a],diagonal[b],bab);
     need(det>=-9007199254740991n&&det<=9007199254740991n,"exact numeric report determinant");
     values[y].push(Number(det));counts.states++;
     if(det<0n)counts.negative_minor++;else{allowed[y]|=1<<n;if(det===0n)counts.zero_minor++;else counts.positive_minor++;}
     if(minimum===null||det<minimum)minimum=det;if(maximum===null||det>maximum)maximum=det;
    }
   }
   // Complete per-pair state table: position n in each determinant list is the integer common-neighbor count.
   records.push([a,b,e,s,etaDot,off(plus.off_diagonal_Z[p],s,0,0,etaDot),values[0],values[1],allowed[0],allowed[1]]);
   const key=s+":"+(e>=0?1:0)+":"+allowed[0]+":"+allowed[1];hist[key]=(hist[key]||0)+1;counts.pairs++;
   if(e>=0&&allowed[1]===0){edgeZero.push([a,b,e,zeros.has(e)]);edgeNegativeAll++;}
   if(allowed[0]===0&&(e<0||allowed[1]===0))pairCover.push([a,b,e]);
   if(allowed[0]===0&&e>=0&&allowed[1]!==0)forcedEdge.push([a,b,e]);
   if(values[0].some(x=>x<0)||(values[1]&&values[1].some(x=>x<0)))restrictedStates.push(p);
  }
 }
 need(counts.pairs===114960&&records.length===114960&&counts.eligible_edges===68394,"complete pair scope");
 need(counts.negative_minor+counts.zero_minor+counts.positive_minor===counts.states,"state accounting");tick();
 return {schema:"conway99.f0.spectral-gap-pair-census.v1",status:"COMPLETE_FORWARD_PAIR_AND_INTEGER_COMMON_NEIGHBOR_CENSUS",
  source_math:"B=180L=2N-180R+30eta^Teta; N=60S; R_ab=2-s-n-y",scope:"All distinct original signatures; y=0 always, y=1 for original eligible edges; every integer n from0 through2-s-y.",
  counts,minimum_determinant:minimum.toString(),maximum_determinant:maximum.toString(),eta,diagonal,
  record_format:["a","b","edge_id_or_minus1","signature_overlap","fiber_profile_dot","B_ab_at_y0_n0","determinants_y0_by_n","determinants_y1_by_n_or_null","allowed_n_bitmask_y0","allowed_n_bitmask_y1"],
  complete_pair_state_records:records,state_mask_histogram:hist,edge_zero_rows:edgeZero,selector_pair_cover_rows:pairCover,forced_adjacency_rows:forcedEdge,
  pairs_with_any_rejected_integer_state:restrictedStates,edge_zeros_already_literal:edgeZero.filter(r=>r[3]).length,edge_zeros_not_in_literal_zero_family:edgeZero.filter(r=>!r[3]).length,
  pair_covers_not_compared_to_old_rows:true,forced_adjacencies_not_compared_to_old_rows:true,old_literal_zeros_used_only_for_disposition:true,
  seconds:(Date.now()-start)/1000,maximum_ms:maximumMs,optimizer_calls:0,native_model_builds:0,graph_constructed:false,whole_component_excluded:false};
}
return {controls,run};
})()