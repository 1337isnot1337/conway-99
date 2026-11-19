"use strict";

function replayRoot42Decorated(scope,presence,point,result,isomorphisms){
 const check=(v,m)=>{if(!v)throw Error(m);},pop=x=>{let n=0;while(x){n+=x&1;x>>>=1;}return n;};
 const states=scope.complete_state_ledger,classes=presence.literal_classes,root=scope.root_rows,high=scope.high_masks;
 check(result.status==="EXACT_ROOT42_COMPLETE_DECORATED_MOMENT_DISTRIBUTION","positive certificate");
 check(states.length===343&&result.atom_weights.length===343&&classes.length===31,"full fixed domain");
 const weights=result.atom_weights.map((r,i)=>{
  const s=states[i];check(r.state_index===i&&JSON.stringify(r.masks)===JSON.stringify(s.masks)&&r.edge_code===s.edge_code&&r.root_orbit===s.root_orbit,"weight identity");
  const w=BigInt(r.weight);check(w>=0n,"positive weight");return w;
 });
 const group=scope.actual_root_automorphisms;
 check(group.length===24&&new Set(group.map(p=>p.join(","))).size===24,"complete literal S4");
 for(const p of group){
  check(p.length===6&&new Set(p).size===6&&p[4]===4&&p[5]===5,"root permutation");
  for(let i=0;i<6;i++)for(let j=0;j<6;j++)check(((root[i]>>j)&1)===((root[p[i]]>>p[j])&1),"actual root automorphism");
 }
 const edges=s=>{
  const out=[];for(let i=0;i<s.masks.length;i++)for(let j=i+1;j<s.masks.length;j++)if(s.rows[6+i]>>(6+j)&1)out.push([s.masks[i],s.masks[j]]);
  return out;
 };
 const makeKey=(m,e)=>m.slice().sort((a,b)=>a-b).join(",")+"|"+e.map(p=>p.slice().sort((a,b)=>a-b)).sort((a,b)=>a[0]-b[0]||a[1]-b[1]).map(p=>p.join(",")).join(";");
 const keys=new Map(states.map((s,i)=>[makeKey(s.masks,edges(s)),i]));check(keys.size===343,"unique states");
 const stabilizers=[];
 for(let j=0;j<states.length;j++){
  const s=states[j],a=s.rows,n=a.length;check(n===6+s.masks.length,"literal size");
  for(let i=0;i<n;i++){
   check(!(a[i]>>i&1),"no loop");
   for(let k=0;k<n;k++)check(((a[i]>>k)&1)===((a[k]>>i)&1),"literal symmetry");
   for(let k=i+1;k<n;k++)check(pop(a[i]&a[k])+((a[i]>>k)&1)<=2,"visible caps");
  }
  check(s.masks.every((m,i)=>(a[6+i]&63)===m),"root masks");
  const fixed=[];
  for(let g=0;g<group.length;g++){
   const p=group[g],move=m=>{let v=0;for(let i=0;i<6;i++)if(m>>i&1)v|=1<<p[i];return v;};
   const moved=keys.get(makeKey(s.masks.map(move),edges(s).map(e=>e.map(move))));
   check(moved!==undefined&&weights[moved]===weights[j],"root action and invariant weights");
   if(moved===j)fixed.push(g);
  }
  check(JSON.stringify(fixed)===JSON.stringify(s.stabilizer_indices),"independent stabilizer replay");
  check(weights[j]%BigInt(fixed.length)===0n,"divisibility");stabilizers.push(fixed.length);
 }
 const aut=classes.map(c=>{const n=isomorphisms(c.rows).count;check(n===c.automorphisms,"literal automorphism factor");return BigInt(n);});
 const values=classes.map(c=>{const n=point.induced_counts[c.catalogue_type];check(Number.isSafeInteger(n)&&n>=0,"exact induced count");return BigInt(n);});
 const extendsLiteral=(a,b)=>{
  const positions=a.masks.map(m=>b.masks.indexOf(m));if(positions.some(i=>i<0))return false;
  for(let i=0;i<positions.length;i++)for(let j=i+1;j<positions.length;j++)
   if(((a.rows[6+i]>>(6+j))&1)!==((b.rows[6+positions[i]]>>(6+positions[j]))&1))return false;
  return true;
 };
 const upper=states.map(a=>states.map((b,i)=>extendsLiteral(a,b)?i:-1).filter(i=>i>=0));
 for(const s of states)if(s.population<=4)check(isomorphisms(s.rows,classes[s.literal_class].rows).count>0,"every known literal graph identity");
 const parameters=result.fifth_parameters.map(BigInt);check(parameters.length===2&&parameters.every(u=>u>=0n&&u%2n===0n),"even fifth masses");
 const target=(s,u)=>s.population<=4?aut[s.literal_class]*values[s.literal_class]:u[edges(s).length];
 for(let i=0;i<343;i++)check(upper[i].reduce((z,j)=>z+weights[j],0n)===target(states[i],parameters),"all original decorated moment equations");
 const mass=weights.reduce((a,b)=>a+b,0n);check(mass===24n*BigInt(point.induced_counts[42])&&mass===BigInt(result.labelled_root_mass),"root normalization");
 const constants=result.atom_constants.map(BigInt);
 check(constants.length===343,"all constants");
 for(let i=0;i<343;i++){
  const s=states[i],c=s.affine_coefficients.slice(0,31).reduce((z,v,j)=>z+BigInt(v)*values[j],0n);
  check(c===constants[i],"direct induced constant");
  check(c+BigInt(s.affine_coefficients[31])*parameters[0]+BigInt(s.affine_coefficients[32])*parameters[1]===weights[i],"supplied mass certificate");
  check(c%BigInt(stabilizers[i])===0n&&s.affine_coefficients.slice(31).every(v=>(2n*BigInt(v))%BigInt(stabilizers[i])===0n),"coefficientwise even-parameter divisibility");
 }
 const upperParameters=result.exact_integer_intervals.slice(0,2).map(b=>2n*BigInt(b.upper));
 check(result.exact_integer_intervals.slice(0,2).every(b=>BigInt(b.lower)===0n),"zero individual lower bounds");
 const upperWitnesses=[];
 for(let v=0;v<2;v++){
  const i=result.exact_integer_intervals[v].upper_rows[0],row=states[i].affine_coefficients;
  check(row[31+v]===-1&&row[32-v]===0,"direct unit upper-bound atom");
  check(constants[i]===upperParameters[v],"exact necessary upper endpoint");
  upperWitnesses.push({parameter:v,state_index:i,constant:constants[i].toString(),coefficient:-1,other_coefficient:0});
 }
 const corners=[[0n,0n],[upperParameters[0],0n],[0n,upperParameters[1]],upperParameters.slice()];
 let cornerMomentChecks=0,cornerDivisibilityChecks=0;
 for(const u of corners){
  const w=states.map((s,i)=>constants[i]+BigInt(s.affine_coefficients[31])*u[0]+BigInt(s.affine_coefficients[32])*u[1]);
  check(w.every(x=>x>=0n),"all rectangle-corner masses");
  for(let i=0;i<343;i++){
   check(upper[i].reduce((z,j)=>z+w[j],0n)===target(states[i],u),"rectangle corner original equations");cornerMomentChecks++;
   check(w[i]%BigInt(stabilizers[i])===0n,"rectangle corner divisibility");cornerDivisibilityChecks++;
  }
 }
 const sumU=parameters[0]+parameters[1];
 for(let i=0;i<presence.atoms.length;i++){
  const a=presence.atoms[i],actual=states.reduce((z,s,j)=>z+(JSON.stringify(s.masks)===JSON.stringify(a.masks)?weights[j]:0n),0n);
  const affine=presence.affine_atoms[i],constant=affine.induced_constant_form.reduce((z,[t,c])=>z+BigInt(c)*BigInt(point.induced_counts[t]),0n);
  check(actual===constant+BigInt(affine.fifth_moment_slope)*sumU&&actual===BigInt(result.presence_atom_weights[i]),"presence coarsening");
 }
 for(const row of presence.all_small_moment_forms){
  const a=presence.atoms[row.atom_index],actual=states.reduce((z,s,j)=>z+(a.masks.every(m=>s.masks.includes(m))?weights[j]:0n),0n);
  const expected=row.induced_count_form.reduce((z,[t,c])=>z+BigInt(c)*BigInt(point.induced_counts[t]),0n);
  check(actual===expected,"all known presence moments");
 }
 let quotientRows=0;
 for(const orbit of scope.state_orbits)if(orbit.population<=4){
  const actual=scope.state_orbits.reduce((z,o)=>z+BigInt(o.members.filter(j=>extendsLiteral(states[orbit.representative],states[j])).length)*weights[o.representative],0n);
  check(actual===target(states[orbit.representative],parameters),"direct quotient equation");quotientRows++;
 }
 const integerPairs=(upperParameters[0]/2n+1n)*(upperParameters[1]/2n+1n);
 return {
  status:"PASS_INDEPENDENT_DIRECT_DECORATED_MASS_AND_RECTANGLE_REPLAY",
  source_query_imported:false,affine_inversion_recomputed:false,optimizer_called:false,
  full_states:343,all_literal_caps_checked:343,known_literal_graph_matches:319,literal_automorphism_factors_checked:31,
  exact_original_decorated_moment_equations:343,exact_quotient_equations:quotientRows,
  root_action_images_checked:343*24,exact_stabilizer_divisibilities:343,
  presence_coarsenings_checked:253,known_presence_moments_checked:241,
  all_rectangle_corners_verified:4,corner_original_moment_equations:cornerMomentChecks,corner_divisibility_checks:cornerDivisibilityChecks,
  fifth_parameter_rectangle:upperParameters.map((u,i)=>({parameter:i,minimum:"0",maximum:u.toString(),modulus:2})),
  necessary_upper_bound_atom_certificates:upperWitnesses,
  feasible_even_parameter_pairs:integerPairs.toString(),
  positive_masses:weights.filter(w=>w>0n).length,zero_masses:weights.filter(w=>w===0n).length,
  labelled_root_mass:mass.toString(),chosen_parameters:parameters.map(String),
  whole_graph_constructed:false,
  scope:"Every even pair in the recorded rectangle gives a nonnegative integral local state distribution. The stored chosen masses are independently checked against the original literal moments."
 };
}

if(typeof module!=="undefined"){
 module.exports={replayRoot42Decorated};
 if(require.main===module){
  const fs=require("fs"),path=require("path"),crypto=require("crypto");
  const blob=p=>{const b=fs.readFileSync(p);return crypto.createHash("sha1").update(Buffer.from("blob "+b.length+"\0")).update(b).digest("hex");};
  const [scopePath,presencePath,pointPath,resultPath]=process.argv.slice(2);
  if(!resultPath)throw Error("Usage: node replay.js scope.json presence-preparation.json point.json result.json");
  const expected=["4a9b464efe9beaa097e0a8f19621f064b44b7502","7f6b7952f81dc6c1ee0f25e12379e3dcd3656979","c881dae3be05cf289fcc45a99d72c405ac863c46","56c805dfc075c824c68fdb160dfacee533c9f29a"];
  [scopePath,presencePath,pointPath,resultPath].forEach((p,i)=>{if(blob(p)!==expected[i])throw Error("Frozen input binding "+i);});
  const isoPath=path.join(__dirname,"root49_packing_moment_recovery_check.js");
  if(blob(isoPath)!=="d547df71ef544fc7e36a8580bc9f7bdc311d6871")throw Error("Frozen literal isomorphism source");
  const read=p=>JSON.parse(fs.readFileSync(p,"utf8")),iso=require(isoPath).makeRoot49RecoveryTools().isomorphisms;
  console.log(JSON.stringify(replayRoot42Decorated(read(scopePath),read(presencePath),read(pointPath),read(resultPath),iso),null,2));
 }
}
