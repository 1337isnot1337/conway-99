(() => {
"use strict";
function assert(b,m){if(!b)throw Error(m);}
function run(I,p){
 const H=new Set(p.H);assert(H.size===42,"H cardinality");
 function expand(rows){let b=0;const c=Array(1214).fill(0);for(const [id,w]of rows){b+=w*I.Gram_rows[id][2];for(const a of I.Gram_rows[id][3])c[a]+=w;}return {b,c};}
 const parity=expand(p.parity.original_Gram_rows.map(id=>[id,1]));
 assert(parity.b===81&&parity.c.every((c,a)=>c===p.parity.full1214_coefficients[a]),"parity original coefficient replay");
 const nz=new Set(p.needed_proved_zero_columns),odd=parity.c.map((c,a)=>[c,a]).filter(([c,a])=>(c&1)&&!nz.has(a)).map(([c,a])=>a);
 assert(JSON.stringify(odd)===JSON.stringify(p.H),"parity support");
 const five=expand(p.upper_five.original_Gram_rows.map(id=>[id,1]));
 assert(five.b===5&&five.c.every((c,a)=>c-(H.has(a)?1:0)===p.upper_five.full1214_residual[a]&&p.upper_five.full1214_residual[a]>=0),"upper five");
 const b922=expand(p.bound922.original_Gram_rows);
 assert(b922.b===7&&b922.c.every((c,a)=>c-(H.has(a)?1:0)-(a===922?3:0)===p.bound922.full1214_nonnegative_residual[a]&&p.bound922.full1214_nonnegative_residual[a]>=0),"bound922");
 const b600=expand(p.bound600.direct_Gram_rows);
 assert(b600.b===18&&b600.c.every((c,a)=>c-3*(H.has(a)?1:0)-(a===600?4:0)===p.bound600.full1214_residual[a]),"bound600 full identity");
 assert(p.bound600.full1214_residual.every((c,a)=>a===783?c===-1:c>=0)&&nz.has(783),"sole negative zero");
 const q=I.Gram_rows[p.mutual_capacity.original_Gram_row];assert(q[2]===1&&q[3].includes(600)&&q[3].includes(922),"mutual capacity");
 const expected=p.H.map(a=>[a,1]).concat([[600,2],[922,2]]).sort((a,b)=>a[0]-b[0]);assert(JSON.stringify(expected)===JSON.stringify(p.final_integer_inequality.terms)&&p.final_integer_inequality.upper===5,"final integer cut");
 let checked=0;for(const v of [1,3,5])for(const a of [0,1])for(const b of [0,1])if(a+b<=1&&v+3*b<=7&&3*v+4*a<=18){assert(v+2*(a+b)<=5,"integer consequence");checked++;}
 return {status:"PASS",all_original_coordinates:1214,integer_cases_checked:checked,original_row_identities:4,optimizer_calls:0,propagation_repeated:false};
}
return {run};
})()