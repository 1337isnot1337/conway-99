"use strict";
// Exact evaluation only. No new reconstruction, optimizer or domain search.
// Node: node rook_case4_gram_native_evaluation.js native-model.json gram-result.json output.json
function sha256Ascii(text) {
  if ([...text].some(c=>c.charCodeAt(0)>127)) throw new Error("ASCII hash input required");
  const k=[0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2];
  let h=[0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19];
  const bytes=Array.from(text,c=>c.charCodeAt(0)), bits=bytes.length*8;
  bytes.push(128); while(bytes.length%64!==56)bytes.push(0);
  for(const part of [Math.floor(bits/4294967296),bits>>>0])for(let s=24;s>=0;s-=8)bytes.push(part>>>s&255);
  const rr=(x,n)=>(x>>>n)|(x<<(32-n));
  for(let off=0;off<bytes.length;off+=64){
    const w=Array(64).fill(0);
    for(let i=0;i<16;i++)w[i]=(bytes[off+4*i]<<24)|(bytes[off+4*i+1]<<16)|(bytes[off+4*i+2]<<8)|bytes[off+4*i+3];
    for(let i=16;i<64;i++){const a=w[i-15],b=w[i-2];w[i]=(w[i-16]+(rr(a,7)^rr(a,18)^(a>>>3))+w[i-7]+(rr(b,17)^rr(b,19)^(b>>>10)))|0;}
    let[a,b,c,d,e,f,g,z]=h;
    for(let i=0;i<64;i++){const t1=(z+(rr(e,6)^rr(e,11)^rr(e,25))+((e&f)^(~e&g))+k[i]+w[i])|0;const t2=((rr(a,2)^rr(a,13)^rr(a,22))+((a&b)^(a&c)^(b&c)))|0;z=g;g=f;f=e;e=(d+t1)|0;d=c;c=b;b=a;a=(t1+t2)|0;}
    h=h.map((v,i)=>(v+[a,b,c,d,e,f,g,z][i])|0);
  }
  return h.map(v=>(v>>>0).toString(16).padStart(8,"0")).join("");
}

function check(ok,msg){if(!ok)throw new Error(msg);}
function evaluateCase4Native(nativeRaw,resultRaw){
  check(sha256Ascii(nativeRaw)==="a9004e97a2d166bf8b162609cfb538eae0dd4d26942b6df5119b6a88d65ec476","native model raw binding");
  check(sha256Ascii(resultRaw)==="0b2f1ac00015b12e612ae29a3f48c67c15d773365152cbc464d3f31f3a37957b","Gram point raw binding");
  const native=JSON.parse(nativeRaw),r=JSON.parse(resultRaw),inv=native.primary_inventory;
  const x=r.numerators.map(BigInt),q=BigInt(r.common_denominator);
  check(q>0n&&x.length===1214&&x.every(v=>v>=0n&&v<=q),"bounded rational point");
  const violations=[],counts={Gram:0,original_signature:0,triple:0,Gram_conflict:0,uncapped_row_cut:0,old_unit:0};
  const sum=members=>members.reduce((s,a)=>{check(Number.isInteger(a)&&a>=0&&a<1214,"column");return s+x[a];},0n);
  function capacity(family,index,label,lhs,rhs){
    counts[family]++;
    if(lhs>rhs)violations.push({family,index,label,lhs_numerator:String(lhs),rhs_numerator:String(rhs),
      positive_gap_numerator:String(lhs-rhs),denominator:String(q)});
  }
  inv.Gram_rows.forEach(([i,j,b,s])=>{check(sum(s)===BigInt(b)*q,"Gram row");counts.Gram++;});
  inv.original_signature_rows.forEach(([a,s],k)=>capacity("original_signature",k,a,sum(s),q));
  inv.triple_rows.forEach((v,k)=>capacity("triple",k,v.triple,sum(v.members),q));
  inv.Gram_conflict_clauses.forEach((clause,k)=>{
    check(clause.length===2&&clause.every(l=>Number.isInteger(l)&&l<0),"two negative-primary clause");
    const ids=clause.map(l=>-l-1);capacity("Gram_conflict",k,ids,sum(ids),q);
  });
  inv.uncapped_integer_cuts.forEach((cut,k)=>{
    check(Number.isInteger(cut.positive_demand)&&cut.positive_demand>0,"positive exact demand");
    let rhs=0n;
    for(const[a,w]of cut.positive_terms){check(Number.isInteger(w)&&w>0,"positive exact weight");rhs+=BigInt(w)*x[a];}
    capacity("uncapped_row_cut",k,cut.target_column,BigInt(cut.positive_demand)*x[cut.target_column],rhs);
  });
  for(const a of[352,353,354,355,439,552,553,645,869,873,957,1080,1081,1167])capacity("old_unit",a,a,x[a],0n);
  check(JSON.stringify(counts)===JSON.stringify({Gram:630,original_signature:186,triple:1365,Gram_conflict:30,uncapped_row_cut:60,old_unit:14}),"complete native coverage");
  const hist={};for(const v of violations)hist[v.family]=(hist[v.family]||0)+1;
  check(violations.length===22&&hist.triple===1&&hist.uncapped_row_cut===21,"recorded exact outcome");
  return {status:"complete exact evaluation of published native rows on certified Gram point",
    native_model_git_blob:"89fece302243da184766735c7517aa67f00a0dbe",
    native_model_sha256:"a9004e97a2d166bf8b162609cfb538eae0dd4d26942b6df5119b6a88d65ec476",
    point_git_blob:"b0bc5e43f768e7f082fe93d87f2a429281e10a20",
    point_sha256:"0b2f1ac00015b12e612ae29a3f48c67c15d773365152cbc464d3f31f3a37957b",
    counts,violation_count:violations.length,violations_by_family:hist,violations,
    full_coordinate_covers_evaluated:false,new_reconstruction_performed:false,optimizer_calls:0,case4_excluded:false};
}
if(typeof module!=="undefined")module.exports={evaluateCase4Native};
if(typeof require!=="undefined"&&typeof module!=="undefined"&&require.main===module){
  const fs=require("fs"),args=process.argv.slice(2);
  check(!fs.existsSync(args[2]),"fresh output required");
  const result=evaluateCase4Native(fs.readFileSync(args[0],"utf8"),fs.readFileSync(args[1],"utf8"));
  fs.writeFileSync(args[2],JSON.stringify(result,null,2)+"\n");
}
