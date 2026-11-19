(() => {
"use strict";
function insist(ok, message) { if (!ok) throw new Error(message); }
function base64Bytes(text) {
  insist(typeof text === "string", "base64 input must be text");
  const s = text.replace(/[\t\n\r ]/g, "");
  insist(s.length % 4 === 0 && /^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(s), "invalid base64");
  const alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
  const lut = new Int16Array(128); lut.fill(-1);
  for (let i=0; i<64; ++i) lut[alphabet.charCodeAt(i)] = i;
  const padding = s.endsWith("==") ? 2 : s.endsWith("=") ? 1 : 0;
  const out = new Uint8Array(s.length/4*3-padding);
  let p=0;
  for (let i=0; i<s.length; i+=4) {
    const a=lut[s.charCodeAt(i)], b=lut[s.charCodeAt(i+1)];
    const c=s[i+2]==="="?0:lut[s.charCodeAt(i+2)], d=s[i+3]==="="?0:lut[s.charCodeAt(i+3)];
    const v=(a<<18)|(b<<12)|(c<<6)|d;
    if (p<out.length) out[p++]=v>>>16;
    if (p<out.length) out[p++]=(v>>>8)&255;
    if (p<out.length) out[p++]=v&255;
    if (i+4===s.length) insist(padding===0 || (padding===1 ? (c&3)===0 : (b&15)===0), "noncanonical base64 padding");
  }
  return out;
}
const crcTable = new Uint32Array(256);
for (let i=0; i<256; ++i) { let c=i; for(let j=0;j<8;++j)c=(c&1)?(0xedb88320^(c>>>1)):(c>>>1); crcTable[i]=c>>>0; }
function crc32(a, start=0, end=a.length) {
  let c=0xffffffff;
  for(let i=start;i<end;++i)c=crcTable[(c^a[i])&255]^(c>>>8);
  return (c^0xffffffff)>>>0;
}
function u32(a,p) { return (a[p]|(a[p+1]<<8)|(a[p+2]<<16)|(a[p+3]<<24))>>>0; }
function huffman(lengths) {
  const counts=new Int32Array(16), first=new Int32Array(16), offsets=new Int32Array(16);
  let maximum=0;
  for(const n of lengths) { insist(Number.isInteger(n)&&n>=0&&n<=15,"invalid Huffman length"); if(n){++counts[n];maximum=Math.max(maximum,n);} }
  let left=1, code=0, total=0;
  for(let n=1;n<=15;++n) {
    left=left*2-counts[n]; insist(left>=0,"oversubscribed Huffman tree");
    code=(code+counts[n-1])*2; first[n]=code; offsets[n]=total; total+=counts[n];
  }
  const symbols=new Int32Array(total), next=Int32Array.from(offsets);
  for(let s=0;s<lengths.length;++s)if(lengths[s])symbols[next[lengths[s]]++]=s;
  return {counts,first,offsets,symbols,maximum};
}
function gunzip(input, maximumOutput=64*1024*1024) {
  const a=input instanceof Uint8Array?input:Uint8Array.from(input);
  insist(Number.isSafeInteger(maximumOutput)&&maximumOutput>=0&&maximumOutput<=0x3fffffff,"invalid output bound");
  insist(a.length>=18 && a.length<=64*1024*1024,"invalid gzip input length");
  insist(a[0]===31&&a[1]===139&&a[2]===8,"gzip header/method");
  const flags=a[3]; insist((flags&224)===0,"reserved gzip flags");
  let p=10;
  const trailer=a.length-8;
  if(flags&4) { insist(p+2<=trailer,"truncated extra length");const n=a[p]|(a[p+1]<<8);p+=2+n;insist(p<=trailer,"truncated extra field"); }
  for(const bit of [8,16])if(flags&bit) { while(p<trailer&&a[p]!==0)++p;insist(p<trailer,"unterminated gzip header string");++p; }
  if(flags&2) { insist(p+2<=trailer,"truncated header CRC");insist((crc32(a,0,p)&65535)===(a[p]|(a[p+1]<<8)),"header CRC mismatch");p+=2; }
  insist(p<=trailer,"truncated gzip header");
  const expectedSize=u32(a,a.length-4), expectedCRC=u32(a,trailer);
  insist(expectedSize<=maximumOutput,"output limit exceeded");
  const out=new Uint8Array(expectedSize);
  let position=p*8, written=0, blocks=0, storedBlocks=0, fixedBlocks=0, dynamicBlocks=0;
  function bits(n) {
    insist(n>=0&&n<=16&&position+n<=trailer*8,"truncated deflate bits");
    let v=0;for(let j=0;j<n;++j,++position)v|=((a[position>>>3]>>>(position&7))&1)<<j;return v;
  }
  function symbol(tree) {
    let code=0;
    for(let n=1;n<=tree.maximum;++n) {
      code=code*2+bits(1);
      const delta=code-tree.first[n];
      if(delta>=0&&delta<tree.counts[n])return tree.symbols[tree.offsets[n]+delta];
    }
    throw new Error("invalid Huffman code");
  }
  const lengthBase=[3,4,5,6,7,8,9,10,11,13,15,17,19,23,27,31,35,43,51,59,67,83,99,115,131,163,195,227,258];
  const lengthExtra=[0,0,0,0,0,0,0,0,1,1,1,1,2,2,2,2,3,3,3,3,4,4,4,4,5,5,5,5,0];
  const distanceBase=[1,2,3,4,5,7,9,13,17,25,33,49,65,97,129,193,257,385,513,769,1025,1537,2049,3073,4097,6145,8193,12289,16385,24577];
  const distanceExtra=[0,0,0,0,1,1,2,2,3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,11,11,12,12,13,13];
  let last=false;
  while(!last) {
    last=bits(1)!==0; const type=bits(2);++blocks;
    insist(blocks<=a.length*8,"excess block count");
    if(type===0) {
      ++storedBlocks;position=(position+7)&~7;
      const n=bits(16), inverse=bits(16);insist((n^65535)===inverse,"stored length mismatch");
      insist(written+n<=out.length&&position+n*8<=trailer*8,"stored block bounds");
      for(let j=0;j<n;++j)out[written++]=bits(8);
      continue;
    }
    insist(type!==3,"reserved deflate block");
    let literalTree, distanceTree;
    if(type===1) {
      ++fixedBlocks;
      literalTree=huffman(Array.from({length:288},(_,s)=>s<144?8:s<256?9:s<280?7:8));
      distanceTree=huffman(Array(32).fill(5));
    } else {
      ++dynamicBlocks;
      const literalCount=bits(5)+257,distanceCount=bits(5)+1,codeCount=bits(4)+4;
      insist(literalCount<=286,"invalid literal alphabet size");
      const order=[16,17,18,0,8,7,9,6,10,5,11,4,12,3,13,2,14,1,15];
      const codeLengths=Array(19).fill(0);
      for(let j=0;j<codeCount;++j)codeLengths[order[j]]=bits(3);
      const codeTree=huffman(codeLengths), lengths=[];
      while(lengths.length<literalCount+distanceCount) {
        const s=symbol(codeTree);
        if(s<=15)lengths.push(s);
        else {
          let n,v;
          if(s===16){insist(lengths.length>0,"repeat without previous code");n=bits(2)+3;v=lengths[lengths.length-1];}
          else if(s===17){n=bits(3)+3;v=0;}
          else {insist(s===18,"bad repeat code");n=bits(7)+11;v=0;}
          insist(lengths.length+n<=literalCount+distanceCount,"code repeat overflow");
          for(let j=0;j<n;++j)lengths.push(v);
        }
      }
      insist(lengths[256]>0,"missing end-of-block symbol");
      literalTree=huffman(lengths.slice(0,literalCount));distanceTree=huffman(lengths.slice(literalCount));
    }
    for(;;) {
      const s=symbol(literalTree);
      if(s<256){insist(written<out.length,"literal output overflow");out[written++]=s;continue;}
      if(s===256)break;
      insist(s>=257&&s<=285,"reserved length symbol");
      const index=s-257,n=lengthBase[index]+bits(lengthExtra[index]);
      const d=symbol(distanceTree);insist(d<30,"reserved distance symbol");
      const distance=distanceBase[d]+bits(distanceExtra[d]);
      insist(distance<=written&&written+n<=out.length,"distance/output bounds");
      for(let j=0;j<n;++j){out[written]=out[written-distance];++written;}
    }
  }
  insist(Math.ceil(position/8)===trailer,"trailing/concatenated gzip data");
  insist(written===expectedSize,"ISIZE mismatch");
  insist(crc32(out)===expectedCRC,"CRC32 mismatch");
  return {bytes:out,compressed_bytes:a.length,uncompressed_bytes:written,crc32:expectedCRC,blocks,stored_blocks:storedBlocks,fixed_blocks:fixedBlocks,dynamic_blocks:dynamicBlocks};
}
function ascii(bytes) {
  const chunks=[];
  for(let p=0;p<bytes.length;p+=8192) {
    const piece=bytes.subarray(p,Math.min(bytes.length,p+8192));
    for(const b of piece)insist(b<128,"non-ASCII input; explicit UTF-8 reader required");
    chunks.push(String.fromCharCode(...piece));
  }
  return chunks.join("");
}
return {base64Bytes,crc32,gunzip,ascii};
})()
