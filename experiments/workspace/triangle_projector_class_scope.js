"use strict";

function triangleProjectorClassScope(){
 const check=(a,m)=>{if(!a)throw Error(m);},pop=x=>{let n=0;while(x){n+=x&1;x>>>=1;}return n;};
 const permutations=a=>a.length?a.flatMap((v,i)=>permutations(a.filter((_u,j)=>i!==j)).map(p=>[v,...p])):[[]];
 const p4=permutations([0,1,2,3]),p3=permutations([0,1,2]),pairs=[];
 for(let i=0;i<4;i++)for(let j=i+1;j<4;j++)pairs.push([i,j]);
 const rowsFromCode=code=>{const r=[0,0,0,0];pairs.forEach(([a,b],i)=>{if(code>>i&1){r[a]|=1<<b;r[b]|=1<<a;}});return r;};
 const codeFromRows=r=>pairs.reduce((s,[a,b],i)=>s|(((r[a]>>b)&1)<<i),0);
 const move=(r,p)=>{const o=Array(r.length).fill(0);for(let i=0;i<r.length;i++)for(let j=0;j<r.length;j++)if(r[i]>>j&1)o[p[i]]|=1<<p[j];return o;};
 const caps=r=>{for(let i=0;i<r.length;i++)for(let j=i+1;j<r.length;j++)if(pop(r[i]&r[j])+((r[i]>>j)&1)>2)return false;return true;};
 const rootCodes=new Set();
 for(let code=0;code<64;code++){const r=rowsFromCode(code);if(caps(r))rootCodes.add(Math.min(...p4.map(p=>codeFromRows(move(r,p)))));}
 check(rootCodes.size===9,"nine root types");
 const roots=[];
 for(const code of [...rootCodes].sort((a,b)=>a-b)){
  const r=rowsFromCode(code),classes=[];
  for(let a=0;a<16;a++)for(let b=a;b<16;b++)for(let c=b;c<16;c++){
   const masks=[a,b,c];if((a&b)||(a&c)||(b&c))continue;
   const graph=r.slice();
   for(let j=0;j<3;j++){graph.push(masks[j]);for(let i=0;i<4;i++)if(masks[j]>>i&1)graph[i]|=1<<(4+j);}
   for(let i=0;i<3;i++)for(let j=i+1;j<3;j++){graph[4+i]|=1<<(4+j);graph[4+j]|=1<<(4+i);}
   if(!caps(graph))continue;
   const stabilizer=p3.filter(p=>masks.every((m,i)=>m===masks[p[i]])).length;
   const z=masks.filter(m=>m===0).length,factor=[1,1,2,6][z];
   check(stabilizer===factor,"literal triangle-label factor");
   classes.push({masks,literal_rows:graph,free_label_stabilizer:factor});
  }
  roots.push({root_code:code,root_rows:r,root_automorphism_order:p4.filter(p=>codeFromRows(move(r,p))===code).length,classes,
   class_count:classes.length,factor_counts:classes.reduce((o,c)=>(o[c.free_label_stabilizer]=(o[c.free_label_stabilizer]||0)+1,o),{})});
 }
 check(roots[0].class_count===51,"Burnside control");
 return {status:"COMPLETE_NINE_ROOT_TRIANGLE_CLASS_SCOPE",roots,total_classes:roots.reduce((s,r)=>s+r.class_count,0),
  max_class_count:Math.max(...roots.map(r=>r.class_count)),ordered_pair_entries:roots.reduce((s,r)=>s+r.class_count*r.class_count,0),
  lower_entries:roots.reduce((s,r)=>s+r.class_count*(r.class_count+1)/2,0),
  complete_root_graph_candidates:64,actual_root_types:9,
  graph_count_point_loaded:false,pair_products_built:false,optimizer_called:false,
  normalization:"A specified labelled triangle flag equals z! times the unlabelled triangle class indicator, where z is the number of zero root-neighborhood masks."};
}

function triangleProjectorAlgebraChecks(){
 const check=(v,m)=>{if(!v)throw Error(m);};
 const multiply=(a,b)=>[
  a[0]*b[0]+12*a[1]*b[1],
  a[0]*b[1]+a[1]*b[0]-a[1]*b[1],
  a[0]*b[2]+a[2]*b[0]+2*a[1]*b[1]+14*(a[1]*b[2]+a[2]*b[1])+99*a[2]*b[2]
 ];
 const inverseNumerator=[126,-21,2],denominator=630;
 check(JSON.stringify(multiply([7,1,0],inverseNumerator))==="[630,0,0]","inverse in SRG adjacency algebra");
 const q=(same,intersection,crossEdges)=>210*same-42*intersection+7*crossEdges-6;
 check(q(1,3,6)===120&&q(0,1,4)===-20,"diagonal and one-point overlap");
 check([0,1,2,3].every(e=>q(0,0,e)===7*e-6),"disjoint entries");
 const coefficients={I:210-42*3+7*(-12),L:-42+7*(-1),L_squared:7,J:-6};
 check(coefficients.I===0&&coefficients.L===-49,"triangle intersection polynomial");
 check(99*7/3===231&&231-99===132&&120*231===210*132,"rank and trace");
 return {inverse_numerator_basis_I_A_J:inverseNumerator,inverse_denominator:denominator,
  product_with_7I_plus_A:[630,0,0],triangle_count:231,incidence_rank:99,projector_rank:132,
  projector_scale:210,diagonal:120,one_point_intersection:-20,disjoint_entries:[-6,1,8,15],
  intersection_graph_polynomial:coefficients,
  PSD_reason:"7I+A is invertible and B B^T=7I+A, so I-B^T(7I+A)^-1 B is a symmetric idempotent.",
  direct_vertex_pullback_obstruction:"Every B^T P B vanishes on ker B, while Q acts on ker B as 210I.",
  full_existing_flag_cone_redundancy_decided:false};
}

function prepare(){
 const result=triangleProjectorClassScope();
 result.algebra_checks=triangleProjectorAlgebraChecks();
 return result;
}
if(typeof module!=="undefined"){
 module.exports={triangleProjectorClassScope,triangleProjectorAlgebraChecks,prepare};
 if(require.main===module)console.log(JSON.stringify(prepare(),null,2));
}
