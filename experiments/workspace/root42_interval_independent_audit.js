"use strict";

/* Independent root42 domain, affine and interval audit. No point values. */
function auditRoot42Interval(subject, prepared, input) {
  function check(ok,message) { if(!ok) throw Error(message); }
  function same(a,b) { return JSON.stringify(a)===JSON.stringify(b); }
  function pc(x) { let n=0;for(;x;x&=x-1)n++;return n; }
  function graph(root,masks) {
    const rows=root.slice();
    masks.forEach((mask,j)=>{rows.push(mask);for(let i=0;i<6;i++)if((mask>>i)&1)rows[i]|=1<<(6+j);});
    return rows;
  }
  function cap(rows) {
    for(let i=0;i<rows.length;i++)for(let j=i+1;j<rows.length;j++)
      if(((rows[i]>>j)&1)+pc(rows[i]&rows[j])>2)return false;
    return true;
  }
  function perms(items) {
    if(!items.length)return [[]];
    return items.flatMap((x,i)=>perms(items.filter((_v,j)=>j!==i)).map(p=>[x,...p]));
  }
  function coefficients(terms) {
    const m=new Map();
    for(const [i,c]of terms)m.set(i,(m.get(i)||0n)+BigInt(c));
    return m;
  }
  function sparse(m) { return [...m].filter(([_i,c])=>c).sort((a,b)=>a[0]-b[0]).map(([i,c])=>[i,c.toString()]); }
  function add(m,terms,scale=1n) { for(const [i,c]of terms)m.set(i,(m.get(i)||0n)+scale*BigInt(c)); }
  function subset(a,b) { return a.every(x=>b.includes(x)); }
  const root=[32,32,32,32,0,15];
  check(same(prepared.root_rows,root),"root adjacency");
  const universe=Array.from({length:64},(_,i)=>i).filter(m=>pc(m)>=3);
  const high=universe.filter(m=>cap(graph(root,[m])));
  check(same(high,prepared.high_masks)&&high.length===10,"all42 possible high masks tested");
  const uindex=new Map(universe.map((m,i)=>[m,i]));
  const code=ms=>ms.reduce((a,m)=>a|(1n<<BigInt(uindex.get(m))),0n);
  const domain=[];
  for(let bits=0;bits<(1<<high.length);bits++) {
    const masks=high.filter((_m,j)=>(bits>>j)&1);
    if(cap(graph(root,masks)))domain.push({masks,code:code(masks)});
  }
  domain.sort((a,b)=>a.code<b.code?-1:1);
  check(domain.length===253&&domain.every(a=>a.masks.length<=5),"complete1024-subset domain");
  check(same(domain.map(a=>a.code.toString()),prepared.atoms.map(a=>a.code)),"exact domain binding");
  const group=perms([0,1,2,3]).map(p=>p.concat([4,5]));
  check(same(group.map(p=>p.join(",")).sort(),prepared.actual_root_automorphisms.map(p=>p.join(",")).sort()),"literalS4 group");
  const moved=(mask,p)=>{let y=0;for(let i=0;i<6;i++)if((mask>>i)&1)y|=1<<p[i];return y;};
  const index=new Map(domain.map((a,i)=>[a.masks.join(","),i]));
  const five=domain.map((a,i)=>a.masks.length===5?i:null).filter(i=>i!==null);
  check(five.length===12&&same(five,prepared.fifth_atom_indices),"all fifth atoms");
  const firstImages=new Set(group.map(p=>index.get(domain[five[0]].masks.map(m=>moved(m,p)).sort((a,b)=>a-b).join(","))));
  check(same([...firstImages].sort((a,b)=>a-b),five),"single complete fifth orbit");
  const lower=new Map(prepared.all_small_moment_forms.map(a=>[a.atom_index,a.induced_count_form]));
  check(lower.size===241,"all lower moments");
  let symbolicTerms=0,stabilizerChecks=0;
  const recomputed=[];
  for(let a=0;a<253;a++) {
    const constant=new Map();
    for(const [t,f]of lower)if(subset(domain[a].masks,domain[t].masks))
      add(constant,f,(domain[t].masks.length-domain[a].masks.length)&1?-1n:1n);
    const supersets=five.filter(t=>subset(domain[a].masks,domain[t].masks));
    const slope=((5-domain[a].masks.length)&1?-1:1)*supersets.length;
    const stab=group.filter(p=>same(domain[a].masks.map(m=>moved(m,p)).sort((x,y)=>x-y),domain[a].masks)).length;
    check(same(sparse(constant),prepared.affine_atoms[a].induced_constant_form),"every affine constant");
    check(slope===prepared.affine_atoms[a].fifth_moment_slope,"every affine slope");
    check(stab===prepared.affine_atoms[a].stabilizer_order,"every literal stabilizer");
    check([...constant.values()].every(c=>c%BigInt(stab)===0n)&&(2*slope)%stab===0,"all congruences from evenu");
    if(domain[a].masks.length===5)check(stab===2&&slope===1&&constant.size===0,"fifth mass equals even parameter");
    symbolicTerms+=constant.size;stabilizerChecks++;
    recomputed.push({form:sparse(constant),slope});
  }
  for(let t=0;t<253;t++) {
    const sum=new Map();let slope=0;
    for(let a=0;a<253;a++)if(subset(domain[t].masks,domain[a].masks)) {
      add(sum,recomputed[a].form);slope+=recomputed[a].slope;
    }
    check(same(sparse(sum),lower.get(t)||[])&&slope===(domain[t].masks.length===5?1:0),"all253 symbolic zeta equations");
  }
  const rows=input.roots[0].tensor.rows;
  check(rows.length===prepared.product_rows.length&&rows.length===67,"all literal product rows");
  for(let i=0;i<rows.length;i++) {
    check(rows[i].row===prepared.product_rows[i].row,"product row ordering");
    check(same(rows[i].indices.map((t,j)=>[t,rows[i].data[j]]),prepared.product_rows[i].catalogue_coefficients),"all input tensor coefficients");
  }
  const start=subject.indexOf("  function compareFractions("),end=subject.indexOf("  function prepare(",start);
  check(start>=0&&end>start,"frozen private interval functions");
  const interval=new Function("function assert(x,m){if(!x)throw Error(m);}\n"+subject.slice(start,end)+"\nreturn interval;")();
  let intervalControls=0;
  for(let c1=-4;c1<=4;c1++)for(let s1=-3;s1<=3;s1++)
    for(let c2=-4;c2<=4;c2++)for(let s2=-3;s2<=3;s2++) {
      const constants=[10n,10n,BigInt(c1),BigInt(c2)],slopes=[1,-1,s1,s2];
      const actual=interval(constants,slopes),valid=[];
      for(let u=-10;u<=10;u+=2)
        if(constants.every((c,i)=>c+BigInt(slopes[i]*u)>=0n))valid.push(u);
      check(actual.even_feasible===(valid.length>0),"even interval versus exhaustive bounded integers");
      if(valid.length)check(actual.least_even_candidate===BigInt(valid[0]),"least even integer including negative endpoints");
      intervalControls++;
    }
  return {
    status:"PASS: independent root42 domain, affine identities and interval controls",
    domain_subsets_checked:1024,all_high_masks_checked:42,atoms:253,lower_moments:241,
    fifth_atoms:12,complete_fifth_orbits:1,fifth_stabilizer:2,
    affine_constants_and_slopes_checked:253,symbolic_zeta_equations_checked:253,
    coefficientwise_stabilizer_checks:stabilizerChecks,affine_sparse_terms:symbolicTerms,
    frozen_product_rows_bound:67,small_even_interval_controls:intervalControls,
    count_point_loaded:false,optimizer_called:false,
    subject_prepare_or_query_called:false,
    scope:"Complete necessary root42 presence model; no decorated-edge model or graph-existence assertion."
  };
}
if(typeof module!=="undefined"&&module.exports) {
  module.exports={auditRoot42Interval};
  if(require.main===module) {
    const fs=require("fs"),crypto=require("crypto");
    const [sourcePath,preparedPath,inputPath]=process.argv.slice(2);
    const blob=p=>{const b=fs.readFileSync(p);return crypto.createHash("sha1").update("blob "+b.length+"\0").update(b).digest("hex");};
    if(blob(sourcePath)!=="9f78b4b3075d3f5c991ce47379e593d11f7f992b"||
       blob(preparedPath)!=="7f6b7952f81dc6c1ee0f25e12379e3dcd3656979"||
       blob(inputPath)!=="ad89299823eef485ceeeea4824ce0eb9ebacbb3a")throw Error("Frozen input bindings");
    console.log(JSON.stringify(auditRoot42Interval(fs.readFileSync(sourcePath,"utf8"),
      JSON.parse(fs.readFileSync(preparedPath,"utf8")),JSON.parse(fs.readFileSync(inputPath,"utf8"))),null,2));
  }
}
