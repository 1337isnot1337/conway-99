(() => {
"use strict";
const N=480,EDGE_COUNT=68394,EDGE_HASH="411052a41a473bb7199fe277516fb60c54018dec120309622a499229579791bb";
const TRIANGLE_HASH="60dd838a427e23b5d3c773e7eb8ecb9852e77a88bd0d9e1ac647e51be7965ff8";
const EXPECTED={initial_zeros:1956,targets:132,already_zero_targets:48,live_targets:84,structural_records:6540,surviving_records:5364};
function require(x,m){if(!x)throw Error(m);}
function canonical(v){if(v===null||typeof v!=="object")return JSON.stringify(v);
  if(Array.isArray(v))return "["+v.map(canonical).join(",")+"]";
  return "{"+Object.keys(v).sort().map(k=>JSON.stringify(k)+":"+canonical(v[k])).join(",")+"}";}
function identical(a,b,m){require(canonical(a)===canonical(b),m);}
function bounded(x,l,h){require(Number.isSafeInteger(x)&&x>=l&&x<=h,"integer range");}
function pairKey(a,b){return a<b?a+":"+b:b+":"+a;}
function triKey(a,b,v){const t=[a,b,v];t.sort((x,y)=>x-y);return t.join(":");}
function separate(a,b){for(const x of a)if(b.has(x))return false;return true;}
function readLiteralDomain(d,tick){
  const n=d.signature_domain.length,signatures=d.signature_domain.map(h=>{
    require(h.length===3&&new Set(h).size===3,"literal signature weight");
    for(const x of h)bounded(x,0,17);identical(h,h.slice().sort((a,b)=>a-b),"signature order");return new Set(h);});
  require(new Set(d.signature_domain.map(h=>h.join(":"))).size===n,"distinct signatures");
  require(d.component_adjacency_rows.length===18,"18 core rows");
  const core=d.component_adjacency_rows.map((bits,i)=>{
    bounded(bits,0,(1<<18)-1);const s=new Set();for(let j=0;j<18;j++)if((bits>>>j)&1)s.add(j);
    require(!s.has(i),"core diagonal");return s;});
  for(let i=0;i<18;i++)for(let j=0;j<18;j++)require(core[i].has(j)===core[j].has(i),"undirected core");
  const quotas=[];
  for(let a=n-1;a>=0;a--){
    tick();const row=[];
    for(let i=0;i<18;i++){let adjacent=0;for(const x of signatures[a])if(core[i].has(x))adjacent++;
      row.push(2-(signatures[a].has(i)?1:0)-adjacent);}
    identical(row,d.row_targets[a],"independent literal quota row");quotas[a]=row;
  }
  // Larger endpoint is outermost and both endpoints descend. Native IDs are assigned only after sorting.
  const edges=[],neighbors=Array.from({length:n},()=>new Set());
  for(let b=n-1;b>0;b--){
    tick();
    for(let a=b-1;a>=0;a--){
      let common=0;for(const x of signatures[a])if(signatures[b].has(x))common++;
      if(common>1)continue;
      let allowed=true;
      for(const x of signatures[b])if(quotas[a][x]<=0)allowed=false;
      for(const x of signatures[a])if(quotas[b][x]<=0)allowed=false;
      if(allowed){edges.push([a,b]);neighbors[a].add(b);neighbors[b].add(a);}
    }
  }
  edges.sort((x,y)=>x[0]-y[0]||x[1]-y[1]);
  const edgeIDs=new Map(edges.map((p,i)=>[pairKey(...p),i]));
  require(edgeIDs.size===edges.length,"distinct eligible edges");
  if(d.possible_neighbor_signature_ids!==undefined)
    for(let a=n-1;a>=0;a--)identical(Array.from(neighbors[a]).sort((x,y)=>x-y),d.possible_neighbor_signature_ids[a],"complete original neighbor row");
  return {n,signatures,signatureArrays:d.signature_domain,quotas,edges,edgeIDs,neighbors};
}
function thirdVertexTables(g,targets,covers,tick){
  const byFirst=Array.from({length:g.n},()=>[]),tables=new Map();
  for(const target of targets){const [a,b]=target.endpoints;
    require(a<b&&g.edgeIDs.get(pairKey(a,b))===target.edge_id&&!tables.has(target.edge_id),"target identity");
    byFirst[a].push(target);tables.set(target.edge_id,[]);}
  for(const row of byFirst)row.sort((x,y)=>y.endpoints[1]-x.endpoints[1]);
  // Enumerate the third vertex first, via its literal disjoint-neighbor set.
  for(let v=g.n-1;v>=0;v--){
    tick();const disjointNeighbors=new Set();
    for(const a of g.neighbors[v])if(separate(g.signatures[a],g.signatures[v]))disjointNeighbors.add(a);
    for(const a of Array.from(disjointNeighbors).sort((x,y)=>y-x)){
      for(const target of byFirst[a]){
        const b=target.endpoints[1];
        if(!disjointNeighbors.has(b)||!separate(g.signatures[a],g.signatures[b]))continue;
        const left=g.edgeIDs.get(pairKey(a,v)),right=g.edgeIDs.get(pairKey(b,v)),k=triKey(a,b,v);
        require(left!==undefined&&right!==undefined,"original side edges");
        tables.get(target.edge_id).push([v,left,right,covers.has(k)?covers.get(k):-1]);
      }
    }
  }
  return tables;
}
function compareTables(targets,tables,zeros,savedTables,savedTerminal,tick){
  const tableMap=new Map(savedTables.map((t,i)=>[t.edge_id,{...t,table_index:i}]));
  const terminalMap=new Map(savedTerminal.map(t=>[t.edge_id,t]));
  require(tableMap.size===savedTables.length&&terminalMap.size===savedTerminal.length,"no duplicate saved target");
  require(tableMap.size===targets.length&&terminalMap.size===targets.length&&tables.size===targets.length,"complete table/terminal target coverage");
  let structural=0,surviving=0;const normalized=[];
  for(const target of targets.slice().sort((a,b)=>b.edge_id-a.edge_id)){
    tick();const saved=tableMap.get(target.edge_id),terminal=terminalMap.get(target.edge_id);
    require(saved&&terminal&&saved.premise_index===target.premise_index&&terminal.premise_index===target.premise_index,"saved premise identity");
    const rows=tables.get(target.edge_id).slice().sort((a,b)=>a[0]-b[0]);
    require(new Set(rows.map(r=>r[0])).size===rows.length,"one support per third selector");
    identical(rows,saved.supports,"every independently reconstructed structural record");
    const live=[];
    for(let i=0;i<rows.length;i++)if(rows[i][3]===-1&&!zeros.has(rows[i][1])&&!zeros.has(rows[i][2]))live.push(i);
    identical(live,terminal.surviving_support_indices,"every independently reconstructed surviving index");
    require(live.length>0,"terminal fixed point has a live support");
    structural+=rows.length;surviving+=live.length;
    normalized.push([target.edge_id,target.premise_index,rows,live]);
  }
  normalized.sort((a,b)=>a[0]-b[0]);
  return {structural,surviving,normalized};
}
function acceptedPremises(d,o,s,sa,t,ts,ta,g,c,tick){
  require(d.status==="complete component-zero exterior-row domain preparation"&&d.complete_signature_count===N&&d.complete_possible_edge_count===EDGE_COUNT,"domain status");
  require(d.hypothetical_graph_symmetry_assumed===false,"no selector symmetry restriction");
  require(g.n===N&&g.edges.length===EDGE_COUNT&&c.sha256(c.utf8(JSON.stringify(g.edges)))===EDGE_HASH,"complete original edge namespace");
  require(s.status==="PASS_COMPLETE_INDEPENDENT_SPECTRAL_GAP_PAIR_CENSUS"&&s.complete&&s.all405426_saved_integer_determinants_checked,"accepted spectral cold");
  require(sa.status==="ROOT_ACCEPTS_COMPLETE_INDEPENDENT_SPECTRAL_GAP_PAIR_CENSUS"&&sa.all_forward_and_cold_deduction_rows_compared,"spectral acceptance");
  require(o.status==="COMPLETE_LITERAL_PRISM_ZEROS_AND_CORE_PAIR_CLIQUES"&&o.complete_edge_order_sha256===EDGE_HASH,"accepted literal zero overlay");
  const zeroOrigins=new Map(),oldZeros=new Set();
  function add(e,origin){if(!zeroOrigins.has(e))zeroOrigins.set(e,{edge_id:e,endpoints:g.edges[e],origins:[]});zeroOrigins.get(e).origins.push(origin);}
  require(o.zero_rows.length===1884,"1884 literal zero rows");
  for(let i=0;i<o.zero_rows.length;i++){
    const z=o.zero_rows[i];bounded(z.edge_id,0,EDGE_COUNT-1);
    require(!oldZeros.has(z.edge_id)&&z.native_row_index===163070+i&&z.variable_index===540+z.edge_id,"literal zero native identity");
    identical(z.witness.pair,g.edges[z.edge_id],"literal zero endpoint witness");oldZeros.add(z.edge_id);
    add(z.edge_id,{kind:"literal_overlay",record_index:i,native_row_index:z.native_row_index});
  }
  const spectralZeros=s.mathematical.edge_zero_rows,seen=new Set();require(spectralZeros.length===132,"132 spectral zero rows");
  spectralZeros.forEach((r,i)=>{require(r.length===4,"spectral zero record");const [a,b,e,old]=r;bounded(e,0,EDGE_COUNT-1);
    require(!seen.has(e)&&typeof old==="boolean"&&old===oldZeros.has(e),"spectral zero distinctness/disposition");seen.add(e);
    identical([a,b],g.edges[e],"spectral zero original identity");add(e,{kind:"spectral_zero",record_index:i});});
  const initial=Array.from(zeroOrigins.values()).sort((a,b)=>a.edge_id-b.edge_id);
  require(initial.length===EXPECTED.initial_zeros,"initial zero union");
  const zeros=new Set(initial.map(x=>x.edge_id)),initialIndex=new Map(initial.map((x,i)=>[x.edge_id,i]));
  const required=s.mathematical.edge_present_requires_one_common_exterior_neighbor,targets=[];
  require(required.length===132&&sa.edge_present_requires_one_common_exterior_neighbor===132,"complete must-triangle list");
  const requiredSeen=new Set();
  required.forEach((r,i)=>{require(r.length===4,"required edge record");const [a,b,e,old]=r;bounded(e,0,EDGE_COUNT-1);
    require(!requiredSeen.has(e)&&typeof old==="boolean"&&old===oldZeros.has(e),"required edge uniqueness/disposition");requiredSeen.add(e);
    identical([a,b],g.edges[e],"required original edge identity");
    require(separate(g.signatures[a],g.signatures[b]),"must-triangle endpoints have disjoint signatures");
    targets.push({edge_id:e,premise_index:i,endpoints:[a,b]});});
  targets.sort((a,b)=>a.edge_id-b.edge_id);
  const already=targets.filter(x=>zeros.has(x.edge_id)).map(x=>({edge_id:x.edge_id,premise_index:x.premise_index,authority:{kind:"initial",index:initialIndex.get(x.edge_id)}}));
  const live=targets.filter(x=>!zeros.has(x.edge_id));
  require(already.length===48&&live.length===84,"complete target partition");
  require(t.status==="COMPLETE_EXACT_TRIANGLE_PRINCIPAL_MINOR_CENSUS"&&ts.status==="PASS_COMPLETE_INDEPENDENT_CENSUS_AND_LITERAL_ZERO_DISPOSITION","accepted triangle records");
  require(ta.status==="ROOT_ACCEPTS_COMPLETE_INDEPENDENT_CENSUS_AND_EVERY_ZERO_DISPOSITION"&&ta.all_exact_negative_records_and_proper_minors_compared===10830,"triangle root acceptance");
  const family=t.families.find(f=>f.family==="plus"),records=family.nonpositive_determinant_records_with_nonnegative_proper_minors;
  require(records.length===10830&&c.sha256(c.utf8(JSON.stringify(records)))===TRIANGLE_HASH,"complete accepted triangle row hash");
  require(ts.families.find(f=>f.family==="plus").nonpositive_records_sha256===TRIANGLE_HASH,"independent triangle hash binding");
  const covers=new Map();
  for(let i=records.length-1;i>=0;i--){
    if((i&255)===0)tick();const r=records[i];require(r.length===7,"triangle record length");const [a,b,v]=r;
    bounded(a,0,N-1);bounded(b,a+1,N-1);bounded(v,b+1,N-1);
    require(separate(g.signatures[a],g.signatures[b])&&separate(g.signatures[a],g.signatures[v])&&separate(g.signatures[b],g.signatures[v]),"literal cover disjointness");
    require(g.edgeIDs.has(pairKey(a,b))&&g.edgeIDs.has(pairKey(a,v))&&g.edgeIDs.has(pairKey(b,v)),"literal cover eligible edges");
    const k=triKey(a,b,v);require(!covers.has(k),"distinct accepted cover");covers.set(k,i);
  }
  return {initial,zeros,targets,already,live,covers};
}
function controls(){
  const started=Date.now(),tick=()=>{},full=[[0,1],[0,2],[0,3],[1,2],[1,3],[2,3]],triples=[[0,1,2],[0,1,3],[0,2,3],[1,2,3]];
  const fixtures=[[[0,1,2],[3,4,5],[6,7,8],[9,10,11]],[[0,1,2],[0,3,4],[5,6,7],[8,9,10]],[[0,1,2],[0,1,3],[4,5,6],[7,8,9]]];
  let systems=0,recordsChecked=0,survivorsChecked=0;
  function toyGraph(h,edges){
    const neighbors=Array.from({length:h.length},()=>new Set());for(const [a,b]of edges){neighbors[a].add(b);neighbors[b].add(a);}
    return {n:h.length,signatureArrays:h,signatures:h.map(x=>new Set(x)),edges,neighbors,edgeIDs:new Map(edges.map((p,i)=>[pairKey(...p),i]))};
  }
  function scalar(g,targets,covers,zeros){
    const saved=[],terminal=[];
    for(const target of targets){const [a,b]=target.endpoints,rows=[];
      for(let v=0;v<g.n;v++){
        if(v===a||v===b)continue;
        if(g.signatureArrays[a].some(x=>g.signatureArrays[b].includes(x))||
           g.signatureArrays[a].some(x=>g.signatureArrays[v].includes(x))||
           g.signatureArrays[b].some(x=>g.signatureArrays[v].includes(x)))continue;
        const left=g.edges.findIndex(p=>(p[0]===a&&p[1]===v)||(p[0]===v&&p[1]===a));
        const right=g.edges.findIndex(p=>(p[0]===b&&p[1]===v)||(p[0]===v&&p[1]===b));
        if(left<0||right<0)continue;
        const key=[a,b,v].sort((x,y)=>x-y).join(":");rows.push([v,left,right,covers.has(key)?covers.get(key):-1]);
      }
      saved.push({edge_id:target.edge_id,premise_index:target.premise_index,supports:rows});
      terminal.push({edge_id:target.edge_id,premise_index:target.premise_index,
        surviving_support_indices:rows.map((r,i)=>r[3]===-1&&!zeros.has(r[1])&&!zeros.has(r[2])?i:-1).filter(i=>i>=0)});
    }
    return {saved,terminal};
  }
  for(const h of fixtures)for(let graphMask=0;graphMask<64;graphMask++){
    const edges=full.filter((_,i)=>graphMask&(1<<i)),g=toyGraph(h,edges);
    const targets=edges.map((p,i)=>({edge_id:i,premise_index:i,endpoints:p}));
    for(let coverMask=0;coverMask<16;coverMask++)for(let zmode=0;zmode<2;zmode++){
      const covers=new Map(triples.map((t,i)=>[t.join(":"),i]).filter((_,i)=>coverMask&(1<<i))),zeros=new Set();
      if(zmode&&edges.length){zeros.add(0);zeros.add(edges.length-1);}
      const expected=scalar(g,targets,covers,zeros),actual=thirdVertexTables(g,targets,covers,tick);
      for(let i=0;i<targets.length;i++){
        const rows=actual.get(i).slice().sort((a,b)=>a[0]-b[0]);identical(rows,expected.saved[i].supports,"independent finite triple oracle");
        const live=rows.map((r,j)=>r[3]===-1&&!zeros.has(r[1])&&!zeros.has(r[2])?j:-1).filter(j=>j>=0);
        identical(live,expected.terminal[i].surviving_support_indices,"independent finite support filter");
        recordsChecked+=rows.length;survivorsChecked+=live.length;
      }
      systems++;
    }
  }
  // Quota controls use independent direct expected graph facts, not the support constructor.
  const h=fixtures[0],core=Array(18).fill(0);
  function quotaRows(h,core){return h.map(s=>Array.from({length:18},(_,i)=>2-(s.includes(i)?1:0)-s.filter(x=>(core[i]>>>x)&1).length));}
  let d={signature_domain:h,component_adjacency_rows:core,row_targets:quotaRows(h,core)};
  require(readLiteralDomain(d,tick).edges.length===6,"disjoint signatures with empty core");
  const h2=fixtures[2];d={signature_domain:h2,component_adjacency_rows:core,row_targets:quotaRows(h2,core)};
  const overlap=readLiteralDomain(d,tick);require(overlap.edges.length===5&&!overlap.edgeIDs.has("0:1"),"two shared sites reject pair");
  const core2=Array(18).fill(0);core2[3]=(1<<0)|(1<<1);core2[0]=core2[1]=1<<3;
  d={signature_domain:h,component_adjacency_rows:core2,row_targets:quotaRows(h,core2)};
  const qg=readLiteralDomain(d,tick);require(qg.quotas[0][3]===0&&!qg.edgeIDs.has("0:1"),"zero mixed quota rejects disjoint pair");
  const g=toyGraph(h.slice(0,3),[[0,1],[0,2],[1,2]]),targets=g.edges.map((p,i)=>({edge_id:i,premise_index:i,endpoints:p}));
  const covers=new Map(),zeros=new Set(),original=scalar(g,targets,covers,zeros),tables=thirdVertexTables(g,targets,covers,tick);
  compareTables(targets,tables,zeros,original.saved,original.terminal,tick);
  let rejected=0;const clone=x=>JSON.parse(JSON.stringify(x));
  for(let change=0;change<5;change++){
    const bad=clone(original);
    if(change===0)bad.saved[0].supports=[];
    if(change===1)bad.saved[0].supports[0][1]=999;
    if(change===2)bad.saved[0].supports[0][3]=0;
    if(change===3)bad.terminal[0].surviving_support_indices=[];
    if(change===4)bad.saved.pop();
    try{compareTables(targets,tables,zeros,bad.saved,bad.terminal,tick);}catch(_){rejected++;continue;}
    throw Error("altered support ledger accepted");
  }
  require(rejected===5,"five ledger mutations rejected");
  return {status:"PASS_INDEPENDENT_LITERAL_SUPPORT_TINY_CONTROLS",systems,structural_records_compared:recordsChecked,
    surviving_records_compared:survivorsChecked,quota_controls:3,rejected_ledger_mutations:rejected,
    forward_source_imported:false,actual_case_main_calls:0,native_model_builds:0,optimizer_calls:0,elapsed_ms:Date.now()-started};
}
function run(configText,payload,codecText,sourceText){
  const started=Date.now(),c=eval(codecText),cfg=JSON.parse(configText);
  const progress={phase:"input_bindings",complete:false};let error=null,summary=null;
  const tick=()=>{if(Date.now()-started>=30000)throw Error("30-second complete literal-support replay deadline");};
  try{
    require(cfg.maximum_ms===30000&&cfg.maximum_report_bytes===16777216,"fixed replay bounds");
    identical(cfg.expected,EXPECTED,"fixed complete target");
    require(c.sha256(c.utf8(codecText))==="fbccc2396bfbe6085576f02468ef0acd23182445837c02abd5d05e00b9e87a00","codec binding");
    require(c.sha256(c.utf8(sourceText))===cfg.source.sha256,"source binding");
    const names=["domain","overlay","spectral_cold","spectral_acceptance","triangle_forward","triangle_summary","triangle_acceptance",
      "support_ledger","support_finalization","support_gate","support_configuration"];
    identical(Object.keys(cfg.inputs).sort(),names.slice().sort(),"exact premise scope");
    identical(Object.keys(payload).sort(),names.slice().sort(),"exact payload scope");
    const data={};
    for(const name of names){
      tick();const ref=cfg.inputs[name],raw=ref.encoding==="base64_gzip"?c.base64(payload[name]):c.utf8(payload[name]);
      require(raw.length===ref.bytes&&c.sha256(raw)===ref.sha256&&c.gitBlob(raw)===ref.git_blob,"input bytes "+name);
      const decoded=ref.encoding==="base64_gzip"?c.gunzip(raw):raw;
      if(ref.raw_sha256)require(c.sha256(decoded)===ref.raw_sha256,"raw archive "+name);
      data[name]=JSON.parse(c.ascii(decoded));
    }
    const l=data.support_ledger,f=data.support_finalization,g=data.support_gate,sc=data.support_configuration;
    require(l.status==="PASS_COMPLETE_TARGETED_SUPPORT_FIXED_POINT"&&l.complete&&l.error===null,"forward complete ledger");
    require(f.status==="PASS_COMPLETE_SUPPORT_CHECK_AND_SERIALIZATION"&&f.within_declared_bounds&&f.report_complete&&f.main_calls===1,"forward finalization");
    require(f.report_bytes===cfg.inputs.support_ledger.bytes&&f.elapsed_ms<30000,"forward report/clock");
    require(g.status==="AUTHORIZE_ONE_TARGETED_TRIANGLE_SUPPORT_FIXED_POINT"&&g.source.sha256===l.source.sha256,"forward source gate");
    require(g.configuration.sha256===cfg.inputs.support_configuration.sha256&&l.configuration_sha256===cfg.inputs.support_configuration.sha256,"forward configuration");
    identical(l.inputs,sc.inputs,"forward premise bindings");
    for(const name of names.slice(0,7))identical(cfg.inputs[name],sc.inputs[name],"same independently replayed premise "+name);
    require(data.spectral_acceptance.cold.sha256===cfg.inputs.spectral_cold.sha256,"spectral acceptance/cold binding");
    identical(data.triangle_summary.report,data.triangle_acceptance.report,"triangle acceptance/cold binding");
    progress.phase="literal_original_edge_reconstruction";
    const graph=readLiteralDomain(data.domain,tick);
    const premises=acceptedPremises(data.domain,data.overlay,data.spectral_cold,data.spectral_acceptance,
      data.triangle_forward,data.triangle_summary,data.triangle_acceptance,graph,c,tick);
    identical(premises.initial,l.initial_zero_authorities,"all 1956 zero authorities and complete origins");
    identical(premises.targets,l.targets,"all 132 required targets and original indices");
    identical(premises.already,l.initially_zero_targets,"all 48 already-zero targets");
    identical(Array.from(premises.zeros).sort((a,b)=>a-b),l.final_zero_edge_ids,"full final zero set");
    require(l.initial_zero_count===1956&&l.target_count===132&&l.new_edge_zero_count===0&&l.completed_passes===1&&l.phase==="complete","exact forward fixed-point claims");
    require(l.certificates.length===0&&l.row_keys.length===0,"no unverified added zero");
    progress.phase="independent_third_vertex_enumeration";
    const tables=thirdVertexTables(graph,premises.live,premises.covers,tick);
    progress.phase="complete_literal_ledger_comparison";
    const compared=compareTables(premises.live,tables,premises.zeros,l.support_tables,l.uneliminated_targets,tick);
    require(compared.structural===6540&&compared.surviving===5364,"complete structural and surviving record counts");
    summary={...EXPECTED,original_eligible_edges:graph.edges.length,all_original_neighbor_rows_compared:480,
      accepted_triangle_covers:premises.covers.size,
      normalized_complete_support_records_sha256:c.sha256(c.utf8(JSON.stringify(compared.normalized))),
      every_remaining_target_has_live_support:true,zero_propagation_fixed_point_independently_verified:true,
      all_saved_support_records_and_surviving_indices_compared:true,
      all_initial_zero_authorities_and_target_premises_compared:true};
    tick();progress.phase="complete";progress.complete=true;
  }catch(e){error={name:e.name,message:String(e.message)};}
  const report={schema:"conway99.f0.spectral-triangle-support-independent-literal-replay.v1",
    status:progress.complete&&error===null?"PASS_COMPLETE_INDEPENDENT_LITERAL_SUPPORT_REPLAY":"UNACCEPTED_LITERAL_SUPPORT_REPLAY",
    source:cfg.source,configuration_sha256:c.sha256(c.utf8(configText)),inputs:cfg.inputs,expected:EXPECTED,progress,error,summary,
    enumeration:"Descending third vertex, through literal disjoint-neighbor sets and target edges anchored at their smaller endpoint.",
    edge_enumeration:"Descending larger endpoint and descending smaller endpoint, then canonical original edge-ID assignment.",
    forward_source_imported_or_called:false,signature_representation:"literal sets",
    source_author_also_authored_forward:true,independent_source_review_required:true,
    graph_constructed:false,whole_component_excluded:false,native_model_builds:0,optimizer_calls:0,
    seconds_before_serialization:(Date.now()-started)/1000};
  const text=JSON.stringify(report)+"\n";
  for(let i=0;i<text.length;i++)require(text.charCodeAt(i)<128,"ASCII report");
  const elapsed=Date.now()-started,within=elapsed<30000&&text.length<=16777216;
  return {report,text,finalization:{status:report.status==="PASS_COMPLETE_INDEPENDENT_LITERAL_SUPPORT_REPLAY"&&within?
    "PASS_COMPLETE_LITERAL_REPLAY_AND_SERIALIZATION":"UNACCEPTED_LITERAL_REPLAY_OR_BOUND",
    elapsed_ms:elapsed,maximum_ms:30000,report_bytes:text.length,maximum_report_bytes:16777216,
    within_declared_bounds:within,main_calls:1,native_model_builds:0,optimizer_calls:0}};
}
return {controls,run};
})()
