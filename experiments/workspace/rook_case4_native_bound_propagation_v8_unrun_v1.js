/* Exact Boolean bound propagation for a supplied native-row inventory.
All arithmetic is safe integer arithmetic; every accepted force has a sequential original-row reason.
No optimizer, native model, or coordinate-cover registry is called. */
(() => {
"use strict";
function assert(ok,msg){if(!ok)throw Error(msg);}
function normalized(kind,id,terms,lower,upper,extra={}){
 const m=new Map();for(const [a,c]of terms){assert(Number.isSafeInteger(a)&&a>=0&&a<1214&&Number.isSafeInteger(c),"term");m.set(a,(m.get(a)||0)+c);}
 const t=[...m].filter(([a,c])=>c!==0).sort((x,y)=>x[0]-y[0]);
 assert(Number.isSafeInteger(lower)&&Number.isSafeInteger(upper)&&lower<=upper,"endpoints");
 assert(Number.isSafeInteger(t.reduce((s,[a,c])=>s+Math.abs(c),0)),"integer activity");
 return {kind,original_id:id,terms:t,lower,upper,...extra};
}
function nativeRows(I){
 const r=[];
 I.Gram_rows.forEach((g,id)=>r.push(normalized("Gram",id,g[3].map(a=>[a,1]),g[2],g[2],{core_pair:g.slice(0,2)})));
 I.original_signature_rows.forEach((g,id)=>r.push(normalized("signature",id,g[1].map(a=>[a,1]),0,1,{signature:g[0]})));
 I.triple_rows.forEach((g,id)=>r.push(normalized("triple",id,g.members.map(a=>[a,1]),0,1,{core_triple:g.triple})));
 I.Gram_conflict_clauses.forEach((g,id)=>{assert(g.every(v=>v<0),"all-negative conflict");r.push(normalized("Gram_conflict",id,g.map(v=>[-v-1,1]),0,g.length-1));});
 I.uncapped_integer_cuts.forEach((g,id)=>{
  const terms=g.positive_terms.map(([a,w])=>[a,w]);assert(terms.every(([a,w])=>w>0),"positive cut terms");
  const upper=terms.reduce((s,[a,w])=>s+w,0);terms.push([g.target_column,-g.positive_demand]);
  r.push(normalized("uncapped_exterior_row",id,terms,0,upper,{original_target:g.target_column}));
 });
 assert(r.length===2271,"all native rows");
 return r;
}
function extrema(row,x){
 let lo=0,hi=0;for(const [a,c]of row.terms){if(x[a]<0){lo+=Math.min(0,c);hi+=Math.max(0,c);}else lo+=c*x[a],hi+=c*x[a];}
 return [lo,hi];
}
function oppositeOutside(row,x,a,value){
 let lo=0,hi=0;
 for(const [b,c]of row.terms){const v=b===a?1-value:x[b];if(v<0){lo+=Math.min(0,c);hi+=Math.max(0,c);}else{lo+=c*v;hi+=c*v;}}
 return {lo,hi,excluded:hi<row.lower||lo>row.upper};
}
function propagate(rows,seeds,limits={milliseconds:60000,maximum_row_visits:3000000}){
 const started=Date.now(),x=Array(1214).fill(-1),members=Array.from({length:1214},()=>[]),trace=[],queue=[],pending=rows.map(()=>false);
 for(const [a,v]of seeds){assert(x[a]===-1 || x[a]===v,"seed conflict");assert(v===0||v===1,"seed bit");x[a]=v;}
 rows.forEach((r,i)=>{for(const [a,c]of r.terms)members[a].push(i);queue.push(i);pending[i]=true;});
 let visits=0,head=0,terminal=null;
 function enqueue(i){if(!pending[i]){pending[i]=true;queue.push(i);}}
 while(head<queue.length){
  if(Date.now()-started>limits.milliseconds || visits>=limits.maximum_row_visits){terminal={status:"partial",reason:"finite resource bound"};break;}
  const id=queue[head++],row=rows[id];pending[id]=false;visits++;
  let [lo,hi]=extrema(row,x);
  if(hi<row.lower || lo>row.upper){terminal={status:"contradiction",row:id,lo,hi,lower:row.lower,upper:row.upper};break;}
  for(const [a,c]of row.terms)if(x[a]<0){
   const lo0=lo-Math.min(0,c),hi0=hi-Math.max(0,c),lo1=lo0+c,hi1=hi0+c;
   const zero=!(hi0<row.lower||lo0>row.upper),one=!(hi1<row.lower||lo1>row.upper);
   if(!zero&&!one){terminal={status:"contradiction_by_binary_split",row:id,variable:a,lo0,hi0,lo1,hi1,lower:row.lower,upper:row.upper};break;}
   if(zero===one)continue;
   const value=one?1:0;
   trace.push({row:id,variable:a,value,before_min:lo,before_max:hi,coefficient:c,excluded_value:1-value,excluded_min:value?lo0:lo1,excluded_max:value?hi0:hi1});
   x[a]=value;lo=lo0+c*value;hi=hi0+c*value;
   for(const rid of members[a])enqueue(rid);
  }
  if(terminal)break;
 }
 if(!terminal)terminal={status:"fixed_point"};
 return {schema:"rook-case4-native-exact-bound-propagation-v1",terminal,seeds,trace,assignment:x,row_visits:visits,limits,elapsed_ms:Date.now()-started,cover_registry_included:false,optimizer_calls:0};
}
function replay(rows,record){
 const x=Array(1214).fill(-1);
 for(const [a,v]of record.seeds){assert(x[a]===-1||x[a]===v,"seed conflict");x[a]=v;}
 for(let k=0;k<record.trace.length;k++){
  const t=record.trace[k],row=rows[t.row];assert(x[t.variable]===-1,"no repeated force");
  const [lo,hi]=extrema(row,x);assert(lo===t.before_min&&hi===t.before_max,"sequential extrema");
  assert(!(hi<row.lower||lo>row.upper),"earlier contradiction");
  const opp=oppositeOutside(row,x,t.variable,t.value);
  assert(opp.excluded && opp.lo===t.excluded_min && opp.hi===t.excluded_max,"excluded opposite branch");
  assert(row.terms.some(([a,c])=>a===t.variable&&c===t.coefficient),"original coefficient");x[t.variable]=t.value;
 }
 assert(JSON.stringify(x)===JSON.stringify(record.assignment),"final assignment");
 const z=record.terminal;
 if(z.status==="contradiction"){const [lo,hi]=extrema(rows[z.row],x);assert(lo===z.lo&&hi===z.hi&&(hi<rows[z.row].lower||lo>rows[z.row].upper),"terminal contradiction");}
 else if(z.status==="contradiction_by_binary_split"){
  assert(x[z.variable]===-1,"split free");
  for(const v of [0,1]){const y=x.slice();y[z.variable]=v;const [lo,hi]=extrema(rows[z.row],y);assert(hi<rows[z.row].lower||lo>rows[z.row].upper,"split contradiction");}
 }else if(z.status==="fixed_point"){
  for(const row of rows){const [lo,hi]=extrema(row,x);assert(!(hi<row.lower||lo>row.upper),"fixed point consistency");
   for(const [a,c]of row.terms)if(x[a]<0)for(const v of [0,1])assert(!oppositeOutside(row,x,a,v).excluded,"fixed point exhaustion");
  }
 }else assert(z.status==="partial","terminal status");
 return {status:"PASS",terminal_status:z.status,forces:record.trace.length,zeros:x.filter(v=>v===0).length,ones:x.filter(v=>v===1).length,all_row_fixed_point_checked:z.status==="fixed_point",optimizer_calls:0};
}
function controls(){
 let partial_extrema=0,conditioned_extrema=0,bound_implications=0;
 for(let n=0;n<=3;n++){
  const coeff=Array(n).fill(-2);
  function cs(i){if(i<n){for(let c=-2;c<=2;c++){coeff[i]=c;cs(i+1);}return;}
   const state=Array(n).fill(-1);
   function st(j){if(j<n){for(const v of [-1,0,1]){state[j]=v;st(j+1);}return;}
    const vertices=[];
    for(let bits=0;bits<(1<<n);bits++){const x=Array.from({length:n},(_,k)=>(bits>>k)&1);if(x.some((v,k)=>state[k]>=0&&state[k]!==v))continue;vertices.push({x,value:x.reduce((s,v,k)=>s+v*coeff[k],0)});}
    const row={terms:coeff.map((c,a)=>[a,c]),lower:0,upper:0};
    const [lo,hi]=extrema(row,state);assert(lo===Math.min(...vertices.map(v=>v.value))&&hi===Math.max(...vertices.map(v=>v.value)),"literal extrema control");partial_extrema++;
    for(let a=0;a<n;a++)if(state[a]<0)for(const v of [0,1]){
     const sub=vertices.filter(t=>t.x[a]===v),y=state.slice();y[a]=v;const [l,h]=extrema(row,y);
     assert(l===Math.min(...sub.map(t=>t.value))&&h===Math.max(...sub.map(t=>t.value)),"conditioned literal extrema control");conditioned_extrema++;
    }
    for(let lower=-6;lower<=6;lower++)for(let upper=lower;upper<=6;upper++){
     row.lower=lower;row.upper=upper;const feasible=vertices.filter(t=>t.value>=lower&&t.value<=upper);
     if(hi<lower||lo>upper)assert(feasible.length===0,"literal contradiction control");
     for(let a=0;a<n;a++)if(state[a]<0)for(const v of [0,1])if(oppositeOutside(row,state,a,v).excluded)assert(feasible.every(t=>t.x[a]===v),"literal force control");
     bound_implications++;
    }
   }st(0);
  }cs(0);
 }
 return {status:"PASS",partial_extrema,conditioned_extrema,bound_implications,all_coefficients:[-2,-1,0,1,2],maximum_variables:3,optimizer_calls:0,case4_propagation_calls:0};
}
return {normalized,nativeRows,extrema,propagate,replay,controls};
})()
