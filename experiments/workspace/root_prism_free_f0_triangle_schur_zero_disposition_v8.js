(() => {
"use strict";
const assert=(ok,m)=>{if(!ok)throw Error(m);};
function classifyRecords(records,edgeIds,zeros){
 const output=[],retained=[];
 for(let id=0;id<records.length;id++){
  const [a,b,c]=records[id],pairs=[[a,b],[a,c],[b,c]];
  const ids=pairs.map(p=>edgeIds.get(p.join(",")));assert(ids.every(Number.isInteger),"missing triangle edge");
  const proofs=ids.filter(e=>zeros.has(e)).map(e=>zeros.get(e));
  if(proofs.length)output.push({record_id:id,triangle:[a,b,c],edge_ids:ids,disposition:"OLD_LITERAL_EDGE_ZERO",zero_premises:proofs});
  else{output.push({record_id:id,triangle:[a,b,c],edge_ids:ids,disposition:"NOT_REJECTED_BY_LITERAL_EDGE_ZERO"});retained.push(id);}
 }
 return {ledger:output,retained_record_ids:retained};
}
function controls(){
 const ids=new Map([["0,1",0],["0,2",1],["1,2",2],["0,3",3],["1,3",4]]);
 const zero=new Map([[1,{edge_id:1,native_row_index:17}]]);
 const r=classifyRecords([[0,1,2],[0,1,3]],ids,zero);
 assert(r.ledger[0].zero_premises[0].edge_id===1&&r.retained_record_ids.join(",")==="1","classification controls");
 let rejected=0;try{classifyRecords([[0,2,3]],ids,zero);}catch(e){rejected++;}
 assert(rejected===1,"missing edge rejection");
 return {status:"PASS_LITERAL_ZERO_TRIANGLE_DISPOSITION_CONTROLS",accepted_examples:2,rejected_missing_edge:1};
}
function run(domain,overlay,census,sha256Text){
 const started=Date.now(),edges=[];
 for(let a=0;a<480;a++)for(const b of domain.possible_neighbor_signature_ids[a])if(a<b)edges.push([a,b]);
 assert(edges.length===68394&&sha256Text(JSON.stringify(edges))===overlay.complete_edge_order_sha256,"edge order binding");
 const edgeIds=new Map(edges.map((e,i)=>[e.join(","),i])),zeros=new Map();
 assert(overlay.status==="COMPLETE_LITERAL_PRISM_ZEROS_AND_CORE_PAIR_CLIQUES"&&overlay.zero_rows.length===1884,"overlay status");
 for(let i=0;i<overlay.zero_rows.length;i++){
  const r=overlay.zero_rows[i];
  assert(Number.isInteger(r.edge_id)&&r.edge_id>=0&&r.edge_id<edges.length&&!zeros.has(r.edge_id),"unique zero edge");
  assert(r.variable_index===540+r.edge_id&&r.native_row_index===163070+i,"native zero location");
  assert(r.witness.kind==="P"&&JSON.stringify(r.witness.pair)===JSON.stringify(edges[r.edge_id]),"prism witness endpoint binding");
  zeros.set(r.edge_id,{edge_id:r.edge_id,native_row_index:r.native_row_index,variable_index:r.variable_index,witness_index:r.witness_index});
 }
 assert(census.status==="COMPLETE_EXACT_TRIANGLE_PRINCIPAL_MINOR_CENSUS","census status");
 const plus=census.families.find(f=>f.family==="plus"),records=plus.nonpositive_determinant_records_with_nonnegative_proper_minors;
 assert(records.length===10830&&records.every(r=>BigInt(r[3])<0n),"negative triangle family");
 const result=classifyRecords(records,edgeIds,zeros);
 assert(result.ledger.length===records.length&&Date.now()-started<10000,"disposition scope/bound");
 return {schema:"conway99.f0.triangle-schur-literal-zero-disposition.v1",status:"COMPLETE_LITERAL_EDGE_ZERO_DISPOSITION",
  tested_triangles:records.length,old_literal_edge_zero:records.length-result.retained_record_ids.length,
  not_rejected_by_literal_edge_zero:result.retained_record_ids.length,...result,seconds:(Date.now()-started)/1000,
  other_native_or_prism_constraints_tested:false,logical_independence_claimed:false,new_native_model_built:false,optimizer_calls:0};
}
return {controls,run};
})()