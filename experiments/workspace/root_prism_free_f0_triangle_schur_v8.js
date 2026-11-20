(() => {
"use strict";
const VERSION="conway99.f0.exterior-triangle-schur-census.v1";
function insist(ok,message){if(!ok)throw Error(message);}
function popcount(n){let c=0;while(n){n&=n-1;c++;}return c;}
function pairId(a,b){if(a>b)[a,b]=[b,a];insist(a<b,"distinct pair");return a*(959-a)/2+b-a-1;}
function det3(a,b,c,d,e,f){return a*b*c+2*d*e*f-a*f*f-b*e*e-c*d*d;}
function det3Big(a,b,c,d,e,f){return a*b*c+2n*d*e*f-a*f*f-b*e*e-c*d*d;}
function detPermutation(m){
 const permutations=[[0,1,2],[0,2,1],[1,0,2],[1,2,0],[2,0,1],[2,1,0]];
 let total=0n;
 for(const p of permutations){let inversions=0;for(let i=0;i<3;i++)for(let j=i+1;j<3;j++)if(p[i]>p[j])inversions++;
  total+=(inversions%2?-1n:1n)*m[0][p[0]]*m[1][p[1]]*m[2][p[2]];}
 return total;
}
function controls(){
 let tested=0,negative=0,zero=0,positive=0;
 for(let a=-1;a<=1;a++)for(let b=-1;b<=1;b++)for(let c=-1;c<=1;c++)
 for(let d=-1;d<=1;d++)for(let e=-1;e<=1;e++)for(let f=-1;f<=1;f++){
  const x=[a,b,c,d,e,f].map(BigInt),[A,B,C,D,E,F]=x;
  const wanted=detPermutation([[A,D,E],[D,B,F],[E,F,C]]),actual=det3Big(...x);
  insist(actual===wanted&&BigInt(det3(a,b,c,d,e,f))===wanted,"determinant control");
  tested++;if(actual<0n)negative++;else if(actual===0n)zero++;else positive++;
 }
 insist(tested===729,"control coverage");
 // Positive, singular PSD, and indefinite examples have the same positive 1x1/2x2 tests.
 insist(det3(1,1,1,0,0,0)===1,"positive example");
 insist(det3(2,2,2,-1,-1,-1)===0,"singular example");
 insist(det3(3,3,3,-2,-2,-2)===-25,"negative example");
 return {status:"PASS_TRIANGLE_DETERMINANT_CONTROLS",matrices:tested,negative,zero,positive,explicit_examples:3};
}
function run(domain,kernels,audit,sha256Text,options={}){
 const started=Date.now(),maximumMs=options.maximum_ms??60000,maximumRecords=options.maximum_records??500000;
 insist(maximumMs>0&&maximumMs<=60000&&maximumRecords<=500000,"bounds");
 const tick=()=>insist(Date.now()-started<maximumMs,"triangle census deadline");
 const core=domain.component_core_rows,triples=domain.signature_domain,q=domain.row_targets,neighbors=domain.possible_neighbor_signature_ids;
 insist(core.length===21&&triples.length===480&&q.length===480&&neighbors.length===480,"domain dimensions");
 insist(JSON.stringify(core)==="[510,32261,2064387,33297,66569,133185,266273,532737,1065089,67594,40978,262690,147522,1049730,528642,132108,524820,36900,1050692,82052,270596]","fixed core");
 for(let i=0;i<21;i++){insist(((core[i]>>>i)&1)===0,"core loop");for(let j=0;j<21;j++)insist(((core[i]>>>j)&1)===((core[j]>>>i)&1),"core symmetry");}
 const adjacency=core.slice(3).map(x=>x>>>3);insist(adjacency.every(x=>popcount(x)===3),"component degree");
 const masks=triples.map((t,a)=>{
  insist(t.length===3&&t.every((x,i)=>Number.isInteger(x)&&x>=0&&x<18&&(i===0||t[i-1]<x)),"signature");
  if(a)insist(t[0]>triples[a-1][0]||(t[0]===triples[a-1][0]&&(t[1]>triples[a-1][1]||(t[1]===triples[a-1][1]&&t[2]>triples[a-1][2]))),"signature order");
  return t.reduce((s,i)=>s|(1<<i),0);
 });
 for(let a=0;a<480;a++){
  insist(q[a].length===18,"quota size");
  for(let i=0;i<18;i++)insist(q[a][i]===2-((masks[a]>>>i)&1)-popcount(adjacency[i]&masks[a]),"quota reconstruction");
  insist(q[a].every(x=>x>=0&&x<=2)&&q[a].reduce((s,x)=>s+x,0)===24,"quota bounds");
 }
 const edge=new Uint8Array(480*480),disjointHigher=Array.from({length:480},()=>[]),recovered=Array.from({length:480},()=>[]);
 let eligible=0,disjointEdges=0;
 for(let a=0;a<480;a++)for(let b=a+1;b<480;b++){
  const common=popcount(masks[a]&masks[b]);
  if(common>1||!triples[b].every(i=>q[a][i]>0)||!triples[a].every(i=>q[b][i]>0))continue;
  edge[a*480+b]=edge[b*480+a]=1;recovered[a].push(b);recovered[b].push(a);eligible++;
  if(common===0){disjointHigher[a].push(b);disjointEdges++;}
 }
 insist(eligible===68394&&JSON.stringify(recovered)===JSON.stringify(neighbors),"complete edge reconstruction");
 insist(kernels.source_sha256==="141392693e8d4b7e140c329cfa4128b8794bd376713558394ef014975e2fc63f","kernel source");
 insist(kernels.kernels.length===2&&audit.families.length===2,"kernel families");
 const families=kernels.kernels.map((k,index)=>{
  const expected=index===0?"plus":"minus",divisor=index===0?1:11;
  insist(k.family===expected&&k.common_numerator_divisor===divisor&&k.diagonal_x.length===480&&k.off_diagonal_Z.length===114960,"kernel metadata");
  insist(k.Y===(index===0?-540:2797080)&&k.Schur_coefficient_denominator===(index===0?60:254280),"kernel scaling");
  insist(k.diagonal_x.concat(k.off_diagonal_Z,[k.Y]).every(v=>Number.isSafeInteger(v)&&v%divisor===0),"kernel integers");
  const diagonal=k.diagonal_x.map(v=>v/divisor),off=k.off_diagonal_Z.map(v=>v/divisor),y=k.Y/divisor;
  insist(diagonal.every(v=>v>0),"positive singletons");
  const ordered=[];for(let a=0;a<480;a++)for(let b=a;b<480;b++)ordered.push(a===b?diagonal[a]:off[pairId(a,b)]);ordered.push(y);
  const primitiveHash=sha256Text(JSON.stringify(ordered));
  insist(primitiveHash===k.primitive_kernel_sha256&&primitiveHash===audit.families[index].primitive_kernel_sha256,"independent primitive kernel hash");
  const edgeOff=off.map(v=>v+y);let bound=0;
  for(const value of diagonal)bound=Math.max(bound,Math.abs(value));
  for(const value of edgeOff)bound=Math.max(bound,Math.abs(value));
  if(index===0)insist(6n*BigInt(bound)**3n<(1n<<53n),"exact Number determinant bound");
  let negativePairs=[],zeroPairs=0,minMinor=null;
  for(let a=0;a<480;a++)for(let b=a+1;b<480;b++)if(edge[a*480+b]){
   const p=pairId(a,b),minor=BigInt(diagonal[a])*BigInt(diagonal[b])-BigInt(edgeOff[p])**2n;
   if(minMinor===null||minor<minMinor)minMinor=minor;
   if(minor<0n)negativePairs.push([a,b,minor.toString()]);else if(minor===0n)zeroPairs++;
  }
  tick();
  return {family:expected,diagonal,off:edgeOff,bigDiagonal:diagonal.map(BigInt),bigOff:edgeOff.map(BigInt),
   negativePairs,zeroPairs,minimum_edge_minor:minMinor.toString(),primitiveHash,
   counts:{negative_proper_minor:0,negative_determinant:0,zero_determinant:0,positive_determinant:0},
   minimum_determinant:null,maximum_determinant:null,records:[]};
 });
 let triangles=0;
 for(let a=0;a<480;a++){
  tick();const n=disjointHigher[a];
  for(let bi=0;bi<n.length;bi++)for(let ci=bi+1;ci<n.length;ci++){
   const b=n[bi],c=n[ci];if((masks[b]&masks[c])!==0||edge[b*480+c]===0)continue;
   triangles++;const ab=pairId(a,b),ac=pairId(a,c),bc=pairId(b,c);
   for(let index=0;index<2;index++){
    const f=families[index],A=f.bigDiagonal[a],B=f.bigDiagonal[b],C=f.bigDiagonal[c],D=f.bigOff[ab],E=f.bigOff[ac],F=f.bigOff[bc];
    const proper=[A*B-D*D,A*C-E*E,B*C-F*F];
    const determinant=index===0?BigInt(det3(f.diagonal[a],f.diagonal[b],f.diagonal[c],f.off[ab],f.off[ac],f.off[bc])):det3Big(A,B,C,D,E,F);
    if(f.minimum_determinant===null||determinant<f.minimum_determinant)f.minimum_determinant=determinant;
    if(f.maximum_determinant===null||determinant>f.maximum_determinant)f.maximum_determinant=determinant;
    if(proper.some(v=>v<0n)){f.counts.negative_proper_minor++;continue;}
    if(determinant<0n)f.counts.negative_determinant++;
    else if(determinant===0n)f.counts.zero_determinant++;
    else f.counts.positive_determinant++;
    if(determinant<=0n){
     insist(f.records.length<maximumRecords,"triangle record cap");
     f.records.push([a,b,c,determinant.toString(),...proper.map(String)]);
    }
   }
  }
 }
 tick();
 return {schema:VERSION,status:"COMPLETE_EXACT_TRIANGLE_PRINCIPAL_MINOR_CENSUS",selectors:480,original_eligible_edges:eligible,
  pairwise_disjoint_signature_edges:disjointEdges,pairwise_disjoint_eligible_triangles:triangles,
  overlapping_signature_triangles:"excluded by separate lambda=1 proof; not counted in this disjoint census",
  old_prism_zero_or_path_rows_used:false,new_cut_novelty_claimed:false,optimizer_calls:0,
  graph_constructed:false,whole_component_excluded:false,maximum_ms:maximumMs,
  families:families.map(f=>({family:f.family,primitive_kernel_sha256:f.primitiveHash,negative_eligible_edge_pairs:f.negativePairs,
   zero_eligible_edge_minors:f.zeroPairs,minimum_eligible_edge_minor:f.minimum_edge_minor,counts:f.counts,
   minimum_triangle_determinant:f.minimum_determinant===null?null:f.minimum_determinant.toString(),
   maximum_triangle_determinant:f.maximum_determinant===null?null:f.maximum_determinant.toString(),
   nonpositive_determinant_records_with_nonnegative_proper_minors:f.records})),
  seconds:(Date.now()-started)/1000};
}
return {controls,run};
})()