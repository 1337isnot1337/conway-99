"use strict";

function makeRoot42DecoratedQuery(){
 const check=(x,m)=>{if(!x)throw Error(m);};
 const max=(a,b)=>a>b?a:b,min=(a,b)=>a<b?a:b;
 const floorDiv=(a,b)=>{check(b>0n,"positive divisor");return a>=0n?a/b:-((-a+b-1n)/b);};
 const ceilDiv=(a,b)=>-floorDiv(-a,b);
 const gcd=(a,b)=>{while(b){const t=a%b;a=b;b=t;}return a<0n?-a:a;};
 const wire=x=>typeof x==="bigint"?x.toString():Array.isArray(x)?x.map(wire):x&&typeof x==="object"?Object.fromEntries(Object.entries(x).map(([k,v])=>[k,wire(v)])):x;
 function solveIntervals(bounds){
  check(bounds.length===3&&bounds.every(b=>typeof b.lower==="bigint"&&typeof b.upper==="bigint"),"three finite integer intervals");
  for(let i=0;i<3;i++)if(bounds[i].lower>bounds[i].upper)return {feasible:false,reason:"empty_individual_interval",interval:i};
  const lower=max(bounds[2].lower,bounds[0].lower+bounds[1].lower);
  const upper=min(bounds[2].upper,bounds[0].upper+bounds[1].upper);
  if(lower>upper)return {feasible:false,reason:"sum_interval_disjoint",feasible_sum_lower:lower,feasible_sum_upper:upper};
  const x=max(bounds[0].lower,lower-bounds[1].upper),y=lower-x;
  check(x<=bounds[0].upper&&y>=bounds[1].lower&&y<=bounds[1].upper,"exact witness");
  return {feasible:true,normalized_parameters:[x,y],normalized_sum:lower,feasible_sum_lower:lower,feasible_sum_upper:upper};
 }
 function controls(){
  let divisions=0,cases=0;
  for(let a=-20;a<=20;a++)for(let b=1;b<=7;b++){
   check(floorDiv(BigInt(a),BigInt(b))===BigInt(Math.floor(a/b)),"floor control");
   check(ceilDiv(BigInt(a),BigInt(b))===BigInt(Math.ceil(a/b)),"ceiling control");divisions++;
  }
  const intervals=[];for(let a=-2;a<=2;a++)for(let b=a;b<=2;b++)intervals.push({lower:BigInt(a),upper:BigInt(b)});
  for(const a of intervals)for(const b of intervals)for(const s of intervals){
   const exact=solveIntervals([a,b,s]);let found=false;
   for(let x=Number(a.lower);x<=Number(a.upper);x++)for(let y=Number(b.lower);y<=Number(b.upper);y++)if(BigInt(x+y)>=s.lower&&BigInt(x+y)<=s.upper)found=true;
   check(exact.feasible===found,"interval exhaustive control");cases++;
  }
  const empty=solveIntervals([{lower:1n,upper:0n},{lower:0n,upper:0n},{lower:0n,upper:0n}]);
  check(!empty.feasible,"empty interval");
  return {status:"PASS_EXACT_SIGNED_INTERVAL_CONTROLS",division_pairs:divisions,interval_triples:cases,empty_interval_controls:1,point_loaded:false};
 }
 function query(scope,presence,point,sourceBlob){
  check(scope.state_count===343&&scope.orbit_count===33&&scope.known_moment_orbits===31,"frozen decorated scope");
  const states=scope.complete_state_ledger,classes=presence.literal_classes;
  check(states.length===343&&classes.length===31,"complete inputs");
  check(JSON.stringify(classes.map(c=>c.catalogue_type))===JSON.stringify(scope.affine_coordinate_convention.known_induced_count_types),"known count coordinates");
  const values=classes.map(c=>{const n=point.induced_counts[c.catalogue_type];check(Number.isSafeInteger(n)&&n>=0,"exact induced count");return BigInt(n);});
  const constants=states.map(s=>{
   check(s.affine_coefficients.length===33&&s.affine_coefficients.every(Number.isSafeInteger),"integer affine row");
   return s.affine_coefficients.slice(0,31).reduce((z,c,i)=>z+BigInt(c)*values[i],0n);
  });
  const bounds=Array.from({length:3},()=>({lower:null,upper:null,lower_rows:[],upper_rows:[]}));
  const zeroFailures=[],rowBounds=[];
  for(let i=0;i<343;i++){
   const [a,b]=states[i].affine_coefficients.slice(-2),c=constants[i];
   check(a===0||b===0||a===b,"three interval directions");
   if(!a&&!b){if(c<0n)zeroFailures.push(i);continue;}
   const direction=a===b?2:b===0?0:1,t=BigInt(a||b);
   if(t>0n){
    const lower=ceilDiv(-c,2n*t),box=bounds[direction];
    rowBounds.push({state:i,direction,kind:"lower",bound:lower,constant:c,coefficient_on_half_parameter:2n*t});
    if(box.lower===null||lower>box.lower){box.lower=lower;box.lower_rows=[i];}
    else if(lower===box.lower)box.lower_rows.push(i);
   }else{
    const upper=floorDiv(c,-2n*t),box=bounds[direction];
    rowBounds.push({state:i,direction,kind:"upper",bound:upper,constant:c,coefficient_on_half_parameter:2n*t});
    if(box.upper===null||upper<box.upper){box.upper=upper;box.upper_rows=[i];}
    else if(upper===box.upper)box.upper_rows.push(i);
   }
  }
  check(bounds.every(b=>b.lower!==null&&b.upper!==null),"bounded three-interval model");
  const solution=solveIntervals(bounds);
  const base={
   source_git_blob:sourceBlob,bindings:{scope_git_blob:"4a9b464efe9beaa097e0a8f19621f064b44b7502",presence_preparation_git_blob:"7f6b7952f81dc6c1ee0f25e12379e3dcd3656979",point_git_blob:"c881dae3be05cf289fcc45a99d72c405ac863c46"},
   root_type:42,states:343,root_orbits:33,interval_coordinates:["u0/2","u1/2","(u0+u1)/2"],
   exact_integer_intervals:bounds,all_row_bounds:rowBounds,zero_slope_negative_states:zeroFailures,interval_solution:solution,
   atom_constants:constants,optimizer_called:false,graph_existence_resolved:false
  };
  if(zeroFailures.length||!solution.feasible){
   const indices=zeroFailures.length?zeroFailures:[...new Set(bounds.flatMap(b=>[...b.lower_rows,...b.upper_rows]))];
   base.status=zeroFailures.length?"EXACT_DECORATED_ZERO_SLOPE_SEPARATOR":"EXACT_DECORATED_EVEN_INTERVAL_INFEASIBILITY";
   base.certificate_rows=indices.map(i=>({state:i,masks:states[i].masks,edge_code:states[i].edge_code,
    induced_count_form:states[i].affine_coefficients.slice(0,31).map((c,j)=>[classes[j].catalogue_type,c]).filter(x=>x[1]),
    fifth_coefficients:states[i].affine_coefficients.slice(-2),constant_value:constants[i]}));
   return wire(base);
  }
  const parameters=solution.normalized_parameters.map(x=>2n*x);
  const weights=states.map((s,i)=>constants[i]+BigInt(s.affine_coefficients[31])*parameters[0]+BigInt(s.affine_coefficients[32])*parameters[1]);
  check(weights.every(w=>w>=0n),"all atom masses nonnegative");
  const candidateEdges=scope.candidate_edges,high=scope.high_masks,index=new Map(high.map((m,i)=>[m,i]));
  const edgeMasks=candidateEdges.map(([a,b])=>(1<<index.get(a))|(1<<index.get(b)));
  const possible=bits=>edgeMasks.reduce((z,e,i)=>z|((bits&e)===e?1<<i:0),0);
  const extendsState=(a,b)=>(a.bits&b.bits)===a.bits&&((b.edge_code&possible(a.bits))===a.edge_code);
  let individual=0;
  for(let i=0;i<343;i++){
   const actual=states.reduce((s,t,j)=>s+(extendsState(states[i],t)?weights[j]:0n),0n);
   let expected;
   if(states[i].population<=4)expected=BigInt(classes[states[i].literal_class].automorphisms)*values[states[i].literal_class];
   else expected=parameters[scope.unknown_fifth_orbits.findIndex(o=>o.id===states[i].root_orbit)];
   check(actual===expected,"every original decorated moment");
   check(weights[i]%BigInt(states[i].stabilizer_indices.length)===0n,"free-action divisibility");
   individual++;
  }
  for(const o of scope.state_orbits)check(o.members.every(i=>weights[i]===weights[o.representative]),"root-orbit invariance");
  let row=0;
  for(const o of scope.state_orbits)if(o.population<=4){
   const actual=scope.quotient_coefficients[row].reduce((s,c,j)=>s+BigInt(c)*weights[scope.state_orbits[j].representative],0n);
   const k=states[o.representative].literal_class;
   check(actual===BigInt(classes[k].automorphisms)*values[k],"all 31 quotient equations");row++;
  }
  const sumU=parameters[0]+parameters[1],presenceWeights=[];
  for(let i=0;i<presence.atoms.length;i++){
   const atom=presence.atoms[i],bits=atom.masks.reduce((s,m)=>s|(1<<index.get(m)),0),mass=states.reduce((s,t,j)=>s+(t.bits===bits?weights[j]:0n),0n);
   const a=presence.affine_atoms[i];
   const c=a.induced_constant_form.reduce((s,[t,v])=>s+BigInt(v)*BigInt(point.induced_counts[t]),0n);
   check(mass===c+BigInt(a.fifth_moment_slope)*sumU,"all presence coarsenings");
   presenceWeights.push(mass);
  }
  for(const m of presence.all_small_moment_forms){
   const target=m.induced_count_form.reduce((s,[t,c])=>s+BigInt(c)*BigInt(point.induced_counts[t]),0n);
   const required=presence.atoms[m.atom_index].masks.reduce((s,x)=>s|(1<<index.get(x)),0);
   const actual=states.reduce((s,t,j)=>s+((t.bits&required)===required?weights[j]:0n),0n);
   check(actual===target,"all known presence moments");
  }
  const mass=weights.reduce((a,b)=>a+b,0n),rootMass=24n*BigInt(point.induced_counts[42]);
  check(mass===rootMass,"total root mass");
  const g=weights.reduce(gcd,mass);
  return wire({...base,status:"EXACT_ROOT42_COMPLETE_DECORATED_MOMENT_DISTRIBUTION",fifth_parameters:parameters,presence_fifth_parameter:sumU,
   labelled_root_mass:mass,reduced_probability_denominator:mass/g,
   atom_weights:states.map((s,i)=>({state_index:i,presence_bits:s.bits,masks:s.masks,edge_code:s.edge_code,root_orbit:s.root_orbit,weight:weights[i]})),
   positive_atoms:weights.filter(w=>w>0n).length,zero_atoms:weights.filter(w=>w===0n).length,
   orbit_weights:scope.state_orbits.map((o,j)=>({orbit:j,per_state_weight:weights[o.representative],total_weight:BigInt(o.members.length)*weights[o.representative],population:o.population})),
   presence_atom_weights:presenceWeights,
   original_decorated_moment_equations_checked:individual,known_quotient_equations_checked:row,
   stabilizer_divisibilities_checked:343,presence_coarsenings_checked:253,known_presence_moments_checked:241});
 }
 return {query,controls,solveIntervals,wire};
}

if(typeof module!=="undefined"){
 module.exports={makeRoot42DecoratedQuery};
 if(require.main===module){
  const api=makeRoot42DecoratedQuery(),fs=require("fs"),crypto=require("crypto");
  const blob=p=>{const b=fs.readFileSync(p);return crypto.createHash("sha1").update(Buffer.from("blob "+b.length+"\0")).update(b).digest("hex");};
  const [mode,scopePath,presencePath,pointPath]=process.argv.slice(2);
  if(mode==="controls")console.log(JSON.stringify(api.controls(),null,2));
  else{
   if(mode!=="query"||!scopePath||!presencePath||!pointPath)throw Error("Usage: node query.js controls | query scope.json presence-preparation.json point.json");
   if(blob(scopePath)!=="4a9b464efe9beaa097e0a8f19621f064b44b7502"||blob(presencePath)!=="7f6b7952f81dc6c1ee0f25e12379e3dcd3656979"||blob(pointPath)!=="c881dae3be05cf289fcc45a99d72c405ac863c46")throw Error("Frozen input binding");
   const read=p=>JSON.parse(fs.readFileSync(p,"utf8"));
   console.log(JSON.stringify(api.query(read(scopePath),read(presencePath),read(pointPath),blob(__filename)),null,2));
  }
 }
}
