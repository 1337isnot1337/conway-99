(() => {
"use strict";
function run(source,codecSource,configuration,encodedInputs){
 const start=Date.now(),c=eval(codecSource),result={report:null,text:null,finalization:null},receipts=[];
 function bindText(text,entry){const b=c.utf8(text);c.check(b.length===entry.bytes&&c.sha256(b)===entry.sha256&&c.gitBlob(b)===entry.git_blob,"text identity "+entry.path);}
 try{
  bindText(source,configuration.source);bindText(codecSource,configuration.codec);
  const decoded=configuration.inputs.map((identity,index)=>{
   const archive=c.base64(encodedInputs[index]);
   c.check(archive.length===identity.archive_bytes&&c.sha256(archive)===identity.archive_sha256&&c.gitBlob(archive)===identity.archive_git_blob,"archive identity "+identity.path);
   const raw=c.gunzip(archive,configuration.limits.maximum_input_raw_bytes);
   c.check(raw.length===identity.raw_bytes&&c.sha256(raw)===identity.raw_sha256,"raw identity "+identity.path);
   receipts.push({...identity,archive_and_raw_reverified:true});
   return JSON.parse(c.ascii(raw));
  });
  result.report=eval(source).run(decoded[0],decoded[1],decoded[2],text=>c.sha256(c.utf8(text)));
  result.text=JSON.stringify(result.report)+"\n";
  c.check(result.text.length<=configuration.limits.maximum_report_bytes,"serialized report bound");
  for(let i=0;i<result.text.length;i++)c.check(result.text.charCodeAt(i)<128,"ASCII report byte count");
  const seconds=(Date.now()-start)/1000;
  c.check(seconds*1000<configuration.limits.wrapper_ms,"wrapper deadline");
  result.finalization={schema:"conway99.f0.spectral-gap-pair-finalization.v1",status:"COMPLETE_WITHIN_CENSUS_SERIALIZATION_AND_BYTE_LIMITS",seconds,serialized_bytes:result.text.length,inputs:receipts,source:configuration.source,limits:configuration.limits,publication_hashing_in_timed_main:false,optimizer_calls:0,native_model_builds:0,whole_component_excluded:false};
 }catch(error){
  result.finalization={schema:"conway99.f0.spectral-gap-pair-finalization.v1",status:"UNACCEPTED_FAILURE_NO_AUTOMATIC_RETRY",error:String(error),seconds:(Date.now()-start)/1000,complete_report_returned:result.report!==null,serialized_report_retained:result.text!==null,inputs:receipts,source:configuration.source,limits:configuration.limits,optimizer_calls:0,native_model_builds:0,whole_component_excluded:false};
 }
 return result;
}
return {run};
})()