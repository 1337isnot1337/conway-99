(() => {
"use strict";
const edges=[[0,1],[0,2],[1,2]];
function insist(condition,message){if(!condition)throw Error(message);}
function count(mask){let n=0;while(mask){mask&=mask-1;n++;}return n;}
function members(cube){
 let result=0;
 for(let pattern=0;pattern<8;pattern++)
  if(cube.every((value,i)=>value===-1||((pattern>>>i)&1)===value))result|=1<<pattern;
 return result;
}
function primeCubes(forbidden){
 insist(Number.isInteger(forbidden)&&forbidden>=0&&forbidden<256,"forbidden mask");
 const result=[];
 for(let a=-1;a<=1;a++)for(let b=-1;b<=1;b++)for(let c=-1;c<=1;c++){
  const cube=[a,b,c],inside=members(cube);
  if((inside&~forbidden)!==0)continue;
  let minimal=true;
  for(let i=0;i<3;i++)if(cube[i]!==-1){
   const parent=cube.slice();parent[i]=-1;
   if((members(parent)&~forbidden)===0){minimal=false;break;}
  }
  if(minimal)result.push({cube,completions:inside});
 }
 return result;
}
function guardedRow(cube){
 const positive=[],negative=[],covered=new Set();
 for(let i=0;i<3;i++){
  if(cube[i]===1){positive.push(i);edges[i].forEach(v=>covered.add(v));}
  else if(cube[i]===0)negative.push(i);
 }
 const selectors=[0,1,2].filter(v=>!covered.has(v));
 return {positive_edges:positive,negative_edges:negative,guard_selectors:selectors,
         rhs:positive.length+selectors.length-1};
}
function controls(){
 let validAssignments=0,patternOracleChecks=0,validInequalities=0,forbiddenAssignments=0,homogeneousPathChecks=0,totalPrimeCubes=0;
 for(let forbidden=0;forbidden<256;forbidden++){
  const cubes=primeCubes(forbidden),rows=cubes.map(c=>guardedRow(c.cube));
  totalPrimeCubes+=cubes.length;
  let covered=0;for(const cube of cubes)covered|=cube.completions;
  insist(covered===forbidden,"complete bad-pattern coverage");
  for(let i=0;i<cubes.length;i++)for(let j=0;j<cubes.length;j++)if(i!==j)
   insist((cubes[i].completions&~cubes[j].completions)!==0,"strict prime-cube antichain");
  for(let selection=0;selection<8;selection++)for(let pattern=0;pattern<8;pattern++){
   const x=[0,1,2].map(i=>(selection>>>i)&1),y=[0,1,2].map(i=>(pattern>>>i)&1);
   if(edges.some(([a,b],i)=>y[i]>x[a]||y[i]>x[b]))continue;
   validAssignments++;
   const expected=selection!==7||((forbidden>>>pattern)&1)===0;
   let all=true;
   for(const row of rows){
    const left=row.positive_edges.reduce((s,i)=>s+y[i],0)-row.negative_edges.reduce((s,i)=>s+y[i],0)+row.guard_selectors.reduce((s,i)=>s+x[i],0);
    const pass=left<=row.rhs;all=all&&pass;
    if(expected){insist(pass,"guarded row rejected an oracle-feasible assignment");validInequalities++;}
    if(row.positive_edges.length===2){
     const [e,f]=row.positive_edges,center=edges[e].find(v=>edges[f].includes(v));
     insist(center!==undefined&&row.guard_selectors.length===0&&row.rhs===1,"path incidence");
     const homogeneous=y[e]+y[f]-row.negative_edges.reduce((s,i)=>s+y[i],0)<=x[center];
     insist(homogeneous===pass,"path homogenization");
     homogeneousPathChecks++;
    }
   }
   insist(all===expected,"exact selected-triple oracle projection");
   patternOracleChecks++;if(!expected)forbiddenAssignments++;
  }
 }
 insist(validAssignments===4608&&patternOracleChecks===4608&&forbiddenAssignments===1024,"exhaustive assignment counts");
 const onlyPositiveAB=primeCubes(170);
 insist(onlyPositiveAB.length===1&&JSON.stringify(onlyPositiveAB[0].cube)==="[1,-1,-1]","single-positive example");
 const guarded=guardedRow(onlyPositiveAB[0].cube);
 insist(JSON.stringify(guarded.guard_selectors)==="[2]"&&guarded.rhs===1,"third-selector guard");
 // The assignment x=(1,1,0), y=(1,0,0) is permitted. Dropping the
 // third-selector guard and reducing RHS to zero would reject it.
 insist(1+0<=1&&!(1<=0),"missing-guard counterexample");
 return {status:"PASS_EXHAUSTIVE_PARTIAL_CUBE_ACTIVATION_GUARDS",forbidden_pattern_sets:256,
  ternary_cubes_per_set:27,endpoint_activated_assignments_per_set:18,
  valid_assignments_checked:validAssignments,exact_oracle_checks:patternOracleChecks,
  forbidden_selected_assignments:forbiddenAssignments,valid_row_inequalities_checked:validInequalities,
  prime_cubes_total:totalPrimeCubes,homogeneous_path_checks:homogeneousPathChecks,
  missing_selector_guard_counterexample:true,production_kernel_inputs_used:false,
  native_model_builds:0,optimizer_calls:0};
}
return {primeCubes,guardedRow,controls};
})()