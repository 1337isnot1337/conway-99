(() => {
"use strict";
function run(configurationText,payload,codecText,checkerText){
 const start=Date.now(),out={report:null,text:null,finalization:null};
 let cfg=null;
 try{
  const c=eval(codecText);
  function bytes(s){const b=new Uint8Array(s.length);for(let i=0;i<s.length;i++){const v=s.charCodeAt(i);c.check(v<128,"ASCII bound input");b[i]=v;}return b;}
  c.check(c.sha256(bytes(configurationText))==="33db79538313dd72695ca4a5940e5501c200bd04c40955a6787cef23820d6cc1","frozen artifact configuration");
  cfg=JSON.parse(configurationText);
  function textBinding(s,ref){const b=bytes(s);c.check(b.length===ref.bytes&&c.sha256(b)===ref.sha256&&c.gitBlob(b)===(ref.git_blob||ref.git_blob_sha),"exact bound text "+ref.path);return JSON.parse(s);}
  for(const [s,ref] of [[codecText,cfg.codec],[checkerText,cfg.source]]){const b=bytes(s);c.check(b.length===ref.bytes&&c.sha256(b)===ref.sha256&&c.gitBlob(b)===(ref.git_blob||ref.git_blob_sha),"exact implementation");}
  const loaded={};
  for(const [name,ref] of Object.entries(cfg.texts))loaded[name]=textBinding(payload[name],ref);
  for(const [name,ref] of Object.entries(cfg.archives)){
   const archive=c.base64(payload[name]);
   c.check(archive.length===ref.archive_bytes&&c.sha256(archive)===ref.archive_sha256&&c.gitBlob(archive)===ref.archive_git_blob,"archive binding "+name);
   const raw=c.gunzip(archive);
   c.check(raw.length===ref.raw_bytes&&c.sha256(raw)===ref.raw_sha256,"raw binding "+name);
   loaded[name]=JSON.parse(c.ascii(raw));
  }
  c.check(loaded.finalization.status==="COMPLETE_FORWARD_AND_SERIALIZATION_WITHIN_DECLARED_BOUNDS"&&loaded.finalization.complete_within_declared_bounds===true&&loaded.finalization.report.sha256===cfg.texts.report.sha256,"successful completed report");
  const parent=loaded.parent_cold;
  c.check(parent.status==="PASS_INDEPENDENT_COMPLETE_BOOLEAN_SHARED_MODEL"&&parent.native_raw_model_sha256===cfg.original_parent_raw_sha256&&parent.inventory.rows===168050&&parent.inventory.mixed_rows===8640&&parent.complete_parent_bytes_checked===true,"accepted original native mixed-row premises");
  c.check(loaded.source_review.status==="PASS_COMPLETE_ARTIFACT_REPLAY_SOURCE_REVIEW"&&loaded.source_review.source.sha256===cfg.source.sha256,"independent source review");
  const checker=eval(checkerText),controls=checker.controls();
  c.check(JSON.stringify(controls)===JSON.stringify(loaded.controls),"actual controls receipt");
  out.report=checker.verify(loaded.report,loaded.domain,loaded.overlay,s=>c.sha256(bytes(s)));
  out.text=JSON.stringify(out.report)+"\n";
  bytes(out.text);
  const elapsed=Date.now()-start;
  c.check(out.text.length<=cfg.maximum_report_bytes&&elapsed<cfg.maximum_outer_ms,"complete replay and serialization outer bounds");
  const r=out.report;
  c.check(r.status==="PASS_EVERY_ORIGINAL_ROW_ORIGIN_AND_MIXED_LINEAR_CERTIFICATE"&&r.complete_original_rows===cfg.expected_original_rows&&r.complete_original_cases===cfg.expected_original_cases&&r.complete_coefficients_checked_for_certificates===cfg.expected_certificate_count&&r.rows_implied_by_two_original_mixed_equations===cfg.expected_deleted_rows&&r.retained_rows===cfg.expected_retained_rows&&r.retained_row_ids_sha256===cfg.expected_retained_id_sha256,"all required complete certificate results");
  out.finalization={schema:"conway99.f0.four-exterior-cross-quota-certificate-finalization.v1",status:"PASS_COMPLETE_ARTIFACT_REPLAY_AND_SERIALIZATION_WITHIN_BOUND",configuration_sha256:"33db79538313dd72695ca4a5940e5501c200bd04c40955a6787cef23820d6cc1",source:cfg.source,report_sha256_to_be_bound_after_timed_main:true,seconds:elapsed/1000,maximum_ms:cfg.maximum_outer_ms,serialized_report_bytes:out.text.length,all_input_bytes_reverified:true,publication_hashes_outside_main:true,optimizer_calls:0,native_model_builds:0,automatic_retries:0};
 }catch(error){
  out.finalization={schema:"conway99.f0.four-exterior-cross-quota-certificate-finalization.v1",status:"UNACCEPTED_ARTIFACT_REPLAY_FAILURE_NO_AUTOMATIC_RETRY",error:String(error),seconds:(Date.now()-start)/1000,complete_candidate_preserved:out.report!==null,serialized_candidate_preserved:out.text!==null,optimizer_calls:0,native_model_builds:0,automatic_retries:0};
 }
 return out;
}
return {run};
})()