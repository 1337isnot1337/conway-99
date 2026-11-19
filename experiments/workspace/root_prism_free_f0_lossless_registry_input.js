"use strict";
/* Lossless read of fixed, Python-parsed integer-only registry bytes.
   All historical hashes use Python's sorted ensure_ascii integer JSON.
   No mathematical model, optimizer or graph restriction is introduced. */
const fs=require("fs"),path=require("path"),crypto=require("crypto"),zlib=require("zlib");
const check=(ok,message)=>{if(!ok)throw new Error(message);};
const sha=x=>crypto.createHash("sha256").update(x).digest("hex");
const TAG="__f0_exact_json_integer__",MAX=9007199254740991n;
const bindings={
  converter:"795836b0bff4e9ad55e1e2c44954d719058fcaec81e0a84dbd9fb668dafdcff2",
  transfer:"c990af1c45cd9683110ee293cb0f13f741a4ed96c16641dae18f3d521708b5a3",
  individual:"6acd86b609230632c42b345ba0d1742ca3a3155cf216271f74508acaa71f1e41",
  shared:"6ea36f93085ab07e641e5148fb9a297b9d9bdd9abd6ff36922fde5f112ccd71d",
  quadratic:"29610083a8ce62eca87fb53e9cadbcdc5cca94cb8c24952a213cc19e876a8871"
};
function statistics(){return {integer_values:0,tagged_large_integers:0,maximum_integer_bits:0};}
function tally(value,count,tagged){
  count.integer_values++;if(tagged)count.tagged_large_integers++;
  const a=value<0n?-value:value;
  count.maximum_integer_bits=Math.max(count.maximum_integer_bits,a===0n?0:a.toString(2).length);
}
function decodeWire(value,count=statistics()){
  if(value===null||typeof value==="string"||typeof value==="boolean")return value;
  if(typeof value==="number"){
    check(Number.isSafeInteger(value),"wire Number must be a safe integer");
    tally(BigInt(value),count,false);return value;
  }
  if(Array.isArray(value))return value.map(x=>decodeWire(x,count));
  check(value&&typeof value==="object","wire value type");
  if(Object.hasOwn(value,TAG)){
    check(Object.keys(value).length===1,"integer tag must be a singleton object");
    const text=value[TAG];
    check(typeof text==="string"&&/^(0|-?[1-9][0-9]*)$/.test(text),"canonical tagged integer");
    const number=BigInt(text);
    check(number>MAX||number<-MAX,"only unsafe integers receive tags");
    tally(number,count,true);return number;
  }
  return Object.fromEntries(Object.keys(value).map(key=>[key,decodeWire(value[key],count)]));
}
function codePointOrder(a,b){
  const x=Array.from(a,c=>c.codePointAt(0)),y=Array.from(b,c=>c.codePointAt(0));
  for(let i=0;i<Math.min(x.length,y.length);i++)if(x[i]!==y[i])return x[i]-y[i];
  return x.length-y.length;
}
function pythonString(value){
  return JSON.stringify(value).replace(/[\u007f-\uffff]/g,c=>"\\u"+c.charCodeAt(0).toString(16).padStart(4,"0"));
}
function pythonCanonical(value){
  if(value===null)return "null";
  if(typeof value==="string")return pythonString(value);
  if(typeof value==="boolean")return value?"true":"false";
  if(typeof value==="bigint")return value.toString();
  if(typeof value==="number"){
    check(Number.isSafeInteger(value),"historical Number must be a safe integer");
    return BigInt(value).toString();
  }
  if(Array.isArray(value))return "["+value.map(pythonCanonical).join(",")+"]";
  check(value&&typeof value==="object","historical JSON value type");
  return "{"+Object.keys(value).sort(codePointOrder).map(k=>pythonString(k)+":"+pythonCanonical(value[k])).join(",")+"}";
}
const pyHash=value=>sha(pythonCanonical(value));
function controls(saved){
  check(saved.status==="PASS: lossless integer transfer and lexical rejection controls","Python controls status");
  check(saved.fixtures.length===4&&saved.rejected_json_inputs.length===8,"Python control coverage");
  let fixtures=0,rejected=0;
  for(const f of saved.fixtures){
    const count=statistics(),decoded=decodeWire(f.wire,count),actual=pythonCanonical(decoded);
    check(actual===f.expected_python_canonical&&sha(actual)===f.expected_python_canonical_sha256,"literal Python/V8 canonical agreement");
    check(pythonCanonical(count)===pythonCanonical(f.statistics),"fixture exact statistics");fixtures++;
  }
  const invalid=[9007199254740992,1.5,NaN,Infinity,
    {[TAG]:"9007199254740992",extra:0},{[TAG]:"01"},{[TAG]:"-0"},
    {[TAG]:"1e30"},{[TAG]:"1.5"},{[TAG]:9007199254740992},
    {[TAG]:"9007199254740991"},{[TAG]:"-9007199254740991"},{[TAG]:"0"}];
  for(const x of invalid){let failed=false;try{decodeWire(x);}catch(e){failed=true;}check(failed,"bad wire integer refused");rejected++;}
  for(const x of [9007199254740992,1.5,NaN,Infinity,undefined]){
    let failed=false;try{pythonCanonical(x);}catch(e){failed=true;}check(failed,"bad historical numeric input refused");rejected++;
  }
  for(const x of ["1e30","1.5","-9007199254740993","escaped\\quote\""]){
    check(decodeWire(x)===x&&pythonCanonical(x)===pythonString(x),"strings are never interpreted as numbers");
  }
  check(pythonCanonical(-0)==="0","negative integer zero");
  return {status:"PASS: lossless integer decoding and independent Python canonical reproduction",
    literal_cross_language_fixtures:fixtures,invalid_V8_values_rejected:rejected,
    Python_fraction_exponent_nonfinite_or_duplicate_rejections:saved.rejected_json_inputs,
    numeric_looking_strings_preserved:true,escaped_and_Unicode_keys_checked:true,
    large_negative_integers_checked:true,maximum_fixture_integer_bits:201,
    optimizer_called:false};
}
function loadRegistry(root){
  const converter=path.join(__dirname,"root_prism_free_f0_lossless_registry_input.py");
  check(sha(fs.readFileSync(converter))===bindings.converter,"converter source binding");
  const transferPath=path.join(__dirname,"../logs/root-prism-free/f0-boolean-registry-lossless-input.json.gz");
  const raw=fs.readFileSync(transferPath);check(sha(raw)===bindings.transfer,"lossless transfer binding");
  const payload=JSON.parse(zlib.gunzipSync(raw).toString("utf8"));
  check(payload.schema==="f0-lossless-final-registry-input-v1"&&payload.source_sha256===bindings.converter,"transfer schema/source");
  check(payload.integer_tag===TAG&&payload.maximum_untagged_integer===Number(MAX),"tag contract");
  check(payload.raw_registries_modified===false&&payload.mathematical_normalization_performed===false&&payload.optimizer_called===false,"transfer scope");
  const controlReport=controls(payload.controls),result={},inputs={};
  for(const label of ["individual","shared","quadratic"]){
    const entry=payload.inputs[label],original=fs.readFileSync(path.join(root,entry.path));
    check(sha(original)===bindings[label]&&entry.compressed_sha256===bindings[label]&&original.length===entry.compressed_bytes,"raw registry binding "+label);
    const body=zlib.gunzipSync(original);check(sha(body)===entry.uncompressed_sha256&&body.length===entry.uncompressed_bytes,"raw decompressed binding "+label);
    const count=statistics(),decoded=decodeWire(entry.wire,count);
    check(Array.isArray(decoded)&&decoded.length===entry.record_count,"exact registry record count");
    check(pyHash(decoded)===entry.canonical_original_sha256,"lossless historical canonical hash "+label);
    check(pythonCanonical(count)===pythonCanonical(entry.statistics),"all original integer statistics "+label);
    result[label]=decoded;
    inputs[label]={compressed_sha256:bindings[label],uncompressed_sha256:entry.uncompressed_sha256,
      canonical_original_sha256:entry.canonical_original_sha256,record_count:decoded.length,statistics:count};
  }
  result.lossless_report={status:"PASS: fixed raw registries decoded losslessly with exact original canonical hashes",
    reader_source_sha256:sha(fs.readFileSync(__filename)),converter_source_sha256:bindings.converter,
    transfer_file_sha256:bindings.transfer,inputs,controls:controlReport,optimizer_called:false};
  return result;
}
if(require.main===module){
  const args=process.argv.slice(2);check(args.length===2,"RECOVERY_ROOT OUTPUT_JSON");
  const value=loadRegistry(args[0]).lossless_report;
  check(!fs.existsSync(args[1]),"fresh report");
  fs.mkdirSync(path.dirname(args[1]),{recursive:true});
  fs.writeFileSync(args[1],JSON.stringify(value,null,2)+"\n",{flag:"wx"});
  process.stdout.write(JSON.stringify(value,null,2)+"\n");
}
module.exports={decodeWire,pythonCanonical,pyHash,controls,loadRegistry};

