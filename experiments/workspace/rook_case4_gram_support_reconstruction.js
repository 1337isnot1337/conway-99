"use strict";
// Exact reconstruction on one published numerical support. No optimizer.
// Node CLI:
//   node rook_case4_gram_support_reconstruction.js prepare input.json output.json
//   node rook_case4_gram_support_reconstruction.js solve input.json preparation.json output.json
//   node rook_case4_gram_support_reconstruction.js verify input.json result.json output.json
// The source also exports pure functions for V8 execution.

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

const EXPECTED_INPUT_OBJECT_SHA256 = "c05810ebd73ab18c943003f9a7a14c99d7aece56efea0ddb0ecb70360b5710ac";
function check(ok,msg){if(!ok)throw new Error(msg);}
function same(a,b){return JSON.stringify(a)===JSON.stringify(b);}
function gcd(a,b){a=a<0n?-a:a;b=b<0n?-b:b;while(b){const r=a%b;a=b;b=r;}return a;}
function bitLength(a){return (a<0n?-a:a).toString(2).length;}
function powmod(a,k,p){let result=1;while(k){if(k&1)result=result*a%p;a=a*a%p;k=Math.floor(k/2);}return result;}

function loadDomain(input){
  check(sha256Ascii(JSON.stringify(input))===EXPECTED_INPUT_OBJECT_SHA256,"exact input object binding");
  check(input.case_index===4 && input.column_masks35_decimal.length===1214,"case/domain size");
  const masks=input.column_masks35_decimal.map(BigInt),G=input.Gram;
  check(G.length===35 && G.every(row=>row.length===35),"Gram size");
  check(masks.every(h=>h>=0n && h<(1n<<35n)),"35-bit column range");
  const rows=[];
  for(let i=0;i<35;i++)for(let j=i;j<35;j++){
    check(Number.isSafeInteger(G[i][j])&&G[i][j]>=0&&G[i][j]===G[j][i],"integer symmetric Gram");
    const support=[];
    for(let a=0;a<1214;a++)if((masks[a]>>BigInt(i)&1n)&&(masks[a]>>BigInt(j)&1n))support.push(a);
    rows.push([i,j,G[i][j],support]);
  }
  check(sha256Ascii(JSON.stringify(rows))===input.all630_Gram_rows_sha256,"all630 exact row supports");
  check(G[3][27]+G[4][27]-G[17][27]===0,"zero-face RHS");
  const zeroFace=[];
  for(let a=0;a<1214;a++){
    const h=masks[a],at=i=>Number(h>>BigInt(i)&1n);
    const c=(at(3)+at(4)-at(17))*at(27);
    check(c===0||c===1,"nonnegative zero-face coefficient");
    if(c)zeroFace.push(a);
  }
  check(same(zeroFace,input.proved_Gram_zero_columns)&&zeroFace.length===46,"exact46-zero face");
  const values=input.numerical_proposal.values;
  check(values.length===1214&&values.every(v=>Number.isFinite(v)&&v>=0&&v<=1),"proposal values");
  const selected=[],discarded=[];
  for(let a=0;a<1214;a++){
    if(values[a]>1e-9)selected.push(a);
    else if(values[a]!==0)discarded.push([a,values[a]]);
  }
  check(selected.length===287 && same(discarded,input.support_rule.discarded_nonzero_coordinates),"explicit support choice");
  check(!selected.some(a=>zeroFace.includes(a)),"selected support avoids every proved zero");
  const selectedPosition=new Map(selected.map((a,j)=>[a,j]));
  const A=rows.map(row=>{
    const out=new Uint8Array(selected.length);
    for(const a of row[3])if(selectedPosition.has(a))out[selectedPosition.get(a)]=1;
    return out;
  });
  return {masks,G,rows,selected,A,b:rows.map(r=>r[2]),values,discarded};
}

function modularRank(A,b,p){
  check(Number.isSafeInteger(p)&&p>2&&p<100000,"bounded modular prime");
  for(let d=2;d*d<=p;d++)check(p%d!==0,"prime modulus");
  const m=A.length,n=A[0].length;
  const M=A.map((row,i)=>Uint32Array.from([...row,b[i]]));
  const ids=Array.from({length:m},(_,i)=>i),columns=[],pivotValues=[];
  let r=0,determinant=1;
  for(let j=0;j<n;j++){
    let at=r;while(at<m&&M[at][j]===0)at++;
    if(at===m)continue;
    [M[r],M[at]]=[M[at],M[r]];[ids[r],ids[at]]=[ids[at],ids[r]];
    const pivot=M[r][j],inverse=powmod(pivot,p-2,p);
    check(pivot*inverse%p===1,"modular inverse");
    pivotValues.push(pivot);determinant=determinant*pivot%p;
    for(let k=j;k<=n;k++)M[r][k]=M[r][k]*inverse%p;
    for(let i=r+1;i<m;i++){
      const factor=M[i][j];if(!factor)continue;
      M[i][j]=0;
      for(let k=j+1;k<=n;k++){
        let value=(M[i][k]-factor*M[r][k])%p;
        if(value<0)value+=p;M[i][k]=value;
      }
    }
    columns.push(j);r++;
  }
  const inconsistent=[];
  for(let i=r;i<m;i++){
    check(M[i].slice(0,n).every(x=>x===0),"modular rank exhausted");
    if(M[i][n])inconsistent.push({original_row:ids[i],residual:M[i][n]});
  }
  return {prime:p,rank:r,pivot_column_positions:columns,independent_original_rows:ids.slice(0,r),
    pivot_values:pivotValues,ordered_minor_determinant_mod_prime:determinant,
    augmented_system_consistent_mod_prime:inconsistent.length===0,inconsistent_rows:inconsistent,
    rational_rank_claim:"only the displayed nonsingular minor is asserted over Q; full-row exact replay decides the proposed solution"};
}

function roundDecimalToScale(value,scale){
  const s=value.toString().toLowerCase(),pieces=s.split("e");
  const power=pieces.length===2?Number(pieces[1]):0,decimal=pieces[0].split(".");
  check(!decimal[0].startsWith("-"),"nonnegative free proposal");
  let numerator=BigInt(decimal.join("")),denominator=10n**BigInt((decimal[1]||"").length);
  if(power>=0)numerator*=10n**BigInt(power);else denominator*=10n**BigInt(-power);
  return (2n*numerator*scale+denominator)/(2n*denominator);
}

function fractionFreeSolve(matrix,rhs,deadline,maximumBits){
  const n=matrix.length;
  check(n>0&&rhs.length===n&&matrix.every(row=>row.length===n),"square exact solve");
  const M=matrix.map((row,i)=>[...row.map(BigInt),BigInt(rhs[i])]);
  let previous=1n,swaps=0,peakBits=1,divisions=0;
  const tick=()=>check(Date.now()<=deadline,"exact solve time budget");
  const bounded=value=>{const bits=bitLength(value);if(bits>peakBits)peakBits=bits;check(bits<=maximumBits,"exact integer bit budget");};
  for(let k=0;k<n-1;k++){
    tick();
    if(M[k][k]===0n){
      let at=k+1;while(at<n&&M[at][k]===0n)at++;
      check(at<n,"singular exact minor");[M[k],M[at]]=[M[at],M[k]];swaps++;
    }
    const pivot=M[k][k];bounded(pivot);
    for(let i=k+1;i<n;i++){
      if((i&15)===0)tick();
      const factor=M[i][k];
      for(let j=k+1;j<=n;j++){
        const numerator=pivot*M[i][j]-factor*M[k][j];
        check(numerator%previous===0n,"Bareiss exact divisibility");
        M[i][j]=numerator/previous;divisions++;
      }
      M[i][k]=0n;bounded(M[i][n]);bounded(M[i][i]);
    }
    previous=pivot;
  }
  tick();
  const denominator=M[n-1][n-1];check(denominator!==0n,"nonsingular final pivot");
  const numerators=Array(n).fill(0n);
  for(let i=n-1;i>=0;i--){
    let numerator=denominator*M[i][n];
    for(let j=i+1;j<n;j++)numerator-=M[i][j]*numerators[j];
    check(numerator%M[i][i]===0n,"exact integer adjugate back substitution");
    numerators[i]=numerator/M[i][i];bounded(numerators[i]);
  }
  for(let i=0;i<n;i++){
    tick();
    let value=0n;for(let j=0;j<n;j++)value+=BigInt(matrix[i][j])*numerators[j];
    check(value===BigInt(rhs[i])*denominator,"literal exact minor replay");
  }
  return {numerators,denominator,swaps,peakBits,divisions};
}

function smallControls(){
  let checked=0;
  for(let a=-1;a<=1;a++)for(let b=-1;b<=1;b++)for(let c=-1;c<=1;c++)for(let d=-1;d<=1;d++){
    const determinant=a*d-b*c;if(determinant===0)continue;
    for(let u=-1;u<=1;u++)for(let v=-1;v<=1;v++){
      const out=fractionFreeSolve([[a,b],[c,d]],[u,v],Date.now()+1000,256);
      check(out.numerators[0]*BigInt(determinant)===BigInt(d*u-b*v)*out.denominator,"literal2x2 Cramer coordinate0");
      check(out.numerators[1]*BigInt(determinant)===BigInt(a*v-c*u)*out.denominator,"literal2x2 Cramer coordinate1");
      checked++;
    }
  }
  const M=[[0,1,1],[1,0,1],[1,1,0]],x=[2,3,5],b=M.map(row=>row.reduce((s,v,j)=>s+v*x[j],0));
  const out=fractionFreeSolve(M,b,Date.now()+1000,256);
  check(out.numerators.every((v,j)=>v===BigInt(x[j])*out.denominator),"3x3 pivot control");
  check(roundDecimalToScale(0.125,1000n)===125n&&roundDecimalToScale(1e-6,1000000n)===1n,"decimal rounding controls");
  return {literal_2x2_nonsingular_systems:checked,three_by_three_pivot_control:true,decimal_rounding_controls:true,optimizer_calls:0};
}

function prepare(input){
  const started=Date.now(),domain=loadDomain(input),rank=modularRank(domain.A,domain.b,input.coefficient_field_prime);
  check(rank.augmented_system_consistent_mod_prime,"chosen support has modular incompatibility");
  const pivot=new Set(rank.pivot_column_positions),free=[];
  const scale=BigInt(input.free_coordinate_rounding_denominator);
  for(let j=0;j<domain.selected.length;j++)if(!pivot.has(j)){
    const id=domain.selected[j],value=roundDecimalToScale(domain.values[id],scale);
    check(value>0n&&value<scale,"rounded positive free coordinate");
    free.push({support_position:j,original_column:id,numerator:String(value),denominator:String(scale)});
  }
  return {status:"one exact support reconstruction prepared; no large elimination or optimizer",
    input_object_sha256:EXPECTED_INPUT_OBJECT_SHA256,case_index:4,selected_support:domain.selected,
    selected_support_sha256:sha256Ascii(JSON.stringify(domain.selected)),
    discarded_nonzero_coordinates:domain.discarded,proved_Gram_zero_count:46,
    support_disjoint_from_proved_zeros:true,all630_rows_recovered:true,modular:rank,
    free_coordinates:free,free_scale:String(scale),maximum_exact_solve_seconds:60,
    maximum_intermediate_integer_bits:4096,small_controls:smallControls(),preparation_seconds:(Date.now()-started)/1000,
    exact_point_claimed:false,case4_excluded:false};
}

function verify(input,result){
  const domain=loadDomain(input);
  check(result.input_object_sha256===EXPECTED_INPUT_OBJECT_SHA256,"witness input binding");
  check(result.exact_Gram_point===true,"exact witness flag");
  const q=BigInt(result.common_denominator),values=result.numerators.map(BigInt);
  check(q>0n&&values.length===1214&&values.every(v=>v>=0n),"exact nonnegative rational point");
  let maximum=0n,positive=0,ones=0;
  for(const v of values){if(v>maximum)maximum=v;if(v>0n)positive++;if(v===q)ones++;}
  check(maximum<=q,"finite individual selector upper bounds");
  for(const a of input.proved_Gram_zero_columns)check(values[a]===0n,"all46 proved zeros");
  const support=new Set(domain.selected);
  for(let a=0;a<1214;a++)if(!support.has(a))check(values[a]===0n,"explicit support restriction");
  for(const [i,j,b,members] of domain.rows){
    let value=0n;for(const a of members)value+=values[a];
    check(value===BigInt(b)*q,"full original Gram row "+i+","+j);
  }
  const total=values.reduce((s,v)=>s+v,0n);check(total===64n*q,"derived population64");
  let common=q;for(const v of values)common=gcd(common,v);check(common===1n,"primitive common denominator");
  return {status:"PASS: all630 original Gram equations and every nonnegative rational coordinate",
    Gram_positions_checked:630,primary_columns_checked:1214,positive_columns:positive,unit_columns:ones,
    all46_proved_zeros_checked:true,all_individual_upper_bounds_checked:true,derived_population:64,
    common_denominator_bits:bitLength(q),maximum_numerator_bits:bitLength(maximum),
    original_signature_or_triple_capacities_claimed:false,exterior_row_cuts_or_covers_claimed:false,
    binary_incidence_or_graph_claimed:false,case4_excluded:false};
}

function solve(input,prepared){
  const started=Date.now(),deadline=started+60000;
  const domain=loadDomain(input);
  check(prepared.input_object_sha256===EXPECTED_INPUT_OBJECT_SHA256&&same(prepared.selected_support,domain.selected),"prepared support binding");
  const mod=modularRank(domain.A,domain.b,input.coefficient_field_prime);
  check(same(mod,prepared.modular),"cold modular minor replay");
  const rows=mod.independent_original_rows,cols=mod.pivot_column_positions;
  const scale=BigInt(prepared.free_scale),free=prepared.free_coordinates;
  check(scale===BigInt(input.free_coordinate_rounding_denominator),"free scale binding");
  const selectedValues=Array(domain.selected.length).fill(0n);
  const freeSet=new Set();
  for(const item of free){
    check(!freeSet.has(item.support_position)&&!cols.includes(item.support_position),"free/pivot partition");
    freeSet.add(item.support_position);
    check(domain.selected[item.support_position]===item.original_column&&BigInt(item.denominator)===scale,"free coordinate identity");
    check(BigInt(item.numerator)===roundDecimalToScale(domain.values[item.original_column],scale),"free proposal rounding replay");
    selectedValues[item.support_position]=BigInt(item.numerator);
  }
  check(freeSet.size+cols.length===domain.selected.length,"complete support partition");
  const matrix=rows.map(i=>cols.map(j=>domain.A[i][j]));
  const rhs=rows.map(i=>{
    let value=BigInt(domain.b[i])*scale;
    for(const item of free)value-=BigInt(domain.A[i][item.support_position])*BigInt(item.numerator);
    return value;
  });
  const exact=fractionFreeSolve(matrix,rhs,deadline,4096);
  let denominator=exact.denominator*scale;
  for(let j=0;j<cols.length;j++)selectedValues[cols[j]]=exact.numerators[j];
  for(const item of free)selectedValues[item.support_position]*=exact.denominator;
  if(denominator<0n){denominator=-denominator;for(let j=0;j<selectedValues.length;j++)selectedValues[j]=-selectedValues[j];}
  let common=denominator;for(const v of selectedValues)common=gcd(common,v);
  denominator/=common;for(let j=0;j<selectedValues.length;j++)selectedValues[j]/=common;
  const values=Array(1214).fill(0n);
  domain.selected.forEach((a,j)=>{values[a]=selectedValues[j];});
  const result={status:"exact proposed Gram point; full-row check pending",
    input_object_sha256:EXPECTED_INPUT_OBJECT_SHA256,preparation_object_sha256:sha256Ascii(JSON.stringify(prepared)),
    common_denominator:String(denominator),numerators:values.map(String),exact_Gram_point:true,
    exact_solve_statistics:{square_minor_order:matrix.length,row_swaps:exact.swaps,Bareiss_divisions:exact.divisions,
      maximum_intermediate_bits_checked:exact.peakBits,free_coordinate_count:free.length},
    optimizer_calls:0,case4_excluded:false};
  result.exact_check=verify(input,result);
  check(Date.now()<=deadline,"total exact reconstruction time budget");
  result.status="EXACT_RATIONAL_CASE4_GRAM_POINT";
  result.seconds=(Date.now()-started)/1000;
  return result;
}

if(typeof module!=="undefined")module.exports={loadDomain,modularRank,fractionFreeSolve,smallControls,prepare,solve,verify};
if(typeof require!=="undefined"&&typeof module!=="undefined"&&require.main===module){
  const fs=require("fs"),args=process.argv.slice(2),mode=args[0];
  const input=JSON.parse(fs.readFileSync(args[1],"utf8"));
  let out,destination;
  if(mode==="prepare"){out=prepare(input);destination=args[2];}
  else if(mode==="solve"){out=solve(input,JSON.parse(fs.readFileSync(args[2],"utf8")));destination=args[3];}
  else if(mode==="verify"){out=verify(input,JSON.parse(fs.readFileSync(args[2],"utf8")));destination=args[3];}
  else throw new Error("mode must be prepare, solve or verify");
  check(!fs.existsSync(destination),"fresh output required");
  fs.writeFileSync(destination,JSON.stringify(out,null,2)+"\n");
  console.log(JSON.stringify(out.status));
}
