(() => {
"use strict";
function run(source,codecSource,configuration,encodedDomain,encodedOverlay){
 const start=Date.now(),c=eval(codecSource),receipts=[];
 function bindText(text,entry){const bytes=c.utf8(text);c.check(bytes.length===entry.bytes&&c.sha256(bytes)===entry.sha256&&c.gitBlob(bytes)===entry.git_blob,"text identity "+entry.path);}
 bindText(source,configuration.source);bindText(codecSource,configuration.codec);
 function decode(encoded,identity){
  const archive=c.base64(encoded);
  c.check(archive.length===identity.archive_bytes&&c.sha256(archive)===identity.archive_sha256&&c.gitBlob(archive)===identity.archive_git_blob,"archive identity "+identity.path);
  const raw=c.gunzip(archive,configuration.limits.serialized_report_bytes);
  c.check(raw.length===identity.raw_bytes&&c.sha256(raw)===identity.raw_sha256,"raw identity "+identity.path);
  receipts.push({...identity,archive_and_raw_reverified:true});
  return JSON.parse(c.ascii(raw));
 }
 const domain=decode(encodedDomain,configuration.inputs[0]),overlay=decode(encodedOverlay,configuration.inputs[1]);
 const report=eval(source).run(domain,overlay,text=>c.sha256(c.utf8(text)));
 const text=JSON.stringify(report)+"\n";
 c.check(text.length<=configuration.limits.serialized_report_bytes,"serialized report byte bound");
 const bytes=new Uint8Array(text.length);
 for(let i=0;i<text.length;i++){const x=text.charCodeAt(i);c.check(x<128,"ASCII report");bytes[i]=x;}
 const sha256=c.sha256(bytes),git_blob=c.gitBlob(bytes),seconds=(Date.now()-start)/1000;
 c.check(seconds*1000<configuration.limits.wrapper_ms,"wrapper deadline including finalization");
 return {report,text,receipt:{schema:"conway99.f0.four-exterior-cross-quota-finalization.v1",status:"COMPLETE_WITHIN_SOURCE_BOUND_LIMITS",source:configuration.source,codec:configuration.codec,inputs:receipts,report:{bytes:bytes.length,sha256,git_blob},seconds,limits:configuration.limits,optimizer_calls:0,native_model_builds:0,whole_component_excluded:false}};
}
return {run};
})()