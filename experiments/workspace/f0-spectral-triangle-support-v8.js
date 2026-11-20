(() => {
"use strict";
const PIN = {
  codec_sha256:"fbccc2396bfbe6085576f02468ef0acd23182445837c02abd5d05e00b9e87a00",
  edge_sha256:"411052a41a473bb7199fe277516fb60c54018dec120309622a499229579791bb",
  triangle_records_sha256:"60dd838a427e23b5d3c773e7eb8ecb9852e77a88bd0d9e1ac647e51be7965ff8",
  domain_raw_sha256:"fa3bd2e5bb541d58cb647aa1d3df95a9d3c17e394836a657ad4f4bf6eb5f6bfe",
  overlay_raw_sha256:"bfdbdb641325f289fc844b6f430f6b0585584cf2b356a50e4a06b0fd78e69aee",
  spectral_sha256:"e8d27725afb707867f6683604ff1f3123f8960305c721058f495883f23476349",
  triangle_sha256:"7027feb1a77cb8131371bb10823ec7e5e8b6a33f5281a0b27881ee2f6b088155"
};
const LIMITS={maximum_ms:30000,maximum_report_bytes:16777216,maximum_targets:132,maximum_passes:133};
function need(value,message){if(!value)throw Error(message);}
function eq(a,b,message){need(JSON.stringify(a)===JSON.stringify(b),message);}
function integer(x,lo,hi){need(Number.isSafeInteger(x)&&x>=lo&&x<=hi,"integer range");return x;}
function pop(x){let n=0;for(;x;x&=x-1)n++;return n;}
function hash(c,text){return c.sha256(c.utf8(text));}
function referenceEqual(a,b){need(a.path===b.path&&a.sha256===b.sha256,"reference binding");if(a.bytes!==undefined&&b.bytes!==undefined)need(a.bytes===b.bytes,"reference bytes");}
function triangleKey(a,b,c){return [a,b,c].sort((x,y)=>x-y).join(",");}
function makeGraph(signatures,edges){
  const n=signatures.length,masks=signatures.map(s=>s.reduce((v,i)=>v|(1<<i),0));
  const index=new Int32Array(n*n);index.fill(-1);
  let last=-1;
  for(let e=0;e<edges.length;e++){const [a,b]=edges[e];integer(a,0,n-1);integer(b,a+1,n-1);
    need(a*n+b>last,"ordered distinct edges");last=a*n+b;index[a*n+b]=index[b*n+a]=e;}
  return {n,signatures,masks,edges,index};
}
function supports(g,e,covers,tick){
  const [a,b]=g.edges[e],out=[];
  if(g.masks[a]&g.masks[b])return out;
  for(let v=0;v<g.n;v++){
    if((v&63)===0)tick();
    if(v===a||v===b||(g.masks[v]&(g.masks[a]|g.masks[b])))continue;
    const left=g.index[a*g.n+v],right=g.index[b*g.n+v];
    if(left<0||right<0)continue;
    const k=triangleKey(a,b,v);
    out.push([v,left,right,covers.has(k)?covers.get(k):-1]);
  }
  return out;
}
// This checker reconstructs the support universe by literal set unions, not bit-mask filtering.
function verifyTable(g,e,table,covers,tick){
  const [a,b]=g.edges[e],expected=[];
  for(let v=0;v<g.n;v++){
    if((v&63)===0)tick();
    if(v===a||v===b)continue;
    const concatenated=[...g.signatures[a],...g.signatures[b],...g.signatures[v]];
    if(new Set(concatenated).size!==concatenated.length)continue;
    const left=g.index[a*g.n+v],right=g.index[b*g.n+v];
    if(left<0||right<0)continue;
    const k=[a,b,v].sort((x,y)=>x-y).join(",");
    expected.push([v,left,right,covers.has(k)?covers.get(k):-1]);
  }
  eq(table,expected,"complete literal support table");
}
function eliminateReason(s,known){
  if(s[3]>=0)return {kind:"triangle_cover",record_index:s[3]};
  const choices=[s[1],s[2]].filter(e=>known.has(e)).sort((a,b)=>a-b);
  if(!choices.length)return null;
  const e=choices[0];
  return {kind:"edge_zero",edge_id:e,authority:{...known.get(e)}};
}
function verifyCertificate(g,target,table,certificate,known,covers,tick){
  need(!known.has(target.edge_id),"target already zero");
  need(certificate.edge_id===target.edge_id&&certificate.required_premise_index===target.premise_index,"target premise");
  verifyTable(g,target.edge_id,table,covers,tick);
  need(certificate.eliminated_supports.length===table.length,"all supports accounted");
  for(let i=0;i<table.length;i++){
    const r=certificate.eliminated_supports[i],s=table[i];
    need(r.support_index===i,"support order");
    if(r.kind==="triangle_cover"){need(s[3]>=0&&r.record_index===s[3],"actual accepted triangle cover");}
    else{
      need(r.kind==="edge_zero"&&(r.edge_id===s[1]||r.edge_id===s[2]),"actual side-edge zero");
      need(known.has(r.edge_id),"earlier zero required");
      eq(r.authority,known.get(r.edge_id),"zero authority identity");
      if(r.authority.kind==="derived")need(r.authority.index<certificate.certificate_index,"strict prior dependency");
      else need(r.authority.kind==="initial","initial authority kind");
    }
  }
  eq(certificate.row_key,[0,0,[[540+target.edge_id,1]]],"native zero row");
}
function close(g,targets,initial,covers,tick,maximumPasses,progress){
  const known=new Map(initial.map((z,i)=>[z.edge_id,{kind:"initial",index:i}]));
  need(known.size===initial.length,"distinct initial zeros");
  progress.initial_zero_count=initial.length;
  const tables=new Map();
  for(const target of targets){
    tick();
    if(known.has(target.edge_id)){progress.initially_zero_targets.push({edge_id:target.edge_id,premise_index:target.premise_index,authority:known.get(target.edge_id)});continue;}
    const table=supports(g,target.edge_id,covers,tick);
    verifyTable(g,target.edge_id,table,covers,tick);
    tables.set(target.edge_id,table);
    progress.support_tables.push({edge_id:target.edge_id,premise_index:target.premise_index,supports:table});
  }
  progress.phase="closure";
  for(let pass=0;pass<maximumPasses;pass++){
    let changed=0;
    for(const target of targets){
      tick();
      if(known.has(target.edge_id))continue;
      const table=tables.get(target.edge_id),eliminated=[];
      let live=false;
      for(let i=0;i<table.length;i++){
        const r=eliminateReason(table[i],known);
        if(r===null){live=true;break;}
        eliminated.push({support_index:i,...r});
      }
      if(live)continue;
      const certificate={certificate_index:progress.certificates.length,pass,edge_id:target.edge_id,
        endpoints:g.edges[target.edge_id],required_premise_index:target.premise_index,
        eliminated_supports:eliminated,row_key:[0,0,[[540+target.edge_id,1]]]};
      verifyCertificate(g,target,table,certificate,known,covers,tick);
      // Commit only after the whole certificate passes. This forbids circular round-local reasoning.
      progress.certificates.push(certificate);
      known.set(target.edge_id,{kind:"derived",index:certificate.certificate_index});changed++;
    }
    progress.completed_passes=pass+1;
    if(changed!==0)continue;
    progress.phase="terminal_support_check";
    const terminal=[];
    for(const target of targets){
      tick();
      if(known.has(target.edge_id))continue;
      const table=tables.get(target.edge_id),live=[];
      verifyTable(g,target.edge_id,table,covers,tick);
      for(let i=0;i<table.length;i++)if(eliminateReason(table[i],known)===null)live.push(i);
      need(live.length>0,"every uneliminated target needs a surviving support");
      terminal.push({edge_id:target.edge_id,premise_index:target.premise_index,surviving_support_indices:live});
    }
    progress.uneliminated_targets=terminal;
    progress.final_zero_edge_ids=Array.from(known.keys()).sort((a,b)=>a-b);
    progress.phase="complete";progress.complete=true;
    return progress;
  }
  throw Error("finite monotone pass bound exceeded");
}
function emptyProgress(){return {phase:"input_binding",complete:false,initial_zero_count:0,initially_zero_targets:[],
  support_tables:[],certificates:[],completed_passes:0,uneliminated_targets:[],final_zero_edge_ids:[]};}
function load(cfg,payload,c,tick){
  const data={},bindings={};
  const names=["domain","overlay","spectral_cold","spectral_acceptance","triangle_forward","triangle_summary","triangle_acceptance"];
  eq(Object.keys(cfg.inputs).sort(),names.slice().sort(),"exact premise set");
  eq(Object.keys(payload).sort(),names.slice().sort(),"exact payload set");
  for(const name of names){
    tick();const ref=cfg.inputs[name],input=payload[name];
    need(typeof input==="string","string input");
    const archive=ref.encoding==="base64_gzip"?c.base64(input):c.utf8(input);
    need(archive.length===ref.bytes&&c.sha256(archive)===ref.sha256&&c.gitBlob(archive)===ref.git_blob,"input bytes "+name);
    const raw=ref.encoding==="base64_gzip"?c.gunzip(archive):archive;
    if(ref.raw_sha256)need(c.sha256(raw)===ref.raw_sha256,"raw input "+name);
    data[name]=JSON.parse(c.ascii(raw));bindings[name]={...ref};
  }
  need(cfg.inputs.domain.raw_sha256===PIN.domain_raw_sha256&&cfg.inputs.overlay.raw_sha256===PIN.overlay_raw_sha256,"literal premise pins");
  need(cfg.inputs.spectral_cold.sha256===PIN.spectral_sha256&&cfg.inputs.triangle_forward.sha256===PIN.triangle_sha256,"accepted deduction pins");
  const d=data.domain,o=data.overlay,s=data.spectral_cold,sa=data.spectral_acceptance,
    t=data.triangle_forward,ts=data.triangle_summary,ta=data.triangle_acceptance;
  need(d.status==="complete component-zero exterior-row domain preparation"&&d.complete_signature_count===480&&d.complete_possible_edge_count===68394,"domain status");
  need(d.hypothetical_graph_symmetry_assumed===false,"literal domain, no symmetry assumption");
  need(s.status==="PASS_COMPLETE_INDEPENDENT_SPECTRAL_GAP_PAIR_CENSUS"&&s.complete===true&&s.all405426_saved_integer_determinants_checked===true,"accepted spectral cold");
  need(sa.status==="ROOT_ACCEPTS_COMPLETE_INDEPENDENT_SPECTRAL_GAP_PAIR_CENSUS"&&sa.all_forward_and_cold_deduction_rows_compared===true,"spectral root acceptance");
  referenceEqual(sa.cold,cfg.inputs.spectral_cold);
  need(ts.status==="PASS_COMPLETE_INDEPENDENT_CENSUS_AND_LITERAL_ZERO_DISPOSITION"&&
    ta.status==="ROOT_ACCEPTS_COMPLETE_INDEPENDENT_CENSUS_AND_EVERY_ZERO_DISPOSITION","accepted triangle cold");
  referenceEqual(ts.report,ta.report);
  need(ta.all_exact_negative_records_and_proper_minors_compared===10830,"all supplied triangle covers accepted");
  need(t.status==="COMPLETE_EXACT_TRIANGLE_PRINCIPAL_MINOR_CENSUS","triangle forward");
  need(o.status==="COMPLETE_LITERAL_PRISM_ZEROS_AND_CORE_PAIR_CLIQUES"&&o.complete_edge_order_sha256===PIN.edge_sha256,"literal zero premise");
  const sig=d.signature_domain;need(sig.length===480,"all selectors");
  const masks=sig.map(h=>{need(h.length===3,"signature weight");eq(h,h.slice().sort((a,b)=>a-b),"signature order");
    need(new Set(h).size===3,"signature distinct");for(const i of h)integer(i,0,17);return h.reduce((v,i)=>v|(1<<i),0);});
  need(new Set(masks).size===480,"distinct literal signatures");
  const core=d.component_adjacency_rows;need(core.length===18,"18 core sites");
  const targets=d.row_targets;need(targets.length===480,"all quota rows");
  for(let a=0;a<480;a++){
    tick();need(targets[a].length===18,"18 quotas");
    for(let i=0;i<18;i++)need(targets[a][i]===2-((masks[a]>>>i)&1)-pop(core[i]&masks[a]),"literal mixed quota");
  }
  const edges=[],neighbors=Array.from({length:480},()=>[]);
  for(let a=0;a<480;a++){
    tick();
    for(let b=a+1;b<480;b++)if(pop(masks[a]&masks[b])<=1&&sig[a].every(i=>targets[b][i]>0)&&sig[b].every(i=>targets[a][i]>0)){
      edges.push([a,b]);neighbors[a].push(b);neighbors[b].push(a);
    }
  }
  need(edges.length===68394&&hash(c,JSON.stringify(edges))===PIN.edge_sha256,"complete original eligible edge order");
  eq(neighbors,d.possible_neighbor_signature_ids,"every original neighbor list");
  const g=makeGraph(sig,edges),initialMap=new Map();
  function initial(e,origin){integer(e,0,68393);if(!initialMap.has(e))initialMap.set(e,{edge_id:e,endpoints:edges[e],origins:[]});initialMap.get(e).origins.push(origin);}
  need(o.zero_rows.length===1884,"1884 literal zeros");
  const oldSet=new Set();
  for(let i=0;i<o.zero_rows.length;i++){
    const z=o.zero_rows[i];integer(z.edge_id,0,68393);
    need(!oldSet.has(z.edge_id)&&z.native_row_index===163070+i&&z.variable_index===540+z.edge_id,"literal zero native identity");
    eq(z.witness.pair,edges[z.edge_id],"literal zero endpoints");oldSet.add(z.edge_id);
    initial(z.edge_id,{kind:"literal_overlay",record_index:i,native_row_index:z.native_row_index});
  }
  const math=s.mathematical;need(math.edge_zero_rows.length===132,"132 spectral zeros");
  const spectralSeen=new Set();
  math.edge_zero_rows.forEach((r,i)=>{need(r.length===4,"spectral zero shape");const [a,b,e,old]=r;
    integer(e,0,68393);need(!spectralSeen.has(e),"distinct spectral zeros");spectralSeen.add(e);
    eq([a,b],edges[e],"spectral zero endpoints");need(typeof old==="boolean"&&old===oldSet.has(e),"old-zero disposition");
    initial(e,{kind:"spectral_zero",record_index:i});});
  need(initialMap.size===1956,"1884 plus 72 initial zeros");
  const required=math.edge_present_requires_one_common_exterior_neighbor;
  need(required.length===132&&sa.edge_present_requires_one_common_exterior_neighbor===132,"132 required triangles");
  const must=[],requiredSeen=new Set();
  required.forEach((r,i)=>{need(r.length===4,"required-edge shape");const [a,b,e,old]=r;
    integer(e,0,68393);need(!requiredSeen.has(e),"distinct required edges");requiredSeen.add(e);
    eq([a,b],edges[e],"required edge endpoints");need(typeof old==="boolean"&&old===oldSet.has(e),"required old-zero disposition");
    need((masks[a]&masks[b])===0,"n=1 adjacent pair has disjoint first signatures");
    must.push({edge_id:e,premise_index:i,endpoints:[a,b]});});
  must.sort((a,b)=>a.edge_id-b.edge_id);
  const plus=t.families.find(f=>f.family==="plus"),records=plus.nonpositive_determinant_records_with_nonnegative_proper_minors;
  need(records.length===10830&&hash(c,JSON.stringify(records))===PIN.triangle_records_sha256,"complete accepted triangle row list");
  need(ts.families.find(f=>f.family==="plus").nonpositive_records_sha256===PIN.triangle_records_sha256,"triangle cold list binding");
  const covers=new Map();
  records.forEach((r,i)=>{
    need(r.length===7,"triangle record shape");
    const [a,b,v]=r;integer(a,0,479);integer(b,a+1,479);integer(v,b+1,479);
    need(!(masks[a]&masks[b])&&!(masks[a]&masks[v])&&!(masks[b]&masks[v]),"triangle disjoint signatures");
    need(g.index[a*480+b]>=0&&g.index[a*480+v]>=0&&g.index[b*480+v]>=0,"triangle original eligible edges");
    need(BigInt(r[3])<0&&r.slice(4).every(x=>BigInt(x)>=0n),"accepted negative triangle record");
    const k=triangleKey(a,b,v);need(!covers.has(k),"distinct triangle cover");covers.set(k,i);
  });
  return {g,must,initial:Array.from(initialMap.values()).sort((a,b)=>a.edge_id-b.edge_id),covers,bindings};
}
function controls(){
  const started=Date.now(),tick=()=>{},facts={systems:0,boolean_assignments:0,admissible_assignments:0,derived_zeros_checked:0};
  function fixture(signatures,edges){
    const g=makeGraph(signatures,edges),triples=[];
    for(let a=0;a<g.n;a++)for(let b=a+1;b<g.n;b++)for(let v=b+1;v<g.n;v++)
      if(g.index[a*g.n+b]>=0&&g.index[a*g.n+v]>=0&&g.index[b*g.n+v]>=0)triples.push([a,b,v]);
    const E=edges.length;
    for(let requiredMask=0;requiredMask<(1<<E);requiredMask++)for(let coverMask=0;coverMask<(1<<triples.length);coverMask++){
      const covers=new Map();triples.forEach((t,i)=>{if(coverMask&(1<<i))covers.set(t.join(","),i);});
      const zeroEdge=(requiredMask+3*coverMask)%(E+1)-1;
      const initial=zeroEdge<0?[]:[{edge_id:zeroEdge,origins:[{kind:"synthetic"}]}];
      const must=edges.map((_,e)=>({edge_id:e,premise_index:e})).filter(t=>requiredMask&(1<<t.edge_id));
      const p=close(g,must,initial,covers,tick,E+1,emptyProgress());
      need(p.complete,"tiny closure completed");facts.systems++;
      for(let assignment=0;assignment<(1<<E);assignment++){
        facts.boolean_assignments++;
        if(zeroEdge>=0&&(assignment&(1<<zeroEdge)))continue;
        let valid=true;
        for(const [a,b,v] of triples){
          const all=(assignment&(1<<g.index[a*g.n+b]))&&(assignment&(1<<g.index[a*g.n+v]))&&(assignment&(1<<g.index[b*g.n+v]));
          if(all&&(covers.has([a,b,v].join(","))||(g.masks[a]&g.masks[b])||(g.masks[a]&g.masks[v])||(g.masks[b]&g.masks[v]))){valid=false;break;}
        }
        if(!valid)continue;
        for(const target of must)if(assignment&(1<<target.edge_id)){
          const [a,b]=g.edges[target.edge_id];let count=0;
          for(let v=0;v<g.n;v++){const l=g.index[a*g.n+v],r=g.index[b*g.n+v];if(l>=0&&r>=0&&(assignment&(1<<l))&&(assignment&(1<<r)))count++;}
          if(count!==1){valid=false;break;}
        }
        if(!valid)continue;
        facts.admissible_assignments++;
        for(const certificate of p.certificates){need(!(assignment&(1<<certificate.edge_id)),"truth-table soundness");facts.derived_zeros_checked++;}
      }
    }
  }
  const disjoint=[[0,1,2],[3,4,5],[6,7,8],[9,10,11]],full=[[0,1],[0,2],[0,3],[1,2],[1,3],[2,3]];
  fixture(disjoint,full);
  fixture([[0,1,2],[0,3,4],[5,6,7],[8,9,10]],full);
  fixture(disjoint,[[0,1],[0,2],[1,2],[1,3],[2,3]]);
  const g=makeGraph(disjoint.slice(0,3),[[0,1],[0,2],[1,2]]),must=g.edges.map((_,e)=>({edge_id:e,premise_index:e})),covers=new Map();
  const cycle=close(g,must,[],covers,tick,4,emptyProgress());need(cycle.certificates.length===0&&cycle.uneliminated_targets.length===3,"mutual support is not a zero proof");
  const chain=close(g,must,[{edge_id:2}],covers,tick,4,emptyProgress());need(chain.certificates.length===2,"sequential zero chain");
  const known0=new Map([[2,{kind:"initial",index:0}]]),known1=new Map([...known0,[0,{kind:"derived",index:0}]]);
  let rejects=0;
  function rejected(call){try{call();}catch(_){rejects++;return;}throw Error("tampered certificate accepted");}
  const copy=x=>JSON.parse(JSON.stringify(x));
  let bad=copy(chain.certificates[0]);bad.eliminated_supports=[];
  rejected(()=>verifyCertificate(g,must[0],chain.support_tables[0].supports,bad,known0,covers,tick));
  bad=copy(chain.certificates[1]);bad.eliminated_supports[0].authority.index=1;
  rejected(()=>verifyCertificate(g,must[1],chain.support_tables[1].supports,bad,known1,covers,tick));
  bad=copy(chain.certificates[0]);bad.eliminated_supports[0]={support_index:0,kind:"triangle_cover",record_index:0};
  rejected(()=>verifyCertificate(g,must[0],chain.support_tables[0].supports,bad,known0,covers,tick));
  bad=copy(chain.certificates[0]);bad.row_key[2][0][0]++;
  rejected(()=>verifyCertificate(g,must[0],chain.support_tables[0].supports,bad,known0,covers,tick));
  rejected(()=>verifyTable(g,0,[],covers,tick));
  need(rejects===5,"five altered proofs rejected");
  return {schema:"conway99.f0.spectral-triangle-support-controls.v1",status:"PASS_EXACT_TINY_SUPPORT_CONTROLS",
    ...facts,mutual_cycle_preserved:true,sequential_dependency_chain_checked:true,rejected_proof_mutations:rejects,
    actual_case_supports_enumerated:0,optimizer_calls:0,seconds:(Date.now()-started)/1000};
}
function run(configurationText,payload,codecText,sourceText){
  const started=Date.now(),c=eval(codecText),cfg=JSON.parse(configurationText),progress=emptyProgress();
  const tick=()=>{if(Date.now()-started>=LIMITS.maximum_ms)throw Error("30-second support-check deadline");};
  let loaded=null,error=null;
  try{
    need(hash(c,codecText)===PIN.codec_sha256,"frozen codec");
    need(cfg.schema==="conway99.f0.spectral-triangle-support-configuration.v1","configuration schema");
    eq(cfg.limits,LIMITS,"fixed limits");
    need(hash(c,sourceText)===cfg.source.sha256&&c.gitBlob(c.utf8(sourceText))===cfg.source.git_blob,"frozen source");
    loaded=load(cfg,payload,c,tick);progress.phase="support_universe";
    close(loaded.g,loaded.must,loaded.initial,loaded.covers,tick,LIMITS.maximum_passes,progress);
    tick();
  }catch(e){error={name:e.name,message:String(e.message)};}
  const report={schema:"conway99.f0.spectral-triangle-support-ledger.v1",
    status:progress.complete&&error===null?"PASS_COMPLETE_TARGETED_SUPPORT_FIXED_POINT":"PARTIAL_OR_UNACCEPTED_SUPPORT_CHECK",
    source:cfg.source,configuration_sha256:hash(c,configurationText),inputs:cfg.inputs,limits:LIMITS,
    complete:progress.complete&&error===null,error,
    target_count:loaded?loaded.must.length:null,targets:loaded?loaded.must:[],
    initial_zero_authorities:loaded?loaded.initial:[],...progress,complete:progress.complete&&error===null,
    every_committed_new_zero_directly_verified:true,
    row_keys:progress.certificates.map(x=>x.row_key),new_edge_zero_count:progress.certificates.length,
    scope:"Only the 132 accepted must-triangle edges; supports use original eligible disjoint signatures, accepted triangle covers and earlier certified zeros.",
    survivors_are_only_uneliminated_by_this_rule:true,whole_component_excluded:false,
    unused_inputs:["unverified eight-pattern masks","unavailable three-path inventory","other row families"],
    optimizer_calls:0,native_model_builds:0,seconds_before_serialization:(Date.now()-started)/1000};
  const text=JSON.stringify(report)+"\n";
  for(let i=0;i<text.length;i++)need(text.charCodeAt(i)<128,"ASCII report");
  const elapsed=Date.now()-started,within=elapsed<LIMITS.maximum_ms&&text.length<=LIMITS.maximum_report_bytes;
  const finalization={schema:"conway99.f0.spectral-triangle-support-finalization.v1",
    status:report.complete&&within?"PASS_COMPLETE_SUPPORT_CHECK_AND_SERIALIZATION":"UNACCEPTED_PARTIAL_OR_RESOURCE_BOUND",
    report_complete:report.complete,report_bytes:text.length,elapsed_ms:elapsed,maximum_ms:LIMITS.maximum_ms,
    maximum_report_bytes:LIMITS.maximum_report_bytes,within_declared_bounds:within,main_calls:1,automatic_retries:0,
    complete_certificates_preserved:report.new_edge_zero_count};
  return {report,text,finalization};
}
return {controls,run};
})()
