(() => {
"use strict";
function run(configurationText,payload,sourceText,codecText){
 const started=Date.now(),out={report:null,text:null,finalization:null};
 try{
  const c=eval(codecText),cfg=JSON.parse(configurationText),rawCfg=c.utf8(configurationText);
  c.check(c.sha256(rawCfg)==="acd44d5d8bf04035177d632df84507f6d4cb4266b8ef0b71591bdcf2839c1144","frozen root literal configuration");
  function bound(s,ref){const b=c.utf8(s);c.check(b.length===ref.bytes&&c.sha256(b)===ref.sha256&&c.gitBlob(b)===ref.git_blob,"exact literal text binding");return s;}
  bound(sourceText,cfg.source);bound(codecText,cfg.codec);
  const data={};
  for(const [name,ref] of Object.entries(cfg.texts))data[name]=JSON.parse(bound(payload[name],ref));
  for(const [name,ref] of Object.entries(cfg.archives)){
   const archive=c.base64(payload[name]);c.check(archive.length===ref.archive_bytes&&c.sha256(archive)===ref.archive_sha256&&c.gitBlob(archive)===ref.archive_git_blob,"exact archive binding");
   const raw=c.gunzip(archive);c.check(raw.length===ref.raw_bytes&&c.sha256(raw)===ref.raw_sha256,"exact raw binding");
   data[name]=JSON.parse(c.ascii(raw));
  }
  c.check(data.finalization.status==="PASS_ALL_PROVIDED_CERTIFICATES_AND_COMPLETE_SERIALIZATION_WITHIN_BOUND"&&data.finalization.seconds*1000<60000&&data.finalization.serialized_report_bytes===cfg.texts.report.bytes,"producer complete terminal acceptance");
  c.check(data.report.source_sha256==="db1d0956b261e2dd10b69f70f104bdbb8cd055ad49c039583fdec67aeda9bca3"&&data.report.configuration_sha256==="a42abc4489fcc8738539ffa05a24eeb4eb0d1f8fd5d9ab7b31716ea52678f4d4","accepted producer bindings");
  const checker=eval(sourceText);c.check(JSON.stringify(checker.controls())===JSON.stringify(cfg.controls),"four exact independent controls");
  out.report=checker.verify(data.report,data.domain,data.kernels,data.overlay,s=>c.sha256(c.utf8(s)));
  out.text=JSON.stringify(out.report)+"\n";const bytes=c.utf8(out.text),elapsed=Date.now()-started;
  c.check(elapsed<cfg.maximum_outer_ms&&bytes.length<=1048576,"literal replay serialization bounds");
  c.check(out.report.status==="PASS_ALL_252_LITERAL_NEGATIVE_QUADRATIC_CERTIFICATES_AND_NATIVE_KEYS"&&out.report.certificates===cfg.expected_certificates&&out.report.rows===cfg.expected_rows&&out.report.row_keys_sha256===cfg.expected_row_keys_sha256,"all provided signed rows");
  out.finalization={schema:"conway99.f0.signed-literal-root-replay-finalization.v1",status:"PASS_LITERAL_REPLAY_AND_SERIALIZATION_WITHIN_BOUND",configuration_sha256:c.sha256(rawCfg),seconds:elapsed/1000,maximum_ms:cfg.maximum_outer_ms,serialized_bytes:bytes.length,all_raw_inputs_reverified:true,publication_hashing_outside_main:true,automatic_retries:0,optimizer_calls:0,native_model_builds:0};
 }catch(error){out.finalization={schema:"conway99.f0.signed-literal-root-replay-finalization.v1",status:"UNACCEPTED_LITERAL_REPLAY_FAILURE_NO_AUTOMATIC_RETRY",error:String(error),seconds:(Date.now()-started)/1000,complete_candidate_preserved:out.report!==null,serialized_candidate_preserved:out.text!==null,automatic_retries:0,optimizer_calls:0,native_model_builds:0};}
 return out;
}
return {run};
})()