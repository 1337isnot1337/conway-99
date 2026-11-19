"use strict";

function root42DecoratedScope(presence, isomorphisms) {
  const check=(v,m)=>{if(!v)throw Error(m);};
  const pop=n=>{let s=0;while(n){s+=n&1;n>>>=1;}return s;};
  const root=[32,32,32,32,0,15];
  check(JSON.stringify(presence.root_rows)===JSON.stringify(root),"literal root");
  function rows(masks,edges=[]) {
    const r=root.slice();
    for(let j=0;j<masks.length;j++){
      r.push(masks[j]);
      for(let i=0;i<6;i++)if(masks[j]>>i&1)r[i]|=1<<(6+j);
    }
    for(const [i,j] of edges){r[6+i]|=1<<(6+j);r[6+j]|=1<<(6+i);}
    return r;
  }
  function caps(r){
    for(let i=0;i<r.length;i++)for(let j=i+1;j<r.length;j++)
      if(pop(r[i]&r[j])+((r[i]>>j)&1)>2)return false;
    return true;
  }
  const high=[];
  for(let m=0;m<64;m++)if(pop(m)>=3&&caps(rows([m])))high.push(m);
  check(JSON.stringify(high)===JSON.stringify(presence.high_masks),"complete high masks");
  check(high.length===10,"ten masks");
  const index=new Map(high.map((m,i)=>[m,i]));
  const candidateEdges=[];
  for(let i=0;i<10;i++)for(let j=i+1;j<10;j++){
    const allowed=caps(rows([high[i],high[j]],[[0,1]]));
    const complementaryA=!(high[i]&32)&&!(high[j]&32)&&((high[i]&15)&(high[j]&15))===0;
    check(allowed===complementaryA,"all 45 pair edge classifications");
    if(allowed)candidateEdges.push([i,j]);
  }
  check(candidateEdges.length===3,"three possible edges");
  const edgeIndex=new Map(candidateEdges.map((e,i)=>[e.join(","),i]));
  const possibleEdges=bits=>candidateEdges.reduce((s,[a,b],i)=>s|((bits>>a&1)&&(bits>>b&1)?1<<i:0),0);
  const states=[],presenceSets=[],populations={},presencePopulations={};
  let fullGraphChoices=0;
  for(let bits=0;bits<1024;bits++){
    const masks=high.filter((_m,i)=>bits>>i&1);
    const valid=caps(rows(masks)),aDegree=[0,0,0,0];
    let bCount=0;
    for(const m of masks){if(m&32)bCount++;for(let i=0;i<4;i++)if(m>>i&1)aDegree[i]++;}
    check(valid===(bCount<=2&&aDegree.every(v=>v<=2)),"complete presence inequalities");
    if(!valid)continue;
    check(masks.length<=5,"maximum population five");
    presenceSets.push(bits);presencePopulations[masks.length]=(presencePopulations[masks.length]||0)+1;
    const localPairs=[];
    for(let i=0;i<masks.length;i++)for(let j=i+1;j<masks.length;j++)localPairs.push([i,j]);
    const found=new Set();
    for(let graph=0;graph<(1<<localPairs.length);graph++){
      fullGraphChoices++;
      const edges=localPairs.filter((_e,i)=>graph>>i&1),literal=rows(masks,edges);
      if(!caps(literal))continue;
      let globalEdges=0;
      for(const [i,j] of edges){
        const key=[index.get(masks[i]),index.get(masks[j])].sort((a,b)=>a-b).join(",");
        check(edgeIndex.has(key),"allowed edge found in complete pair census");
        globalEdges|=1<<edgeIndex.get(key);
      }
      check(!found.has(globalEdges),"unique graph");
      found.add(globalEdges);
      states.push({bits,masks,edge_code:globalEdges,rows:literal,population:masks.length});
      populations[masks.length]=(populations[masks.length]||0)+1;
    }
    const possible=possibleEdges(bits),expected=[];
    for(let e=0;e<8;e++)if((e&possible)===e)expected.push(e);
    check(JSON.stringify([...found].sort((a,b)=>a-b))===JSON.stringify(expected),"all matching subgraphs and no others");
  }
  states.sort((a,b)=>a.bits-b.bits||a.edge_code-b.edge_code);
  const key=s=>s.bits+":"+s.edge_code;
  const byKey=new Map(states.map((s,i)=>[key(s),i]));
  check(states.length===343&&presenceSets.length===253,"complete state count");
  function permutations(a){
    if(!a.length)return [[]];
    return a.flatMap((x,i)=>permutations(a.filter((_y,j)=>i!==j)).map(p=>[x,...p]));
  }
  const group=permutations([0,1,2,3]).map(p=>[...p,4,5]);
  check(JSON.stringify(group)===JSON.stringify(presence.actual_root_automorphisms),"literal full S4 group");
  const moveMask=(m,p)=>{let x=0;for(let i=0;i<6;i++)if(m>>i&1)x|=1<<p[i];return x;};
  const transports=group.map(p=>{
    for(let i=0;i<6;i++)for(let j=0;j<6;j++)check(((root[i]>>j)&1)===((root[p[i]]>>p[j])&1),"root automorphism");
    const highMap=high.map(m=>index.get(moveMask(m,p)));
    check(new Set(highMap).size===10&&!highMap.includes(undefined),"mask permutation");
    const edges=candidateEdges.map(([a,b])=>edgeIndex.get([highMap[a],highMap[b]].sort((x,y)=>x-y).join(",")));
    check(new Set(edges).size===3&&!edges.includes(undefined),"edge permutation");
    return {root:p,high:highMap,edges};
  });
  function moveState(s,t){
    let bits=0,edge_code=0;
    for(let i=0;i<10;i++)if(s.bits>>i&1)bits|=1<<t.high[i];
    for(let i=0;i<3;i++)if(s.edge_code>>i&1)edge_code|=1<<t.edges[i];
    const out=byKey.get(bits+":"+edge_code);check(out!==undefined,"complete state action");return out;
  }
  const orbitOf=new Array(states.length).fill(-1),orbits=[],stabilizers=[];
  for(let i=0;i<states.length;i++){
    const images=transports.map(t=>moveState(states[i],t));
    stabilizers.push(images.map((v,j)=>v===i?j:-1).filter(x=>x>=0));
    if(orbitOf[i]>=0)continue;
    const members=[...new Set(images)].sort((a,b)=>a-b),id=orbits.length;
    for(const j of members){check(orbitOf[j]<0,"orbit partition");orbitOf[j]=id;}
    check(members.length*stabilizers[i].length===24,"orbit stabilizer");
    orbits.push({representative:i,members,population:states[i].population,edge_count:pop(states[i].edge_code)});
  }
  const knownOrbits=orbits.map((o,i)=>({...o,id:i})).filter(o=>o.population<=4);
  const fifthOrbits=orbits.map((o,i)=>({...o,id:i})).filter(o=>o.population===5);
  check(orbits.length===33&&knownOrbits.length===31&&fifthOrbits.length===2,"33 orbits and two unknowns");
  check(fifthOrbits.every(o=>o.members.length===12&&stabilizers[o.representative].length===2),"two fifth moments even");
  const classes=presence.literal_classes,known=new Map();
  check(classes.length===31,"frozen literal classes");
  let literalMatches=0;
  for(let i=0;i<states.length;i++)if(states[i].population<=4){
    const found=[];
    for(let j=0;j<classes.length;j++)if(states[i].rows.length===classes[j].rows.length&&isomorphisms(states[i].rows,classes[j].rows).count)found.push(j);
    check(found.length===1,"unique independent literal type matching");
    known.set(i,found[0]);literalMatches++;
  }
  for(const c of classes)check(isomorphisms(c.rows).count===c.automorphisms,"exact literal automorphism factor");
  const superset=(a,b)=>((b.bits&a.bits)===a.bits)&&((b.edge_code&possibleEdges(a.bits))===a.edge_code);
  const upper=states.map(a=>states.map((b,j)=>superset(a,b)?j:-1).filter(j=>j>=0));
  const dimension=classes.length+2;
  const affine=states.map((a,i)=>{
    const c=Array(dimension).fill(0);
    for(const j of upper[i]){
      const sign=(states[j].population-a.population)%2?-1:1;
      if(known.has(j))c[known.get(j)]+=sign*classes[known.get(j)].automorphisms;
      else{
        const q=fifthOrbits.findIndex(o=>o.id===orbitOf[j]);check(q>=0,"unknown orbit");c[classes.length+q]+=sign;
      }
    }
    return c;
  });
  let zetaTerms=0;
  for(let i=0;i<states.length;i++){
    const sum=Array(dimension).fill(0);
    for(const j of upper[i]){for(let k=0;k<dimension;k++)sum[k]+=affine[j][k];zetaTerms++;}
    const expected=Array(dimension).fill(0);
    if(known.has(i))expected[known.get(i)]=classes[known.get(i)].automorphisms;
    else expected[classes.length+fifthOrbits.findIndex(o=>o.id===orbitOf[i])]=1;
    check(JSON.stringify(sum)===JSON.stringify(expected),"all symbolic induced zeta identities");
  }
  for(let i=0;i<states.length;i++){
    const s=stabilizers[i].length;
    check(affine[i].slice(0,classes.length).every(c=>c%s===0),"constant coefficient stabilizer divisibility");
    check(affine[i].slice(classes.length).every(c=>(2*c)%s===0),"even unknowns suffice for all divisibilities");
  }
  const presenceIndex=new Map(presence.atoms.map((a,i)=>[a.masks.reduce((s,m)=>s|(1<<index.get(m)),0),i]));
  let coarsenings=0;
  const typeIndex=new Map(classes.map((c,i)=>[c.catalogue_type,i]));
  for(const bits of presenceSets){
    const sum=Array(dimension).fill(0);
    for(let j=0;j<states.length;j++)if(states[j].bits===bits)for(let k=0;k<dimension;k++)sum[k]+=affine[j][k];
    const original=presence.affine_atoms[presenceIndex.get(bits)],expected=Array(dimension).fill(0);
    for(const [t,c] of original.induced_constant_form){check(typeIndex.has(t),"known presence type");expected[typeIndex.get(t)]+=Number(c);}
    expected[classes.length]=expected[classes.length+1]=original.fifth_moment_slope;
    check(JSON.stringify(sum)===JSON.stringify(expected),"presence coarsening with u=u0+u1");
    coarsenings++;
  }
  const orbitRows=knownOrbits.map(o=>orbits.map(v=>v.members.reduce((sum,j)=>sum+(superset(states[o.representative],states[j])?1:0),0)));
  // The invariant equation for one representative uses one shared exact-state
  // mass per labelled state of an orbit, not the orbit-total mass.
  const orders=knownOrbits.map((o,i)=>({o,i})).sort((a,b)=>a.o.population-b.o.population||a.i-b.i);
  for(let i=0;i<orders.length;i++)for(let j=0;j<orders.length;j++){
    const v=orbitRows[orders[i].i][orders[j].o.id];
    if(i===j)check(v===1,"known quotient unit diagonal");
    if(i>j)check(v===0,"known quotient triangular minor");
  }
  return {
    status:"COMPLETE_POINT_INDEPENDENT_ROOT42_DECORATED_TWO_PARAMETER_SCOPE",
    root_type:42,root_rows:root,high_masks:high,candidate_edges:candidateEdges.map(e=>e.map(i=>high[i])),
    source_presence_preparation_git_blob:"7f6b7952f81dc6c1ee0f25e12379e3dcd3656979",
    literal_isomorphism_source_git_blob:"d547df71ef544fc7e36a8580bc9f7bdc311d6871",
    actual_root_automorphisms:group,all_presence_sets_checked:1024,complete_pair_edge_checks:45,
    complete_internal_graph_choices_checked:fullGraphChoices,
    population_counts:populations,presence_population_counts:presencePopulations,
    state_count:states.length,known_state_count:known.size,unknown_state_count:states.length-known.size,
    orbit_count:orbits.length,known_moment_orbits:knownOrbits.length,unknown_moment_orbits:fifthOrbits.length,
    complete_state_ledger:states.map((s,i)=>({...s,index:i,root_orbit:orbitOf[i],stabilizer_indices:stabilizers[i],
      literal_class:known.has(i)?known.get(i):null,affine_coefficients:affine[i]})),
    state_orbits:orbits,unknown_fifth_orbits:fifthOrbits,
    affine_coordinate_convention:{known_induced_count_types:classes.map(c=>c.catalogue_type),last_two_coordinates:"Shared exact weight u0 or u1 of one labelled fifth-state; both must be even."},
    exact_literal_matches:literalMatches,exact_literal_automorphism_checks:classes.length,
    symbolic_zeta_equations:states.length,symbolic_zeta_terms:zetaTerms,coefficientwise_stabilizer_checks:states.length,
    presence_coarsenings:coarsenings,presence_parameter_identity:"u=u0+u1",
    invariant_known_moment_rank:31,invariant_affine_dimension:2,
    sufficient_unknown_moduli:[2,2],quotient_coefficients:orbitRows,
    no_tensor_generation:true,no_new_catalogue_type_lookup:true,no_count_point_loaded:true,no_optimizer:true,
    point_query_performed:false,
    scope:"Complete visible-cap decorated states over this fixed six-root. All lower moments use frozen literal induced forms. Nonnegative even-parameter feasibility has not been evaluated."
  };
}

if(typeof module!=="undefined"){
  module.exports={root42DecoratedScope};
  if(require.main===module){
    const fs=require("fs"),path=require("path"),crypto=require("crypto");
    const blob=p=>{
      const raw=fs.readFileSync(p);
      return crypto.createHash("sha1").update(Buffer.from("blob "+raw.length+"\0")).update(raw).digest("hex");
    };
    const inputPath=process.argv[2];
    if(!inputPath)throw Error("Usage: node root42_decorated_interval_scope.js root42-presence-preparation.json");
    const isoPath=path.join(__dirname,"root49_packing_moment_recovery_check.js");
    if(blob(isoPath)!=="d547df71ef544fc7e36a8580bc9f7bdc311d6871")throw Error("Frozen literal isomorphism dependency");
    if(blob(inputPath)!=="7f6b7952f81dc6c1ee0f25e12379e3dcd3656979")throw Error("Frozen root42 presence preparation");
    const iso=require(isoPath).makeRoot49RecoveryTools().isomorphisms;
    const result=root42DecoratedScope(JSON.parse(fs.readFileSync(inputPath,"utf8")),iso);
    console.log(JSON.stringify(result,null,2));
  }
}
