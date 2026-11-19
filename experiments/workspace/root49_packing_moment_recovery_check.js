"use strict";

/* Exact root49 recovery calculation. Public inputs are immutable checkpoint42 files.
   Preparation is point-independent. Query uses BigInt and no optimizer.
   Local catalogue identities come from unique frozen product terms; the global
   catalogue is not independently rebuilt. */

function makeRoot49RecoveryTools() {
  "use strict";
  const ROOT=49, ROWS=[48,32,32,32,1,15];
  const BINDINGS={
    commit:"a20ec755c7364c4b7a6e40317e5a7a745224679d",
    extraction_git_blob:"e37ba84dab96432460fd4360af0d4de673be1649",
    scope_git_blob:"4bc0045ae1447160dbf667a1918e32a9f4e3c454",
    scope_sha256:"fd577aca265beb46bee2206ea8d474edcd048d6d0bdc12f4d4d7d4709e607142",
    arrays_sha256:"4af4af187681c33af2ce0d64fc1e7c3e7afb30e37eec181c741776883d602533",
    tensors_sha256:"84d69eb567b961f8cdce332f66b152a2cac803feb50a5a7b161d67479b31fb5c",
    point_git_blob:"c881dae3be05cf289fcc45a99d72c405ac863c46",
    point_sha256:"0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df"
  };
  function assert(x,m){if(!x)throw Error(m);}
  function same(a,b){return JSON.stringify(a)===JSON.stringify(b);}
  function pc(x){let n=0;for(;x;x&=x-1)n++;return n;}
  function choose(a,k){
    const out=[];
    function rec(at,chosen){if(chosen.length===k){out.push(chosen.slice());return;}
      for(let i=at;i<=a.length-(k-chosen.length);i++){chosen.push(a[i]);rec(i+1,chosen);chosen.pop();}}
    rec(0,[]);return out;
  }
  function attach(masks,edgePairs=[]){
    const rows=ROWS.slice();
    masks.forEach((m,j)=>{rows.push(m);for(let i=0;i<6;i++)if((m>>i)&1)rows[i]|=1<<(6+j);});
    for(const [a,b] of edgePairs){rows[6+a]|=1<<(6+b);rows[6+b]|=1<<(6+a);}
    return rows;
  }
  function violation(rows){
    for(let i=0;i<rows.length;i++)for(let j=i+1;j<rows.length;j++){
      const adjacency=(rows[i]>>j)&1,common=pc(rows[i]&rows[j]);
      if(adjacency+common>2)return {pair:[i,j],adjacency,common_neighbors:common};
    }
    return null;
  }
  function isomorphisms(left,right=left,saveFirst=false){
    const n=left.length;
    assert(n<=10,"isomorphism order bound");
    if(right.length!==n)return {count:0,first:null};
    for(const rows of [left,right])for(let i=0;i<n;i++){
      assert(Number.isSafeInteger(rows[i])&&rows[i]>=0&&rows[i]<(1<<n)&&!((rows[i]>>i)&1),"simple graph row");
      for(let j=0;j<n;j++)assert(((rows[i]>>j)&1)===((rows[j]>>i)&1),"symmetric graph");
    }
    let colors=[left.map(pc),right.map(pc)];
    for(let pass=0;pass<n;pass++){
      const keys=[left,right].map((rows,g)=>rows.map((row,i)=>{
        const neighbors=[];for(let j=0;j<n;j++)if((row>>j)&1)neighbors.push(colors[g][j]);
        neighbors.sort((a,b)=>a-b);return JSON.stringify([colors[g][i],neighbors]);
      }));
      const distinct=[...new Set(keys.flat())].sort(),id=new Map(distinct.map((key,i)=>[key,i]));
      const next=keys.map(ks=>ks.map(key=>id.get(key)));
      const before=colors.flat(),after=next.flat();let stable=true;
      for(let i=0;i<2*n;i++)for(let j=0;j<i;j++)if((before[i]===before[j])!==(after[i]===after[j]))stable=false;
      colors=next;if(stable)break;
    }
    const cells=new Map();colors[1].forEach((c,i)=>{if(!cells.has(c))cells.set(c,[]);cells.get(c).push(i);});
    const hist=x=>JSON.stringify([...x.reduce((m,c)=>m.set(c,(m.get(c)||0)+1),new Map())].sort((a,b)=>a[0]-b[0]));
    if(hist(colors[0])!==hist(colors[1]))return {count:0,first:null};
    const order=Array.from({length:n},(_,i)=>i).sort((a,b)=>cells.get(colors[0][a]).length-cells.get(colors[0][b]).length||pc(left[b])-pc(left[a])||a-b);
    const image=Array(n).fill(-1);let used=0,count=0,first=null;
    function rec(at){
      if(at===n){count++;if(saveFirst&&first===null)first=image.slice();return;}
      const a=order[at];
      for(const b of cells.get(colors[0][a]))if(!((used>>b)&1)){
        let good=true;for(let z=0;z<at;z++){const c=order[z];if(((left[a]>>c)&1)!==((right[b]>>image[c])&1)){good=false;break;}}
        if(good){image[a]=b;used|=1<<b;rec(at+1);used^=1<<b;image[a]=-1;}
      }
    }
    rec(0);assert(Number.isSafeInteger(count)&&count>=0,"isomorphism count");return {count,first};
  }
  function lower(a,b){if(a<b)[a,b]=[b,a];return a*(a+1)/2+b;}
  function wire(x){return JSON.parse(JSON.stringify(x,(_k,v)=>typeof v==="bigint"?v.toString():v));}
  function inverseMoments(atoms,moments){
    const order=atoms.map((_,i)=>i).sort((a,b)=>atoms[b].population-atoms[a].population||a-b);
    const weights=Array(atoms.length).fill(0n);
    for(const i of order){
      let value=moments[i];
      for(const j of order)if(atoms[j].population>atoms[i].population&&(atoms[j].code&atoms[i].code)===atoms[i].code)value-=weights[j];
      weights[i]=value;
    }
    for(let i=0;i<atoms.length;i++){
      let reconstructed=0n,mobius=0n;
      for(let j=0;j<atoms.length;j++)if((atoms[j].code&atoms[i].code)===atoms[i].code){
        reconstructed+=weights[j];
        mobius+=((atoms[j].population-atoms[i].population)&1?-1n:1n)*moments[j];
      }
      assert(reconstructed===moments[i]&&mobius===weights[i],"exact inversion/reconstruction");
    }
    return weights;
  }
  function directPatternEmbeddingCount(host,masks){
    const n=host.length, image=Array(6).fill(-1);let used=0,count=0;
    function rec(at){
      if(at===6){
        const seen=new Set();
        for(let x=0;x<n;x++)if(!((used>>x)&1)){
          let mask=0;for(let i=0;i<6;i++)if((host[x]>>image[i])&1)mask|=1<<i;
          if(pc(mask)>=3){assert(!seen.has(mask),"high-class uniqueness in literal cap host");seen.add(mask);}
        }
        if(masks.every(m=>seen.has(m)))count++;
        return;
      }
      for(let x=0;x<n;x++)if(!((used>>x)&1)){
        let good=true;for(let i=0;i<at;i++)if(((ROWS[at]>>i)&1)!==((host[x]>>image[i])&1)){good=false;break;}
        if(good){image[at]=x;used|=1<<x;rec(at+1);used^=1<<x;image[at]=-1;}
      }
    }
    rec(0);return count;
  }
  function prepare(input,scope,sourceGitBlob=null){
    assert(input.root_type===ROOT&&input.source_commit===BINDINGS.commit&&!input.optimizer_called,"input provenance");
    assert(input.input_bindings["order10-high-mask-packing-other-roots-scope01-arrays.npz"].sha256===BINDINGS.arrays_sha256,"array binding");
    assert(input.input_bindings["prism-zero-order10-r6s2-blocks.pickle.gz"].sha256===BINDINGS.tensors_sha256,"tensor binding");
    assert(scope.complete&&scope.roots.length===61,"complete scope input");
    const record=scope.roots.find(r=>r.root_type===ROOT);
    assert(record&&same(record.root_rows,ROWS)&&record.complete&&same(record.quotient_shape,[19,19]),"root scope");
    const arrays=input.scope_arrays;
    function data(name,shape,dtype){
      const item=arrays["r49_"+name];assert(item&&same(item.shape,shape)&&item.dtype===dtype,"array "+name);return item.data;
    }
    const atomNumbers=data("atom_codes",[80],"uint64"),labels=data("labels",[80],"int32");
    const representatives=data("representatives",[19],"int32"),sizes=data("sizes",[19],"int32");
    const C=data("quotient_coefficients",[19,19],"int64");
    assert(same(data("small_atom_ids",[80],"int32"),Array.from({length:80},(_,i)=>i)),"all small atoms");
    assert(same(data("supported_row_orbits",[19],"int32"),Array.from({length:19},(_,i)=>i)),"all orbit rows");
    assert(atomNumbers.every((x,i)=>Number.isSafeInteger(x)&&x>=0&&(!i||atomNumbers[i-1]<x))&&atomNumbers[0]===0,"ordered atom codes");
    assert(C.every(r=>r.length===19&&r.every(x=>Number.isSafeInteger(x)&&x>=0)),"integer quotient");
    const universal=Array.from({length:64},(_,i)=>i).filter(x=>pc(x)>=3),uIndex=new Map(universal.map((x,i)=>[x,i]));
    const codeOf=masks=>masks.reduce((s,m)=>s|(1n<<BigInt(uIndex.get(m))),0n);
    const high=Array.from({length:64},(_,m)=>m).filter(m=>pc(m)>=3&&!violation(attach([m])));
    assert(same(high,record.high_masks)&&high.length===9,"complete high-mask domain");
    const atoms=atomNumbers.map((x,i)=>{
      const code=BigInt(x),masks=universal.filter((_m,j)=>Boolean(code&(1n<<BigInt(j))));
      assert(masks.every(m=>high.includes(m)),"atom uses allowed class");
      return {index:i,code,masks,population:masks.length,orbit:labels[i]};
    });
    assert(atoms.every(a=>a.population<=4&&a.orbit>=0&&a.orbit<19),"atom population/labels");
    const lookup=new Map(atoms.map(a=>[a.code.toString(),a.index]));
    const pairCases=[];
    for(const pair of choose(high,2)){
      const edgeViolation=violation(attach(pair,[[0,1]]));
      assert(edgeViolation!==null,"all high edges forbidden");
      pairCases.push({masks:pair,edge_forbidden_witness:edgeViolation,nonedge_allowed:!violation(attach(pair))});
    }
    const expectedFlags=[{size:0,masks:[],edge:0,rows:ROWS}];
    for(const m of high)expectedFlags.push({size:1,masks:[m],edge:0,rows:attach([m])});
    for(let a=0;a<64;a++)for(let b=a+1;b<64;b++)for(const edge of [0,1]){
      if(Math.min(pc(a),pc(b))+edge<3)continue;
      const rows=attach([a,b],edge?[[0,1]]:[]);
      if(!violation(rows))expectedFlags.push({size:2,masks:[a,b],edge,rows});
    }
    const flags=input.flags;
    assert(expectedFlags.length===127&&flags.length===127,"complete flag count");
    for(let i=0;i<flags.length;i++){
      const f=flags[i],e=expectedFlags[i];
      assert(f.size===e.size&&f.edge===e.edge&&same(f.masks,e.masks)&&same(f.rows,e.rows),"literal flag order "+i);
      assert(Number.isSafeInteger(f.type)&&f.type>=0&&f.type<48965,"flag catalogue type");
    }
    const tensor=input.tensor;
    assert(tensor.dtype==="int64"&&same(tensor.shape,[8128,48965]),"tensor dimensions");
    assert(tensor.indptr.length===8129&&tensor.indptr[0]===0&&tensor.indptr[8128]===10321,"tensor pointers");
    assert(tensor.data.length===10321&&tensor.indices.length===10321,"tensor nnz");
    for(let r=0;r<8128;r++){
      assert(Number.isSafeInteger(tensor.indptr[r])&&tensor.indptr[r]<=tensor.indptr[r+1],"CSR row");
      let previous=-1;
      for(let j=tensor.indptr[r];j<tensor.indptr[r+1];j++){
        assert(Number.isSafeInteger(tensor.data[j])&&tensor.data[j]>0,"positive tensor coefficient");
        assert(Number.isSafeInteger(tensor.indices[j])&&tensor.indices[j]>previous&&tensor.indices[j]<48965,"ordered tensor columns");
        previous=tensor.indices[j];
      }
    }
    const singles=new Map(),pairs=new Map();
    flags.forEach((f,i)=>{if(f.size===1)singles.set(f.masks[0],i);
      if(f.size===2&&f.masks.every(m=>pc(m)>=3)){
        const key=f.masks.join(",");if(!pairs.has(key))pairs.set(key,[]);pairs.get(key).push(i);
      }});
    function references(masks){
      if(!masks.length)return [0];
      if(masks.length===1)return [lower(singles.get(masks[0]),0)];
      const left=pairs.get(masks.slice(0,2).join(","))||[];
      if(masks.length===2)return left.map(i=>lower(i,0));
      if(masks.length===3)return left.map(i=>lower(i,singles.get(masks[2])));
      const right=pairs.get(masks.slice(2).join(","))||[];
      return left.flatMap(i=>right.map(j=>lower(i,j)));
    }
    function product(refs){
      const result=new Map();
      for(const r of refs)for(let j=tensor.indptr[r];j<tensor.indptr[r+1];j++){
        const col=tensor.indices[j];result.set(col,(result.get(col)||0n)+BigInt(tensor.data[j]));
      }
      return [...result].sort((a,b)=>a[0]-b[0]);
    }
    const supported=[],unsupported=[];let rawCount=0;
    for(let degree=0;degree<=4;degree++)for(const masks of choose(high,degree)){
      rawCount++;const code=codeOf(masks),rows=attach(masks),bad=violation(rows),refs=references(masks),form=product(refs);
      if(bad){
        assert(!lookup.has(code.toString())&&form.length===0,"unsupported monomial must be literally and coefficientwise zero");
        unsupported.push({masks,visible_violation:bad,cached_product_rows:refs});
      }else{
        assert(lookup.has(code.toString())&&form.length===1&&form[0][1]===1n,"unique labelled extension coefficient");
        const index=lookup.get(code.toString()),aut=isomorphisms(rows).count;
        assert(aut>=1,"literal unrooted automorphisms");
        if(masks.length<=2){
          const fi=masks.length===0?0:masks.length===1?singles.get(masks[0]):pairs.get(masks.join(","))[0];
          assert(form[0][0]===flags[fi].type,"direct flag type agrees with tensor type");
        }
        supported.push({atom_index:index,global_atom_code:Number(code),masks,root_orbit:labels[index],
          literal_graph_rows:rows,cached_product_rows:refs,catalogue_type:form[0][0],
          labelled_embedding_coefficient:1,unrooted_automorphisms:aut,
          induced_count_coefficient:aut});
      }
    }
    assert(rawCount===256&&supported.length===80&&unsupported.length===176,"complete degree-four coverage");
    supported.sort((a,b)=>a.atom_index-b.atom_index);
    assert(supported.every((r,i)=>r.atom_index===i),"every saved atom covered");
    const fiveWitnesses=choose(high,5).map(masks=>{
      const bad=violation(attach(masks));assert(bad!==null,"population-five exclusion");
      return {masks,visible_violation:bad};
    });
    assert(fiveWitnesses.length===126,"complete five-subset bound");
    let localTypeComparisons=0;
    for(let i=0;i<supported.length;i++)for(let j=0;j<i;j++){
      const a=supported[i],b=supported[j];
      if(a.masks.length!==b.masks.length)continue;
      const ca=a.literal_graph_rows.map(pc).sort((x,y)=>x-y),cb=b.literal_graph_rows.map(pc).sort((x,y)=>x-y);
      if(!same(ca,cb)){assert(a.catalogue_type!==b.catalogue_type,"same type degrees");continue;}
      const iso=isomorphisms(a.literal_graph_rows,b.literal_graph_rows);localTypeComparisons++;
      assert((iso.count>0)===(a.catalogue_type===b.catalogue_type),"local graph/type bijection");
      if(iso.count)assert(iso.count===a.unrooted_automorphisms&&iso.count===b.unrooted_automorphisms,"isomorphism/automorphism factors");
    }
    const group=record.complete_root_automorphisms;
    assert(group.length===6&&isomorphisms(ROWS).count===6,"complete actual root group");
    const groupKeys=new Set();
    for(const p of group){
      assert(same(p.slice().sort((a,b)=>a-b),[0,1,2,3,4,5]),"root permutation");
      assert(ROWS.every((row,i)=>ROWS.every((_r,j)=>((row>>j)&1)===((ROWS[p[i]]>>p[j])&1))),"root automorphism");
      groupKeys.add(p.join(","));
    }
    assert(groupKeys.size===6,"distinct root group");
    function move(mask,p){let out=0;for(let i=0;i<6;i++)if((mask>>i)&1)out|=1<<p[i];return out;}
    const orbitChecks=[];
    for(let o=0;o<19;o++){
      const representative=representatives[o],members=atoms.filter(a=>a.orbit===o).map(a=>a.index);
      assert(Number.isSafeInteger(representative)&&members[0]===representative&&members.length===sizes[o],"orbit members");
      const images=new Set(group.map(p=>lookup.get(codeOf(atoms[representative].masks.map(m=>move(m,p))).toString())));
      assert(same([...images].sort((a,b)=>a-b),members),"complete literal root orbit");
      assert(members.every(i=>supported[i].catalogue_type===supported[representative].catalogue_type&&supported[i].unrooted_automorphisms===supported[representative].unrooted_automorphisms),"literal moment constancy");
      orbitChecks.push({orbit:o,representative,members,size:members.length});
    }
    for(let o=0;o<19;o++){
      const code=atoms[representatives[o]].code;
      for(let r=0;r<19;r++){
        const count=atoms.filter(a=>a.orbit===r&&(a.code&code)===a.code).length;
        assert(C[r][o]===count,"exact complete quotient feature");
      }
      assert(C[o][o]===1,"unimodular diagonal");
    }
    const autControls=[
      {rows:Array(6).fill(0),expected:720},
      {rows:[32,0,0,0,0,1],expected:48},
      {rows:[62,1,1,1,1,1],expected:120},
      {rows:[2,5,10,20,40,16],expected:2},
      {rows:[34,5,10,20,40,17],expected:12},
      {rows:ROWS,expected:6},
      {rows:Array.from({length:9},(_,i)=>{let m=0;for(let j=0;j<9;j++)if(i!==j&&(Math.floor(i/3)===Math.floor(j/3)||i%3===j%3))m|=1<<j;return m;}),expected:72}
    ];
    for(const c of autControls)assert(isomorphisms(c.rows).count===c.expected,"automorphism control");
    assert(isomorphisms([34,5,10,20,40,17],[6,5,3,48,40,24]).count===0,"same-degree nonisomorphism control");
    const normalizationControls=[];
    for(let degree=0;degree<=4;degree++){
      const row=supported.find(r=>r.masks.length===degree),count=directPatternEmbeddingCount(row.literal_graph_rows,row.masks);
      assert(count===row.unrooted_automorphisms,"direct labelled-embedding normalization");
      normalizationControls.push({masks:row.masks,host_rows:row.literal_graph_rows,
        directly_counted_root_embeddings:count,unrooted_automorphisms:row.unrooted_automorphisms});
    }
    for(let active=0;active<80;active++){
      const moments=atoms.map(a=>(a.code&atoms[active].code)===a.code?1n:0n);
      const weights=inverseMoments(atoms,moments);
      assert(weights.every((w,i)=>w===(i===active?1n:0n)),"all deterministic distribution controls");
    }
    return {
      status:"POINT_INDEPENDENT_ROOT49_PREPARATION_PASS",
      source_git_blob:sourceGitBlob,bindings:BINDINGS,
      root_type:49,root_rows:ROWS,high_masks:high,
      high_mask_uniqueness_reason:"Distinct vertices with the same mask of size at least three would have at least three common neighbors.",
      coefficient_normalization:"The sole cached coefficient is 1 in labelled induced embeddings; its coefficient in unlabelled induced counts is Aut(F).",
      catalogue_identity_scope:"Catalogue IDs are read from frozen unique-term product rows. All local type/isomorphism consistency and automorphism factors are checked literally; the global catalogue is not regenerated.",
      all_pair_edges_forbidden:true,pair_cases:pairCases,
      complete_raw_monomials:256,complete_supported_monomials:80,complete_unsupported_monomials:176,
      supported,unsupported,maximum_population:4,five_subset_exclusion_witnesses:fiveWitnesses,
      complete_actual_root_automorphisms:group,orbits:orbitChecks,quotient_coefficients:C,
      local_graph_type_isomorphism_comparisons:localTypeComparisons,
      automorphism_controls:autControls.length,same_degree_nonisomorphism_controls:1,
      direct_normalization_controls:normalizationControls,deterministic_distribution_controls:80,
      point_loaded:false,optimizer_called:false
    };
  }
  function query(input,scope,point,prepared,sourceGitBlob=null){
    const fresh=prepare(input,scope,sourceGitBlob);
    assert(same(fresh,prepared),"cold preparation binding");
    assert(point.induced_counts.length===48965&&point.induced_counts.every(x=>Number.isSafeInteger(x)&&x>=0),"exact nonnegative point counts");
    assert(point.exact_count_and_held_cut_witness&&point.x521_zero&&point.required_zeros_hold,"point scope");
    const atoms=prepared.supported.map(r=>({code:BigInt(r.global_atom_code),population:r.masks.length}));
    const moments=prepared.supported.map(r=>BigInt(r.induced_count_coefficient)*BigInt(point.induced_counts[r.catalogue_type]));
    const weights=inverseMoments(atoms,moments);
    const orbitWeights=prepared.orbits.map(o=>o.members.reduce((s,i)=>s+weights[i],0n));
    for(const o of prepared.orbits)assert(o.members.every(i=>weights[i]===weights[o.representative]),"exact atom orbit invariance");
    for(let r=0;r<19;r++){
      const rhs=BigInt(prepared.orbits[r].size)*moments[prepared.orbits[r].representative];
      const actual=prepared.quotient_coefficients[r].reduce((s,c,o)=>s+BigInt(c)*orbitWeights[o],0n);
      assert(actual===rhs,"all original quotient equations");
    }
    const negatives=[];
    for(let a=0;a<80;a++)if(weights[a]<0n){
      const terms=[],form=new Map();
      for(let t=0;t<80;t++)if((atoms[t].code&atoms[a].code)===atoms[a].code){
        const sign=(atoms[t].population-atoms[a].population)&1?-1:1,row=prepared.supported[t];
        terms.push({atom_index:t,masks:row.masks,sign,catalogue_type:row.catalogue_type,induced_count_coefficient:sign*row.induced_count_coefficient,cached_product_rows:row.cached_product_rows});
        form.set(row.catalogue_type,(form.get(row.catalogue_type)||0n)+BigInt(sign)*BigInt(row.induced_count_coefficient));
      }
      for(let s=0;s<80;s++){
        const value=terms.reduce((z,t)=>z+(((atoms[t.atom_index].code&atoms[s].code)===atoms[t.atom_index].code)?BigInt(t.sign):0n),0n);
        assert(value===(s===a?1n:0n),"universal full-atom polynomial");
      }
      const sparse=[...form].filter(([_i,c])=>c!==0n).sort((a,b)=>a[0]-b[0]);
      const exact=sparse.reduce((s,[i,c])=>s+c*BigInt(point.induced_counts[i]),0n);
      assert(exact===weights[a]&&exact<0n,"strict direct induced separator");
      negatives.push({atom_index:a,masks:prepared.supported[a].masks,exact_value:exact,
        polynomial_terms:terms,direct_induced_count_form:sparse,
        full_structural_atoms_checked:80,global_catalogue_rebuilt:false});
    }
    const sum=weights.reduce((s,w)=>s+w,0n);assert(sum===moments[0],"root mass normalization");
    return wire({
      status:negatives.length?"EXACT_ROOT49_PACKING_MOMENT_SEPARATOR":"EXACT_ROOT49_COMPLETE_PACKING_MOMENT_DISTRIBUTION",
      source_git_blob:sourceGitBlob,bindings:BINDINGS,
      root_type:49,labelled_root_mass:moments[0],complete_atoms:80,complete_orbits:19,
      complete_supported_moments:80,structurally_zero_moments:176,
      atom_weights:prepared.supported.map((r,i)=>({atom_index:i,masks:r.masks,global_atom_code:r.global_atom_code,weight:weights[i],moment:moments[i],catalogue_type:r.catalogue_type,automorphisms:r.unrooted_automorphisms})),
      orbit_weights:orbitWeights,negative_atoms:negatives.length,negative_certificates:negatives,
      all_80_moment_equations_checked:true,all_19_quotient_equations_checked:true,
      optimizer_called:false,full_graph_existence_claimed:false,
      scope:"Exact finite presence-moment calculation for root49 using the frozen complete structural packing domain."
    });
  }
  return {bindings:BINDINGS,prepare,query,wire,isomorphisms};
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { makeRoot49RecoveryTools };
  if (require.main === module) {
    const fs = require("fs"), crypto = require("crypto");
    const api = makeRoot49RecoveryTools();
    function gitBlob(path) {
      const bytes=fs.readFileSync(path);
      return crypto.createHash("sha1").update("blob "+bytes.length+"\0").update(bytes).digest("hex");
    }
    const [mode,inputPath,scopePath,pointPath]=process.argv.slice(2);
    if (!["prepare","query"].includes(mode)||!inputPath||!scopePath) throw Error("Usage: node checker.js prepare|query input.json scope.json [point.json]");
    if(gitBlob(inputPath)!==api.bindings.extraction_git_blob||gitBlob(scopePath)!==api.bindings.scope_git_blob)throw Error("Input Git blob binding");
    const input=JSON.parse(fs.readFileSync(inputPath,"utf8")), scope=JSON.parse(fs.readFileSync(scopePath,"utf8"));
    const sourceGitBlob=gitBlob(__filename), prepared=api.prepare(input,scope,sourceGitBlob);
    let result=prepared;
    if(mode==="query") {
      if(!pointPath||gitBlob(pointPath)!==api.bindings.point_git_blob)throw Error("Point Git blob binding");
      const point=JSON.parse(fs.readFileSync(pointPath,"utf8"));
      result=api.query(input,scope,point,prepared,sourceGitBlob);
    }
    console.log(JSON.stringify(result,null,2));
  }
}
