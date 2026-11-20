(() => {
"use strict";
const LIMIT_MS = 30000, REPORT_LIMIT = 65536;
const ACCEPTED = ["domain","kernels","kernel_audit","spectral_theorem","spectral_review",
  "indicator","triangle_literal_root","combined_configuration","combined_root","method"];
const FORWARD = ["forward_configuration","forward_report","forward_finalization",
  "forward_owner","forward_gate","forward_review","forward_source"];
const ALL_INPUTS = ACCEPTED.concat(FORWARD);
const SUBSETS = [[0],[1],[2],[0,1],[0,2],[1,2],[0,1,2]];
function requireTrue(ok, label) { if (!ok) throw Error(label); }
function integer(x, low, high, label) {
  requireTrue(Number.isSafeInteger(x) && x >= low && x <= high, "integer " + label);
  return x;
}
function ordered(value) {
  if (Array.isArray(value)) return value.map(ordered);
  if (value !== null && typeof value === "object")
    return Object.fromEntries(Object.keys(value).sort().map(k => [k,ordered(value[k])]));
  return value;
}
function equal(a,b,label) {
  requireTrue(JSON.stringify(ordered(a)) === JSON.stringify(ordered(b)), label);
}
function reference(a,b,label) {
  requireTrue(a && b && a.path === b.path && a.sha256 === b.sha256, "reference " + label);
  if (a.bytes !== undefined && b.bytes !== undefined) requireTrue(a.bytes === b.bytes, "bytes " + label);
  if (a.git_blob && b.git_blob) requireTrue(a.git_blob === b.git_blob, "Git " + label);
}
function determinant(matrix, selected) {
  let terms = [{columns:[],negative:false}];
  for (const column of selected) {
    const next = [];
    for (const term of terms) for (let position=0;position<=term.columns.length;position++) {
      const columns = term.columns.slice();
      columns.splice(position,0,column);
      next.push({columns,negative:term.negative !== ((term.columns.length-position)%2 === 1)});
    }
    terms = next;
  }
  let answer = 0n;
  for (const term of terms) {
    let product = 1n;
    for (let row=0;row<selected.length;row++) product *= matrix[selected[row]][term.columns[row]];
    answer += term.negative ? -product : product;
  }
  return answer;
}
function controls(tick) {
  const large = 9007199254740993n;
  const fixtures = [
    [[[2n,0n,0n],[0n,3n,0n],[0n,0n,5n]],[2n,3n,5n,6n,10n,15n,30n]],
    [[[1n,1n,1n],[1n,1n,1n],[1n,1n,1n]],[1n,1n,1n,0n,0n,0n,0n]],
    [[[1n,-1n,-1n],[-1n,1n,-1n],[-1n,-1n,1n]],[1n,1n,1n,0n,0n,0n,-4n]],
    [[[-1n,0n,0n],[0n,2n,0n],[0n,0n,3n]],[-1n,2n,3n,-2n,-3n,6n,-6n]],
    [[[1n,2n,0n],[2n,1n,0n],[0n,0n,1n]],[1n,1n,1n,-3n,1n,1n,-3n]],
    [[[3n,1n,2n],[1n,4n,0n],[2n,0n,5n]],[3n,4n,5n,11n,11n,20n,39n]],
    [[[large,0n,0n],[0n,large+1n,0n],[0n,0n,large+2n]],
      [large,large+1n,large+2n,large*(large+1n),large*(large+2n),
       (large+1n)*(large+2n),large*(large+1n)*(large+2n)]]
  ];
  const relabelings = [[0,1,2],[0,2,1],[1,0,2],[1,2,0],[2,0,1],[2,1,0]];
  let minorChecks=0, relabelingChecks=0;
  for (const [matrix, expected] of fixtures) {
    for (let j=0;j<SUBSETS.length;j++) {
      requireTrue(determinant(matrix,SUBSETS[j]) === expected[j], "known exact principal minor");
      minorChecks++;
    }
    for (const permutation of relabelings) {
      const permuted = permutation.map(i=>permutation.map(j=>matrix[i][j]));
      requireTrue(determinant(permuted,[0,1,2]) === expected[6], "determinant relabeling");
      relabelingChecks++;
    }
    tick("tiny controls");
  }
  requireTrue(fixtures[2][1].slice(0,6).every(x=>x>=0n) && fixtures[2][1][6]<0n,
    "proper-minor versus determinant failure");
  return {status:"PASS_INDEPENDENT_LITERAL_PERMUTATION_MINOR_CONTROLS",
    exact_fixtures:fixtures.length,known_minor_comparisons:minorChecks,
    determinant_relabeling_comparisons:relabelingChecks,
    integers_above_2_to_53_checked:true,optimizer_calls:0};
}
function replay(payload, configurationText, sourceText, codecText, C) {
  const started = Date.now();
  let stage="initial", failure=null, cfg=null;
  const output = {schema:"conway99.f0.recorded-triangle-spectral-gap-independent-literal-replay.v1",
    status:"UNACCEPTED_INCOMPLETE_INDEPENDENT_TRIANGLE_GAP_REPLAY",complete:false,
    execution_acceptance_requires_finalization:true,input_bindings:{},records_verified:0,
    failed_triangle_indices:[],all_5364_records_independently_verified:false,
    forward_source_imported_or_executed:false,native_imports:0,optimizer_calls:0,
    native_model_built:false,native_model_modified:false,automatic_retries:0,
    case_replays:1,new_domain_censuses:0,graph_constructed:false,whole_component_excluded:false};
  const utf8 = text => C.utf8(text), sha = bytes => C.sha256(bytes);
  const valueHash = value => sha(utf8(JSON.stringify(value)));
  function elapsed() {
    const milliseconds=Date.now()-started;
    requireTrue(milliseconds>=0,"clock moved backward");
    return milliseconds;
  }
  function tick(label) { stage=label; requireTrue(elapsed()<=LIMIT_MS,"replay time limit: "+label); }
  try {
    cfg=JSON.parse(configurationText);
    requireTrue(cfg.schema==="conway99.f0.recorded-triangle-spectral-gap-independent-literal-configuration.v1",
      "configuration schema");
    equal(cfg.limits,{worker_milliseconds:30000,outer_milliseconds:45000,maximum_report_bytes:65536,
      automatic_retries:0},"fixed replay limits");
    equal(cfg.expected,{triangles:5364,targets:84,selectors:480,edges:68394,indicator_start:71382,
      failed_count:3156,compatible_count:2208},"fixed input scope");
    const sourceBytes=utf8(sourceText), codecBytes=utf8(codecText), configBytes=utf8(configurationText);
    requireTrue(sourceBytes.length===cfg.source.bytes && sha(sourceBytes)===cfg.source.sha256 &&
      C.gitBlob(sourceBytes)===cfg.source.git_blob,"replay source identity");
    requireTrue(codecBytes.length===cfg.codec.bytes && sha(codecBytes)===cfg.codec.sha256 &&
      C.gitBlob(codecBytes)===cfg.codec.git_blob,"codec identity");
    output.source=cfg.source;
    output.configuration={path:cfg.configuration_path,bytes:configBytes.length,
      sha256:sha(configBytes),git_blob:C.gitBlob(configBytes)};
    equal(Object.keys(cfg.inputs).sort(),ALL_INPUTS.slice().sort(),"all input aliases");
    equal(Object.keys(payload).sort(),ALL_INPUTS.slice().sort(),"all payload aliases");
    const inputs={}, rawLengths={};
    for (const name of ALL_INPUTS) {
      tick("bind "+name);
      const ref=cfg.inputs[name],text=payload[name];
      requireTrue(typeof text==="string","input is text "+name);
      let raw;
      if (ref.encoding==="base64-gzip") {
        const compressed=C.base64(text.replace(/\s/g,""));
        requireTrue(compressed.length===ref.bytes && sha(compressed)===ref.sha256 &&
          C.gitBlob(compressed)===ref.git_blob,"archive binding "+name);
        raw=C.gunzip(compressed);
        requireTrue(sha(raw)===ref.raw_sha256,"raw archive hash "+name);
        if(ref.raw_bytes!==undefined)requireTrue(raw.length===ref.raw_bytes,"raw archive length "+name);
        inputs[name]=JSON.parse(C.ascii(raw));
      } else {
        requireTrue(ref.encoding==="utf-8","text encoding "+name);
        raw=utf8(text);
        requireTrue(raw.length===ref.bytes && sha(raw)===ref.sha256 &&
          C.gitBlob(raw)===ref.git_blob,"text binding "+name);
        inputs[name]=ref.format==="text"?text:JSON.parse(text);
      }
      rawLengths[name]=raw.length;
      output.input_bindings[name]={...ref,actual_raw_bytes:raw.length};
    }
    const fcfg=inputs.forward_configuration,f=inputs.forward_report,final=inputs.forward_finalization;
    const owner=inputs.forward_owner,gate=inputs.forward_gate,peer=inputs.forward_review;
    requireTrue(fcfg.schema==="conway99.f0.recorded-triangle-spectral-gap-configuration.v1","forward config schema");
    requireTrue(f.schema==="conway99.f0.recorded-triangle-spectral-gap-minors.v1" &&
      f.status==="COMPLETE_EXACT_RECORDED_TRIANGLE_SPECTRAL_GAP_TEST" && f.complete===true,
      "complete forward report");
    requireTrue(f.records.length===5364 && f.tested_triangles===5364 && f.tested_principal_minors===37548 &&
      f.target_incidence_tables_checked===84,"complete forward dimensions");
    reference(f.configuration,cfg.inputs.forward_configuration,"forward report config");
    reference(f.source,cfg.inputs.forward_source,"forward report source");
    reference(fcfg.source,cfg.inputs.forward_source,"configured forward source");
    equal(Object.keys(fcfg.inputs).sort(),ACCEPTED.slice().sort(),"forward accepted aliases");
    equal(Object.keys(f.input_bindings).sort(),ACCEPTED.slice().sort(),"forward input binding coverage");
    for(const name of ACCEPTED) {
      reference(fcfg.inputs[name],cfg.inputs[name],"shared accepted input "+name);
      equal(f.input_bindings[name],{...fcfg.inputs[name],actual_raw_bytes:rawLengths[name]},
        "complete forward binding "+name);
    }
    requireTrue(final.schema==="conway99.f0.recorded-triangle-spectral-gap-finalization.v1" &&
      final.status==="PASS_COMPLETE_RECORDED_TRIANGLE_GAP_TEST_AND_FINALIZATION" &&
      final.accepted===true && final.report_complete===true && final.within_declared_bounds===true,
      "forward finalization accepted");
    requireTrue(final.report_sha256===cfg.inputs.forward_report.sha256 &&
      final.report_bytes===cfg.inputs.forward_report.bytes && final.maximum_ms===30000 &&
      final.maximum_report_bytes===8388608 && final.automatic_retries===0,"forward finalization identity");
    integer(final.elapsed_through_report_hash_ms,0,30000,"forward worker time");
    if(final.elapsed_after_first_finalization_serialization_ms!==undefined)
      integer(final.elapsed_after_first_finalization_serialization_ms,0,30000,"forward final serialization");
    requireTrue(owner.schema==="conway99.f0.recorded-triangle-spectral-gap-owner.v1" &&
      owner.status==="OWNED_COMPLETE_RECORDED_TRIANGLE_GAP_TEST_ACCEPTED" && owner.accepted===true,
      "forward owner accepted");
    for(const [field,alias] of [["source","forward_source"],["configuration","forward_configuration"],
      ["root_gate","forward_gate"],["independent_source_review","forward_review"],["report","forward_report"]])
      reference(owner[field],cfg.inputs[alias],"forward owner "+field);
    requireTrue(owner.worker_finalization_path===cfg.inputs.forward_finalization.path &&
      owner.worker_status===final.status && owner.worker_elapsed_through_report_hash_ms===final.elapsed_through_report_hash_ms &&
      owner.worker_maximum_ms===30000 && owner.outer_maximum_ms===45000,"forward owner worker fields");
    integer(owner.outer_elapsed_ms,final.elapsed_through_report_hash_ms,45000,"forward outer elapsed");
    integer(owner.outer_elapsed_through_first_owner_serialization_ms,0,45000,"forward owner serialization");
    integer(owner.texts_preserved_at_elapsed_ms,0,45000,"forward text preservation");
    requireTrue(owner.worker_returned===true && owner.worker_invocations===1 && owner.complete_case_records===5364 &&
      owner.automatic_retries===0 && owner.error===null && owner.exact_return_texts_preserved_before_publication===true &&
      owner.outer_started_before_factory_evaluation===true && owner.controls_and_main_in_same_call===true,
      "forward complete single invocation");
    requireTrue(owner.optimizer_calls===0 && owner.native_model_builds===0 && owner.native_model_changes===0 &&
      owner.OS_child_constructed===false && owner.hard_OS_preemption_claimed===false,"forward no native activity");
    requireTrue(gate.status==="AUTHORIZE_ONE_COMPLETE_RECORDED_TRIANGLE_SPECTRAL_GAP_METADATA_TEST" &&
      gate.exact_worker_invocations===1 && gate.automatic_retries===0,"forward root gate");
    for(const [field,alias] of [["source","forward_source"],["configuration","forward_configuration"],
      ["peer_review","forward_review"],["proof","method"]])reference(gate[field],cfg.inputs[alias],"gate "+field);
    equal(gate.inputs,fcfg.inputs,"complete gate input set");
    requireTrue(peer.status==="PASS_COMPLETE_RECORDED_TRIANGLE_SPECTRAL_GAP_THEOREM_AND_SOURCE_REVIEW_UNRUN",
      "complete forward source review");
    reference(peer.source,cfg.inputs.forward_source,"peer reviewed source");
    reference(peer.configuration,cfg.inputs.forward_configuration,"peer reviewed config");
    reference(peer.method,cfg.inputs.method,"peer reviewed method");
    const d=inputs.domain,k=inputs.kernels,audit=inputs.kernel_audit,indicator=inputs.indicator;
    const theoremReview=inputs.spectral_review, modelCfg=inputs.combined_configuration,modelRoot=inputs.combined_root;
    requireTrue(theoremReview.status==="PASS_MATHEMATICAL_NECESSITY" && theoremReview.complete_subject_read===true,
      "accepted spectral theorem");
    reference(theoremReview.subject,cfg.inputs.spectral_theorem,"spectral theorem subject");
    equal(theoremReview.input_bindings,fcfg.expected_spectral_review_bindings,"theorem input bindings");
    requireTrue(k.schema==="f0-full21-core-Schur-kernels-v1" &&
      k.inputs.independent_audit_record_sha256===cfg.inputs.kernel_audit.sha256,"accepted kernel audit");
    requireTrue(k.scope.global_prism_and_F_zero===true && k.scope.split_shell==="18+18" &&
      k.scope.component===0 && k.scope.other_component_and_alignment_free===true &&
      k.scope.per_embedding_Schur_before_averaging===true,"kernel theorem scope");
    requireTrue(audit.status==="PASS: exact full-core Schur corrections; no point query" &&
      audit.signature_count===480 && audit.fiber_neighbor_counts_all_one===true,"accepted audit");
    requireTrue(inputs.triangle_literal_root.status==="ROOT_ACCEPTS_COMPLETE_SEPARATE_LITERAL_SUPPORT_REPLAY_AND_INDICATOR_BINDINGS" &&
      inputs.triangle_literal_root.root_previously_checked_all_5364_indicator_identities_and_all_84_target_equalities===true,
      "accepted indicators");
    requireTrue(modelRoot.status==="ROOT_ACCEPTS_COMPLETE_COMBINED_EXTENSIONS_NATIVE_MODEL_AND_INDEPENDENT_COLD" &&
      modelRoot.model_raw_sha256===fcfg.accepted_model.raw_sha256 && modelRoot.model_raw_bytes===fcfg.accepted_model.raw_bytes &&
      modelRoot.independent_replay_triangle_surviving_records===5364 && modelRoot.independent_replay_triangle_targets===84,
      "accepted native indicator identities");
    reference(modelRoot.configuration,cfg.inputs.combined_configuration,"combined config");
    reference(modelCfg.inputs.domain,cfg.inputs.domain,"native domain");
    reference(modelCfg.inputs.triangle_inventory,cfg.inputs.indicator,"native indicator table");
    reference(modelCfg.inputs.triangle_literal_root_acceptance,cfg.inputs.triangle_literal_root,"native literal authority");
    requireTrue(modelCfg.layout.triangle_variable_start===71382 && modelCfg.layout.triangle_variables===5364,
      "native indicator offsets");
    requireTrue(indicator.status==="PASS_EXACT_SHARED_TRIANGLE_INDICATOR_INVENTORY" &&
      indicator.triangles.length===5364 && indicator.targets.length===84 &&
      indicator.unique_surviving_support_triples===5364 && indicator.target_triangle_incidences===5364,
      "complete accepted indicator table");
    output.controls=controls(tick);
    const h=d.signature_domain,adj=d.possible_neighbor_signature_ids,core=d.component_core_rows;
    requireTrue(h.length===480 && adj.length===480 && core.length===21,"literal input dimensions");
    const masks=[],eta=[],fiberOf=[],fibers=[[],[],[]];
    for(let j=0;j<18;j++) {
      const choices=[];
      for(let i=0;i<3;i++)if((integer(core[i],0,2097151,"central row") & (1<<(j+3)))!==0)choices.push(i);
      requireTrue(choices.length===1,"unique central fiber");
      fiberOf.push(choices[0]);fibers[choices[0]].push(j);
    }
    requireTrue(fibers.every(x=>x.length===6),"six sites per fiber");
    for(let v=0;v<480;v++) {
      requireTrue(Array.isArray(h[v]) && h[v].length===3 && h[v][0]<h[v][1] && h[v][1]<h[v][2],
        "three distinct signature sites");
      let mask=0;const profile=[0,0,0];
      for(const j of h[v]){integer(j,0,17,"signature site");mask|=1<<j;profile[fiberOf[j]]++;}
      masks.push(mask);eta.push(profile);
    }
    equal(fibers,k.fibers,"literal fibers");equal(eta,k.fiber_counts,"literal occupancies");
    equal(eta.map(row=>row.map(x=>x-1)),k.fiber_deviations,"literal deviations");
    const sets=adj.map((row,v)=>{
      requireTrue(Array.isArray(row),"neighbor row");
      for(let j=0;j<row.length;j++)requireTrue(integer(row[j],0,479,"neighbor")!==v &&
        (j===0 || row[j-1]<row[j]),"simple ordered neighbors");
      return new Set(row);
    });
    const edges=[];
    for(let right=479;right>=0;right--) {
      for(const left of adj[right]){
        requireTrue(sets[left].has(right),"symmetric saved edge");
        if(left<right)edges.push([left,right]);
      }
      if(right%32===0)tick("reindex saved edges");
    }
    edges.sort((u,v)=>u[0]-v[0] || u[1]-v[1]);
    requireTrue(edges.length===68394 && valueHash(edges)===fcfg.original_edges_value_sha256,"full edge namespace");
    const edgeIds=new Map(edges.map((pair,id)=>[pair.join(","),id]));
    const plusList=k.kernels.filter(x=>x.family==="plus"),auditPlus=audit.families.filter(x=>x.family==="plus");
    requireTrue(plusList.length===1 && auditPlus.length===1,"unique plus kernel");
    const plus=plusList[0],prefix=[0];
    for(let i=0;i<480;i++)prefix.push(prefix[i]+479-i);
    requireTrue(prefix[480]===114960 && plus.diagonal_x.length===480 && plus.off_diagonal_Z.length===114960 &&
      plus.Schur_coefficient_denominator===60 && plus.Y===-540 && plus.common_numerator_divisor===1 &&
      plus.primitive_kernel_sha256===fcfg.plus_primitive_sha256 &&
      auditPlus[0].primitive_kernel_sha256===fcfg.plus_primitive_sha256,"plus scale and namespace");
    const primitive=[];
    for(let i=0;i<480;i++){
      primitive.push(integer(plus.diagonal_x[i],-1238,1238,"plus diagonal"));
      for(let j=i+1;j<480;j++)primitive.push(integer(plus.off_diagonal_Z[prefix[i]+j-i-1],-1238,1238,"plus pair"));
    }
    primitive.push(-540);
    requireTrue(valueHash(primitive)===fcfg.plus_primitive_sha256,"complete primitive hash");
    const targets=new Map(),targetIncidence=new Map();
    for(const target of indicator.targets){
      const id=integer(target.edge_id,0,68393,"target ID");
      requireTrue(!targets.has(id),"unique target");equal(target.endpoints,edges[id],"target endpoints");
      targets.set(id,target);targetIncidence.set(id,[]);
    }
    const derivedRecords=new Array(5364),failed=[];
    const counts={negative_diagonal:0,negative_pair_minor:0,negative_determinant_only:0,
      all_principal_minors_nonnegative:0,passes_with_zero_determinant:0};
    const lex=(a,b)=>a[0]-b[0] || a[1]-b[1] || a[2]-b[2];
    for(let index=5363;index>=0;index--){
      if(index%32===0)tick("reverse triangle "+index);
      const tri=indicator.triangles[index],vertices=tri.vertices;
      requireTrue(Array.isArray(vertices) && vertices.length===3 && vertices[0]<vertices[1] && vertices[1]<vertices[2],
        "triangle vertices");
      for(const v of vertices)integer(v,0,479,"triangle signature");
      if(index>0)requireTrue(lex(indicator.triangles[index-1].vertices,vertices)<0,"unique lexicographic universe");
      requireTrue(tri.triangle_index===index && tri.proposed_variable_index===68934+index,"standalone indicator index");
      const pairs=[[vertices[0],vertices[1]],[vertices[0],vertices[2]],[vertices[1],vertices[2]]];
      const ids=pairs.map(pair=>edgeIds.get(pair.join(",")));
      requireTrue(ids.every(x=>x!==undefined),"three original edges");equal(ids,tri.edge_ids,"literal triangle edge IDs");
      for(const[left,right]of pairs)requireTrue((masks[left]&masks[right])===0,"triangle first-incidence disjointness");
      requireTrue(tri.origins.length===1,"complete unique origin");
      const origin=tri.origins[0];
      integer(origin.support_table_index,0,131,"target support table");
      integer(origin.support_index,0,479,"target support index");
      requireTrue(targets.has(origin.target_edge_id) && ids.includes(origin.target_edge_id),"literal target origin");
      targetIncidence.get(origin.target_edge_id).push(index);
      const matrix=Array.from({length:3},()=>[0n,0n,0n]);
      for(let i=0;i<3;i++)for(let j=0;j<3;j++){
        const u=vertices[i],v=vertices[j],left=Math.min(u,v),right=Math.max(u,v);
        const y=i===j?0n:1n,n=i===j?8n:1n,intersection=i===j?3n:0n;
        const numerator=i===j?BigInt(plus.diagonal_x[u]):
          BigInt(plus.off_diagonal_Z[prefix[left]+right-left-1])-540n*y;
        const residual=(i===j?12n:0n)+2n-intersection-n-y;
        requireTrue(residual===(i===j?3n:0n),"actual triangle residual identity");
        let profileDot=0n;
        for(let f=0;f<3;f++)profileDot+=BigInt(eta[u][f])*BigInt(eta[v][f]);
        matrix[i][j]=2n*numerator-180n*residual+30n*profileDot;
      }
      const minors=SUBSETS.map(subset=>determinant(matrix,subset));
      let mask=0;for(let j=0;j<7;j++)if(minors[j]<0n)mask+=1<<j;
      let classification="all_principal_minors_nonnegative";
      if(minors.slice(0,3).some(x=>x<0n))classification="negative_diagonal";
      else if(minors.slice(3,6).some(x=>x<0n))classification="negative_pair_minor";
      else if(minors[6]<0n)classification="negative_determinant_only";
      counts[classification]++;if(mask===0 && minors[6]===0n)counts.passes_with_zero_determinant++;
      const record={triangle_index:index,vertices,edge_ids:ids,indicator_variable:71382+index,origin,
        matrix_entries:[matrix[0][0],matrix[1][1],matrix[2][2],matrix[0][1],matrix[0][2],matrix[1][2]].map(String),
        principal_minors:minors.map(String),negative_minor_mask:mask,classification};
      equal(record,f.records[index],"every complete forward record "+index);
      derivedRecords[index]=record;
      if(mask)failed.push(index);
      output.records_verified++;
    }
    for(const[id,origin]of targets){
      targetIncidence.get(id).sort((a,b)=>a-b);
      equal(targetIncidence.get(id),origin.triangle_indices,"complete target-origin table");
    }
    failed.sort((a,b)=>a-b);
    const expectedFailures=failed.map(i=>[i,derivedRecords[i].negative_minor_mask]);
    const zeros=failed.map(i=>({triangle_index:i,row_key:[0,0,[[71382+i,1]]]}));
    const covers=failed.map(i=>({triangle_index:i,row_key:[0,2,derivedRecords[i].edge_ids.map(e=>[540+e,1])]}));
    equal(expectedFailures,f.failures,"all failure entries");
    equal(zeros,f.proposed_indicator_zero_rows,"every proposed indicator-zero key");
    equal(covers,f.proposed_triangle_cover_rows,"every proposed edge-cover key");
    equal(counts,f.counts,"complete classifications");
    requireTrue(failed.length===3156 && counts.all_principal_minors_nonnegative===2208,"fixed terminal counts");
    equal(f.matrix_entry_order,["aa","bb","cc","ab","ac","bc"],"matrix order");
    equal(f.principal_minor_order,["a","b","c","ab","ac","bc","abc"],"minor order");
    const recordsHash=valueHash(derivedRecords),zeroHash=valueHash(zeros.map(x=>x.row_key)),
      coverHash=valueHash(covers.map(x=>x.row_key));
    requireTrue(recordsHash===f.records_value_sha256,"complete derived record hash");
    requireTrue(zeroHash===f.proposed_indicator_zero_row_keys_sha256,"complete zero-key hash");
    requireTrue(coverHash===f.proposed_triangle_cover_row_keys_sha256,"complete cover-key hash");
    equal(f.accepted_native_model,fcfg.accepted_model,"forward native-model binding");
    requireTrue(f.optimizer_calls===0 && f.native_imports===0 && f.native_model_built===false &&
      f.native_model_modified===false && f.old_zero_pruning===false && f.new_rows_installed===0 &&
      f.independent_terminal_replay_completed===false && f.automatic_retries===0,"forward scope flags");
    output.forward_report=cfg.inputs.forward_report;
    output.forward_finalization=cfg.inputs.forward_finalization;
    output.forward_owner=cfg.inputs.forward_owner;
    output.forward_gate=cfg.inputs.forward_gate;
    output.failed_triangle_indices=failed;output.failed_count=failed.length;output.counts=counts;
    output.complete_record_value_sha256=recordsHash;
    output.proposed_indicator_zero_row_keys_sha256=zeroHash;
    output.proposed_triangle_cover_row_keys_sha256=coverHash;
    output.failed_triangle_indices_sha256=valueHash(failed);
    output.all_5364_records_independently_verified=true;
    output.all_seven_minors_per_record_independently_recomputed=true;
    output.complete_triangle_origins_and_target_incidence_checked=true;
    output.all_proposed_zero_and_cover_rows_checked=true;
    output.target_tables_checked=84;output.principal_minors_recomputed=37548;
    output.enumeration_order="reverse accepted triangle index";
    output.matrix_arithmetic="Literal 3x3 BigInt matrix; signed permutation determinants of every principal submatrix.";
    output.original_edges_checked=68394;output.saved_neighbor_rows_checked=480;
    output.accepted_indicator_start=71382;output.accepted_indicator_count=5364;
    output.complete=true;output.status="PASS_COMPLETE_INDEPENDENT_RECORDED_TRIANGLE_GAP_LITERAL_REPLAY";
    tick("before replay serialization");
  } catch(error) {
    failure=String(error && error.message || error);
    output.status="UNACCEPTED_INDEPENDENT_RECORDED_TRIANGLE_GAP_LITERAL_REPLAY";
    output.complete=false;output.error={stage,message:failure};
  }
  output.elapsed_before_serialization_ms=Date.now()-started;
  const reportText=JSON.stringify(output)+"\n",reportBytes=utf8(reportText),reportSha=sha(reportBytes);
  const finalElapsed=Date.now()-started;
  const within=finalElapsed>=0 && finalElapsed<=LIMIT_MS && reportBytes.length<=REPORT_LIMIT;
  const finalization={schema:"conway99.f0.recorded-triangle-spectral-gap-independent-literal-finalization.v1",
    status:output.complete && failure===null && within?
      "PASS_COMPLETE_INDEPENDENT_RECORDED_TRIANGLE_GAP_REPLAY_AND_FINALIZATION":
      "UNACCEPTED_INDEPENDENT_RECORDED_TRIANGLE_GAP_REPLAY_OR_FINALIZATION",
    report_sha256:reportSha,report_bytes:reportBytes.length,report_complete:output.complete,
    elapsed_through_report_hash_ms:finalElapsed,maximum_ms:LIMIT_MS,maximum_report_bytes:REPORT_LIMIT,
    within_declared_bounds:within,accepted:output.complete && failure===null && within,automatic_retries:0};
  let finalizationText=JSON.stringify(finalization)+"\n";
  const afterFinalization=Date.now()-started;
  if(afterFinalization<0 || afterFinalization>LIMIT_MS){
    finalization.status="UNACCEPTED_INDEPENDENT_RECORDED_TRIANGLE_GAP_REPLAY_OR_FINALIZATION";
    finalization.accepted=false;finalization.within_declared_bounds=false;
    finalization.elapsed_after_first_finalization_serialization_ms=afterFinalization;
    finalizationText=JSON.stringify(finalization)+"\n";
  }
  return {report_text:reportText,finalization_text:finalizationText};
}
return {replay,controls};
})()
