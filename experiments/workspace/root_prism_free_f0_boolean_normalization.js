"use strict";
// Exact Boolean normalizations. No optimizer or model query is used here.
function check(condition, message) { if (!condition) throw new Error(message); }
function integer(value) {
  if (typeof value === "bigint") return value;
  if (typeof value === "number") { check(Number.isSafeInteger(value), "safe input integer"); return BigInt(value); }
  check(typeof value === "string" && /^-?\d+$/.test(value), "integer string");
  return BigInt(value);
}
function gcd(a,b) { a=a<0n?-a:a; b=b<0n?-b:b; while(b){const r=a%b;a=b;b=r;} return a; }
function id(value) { check(Number.isSafeInteger(value)&&value>=0,"nonnegative variable id");return value; }
function signedTerms(terms) {
  const seen=new Set();
  return terms.map(([a,c])=>{id(a);check(!seen.has(a),"distinct variable ids");seen.add(a);c=integer(c);check(c!==0n,"nonzero coefficient");return[a,c];}).sort((x,y)=>x[0]-y[0]);
}
function normalizeGuarded(target, weights, demand) {
  id(target);const d=integer(demand);check(d>0n,"positive guarded demand");
  const raw=signedTerms(weights);check(raw.every(([a,w])=>a!==target&&w>0n),"positive distinct non-guard weights");
  const capped=raw.map(([a,w])=>[a,w<d?w:d]);
  const g=capped.length?capped.reduce((z,[,w])=>gcd(z,w),0n):1n;
  const normalized=capped.map(([a,w])=>[a,w/g]), bound=(d+g-1n)/g;
  return {target,raw_demand:d,capped_weights:capped,divisor:g,demand:bound,weights:normalized,
    terms:[[target,bound],...normalized.map(([a,w])=>[a,-w])].sort((x,y)=>x[0]-y[0]),rhs:0n};
}
function normalizeShared(terms) {
  const raw=signedTerms(terms),d=raw.reduce((z,[,c])=>z+(c>0n?c:0n),0n);
  if(d===0n)return {tautology:true,positive_threshold:0n,divisor:1n,threshold:0n,literals:[],terms:[],rhs:0n};
  // c>0 contributes c*(1-z); c<0 contributes (-c)*z to an at-least threshold d.
  const capped=raw.map(([a,c])=>({id:a,positive:c<0n,weight:(c<0n?-c:c)<d?(c<0n?-c:c):d}));
  const g=capped.reduce((z,x)=>gcd(z,x.weight),0n), threshold=(d+g-1n)/g;
  const literals=capped.map(x=>({...x,weight:x.weight/g}));
  const normalized=literals.map(x=>[x.id,x.positive?-x.weight:x.weight]);
  const constant=literals.reduce((z,x)=>z+(x.positive?0n:x.weight),0n);
  // Since each original positive c is <=d, its weight is not capped and g divides their sum d.
  check(d%g===0n&&constant===threshold,"homogeneous shared expansion");
  return {tautology:false,positive_threshold:d,divisor:g,threshold,literals,terms:normalized,rhs:constant-threshold};
}
function evaluate(terms, numerators) {
  return terms.reduce((s,[a,c])=>s+integer(c)*integer(numerators[a]||0),0n);
}
function normalizationControls() {
  let individual=0,shared=0,big=0;
  for(let n=0;n<=4;n++){
    const choices=4**n;
    for(let code=0;code<choices;code++){
      let k=code;const w=[];for(let i=0;i<n;i++){w.push([i+1,BigInt(1+k%4)]);k=Math.floor(k/4);}
      for(let d=1;d<=8;d++){
        const norm=normalizeGuarded(0,w,d),raw=[[0,BigInt(d)],...w.map(([a,c])=>[a,-c])];
        for(let mask=0;mask<(1<<(n+1));mask++){
          const z=Array.from({length:n+1},(_,j)=>(mask>>j)&1);
          check((evaluate(raw,z)<=0n)===(evaluate(norm.terms,z)<=norm.rhs),"guarded Boolean equivalence");
          individual++;
        }
      }
    }
  }
  for(let n=0;n<=4;n++){
    const choices=7**n;
    for(let code=0;code<choices;code++){
      let k=code;const terms=[];
      for(let i=0;i<n;i++){const c=BigInt(k%7-3);if(c)terms.push([i,c]);k=Math.floor(k/7);}
      const norm=normalizeShared(terms);
      for(let mask=0;mask<(1<<n);mask++){
        const z=Array.from({length:n},(_,j)=>(mask>>j)&1);
        check((evaluate(terms,z)<=0n)===(evaluate(norm.terms,z)<=norm.rhs),"shared Boolean equivalence");
        shared++;
      }
    }
  }
  const huge=(1n<<85n)+3n;
  const ng=normalizeGuarded(0,[[1,(1n<<88n)+7n],[2,2n*huge+1n]],huge);
  const rawg=[[0,huge],[1,-((1n<<88n)+7n)],[2,-(2n*huge+1n)]];
  for(let mask=0;mask<8;mask++){
    const z=Array.from({length:3},(_,j)=>(mask>>j)&1);
    check((evaluate(rawg,z)<=0n)===(evaluate(ng.terms,z)<=0n),"large guarded");big++;
  }
  const raws=[[0,(1n<<82n)+1n],[1,-((1n<<84n)+3n)]],ns=normalizeShared(raws);
  for(let mask=0;mask<4;mask++){
    const z=[mask&1,(mask>>1)&1];
    check((evaluate(raws,z)<=0n)===(evaluate(ns.terms,z)<=0n),"large shared");big++;
  }
  const examples=[
    {name:"guarded weight cap",raw:[[0,3n],[1,-5n],[2,-1n]],normalized:normalizeGuarded(0,[[1,5n],[2,1n]],3n).terms,numerators:[5,3,0],denominator:5},
    {name:"guarded integer ceiling",raw:[[0,3n],[1,-2n],[2,-2n]],normalized:normalizeGuarded(0,[[1,2n],[2,2n]],3n).terms,numerators:[2,2,1],denominator:2},
    {name:"shared complement weight cap",raw:[[0,2n],[1,-5n]],normalized:normalizeShared([[0,2n],[1,-5n]]).terms,numerators:[5,2],denominator:5}
  ];
  for(const x of examples)check(evaluate(x.raw,x.numerators)===0n&&evaluate(x.normalized,x.numerators)>0n,"strict fractional example");
  return {status:"PASS: exact Boolean-equivalence and strict fractional controls",individual_boolean_assignments:individual,
    shared_boolean_assignments:shared,large_integer_assignments:big,largest_control_coefficient_bits:89,
    strict_fractional_examples:examples.map(x=>({name:x.name,denominator:x.denominator,raw_numerator:String(evaluate(x.raw,x.numerators)),normalized_violation_numerator:String(evaluate(x.normalized,x.numerators))})),
    optimizer_called:false};
}
if(typeof module!=="undefined")module.exports={integer,gcd,signedTerms,normalizeGuarded,normalizeShared,evaluate,normalizationControls};
