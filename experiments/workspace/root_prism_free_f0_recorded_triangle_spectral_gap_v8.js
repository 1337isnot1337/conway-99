(() => {
"use strict";
const MAX_MS = 30000, MAX_BYTES = 8 * 1024 * 1024;
const EXPECTED = { selectors: 480, edges: 68394, triangles: 5364, targets: 84,
  edge_start: 540, indicator_start: 71382, model_variables: 80730, model_rows: 297470 };
const INPUT_NAMES = ["domain", "kernels", "kernel_audit", "spectral_theorem",
  "spectral_review", "indicator", "triangle_literal_root",
  "combined_configuration", "combined_root", "method"];
function check(ok, message) { if (!ok) throw Error(message); }
function int(x, lo, hi, label) {
  check(Number.isSafeInteger(x) && lo <= x && x <= hi, "integer " + label);
  return x;
}
function same(a, b, label) { check(JSON.stringify(a) === JSON.stringify(b), label); }
function pairId(a, b) { check(a < b, "ordered pair"); return a * (959 - a) / 2 + b - a - 1; }
function lex(a, b) {
  for (let i = 0; i < a.length; i++) if (a[i] !== b[i]) return a[i] - b[i];
  return 0;
}
function minors3(m) {
  const [a,b,c,p,q,r] = m;
  return [a,b,c,a*b-p*p,a*c-q*q,b*c-r*r,
    a*b*c+2n*p*q*r-a*r*r-b*q*q-c*p*p];
}
function oracleDet(matrix, subset) {
  let answer = 0n;
  function visit(p, used) {
    if (p.length === subset.length) {
      let inversions = 0, product = 1n;
      for (let i = 0; i < p.length; i++) {
        product *= matrix[subset[i]][subset[p[i]]];
        for (let j = i+1; j < p.length; j++) if (p[i] > p[j]) inversions++;
      }
      answer += inversions % 2 ? -product : product;
      return;
    }
    for (let j = 0; j < subset.length; j++) if (!(used & (1 << j)))
      visit(p.concat(j), used | (1 << j));
  }
  visit([], 0);
  return answer;
}
function controls(tick) {
  const subsets = [[0],[1],[2],[0,1],[0,2],[1,2],[0,1,2]];
  let comparisons = 0;
  function verify(m) {
    const [a,b,c,p,q,r] = m, matrix = [[a,p,q],[p,b,r],[q,r,c]], direct = minors3(m);
    for (let i = 0; i < 7; i++) {
      check(direct[i] === oracleDet(matrix, subsets[i]), "independent determinant oracle");
      comparisons++;
    }
    return direct;
  }
  for (let code = 0; code < 729; code++) {
    let v = code; const m = [];
    for (let i = 0; i < 6; i++) { m.push(BigInt(v % 3 - 1)); v = Math.floor(v / 3); }
    verify(m); if (code % 32 === 0) tick("controls");
  }
  check(verify([2n,3n,4n,0n,0n,0n]).every(x => x > 0n), "positive control");
  check(verify([1n,1n,1n,1n,1n,1n]).every(x => x >= 0n), "singular PSD control");
  check(verify([-1n,1n,1n,0n,0n,0n])[0] < 0n, "negative diagonal control");
  check(verify([1n,1n,1n,2n,0n,0n])[3] < 0n, "negative pair control");
  const determinantOnly = verify([1n,1n,1n,-1n,-1n,-1n]);
  check(determinantOnly.slice(0,6).every(x => x >= 0n) && determinantOnly[6] < 0n,
    "negative determinant with nonnegative proper minors");
  const big = 9007199254740993n, large = verify([big,big+1n,big+2n,0n,0n,0n]);
  check(large[6] === big*(big+1n)*(big+2n), "large integer determinant");
  same(JSON.parse(JSON.stringify(large.map(String))), large.map(String), "decimal-string roundtrip");
  return {status:"PASS_EXHAUSTIVE_SMALL_INTEGER_PRINCIPAL_MINOR_CONTROLS",
    exhaustive_matrices:729, explicit_matrices:6, principal_minor_comparisons:comparisons,
    includes_integers_above_2_to_53:true, arithmetic:"BigInt", optimizer_calls:0};
}
function run(payload, configurationText, sourceText, codecText, C) {
  const started = Date.now();
  let cfg = null, failed = null, stage = "initialization", preSerializationMs = null;
  const report = {schema:"conway99.f0.recorded-triangle-spectral-gap-minors.v1",
    status:"UNACCEPTED_INCOMPLETE_RECORDED_TRIANGLE_GAP_TEST", complete:false,
    execution_acceptance_requires_finalization:true, input_bindings:{},
    expected:EXPECTED, controls:null, records:[], failures:[],
    proposed_indicator_zero_rows:[], proposed_triangle_cover_rows:[],
    optimizer_calls:0, native_imports:0, native_model_built:false, native_model_modified:false,
    graph_constructed:false, whole_component_excluded:false,
    scope:"Only the 5364 accepted recorded triangles; actual-graph PSD necessity, no feasibility claim.",
    old_zero_pruning:false, case_enumerations:1, automatic_retries:0};
  function elapsed() { const t = Date.now() - started; check(t >= 0, "clock moved backward"); return t; }
  function tick(label) { stage = label; check(elapsed() <= MAX_MS, "worker time limit at " + label); }
  const bytes = s => C.utf8(s), sha = b => C.sha256(b);
  const valueSha = v => sha(bytes(JSON.stringify(v)));
  function refMatches(a,b,label) {
    check(a && b && a.path === b.path && a.sha256 === b.sha256, "authority link " + label);
    if (a.git_blob && b.git_blob) check(a.git_blob === b.git_blob, "Git link " + label);
  }
  try {
    cfg = JSON.parse(configurationText);
    check(cfg.schema === "conway99.f0.recorded-triangle-spectral-gap-configuration.v1", "configuration schema");
    same(cfg.expected, EXPECTED, "frozen dimensions");
    same(cfg.limits, {total_milliseconds:MAX_MS, outer_milliseconds:45000,
      maximum_report_bytes:MAX_BYTES, automatic_retries:0}, "frozen limits");
    const sourceBytes = bytes(sourceText), codecBytes = bytes(codecText), configBytes = bytes(configurationText);
    check(sourceBytes.length === cfg.source.bytes && sha(sourceBytes) === cfg.source.sha256 &&
      C.gitBlob(sourceBytes) === cfg.source.git_blob, "source bytes");
    check(codecBytes.length === cfg.codec.bytes && sha(codecBytes) === cfg.codec.sha256 &&
      C.gitBlob(codecBytes) === cfg.codec.git_blob, "codec bytes");
    report.source = cfg.source;
    report.configuration = {path:cfg.configuration_path, bytes:configBytes.length,
      sha256:sha(configBytes), git_blob:C.gitBlob(configBytes)};
    same(Object.keys(cfg.inputs).sort(), INPUT_NAMES.slice().sort(), "complete input alias set");
    same(Object.keys(payload).sort(), INPUT_NAMES.slice().sort(), "complete payload alias set");
    const inputs = {};
    for (const name of INPUT_NAMES) {
      tick("binding " + name);
      const ref = cfg.inputs[name], data = payload[name];
      check(typeof data === "string", "input text " + name);
      let raw;
      if (ref.encoding === "base64-gzip") {
        const compressed = C.base64(data);
        check(compressed.length === ref.bytes && sha(compressed) === ref.sha256 &&
          C.gitBlob(compressed) === ref.git_blob, "compressed input " + name);
        raw = C.gunzip(compressed);
        check(sha(raw) === ref.raw_sha256, "raw input " + name);
        if (ref.raw_bytes !== undefined) check(raw.length === ref.raw_bytes, "raw bytes " + name);
        inputs[name] = JSON.parse(C.ascii(raw));
      } else {
        check(ref.encoding === "utf-8", "input encoding " + name);
        raw = bytes(data);
        check(raw.length === ref.bytes && sha(raw) === ref.sha256 &&
          C.gitBlob(raw) === ref.git_blob, "text input " + name);
        inputs[name] = ref.format === "text" ? data : JSON.parse(data);
      }
      report.input_bindings[name] = {...ref, actual_raw_bytes:raw.length};
    }
    tick("controls"); report.controls = controls(tick); tick("authority checks");
    const d = inputs.domain, kernel = inputs.kernels, audit = inputs.kernel_audit;
    const review = inputs.spectral_review, indicator = inputs.indicator;
    const literal = inputs.triangle_literal_root, modelCfg = inputs.combined_configuration;
    const modelRoot = inputs.combined_root;
    check(review.status === "PASS_MATHEMATICAL_NECESSITY" && review.complete_subject_read === true,
      "accepted spectral theorem");
    refMatches(review.subject, cfg.inputs.spectral_theorem, "spectral theorem");
    same(review.input_bindings, cfg.expected_spectral_review_bindings, "spectral review input identities");
    check(kernel.schema === "f0-full21-core-Schur-kernels-v1" &&
      kernel.inputs.independent_audit_record_sha256 === cfg.inputs.kernel_audit.sha256, "kernel audit binding");
    check(audit.status === "PASS: exact full-core Schur corrections; no point query" &&
      audit.signature_count === 480 && audit.fiber_neighbor_counts_all_one === true, "full core audit");
    check(kernel.scope.global_prism_and_F_zero === true && kernel.scope.split_shell === "18+18" &&
      kernel.scope.component === 0 && kernel.scope.other_component_and_alignment_free === true &&
      kernel.scope.per_embedding_Schur_before_averaging === true, "kernel mathematical scope");
    check(indicator.status === "PASS_EXACT_SHARED_TRIANGLE_INDICATOR_INVENTORY" &&
      indicator.unique_surviving_support_triples === 5364 && indicator.target_triangle_incidences === 5364 &&
      indicator.live_targets === 84 && indicator.triangles.length === 5364 && indicator.targets.length === 84,
      "complete indicator inventory");
    check(literal.status === "ROOT_ACCEPTS_COMPLETE_SEPARATE_LITERAL_SUPPORT_REPLAY_AND_INDICATOR_BINDINGS" &&
      literal.root_previously_checked_all_5364_indicator_identities_and_all_84_target_equalities === true &&
      literal.complete_literal_triangle_supports_accepted_for_future_native_preparation === true,
      "accepted complete literal support");
    check(modelRoot.status === "ROOT_ACCEPTS_COMPLETE_COMBINED_EXTENSIONS_NATIVE_MODEL_AND_INDEPENDENT_COLD" &&
      modelRoot.model_raw_sha256 === cfg.accepted_model.raw_sha256 &&
      modelRoot.model_raw_bytes === cfg.accepted_model.raw_bytes &&
      modelRoot.variables === 80730 && modelRoot.rows === 297470 &&
      modelRoot.independent_replay_triangle_surviving_records === 5364 &&
      modelRoot.independent_replay_triangle_targets === 84, "accepted native indicator layout");
    refMatches(modelRoot.configuration, cfg.inputs.combined_configuration, "native configuration");
    refMatches(modelCfg.inputs.domain, cfg.inputs.domain, "model domain");
    refMatches(modelCfg.inputs.triangle_inventory, cfg.inputs.indicator, "model indicator inventory");
    refMatches(modelCfg.inputs.triangle_literal_root_acceptance, cfg.inputs.triangle_literal_root, "literal root");
    check(modelCfg.layout.triangle_variable_start === 71382 && modelCfg.layout.triangle_variables === 5364 &&
      modelCfg.layout.variables === 80730 && modelCfg.layout.rows === 297470, "native layout");
    const h = d.signature_domain, neighbors = d.possible_neighbor_signature_ids, core = d.component_core_rows;
    check(h.length === 480 && neighbors.length === 480 && core.length === 21, "domain dimensions");
    for (const row of core) int(row,0,2**21-1,"core row");
    const hMasks = h.map((s,a) => {
      check(Array.isArray(s) && s.length === 3 && s[0] < s[1] && s[1] < s[2], "signature triple");
      if (a) check(lex(h[a-1],s) < 0, "signature order");
      return s.reduce((mask,j) => mask | (1 << int(j,0,17,"signature site")),0);
    });
    const fibers = Array.from({length:3},(_,i) =>
      Array.from({length:18},(_,j)=>j).filter(j => (core[i] & (1 << (j+3))) !== 0));
    check(fibers.every(f=>f.length===6), "three fibers of six");
    for (let j=0;j<18;j++) check(fibers.filter(f=>f.includes(j)).length === 1, "fiber partition");
    same(fibers,kernel.fibers,"literal fiber ordering");
    const eta = h.map(s => fibers.map(f => s.filter(j=>f.includes(j)).length));
    same(eta,kernel.fiber_counts,"complete literal fiber counts");
    same(eta.map(v=>v.map(x=>x-1)),kernel.fiber_deviations,"complete fiber deviations");
    const neighborSets = neighbors.map((row,a) => {
      check(Array.isArray(row), "neighbor list");
      for(let j=0;j<row.length;j++) {
        int(row[j],0,479,"neighbor"); check(row[j]!==a && (!j || row[j-1]<row[j]),"neighbor ordering");
      }
      return new Set(row);
    });
    const edges=[], edgeByPair=new Map();
    for(let a=0;a<480;a++) {
      for(const b of neighbors[a]) {
        check(neighborSets[b].has(a),"symmetric saved neighbor relation");
        if(a<b) { edgeByPair.set(a+","+b,edges.length); edges.push([a,b]); }
      }
      if(a%32===0) tick("original edge namespace");
    }
    check(edges.length===68394 && valueSha(edges)===cfg.original_edges_value_sha256,"original edge IDs");
    const plusList=kernel.kernels.filter(k=>k.family==="plus"), auditPlus=audit.families.filter(k=>k.family==="plus");
    check(plusList.length===1 && auditPlus.length===1,"unique plus family");
    const plus=plusList[0], ap=auditPlus[0];
    check(plus.Schur_coefficient_denominator===60 && plus.Y===-540 && plus.common_numerator_divisor===1 &&
      plus.diagonal_x.length===480 && plus.off_diagonal_Z.length===114960 &&
      plus.independent_direct_inverse_audit_matched===true && plus.full_entries_checked===115440,
      "plus scale and coefficient dimensions");
    check(ap.rank21===20 && ap.residual_cross_vectors_checked===480 &&
      ap.all_115440_full_vs_old_kernel_entries_checked===true && ap.coefficient_common_denominator===60 &&
      ap.positive_common_divisor===1 && ap.primitive_kernel_sha256===cfg.plus_primitive_sha256,"plus independent audit");
    const primitive=[];
    for(let a=0;a<480;a++) for(let b=a;b<480;b++)
      primitive.push(int(a===b?plus.diagonal_x[a]:plus.off_diagonal_Z[pairId(a,b)],-1238,1238,"kernel coefficient"));
    primitive.push(-540);
    check(valueSha(primitive)===cfg.plus_primitive_sha256 &&
      plus.primitive_kernel_sha256===cfg.plus_primitive_sha256,"complete primitive kernel order and hash");
    const targets=new Map(), targetIncidences=new Map();
    for(let i=0;i<indicator.targets.length;i++) {
      const t=indicator.targets[i]; int(t.edge_id,0,68393,"target edge");
      check(!targets.has(t.edge_id) && (!i || indicator.targets[i-1].edge_id<t.edge_id),"target order");
      same(t.endpoints,edges[t.edge_id],"target endpoints");
      targets.set(t.edge_id,t); targetIncidences.set(t.edge_id,[]);
    }
    const counts={negative_diagonal:0,negative_pair_minor:0,negative_determinant_only:0,
      all_principal_minors_nonnegative:0,passes_with_zero_determinant:0};
    const dot=(u,v)=>u.reduce((s,x,i)=>s+BigInt(x)*BigInt(v[i]),0n);
    const diagonal=a=>2n*BigInt(plus.diagonal_x[a])-540n+30n*dot(eta[a],eta[a]);
    const off=(a,b)=>2n*BigInt(plus.off_diagonal_Z[pairId(a,b)])-1080n+30n*dot(eta[a],eta[b]);
    for(let k=0;k<5364;k++) {
      if(k%32===0) tick("triangle "+k);
      const t=indicator.triangles[k], v=t.vertices;
      check(Array.isArray(v) && v.length===3 && v[0]<v[1] && v[1]<v[2],"ordered triangle");
      for(const a of v) int(a,0,479,"triangle vertex");
      if(k) check(lex(indicator.triangles[k-1].vertices,v)<0,"complete triangle order");
      check(t.triangle_index===k && t.proposed_variable_index===68934+k,"standalone indicator index");
      const [a,b,c]=v, ids=[edgeByPair.get(a+","+b),edgeByPair.get(a+","+c),edgeByPair.get(b+","+c)];
      check(ids.every(x=>x!==undefined),"three original eligible edges"); same(ids,t.edge_ids,"triangle edge IDs");
      check(!(hMasks[a]&hMasks[b]) && !(hMasks[a]&hMasks[c]) && !(hMasks[b]&hMasks[c]),
        "pairwise disjoint first signatures");
      check(t.origins.length===1,"complete unique target origin");
      const origin=t.origins[0];
      check(targets.has(origin.target_edge_id) && ids.includes(origin.target_edge_id),"target origin");
      int(origin.support_table_index,0,131,"support table"); int(origin.support_index,0,479,"support index");
      targetIncidences.get(origin.target_edge_id).push(k);
      const matrix=[diagonal(a),diagonal(b),diagonal(c),off(a,b),off(a,c),off(b,c)], minors=minors3(matrix);
      const mask=minors.reduce((m,x,i)=>x<0n?m|(1<<i):m,0);
      const classification=(mask&7)?"negative_diagonal":(mask&56)?"negative_pair_minor":
        (mask&64)?"negative_determinant_only":"all_principal_minors_nonnegative";
      counts[classification]++;
      if(!mask && minors[6]===0n) counts.passes_with_zero_determinant++;
      report.records.push({triangle_index:k,vertices:v,edge_ids:ids,indicator_variable:71382+k,
        origin,matrix_entries:matrix.map(String),principal_minors:minors.map(String),
        negative_minor_mask:mask,classification});
      if(mask) {
        report.failures.push([k,mask]);
        report.proposed_indicator_zero_rows.push({triangle_index:k,row_key:[0,0,[[71382+k,1]]]});
        report.proposed_triangle_cover_rows.push({triangle_index:k,row_key:[0,2,ids.map(e=>[540+e,1])]});
      }
    }
    for(const [edge,t] of targets) same(targetIncidences.get(edge),t.triangle_indices,"complete target incidence "+edge);
    tick("complete record validation");
    report.counts=counts; report.tested_triangles=report.records.length;
    report.tested_principal_minors=report.records.length*7; report.target_incidence_tables_checked=targets.size;
    report.matrix_entry_order=["aa","bb","cc","ab","ac","bc"];
    report.principal_minor_order=["a","b","c","ab","ac","bc","abc"];
    report.records_value_sha256=valueSha(report.records);
    report.proposed_indicator_zero_row_keys_sha256=valueSha(report.proposed_indicator_zero_rows.map(x=>x.row_key));
    report.proposed_triangle_cover_row_keys_sha256=valueSha(report.proposed_triangle_cover_rows.map(x=>x.row_key));
    report.accepted_native_model=cfg.accepted_model;
    report.new_rows_installed=0; report.independent_terminal_replay_completed=false;
    report.complete=true; report.status="COMPLETE_EXACT_RECORDED_TRIANGLE_SPECTRAL_GAP_TEST";
    tick("before serialization");
  } catch(error) {
    failed=String(error && error.message || error); report.error={stage,message:failed};
    report.complete=false; report.status="UNACCEPTED_RECORDED_TRIANGLE_GAP_TEST_ERROR_OR_LIMIT";
  }
  preSerializationMs=Date.now()-started;
  report.elapsed_before_serialization_ms=preSerializationMs;
  const reportText=JSON.stringify(report)+"\n", reportBytes=bytes(reportText), reportSha=sha(reportBytes);
  const finalMs=Date.now()-started, within=finalMs>=0 && finalMs<=MAX_MS && reportBytes.length<=MAX_BYTES;
  const accepted=report.complete && failed===null && within;
  const finalization={schema:"conway99.f0.recorded-triangle-spectral-gap-finalization.v1",
    status:accepted?"PASS_COMPLETE_RECORDED_TRIANGLE_GAP_TEST_AND_FINALIZATION":
      "UNACCEPTED_RECORDED_TRIANGLE_GAP_TEST_OR_FINALIZATION",
    report_sha256:reportSha,report_bytes:reportBytes.length,report_complete:report.complete,
    elapsed_through_report_hash_ms:finalMs,maximum_ms:MAX_MS,maximum_report_bytes:MAX_BYTES,
    within_declared_bounds:within,accepted,automatic_retries:0};
  let finalizationText=JSON.stringify(finalization)+"\n";
  const finalizationEnd=Date.now()-started;
  if(finalizationEnd<0 || finalizationEnd>MAX_MS) {
    finalization.status="UNACCEPTED_RECORDED_TRIANGLE_GAP_TEST_OR_FINALIZATION";
    finalization.within_declared_bounds=false; finalization.accepted=false;
    finalization.elapsed_after_first_finalization_serialization_ms=finalizationEnd;
    finalizationText=JSON.stringify(finalization)+"\n";
  }
  return {report_text:reportText,finalization_text:finalizationText};
}
return {run,controls,minors3};
})()
