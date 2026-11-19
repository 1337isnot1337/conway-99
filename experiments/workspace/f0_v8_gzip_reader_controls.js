((R) => {
"use strict";
function insist(ok, message) { if(!ok)throw Error(message); }
const bytes=s=>Uint8Array.from(Array.from(s,c=>c.charCodeAt(0)));
function same(a,b) { return a.length===b.length&&Array.from(a).every((x,i)=>x===b[i]); }
function writer() {
  const a=[];let bit=0;
  return {little(v,n){for(let j=0;j<n;++j){if((bit&7)===0)a.push(0);a[bit>>>3]|=((v>>>j)&1)<<(bit&7);++bit;}},
    code(v,n){for(let j=n-1;j>=0;--j)this.little((v>>>j)&1,1);},
    align(){while(bit&7)this.little(0,1);}, result(){return Uint8Array.from(a);}};
}
function wrap(deflate, plain) {
  const a=[31,139,8,0,0,0,0,0,0,255,...deflate];
  for(const value of [R.crc32(plain),plain.length])for(let j=0;j<4;++j)a.push((value>>>(8*j))&255);
  return Uint8Array.from(a);
}
const records=[];
function check(name, compressed, plain, kinds) {
  const r=R.gunzip(compressed);
  insist(same(r.bytes,plain),"control bytes: "+name);
  for(const [k,v] of Object.entries(kinds||{}))insist(r[k]===v,"control block kind: "+name);
  records.push({name,compressed_bytes:compressed.length,uncompressed_bytes:plain.length,crc32:r.crc32,blocks:r.blocks});
}
insist(R.crc32(bytes("123456789"))===0xcbf43926,"independent CRC32 known vector");
const empty=Uint8Array.from([31,139,8,0,0,0,0,0,2,3,3,0,0,0,0,0,0,0,0,0]);
check("known fixed empty gzip",empty,new Uint8Array(),{fixed_blocks:1});
for(const lengths of [[0],[1],[256],[17,0,31]]) {
  const w=writer(), plain=[];
  for(let i=0;i<lengths.length;++i) {
    const n=lengths[i];w.little(i+1===lengths.length?1:0,1);w.little(0,2);w.align();w.little(n,16);w.little(n^65535,16);
    for(let j=0;j<n;++j){const value=(j*37+i*11)&255;w.little(value,8);plain.push(value);}
  }
  check("stored "+lengths.join("+"),wrap(w.result(),plain),Uint8Array.from(plain),{stored_blocks:lengths.length});
}
function fixedSymbol(w,s) {
  if(s<=143)w.code(48+s,8);else if(s<=255)w.code(256+s,9);else if(s<=279)w.code(s-256,7);else w.code(192+s-280,8);
}
{
  const w=writer(), plain=Uint8Array.from({length:256},(_,i)=>i);
  w.little(1,1);w.little(1,2);for(const b of plain)fixedSymbol(w,b);fixedSymbol(w,256);
  check("fixed complete byte alphabet",wrap(w.result(),plain),plain,{fixed_blocks:1});
}
{
  const w=writer();w.little(1,1);w.little(1,2);
  for(const b of bytes("HELLO "))fixedSymbol(w,b);
  fixedSymbol(w,259);w.code(4,5);w.little(1,1);fixedSymbol(w,256);
  const plain=bytes("HELLO HELLO");
  check("fixed distance six copy",wrap(w.result(),plain),plain,{fixed_blocks:1});
}
{
  const w=writer();w.little(1,1);w.little(1,2);fixedSymbol(w,65);fixedSymbol(w,285);w.code(0,5);fixedSymbol(w,256);
  const plain=bytes("A".repeat(259));
  check("fixed overlapping length 258 copy",wrap(w.result(),plain),plain,{fixed_blocks:1});
}
{
  const w=writer();w.little(1,1);w.little(2,2);w.little(3,5);w.little(0,5);w.little(14,4);
  const order=[16,17,18,0,8,7,9,6,10,5,11,4,12,3,13,2,14,1,15];
  const lens={0:2,1:3,3:2,16:3,17:3,18:3};
  for(let i=0;i<18;++i)w.little(lens[order[i]]||0,3);
  const codes={0:[0,2],3:[1,2],1:[4,3],16:[5,3],17:[6,3],18:[7,3]};
  const symbol=s=>w.code(codes[s][0],codes[s][1]);
  symbol(18);w.little(65-11,7);
  symbol(3);symbol(16);w.little(4-3,2);
  symbol(18);w.little(138-11,7);
  symbol(18);w.little(38-11,7);
  symbol(17);w.little(10-3,3);
  symbol(3);symbol(3);symbol(0);symbol(3);symbol(1);
  for(let s=0;s<5;++s)w.code(s,3);
  w.code(6,3);w.code(0,1);
  w.code(7,3);w.code(0,1);
  w.code(5,3);
  const plain=bytes("ABCDE"+"E".repeat(8));
  check("dynamic all three code-length repeats and overlap",wrap(w.result(),plain),plain,{dynamic_blocks:1});
}
const rejections=[];
function rejects(name, fn){let rejected=false;try{fn();}catch(e){rejected=true;}insist(rejected,"expected rejection: "+name);rejections.push(name);}
for(const s of ["A","AAA","AA=A","AB==","AAB=","AAAA$==="])rejects("base64 "+s,()=>R.base64Bytes(s));
insist(same(R.base64Bytes(" AAEC\n /w== "),Uint8Array.from([0,1,2,255])),"base64 whitespace and padding");
rejects("output bound",()=>R.gunzip(wrap(Uint8Array.from([1,1,0,254,255,65]),bytes("A")),0));
const badCRC=Uint8Array.from(empty);badCRC[12]=1;rejects("CRC32",()=>R.gunzip(badCRC));
const badSize=Uint8Array.from(empty);badSize[16]=1;rejects("ISIZE",()=>R.gunzip(badSize));
const badMethod=Uint8Array.from(empty);badMethod[2]=0;rejects("method",()=>R.gunzip(badMethod));
const badFlag=Uint8Array.from(empty);badFlag[3]=32;rejects("reserved header flag",()=>R.gunzip(badFlag));
const badBlock=Uint8Array.from(empty);badBlock[10]=7;rejects("reserved block type",()=>R.gunzip(badBlock));
rejects("concatenated member",()=>R.gunzip(Uint8Array.from([...empty,...empty])));
rejects("non-ASCII text",()=>R.ascii(Uint8Array.from([128])));
return {status:"PASS",known_CRC32_vector:"123456789 -> cbf43926",roundtrip_controls:records,rejection_controls:rejections,optimizer_calls:0};
})
