(() => {
"use strict";
const MAX_MS=45000;
function assert(ok,label){if(!ok)throw Error(label);}
function reference(a,b,label){
  assert(a && b && a.path===b.path && a.sha256===b.sha256,"reference "+label);
  if(a.bytes!==undefined && b.bytes!==undefined)assert(a.bytes===b.bytes,"bytes "+label);
}
function run(args,C,preserve){
  const started=Date.now();
  const owner={schema:"conway99.f0.recorded-triangle-spectral-gap-independent-literal-owner.v1",
    status:"UNACCEPTED_INDEPENDENT_TRIANGLE_GAP_LITERAL_OWNER",mode:"replay",
    accepted:false,report_accepted:false,worker_invocations:0,worker_returned:false,
    worker_maximum_ms:30000,outer_maximum_ms:MAX_MS,automatic_retries:0,
    exact_return_texts_preserved_before_publication:false,outer_started_before_factory_evaluation:true,
    optimizer_calls:0,native_model_builds:0,native_model_changes:0,
    OS_child_constructed:false,hard_OS_preemption_claimed:false,refs_mutated:false,
    graph_constructed:false,whole_component_excluded:false};
  let result=null;
  const bytes=s=>C.utf8(s),sha=b=>C.sha256(b);
  function identity(text,ref,label){
    const raw=bytes(text);
    assert(raw.length===ref.bytes && sha(raw)===ref.sha256,"binding "+label);
    if(ref.git_blob)assert(C.gitBlob(raw)===ref.git_blob,"Git binding "+label);
    return {path:ref.path,bytes:raw.length,sha256:sha(raw)};
  }
  try{
    assert(typeof preserve==="function","preservation callback");
    const cfg=JSON.parse(args.configuration_text),gate=JSON.parse(args.gate_text);
    identity(args.source_text,cfg.source,"worker source");
    identity(args.codec_text,cfg.codec,"codec");
    const configRef=identity(args.configuration_text,gate.configuration,"configuration");
    assert(configRef.path===cfg.configuration_path,"configuration path");
    identity(args.gate_text,args.gate_ref,"root gate");
    identity(args.wrapper_text,gate.wrapper_source,"outer wrapper");
    identity(args.peer_review_text,args.peer_review_ref,"peer review");
    reference(gate.peer_review,args.peer_review_ref,"peer review gate");
    reference(gate.source,cfg.source,"worker gate");
    reference(gate.codec,cfg.codec,"codec gate");
    assert(gate.schema==="conway99.f0.recorded-triangle-spectral-gap-independent-literal-root-gate.v1" &&
      gate.status==="AUTHORIZE_ONE_COMPLETE_INDEPENDENT_RECORDED_TRIANGLE_GAP_LITERAL_REPLAY",
      "root authorization");
    assert(gate.exact_worker_invocations===1 && gate.automatic_retries===0 &&
      gate.optimizer_calls===0 && gate.native_model_changes_authorized===false,"one non-native call");
    assert(gate.limits.worker_milliseconds===30000 && gate.limits.outer_milliseconds===45000 &&
      gate.limits.maximum_report_bytes===65536 && gate.limits.automatic_retries===0,"outer root limits");
    const peer=JSON.parse(args.peer_review_text);
    assert(typeof peer.status==="string" && peer.status.startsWith("PASS_"),"successful peer source review");
    owner.source=cfg.source;owner.configuration=configRef;owner.root_gate=args.gate_ref;
    owner.independent_source_review=args.peer_review_ref;owner.wrapper_source=gate.wrapper_source;
    owner.forward_report=cfg.inputs.forward_report;owner.forward_finalization=cfg.inputs.forward_finalization;
    owner.forward_owner=cfg.inputs.forward_owner;
    const worker=eval(args.source_text);
    assert(worker && typeof worker.replay==="function","worker entry");
    owner.worker_invocations=1;
    result=worker.replay(args.payload,args.configuration_text,args.source_text,args.codec_text,C);
    owner.worker_returned=true;
    assert(result && typeof result.report_text==="string" && typeof result.finalization_text==="string","exact output texts");
    preserve("report",result.report_text);
    preserve("finalization",result.finalization_text);
    owner.exact_return_texts_preserved_before_publication=true;
    owner.texts_preserved_at_elapsed_ms=Date.now()-started;
    const report=JSON.parse(result.report_text),final=JSON.parse(result.finalization_text);
    const reportBytes=bytes(result.report_text),finalBytes=bytes(result.finalization_text);
    const reportRef={path:cfg.outputs.report,bytes:reportBytes.length,sha256:sha(reportBytes)};
    const finalRef={path:cfg.outputs.finalization,bytes:finalBytes.length,sha256:sha(finalBytes)};
    owner.report=reportRef;owner.finalization=finalRef;owner.worker_status=final.status;
    owner.worker_elapsed_through_report_hash_ms=final.elapsed_through_report_hash_ms;
    assert(report.schema==="conway99.f0.recorded-triangle-spectral-gap-independent-literal-replay.v1" &&
      report.status==="PASS_COMPLETE_INDEPENDENT_RECORDED_TRIANGLE_GAP_LITERAL_REPLAY" &&
      report.complete===true && report.records_verified===5364 &&
      report.all_5364_records_independently_verified===true &&
      report.all_seven_minors_per_record_independently_recomputed===true,"complete worker result");
    reference(report.source,cfg.source,"result source");
    reference(report.configuration,configRef,"result configuration");
    reference(report.forward_report,cfg.inputs.forward_report,"result forward report");
    assert(report.failed_count===3156 && report.failed_triangle_indices.length===3156 &&
      report.optimizer_calls===0 && report.native_imports===0 && report.native_model_built===false &&
      report.native_model_modified===false && report.forward_source_imported_or_executed===false,
      "complete non-native result");
    assert(final.schema==="conway99.f0.recorded-triangle-spectral-gap-independent-literal-finalization.v1" &&
      final.status==="PASS_COMPLETE_INDEPENDENT_RECORDED_TRIANGLE_GAP_REPLAY_AND_FINALIZATION" &&
      final.accepted===true && final.within_declared_bounds===true && final.report_complete===true,
      "accepted finalization");
    assert(final.report_sha256===reportRef.sha256 && final.report_bytes===reportRef.bytes &&
      final.maximum_ms===30000 && final.maximum_report_bytes===65536 &&
      final.elapsed_through_report_hash_ms>=0 && final.elapsed_through_report_hash_ms<=30000 &&
      reportRef.bytes<=65536 && final.automatic_retries===0,"worker complete bound");
    if(final.elapsed_after_first_finalization_serialization_ms!==undefined)
      assert(final.elapsed_after_first_finalization_serialization_ms>=0 &&
        final.elapsed_after_first_finalization_serialization_ms<=30000,"worker final serialization bound");
    owner.complete_case_records=5364;owner.failed_count=3156;
    owner.status="OWNED_COMPLETE_INDEPENDENT_RECORDED_TRIANGLE_GAP_LITERAL_REPLAY_ACCEPTED";
    owner.accepted=true;owner.report_accepted=true;owner.error=null;
  }catch(error){
    owner.status="UNACCEPTED_INDEPENDENT_TRIANGLE_GAP_LITERAL_OWNER";
    owner.accepted=false;owner.report_accepted=false;
    owner.error={type:error && error.name || "Error",message:String(error && error.message || error)};
  }
  owner.outer_elapsed_ms=Date.now()-started;
  if(owner.outer_elapsed_ms<0 || owner.outer_elapsed_ms>MAX_MS){
    owner.status="UNACCEPTED_INDEPENDENT_TRIANGLE_GAP_LITERAL_OWNER";
    owner.accepted=false;owner.report_accepted=false;
  }
  let ownerText=JSON.stringify(owner)+"\n";
  const serializationElapsed=Date.now()-started;
  owner.outer_elapsed_through_first_owner_serialization_ms=serializationElapsed;
  if(serializationElapsed<0 || serializationElapsed>MAX_MS){
    owner.status="UNACCEPTED_INDEPENDENT_TRIANGLE_GAP_LITERAL_OWNER";
    owner.accepted=false;owner.report_accepted=false;
  }
  ownerText=JSON.stringify(owner)+"\n";
  preserve("owner",ownerText);
  return {report_text:result && result.report_text,finalization_text:result && result.finalization_text,owner_text:ownerText};
}
return {run};
})()
