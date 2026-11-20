(() => {
"use strict";
function check(ok, message) { if (!ok) throw Error(message); }
function utf8(s) {
 const out=[];
 for (const c of s) { const n=c.codePointAt(0);
  if(n<128) out.push(n);
  else if(n<2048) out.push(192|(n>>6),128|(n&63));
  else if(n<65536) { check(n<0xd800||n>0xdfff,"unpaired surrogate"); out.push(224|(n>>12),128|((n>>6)&63),128|(n&63)); }
  else out.push(240|(n>>18),128|((n>>12)&63),128|((n>>6)&63),128|(n&63));
 }
 return Uint8Array.from(out);
}
function ascii(b) {
 let s="";
 for(let i=0;i<b.length;i+=8192) { const part=b.subarray(i,i+8192); check(part.every(x=>x<128),"non-ASCII JSON"); s+=String.fromCharCode(...part); }
 return s;
}
function base64(s) {
 const chars="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
 s=s.replace(/\s/g,""); check(s.length%4===0&&/^[A-Za-z0-9+/]*={0,2}$/.test(s),"invalid base64");
 const pad=s.endsWith("==")?2:s.endsWith("=")?1:0;
 const out=new Uint8Array(s.length/4*3-pad); let j=0;
 for(let i=0;i<s.length;i+=4) {
  const a=chars.indexOf(s[i]),b=chars.indexOf(s[i+1]),c=s[i+2]==="="?0:chars.indexOf(s[i+2]),d=s[i+3]==="="?0:chars.indexOf(s[i+3]);
  const n=(a<<18)|(b<<12)|(c<<6)|d;
  if(j<out.length)out[j++]=(n>>>16)&255;
  if(j<out.length)out[j++]=(n>>>8)&255;
  if(j<out.length)out[j++]=n&255;
 }
 return out;
}
function hex(b) { return Array.from(b,x=>x.toString(16).padStart(2,"0")).join(""); }
function fromHex(s) { check(s.length%2===0&&/^[0-9a-f]*$/i.test(s),"bad hex"); return Uint8Array.from(s.match(/../g)||[],x=>parseInt(x,16)); }
function padded(bytes) {
 const n=Math.ceil((bytes.length+9)/64)*64,b=new Uint8Array(n); b.set(bytes); b[bytes.length]=128;
 const length=BigInt(bytes.length)*8n; for(let i=0;i<8;i++) b[n-1-i]=Number((length>>BigInt(i*8))&255n);
 return b;
}
const K=[0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2];
const rr=(x,n)=>(x>>>n)|(x<<(32-n)),rl=(x,n)=>(x<<n)|(x>>>(32-n));
function sha256(input) {
 const b=padded(input),w=new Uint32Array(64),h=[0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19];
 for(let off=0;off<b.length;off+=64) {
  for(let i=0;i<16;i++) {const j=off+4*i;w[i]=((b[j]<<24)|(b[j+1]<<16)|(b[j+2]<<8)|b[j+3])>>>0;}
  for(let i=16;i<64;i++)w[i]=(w[i-16]+(rr(w[i-15],7)^rr(w[i-15],18)^(w[i-15]>>>3))+w[i-7]+(rr(w[i-2],17)^rr(w[i-2],19)^(w[i-2]>>>10)))>>>0;
  let [a,c,d,e,f,g,j,k]=h;
  for(let i=0;i<64;i++) {
   const t1=(k+(rr(f,6)^rr(f,11)^rr(f,25))+((f&g)^(~f&j))+K[i]+w[i])>>>0;
   const t2=((rr(a,2)^rr(a,13)^rr(a,22))+((a&c)^(a&d)^(c&d)))>>>0;
   k=j;j=g;g=f;f=(e+t1)>>>0;e=d;d=c;c=a;a=(t1+t2)>>>0;
  }
  const v=[a,c,d,e,f,g,j,k];for(let i=0;i<8;i++)h[i]=(h[i]+v[i])>>>0;
 }
 return h.map(x=>x.toString(16).padStart(8,"0")).join("");
}
function sha1(input) {
 const b=padded(input),w=new Uint32Array(80),h=[0x67452301,0xefcdab89,0x98badcfe,0x10325476,0xc3d2e1f0];
 for(let off=0;off<b.length;off+=64) {
  for(let i=0;i<16;i++){const j=off+4*i;w[i]=((b[j]<<24)|(b[j+1]<<16)|(b[j+2]<<8)|b[j+3])>>>0;}
  for(let i=16;i<80;i++)w[i]=rl(w[i-3]^w[i-8]^w[i-14]^w[i-16],1)>>>0;
  let [a,c,d,e,f]=h;
  for(let i=0;i<80;i++){const q=i<20?((c&d)|(~c&e)):i<40?(c^d^e):i<60?((c&d)|(c&e)|(d&e)):(c^d^e),k=i<20?0x5a827999:i<40?0x6ed9eba1:i<60?0x8f1bbcdc:0xca62c1d6;
   const t=(rl(a,5)+q+f+k+w[i])>>>0;f=e;e=d;d=rl(c,30)>>>0;c=a;a=t;
  }
  const v=[a,c,d,e,f];for(let i=0;i<5;i++)h[i]=(h[i]+v[i])>>>0;
 }
 return h.map(x=>x.toString(16).padStart(8,"0")).join("");
}
function gitBlob(input) {const prefix=utf8("blob "+input.length+"\0"), b=new Uint8Array(prefix.length+input.length);b.set(prefix);b.set(input,prefix.length);return sha1(b);}
const crcTable=Array.from({length:256},(_,i)=>{let c=i;for(let j=0;j<8;j++)c=(c&1)?(0xedb88320^(c>>>1)):(c>>>1);return c>>>0;});
function crc32(b){let c=0xffffffff;for(const x of b)c=crcTable[(c^x)&255]^(c>>>8);return (c^0xffffffff)>>>0;}
function gunzip(b,maximum=67108864) {
 check(b.length>=18&&b[0]===31&&b[1]===139&&b[2]===8,"gzip header");const flags=b[3];check((flags&224)===0,"gzip flags");
 const u32=i=>((b[i]|(b[i+1]<<8)|(b[i+2]<<16)|(b[i+3]<<24))>>>0);
 const limit=b.length-8, size=u32(b.length-4);check(size<=maximum,"gzip output too large");
 let pos=10;
 if(flags&4){check(pos+2<=limit,"extra");const n=b[pos]|(b[pos+1]<<8);pos+=2+n;}
 for(const flag of [8,16])if(flags&flag){while(pos<limit&&b[pos]!==0)pos++;check(pos<limit,"gzip string");pos++;}
 if(flags&2){check(pos+2<=limit,"header CRC");check((crc32(b.subarray(0,pos))&65535)===(b[pos]|(b[pos+1]<<8)),"header CRC mismatch");pos+=2;}
 check(pos<limit,"missing DEFLATE");let bit=pos*8,nout=0;const out=new Uint8Array(size);
 function bits(n){check(bit+n<=limit*8,"truncated bits");let v=0;for(let i=0;i<n;i++,bit++)v|=((b[bit>>>3]>>>(bit&7))&1)<<i;return v;}
 function table(lengths) {
  const counts=new Uint32Array(16),next=new Uint32Array(16);let max=0;
  for(const n of lengths){check(Number.isInteger(n)&&n>=0&&n<=15,"code length");if(n){counts[n]++;max=Math.max(max,n);}}
  let code=0;for(let n=1;n<=15;n++){code=(code+counts[n-1])<<1;check(code+counts[n]<=1<<n,"oversubscribed Huffman");next[n]=code;}
  const map=new Map();
  lengths.forEach((n,s)=>{if(n){let c=next[n]++,r=0;for(let i=0;i<n;i++){r=(r<<1)|(c&1);c>>>=1;}map.set((n<<16)|r,s);}});
  return {map,max};
 }
 function symbol(t){let c=0;for(let n=1;n<=t.max;n++){c|=bits(1)<<(n-1);const v=t.map.get((n<<16)|c);if(v!==undefined)return v;}throw Error("invalid Huffman symbol");}
 const LB=[3,4,5,6,7,8,9,10,11,13,15,17,19,23,27,31,35,43,51,59,67,83,99,115,131,163,195,227,258];
 const LE=[0,0,0,0,0,0,0,0,1,1,1,1,2,2,2,2,3,3,3,3,4,4,4,4,5,5,5,5,0];
 const DB=[1,2,3,4,5,7,9,13,17,25,33,49,65,97,129,193,257,385,513,769,1025,1537,2049,3073,4097,6145,8193,12289,16385,24577];
 const DE=[0,0,0,0,1,1,2,2,3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,11,11,12,12,13,13];
 let last=false;while(!last){
  last=bits(1)===1;const type=bits(2);check(type!==3,"reserved block");
  if(type===0){bit=(bit+7)&~7;const n=bits(16),inv=bits(16);check((n^inv)===65535&&nout+n<=size,"stored block");for(let i=0;i<n;i++)out[nout++]=bits(8);continue;}
  let lit,dist;
  if(type===1){lit=table(Array.from({length:288},(_,i)=>i<=143?8:i<=255?9:i<=279?7:8));dist=table(Array(32).fill(5));}
  else {
   const nl=bits(5)+257,nd=bits(5)+1,nc=bits(4)+4;check(nl<=286&&nd<=32,"dynamic counts");
   const sequence=[16,17,18,0,8,7,9,6,10,5,11,4,12,3,13,2,14,1,15];
   const cl=Array(19).fill(0);for(let i=0;i<nc;i++)cl[sequence[i]]=bits(3);
   const ct=table(cl),lengths=[];
   while(lengths.length<nl+nd){
    const s=symbol(ct);if(s<=15)lengths.push(s);
    else {let count,value;if(s===16){check(lengths.length>0,"missing repeat");count=bits(2)+3;value=lengths[lengths.length-1];}
     else if(s===17){count=bits(3)+3;value=0;}else{check(s===18,"invalid repeat");count=bits(7)+11;value=0;}
     check(lengths.length+count<=nl+nd,"code repeat overflow");for(let i=0;i<count;i++)lengths.push(value);
    }
   }
   check(lengths[256]>0,"missing end code");lit=table(lengths.slice(0,nl));dist=table(lengths.slice(nl));
  }
  while(true){const s=symbol(lit);if(s<256){check(nout<size,"output overflow");out[nout++]=s;continue;}if(s===256)break;
   check(s>=257&&s<=285,"invalid length");const i=s-257,n=LB[i]+bits(LE[i]),ds=symbol(dist);check(ds<30,"invalid distance");
   const d=DB[ds]+bits(DE[ds]);check(d<=nout&&nout+n<=size,"invalid copy");for(let j=0;j<n;j++){out[nout]=out[nout-d];nout++;}
  }
 }
 check(Math.ceil(bit/8)===limit&&nout===size,"gzip trailing data or size mismatch");
 check(crc32(out)===u32(limit),"gzip CRC mismatch");return out;
}
return {check,utf8,ascii,base64,hex,fromHex,sha256,sha1,gitBlob,crc32,gunzip};
})()