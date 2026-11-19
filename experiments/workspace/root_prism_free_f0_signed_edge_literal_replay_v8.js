(() => {
"use strict";
function need(x,m){if(!x)throw Error(m);}
function same(a,b,m){need(JSON.stringify(a)===JSON.stringify(b),m);}
function contract(diagonal,off,v){return diagonal[0]*v[0]*v[0]+diagonal[1]*v[1]*v[1]+diagonal[2]*v[2]*v[2]+2n*(off[0]*v[0]*v[1]+off[1]*v[0]*v[2]+off[2]*v[1]*v[2]);}
function controls(){
 need(contract([878n,878n,1088n],[-749n,272n,274n],[2n,2n,-1n])===-64n,"literal signed example");
 need(contract([878n,878n,1088n],[-748n,272n,274n],[2n,2n,-1n])===-56n,"coefficient sensitivity");
 need(contract([1n,1n,1n],[0n,0n,0n],[1n,0n,0n])===1n,"positive form");
 need(contract([1n,1n,1n],[0n,0n,0n],[0n,0n,0n])===0n,"zero vector is not negative");
 return {status:"PASS_INDEPENDENT_EXPANDED_QUADRATIC_CONTROLS",checks:4};
}
function verify(report,domain,kernels,overlay,shaText){
 const start=Date.now(),tick=()=>need(Date.now()-start<15000,"signed literal check15seconds");
 need(report.status==="PASS_252_PROVIDED_SINGLE_EDGE_PSD_CERTIFICATES"&&report.complete===true&&report.error===null&&report.certified_records===252&&report.certificates.length===252,"complete supplied certificates");
 const edges=[],lookup=new Map();
 for(let a=0;a<480;a++)for(const b of domain.possible_neighbor_signature_ids[a])if(a<b){lookup.set(a+","+b,edges.length);edges.push([a,b]);}
 need(edges.length===68394&&shaText(JSON.stringify(edges))==="411052a41a473bb7199fe277516fb60c54018dec120309622a499229579791bb","accepted literal edge namespace");
 const zeroSet=new Set(overlay.zero_rows.map(r=>r.edge_id));need(zeroSet.size===1884,"literal zeros");
 const families=new Map(kernels.kernels.map(k=>[k.family,k])),originalKeys=new Map(),values=new Array(252),seen=new Set(),counts={plus:0,minus:0};
 const expectedHashes={plus:"91017b1ad1ea6ff3433e91030586ec820f939a158f8cf3aab0cbf77e4ef574ed",minus:"3ec5835de875dc50cb9f349deb2bbd9bd16457657917b2e267a444d38e642b3d"};
 for(let index=251;index>=0;index--){
  tick();const certificate=report.certificates[index],s=certificate.selectors,mask=certificate.edge_pattern_mask;
  need(certificate.certificate_index===index&&s.length===3&&s.every((a,j)=>Number.isInteger(a)&&0<=a&&a<480&&(j===0||s[j-1]<a))&&[1,2,4].includes(mask),"literal target identity");
  const identity=s.join(",")+"/"+mask;need(!seen.has(identity),"distinct target");seen.add(identity);
  const sites=s.map(a=>domain.signature_domain[a]);same(sites,certificate.signature_sites,"literal signature sites");
  const pairs=[[0,1],[0,2],[1,2]],edgeIds=pairs.map(([i,j])=>{
   need(sites[i].every(x=>!sites[j].includes(x)),"disjoint target signatures");
   const edge=lookup.get(s[i]+","+s[j]);need(Number.isInteger(edge),"original eligible target edge");return edge;
  });
  same(edgeIds,certificate.edge_ids,"three original edges");
  const f=certificate.rejecting_family,k=families.get(f);need(k&&Object.hasOwn(expectedHashes,f)&&k.primitive_kernel_sha256===expectedHashes[f]&&certificate.primitive_kernel_sha256===expectedHashes[f],"accepted primitive kernel family");
  const divisor=BigInt(k.common_numerator_divisor);need(divisor>0n,"positive primitive scale");
  function primitive(value){need(Number.isSafeInteger(value),"exact saved kernel integer");const v=BigInt(value);need(v%divisor===0n,"exact primitive division");return v/divisor;}
  const diagonal=s.map(a=>primitive(k.diagonal_x[a]));
  const off=pairs.map(([i,j],bit)=>primitive(k.off_diagonal_Z[s[i]*(959-s[i])/2+s[j]-s[i]-1])+(((mask>>>bit)&1)?primitive(k.Y):0n));
  const matrix=[diagonal[0],off[0],off[1],off[0],diagonal[1],off[2],off[1],off[2],diagonal[2]];
  same(matrix.map(String),certificate.primitive_matrix,"every reconstructed matrix entry");
  need(certificate.negative_vector.length===3&&certificate.negative_vector.every(x=>typeof x==="string"&&/^-?(0|[1-9][0-9]*)$/.test(x)),"integer negative vector");
  const v=certificate.negative_vector.map(BigInt),q=contract(diagonal,off,v);
  need(q<0n&&q.toString()===certificate.exact_quadratic_value,"fresh expanded negative quadratic contraction");
  const bit=mask===1?0:mask===2?1:2,present=edgeIds[bit],isolated=s[[2,1,0][bit]];
  const terms=[[isolated,1],...edgeIds.map((edge,j)=>[540+edge,j===bit?1:-1])].sort((a,b)=>a[0]-b[0]),key=[-2,1,terms];
  same(key,certificate.row_key,"guarded original native key");
  same(edges[present],certificate.present_edge_endpoints,"present endpoints");
  need(certificate.present_edge_id===present&&certificate.isolated_selector===isolated&&certificate.present_edge_known_zero===zeroSet.has(present),"activation and zero disposition");
  const encoded=JSON.stringify(key);if(!originalKeys.has(encoded))originalKeys.set(encoded,[]);
  originalKeys.get(encoded).push(index);values[index]=q.toString();counts[f]++;
 }
 const savedSeen=new Set();need(report.row_keys.length===report.row_count&&report.row_keys.length===originalKeys.size&&report.row_origins.length===originalKeys.size,"complete unique signed rows");
 for(let r=0;r<report.row_keys.length;r++){
  const key=report.row_keys[r],encoded=JSON.stringify(key),origins=originalKeys.get(encoded);need(origins&&!savedSeen.has(encoded),"one saved row per actual key");savedSeen.add(encoded);
  origins.sort((a,b)=>a-b);same(origins,report.row_origins[r],"all original row certificates");
  for(const i of origins)need(report.certificates[i].row_key_index===r,"row origin backreference");
 }
 const rowHash=shaText(JSON.stringify(report.row_keys));need(rowHash===report.row_keys_sha256,"complete saved key digest");tick();
 return {schema:"conway99.f0.signed-edge-literal-root-replay.v1",status:"PASS_ALL_252_LITERAL_NEGATIVE_QUADRATIC_CERTIFICATES_AND_NATIVE_KEYS",certificates:252,rows:report.row_keys.length,all_original_edge_ids_checked:true,all_primitive_matrix_entries_reconstructed:true,all_negative_values_recomputed_by_expanded_form:true,all_selector_guards_and_row_origins_checked:true,row_keys_sha256:rowHash,exact_negative_value_array_sha256:shaText(JSON.stringify(values)),families:counts,seconds:(Date.now()-start)/1000,maximum_ms:15000,producer_imported:false,diagnostic_pattern_completeness_claimed:false,optimizer_calls:0,native_model_builds:0};
}
return {controls,verify};
})()