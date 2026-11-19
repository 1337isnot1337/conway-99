"use strict";

function replayRoot42Distribution(prepared,result,point,checkerBlob) {
  "use strict";
  function assert(x,m){if(!x)throw Error(m);}
  function same(a,b){return JSON.stringify(a)===JSON.stringify(b);}
  function gcd(a,b){a=a<0n?-a:a;b=b<0n?-b:b;while(b){const r=a%b;a=b;b=r;}return a;}
  function compare(a,b){const x=a[0]*b[1]-b[0]*a[1];return x<0n?-1:x>0n?1:0;}
  function normalized(q){const g=gcd(q[0],q[1]);return [q[0]/g,q[1]/g];}
  function moved(mask,p){let x=0;for(let i=0;i<6;i++)if(mask&(1<<i))x|=1<<p[i];return x;}
  assert(prepared.status==="POINT_INDEPENDENT_ROOT42_INTERVAL_PREPARATION_PASS","preparation status");
  assert(result.status==="EXACT_ROOT42_INTEGER_ATOM_DISTRIBUTION","query status");
  assert(prepared.source_git_blob==="9f78b4b3075d3f5c991ce47379e593d11f7f992b"&&result.source_git_blob===prepared.source_git_blob,"source binding");
  assert(same(prepared.bindings,result.bindings),"input bindings");
  assert(!prepared.count_point_loaded&&!prepared.optimizer_called&&!result.optimizer_called&&!result.full_graph_existence_resolved,"scope");
  assert(point.induced_counts.length===48965&&point.induced_counts.every(n=>Number.isSafeInteger(n)&&n>=0),"integer count point");
  assert(point.exact_count_and_held_cut_witness&&point.required_zeros_hold&&point.x521_zero,"immutable point scope");
  const counts=point.induced_counts.map(BigInt),evaluate=f=>f.reduce((s,[t,c])=>s+BigInt(c)*counts[t],0n);
  const atoms=prepared.atoms,codes=atoms.map(a=>BigInt(a.code));
  assert(atoms.length===253&&prepared.affine_atoms.length===253&&new Set(codes.map(String)).size===253,"complete atom dimensions");
  const five=atoms.filter(a=>a.masks.length===5).map(a=>a.atom_index);
  assert(five.length===12&&same(five,prepared.fifth_atom_indices),"fifth-state domain");
  const moments=new Map(prepared.all_small_moment_forms.map(m=>[m.atom_index,evaluate(m.induced_count_form)]));
  assert(moments.size===241,"all supplied small moments");
  const u=BigInt(result.fifth_moment),weights=result.atom_weights.map(BigInt);
  assert(u>=0n&&u%2n===0n&&weights.length===253&&weights.every(w=>w>=0n),"nonnegative integer even-parameter witness");
  const constants=[],slopes=[];let lower=null,upper=null;
  for(const atom of atoms){
    const i=atom.atom_index;
    assert(i>=0&&i<253&&atoms[i]===atom,"atom indexing");
    let c=0n;
    for(const [j,m]of moments)if((codes[i]&codes[j])===codes[i]){
      c+=((atoms[j].masks.length-atom.masks.length)&1?-1n:1n)*m;
    }
    const count=five.filter(j=>(codes[i]&codes[j])===codes[i]).length;
    const d=BigInt(((5-atom.masks.length)&1?-1:1)*count);
    assert(c===evaluate(prepared.affine_atoms[i].induced_constant_form),"independent constant reconstruction");
    assert(d===BigInt(prepared.affine_atoms[i].fifth_moment_slope),"independent slope reconstruction");
    assert(c===BigInt(result.atom_constants[i])&&d===BigInt(result.atom_slopes[i]),"saved affine data");
    assert(weights[i]===c+d*u,"all saved affine weights");
    constants.push(c);slopes.push(d);
    if(d>0n){const q=[-c,d];if(lower===null||compare(q,lower.value)>0)lower={atom:i,value:q};}
    else if(d<0n){const q=[c,-d];if(upper===null||compare(q,upper.value)<0)upper={atom:i,value:q};}
    else assert(c>=0n,"zero-slope condition");
    const stabilizer=prepared.actual_root_automorphisms.filter(p=>same(atom.masks.map(m=>moved(m,p)).sort((a,b)=>a-b),atom.masks)).length;
    assert(stabilizer===prepared.affine_atoms[i].stabilizer_order&&stabilizer>0,"literal stabilizer count");
    assert(weights[i]%BigInt(stabilizer)===0n,"actual integer stabilizer divisibility");
    if(atom.masks.length===5)assert(stabilizer===2&&weights[i]===u,"even fifth moment");
    let actual=0n;for(let j=0;j<253;j++)if((codes[i]&codes[j])===codes[i])actual+=weights[j];
    assert(actual===(moments.has(i)?moments.get(i):u),"every original individual moment");
  }
  assert(lower!==null&&upper!==null&&compare(lower.value,upper.value)<=0,"nonempty real interval");
  const L=normalized(lower.value),U=normalized(upper.value);
  assert(same(L.map(String),[result.interval.lower.value.n,result.interval.lower.value.d]),"exact lower endpoint");
  assert(same(U.map(String),[result.interval.upper.value.n,result.interval.upper.value.d]),"exact upper endpoint");
  assert(result.interval.real_feasible&&result.interval.even_feasible&&result.interval.zeroFailures.length===0,"interval status");
  assert(u===BigInt(result.interval.least_even_candidate),"candidate identity");
  assert(2n*(L[0]>=0n?(L[0]+2n*L[1]-1n)/(2n*L[1]):L[0]/(2n*L[1]))===u,"least even candidate");
  assert(u*U[1]<=U[0],"candidate below upper bound");
  const orbitWeights=prepared.atom_orbits.map(o=>o.members.reduce((s,i)=>s+weights[i],0n));
  assert(same(orbitWeights.map(String),result.orbit_weights),"orbit masses");
  for(let r=0;r<23;r++){
    const q=prepared.supported_row_orbits[r],expected=BigInt(prepared.sizes[q])*moments.get(prepared.representatives[q]);
    const actual=prepared.quotient_coefficients[r].reduce((s,c,j)=>s+BigInt(c)*orbitWeights[j],0n);
    assert(actual===expected,"all original quotient equations");
  }
  const mass=weights.reduce((s,w)=>s+w,0n);
  assert(mass===24n*counts[42]&&mass===BigInt(result.labelled_root_mass)&&mass===moments.get(0),"root normalization");
  const positive=weights.filter(w=>w>0n).length;
  assert(positive===result.positive_atoms&&253-positive===result.zero_atoms,"sign counts");
  let divisor=mass;for(const w of weights)divisor=gcd(divisor,w);
  return {
    status:"INDEPENDENT_ROOT42_INTEGER_DISTRIBUTION_REPLAY_PASS",checker_git_blob:checkerBlob||null,
    bindings:{preparation_git_blob:"7f6b7952f81dc6c1ee0f25e12379e3dcd3656979",result_git_blob:"233ed73fae5f80b3dc23b126c1528db64a8b6f31",point_git_blob:"c881dae3be05cf289fcc45a99d72c405ac863c46"},
    root_type:42,lower_endpoint:L.map(String),upper_endpoint:U.map(String),chosen_fifth_moment:u.toString(),
    labelled_root_mass:mass.toString(),positive_atoms:positive,zero_atoms:253-positive,
    reduced_probability_denominator:(mass/divisor).toString(),
    original_individual_equations_checked:253,known_lower_moments_checked:241,quotient_equations_checked:23,stabilizer_divisibilities_checked:253,
    independence:"No query or interval helper is imported. Original induced moments, atom constants, slopes, all moment equations, exact endpoints and actual root stabilizers are reconstructed from the frozen artifacts.",
    optimizer_called:false,graph_existence_resolved:false
  };
}

if(typeof module!=="undefined"&&module.exports) {
  module.exports={replayRoot42Distribution};
  if(require.main===module) {
    const fs=require("fs"),crypto=require("crypto");
    function blob(p){const b=fs.readFileSync(p);return crypto.createHash("sha1").update("blob "+b.length+"\0").update(b).digest("hex");}
    const paths=process.argv.slice(2);
    const expected=["7f6b7952f81dc6c1ee0f25e12379e3dcd3656979","233ed73fae5f80b3dc23b126c1528db64a8b6f31","c881dae3be05cf289fcc45a99d72c405ac863c46"];
    if(paths.length!==3)throw Error("Usage: node replay.js preparation.json result.json point.json");
    paths.forEach((p,i)=>{if(blob(p)!==expected[i])throw Error("Exact input binding "+i);});
    const [prepared,result,point]=paths.map(p=>JSON.parse(fs.readFileSync(p,"utf8")));
    console.log(JSON.stringify(replayRoot42Distribution(prepared,result,point,blob(__filename)),null,2));
  }
}
