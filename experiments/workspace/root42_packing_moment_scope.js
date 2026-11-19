"use strict";

function root42Scope(record,knownPreparation,isomorphisms) {
  const check=(x,m)=>{if(!x)throw Error(m);};
  function pop(x){let n=0;while(x){n+=x&1;x>>>=1;}return n;}
  const high=record.high_masks,root=record.root_rows;
  check(record.root_type===42&&JSON.stringify(root)==="[32,32,32,32,0,15]","root42");
  function rows(masks,edges=[]){
    const a=root.slice();
    for(let j=0;j<masks.length;j++){a.push(masks[j]);for(let i=0;i<6;i++)if(masks[j]&(1<<i))a[i]|=1<<(6+j);}
    for(const [i,j]of edges){a[6+i]|=1<<(6+j);a[6+j]|=1<<(6+i);}
    return a;
  }
  function valid(a){for(let i=0;i<a.length;i++)for(let j=i+1;j<a.length;j++)if(pop(a[i]&a[j])+((a[i]>>j)&1)>2)return false;return true;}
  const universe=Array.from({length:64},(_,i)=>i).filter(m=>pop(m)>=3),uindex=new Map(universe.map((m,i)=>[m,i]));
  const code=ms=>ms.reduce((s,m)=>s|(1n<<BigInt(uindex.get(m))),0n);
  const expected=[];
  for(let i=0;i<4;i++)for(let j=i+1;j<4;j++)expected.push((1<<i)|(1<<j)|16);
  for(let i=0;i<4;i++)expected.push((1<<i)|16|32);
  expected.sort((a,b)=>a-b);check(JSON.stringify(expected)===JSON.stringify(high),"A/B masks");
  const atoms=[],allSizeCounts={},quotientSizeCounts={};
  for(let bits=0;bits<(1<<high.length);bits++){
    const masks=high.filter((_m,i)=>(bits>>i)&1),deg=[0,0,0,0];let bs=0;
    for(const m of masks){if(m&32)bs++;for(let i=0;i<4;i++)if(m&(1<<i))deg[i]++;}
    const inequalities=bs<=2&&deg.every(d=>d<=2),caps=valid(rows(masks));
    check(inequalities===caps,"exact structural inequalities");
    if(caps){atoms.push({masks,code:code(masks)});allSizeCounts[masks.length]=(allSizeCounts[masks.length]||0)+1;}
  }
  atoms.sort((a,b)=>a.code<b.code?-1:1);
  check(atoms.length===253&&atoms.every(a=>a.masks.length<=5),"complete atom census");
  const index=new Map(atoms.map((a,i)=>[a.code.toString(),i])),groups=[];
  function moved(mask,p){let x=0;for(let i=0;i<6;i++)if(mask&(1<<i))x|=1<<p[i];return x;}
  const covered=new Set();
  for(let i=0;i<atoms.length;i++)if(!covered.has(i)){
    const members=[...new Set(record.complete_root_automorphisms.map(p=>index.get(code(atoms[i].masks.map(m=>moved(m,p))).toString())))].sort((a,b)=>a-b);
    check(members.every(x=>x!==undefined),"complete action");for(const a of members)covered.add(a);
    const k=atoms[i].masks.length;groups.push({representative:i,members,population:k,masks:atoms[i].masks});
    quotientSizeCounts[k]=(quotientSizeCounts[k]||0)+1;
  }
  check(groups.length===24&&groups.filter(g=>g.population===5).length===1,"24 orbits");
  const fiveAtoms=atoms.filter(a=>a.masks.length===5);
  for(const a of fiveAtoms){
    const edges=a.masks.filter(m=>!(m&32)).map(m=>Array.from({length:4},(_,i)=>i).filter(i=>m&(1<<i)));
    const endpoints=a.masks.filter(m=>m&32).map(m=>[0,1,2,3].find(i=>m&(1<<i))),degrees=[0,0,0,0];
    for(const [i,j]of edges){degrees[i]++;degrees[j]++;}
    check(edges.length===3&&endpoints.length===2&&degrees.every(d=>d===1||d===2)&&endpoints.every(i=>degrees[i]===1),"Hamiltonian path endpoints");
  }
  const flags=[{masks:[],edge:0}];
  for(const m of high)flags.push({masks:[m],edge:0});
  for(let a=0;a<64;a++)for(let b=a+1;b<64;b++)for(const e of[0,1])if(Math.min(pop(a),pop(b))+e>=3&&valid(rows([a,b],e?[[0,1]]:[])))flags.push({masks:[a,b],edge:e});
  check(flags.length===174,"full existing flag count");
  const singles=new Map(),pairs=new Map();
  flags.forEach((f,i)=>{if(f.masks.length===1)singles.set(f.masks[0],i);if(f.masks.length===2&&f.masks.every(m=>pop(m)>=3)){const k=f.masks.join(",");if(!pairs.has(k))pairs.set(k,[]);pairs.get(k).push(i);}});
  const lower=(a,b)=>Math.max(a,b)*(Math.max(a,b)+1)/2+Math.min(a,b);
  function partitions(T){
    if(!T.length)return [[[0,0]]];
    if(T.length===1)return [[[singles.get(T[0]),0]]];
    if(T.length===2)return [(pairs.get(T.join(","))||[]).map(i=>[i,0]),[[singles.get(T[0]),singles.get(T[1])]]];
    if(T.length===3)return [0,1,2].map(s=>(pairs.get(T.filter((_m,i)=>i!==s).join(","))||[]).map(i=>[i,singles.get(T[s])]));
    return [[0,1,2,3],[0,2,1,3],[0,3,1,2]].map(([a,b,c,d])=>(pairs.get([T[a],T[b]].join(","))||[]).flatMap(i=>(pairs.get([T[c],T[d]].join(","))||[]).map(j=>[i,j])));
  }
  const fullRows=new Set(),representativeRows=new Set(),pool=[],contexts=new Map(),completionHist={},representativeCompletionHist={};
  function graphClass(a){
    for(let i=0;i<pool.length;i++)if(a.length===pool[i].rows.length&&isomorphisms(a,pool[i].rows).count)return i;
    const aut=isomorphisms(a).count,known=[];
    for(const g of knownPreparation.literal_graph_classes)if(a.length===g.rows.length&&isomorphisms(a,g.rows).count)known.push(g.literal_class);
    check(known.length<=1,"known literal uniqueness");
    const id=pool.length;pool.push({rows:a,automorphisms:aut,known_literal_class:known.length?known[0]:null});return id;
  }
  let fullCompletionCount=0,repCompletionCount=0,ambiguousMonomials=0,maxCompletions=0;
  const small=atoms.map((a,i)=>({...a,index:i})).filter(a=>a.masks.length<=4),representatives=new Set(groups.filter(g=>g.population<=4).map(g=>g.representative));
  for(const atom of small){
    const T=atom.masks,eligible=[];
    for(let i=0;i<T.length;i++)for(let j=i+1;j<T.length;j++){
      const disjointA=!(T[i]&32)&&!(T[j]&32)&&pop((T[i]&15)&(T[j]&15))===0;
      check(disjointA===valid(rows([T[i],T[j]],[[0,1]])),"eligible edge classification");
      if(disjointA)eligible.push([i,j]);
    }
    const completionCount=1<<eligible.length;fullCompletionCount+=completionCount;
    completionHist[completionCount]=(completionHist[completionCount]||0)+1;
    if(completionCount>1)ambiguousMonomials++;maxCompletions=Math.max(maxCompletions,completionCount);
    const recipes=partitions(T);
    for(const partition of recipes)for(const [a,b]of partition)fullRows.add(lower(a,b));
    if(!representatives.has(atom.index))continue;
    repCompletionCount+=completionCount;representativeCompletionHist[completionCount]=(representativeCompletionHist[completionCount]||0)+1;
    const completions=[];
    for(let bits=0;bits<completionCount;bits++){
      const edges=eligible.filter((_e,j)=>(bits>>j)&1),a=rows(T,edges);
      check(valid(a),"all matching-edge choices valid");
      completions.push({edges,literal_class:graphClass(a)});
    }
    for(const partition of recipes)for(const [a,b]of partition){
      const r=lower(a,b);representativeRows.add(r);const expectedCounts=new Map();
      for(const c of completions){
        let consistent=true;
        for(const f of[flags[a],flags[b]])if(f.masks.length===2){
          const x=T.indexOf(f.masks[0]),y=T.indexOf(f.masks[1]);
          const e=c.edges.some(([i,j])=>i===Math.min(x,y)&&j===Math.max(x,y));
          if(Number(e)!==f.edge)consistent=false;
        }
        if(consistent)expectedCounts.set(c.literal_class,(expectedCounts.get(c.literal_class)||0)+1);
      }
      const signature=JSON.stringify([...expectedCounts].sort((a,b)=>a[0]-b[0]));
      if(contexts.has(r))check(contexts.get(r).signature===signature,"same row semantics");else contexts.set(r,{flags:[a,b],signature,expectedCounts});
    }
  }
  const fingerprints=pool.map((_g,i)=>JSON.stringify([...contexts].sort((a,b)=>a[0]-b[0]).filter(([_r,c])=>c.expectedCounts.has(i)).map(([r,c])=>[r,c.expectedCounts.get(i)])));
  const fingerprintGroups=new Map();fingerprints.forEach((s,i)=>{if(!fingerprintGroups.has(s))fingerprintGroups.set(s,[]);fingerprintGroups.get(s).push(i);});
  return {
    status:"ROOT42_POINT_INDEPENDENT_SCOPE_ONLY",
    root_type:42,root_rows:root,high_masks:high,automorphism_order:24,
    existing_quotient:{shape:record.quotient_shape,nonzeros:record.quotient_nnz,exact_rank:record.exact_row_rank},
    all_1024_presence_sets_checked:true,atom_count:253,atom_population_counts:allSizeCounts,orbit_count:24,orbit_population_counts:quotientSizeCounts,
    full_moment_monomials:241,representative_moment_rows:23,full_flag_records:174,
    all_supported_product_rows:fullRows.size,representative_supported_product_rows:representativeRows.size,
    representative_tensor_row_indices:[...representativeRows].sort((a,b)=>a-b),
    full_literal_completions:fullCompletionCount,representative_literal_completions:repCompletionCount,
    ambiguous_full_monomials:ambiguousMonomials,maximum_literal_completions:maxCompletions,
    full_completion_histogram:completionHist,representative_completion_histogram:representativeCompletionHist,
    representative_literal_classes:pool.length,known_from_remaining32:pool.filter(g=>g.known_literal_class!==null).length,
    new_literal_classes:pool.filter(g=>g.known_literal_class===null).length,
    expected_fingerprint_groups:fingerprintGroups.size,ambiguous_expected_fingerprint_groups:[...fingerprintGroups.values()].filter(g=>g.length>1).map(g=>g),
    exact_interval_dimension:1,unknown_fifth_moment_orbit_size:12,
    direct_atom_list:atoms.map(a=>({masks:a.masks,code:a.code.toString()})),
    atom_orbits:groups,representative_literal_class_records:pool,
    required_scope_array_keys:["atom_codes","small_atom_ids","supported_row_orbits","quotient_coefficients","labels","representatives","sizes","populations"],
    no_moment_values_evaluated:true,no_optimizer:true,no_tensor_rows_retrieved:true
  };
}

if(typeof module!=="undefined"&&module.exports) {
  module.exports={root42Scope};
  if(require.main===module) {
    const fs=require("fs"),crypto=require("crypto"),path=require("path");
    const [scopePath,knownPath]=process.argv.slice(2);
    function blob(p){const b=fs.readFileSync(p);return crypto.createHash("sha1").update("blob "+b.length+"\0").update(b).digest("hex");}
    if(!scopePath||!knownPath)throw Error("Usage: node scope.js original-scope.json small-roots-preparation.json");
    if(blob(scopePath)!=="4bc0045ae1447160dbf667a1918e32a9f4e3c454"||blob(knownPath)!=="537b722f2dd4f964c5fa053d5398e41c60b4ed9d")throw Error("Frozen input binding");
    const dependency=path.join(__dirname,"root49_packing_moment_recovery_check.js");
    if(blob(dependency)!=="d547df71ef544fc7e36a8580bc9f7bdc311d6871")throw Error("Frozen isomorphism binding");
    const record=JSON.parse(fs.readFileSync(scopePath,"utf8")).roots.find(r=>r.root_type===42);
    const known=JSON.parse(fs.readFileSync(knownPath,"utf8"));
    const iso=require(dependency).makeRoot49RecoveryTools().isomorphisms;
    console.log(JSON.stringify(root42Scope(record,known,iso),null,2));
  }
}
