/* Independent literal verification of saved triangle-capacity proposals.
 * Uses only accepted saved metadata; never evaluates the proposal producer.
 * Native messages are left for the separately owned protobuf replay.
 */
(function (codec) {
  "use strict";
  const need = (value, message) => { if (!value) throw new Error(message); };
  const json = value => JSON.stringify(value);
  function canonical(value) {
    if (Array.isArray(value)) return "[" + value.map(canonical).join(",") + "]";
    if (value !== null && typeof value === "object")
      return "{" + Object.keys(value).sort().map(k => json(k) + ":" + canonical(value[k])).join(",") + "}";
    return json(value);
  }
  const equal = (a, b, label) => need(canonical(a) === canonical(b), label);
  const digest = value => codec.sha256(codec.utf8(json(value)));
  function sameRef(a, b, label) {
    need(a.path === b.path && a.bytes === b.bytes && a.sha256 === b.sha256, label);
  }
  function run(inputs, configurationText, sourceText, codecText) {
    const started = Date.now(), cfg = JSON.parse(configurationText);
    const tick = () => need(Date.now() - started < cfg.limits.total_milliseconds, "literal verification deadline");
    need(cfg.schema === "conway99.f0.recorded-triangle-capacity-literal-configuration.v1", "configuration schema");
    equal(cfg.limits, {total_milliseconds:30000, maximum_report_bytes:65536}, "fixed limits");
    const bind = (text, ref) => {
      const bytes = ref.encoding === "base64-gzip" ? codec.base64(text.replace(/\s/g, "")) : codec.utf8(text);
      need(bytes.length === ref.bytes && codec.sha256(bytes) === ref.sha256 && codec.gitBlob(bytes) === ref.git_blob, "binding " + ref.path);
      tick();
      if (ref.encoding === "base64-gzip") {
        const raw = codec.gunzip(bytes);
        need(codec.sha256(raw) === ref.raw_sha256, "gzip raw binding");
        return codec.ascii(raw);
      }
      return text;
    };
    bind(sourceText, cfg.source);
    bind(codecText, cfg.codec);
    const data = {};
    for (const [key, ref] of Object.entries(cfg.inputs)) {
      need(typeof inputs[key] === "string", "missing input " + key);
      const text = bind(inputs[key], ref);
      data[key] = key === "theorem_note" ? text : JSON.parse(text);
    }
    const d = data.domain, ind = data.indicator, mc = data.model_configuration;
    const mr = data.model_root, p = data.proposal, pf = data.proposal_finalization;
    const po = data.proposal_owner, descriptor = data.row_descriptor, review = data.theorem_review;
    need(mr.status === "ROOT_ACCEPTS_COMPLETE_COMBINED_EXTENSIONS_NATIVE_MODEL_AND_INDEPENDENT_COLD", "parent accepted");
    sameRef(mr.configuration, cfg.inputs.model_configuration, "parent configuration");
    sameRef(mc.inputs.domain, cfg.inputs.domain, "accepted domain");
    sameRef(mc.inputs.triangle_inventory, cfg.inputs.indicator, "accepted indicator");
    sameRef(mc.inputs.triangle_literal_root_acceptance, cfg.inputs.triangle_literal_root, "accepted literal");
    need(data.triangle_literal_root.status === "ROOT_ACCEPTS_COMPLETE_SEPARATE_LITERAL_SUPPORT_REPLAY_AND_INDICATOR_BINDINGS", "literal authority");
    need(data.triangle_literal_root.complete_literal_triangle_supports_accepted_for_future_native_preparation === true, "literal support flag");
    need(mr.model_raw_sha256 === cfg.parent_raw_sha256 && mr.model_raw_bytes === 39306083, "parent bytes");
    need(mr.variables === 80730 && mr.rows === 297470, "parent dimensions");
    const L = mc.layout;
    for (const [key, value] of Object.entries({variables:80730, rows:297470, triangle_variable_start:71382, triangle_variables:5364, triangle_and_start:260042, triangle_target_start:281498}))
      need(L[key] === value, "layout " + key);
    need(review.status === "PASS_COMPLETE_MATHEMATICAL_AND_FROZEN_EXTRACTOR_SOURCE_REVIEW_UNRUN", "theorem review");
    sameRef(review.theorem_note, cfg.inputs.theorem_note, "theorem note");
    sameRef(review.accepted_combined_model_root, cfg.inputs.model_root, "theorem parent");
    sameRef(review.configuration, cfg.inputs.producer_configuration, "producer configuration");
    sameRef(p.source, review.source, "proposal source");
    sameRef(po.source, review.source, "failed owner source");
    sameRef(po.configuration, cfg.inputs.producer_configuration, "failed owner configuration");
    sameRef(po.report, cfg.inputs.proposal, "failed owner report");
    sameRef(po.finalization, cfg.inputs.proposal_finalization, "failed owner finalization");
    need(p.configuration_sha256 === cfg.inputs.producer_configuration.sha256, "proposal configuration");
    need(pf.status === "UNACCEPTED_METADATA_FINALIZATION_BUDGET_OVERRUN", "failed finalization preserved");
    need(pf.report_sha256 === cfg.inputs.proposal.sha256 && pf.report_bytes === cfg.inputs.proposal.bytes, "failed report binding");
    need(pf.total_milliseconds > pf.maximum_milliseconds && pf.maximum_milliseconds === 10000, "failed finalization bound");
    need(po.status === "UNACCEPTED_TRIANGLE_CAPACITY_METADATA_EXECUTION" && po.report_accepted === false && po.within_budget === false, "failed owner preserved");
    need(po.elapsed_milliseconds > po.maximum_milliseconds && po.maximum_milliseconds === 10000 && po.worker_invocations === 1 && po.automatic_retries === 0, "failed owner counts");
    sameRef(descriptor.report, cfg.inputs.proposal, "descriptor proposal");
    sameRef(descriptor.owner, cfg.inputs.proposal_owner, "descriptor owner");
    sameRef(descriptor.finalization, cfg.inputs.proposal_finalization, "descriptor finalization");
    need(descriptor.original_run_accepted === false && descriptor.overrun_waived_or_relabelled === false, "descriptor no waiver");
    need(ind.status === "PASS_EXACT_SHARED_TRIANGLE_INDICATOR_INVENTORY" && ind.triangles.length === 5364 && ind.targets.length === 84, "indicator inventory");
    need(d.signature_domain.length === 480 && d.possible_neighbor_signature_ids.length === 480 && d.component_adjacency_rows.length === 18, "saved domain dimensions");
    const signatures = d.signature_domain, neighbors = d.possible_neighbor_signature_ids, edges = [], edgeIndex = new Map();
    const neighborSets = neighbors.map(list => new Set(list));
    for (let a = 0; a < 480; a++) {
      need(neighborSets[a].size === neighbors[a].length, "duplicate saved neighbor");
      equal(neighbors[a], neighbors[a].slice().sort((x,y) => x-y), "neighbor order");
      for (const b of neighbors[a]) {
        need(Number.isInteger(b) && b >= 0 && b < 480 && b !== a && neighborSets[b].has(a), "saved neighbor reciprocity");
        if (a < b) { edgeIndex.set(a + "," + b, edges.length); edges.push([a,b]); }
      }
    }
    need(edges.length === 68394 && digest(edges) === "411052a41a473bb7199fe277516fb60c54018dec120309622a499229579791bb", "complete original saved edge order");
    const k0 = signatures.map((h, a) => {
      need(h.length === 3 && h.every((v,i) => Number.isInteger(v) && v >= 0 && v < 18 && (i === 0 || h[i-1] < v)), "signature " + a);
      let n = 0;
      for (let i = 0; i < 3; i++) for (let j = i+1; j < 3; j++) n += (d.component_adjacency_rows[h[i]] >> h[j]) & 1;
      need(n === 0 || n === 1, "signature internal matching");
      return n;
    });
    for (let i = 0; i < 18; i++) need(d.component_adjacency_rows[i] === (d.component_core_rows[i+3] >> 3), "core row identity");
    const incidence = new Map(), local = Array.from({length:480}, () => []), triangleKeys = new Set();
    for (let t = 0; t < 5364; t++) {
      const tri = ind.triangles[t], v = tri.vertices;
      need(tri.triangle_index === t && v.length === 3 && v[0] < v[1] && v[1] < v[2] && v.every(x => Number.isInteger(x) && x >= 0 && x < 480), "triangle order");
      need(!triangleKeys.has(v.join(",")), "duplicate triangle"); triangleKeys.add(v.join(","));
      need(tri.origins.length === 1, "unique target origin");
      const pairs = [[v[0],v[1]], [v[0],v[2]], [v[1],v[2]]];
      const ids = pairs.map(pair => edgeIndex.get(pair.join(",")));
      need(ids.every(Number.isInteger), "triangle saved edge membership");
      equal(ids, tri.edge_ids, "triangle original edge IDs");
      for (let i = 0; i < 3; i++) {
        const [a,b] = pairs[i], eid = ids[i], third = v.find(x => x !== a && x !== b);
        need(!signatures[a].some(x => signatures[b].includes(x)), "triangle disjoint signatures");
        if (!incidence.has(eid)) incidence.set(eid, {edge_id:eid, endpoints:[a,b], triangle_indices:[], thirds:[], and_upper_native_rows:[]});
        const rec = incidence.get(eid);
        equal(rec.endpoints, [a,b], "edge endpoint consistency");
        rec.triangle_indices.push(t); rec.thirds.push(third); rec.and_upper_native_rows.push(260042 + 4*t + i);
      }
      for (const a of v) local[a].push(t);
      if ((t & 255) === 0) tick();
    }
    const targetMap = new Map();
    for (let i = 0; i < ind.targets.length; i++) {
      const target = ind.targets[i], rec = incidence.get(target.edge_id);
      need(rec && !targetMap.has(target.edge_id) && (i === 0 || ind.targets[i-1].edge_id < target.edge_id), "target order");
      equal(target.endpoints, rec.endpoints, "target endpoints");
      equal(target.triangle_indices, rec.triangle_indices, "complete target indicator set");
      for (const t of rec.triangle_indices) need(ind.triangles[t].origins[0].target_edge_id === target.edge_id, "target origin");
      targetMap.set(target.edge_id, i);
    }
    need(incidence.size === 6300 && targetMap.size === 84, "complete edge count");
    const allEdges = [...incidence.values()].sort((a,b) => a.edge_id-b.edge_id), sideKeys = [], sideRecords = [];
    let singleton = 0, sideTerms = 0;
    for (const rec of allEdges) {
      need(new Set(rec.thirds).size === rec.thirds.length, "distinct edge thirds");
      if (targetMap.has(rec.edge_id)) {
        rec.disposition = "existing_target_equality";
        rec.existing_target_native_row = 281498 + targetMap.get(rec.edge_id);
      } else if (rec.triangle_indices.length === 1) {
        rec.disposition = "existing_singleton_AND_upper"; singleton++;
      } else {
        rec.disposition = "proposed_side_capacity"; rec.proposal_index = sideKeys.length;
        const key = [-1,0,[[540+rec.edge_id,-1], ...rec.triangle_indices.map(t => [71382+t,1])]];
        const row = p.side_capacity_proposals[sideKeys.length];
        need(row, "missing side proposal");
        equal([row.edge_id,row.endpoints,row.triangle_indices,row.third_selectors,row.proposed_native_row_key],
              [rec.edge_id,rec.endpoints,rec.triangle_indices,rec.thirds,key], "complete side row and origins");
        sideKeys.push(key); sideTerms += key[2].length;
        sideRecords.push([rec.edge_id,rec.endpoints,rec.triangle_indices,rec.thirds,key]);
      }
    }
    equal(allEdges, p.complete_edge_incidence, "all complete edge incidence records");
    need(sideKeys.length === 2904 && p.side_capacity_proposals.length === 2904 && singleton === 3312 && sideTerms === 10320, "side counts");
    const localKeys = [], localRecords = [], empty = []; let localTerms = 0;
    for (let a = 0; a < 480; a++) {
      const list = local[a];
      if (!list.length) { empty.push(a); continue; }
      const cap = 2+k0[a], key = [-cap,0,[[a,-cap], ...list.map(t => [71382+t,1])]];
      const row = p.local_capacity_proposals[localKeys.length];
      need(row, "missing local proposal");
      equal([row.selector,row.k0,row.triangle_indices,row.proposed_native_row_key,row.original_degree_native_row,row.overlap_one_mixed_native_rows,row.overlap_one_degree_coefficient,row.overlap_zero_degree_coefficient],
            [a,k0[a],list,key,153950+a,signatures[a].map(i => 154430+18*a+i),3-2*k0[a],5+2*k0[a]], "complete local row and origins");
      localKeys.push(key); localTerms += key[2].length;
      localRecords.push([a,k0[a],list,key,153950+a,signatures[a].map(i => 154430+18*a+i)]);
    }
    equal(empty, p.local_empty_tautologies, "all empty local dispositions");
    need(localKeys.length === 420 && p.local_capacity_proposals.length === 420 && empty.length === 60 && localTerms === 16512, "local counts");
    const keys = sideKeys.concat(localKeys);
    for (const key of keys) {
      need(Number.isSafeInteger(key[0]) && key[1] === 0, "integer row bounds");
      need(key[2].every((term,i) => term.length === 2 && Number.isSafeInteger(term[0]) && term[0] >= 0 && term[0] < 80730 && Number.isSafeInteger(term[1]) && term[1] !== 0 && (i === 0 || key[2][i-1][0] < term[0])), "complete integer row terms");
    }
    const hashes = {row_keys_sha256:digest(keys), side_row_keys_sha256:digest(sideKeys), local_row_keys_sha256:digest(localKeys),
      complete_edge_incidence_sha256:digest(allEdges), side_records_sha256:digest(sideRecords), local_records_sha256:digest(localRecords), local_empty_sha256:digest(empty)};
    need(hashes.row_keys_sha256 === descriptor.row_keys_sha256 && hashes.side_row_keys_sha256 === descriptor.family_row_keys_sha256.side_edge && hashes.local_row_keys_sha256 === descriptor.family_row_keys_sha256.local_selector && hashes.complete_edge_incidence_sha256 === descriptor.complete_edge_incidence_sha256, "all descriptor digests");
    tick();
    const report = {schema:"conway99.f0.recorded-triangle-capacity-literal-replay.v1", status:"PASS_COMPLETE_INDEPENDENT_RECORDED_TRIANGLE_CAPACITY_ROWS",
      source:cfg.source, configuration_sha256:codec.sha256(codec.utf8(configurationText)), input_bindings:cfg.inputs,
      parent_raw_sha256:cfg.parent_raw_sha256, parent_variables:80730, parent_rows:297470,
      saved_original_neighbor_rows_checked:480, saved_original_edge_order_checked:68394, accepted_triangles_checked:5364,
      complete_edge_incidences_checked:6300, existing_target_equalities_checked:84, existing_singleton_AND_origins_checked:3312,
      side_rows_checked:2904, local_rows_checked:420, empty_local_dispositions_checked:60,
      new_variables:0, appended_rows:3324, appended_terms:26832, resulting_rows:300794,
      family_order:["side_edge","local_selector"], family_row_counts:{side_edge:2904,local_selector:420}, family_term_counts:{side_edge:10320,local_selector:16512},
      hashes, every_proposed_native_key_and_origin_compared:true, failed_producer_execution_accepted:false,
      failed_producer_finalization_milliseconds:pf.total_milliseconds, failed_producer_owner_milliseconds:po.elapsed_milliseconds,
      failed_producer_overrun_waived:false, producer_source_executed:false, redundancy_audit_repeated:false,
      redundancy_claims_accepted_by_this_report:false, proposal_used_only_after_independent_row_derivation:true,
      native_model_messages_decoded:false, future_complete_independent_native_replay_required:true,
      new_domain_or_triangle_census_calls:0, native_model_builds:0, optimizer_calls:0, graph_constructed:false, whole_component_excluded:false,
      replay_milliseconds:Date.now()-started, maximum_milliseconds:cfg.limits.total_milliseconds};
    const reportText = json(report)+"\n", reportBytes = codec.utf8(reportText);
    need(reportBytes.length <= cfg.limits.maximum_report_bytes, "report bound");
    const reportSHA = codec.sha256(reportBytes);
    tick();
    const finalization = {schema:"conway99.f0.recorded-triangle-capacity-literal-finalization.v1",
      status:"PASS_COMPLETE_SERIALIZATION_WITHIN_DECLARED_BOUND", report_bytes:reportBytes.length, report_sha256:reportSHA,
      total_milliseconds:Date.now()-started, maximum_milliseconds:cfg.limits.total_milliseconds,
      original_failed_producer_remains_unaccepted:true, optimizer_calls:0};
    const finalizationText = json(finalization)+"\n";
    tick();
    return {reportText, finalizationText};
  }
  return {run};
})
