(() => {
"use strict";
const BASE=68934,ROWS=257594,EDGE_OFFSET=540,MAX_EDGE=68393;
const PINS={ledger:"0103baa3822afaae8992e2be6517e6a173615a937a721e3e5a83c724cdc89e86",
  finalization:"1d3e3bb3850c75dd7ae79a6139493d39cede82f7faeb2dfa107de11e25aa9aae",
  gate:"d1179db268413caabeaddc85e007bab7698ffc89887153699fbdc5a2ae5f1a14",
  support_configuration:"c14d0bcb35d3ee393039fd6af0e7e74bce7625c523077428a61fd32c6adec456",
  model_acceptance:"1c09b33189f337c90759a6339716fee001efe0b7b6c3727f8a0ec41e8a141116"};
function need(x,m){if(!x)throw Error(m);}
function equal(a,b,m){need(JSON.stringify(a)===JSON.stringify(b),m);}
function int(x,l,h){need(Number.isSafeInteger(x)&&x>=l&&x<=h,"integer range");}
function pair(a,b){return a<b?[a,b]:[b,a];}
function tupleCompare(a,b){for(let i=0;i<a.length;i++)if(a[i]!==b[i])return a[i]-b[i];return 0;}
function row(lower,upper,terms){terms=terms.slice().sort((a,b)=>a[0]-b[0]);need(new Set(terms.map(t=>t[0])).size===terms.length,"distinct row variables");return [lower,upper,terms];}
function andRows(edges,variable){
  return [...edges.map(e=>row(0,1,[[EDGE_OFFSET+e,1],[variable,-1]])),
    row(-2,1,[[variable,1],...edges.map(e=>[EDGE_OFFSET+e,-1])])];
}
function assemble(records,base,tick){
  const tripleMap=new Map(),edgePairs=new Map(),pairEdges=new Map(),seenTargets=new Set();
  const targets=[];
  function bindEdge(e,a,b){
    int(e,0,MAX_EDGE);int(a,0,479);int(b,0,479);need(a!==b,"distinct edge endpoints");
    const p=pair(a,b),k=p.join(",");
    if(edgePairs.has(e))equal(edgePairs.get(e),p,"one edge ID has one pair");else edgePairs.set(e,p);
    if(pairEdges.has(k))need(pairEdges.get(k)===e,"one pair has one edge ID");else pairEdges.set(k,e);
  }
  for(const record of records){
    tick();const e=record.edge_id,[a,b]=record.endpoints;
    need(a<b&&!seenTargets.has(e),"distinct ordered target");seenTargets.add(e);bindEdge(e,a,b);
    const keys=[];
    for(const support of record.supports){
      const [v,left,right]=support.row;int(v,0,479);need(v!==a&&v!==b,"third distinct");
      need(new Set([e,left,right]).size===3,"three distinct triangle edges");bindEdge(left,a,v);bindEdge(right,b,v);
      const vertices=[a,b,v].sort((x,y)=>x-y),k=vertices.join(",");
      const local=new Map([[pair(a,b).join(","),e],[pair(a,v).join(","),left],[pair(b,v).join(","),right]]);
      const edges=[local.get(pair(vertices[0],vertices[1]).join(",")),local.get(pair(vertices[0],vertices[2]).join(",")),local.get(pair(vertices[1],vertices[2]).join(","))];
      const origin={target_edge_id:e,support_table_index:record.support_table_index,support_index:support.index};
      if(!tripleMap.has(k))tripleMap.set(k,{vertices,edge_ids:edges,origins:[]});
      const item=tripleMap.get(k);equal(item.edge_ids,edges,"shared triangle edge identity");item.origins.push(origin);keys.push(k);
    }
    need(keys.length>0&&new Set(keys).size===keys.length,"complete nonempty distinct target supports");
    targets.push({edge_id:e,endpoints:[a,b],required_premise_index:record.premise_index,keys});
  }
  const triangles=Array.from(tripleMap.values()).sort((a,b)=>tupleCompare(a.vertices,b.vertices));
  const indices=new Map();
  triangles.forEach((t,i)=>{t.triangle_index=i;t.proposed_variable_index=base+i;indices.set(t.vertices.join(","),i);
    t.origins.sort((a,b)=>a.target_edge_id-b.target_edge_id||a.support_index-b.support_index);
    need(t.origins.length>=1&&t.origins.length<=3,"one origin per incident target edge");});
  targets.sort((a,b)=>a.edge_id-b.edge_id);
  for(const target of targets){target.triangle_indices=target.keys.map(k=>indices.get(k)).sort((a,b)=>a-b);delete target.keys;}
  const incidence=targets.reduce((s,t)=>s+t.triangle_indices.length,0);
  need(incidence===triangles.reduce((s,t)=>s+t.origins.length,0),"all shared incidences retained");
  return {triangles,targets,incidence};
}
function controls(){
  const tick=()=>{},rows=andRows([0,1,2],2000);let andAssignments=0;
  function satisfies(rs,values){return rs.every(([lo,hi,ts])=>{const s=ts.reduce((n,[j,c])=>n+c*values.get(j),0);return lo<=s&&s<=hi;});}
  for(let mask=0;mask<8;mask++)for(let t=0;t<2;t++){
    const y=[mask&1,(mask>>>1)&1,(mask>>>2)&1],values=new Map(y.map((v,j)=>[EDGE_OFFSET+j,v]));values.set(2000,t);
    need(satisfies(rows,values)===(t===(y[0]&y[1]&y[2])),"exact three-edge AND truth table");andAssignments++;
  }
  const openPath=new Map([[540,0],[541,1],[542,1],[2000,0]]);
  need(satisfies(rows,openPath),"inactive target permits the two-edge path");
  const records=[
    {edge_id:0,endpoints:[0,1],premise_index:0,support_table_index:0,supports:[{index:0,row:[2,1,2,-1]},{index:1,row:[3,3,4,-1]}]},
    {edge_id:1,endpoints:[0,2],premise_index:1,support_table_index:1,supports:[{index:0,row:[1,0,2,-1]}]}
  ];
  const a=assemble(records,2000,tick);need(a.triangles.length===2&&a.incidence===3,"shared triangle deduplicated");
  equal(a.targets.map(t=>t.triangle_indices),[[0,1],[0]],"all target incidences");
  const syntheticRows=a.triangles.flatMap(t=>andRows(t.edge_ids,t.proposed_variable_index));
  for(const target of a.targets)syntheticRows.push(row(0,0,[...target.triangle_indices.map(i=>[2000+i,1]),[540+target.edge_id,-1]]));
  need(syntheticRows.length===10&&syntheticRows.reduce((s,r)=>s+r[2].length,0)===25,"row and term accounting");
  let sharedAssignments=0,validAssignments=0;
  for(let mask=0;mask<32;mask++)for(let aux=0;aux<4;aux++){
    const y=Array.from({length:5},(_,i)=>(mask>>>i)&1),t=[aux&1,(aux>>>1)&1];
    const values=new Map(y.map((v,i)=>[540+i,v]));values.set(2000,t[0]);values.set(2001,t[1]);
    const logical=t[0]===(y[0]&y[1]&y[2])&&t[1]===(y[0]&y[3]&y[4])&&t[0]+t[1]===y[0]&&t[0]===y[1];
    need(satisfies(syntheticRows,values)===logical,"shared indicator and target equations");sharedAssignments++;if(logical)validAssignments++;
  }
  let rejected=0;const bad=JSON.parse(JSON.stringify(records));bad[1].supports[0].row[1]=5;
  try{assemble(bad,2000,tick);}catch(_){rejected++;}
  need(rejected===1,"inconsistent shared edge identity rejected");
  return {status:"PASS_TRIANGLE_INDICATOR_TINY_CONTROLS",and_assignments:andAssignments,shared_assignments:sharedAssignments,
    valid_shared_assignments:validAssignments,open_two_edge_path_preserved:true,inconsistent_shared_edge_rejected:true,
    actual_case_inventory_calls:0,native_model_builds:0,optimizer_calls:0};
}
function run(configText,payload,codecText,sourceText){
  const start=Date.now(),c=eval(codecText),cfg=JSON.parse(configText),tick=()=>{if(Date.now()-start>=10000)throw Error("10-second inventory deadline");};
  need(cfg.maximum_ms===10000&&cfg.maximum_report_bytes===16777216,"declared bounds");
  need(c.sha256(c.utf8(codecText))==="fbccc2396bfbe6085576f02468ef0acd23182445837c02abd5d05e00b9e87a00","codec");
  need(c.sha256(c.utf8(sourceText))===cfg.source.sha256,"source");
  equal(Object.keys(payload).sort(),Object.keys(PINS).sort(),"exact input set");
  const data={};
  for(const name of Object.keys(PINS)){tick();const ref=cfg.inputs[name],bytes=c.utf8(payload[name]);
    need(ref.sha256===PINS[name]&&bytes.length===ref.bytes&&c.sha256(bytes)===ref.sha256&&c.gitBlob(bytes)===ref.git_blob,"input "+name);
    data[name]=JSON.parse(payload[name]);}
  const l=data.ledger,f=data.finalization,g=data.gate,sc=data.support_configuration,m=data.model_acceptance;
  need(l.status==="PASS_COMPLETE_TARGETED_SUPPORT_FIXED_POINT"&&l.complete&&l.error===null,"accepted support ledger");
  need(f.status==="PASS_COMPLETE_SUPPORT_CHECK_AND_SERIALIZATION"&&f.report_complete&&f.within_declared_bounds&&f.main_calls===1,"support finalization");
  need(f.report_bytes===cfg.inputs.ledger.bytes&&f.elapsed_ms<30000,"support byte/time binding");
  need(g.status==="AUTHORIZE_ONE_TARGETED_TRIANGLE_SUPPORT_FIXED_POINT"&&g.source.sha256===l.source.sha256,"support source gate");
  need(g.configuration.sha256===l.configuration_sha256&&l.configuration_sha256===PINS.support_configuration,"support configuration");
  equal(l.inputs,sc.inputs,"all original support premise bindings");
  need(l.target_count===132&&l.initially_zero_targets.length===48&&l.uneliminated_targets.length===84,"fixed complete target partition");
  need(l.new_edge_zero_count===0&&l.certificates.length===0&&l.initial_zero_count===1956,"accepted fixed-point outcome");
  const zeros=new Set(l.final_zero_edge_ids);need(zeros.size===1956,"final initial zero set");
  const targetMap=new Map(l.targets.map(t=>[t.edge_id,t])),tableMap=new Map(l.support_tables.map((t,i)=>[t.edge_id,{...t,index:i}]));
  need(targetMap.size===132&&tableMap.size===84,"target/table distinctness");
  for(const t of l.initially_zero_targets)need(zeros.has(t.edge_id),"old zero target");
  const records=[];
  for(const terminal of l.uneliminated_targets){tick();const target=targetMap.get(terminal.edge_id),table=tableMap.get(terminal.edge_id);
    need(target&&table&&!zeros.has(target.edge_id)&&target.premise_index===terminal.premise_index&&target.premise_index===table.premise_index,"live target identity");
    const live=[];
    table.supports.forEach((s,i)=>{need(s.length===4,"support shape");if(s[3]===-1&&!zeros.has(s[1])&&!zeros.has(s[2]))live.push(i);});
    equal(live,terminal.surviving_support_indices,"complete final live support indices");
    records.push({edge_id:target.edge_id,endpoints:target.endpoints,premise_index:target.premise_index,support_table_index:table.index,
      supports:live.map(i=>({index:i,row:table.supports[i]}))});
  }
  need(m.status==="ROOT_ACCEPTS_COMPLETE_STRENGTHENED_NATIVE_MODEL_AND_INDEPENDENT_COLD"&&m.variables===BASE&&m.rows===ROWS,"frozen base namespace");
  need(m.model_raw_sha256==="4a9b24ab1a0a1758ffedab226a9c45fe7765fafc40e76e23a039c9ccd098aee2","frozen base model");
  const a=assemble(records,BASE,tick),T=a.triangles.length,I=a.incidence;
  const report={schema:"conway99.f0.spectral-triangle-support-indicator-inventory.v1",status:"PASS_EXACT_SHARED_TRIANGLE_INDICATOR_INVENTORY",
    source:cfg.source,configuration_sha256:c.sha256(c.utf8(configText)),inputs:cfg.inputs,
    live_targets:84,already_zero_targets:48,unique_surviving_support_triples:T,target_triangle_incidences:I,
    triangles:a.triangles,targets:a.targets,
    proposed_native_dimensions:{base_variables:BASE,new_boolean_variables:T,total_variables:BASE+T,base_rows:ROWS,
      and_rows:4*T,target_equalities:84,new_rows:4*T+84,total_rows:ROWS+4*T+84,
      and_terms:10*T,target_equality_terms:I+84,new_terms:10*T+I+84},
    exact_templates:{upper:"0 <= y_edge - t_triangle <= 1, once for each of three edges",
      lower:"-2 <= t_triangle - y_ab - y_ac - y_bc <= 1",
      target:"sum(t_triangle for all live supports of e) - y_e = 0"},
    necessary_graph_extension_proved:true,equivalence_to_old_relaxation_claimed:false,
    all_original_rows_and_columns_retained_in_proposal:true,native_model_built:false,native_model_modified:false,
    optimizer_calls:0,support_domain_reenumerated:false};
  tick();const text=JSON.stringify(report)+"\n";
  for(let i=0;i<text.length;i++)need(text.charCodeAt(i)<128,"ASCII report");
  const elapsed=Date.now()-start;
  return {report,text,finalization:{status:elapsed<10000&&text.length<=16777216?"PASS_INVENTORY_AND_SERIALIZATION":"UNACCEPTED_INVENTORY_BOUND",
    elapsed_ms:elapsed,maximum_ms:10000,report_bytes:text.length,maximum_report_bytes:16777216,
    within_declared_bounds:elapsed<10000&&text.length<=16777216,main_calls:1,native_model_builds:0,optimizer_calls:0}};
}
return {controls,run};
})()
