(() => {
"use strict";
function run(configurationText,payload,codecText,sourceText){
 const started=Date.now(),out={report:null,text:null,finalization:null};
 let cfg=null;
 try{
  const codec=eval(codecText),b=codec.utf8(configurationText);
  codec.check(codec.sha256(b)==="a42abc4489fcc8738539ffa05a24eeb4eb0d1f8fd5d9ab7b31716ea52678f4d4","frozen targeted configuration");
  cfg=JSON.parse(configurationText);
  for(const [text,ref] of [[sourceText,cfg.source],[codecText,cfg.codec]]){
   const raw=codec.utf8(text);
   codec.check(raw.length===ref.bytes&&codec.sha256(raw)===ref.sha256&&codec.gitBlob(raw)===ref.git_blob,"frozen targeted implementation");
  }
  out.report=eval(sourceText).run(configurationText,payload,codec,sourceText,codecText);
  out.text=JSON.stringify(out.report)+"\n";
  for(let i=0;i<out.text.length;i++)codec.check(out.text.charCodeAt(i)<128,"ASCII targeted report");
  const seconds=(Date.now()-started)/1000;
  codec.check(out.text.length<=16777216,"targeted report byte bound");
  codec.check(seconds*1000<60000,"targeted outer deadline through complete serialization");
  codec.check(out.report.complete===true&&out.report.status==="PASS_252_PROVIDED_SINGLE_EDGE_PSD_CERTIFICATES"&&out.report.certified_records===252,"all supplied targets proved");
  out.finalization={schema:"conway99.f0.provided-single-edge-schur.finalization.v1",status:"PASS_ALL_PROVIDED_CERTIFICATES_AND_COMPLETE_SERIALIZATION_WITHIN_BOUND",source:cfg.source,configuration_sha256:codec.sha256(b),seconds,serialized_report_bytes:out.text.length,maximum_ms:60000,maximum_report_bytes:16777216,full_pattern_completeness_claimed:false,publication_hashing_in_timed_main:false,optimizer_calls:0,native_model_builds:0,automatic_retries:0};
 }catch(error){
  out.finalization={schema:"conway99.f0.provided-single-edge-schur.finalization.v1",status:"UNACCEPTED_TARGETED_CERTIFICATE_FAILURE_NO_AUTOMATIC_RETRY",error:String(error),source:cfg?cfg.source:null,seconds:(Date.now()-started)/1000,complete_candidate_preserved:out.report!==null,serialized_candidate_preserved:out.text!==null,optimizer_calls:0,native_model_builds:0,automatic_retries:0};
 }
 return out;
}
return {run};
})()