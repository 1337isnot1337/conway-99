(() => {
"use strict";
const ck=(v,m)=>{if(!v)throw Error(m);};
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const pair=(a,b)=>a<b?[a,b]:[b,a];
const pop=v=>{let n=0;for(;v;v&=v-1)n++;return n;};
function certify(D,I,L){
 ck(D.signature_domain.length===480&&D.component_core_rows.length===21,"domain dimensions");
 ck(I.status==="PASS_EXACT_SHARED_TRIANGLE_INDICATOR_INVENTORY"&&I.targets.length===84,"indicator authority");
 ck(L.variables===80730&&L.rows===297470&&L.triangle_variable_start===71382,"native namespace");
 const H=D.signature_domain,B=D.component_core_rows,A=D.component_adjacency_rows;
 for(let i=0;i<18;i++)ck((B[i+3]&7)===(1<<Math.floor(i/6)),"fixed first fiber labels");
 const gram=(i,j)=>12*Number(i===j)+2-pop(B[i+3]&B[j+3])-((B[i+3]>>>(j+3))&1);
 const nativeMap=new Map();let old=0,native=4440;
 for(let i=0;i<18;i++)for(let j=i;j<18;j++){
  const support=H.flatMap((h,a)=>h.includes(i)&&h.includes(j)?[a]:[]);
  nativeMap.set([i,j].join(","),{original:old,native:support.length?native:null,quota:gram(i,j),support});
  if(support.length)native++;else ck(gram(i,j)===0,"empty Gram");old++;
 }
 ck(old===171&&native===4590,"Gram map");
 const edges=I.targets.map(t=>[t.edge_id,...t.endpoints]).sort((a,b)=>a[0]-b[0]);
 ck(new Set(edges.map(e=>e[0])).size===84&&new Set(edges.map(e=>e.slice(1).join(","))).size===84,"edge uniqueness");
 const adj=new Map(),colors=new Map();
 for(const [e,a,b]of edges){ck(0<=a&&a<b&&b<480&&Number.isSafeInteger(e)&&0<=e&&e<68394,"edge record");
  for(const [u,v]of[[a,b],[b,a]]){if(!adj.has(u))adj.set(u,[]);adj.get(u).push(v);}
 }
 const vertices=[...adj.keys()].sort((a,b)=>a-b);ck(vertices.length===84,"vertex count");
 for(const a of vertices){
  adj.get(a).sort((u,v)=>u-v);const h=H[a],coreEdges=[];
  for(let i=0;i<3;i++)for(let j=i+1;j<3;j++)if((A[h[i]]>>>h[j])&1)coreEdges.push([h[i],h[j]]);
  ck(coreEdges.length===1&&gram(...coreEdges[0])===1,"one quota-one core edge per target signature");
  colors.set(a,coreEdges[0]);
 }
 const colorKeys=[...new Set([...colors.values()].map(p=>p.join(",")))].map(s=>s.split(",").map(Number))
  .sort((p,q)=>p[0]-q[0]||p[1]-q[1]);
 ck(colorKeys.length===18,"eighteen colors");
 const colorIndex=new Map(colorKeys.map((p,i)=>[p.join(","),i]));
 const color=a=>colorIndex.get(colors.get(a).join(","));
 const groups=colorKeys.map((p,i)=>({color_index:i,core_edge:p,
  private:p[0]<6&&p[1]>=6,vertices:vertices.filter(a=>color(a)===i),gram:nativeMap.get(p.join(","))}));
 ck(groups.filter(g=>g.private).length===12&&groups.filter(g=>!g.private).length===6,"color partition");
 ck(groups.every(g=>g.gram.quota===1&&g.gram.native!==null&&g.vertices.length===(g.private?6:2)),"color quotas and sizes");
 const privateSet=new Set(vertices.filter(a=>groups[color(a)].private)),sharedSet=new Set(vertices.filter(a=>!privateSet.has(a)));
 const privateNeighbors=a=>adj.get(a).filter(b=>privateSet.has(b));
 const sharedNeighbors=a=>adj.get(a).filter(b=>sharedSet.has(b));
 const centers=new Set([...privateSet].filter(a=>privateNeighbors(a).length===3));
 const exposed=new Set([...privateSet].filter(a=>sharedNeighbors(a).length>0));
 ck(privateSet.size===72&&sharedSet.size===12&&centers.size===12&&exposed.size===24,"structural sizes");
 ck(edges.every(([,a,b])=>privateSet.has(a)||privateSet.has(b)),"no shared-shared edge");
 for(const a of privateSet){
  ck(sharedNeighbors(a).length<=1,"one available shared edge per private vertex");
  if(centers.has(a)){
   ck(sharedNeighbors(a).length===0,"centers unexposed");
   ck(privateNeighbors(a).every(b=>!centers.has(b)),"centers independent");
   ck(privateNeighbors(a).filter(b=>exposed.has(b)).length<=1,"one exposed leaf per center");
  }else ck(new Set(privateNeighbors(a).map(color)).size<=1,"noncenter neighbors have one color");
 }
 ck(edges.every(([,a,b])=>!(privateSet.has(a)&&privateSet.has(b)&&exposed.has(a)&&exposed.has(b))),"no private edge joins two exposed vertices");
 for(const a of sharedSet)ck(adj.get(a).length===2&&new Set(adj.get(a).map(color)).size===1,"shared-neighbor color check");
 const reached=new Set(),components=[];
 for(const v of vertices)if(!reached.has(v)){
  const stack=[v],vs=[];reached.add(v);while(stack.length){const a=stack.pop();vs.push(a);for(const b of adj.get(a))if(!reached.has(b)){reached.add(b);stack.push(b);}}
  vs.sort((a,b)=>a-b);const set=new Set(vs),es=edges.filter(([,a])=>set.has(a));
  const pc=[...new Set(vs.filter(a=>privateSet.has(a)).map(color))].sort((a,b)=>a-b);
  ck(vs.length===42&&es.length===42&&pc.length===6,"component count");
  components.push({vertices:vs,edge_ids:es.map(e=>e[0]),private_color_indices:pc,
   shared_vertices:vs.filter(a=>sharedSet.has(a))});
 }
 ck(components.length===2,"two components");
 const selected=[35,42,72,73,76,77,202,203,206,207,323,327,336,360,455,479];
 ck(selected.length===new Set(selected).size&&selected.every(a=>adj.has(a)),"witness vertices");
 const selectedSet=new Set(selected),witnessEdges=edges.filter(([,a,b])=>selectedSet.has(a)&&selectedSet.has(b));
 ck(groups.every(g=>g.vertices.filter(a=>selectedSet.has(a)).length<=1),"witness color feasibility");
 ck([...privateSet].filter(a=>selectedSet.has(a)).length===12&&witnessEdges.length===12,"attaining witness");
 ck(groups.filter(g=>g.private).every(g=>g.vertices.some(a=>selectedSet.has(a))),"all private quotas attained");
 const fractionalDenominator=6,fractionalX=a=>privateSet.has(a)?1:3;
 ck(groups.every(g=>g.vertices.reduce((s,a)=>s+fractionalX(a),0)===fractionalDenominator),"fractional color quotas");
 ck(edges.every(([,a,b])=>1<=fractionalX(a)&&1<=fractionalX(b)),"fractional activations");
 ck(edges.length===14*fractionalDenominator,"fractional total fourteen");
 const rowKey=[0,12,edges.map(([e])=>[540+e,1])];
 const nodeRecords=vertices.map(a=>({selector:a,signature:H[a],color_index:color(a),
  private:privateSet.has(a),center:centers.has(a),exposed:exposed.has(a),
  private_neighbors:privateNeighbors(a),shared_neighbors:sharedNeighbors(a),
  private_neighbor_color_indices:[...new Set(privateNeighbors(a).map(color))].sort((u,v)=>u-v)}));
 return{edges,colors:groups,private_vertices:[...privateSet].sort((a,b)=>a-b),
  shared_vertices:[...sharedSet].sort((a,b)=>a-b),centers:[...centers].sort((a,b)=>a-b),
  exposed_private_vertices:[...exposed].sort((a,b)=>a-b),nodes:nodeRecords,components,
  exhaustive_local_conditions_checked:{
   no_shared_shared_edges:true,centers_independent:true,centers_unexposed:true,
   every_noncenter_private_neighborhood_has_at_most_one_color:true,
   every_private_vertex_has_at_most_one_shared_neighbor:true,
   every_center_has_at_most_one_exposed_private_neighbor:true,
   no_private_edge_joins_two_exposed_vertices:true,
   hence_selected_private_components_are_stars_edges_or_singletons:true,
   hence_each_selected_private_component_has_at_most_one_shared_attachment_edge:true},
  bound:12,private_Gram_rows:groups.filter(g=>g.private).map(g=>({core_edge:g.core_edge,
   original_row_id:g.gram.original,native_row_id:g.gram.native,quota:g.gram.quota,
   complete_support:g.gram.support,target_support:g.vertices})),
  color_relaxation_attaining_witness:{selected,edge_ids:witnessEdges.map(e=>e[0]),edge_count:12,
   full_model_feasible_claimed:false,full_graph_constructed:false},
  color_relaxation_fractional_control:{denominator:6,private_selector_numerator:1,shared_selector_numerator:3,
   all_target_edge_numerators:1,edge_sum:14,all_eighteen_color_quotas_and_activations_checked:true,
   other_Gram_rows_population_degree_mixed_and_parent_cuts_not_checked:true,full_model_feasible_claimed:false},
  proposed_native_row_key:rowKey,Boolean_bound_proved:true,continuous_implication_claimed:false,
  full_model_nonredundancy_claimed:false,native_model_changed:false,optimizer_calls:0,assignment_enumerations:0};
}
function run(payload,configurationText,sourceText,C){
 const started=Date.now(),cfg=JSON.parse(configurationText),tick=stage=>ck(Date.now()-started<=30000,"deadline after "+stage);
 ck(cfg.schema==="conway99.f0.target-color-twelve-configuration.v1"&&cfg.limits.total_milliseconds===30000
  &&cfg.limits.maximum_report_bytes===1048576,"configuration");
 ck(C.sha256(C.utf8(sourceText))===cfg.source.sha256,"source identity");
 const data={};for(const [key,r]of Object.entries(cfg.inputs)){
  const bytes=r.encoding==="base64-gzip"?C.base64(payload[key]):C.utf8(payload[key]);
  ck(bytes.length===r.bytes&&C.sha256(bytes)===r.sha256&&C.gitBlob(bytes)===r.git_blob,"input "+key);
  const raw=r.encoding==="base64-gzip"?C.gunzip(bytes):bytes;
  if(r.raw_sha256)ck(C.sha256(raw)===r.raw_sha256,"raw "+key);
  data[key]=JSON.parse(C.ascii(raw));tick("input "+key);
 }
 ck(data.triangle_literal_root.status==="ROOT_ACCEPTS_COMPLETE_SEPARATE_LITERAL_SUPPORT_REPLAY_AND_INDICATOR_BINDINGS","triangle authority");
 ck(data.total_bound_review.status==="PASS_INDEPENDENT_CONTINUOUS_18_BOUND_CERTIFICATE","prior exact graph authority");
 ck(data.combined_configuration.inputs.triangle_inventory.sha256===cfg.inputs.indicator.sha256
  &&data.combined_configuration.inputs.domain.sha256===cfg.inputs.domain.sha256,"combined input links");
 const result=certify(data.domain,data.indicator,data.combined_configuration.layout);tick("complete structural certificate");
 const report={schema:"conway99.f0.target-color-twelve-certificate.v1",
  status:"PASS_EXACT_STRUCTURAL_TWELVE_TARGET_BOUND_AND_COLOR_WITNESS",
  source:cfg.source,configuration_sha256:C.sha256(C.utf8(configurationText)),inputs:cfg.inputs,
  ...result,proposed_row_key_sha256:C.sha256(C.utf8(JSON.stringify(result.proposed_native_row_key))),
  all_local_conditions_checked:true,private_selected_component_argument_is_Boolean:true,
  original_domain_or_triangle_census_performed:false,proof_check_milliseconds:Date.now()-started};
 const reportText=JSON.stringify(report)+"\n",rb=C.utf8(reportText);ck(rb.length<=1048576,"report byte bound");
 let final={schema:"conway99.f0.target-color-twelve-finalization.v1",
  status:"PASS_COMPLETE_STRUCTURAL_CERTIFICATE_SERIALIZATION",report_sha256:C.sha256(rb),report_bytes:rb.length,
  total_milliseconds:Date.now()-started,maximum_milliseconds:30000,optimizer_calls:0,assignment_enumerations:0};
 let finalText=JSON.stringify(final)+"\n";
 if(Date.now()-started>30000){final.status="UNACCEPTED_STRUCTURAL_CERTIFICATE_BUDGET_OVERRUN";
  final.total_milliseconds=Date.now()-started;finalText=JSON.stringify(final)+"\n";}
 return{report_text:reportText,finalization_text:finalText};
}
return{certify,run};
})()
