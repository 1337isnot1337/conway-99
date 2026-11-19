(() => {
"use strict";
const SCHEMA="conway99.f0.provided-single-edge-schur-certificates.v1";
const PAIRS=[[0,1],[0,2],[1,2]];
function check(ok,message){if(!ok)throw Error(message);}
function same(a,b,message){check(JSON.stringify(a)===JSON.stringify(b),message);}
function integer(v,message){check(Number.isSafeInteger(v),message);return v;}
function popcount(v){let n=0;while(v){v&=v-1;n++;}return n;}
function gcd(a,b){a=a<0n?-a:a;b=b<0n?-b:b;while(b){const r=a%b;a=b;b=r;}return a;}
function quadratic(matrix,vector){
 check(matrix.length===9&&vector.length===3,"quadratic dimensions");
 let q=0n;for(let i=0;i<3;i++)for(let j=0;j<3;j++)q+=vector[i]*matrix[3*i+j]*vector[j];return q;
}
function normalize(vector){
 let g=0n;for(const v of vector)g=gcd(g,v);check(g>0n,"nonzero witness");
 let v=vector.map(x=>x/g);if(v.find(x=>x!==0n)<0n)v=v.map(x=>-x);return v;
}
const SHORT=[];
for(let a=-2;a<=2;a++)for(let b=-2;b<=2;b++)for(let c=-2;c<=2;c++){
 const v=[BigInt(a),BigInt(b),BigInt(c)];if(v.every(x=>x===0n)||v.find(x=>x!==0n)<0n)continue;
 let g=0n;for(const x of v)g=gcd(g,x);if(g===1n)SHORT.push(v);
}
SHORT.sort((u,v)=>{
 const norm=x=>x.reduce((s,a)=>s+Number(a<0n?-a:a),0),z=norm(u)-norm(v);
 if(z)return z;for(let j=0;j<3;j++)if(u[j]!==v[j])return u[j]<v[j]?-1:1;return 0;
});
check(SHORT.length===49,"complete declared short-vector list");
function findWitness(matrix,counters){
 for(let i=0;i<SHORT.length;i++){
  if(counters)counters.short_vector_tests++;
  const v=SHORT[i],q=quadratic(matrix,v);
  if(q<0n)return {method:"bounded_primitive_short_vector",short_index:i,vector:v.slice(),quadratic:q};
 }
 for(const order of [[0,1,2],[0,2,1],[1,2,0]]){
  if(counters)counters.cofactor_tests++;
  const [i,j,k]=order,A=matrix[3*i+i],B=matrix[3*j+j],D=matrix[3*i+j],E=matrix[3*i+k],F=matrix[3*j+k],p=A*B-D*D;
  if(p<=0n)continue;
  const raw=[0n,0n,0n];raw[i]=D*F-B*E;raw[j]=D*E-A*F;raw[k]=p;
  const v=normalize(raw),q=quadratic(matrix,v);
  if(q<0n)return {method:"positive_pivot_cofactor",pivot_order:order.slice(),pivot_minor:p.toString(),vector:v,quadratic:q};
 }
 return null;
}
function verifyNegative(matrix,vector,value){
 check(vector.length===3&&vector.some(v=>v!==0n),"nonzero negative vector");
 const q=quadratic(matrix,vector);check(q===value&&q<0n,"exact negative quadratic certificate");return q;
}
function rowFor(selectors,edgeIds,mask){
 check([1,2,4].includes(mask),"one-edge pattern");
 const bit=mask===1?0:mask===2?1:2,isolated=[2,1,0][bit];
 check(selectors.length===3&&new Set(selectors).size===3&&selectors.every(i=>Number.isInteger(i)&&i>=0&&i<480),"row selector IDs");
 check(edgeIds.length===3&&new Set(edgeIds).size===3&&edgeIds.every(i=>Number.isInteger(i)&&i>=0&&i<68394),"row edge IDs");
 const terms=[[selectors[isolated],1]];
 for(let e=0;e<3;e++)terms.push([540+edgeIds[e],e===bit?1:-1]);
 terms.sort((u,v)=>u[0]-v[0]);
 check(new Set(terms.map(t=>t[0])).size===4,"row distinct variables");
 return {key:[-2,1,terms],present_bit:bit,isolated_selector:selectors[isolated],present_edge_id:edgeIds[bit]};
}
function determinantControl(m){
 let result=0n;
 for(let a=0;a<3;a++)for(let b=0;b<3;b++)if(b!==a)for(let c=0;c<3;c++)if(c!==a&&c!==b){
  const p=[a,b,c];let inversions=0;for(let i=0;i<3;i++)for(let j=i+1;j<3;j++)if(p[i]>p[j])inversions++;
  result+=(inversions%2?-1n:1n)*m[a]*m[3+b]*m[6+c];
 }return result;
}
function controls(){
 const start=Date.now();let matrices=0,cofactorIdentities=0,requiredNegative=0,foundNegative=0,assignmentTests=0,rejections=0;
 for(let A=1;A<=3;A++)for(let B=1;B<=3;B++)for(let C=1;C<=3;C++)
 for(let D=-2;D<=2;D++)for(let E=-2;E<=2;E++)for(let F=-2;F<=2;F++){
  const m=[A,D,E,D,B,F,E,F,C].map(BigInt),det=determinantControl(m);
  let positivePivot=false;
  for(const [i,j,k] of [[0,1,2],[0,2,1],[1,2,0]]){
   const a=m[3*i+i],b=m[3*j+j],d=m[3*i+j],e=m[3*i+k],f=m[3*j+k],p=a*b-d*d;
   if(p<=0n)continue;positivePivot=true;
   const v=[0n,0n,0n];v[i]=d*f-b*e;v[j]=d*e-a*f;v[k]=p;
   check(quadratic(m,v)===p*det,"cofactor identity");cofactorIdentities++;
  }
  const witness=findWitness(m);
  if(witness){verifyNegative(m,witness.vector,witness.quadratic);foundNegative++;}
  if(det<0n&&positivePivot){requiredNegative++;check(witness!==null,"negative determinant with positive pivot found");}
  if(det>=0n&&[A*B-D*D,A*C-E*E,B*C-F*F].every(v=>v>=0))check(witness===null,"PSD control has no false negative vector");
  matrices++;
 }
 const scale=1n<<100n,m=[3n,-2n,-2n,-2n,3n,-2n,-2n,-2n,3n].map(v=>v*scale),w=findWitness(m);
 check(w!==null,"large exact witness");verifyNegative(m,w.vector,w.quadratic);
 const qExpanded=m[0]*w.vector[0]**2n+m[4]*w.vector[1]**2n+m[8]*w.vector[2]**2n+
  2n*m[1]*w.vector[0]*w.vector[1]+2n*m[2]*w.vector[0]*w.vector[2]+2n*m[5]*w.vector[1]*w.vector[2];
 check(qExpanded===w.quadratic,"independent expanded quadratic");
 for(const mask of [1,2,4]){
  const selectors=[2,7,11],ids=[19,3,87],row=rowFor(selectors,ids,mask);
  same(row.key[2].map(t=>t[0]),[row.isolated_selector,543,559,627],"nonidentity native transport");
  for(let values=0;values<64;values++){
   const x=[values&1,(values>>>1)&1,(values>>>2)&1],y=[(values>>>3)&1,(values>>>4)&1,(values>>>5)&1];
   if(PAIRS.some(([a,b],e)=>y[e]>(x[a]<x[b]?x[a]:x[b])))continue;
   const byId=new Map();selectors.forEach((s,i)=>byId.set(s,x[i]));ids.forEach((e,i)=>byId.set(540+e,y[i]));
   const lhs=row.key[2].reduce((sum,[i,c])=>sum+c*byId.get(i),0);
   const forbidden=x.every(v=>v===1)&&y.every((v,i)=>v===((mask>>>i)&1));
   check(lhs>=-2&&((lhs<=1)===!forbidden),"guarded clause truth table");
   assignmentTests++;
  }
 }
 for(const bad of [()=>verifyNegative(m,w.vector,w.quadratic+1n),()=>verifyNegative(m,[0n,0n,0n],0n),()=>rowFor([2,7,11],[19,3,87],3),()=>rowFor([2,7,11],[19,19,87],1)]){
  try{bad();}catch(e){rejections++;}
 }check(rejections===4,"tampered certificate and row controls");
 return {status:"PASS_TARGETED_CERTIFICATE_CONTROLS",synthetic_symmetric_matrices:matrices,cofactor_identities:cofactorIdentities,
  negative_determinant_positive_pivot_cases:requiredNegative,negative_witnesses_found:foundNegative,
  short_directions:SHORT.length,large_scaled_matrix_bits:102,guarded_valid_endpoint_assignments:assignmentTests,
  deliberately_invalid_inputs_rejected:rejections,targeted_case_patterns_evaluated:0,seconds:(Date.now()-start)/1000};
}
function load(configurationText,payload,codec,sourceText,codecText,tick){
 const cfg=JSON.parse(configurationText),hash=s=>codec.sha256(codec.utf8(s));
 check(cfg.schema==="conway99.f0.provided-single-edge-schur.configuration.v1","configuration schema");
 check(cfg.maximum_ms===60000&&cfg.maximum_report_bytes===16777216&&cfg.expected_target_count===252,"fixed scope and bounds");
 check(cfg.selector_count===480&&cfg.edge_offset===540&&cfg.edge_count===68394,"fixed native namespace");
 check(hash(sourceText)===cfg.source.sha256&&codec.gitBlob(codec.utf8(sourceText))===cfg.source.git_blob,"source binding");
 check(hash(codecText)===cfg.codec.sha256&&codec.gitBlob(codec.utf8(codecText))===cfg.codec.git_blob,"codec binding");
 const data={};
 for(const name of ["domain","kernels","overlay","audit","projection","parent_census","accepted_cold_summary"]){
  tick();const b=cfg.inputs[name];check(b&&typeof payload[name]==="string","input "+name);let raw;
  if(b.encoding==="gzip-base64"){
   const archive=codec.base64(payload[name]);
   check(archive.length===b.archive_bytes&&codec.sha256(archive)===b.archive_sha256&&codec.gitBlob(archive)===b.git_blob,"archive "+name);
   raw=codec.gunzip(archive,cfg.maximum_report_bytes);
  }else{
   check(b.encoding==="utf-8","raw encoding");raw=codec.utf8(payload[name]);check(codec.gitBlob(raw)===b.git_blob,"raw Git "+name);
  }
  check(raw.length===b.raw_bytes&&codec.sha256(raw)===b.raw_sha256,"raw binding "+name);
  data[name]=JSON.parse(codec.ascii(raw));
 }
 const p=data.projection;
 check(p.schema==="conway99.f0.psd-positive-cube-stored-projection.v1"&&p.status==="EXACT_STORED_OUTPUT_PROJECTION_NO_ARITHMETIC_REPLAY","diagnostic projection status");
 same(p.edge_bits,["ab","ac","bc"],"edge pattern bit convention");
 check(p.extra_pattern_count===252&&p.extra_rejected_patterns_without111.length===252,"provided target count");
 check(data.accepted_cold_summary.status==="PASS_COMPLETE_INDEPENDENT_CENSUS_AND_LITERAL_ZERO_DISPOSITION","accepted triangle cold premise");
 check(data.parent_census.status==="COMPLETE_EXACT_TRIANGLE_PRINCIPAL_MINOR_CENSUS","bound parent census");
 check(data.accepted_cold_summary.report.sha256===cfg.accepted_cold_report_sha256,"accepted cold report binding");
 check(data.domain.signature_domain.length===480&&data.domain.complete_possible_edge_count===68394,"literal domain scope");
 check(data.kernels.kernels.length===2&&data.audit.families.length===2,"two kernel families");
 tick();return {cfg,data,source_sha256:cfg.source.sha256,configuration_sha256:hash(configurationText)};
}
function prepare(configurationText,payload,codec,sourceText,codecText){
 const start=Date.now(),tick=()=>check(Date.now()-start<30000,"30-second preparation budget");
 const state=load(configurationText,payload,codec,sourceText,codecText,tick),seen=new Set(),masks={1:0,2:0,4:0};
 for(const r of state.data.projection.extra_rejected_patterns_without111){
  check(r.selectors.length===3&&r.selectors.every((a,i)=>Number.isInteger(a)&&a>=0&&a<480&&(i===0||a>r.selectors[i-1])),"provided selector tuple");
  check([1,2,4].includes(r.edge_pattern_mask),"provided one-edge mask");
  const key=r.selectors.join(",")+"/"+r.edge_pattern_mask;check(!seen.has(key),"provided target uniqueness");seen.add(key);masks[r.edge_pattern_mask]++;
  same(r.signature_sites,r.selectors.map(a=>state.data.domain.signature_domain[a]),"provided signature-site binding");
 }
 const control=controls();tick();
 return {schema:SCHEMA,status:"PREPARED_TARGETED_CERTIFICATE_CHECKER_ONLY",source_sha256:state.source_sha256,
  configuration_sha256:state.configuration_sha256,inputs:state.cfg.inputs,provided_targets:252,provided_mask_histogram:masks,controls:control,
  case_matrices_evaluated:0,case_negative_vectors_proved:0,full_pattern_census_executed:false,main_requires_root_gate:true,seconds:(Date.now()-start)/1000};
}
function reconstructEdges(domain,tick){
 const n=480,core=domain.component_core_rows,adj=domain.component_adjacency_rows,signatures=domain.signature_domain;
 check(core.length===21&&adj.length===18,"fixed core dimensions");
 for(let i=0;i<18;i++)check(adj[i]===(core[i+3]>>>3),"induced core adjacency");
 const masks=signatures.map(s=>{
  check(s.length===3&&s.every((v,i)=>Number.isInteger(v)&&v>=0&&v<18&&(i===0||v>s[i-1])),"signature sites");
  return s.reduce((m,i)=>m|(1<<i),0);
 });
 check(new Set(masks).size===480,"distinct signatures");
 const q=masks.map((m,a)=>Array.from({length:18},(_,i)=>{
  const value=2-((m>>>i)&1)-popcount(m&adj[i]);check(value===domain.row_targets[a][i]&&value>=0&&value<=2,"mixed quota reconstruction");return value;
 }));
 const pairIndex=new Int32Array(n*n).fill(-1),edgeIndex=new Int32Array(n*n).fill(-1),edges=[],neighbors=Array.from({length:n},()=>[]);
 let pair=0;
 for(let a=0;a<n;a++){
  tick();
  for(let b=a+1;b<n;b++){
   pairIndex[a*n+b]=pairIndex[b*n+a]=pair++;
   if(popcount(masks[a]&masks[b])<=1&&signatures[b].every(i=>q[a][i]>0)&&signatures[a].every(i=>q[b][i]>0)){
    const id=edges.length;edges.push([a,b]);edgeIndex[a*n+b]=edgeIndex[b*n+a]=id;neighbors[a].push(b);neighbors[b].push(a);
   }
  }
 }
 check(pair===114960&&edges.length===68394,"complete original pair namespace");
 for(let i=0;i<n;i++)same(neighbors[i],domain.possible_neighbor_signature_ids[i],"original neighbor row "+i);
 return {masks,pairIndex,edgeIndex,edges};
}
function primitive(k,a,indices,codec,tick){
 const div=integer(k.common_numerator_divisor,"primitive divisor");check(div>0,"positive primitive scale");
 const divide=v=>{integer(v,"kernel integer");check(v%div===0,"exact primitive division");return v/div;};
 check(k.diagonal_x.length===480&&k.off_diagonal_Z.length===114960,"kernel array dimensions");
 const diagonal=k.diagonal_x.map(divide),off=k.off_diagonal_Z.map(divide),y=divide(k.Y),all=[];
 for(let i=0;i<480;i++){if((i&31)===0)tick();for(let j=i;j<480;j++)all.push(i===j?diagonal[i]:off[indices.pairIndex[i*480+j]]);}
 all.push(y);const hash=codec.sha256(codec.utf8(JSON.stringify(all)));
 check(hash===k.primitive_kernel_sha256&&hash===a.primitive_kernel_sha256,"accepted primitive kernel");
 check(diagonal.every(v=>v>0),"positive primitive diagonals");
 return {family:k.family,hash,diagonal:diagonal.map(BigInt),off:off.map(BigInt),y:BigInt(y)};
}
function knownZeros(overlay,indices,codec){
 check(overlay.status==="COMPLETE_LITERAL_PRISM_ZEROS_AND_CORE_PAIR_CLIQUES"&&overlay.zero_rows.length===1884,"known zero scope");
 check(codec.sha256(codec.utf8(JSON.stringify(indices.edges)))===overlay.complete_edge_order_sha256,"original native edge order");
 const map=new Map();
 for(let i=0;i<overlay.zero_rows.length;i++){
  const r=overlay.zero_rows[i],e=r.edge_id;
  check(Number.isInteger(e)&&e>=0&&e<68394&&!map.has(e),"known zero edge");
  check(r.variable_index===540+e&&r.native_row_index===163070+i&&r.witness.kind==="P"&&r.witness.edge_id===e,"known zero row location");
  same(r.witness.pair,indices.edges[e],"known zero endpoints");
  map.set(e,{edge_id:e,native_variable_index:r.variable_index,native_row_index:r.native_row_index,witness_index:r.witness_index});
 }
 return map;
}
function matrixFor(f,selectors,pairIds,mask){
 const d=selectors.map(a=>f.diagonal[a]),e=pairIds.map((p,j)=>f.off[p]+(((mask>>>j)&1)?f.y:0n));
 return [d[0],e[0],e[1],e[0],d[1],e[2],e[1],e[2],d[2]];
}
function compareKeys(a,b){
 for(let j=0;j<2;j++)if(a[j]!==b[j])return a[j]-b[j];
 for(let j=0;j<Math.min(a[2].length,b[2].length);j++)for(let k=0;k<2;k++)if(a[2][j][k]!==b[2][j][k])return a[2][j][k]-b[2][j][k];
 return a[2].length-b[2].length;
}
function run(configurationText,payload,codec,sourceText,codecText){
 const started=Date.now(),tick=()=>check(Date.now()-started<60000,"60-second targeted proof budget");
 const certificates=[],counters={matrices_examined:0,short_vector_tests:0,cofactor_tests:0};
 let state=null,edges=null,error=null,complete=false;
 try{
  state=load(configurationText,payload,codec,sourceText,codecText,tick);
  edges=reconstructEdges(state.data.domain,tick);
  const families=["plus","minus"].map(name=>primitive(state.data.kernels.kernels.find(f=>f.family===name),
   state.data.audit.families.find(f=>f.family===name),edges,codec,tick));
  const zeros=knownZeros(state.data.overlay,edges,codec);
  const parent=state.data.parent_census.families.find(f=>f.family==="plus").nonpositive_determinant_records_with_nonnegative_proper_minors;
  const accepted=state.data.accepted_cold_summary.families.find(f=>f.family==="plus");
  check(codec.sha256(codec.utf8(JSON.stringify(parent)))===accepted.nonpositive_records_sha256,"accepted original triangle list");
  const targets=state.data.projection.extra_rejected_patterns_without111,seen=new Set();
  for(let index=0;index<targets.length;index++){
   tick();const target=targets[index],selectors=target.selectors,mask=target.edge_pattern_mask;
   check(selectors.length===3&&selectors.every((a,j)=>Number.isInteger(a)&&a>=0&&a<480&&(j===0||a>selectors[j-1])),"target selector tuple");
   check([1,2,4].includes(mask),"one-edge target mask");
   const targetKey=selectors.join(",")+"/"+mask;check(!seen.has(targetKey),"unique target");seen.add(targetKey);
   check(Number.isInteger(target.parent_record_index)&&target.parent_record_index>=0&&target.parent_record_index<parent.length,"parent record index");
   same(parent[target.parent_record_index].slice(0,3),selectors,"original accepted triangle identity");
   same(target.signature_sites,selectors.map(a=>state.data.domain.signature_domain[a]),"original selected signatures");
   const edgeIds=[],pairIds=[];
   for(const [i,j] of PAIRS){
    const a=selectors[i],b=selectors[j];check((edges.masks[a]&edges.masks[b])===0,"provided disjoint signatures");
    const e=edges.edgeIndex[a*480+b],p=edges.pairIndex[a*480+b];check(e>=0&&p>=0,"original eligible edge");
    edgeIds.push(e);pairIds.push(p);
   }
   same(edgeIds,target.edge_ids,"original edge IDs");
   let proof=null;
   for(const f of families){
    counters.matrices_examined++;const matrix=matrixFor(f,selectors,pairIds,mask),witness=findWitness(matrix,counters);
    if(witness){
     const q=verifyNegative(matrix,witness.vector,witness.quadratic),row=rowFor(selectors,edgeIds,mask);
     proof={certificate_index:index,projection_record_index:index,parent_record_index:target.parent_record_index,
      selectors:selectors.slice(),signature_sites:selectors.map(a=>state.data.domain.signature_domain[a]),edge_ids:edgeIds,edge_pattern_mask:mask,
      edge_bit_order:["ab","ac","bc"],present_edge_id:row.present_edge_id,present_edge_endpoints:edges.edges[row.present_edge_id],
      isolated_selector:row.isolated_selector,rejecting_family:f.family,primitive_kernel_sha256:f.hash,
      primitive_matrix:matrix.map(String),negative_vector:witness.vector.map(String),exact_quadratic_value:q.toString(),
      witness_method:witness.method,witness_details:witness.method==="bounded_primitive_short_vector"?{short_index:witness.short_index}:{pivot_order:witness.pivot_order,pivot_minor:witness.pivot_minor},
      row_key:row.key,present_edge_known_zero:zeros.has(row.present_edge_id),
      present_edge_zero_premise:zeros.get(row.present_edge_id)||null,
      all_triangle_edge_zero_premises:edgeIds.filter(e=>zeros.has(e)).map(e=>zeros.get(e)),
      activation_argument:"Y_present activates its two endpoints; the remaining selector is retained as the guard.",
      saved_minor_strings_used_for_acceptance:false};
     break;
    }
   }
   check(proof!==null,"no exact negative vector proved for provided record "+index);
   certificates.push(proof);
  }
  tick();check(certificates.length===252,"all provided records individually certified");complete=true;
 }catch(e){error=String(e&&e.message?e.message:e);}
 const unique=new Map();for(const c of certificates){const key=JSON.stringify(c.row_key);if(!unique.has(key))unique.set(key,{key:c.row_key,origins:[]});unique.get(key).origins.push(c.certificate_index);}
 const rows=Array.from(unique.values()).sort((a,b)=>compareKeys(a.key,b.key));
 const rowIndex=new Map(rows.map((r,i)=>[JSON.stringify(r.key),i]));for(const c of certificates)c.row_key_index=rowIndex.get(JSON.stringify(c.row_key));
 const rowKeys=rows.map(r=>r.key);
 const result={schema:SCHEMA,status:complete?"PASS_252_PROVIDED_SINGLE_EDGE_PSD_CERTIFICATES":"UNACCEPTED_PARTIAL_TARGETED_CERTIFICATES",complete,
  source_sha256:state?state.source_sha256:null,configuration_sha256:codec.sha256(codec.utf8(configurationText)),inputs:state?state.cfg.inputs:null,
  provided_target_count:252,certified_records:certificates.length,unprocessed_target_count:252-certificates.length,counters,
  row_key_format:"[lower,upper,sorted[[native_variable_index,coefficient],...]]",row_keys:rowKeys,row_origins:rows.map(r=>r.origins),
  row_keys_sha256:codec.sha256(codec.utf8(JSON.stringify(rowKeys))),row_count:rowKeys.length,certificates,
  present_edge_already_known_zero:certificates.filter(r=>r.present_edge_known_zero).length,
  seconds:(Date.now()-started)/1000,maximum_ms:60000,error,
  scope:"Only the252 supplied one-edge diagnostic records; each accepted row has a directly checked negative quadratic form.",
  eight_pattern_census_executed:false,diagnostic_list_completeness_claimed:false,other_pattern_acceptance_claimed:false,
  kernel_inverse_recomputed:false,other_constraint_redundancy_tested:false,optimizer_calls:0,native_models_built:0,refs_mutated:false};
 check(codec.utf8(JSON.stringify(result)).length<=16777216,"targeted report cap");return result;
}
return {controls,prepare,run};
})()
