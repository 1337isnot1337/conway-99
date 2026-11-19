(() => {
"use strict";
const N=480, EC=68394, EDGE0=540, ENDPOINT0=17162, VAR0=68934, ROW0=257594;
const EDGE_SHA="411052a41a473bb7199fe277516fb60c54018dec120309622a499229579791bb";
const MODEL_SHA="4a9b24ab1a0a1758ffedab226a9c45fe7765fafc40e76e23a039c9ccd098aee2";
const LIMIT={total_ms:30000,report_bytes:16777216,main_calls:1};
const ROLES=["domain","overlay","spectral_cold","spectral_root_acceptance","native_root_acceptance","native_cold","forest_theorem","forest_review","forward_configuration","forward_report","forward_finalization","forward_terminal_binding","forward_root_gate","forward_source_review"];
const ROOT_RULE="Reverse the unique parent path from the requested root to its base component root; leave other components rooted as saved. Restrict that orientation to any vertex subset. Each retained edge is bounded by a distinct nonroot endpoint selector; unused nonroot selectors contribute nonnegative slack.";
function need(ok,message){if(!ok)throw Error(message);}
function integer(x,lo,hi){need(Number.isSafeInteger(x)&&x>=lo&&x<=hi,"integer range");return x;}
function canon(x){if(x===null||typeof x!=="object")return JSON.stringify(x);
 if(Array.isArray(x))return "["+x.map(canon).join(",")+"]";
 return "{"+Object.keys(x).sort().map(k=>JSON.stringify(k)+":"+canon(x[k])).join(",")+"}";}
function same(a,b,why){need(canon(a)===canon(b),why);}
function ref(a,b,why){for(const k of ["path","sha256","git_blob","bytes"])need(a&&b&&a[k]===b[k],why+" "+k);}
function pair(a,b){return a<b?a+","+b:b+","+a;}
function lookup(g,a,b){if(a===b)return -1;const e=g.ids.get(pair(a,b));return e===undefined?-1:e;}
function metadata(c,text){const b=c.utf8(text);return {bytes:b.length,sha256:c.sha256(b),git_blob:c.gitBlob(b)};}
function checkedText(c,text,m,why){const a=metadata(c,text);for(const k of ["bytes","sha256","git_blob"])need(a[k]===m[k],why+" "+k);return a;}
function literalGraph(d,c,tick){
 need(d.status==="complete component-zero exterior-row domain preparation"&&d.hypothetical_graph_symmetry_assumed===false,"literal domain acceptance");
 need(d.signature_domain.length===N&&d.row_targets.length===N&&d.component_adjacency_rows.length===18,"literal domain dimensions");
 const signatures=d.signature_domain.map(s=>{need(s.length===3&&new Set(s).size===3,"signature weight");
   for(const v of s)integer(v,0,17);same(s,s.slice().sort((a,b)=>a-b),"sorted signature");return new Set(s);});
 need(new Set(d.signature_domain.map(s=>s.join(","))).size===N,"distinct literal signatures");
 const core=d.component_adjacency_rows.map((v,i)=>{integer(v,0,262143);const row=new Set();
   for(let j=0;j<18;j++)if(Math.floor(v/2**j)%2===1)row.add(j);need(!row.has(i),"core diagonal");return row;});
 for(let i=0;i<18;i++)for(let j=0;j<18;j++)need(core[i].has(j)===core[j].has(i),"core symmetry");
 const quotas=Array.from({length:N},()=>[]);
 for(let a=N-1;a>=0;a--){tick();for(let i=17;i>=0;i--){
   let count=0;for(const v of core[i])if(signatures[a].has(v))count++;
   quotas[a][i]=2-Number(signatures[a].has(i))-count;}
   same(quotas[a],d.row_targets[a],"all literal quota entries");}
 const edges=[],neighbors=Array.from({length:N},()=>[]);
 // Larger endpoint and smaller endpoint both descend; canonical IDs are assigned after enumeration.
 for(let b=N-1;b>0;b--){tick();for(let a=b-1;a>=0;a--){
   let overlap=0;for(const v of signatures[a])if(signatures[b].has(v))overlap++;
   if(overlap>1)continue;
   if(Array.from(signatures[a]).some(v=>quotas[b][v]<=0)||Array.from(signatures[b]).some(v=>quotas[a][v]<=0))continue;
   edges.push([a,b]);neighbors[a].push(b);neighbors[b].push(a);
 }}
 edges.sort((a,b)=>a[0]-b[0]||a[1]-b[1]);const ids=new Map(edges.map((p,e)=>[pair(...p),e]));
 need(ids.size===EC&&edges.length===EC&&c.sha256(c.utf8(JSON.stringify(edges)))===EDGE_SHA,"complete original eligible edge identities");
 for(let a=N-1;a>=0;a--)same(neighbors[a].sort((x,y)=>x-y),d.possible_neighbor_signature_ids[a],"all original neighbor rows");
 return {n:N,edges,ids,signatures};
}
function zeroAuthorities(o,s,g){
 need(o.status==="COMPLETE_LITERAL_PRISM_ZEROS_AND_CORE_PAIR_CLIQUES"&&o.complete_edge_order_sha256===EDGE_SHA,"literal overlay authority");
 need(o.zero_rows.length===1884&&s.mathematical.edge_zero_rows.length===132,"complete zero premise lists");
 const old=new Map(),spectral=new Map();
 for(let i=o.zero_rows.length-1;i>=0;i--){const r=o.zero_rows[i],e=integer(r.edge_id,0,EC-1);
   need(!old.has(e)&&r.variable_index===EDGE0+e&&r.native_row_index===163070+i,"literal zero coordinate");
   same(r.witness.pair,g.edges[e],"literal zero endpoints");old.set(e,{index:i,row:r.native_row_index});}
 for(let i=s.mathematical.edge_zero_rows.length-1;i>=0;i--){const r=s.mathematical.edge_zero_rows[i];
   need(r.length===4,"spectral zero record");const [a,b,e,wasOld]=r;integer(e,0,EC-1);
   need(!spectral.has(e)&&typeof wasOld==="boolean"&&wasOld===old.has(e),"spectral zero origin");
   same(g.edges[e],[a,b],"spectral zero endpoints");spectral.set(e,i);}
 const all=new Set([...old.keys(),...spectral.keys()]),ledger=[];
 for(let e=0;e<EC;e++)if(all.has(e))ledger.push({edge_id:e,endpoints:g.edges[e],
   literal_origin:old.has(e)?old.get(e).index:null,literal_native_row:old.has(e)?old.get(e).row:null,
   spectral_origin:spectral.has(e)?spectral.get(e):null});
 need(all.size===1956&&Array.from(spectral.keys()).filter(e=>old.has(e)).length===60,"complete zero union and overlap");
 return {old,spectral,all,ledger};
}
function dispositions(g,a,b,z){
 const rows=Array(g.n),live=[],allowed=new Set();let original=0;
 // No signature intersection or triangle test occurs in this function.
 for(let v=g.n-1;v>=0;v--){
   const ea=lookup(g,a,v),eb=lookup(g,b,v),anchor=v===a||v===b;
   const flags=Number(anchor)+2*Number(ea<0)+4*Number(eb<0)+8*Number(z.old.has(ea))+
     16*Number(z.spectral.has(ea))+32*Number(z.old.has(eb))+64*Number(z.spectral.has(eb));
   rows[v]=[v,ea,eb,flags];
   if(anchor)continue;
   if(ea>=0&&eb>=0)original++;
   if(ea>=0&&!z.all.has(ea))allowed.add(ea);
   if(eb>=0&&!z.all.has(eb))allowed.add(eb);
   if(flags===0)live.push([v,ea,eb]);
 }
 live.sort((a,b)=>a[0]-b[0]);return {rows,live,original,allowed:Array.from(allowed).sort((a,b)=>a-b)};
}
function verifyForestCertificate(cert,n,edges,allowed){
 const keys=["status","vertices","complete_allowed_original_edge_ids","base_component_roots","parent_endpoint_receipts","receipt_fields","arbitrary_root_rule","other_rows_or_triangle_assumptions_used"];
 same(Object.keys(cert).sort(),keys.sort(),"forest certificate fields");
 need(cert.status==="ENDPOINT_FOREST_IMPLIES_EVERY_ROOT_OMITTED_SUBSET_ROW"&&cert.vertices===n,"skip certificate scope");
 same(cert.complete_allowed_original_edge_ids,allowed,"complete one-sided allowed edge set");
 same(cert.receipt_fields,["child_selector","parent_selector","original_edge_id","native_activation_row"],"endpoint receipt fields");
 need(cert.arbitrary_root_rule===ROOT_RULE&&cert.other_rows_or_triangle_assumptions_used===false,"reroot and restriction theorem");
 const representative=Array.from({length:n},(_,i)=>i),size=Array(n).fill(1);
 function find(a){while(representative[a]!==a){representative[a]=representative[representative[a]];a=representative[a];}return a;}
 for(const e of allowed){integer(e,0,edges.length-1);const [a,b]=edges[e];let x=find(a),y=find(b);
   need(x!==y,"allowed two-star graph must be acyclic");if(size[x]<size[y])[x,y]=[y,x];representative[y]=x;size[x]+=size[y];}
 const minima=new Map();for(let v=0;v<n;v++){const r=find(v);minima.set(r,Math.min(minima.has(r)?minima.get(r):n,v));}
 const roots=Array.from(minima.values()).sort((a,b)=>a-b),rootSet=new Set(roots);
 same(cert.base_component_roots,roots,"all component minima including isolated selectors");
 const byChild=new Map(),used=new Set(),allowedSet=new Set(allowed);
 need(cert.parent_endpoint_receipts.length===allowed.length,"one endpoint receipt per allowed edge");
 for(const r of cert.parent_endpoint_receipts){need(r.length===4,"endpoint receipt width");const [child,parent,e,native]=r;
   integer(child,0,n-1);integer(parent,0,n-1);need(child!==parent&&!rootSet.has(child)&&!byChild.has(child),"distinct nonroot charged endpoints");
   need(allowedSet.has(e)&&!used.has(e),"every allowed edge appears once");const p=edges[e];
   need((p[0]===child&&p[1]===parent)||(p[1]===child&&p[0]===parent),"actual endpoint orientation");
   const side=p[0]===child?0:1;need(native===ENDPOINT0+2*e+side,"original endpoint activation row");
   byChild.set(child,parent);used.add(e);
 }
 need(roots.length+byChild.size===n,"complete component orientation");
 for(let v=0;v<n;v++){let w=v;const path=new Set();while(byChild.has(w)){
   need(!path.has(w),"no directed parent cycle");path.add(w);w=byChild.get(w);}
   need(w===minima.get(find(v)),"every parent path reaches its original component root");}
 return {components:roots.length,edges:allowed.length};
}
function rowKey(lo,hi,terms){
 integer(lo,-100000,100000);integer(hi,lo,100000);const coefficients=Object.create(null);
 for(const [j,a]of terms){integer(j,0,100000);integer(a,-1,1);need(a!==0&&coefficients[j]===undefined,"distinct nonzero row columns");coefficients[j]=a;}
 return [lo,hi,Object.keys(coefficients).map(Number).sort((a,b)=>a-b).map(j=>[j,coefficients[j]])];
}
function indexedBlock(a,b,live,varStart,rowStart,origin){
 const m=live.length,Z=varStart+m,variables=Array(m+1),wedges=Array(m),rows=Array(4*m+3),origins=Array(4*m+3);
 for(let i=m-1;i>=0;i--){const [v,ea,eb]=live[i],z=varStart+i,y=EDGE0+ea,w=EDGE0+eb;
   wedges[i]=[v,ea,eb,z];variables[i]=[z,"cap1_wedge_"+a+"_"+b+"_"+v,[0,1],origin,v];
   rows[3*i]=rowKey(-2,0,[[v,-1],[z,-1],[y,1],[w,1]]);
   rows[3*i+1]=rowKey(-1,0,[[y,-1],[z,1]]);rows[3*i+2]=rowKey(-1,0,[[w,-1],[z,1]]);
   origins[3*i]=[origin,0,v];origins[3*i+1]=[origin,1,v];origins[3*i+2]=[origin,2,v];
   rows[3*m+3+i]=rowKey(-3,0,[[a,-1],[b,-1],[z,-1],[y,1],[w,1],[Z,1]]);
   origins[3*m+3+i]=[origin,6,v];
 }
 variables[m]=[Z,"cap1_total_"+a+"_"+b,[0,1],origin,-1];
 rows[3*m]=rowKey(0,0,[[Z,1],...Array.from({length:m},(_,i)=>[varStart+i,-1])]);
 rows[3*m+1]=rowKey(-1,0,[[a,-1],[Z,1]]);rows[3*m+2]=rowKey(-1,0,[[b,-1],[Z,1]]);
 for(let k=0;k<3;k++)origins[3*m+k]=[origin,3+k,-1];
 need(rows.reduce((s,r)=>s+r[2].length,0)===15*m+5,"exact block term count");
 return {variables,wedges,rows,origins,aggregate:Z,rowStart};
}
function reconstruct(g,z,s,forward,tick){
 const prem=s.mathematical.overlap_zero_selected_pair_common_exterior_neighbor_cap_one;
 need(prem.length===48&&forward.pairs.length===48,"complete 48-pair family");const prepared=Array(48),seen=new Set();
 for(let i=47;i>=0;i--){tick();const p=prem[i];need(p.length===3,"cap-one premise width");const [a,b,e]=p;
   integer(a,0,N-1);integer(b,a+1,N-1);integer(e,0,EC-1);need(!seen.has(pair(a,b)),"distinct cap-one anchor pair");seen.add(pair(a,b));
   same(g.edges[e],[a,b],"original central edge identity");if(i>0)need(prem[i-1][2]<e,"original premise order");
   for(const v of g.signatures[a])need(!g.signatures[b].has(v),"accepted overlap-zero anchors only");
   prepared[i]={a,b,e,detail:dispositions(g,a,b,z)};
 }
 const variableOffsets=[VAR0],rowOffsets=[ROW0];
 for(let i=0;i<48;i++){const m=prepared[i].detail.live.length;
   variableOffsets.push(variableOffsets[i]+(m>1?m+1:0));rowOffsets.push(rowOffsets[i]+(m>1?4*m+3:0));}
 const variables=Array(variableOffsets[48]-VAR0),rows=Array(rowOffsets[48]-ROW0),origins=Array(rows.length),pairs=Array(48);
 const zeroByEdge=new Map(z.ledger.map(r=>[r.edge_id,r]));let skipped=0;
 for(let i=47;i>=0;i--){tick();const {a,b,e,detail:d}=prepared[i],m=d.live.length;
   const p={origin_index:i,original_spectral_cold_record:prem[i].slice(),anchor_pair:[a,b],central_edge_zero_origins:zeroByEdge.get(e)||null,
     dispositions:d.rows,original_common_candidates:d.original,live_common_candidates:m,live_candidates:d.live,assumption_on_central_edge_value:null};
   if(m<=1){
     skipped++;need(forward.pairs[i].endpoint_forest_certificate,"required complete endpoint proof for skip");
     verifyForestCertificate(forward.pairs[i].endpoint_forest_certificate,g.n,g.edges,d.allowed);
     p.status="SKIPPED_ONLY_BY_ENDPOINT_FOREST_IMPLICATION";p.endpoint_forest_certificate=forward.pairs[i].endpoint_forest_certificate;
     p.appended_variables=0;p.appended_rows=0;
   }else{
     const block=indexedBlock(a,b,d.live,variableOffsets[i],rowOffsets[i],i);
     p.status="PROPOSED_COMPLETE_FOREST_EXTENSION";p.wedges=block.wedges;p.aggregate_variable=block.aggregate;
     p.native_row_start=rowOffsets[i];p.appended_variables=m+1;p.appended_rows=4*m+3;
     for(let j=0;j<block.variables.length;j++)variables[variableOffsets[i]-VAR0+j]=block.variables[j];
     for(let j=0;j<block.rows.length;j++){rows[rowOffsets[i]-ROW0+j]=block.rows[j];origins[rowOffsets[i]-ROW0+j]=block.origins[j];}
   }
   pairs[i]=p;
 }
 const counts={accepted_pairs:48,candidate_dispositions:48*N,accepted_zero_union:1956,extended_pairs:48-skipped,endpoint_forest_skipped_pairs:skipped,
   new_variables:variables.length,new_rows:rows.length,new_terms:rows.reduce((n,r)=>n+r[2].length,0),
   proposed_total_variables:VAR0+variables.length,proposed_total_rows:ROW0+rows.length};
 const derived={zero_union_ledger:z.ledger,pairs,proposed_native_variables:variables,proposed_native_row_keys:rows,row_origins:origins,counts};
 same(derived,forward,"whole reconstructed artifact, all records, variables, rows and origins");
 return derived;
}
function readInputs(c,cfg,payload,tick){
 same(Object.keys(cfg.inputs).sort(),ROLES.slice().sort(),"exact configured input role list");
 same(Object.keys(payload).sort(),ROLES.slice().sort(),"exact supplied input role list");
 const out={};
 for(const role of ROLES){tick();const m=cfg.inputs[role],text=payload[role];need(typeof text==="string","input text");
   const b=m.encoding==="base64_gzip"?c.base64(text):c.utf8(text);
   need(b.length===m.bytes&&c.sha256(b)===m.sha256&&c.gitBlob(b)===m.git_blob,"frozen input "+role);
   let raw=text;if(m.encoding==="base64_gzip"){const decoded=c.gunzip(b);need(c.sha256(decoded)===m.raw_sha256,"raw gzip "+role);raw=c.ascii(decoded);}
   else need(m.encoding==="utf-8","explicit input encoding");
   out[role]=m.kind==="text"?raw:JSON.parse(raw);
 }
 return out;
}
function authorities(data,cfg){
 const s=data.spectral_cold,sr=data.spectral_root_acceptance,nr=data.native_root_acceptance,nc=data.native_cold;
 need(s.status==="PASS_COMPLETE_INDEPENDENT_SPECTRAL_GAP_PAIR_CENSUS"&&s.complete&&s.all114960_saved_pair_records_checked&&s.all405426_saved_integer_determinants_checked,"complete accepted spectral scope");
 need(s.mathematical.state_mask_histogram["0:1:3:3"]===48,"complete spectral cap-one class");
 need(sr.status==="ROOT_ACCEPTS_COMPLETE_INDEPENDENT_SPECTRAL_GAP_PAIR_CENSUS"&&sr.extra_overlap_zero_common_neighbor_cap_one===48,"spectral root acceptance");
 ref(sr.cold,cfg.inputs.spectral_cold,"accepted spectral report");
 need(s.input_bindings.archives.domain.archive_sha256===cfg.inputs.domain.sha256&&s.input_bindings.archives.overlay.archive_sha256===cfg.inputs.overlay.sha256,"same literal premises");
 need(nr.status==="ROOT_ACCEPTS_COMPLETE_STRENGTHENED_NATIVE_MODEL_AND_INDEPENDENT_COLD"&&nc.status==="PASS_INDEPENDENT_COMPLETE_STRENGTHENED_LITERAL_NATIVE_APPEND"&&nc.complete_parent_bytes_checked,"accepted complete native prefix");
 ref(nr.independent_cold,cfg.inputs.native_cold,"native parent acceptance");
 for(const r of [nr,nc])need(r.variables===VAR0&&r.rows===ROW0&&r.model_raw_sha256===MODEL_SHA&&r.family_counts.spectral_edge_zero===72,"native dimensions and all accepted added zeros");
 need(data.forest_review.status==="PASS_COMPLETE_CONDITIONAL_POLYHEDRAL_THEOREM","forest theorem accepted");ref(data.forest_review.theorem,cfg.inputs.forest_theorem,"exact forest theorem");
 const fc=data.forward_configuration,f=data.forward_report,fin=data.forward_finalization,b=data.forward_terminal_binding,gate=data.forward_root_gate,peer=data.forward_source_review;
 need(f.schema==="conway99.f0.cap-one-forest-support-inventory.v1"&&f.status==="PASS_COMPLETE_48_PAIR_FOREST_SUPPORT_AND_LITERAL_ROW_INVENTORY"&&f.complete&&f.error===null,"forward complete terminal");
 need(f.configuration_sha256===cfg.inputs.forward_configuration.sha256&&f.original_model_raw_sha256===MODEL_SHA,"forward configuration/model");
 ref(f.source,fc.source,"forward producer source binding");ref(fc.source,cfg.forward_source,"frozen producer, not executed");
 same(f.inputs,fc.inputs,"forward complete premise map");same(f.limits,fc.limits,"forward limits");
 for(const role of Object.keys(fc.inputs))ref(fc.inputs[role],cfg.inputs[role],"same accepted input "+role);
 need(fin.schema==="conway99.f0.cap-one-forest-support-finalization.v1"&&fin.status==="PASS_COMPLETE_FOREST_INVENTORY_AND_SERIALIZATION"&&fin.complete&&fin.within_declared_bounds,"forward finalization");
 need(fin.main_calls===1&&fin.automatic_retries===0&&fin.report_bytes===cfg.inputs.forward_report.bytes&&fin.elapsed_ms<fc.limits.total_ms&&fin.inventory_phase_ms<fc.limits.inventory_ms,"forward finite bounds");
 need(b.status==="PASS_ONE_COMPLETE_FOREST_INVENTORY_WITH_PRESERVED_TERMINAL_BYTES"&&b.actual_main_calls===1&&b.automatic_retries===0&&b.exact_report_and_finalization_texts_preserved_before_publication_hashing,"terminal binding");
 for(const [field,role]of [["report","forward_report"],["finalization","forward_finalization"],["configuration","forward_configuration"],["root_gate","forward_root_gate"],["independent_source_review","forward_source_review"]])ref(b[field],cfg.inputs[role],"forward terminal "+field);
 ref(b.source,fc.source,"terminal producer");same(b.counts,f.derived.counts,"terminal counts");
 same(b.support_sizes,f.derived.pairs.map(p=>p.live_common_candidates),"terminal support sizes");
 need(gate.status==="AUTHORIZE_ONE_COMPLETE_48_PAIR_FOREST_SUPPORT_INVENTORY"&&gate.maximum_main_calls===1,"inventory authority");
 ref(gate.source,fc.source,"gated producer");ref(gate.configuration,cfg.inputs.forward_configuration,"gated configuration");ref(gate.independent_source_review,cfg.inputs.forward_source_review,"gated review");
 same(gate.inputs,fc.inputs,"gate premise list");same(gate.limits,fc.limits,"gated limits");
 need(peer.status==="PASS_COMPLETE_LITERAL_SUPPORT_AND_FOREST_ENCODING_SOURCE_REVIEW"&&peer.complete_257_source_lines_read,"forward source review");
 ref(peer.source,fc.source,"reviewed producer");ref(peer.configuration,cfg.inputs.forward_configuration,"reviewed configuration");
 need(f.native_model_built===false&&f.existing_model_changed===false&&f.optimizer_calls===0&&f.graph_constructed===false&&f.whole_component_excluded===false,"inventory-only forward scope");
 const encoding={disposition_fields:["candidate","original_edge_ac_or_minus1","original_edge_bc_or_minus1","reason_bitmask"],
   reason_bits:{anchor:1,edge_ac_unavailable:2,edge_bc_unavailable:4,edge_ac_literal_zero:8,edge_ac_spectral_zero:16,edge_bc_literal_zero:32,edge_bc_spectral_zero:64},
   variable_fields:["native_index","name","domain","original_cap_one_index","candidate_or_minus1_for_total"],row_key_fields:["lower","upper","sorted_variable_coefficient_pairs"],
   row_origin_fields:["original_cap_one_index","kind","candidate_or_minus1"],row_kinds:{wedge_lower:0,wedge_upper_ac:1,wedge_upper_bc:2,total_definition:3,total_anchor_a:4,total_anchor_b:5,candidate_root:6},
   original_variables_retained:VAR0,original_rows_retained:ROW0,complete_support_uses_only_original_eligibility_and_accepted_zero_union:true,
   signature_disjointness_or_triangle_cover_pruning:false,assumption_on_anchor_edge_value:false,future_model_requires_separate_literal_completeness_check_and_full_native_replay:true};
 same(f.encoding,encoding,"complete original encoding schema");
}

function controls(){
 const start=Date.now();let systems=0,pointCases=0,booleanCases=0,forestCases=0,rerootChecks=0,rejections=0;
 function reject(fn){let failed=false;try{fn();}catch(_){failed=true;}need(failed,"control mutation accepted");rejections++;}
 function graph(n,edges){const e=edges.map(p=>p.slice()).sort((a,b)=>a[0]-b[0]||a[1]-b[1]);return {n,edges:e,ids:new Map(e.map((p,i)=>[pair(...p),i]))};}
 // All five side-edge states: unavailable, live, literal-zero, spectral-zero, both zeros.
 for(let code=0;code<625;code++)for(let central=0;central<3;central++){
   let k=code;const state=[];for(let i=0;i<4;i++){state.push(k%5);k=Math.floor(k/5);}
   const side=[[0,2],[0,3],[1,2],[1,3]],edges=central?[[0,1]]:[];
   for(let i=0;i<4;i++)if(state[i])edges.push(side[i]);const g=graph(4,edges),old=new Map(),spectral=new Map();
   for(let i=0;i<4;i++)if(state[i]>1){const e=lookup(g,...side[i]);if(state[i]===2||state[i]===4)old.set(e,true);if(state[i]>=3)spectral.set(e,true);}
   if(central===2){old.set(lookup(g,0,1),true);spectral.set(lookup(g,0,1),true);}
   const z={old,spectral,all:new Set([...old.keys(),...spectral.keys()])},actual=dispositions(g,0,1,z),oracle=[],live=[],allowed=new Set();let original=0;
   for(let v=0;v<4;v++){
     const ea=g.edges.findIndex(p=>p.includes(0)&&p.includes(v)&&v!==0),eb=g.edges.findIndex(p=>p.includes(1)&&p.includes(v)&&v!==1);
     let mask=(v===0||v===1)?1:0;if(ea<0)mask|=2;if(eb<0)mask|=4;if(old.has(ea))mask|=8;if(spectral.has(ea))mask|=16;if(old.has(eb))mask|=32;if(spectral.has(eb))mask|=64;
     oracle.push([v,ea,eb,mask]);if(v<2)continue;if(ea>=0&&eb>=0)original++;
     if(ea>=0&&!z.all.has(ea))allowed.add(ea);if(eb>=0&&!z.all.has(eb))allowed.add(eb);
     if(ea>=0&&eb>=0&&!z.all.has(ea)&&!z.all.has(eb))live.push([v,ea,eb]);
   }
   same(actual,{rows:oracle,live,original,allowed:Array.from(allowed).sort((a,b)=>a-b)},"exhaustive literal dispositions");systems++;
 }
 const overlapGraph=graph(3,[[0,1],[0,2],[1,2]]);overlapGraph.signatures=[new Set([0,1,2]),new Set([3,4,5]),new Set([0,6,7])];
 const oz={old:new Map([[lookup(overlapGraph,0,1),true]]),spectral:new Map(),all:new Set([lookup(overlapGraph,0,1)])};
 need(dispositions(overlapGraph,0,1,oz).live.length===1,"overlap candidate and zero central edge do not remove a valid wedge");
 function cert(n,edges,roots,parentEdges){
   return {status:"ENDPOINT_FOREST_IMPLIES_EVERY_ROOT_OMITTED_SUBSET_ROW",vertices:n,
     complete_allowed_original_edge_ids:edges.map((_,i)=>i),base_component_roots:roots,parent_endpoint_receipts:parentEdges.map(([child,parent,e])=>[child,parent,e,ENDPOINT0+2*e+(edges[e][0]===child?0:1)]),
     receipt_fields:["child_selector","parent_selector","original_edge_id","native_activation_row"],arbitrary_root_rule:ROOT_RULE,other_rows_or_triangle_assumptions_used:false};
 }
 const forests=[
   {n:4,edges:[],roots:[0,1,2,3],parents:[]},
   {n:7,edges:[[0,2],[0,3],[1,4],[1,5]],roots:[0,1,6],parents:[[2,0,0],[3,0,1],[4,1,2],[5,1,3]]},
   {n:7,edges:[[0,2],[0,3],[0,4],[1,4],[1,5]],roots:[0,6],parents:[[2,0,0],[3,0,1],[4,0,2],[1,4,3],[5,1,4]]}
 ];
 for(const f of forests){
   const receipt=cert(f.n,f.edges,f.roots,f.parents),allowed=f.edges.map((_,i)=>i);
   verifyForestCertificate(receipt,f.n,f.edges,allowed);forestCases++;
   // Verify every reroot and subset restriction as an injective endpoint assignment.
   for(let root=0;root<f.n;root++){
     const parent=new Map(receipt.parent_endpoint_receipts.map(r=>[r[0],{parent:r[1],edge:r[2]}]));
     let v=root,previous=null;while(parent.has(v)){const old=parent.get(v);if(previous===null)parent.delete(v);else parent.set(v,previous);previous={parent:v,edge:old.edge};v=old.parent;}if(previous!==null)parent.set(v,previous);
     for(let subset=0;subset<2**f.n;subset++){
       const used=new Set();let activeEdges=0;
       for(let e=0;e<f.edges.length;e++){const [a,b]=f.edges[e];if(!(subset>>a&1)||!(subset>>b&1))continue;activeEdges++;
         const child=parent.has(a)&&parent.get(a).edge===e?a:b;need(parent.has(child)&&parent.get(child).edge===e&&child!==root&&!used.has(child),"rerooted subset endpoint injection");used.add(child);}
       need(used.size===activeEdges,"all retained edges oriented");rerootChecks++;
     }
   }
   if(f.edges.length){const clone=()=>JSON.parse(JSON.stringify(receipt));
     let bad=clone();bad.parent_endpoint_receipts[0][3]++;reject(()=>verifyForestCertificate(bad,f.n,f.edges,allowed));
     bad=clone();bad.parent_endpoint_receipts.pop();reject(()=>verifyForestCertificate(bad,f.n,f.edges,allowed));
     bad=clone();bad.base_component_roots.pop();reject(()=>verifyForestCertificate(bad,f.n,f.edges,allowed));
     bad=clone();bad.complete_allowed_original_edge_ids.pop();reject(()=>verifyForestCertificate(bad,f.n,f.edges,allowed));
     bad=clone();bad.parent_endpoint_receipts[1][0]=bad.parent_endpoint_receipts[0][0];reject(()=>verifyForestCertificate(bad,f.n,f.edges,allowed));
   }
 }
 const cycle=[[0,2],[0,3],[1,2],[1,3]];
 reject(()=>verifyForestCertificate(cert(4,cycle,[0],[[2,0,0],[3,0,1],[1,2,2]]),4,cycle,[0,1,2,3]));
 function allForestRows(A,B,t,u,v){
   const values=[A,B,...t],m=t.length;
   for(let subset=1;subset<2**(m+2);subset++){
     let X=0,E=0;for(let j=0;j<m+2;j++)if(subset>>j&1)X+=values[j];
     for(let i=0;i<m;i++)if(subset>>(i+2)&1){if(subset&1)E+=u[i];if(subset&2)E+=v[i];}
     for(let r=0;r<m+2;r++)if((subset>>r&1)&&E>X-values[r])return false;
   }
   return true;
 }
 for(const D of [1,2])for(let m=0;m<=2;m++){
   const live=Array.from({length:m},(_,i)=>[i+2,i,m+i]),block=indexedBlock(0,1,live,70123,300123,7);
   for(let code=0;code<(D+1)**(2+3*m);code++){
     let k=code;const vals=[];for(let j=0;j<2+3*m;j++){vals.push(k%(D+1));k=Math.floor(k/(D+1));}
     const [A,B]=vals,t=[],u=[],v=[];let activated=true;
     for(let i=0;i<m;i++){t[i]=vals[2+3*i];u[i]=vals[3+3*i];v[i]=vals[4+3*i];if(u[i]>A||v[i]>B||u[i]>t[i]||v[i]>t[i])activated=false;}
     if(!activated)continue;pointCases++;if(D===1)booleanCases++;
     const values=new Map([[0,A],[1,B]]);let Z=0;
     for(let i=0;i<m;i++){const z=Math.max(0,u[i]+v[i]-t[i]);Z+=z;values.set(i+2,t[i]);values.set(EDGE0+i,u[i]);values.set(EDGE0+m+i,v[i]);values.set(70123+i,z);}
     values.set(block.aggregate,Z);
     const extended=block.variables.every(r=>values.get(r[0])>=0&&values.get(r[0])<=D)&&block.rows.every(([lo,hi,terms])=>{
       const value=terms.reduce((s,[j,a])=>s+a*values.get(j),0);return lo*D<=value&&value<=hi*D;});
     const forest=allForestRows(A,B,t,u,v);need(extended===forest,"all-subset/root forest projection on activated rational grid");
     if(m<=1)need(forest,"endpoint-only skip family");if(D===1)for(let i=0;i<m;i++)need(values.get(70123+i)===Number(u[i]===1&&v[i]===1),"Boolean wedge AND");
   }
 }
 const block=indexedBlock(11,19,[[31,7,20],[44,8,23]],70201,300111,4),frozen=JSON.parse(JSON.stringify(block));
 const mutate=[
   x=>{x.rows[0][0]++;},x=>{x.rows[0][2][0][1]*=-1;},x=>{x.rows[2][2][0][0]++;},
   x=>{x.origins[1][1]++;},x=>{x.variables[0][0]++;},x=>{x.wedges[0][3]++;},x=>{x.rowStart++;}
 ];
 for(const change of mutate){const x=JSON.parse(JSON.stringify(frozen));change(x);reject(()=>same(x,block,"altered row/variable/origin/offset"));}
 return {schema:"conway99.f0.cap-one-forest-support-independent-literal-controls.v1",status:"PASS_TINY_INDEPENDENT_LITERAL_AND_FOREST_CONTROLS",
   exhaustive_side_state_and_central_cases:systems,overlap_candidate_with_zero_central_control:true,
   accepted_small_forests:forestCases,all_reroot_subset_injections:rerootChecks,activated_rational_grid_points:pointCases,
   activated_boolean_points:booleanCases,deliberate_mutations_rejected:rejections,seconds:(Date.now()-start)/1000,
   actual_case_reconstructions:0,producer_calls:0,native_calls:0};
}
function run(configurationText,payload,codecText,sourceText){
 const started=Date.now();let report={schema:"conway99.f0.cap-one-forest-support-independent-literal-replay.v1",status:"UNRESOLVED",complete:false,progress:"START",error:null};
 let c,configurationHash=null;
 const tick=()=>need(Date.now()-started<LIMIT.total_ms,"declared total deadline");
 try{
   c=eval(codecText);const cfg=JSON.parse(configurationText);checkedText(c,codecText,cfg.codec,"exact codec");checkedText(c,sourceText,cfg.source,"independent checker source");
   same(cfg.limits,LIMIT,"fixed complete replay limits");need(cfg.maximum_main_calls===1&&cfg.automatic_retries===0,"one-call preparation");
   configurationHash=c.sha256(c.utf8(configurationText));report.source=cfg.source;report.configuration_sha256=configurationHash;report.inputs=cfg.inputs;report.limits=LIMIT;
   const data=readInputs(c,cfg,payload,tick);report.progress="ALL_INPUTS_BOUND";authorities(data,cfg);tick();
   const g=literalGraph(data.domain,c,tick);report.progress="ALL_ORIGINAL_EDGES_RECONSTRUCTED";
   const z=zeroAuthorities(data.overlay,data.spectral_cold,g);report.progress="ALL_ZERO_AUTHORITIES_RECONSTRUCTED";tick();
   const d=reconstruct(g,z,data.spectral_cold,data.forward_report.derived,tick);tick();
   report.counts=d.counts;report.support_sizes=d.pairs.map(p=>p.live_common_candidates);
   report.complete_original_edges=EC;report.complete_original_neighbor_rows=N;report.zero_union=1956;
   report.support_wedges=d.pairs.reduce((n,p)=>n+p.live_common_candidates,0);
   report.normalized={canonical_format:"JSON with recursively sorted object keys; array order retained; UTF-8; no newline",
     whole_derived_canonical_sha256:c.sha256(c.utf8(canon(d))),
     pairs_canonical_sha256:c.sha256(c.utf8(canon(d.pairs))),
     zero_union_canonical_sha256:c.sha256(c.utf8(canon(d.zero_union_ledger))),
     native_row_keys_json_sha256:c.sha256(c.utf8(JSON.stringify(d.proposed_native_row_keys))),
     native_variables_json_sha256:c.sha256(c.utf8(JSON.stringify(d.proposed_native_variables))),
     row_origins_json_sha256:c.sha256(c.utf8(JSON.stringify(d.row_origins)))};
   tick();report.forward_report_sha256=cfg.inputs.forward_report.sha256;report.forward_finalization_sha256=cfg.inputs.forward_finalization.sha256;
   report.original_model_raw_sha256=MODEL_SHA;report.original_variables=VAR0;report.original_rows=ROW0;
   report.every_candidate_disposition_checked=true;report.every_accepted_zero_origin_checked=true;report.all_original_eligible_edge_ids_rebuilt=true;
   report.every_skip_orientation_checked=true;report.all_native_variable_names_domains_offsets_checked=true;report.all_native_row_keys_offsets_and_origins_checked=true;
   report.whole_derived_artifact_compared=true;report.no_candidate_disjointness_or_triangle_filter=true;report.anchor_edge_not_fixed=true;
   report.producer_imports=0;report.producer_calls=0;report.native_model_builds=0;report.optimizer_calls=0;report.current_model_changed=false;
   report.graph_constructed=false;report.whole_component_excluded=false;report.full_independent_native_replay_still_required=true;
   report.progress="COMPLETE_WHOLE_ARTIFACT_COMPARISON";report.status="PASS_COMPLETE_INDEPENDENT_LITERAL_FOREST_SUPPORT_AND_ROWS";report.complete=true;
 }catch(error){report.status="UNRESOLVED_INDEPENDENT_LITERAL_REPLAY";report.complete=false;report.error=String(error&&error.message||error);}
 report.seconds_before_serialization=(Date.now()-started)/1000;
 let reportText=JSON.stringify(report)+"\n";let reportBytes=reportText.length,ascii=true;
 for(let i=0;i<reportText.length;i++)if(reportText.charCodeAt(i)>127){ascii=false;break;}
 let elapsed=Date.now()-started;
 const finalization={schema:"conway99.f0.cap-one-forest-support-independent-literal-finalization.v1",
   status:report.complete&&ascii&&elapsed<LIMIT.total_ms&&reportBytes<=LIMIT.report_bytes?"PASS_COMPLETE_LITERAL_FOREST_REPLAY_AND_SERIALIZATION":"UNRESOLVED_LITERAL_FOREST_REPLAY_OR_BOUNDS",
   complete:report.complete,elapsed_ms:elapsed,report_bytes:reportBytes,ascii_serialization:ascii,
   within_declared_bounds:ascii&&elapsed<LIMIT.total_ms&&reportBytes<=LIMIT.report_bytes,main_calls:1,automatic_retries:0,publication_hashes_outside_main:true};
 let finalizationText=JSON.stringify(finalization)+"\n";
 // Check through serialization of both texts; any crossing remains an unresolved terminal.
 elapsed=Date.now()-started;
 if(elapsed>=LIMIT.total_ms){finalization.status="UNRESOLVED_LITERAL_FOREST_REPLAY_OR_BOUNDS";finalization.within_declared_bounds=false;}
 finalization.elapsed_ms=elapsed;finalizationText=JSON.stringify(finalization)+"\n";
 return {report,reportText,finalization,finalizationText};
}
return {controls,run};
})()
