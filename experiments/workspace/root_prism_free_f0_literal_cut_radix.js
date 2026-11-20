/* Exact signed-radix encoding of a bounded-support Boolean inequality.
 * Standalone V8/Node-compatible IIFE. No I/O, native solver, or model import.
 * Evaluate this source, compute its SHA256, then call bindSource(that SHA256).
 * This utility does not claim transport of the unavailable 4416-row archive.
 */
(() => {
  "use strict";
  const SCHEMA = "conway99.signed-radix-Boolean-row.v1";
  const I64 = (1n << 63n) - 1n;
  const HALF_I64 = I64 / 2n;
  const ID_LIMIT = 2147483647;

  function fail(message) { throw new Error(message); }
  function requireThat(condition, message) { if (!condition) fail(message); }
  function abs(x) { return x < 0n ? -x : x; }
  function max(a,b) { return a > b ? a : b; }
  function object(value,label) {
    requireThat(value !== null && typeof value === "object" && !Array.isArray(value), label + ": expected object");
    requireThat(Object.getPrototypeOf(value) === Object.prototype, label + ": expected plain object");
  }
  function keys(value, wanted, label) {
    object(value,label);
    requireThat(Object.keys(value).sort().join("|") === wanted.slice().sort().join("|"), label + ": unexpected or missing fields");
  }
  function integer(value,lo,hi,label) {
    requireThat(typeof value === "number" && Number.isSafeInteger(value) && value >= lo && value <= hi, label + ": invalid integer");
    return value;
  }
  function decimal(value,label) {
    requireThat(typeof value === "string" && value.length <= 4096 && /^(0|[1-9][0-9]*|-[1-9][0-9]*)$/.test(value), label + ": noncanonical decimal integer");
    return BigInt(value);
  }
  function canonical(value) {
    if (value === null) return "null";
    if (typeof value === "string" || typeof value === "boolean") return JSON.stringify(value);
    if (typeof value === "number") {
      requireThat(Number.isSafeInteger(value), "canonical: noninteger Number");
      return JSON.stringify(value);
    }
    if (Array.isArray(value)) return "[" + value.map(canonical).join(",") + "]";
    object(value,"canonical");
    return "{" + Object.keys(value).sort().map(k => JSON.stringify(k) + ":" + canonical(value[k])).join(",") + "}";
  }
  function utf8(s) {
    requireThat(typeof s === "string","sha256: string required");
    const out=[];
    for (const c of s) {
      const n=c.codePointAt(0);
      requireThat(n < 0xd800 || n > 0xdfff,"sha256: lone surrogate");
      if (n<128) out.push(n);
      else if(n<2048) out.push(192|(n>>6),128|(n&63));
      else if(n<65536) out.push(224|(n>>12),128|((n>>6)&63),128|(n&63));
      else out.push(240|(n>>18),128|((n>>12)&63),128|((n>>6)&63),128|(n&63));
    }
    return out;
  }
  const SHA_K=[0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2];
  function sha256(s) {
    const a=utf8(s),length=a.length;
    a.push(128);while(a.length%64!==56)a.push(0);
    const high=Math.floor(length/0x20000000),low=(length*8)>>>0;
    for(const x of [high,low])for(let j=3;j>=0;j--)a.push((x>>>(8*j))&255);
    const h=[0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19],w=Array(64);
    const ro=(x,n)=>(x>>>n)|(x<<(32-n));
    for(let k=0;k<a.length;k+=64) {
      for(let j=0;j<16;j++){const p=k+4*j;w[j]=(a[p]<<24)|(a[p+1]<<16)|(a[p+2]<<8)|a[p+3];}
      for(let j=16;j<64;j++){const x=w[j-15],y=w[j-2];w[j]=(w[j-16]+(ro(x,7)^ro(x,18)^(x>>>3))+w[j-7]+(ro(y,17)^ro(y,19)^(y>>>10)))|0;}
      let [A,B,C,D,E,F,G,H]=h;
      for(let j=0;j<64;j++){
        const t1=(H+(ro(E,6)^ro(E,11)^ro(E,25))+((E&F)^(~E&G))+SHA_K[j]+w[j])|0;
        const t2=((ro(A,2)^ro(A,13)^ro(A,22))+((A&B)^(A&C)^(B&C)))|0;
        H=G;G=F;F=E;E=(D+t1)|0;D=C;C=B;B=A;A=(t1+t2)|0;
      }
      [A,B,C,D,E,F,G,H].forEach((v,j)=>h[j]=(h[j]+v)|0);
    }
    return h.map(x=>(x>>>0).toString(16).padStart(8,"0")).join("");
  }
  function options(raw={}) {
    object(raw,"options");
    const allowed=["binaryCount","binaryOffset","firstAux","baseBits","maxDigits"];
    requireThat(Object.keys(raw).every(k=>allowed.includes(k)),"options: unknown field");
    const binaryCount=integer(raw.binaryCount===undefined?480:raw.binaryCount,0,480,"binaryCount");
    const binaryOffset=integer(raw.binaryOffset===undefined?0:raw.binaryOffset,0,ID_LIMIT,"binaryOffset");
    const end=binaryOffset+binaryCount;
    requireThat(end<=ID_LIMIT,"binary ID interval overflow");
    const firstAux=integer(raw.firstAux===undefined?end:raw.firstAux,end,ID_LIMIT,"firstAux");
    return {binaryCount,binaryOffset,firstAux,
      baseBits:integer(raw.baseBits===undefined?30:raw.baseBits,1,30,"baseBits"),
      maxDigits:integer(raw.maxDigits===undefined?128:raw.maxDigits,1,128,"maxDigits")};
  }
  function original(row,p) {
    keys(row,["terms","rhs"],"row");
    requireThat(Array.isArray(row.terms) && row.terms.length<=p.binaryCount,"row terms");
    let last=-1,minimum=0n,magnitude=0n;
    const terms=[];
    for(const term of row.terms) {
      requireThat(Array.isArray(term) && term.length===2,"term shape");
      const id=integer(term[0],p.binaryOffset,p.binaryOffset+p.binaryCount-1,"literal ID");
      requireThat(id>last,"literal IDs must be sorted and unique");last=id;
      const c=decimal(term[1],"coefficient");requireThat(c!==0n,"zero term is not canonical");
      terms.push([id,c.toString()]);if(c<0n)minimum+=c;magnitude=max(magnitude,abs(c));
    }
    const rhs=decimal(row.rhs,"rhs"),slackUpper=max(0n,rhs-minimum);
    magnitude=max(magnitude,max(abs(rhs),slackUpper));
    const B=1n<<BigInt(p.baseBits);let L=1,power=B;
    while(magnitude>=power){L++;requireThat(L<=p.maxDigits,"maxDigits exceeded");power*=B;}
    requireThat(p.firstAux+2*L-1<=ID_LIMIT,"auxiliary ID interval overflow");
    return {row:{terms,rhs:rhs.toString()},n:terms.length,rhs,minimum,slackUpper,magnitude,B,L,power,C:BigInt(terms.length+2)};
  }
  function signedDigits(value,L,B) {
    const sign=value<0n?-1n:1n;let q=abs(value);const out=[];
    for(let j=0;j<L;j++){out.push(sign*(q%B));q/=B;}
    requireThat(q===0n,"digit overflow");return out;
  }
  function nativeAudit(rows,variables,p,n,B) {
    const domains=new Map();
    for(let i=0;i<p.binaryCount;i++)domains.set(p.binaryOffset+i,[0n,1n]);
    let newDomainSum=0n;
    for(const v of variables){
      const lo=BigInt(v.domain[0]),hi=BigInt(v.domain[1]);
      requireThat(lo<=hi && lo>=-HALF_I64 && hi<=HALF_I64,"native variable domain");
      domains.set(v.id,[lo,hi]);
      newDomainSum+=max(max(abs(lo),abs(hi)),hi-lo);
    }
    const limbs=[];let maximumAbsolute=0n,maximumResidual=0n;
    for(const row of rows){
      let lo=0n,hi=0n,sumAbs=0n;
      for(const [id,text] of row.terms){
        const c=BigInt(text),domain=domains.get(id);requireThat(domain!==undefined,"unknown native ID");
        const a=c*domain[0],b=c*domain[1];
        lo+=a<b?a:b;hi+=a>b?a:b;sumAbs+=max(abs(a),abs(b));
      }
      const rhs=BigInt(row.domain[0]),residual=sumAbs+abs(rhs);
      requireThat(lo>=-HALF_I64 && hi<=HALF_I64 && hi-lo<=I64,"native linear activity overflow");
      requireThat(residual<=(2n*BigInt(n)+4n)*B,"proved residual bound failed");
      maximumAbsolute=max(maximumAbsolute,sumAbs);maximumResidual=max(maximumResidual,residual);
      limbs.push({limb:row.limb,minimum_activity:lo.toString(),maximum_activity:hi.toString(),
        interval_width:(hi-lo).toString(),sum_absolute_term_bounds:sumAbs.toString(),
        residual_absolute_bound:residual.toString()});
    }
    requireThat(newDomainSum<I64,"new-variable domain sum overflow");
    return {limbs,maximum_sum_absolute_term_bounds:maximumAbsolute.toString(),
      maximum_residual_absolute_bound:maximumResidual.toString(),
      universal_residual_bound:((2n*BigInt(n)+4n)*B).toString(),
      new_variable_domain_sum:newDomainSum.toString(),
      full_existing_model_domain_sum_checked:false,native_model_validator_executed:false};
  }
  function assignment(values,p) {
    requireThat(Array.isArray(values) && values.length===p.binaryCount,"binary assignment shape");
    for(const v of values)requireThat(typeof v==="number" && (v===0||v===1),"binary assignment must use exact 0/1 Numbers");
    return values;
  }
  function bindSource(sourceSha256) {
    requireThat(typeof sourceSha256==="string" && /^[0-9a-f]{64}$/.test(sourceSha256),"source SHA256 required");
    function encodeRow(row,rawOptions={}) {
      const p=options(rawOptions),o=original(row,p),{B,L,C}=o;
      const variables=[];
      for(let j=0;j<L;j++)variables.push({id:p.firstAux+j,kind:"slack",limb:j,domain:["0",(B-1n).toString()]});
      for(let j=1;j<L;j++)variables.push({id:p.firstAux+L+j-1,kind:"carry",limb:j,domain:[(-C).toString(),C.toString()]});
      const digitColumns=o.row.terms.map(([id,c])=>[id,signedDigits(BigInt(c),L,B)]);
      const rhsDigits=signedDigits(o.rhs,L,B),rows=[];
      for(let j=0;j<L;j++){
        const terms=[];
        for(const [id,d] of digitColumns)if(d[j]!==0n)terms.push([id,d[j].toString()]);
        terms.push([p.firstAux+j,"1"]);
        if(j>0)terms.push([p.firstAux+L+j-1,"1"]);
        if(j+1<L)terms.push([p.firstAux+L+j,(-B).toString()]);
        terms.sort((a,b)=>a[0]-b[0]);
        rows.push({limb:j,terms,domain:[rhsDigits[j].toString(),rhsDigits[j].toString()]});
      }
      return {schema:SCHEMA,source_sha256:sourceSha256,original_row:o.row,
        original_row_sha256:sha256(canonical(o.row)),parameters:p,
        nonzero_terms:o.n,base:B.toString(),digits:L,capacity:o.power.toString(),
        maximum_slack:o.slackUpper.toString(),carry_bound:C.toString(),
        auxiliary_variables:variables,linear_rows:rows,next_aux_id:p.firstAux+2*L-1,
        native_audit:nativeAudit(rows,variables,p,o.n,B)};
    }
    function verifyEncoding(e,expectedRow,expectedOptions) {
      keys(e,["schema","source_sha256","original_row","original_row_sha256","parameters",
        "nonzero_terms","base","digits","capacity","maximum_slack","carry_bound",
        "auxiliary_variables","linear_rows","next_aux_id","native_audit"],"encoding");
      requireThat(e.schema===SCHEMA && e.source_sha256===sourceSha256,"encoding source/schema binding");
      requireThat(expectedRow!==undefined,"external expected original row required");
      const p=options(expectedOptions===undefined?e.parameters:expectedOptions),o=original(expectedRow,p),{B,L,C}=o;
      requireThat(canonical(e.parameters)===canonical(p),"parameter binding");
      requireThat(canonical(e.original_row)===canonical(o.row) && e.original_row_sha256===sha256(canonical(o.row)),"original row binding");
      requireThat(e.nonzero_terms===o.n && e.digits===L && e.base===B.toString() &&
        e.capacity===o.power.toString() && e.maximum_slack===o.slackUpper.toString() &&
        e.carry_bound===C.toString() && e.next_aux_id===p.firstAux+2*L-1,"encoding derived metadata");
      requireThat(Array.isArray(e.auxiliary_variables) && e.auxiliary_variables.length===2*L-1,"auxiliary variable count");
      for(let t=0;t<e.auxiliary_variables.length;t++){
        const v=e.auxiliary_variables[t];keys(v,["id","kind","limb","domain"],"auxiliary variable");
        const slack=t<L,j=slack?t:t-L+1;
        requireThat(v.id===p.firstAux+t && v.kind===(slack?"slack":"carry") && v.limb===j,"auxiliary ID/kind/limb");
        requireThat(canonical(v.domain)===canonical(slack?["0",(B-1n).toString()]:[(-C).toString(),C.toString()]),"auxiliary domain");
      }
      requireThat(Array.isArray(e.linear_rows) && e.linear_rows.length===L,"linear row count");
      const originalTerms=new Map(o.row.terms.map(([id,c])=>[id,BigInt(c)])),weighted=new Map();
      let weight=1n,totalRhs=0n;
      for(let j=0;j<L;j++){
        const row=e.linear_rows[j];keys(row,["limb","terms","domain"],"linear row");
        requireThat(row.limb===j && Array.isArray(row.terms),"linear row limb/terms");
        requireThat(Array.isArray(row.domain) && row.domain.length===2,"equality domain shape");
        const rhs=decimal(row.domain[0],"limb rhs");
        requireThat(row.domain[1]===row.domain[0] && abs(rhs)<B,"limb equality and rhs range");
        requireThat(rhs===0n || (o.rhs!==0n && (rhs<0n)===(o.rhs<0n)),"rhs digit sign");
        const required=new Map([[p.firstAux+j,1n]]);
        if(j>0)required.set(p.firstAux+L+j-1,1n);
        if(j+1<L)required.set(p.firstAux+L+j,-B);
        let last=-1;
        for(const term of row.terms){
          requireThat(Array.isArray(term) && term.length===2,"native term shape");
          const id=integer(term[0],0,ID_LIMIT,"native ID"),c=decimal(term[1],"native coefficient");
          requireThat(id>last && c!==0n,"native terms must be sorted, unique and nonzero");last=id;
          if(originalTerms.has(id)){
            const originalCoefficient=originalTerms.get(id);
            requireThat(abs(c)<B && (c<0n)===(originalCoefficient<0n),"signed canonical digit range");
          }else{
            requireThat(required.has(id) && required.get(id)===c,"carry/slack coefficient or unexpected variable");
            required.delete(id);
          }
          weighted.set(id,(weighted.get(id)||0n)+weight*c);
        }
        requireThat(required.size===0,"missing carry/slack endpoint term");
        totalRhs+=weight*rhs;weight*=B;
      }
      requireThat(totalRhs===o.rhs,"weighted rhs reconstruction");
      for(const [id,c] of originalTerms)requireThat((weighted.get(id)||0n)===c,"weighted original coefficient reconstruction");
      for(let j=0,power=1n;j<L;j++,power*=B)requireThat(weighted.get(p.firstAux+j)===power,"weighted slack reconstruction");
      for(let j=1;j<L;j++)requireThat((weighted.get(p.firstAux+L+j-1)||0n)===0n,"internal carry did not cancel");
      requireThat(weighted.size<=o.n+2*L-1,"unexpected weighted variable");
      const audit=nativeAudit(e.linear_rows,e.auxiliary_variables,p,o.n,B);
      requireThat(canonical(e.native_audit)===canonical(audit),"native arithmetic audit mismatch");
      return {status:"EXACT_ENCODING_VERIFIED",source_sha256:sourceSha256,
        original_row_sha256:e.original_row_sha256,digits:L,auxiliary_variables:2*L-1,
        weighted_original_coefficients_checked:o.n,weighted_slack_coefficients_checked:L,
        internal_carry_cancellations_checked:L-1,native_audit:audit};
    }
    function checkWitness(e,binaryValues,auxiliaryValues) {
      verifyEncoding(e,e.original_row,e.parameters);
      const p=e.parameters,values=assignment(binaryValues,p),map=new Map();
      for(let i=0;i<values.length;i++)map.set(p.binaryOffset+i,BigInt(values[i]));
      requireThat(Array.isArray(auxiliaryValues) && auxiliaryValues.length===e.auxiliary_variables.length,"auxiliary witness shape");
      let slack=0n,weight=1n;
      for(let t=0;t<auxiliaryValues.length;t++){
        const item=auxiliaryValues[t],v=e.auxiliary_variables[t];
        requireThat(Array.isArray(item) && item.length===2 && item[0]===v.id,"auxiliary witness IDs/order");
        const value=decimal(item[1],"auxiliary witness value");
        requireThat(value>=BigInt(v.domain[0]) && value<=BigInt(v.domain[1]),"auxiliary witness outside domain");
        map.set(v.id,value);
        if(v.kind==="slack"){slack+=weight*value;weight*=BigInt(e.base);}
      }
      for(const row of e.linear_rows){
        let activity=0n;
        for(const [id,c] of row.terms)activity+=BigInt(c)*map.get(id);
        requireThat(activity===BigInt(row.domain[0]),"native limb equality failed");
      }
      let activity=0n;for(const [id,c] of e.original_row.terms)activity+=BigInt(c)*map.get(id);
      const rhs=BigInt(e.original_row.rhs);
      requireThat(slack>=0n && activity+slack===rhs && activity<=rhs,"original inequality/weighted slack failed");
      return {status:"EXACT_AUXILIARY_WITNESS_CHECKED",original_row_sha256:e.original_row_sha256,
        binary_assignment_sha256:sha256(canonical(values)),original_activity:activity.toString(),
        rhs:rhs.toString(),slack:slack.toString(),native_equalities_checked:e.digits};
    }
    function completeWitness(e,binaryValues) {
      verifyEncoding(e,e.original_row,e.parameters);
      const p=e.parameters,values=assignment(binaryValues,p),B=BigInt(e.base),C=BigInt(e.carry_bound);
      let activity=0n;
      for(const [id,c] of e.original_row.terms)activity+=BigInt(c)*BigInt(values[id-p.binaryOffset]);
      const slack=BigInt(e.original_row.rhs)-activity;
      if(slack<0n)return {status:"ORIGINAL_ROW_VIOLATED",original_row_sha256:e.original_row_sha256,
        original_activity:activity.toString(),rhs:e.original_row.rhs,slack:slack.toString(),auxiliary_values:null};
      requireThat(slack<BigInt(e.capacity),"satisfying slack capacity failure");
      let q=slack;const digits=[];
      for(let j=0;j<e.digits;j++){digits.push(q%B);q/=B;}requireThat(q===0n,"slack truncation");
      let carry=0n;const carries=[];
      for(let j=0;j<e.digits;j++){
        let numerator=digits[j]+carry-BigInt(e.linear_rows[j].domain[0]);
        for(const [id,c] of e.linear_rows[j].terms)if(id>=p.binaryOffset&&id<p.binaryOffset+p.binaryCount)
          numerator+=BigInt(c)*BigInt(values[id-p.binaryOffset]);
        requireThat(numerator%B===0n,"nonintegral carry");carry=numerator/B;
        requireThat(carry>=-C && carry<=C,"carry bound failed");
        if(j+1<e.digits)carries.push(carry);else requireThat(carry===0n,"final carry not zero");
      }
      const auxiliaryValues=digits.concat(carries).map((v,t)=>[p.firstAux+t,v.toString()]);
      const check=checkWitness(e,values,auxiliaryValues);
      return {status:"EXACT_AUXILIARY_WITNESS",source_sha256:sourceSha256,
        original_row_sha256:e.original_row_sha256,auxiliary_values:auxiliaryValues,check};
    }
    return Object.freeze({encodeRow,verifyEncoding,completeWitness,checkWitness});
  }
  return Object.freeze({schema:SCHEMA,canonical,sha256,bindSource});
})()
