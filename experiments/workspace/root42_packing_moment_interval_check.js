"use strict";

function makeRoot42IntervalTools(isomorphisms,root42Scope) {
  "use strict";
  const BINDINGS={
    input_git_blob:"ad89299823eef485ceeeea4824ce0eb9ebacbb3a",
    extraction_request_git_blob:"768bf542248d214b6e74412e35780233604d1986",
    scope_git_blob:"4bc0045ae1447160dbf667a1918e32a9f4e3c454",
    scope_source_git_blob:"2ab3477323b6a4dff2e66c688fea7826a7490630",
    known_preparation_git_blob:"537b722f2dd4f964c5fa053d5398e41c60b4ed9d",
    isomorphism_source_git_blob:"d547df71ef544fc7e36a8580bc9f7bdc311d6871",
    source_commit:"a20ec755c7364c4b7a6e40317e5a7a745224679d",
    arrays_sha256:"4af4af187681c33af2ce0d64fc1e7c3e7afb30e37eec181c741776883d602533",
    tensors_sha256:"84d69eb567b961f8cdce332f66b152a2cac803feb50a5a7b161d67479b31fb5c",
    point_git_blob:"c881dae3be05cf289fcc45a99d72c405ac863c46",
    point_sha256:"0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df"
  };
  function assert(x,m){if(!x)throw Error(m);}
  function same(a,b){return JSON.stringify(a)===JSON.stringify(b);}
  function pop(x){let c=0;while(x){c+=x&1;x>>>=1;}return c;}
  function wire(x){return JSON.parse(JSON.stringify(x,(_k,v)=>typeof v==="bigint"?v.toString():v));}
  function add(to,terms,factor=1n){for(const [t,c]of terms)to.set(t,(to.get(t)||0n)+factor*BigInt(c));}
  function form(map){return [...map].filter(([_t,c])=>c!==0n).sort((a,b)=>a[0]-b[0]).map(([t,c])=>[t,c.toString()]);}
  function rows(root,masks,edges=[]){
    const a=root.slice();
    for(let j=0;j<masks.length;j++){a.push(masks[j]);for(let i=0;i<6;i++)if(masks[j]&(1<<i))a[i]|=1<<(6+j);}
    for(const [i,j]of edges){a[6+i]|=1<<(6+j);a[6+j]|=1<<(6+i);}return a;
  }
  function valid(a){for(let i=0;i<a.length;i++)for(let j=i+1;j<a.length;j++)if(pop(a[i]&a[j])+((a[i]>>j)&1)>2)return false;return true;}
  function moved(mask,p){let x=0;for(let i=0;i<6;i++)if(mask&(1<<i))x|=1<<p[i];return x;}
  function relabel(a,p){const b=Array(a.length).fill(0);for(let i=0;i<a.length;i++)for(let j=0;j<a.length;j++)if((a[i]>>j)&1)b[p[i]]|=1<<p[j];return b;}
  function completions(root,T){
    const pairs=[];for(let i=0;i<T.length;i++)for(let j=i+1;j<T.length;j++)pairs.push([i,j]);
    const out=[];
    for(let bits=0;bits<(1<<pairs.length);bits++){
      const edges=pairs.filter((_e,i)=>(bits>>i)&1),a=rows(root,T,edges);
      if(valid(a))out.push({edges,rows:a});
    }
    return out;
  }
  function compareFractions(a,b){const d=a.n*b.d-b.n*a.d;return d<0n?-1:d>0n?1:0;}
  function gcd(a,b){a=a<0n?-a:a;b=b<0n?-b:b;while(b){const r=a%b;a=b;b=r;}return a;}
  function rational(n,d){
    assert(d>0n,"positive denominator");const g=gcd(n,d);return {n:n/g,d:d/g};
  }
  function ceilDivision(a,b){
    assert(b>0n,"positive divisor");
    return a>=0n?(a+b-1n)/b:a/b;
  }
  function interval(constants,slopes){
    let lower=null,upper=null;const zeroFailures=[];
    for(let i=0;i<constants.length;i++){
      const c=constants[i],d=BigInt(slopes[i]);
      if(d>0n){
        const q=rational(-c,d);
        if(lower===null||compareFractions(q,lower.value)>0)lower={atom:i,value:q};
      }else if(d<0n){
        const q=rational(c,-d);
        if(upper===null||compareFractions(q,upper.value)<0)upper={atom:i,value:q};
      }else if(c<0n)zeroFailures.push(i);
    }
    assert(lower!==null&&upper!==null,"finite two-sided interval");
    const candidate=2n*ceilDivision(lower.value.n,2n*lower.value.d);
    return {lower,upper,zeroFailures,
      real_feasible:zeroFailures.length===0&&compareFractions(lower.value,upper.value)<=0,
      least_even_candidate:candidate,
      even_feasible:zeroFailures.length===0&&compareFractions(lower.value,upper.value)<=0&&candidate*upper.value.d<=upper.value.n};
  }
  function prepare(input,scope,knownPreparation,sourceGitBlob){
    assert(input.root_count===1&&input.roots.length===1&&input.roots[0].root_type===42,"one root42 input");
    assert(input.source_commit===BINDINGS.source_commit&&input.extraction_request_git_blob===BINDINGS.extraction_request_git_blob,"public provenance");
    assert(!input.count_point_loaded&&!input.optimizer_called&&!input.mathematical_reconstruction_performed,"network-only extraction");
    assert(input.input_bindings["order10-high-mask-packing-other-roots-scope01-arrays.npz"].sha256===BINDINGS.arrays_sha256,"arrays hash");
    assert(input.input_bindings["prism-zero-order10-r6s2-blocks.pickle.gz"].sha256===BINDINGS.tensors_sha256,"tensor hash");
    const record=scope.roots.find(r=>r.root_type===42),root=record.root_rows;
    const scoped=root42Scope(record,knownPreparation,isomorphisms);
    const raw=input.roots[0],group=record.complete_root_automorphisms;
    assert(group.length===24&&isomorphisms(root).count===24,"complete S4 root group");
    assert(new Set(group.map(p=>p.join(","))).size===24,"distinct root permutations");
    for(const p of group){
      assert(same(p.slice().sort((a,b)=>a-b),[0,1,2,3,4,5]),"root permutation");
      assert(same(relabel(root,p),root),"root adjacency preserved");
    }
    function array(name,shape,dtype){
      const x=raw.scope_arrays["r42_"+name];
      assert(x&&same(x.shape,shape)&&x.dtype===dtype,"scope array "+name);return x.data;
    }
    const codeNumbers=array("atom_codes",[253],"uint64"),codes=codeNumbers.map(BigInt);
    const populations=array("populations",[253],"int8"),labels=array("labels",[253],"int32");
    const representatives=array("representatives",[24],"int32"),sizes=array("sizes",[24],"int32");
    const smallIds=array("small_atom_ids",[241],"int32"),rowOrbits=array("supported_row_orbits",[23],"int32");
    const C=array("quotient_coefficients",[23,24],"int64"),globalIds=array("global_atom_ids",[253],"int32");
    assert(globalIds.every((x,i)=>Number.isSafeInteger(x)&&x>=0&&(!i||globalIds[i-1]<x)),"source atom indices");
    assert(same(codes.map(String),scoped.direct_atom_list.map(a=>a.code)),"complete atom list");
    const atoms=scoped.direct_atom_list.map((a,i)=>({index:i,code:BigInt(a.code),masks:a.masks,orbit:labels[i]}));
    assert(same(populations,atoms.map(a=>a.masks.length)),"atom populations");
    assert(same(smallIds,atoms.filter(a=>a.masks.length<=4).map(a=>a.index)),"complete small moment list");
    assert(same(representatives,scoped.atom_orbits.map(o=>o.representative))&&same(sizes,scoped.atom_orbits.map(o=>o.members.length)),"orbit representatives");
    assert(same(rowOrbits,scoped.atom_orbits.map((o,i)=>o.population<=4?i:null).filter(x=>x!==null)),"all lower-degree orbit rows");
    for(let q=0;q<24;q++)assert(same(atoms.filter(a=>a.orbit===q).map(a=>a.index),scoped.atom_orbits[q].members),"all orbit labels");
    for(let r=0;r<23;r++)for(let q=0;q<24;q++){
      const expected=atoms.filter(a=>a.orbit===rowOrbits[r]&&(a.code&atoms[representatives[q]].code)===a.code).length;
      assert(C[r][q]===expected,"all quotient coefficients");
    }
    const high=scoped.high_masks,flags=[{size:0,masks:[],edge:0,rows:root}];
    for(const m of high)flags.push({size:1,masks:[m],edge:0,rows:rows(root,[m])});
    for(let a=0;a<64;a++)for(let b=a+1;b<64;b++)for(const edge of[0,1]){
      if(Math.min(pop(a),pop(b))+edge<3)continue;
      const graph=rows(root,[a,b],edge?[[0,1]]:[]);
      if(valid(graph))flags.push({size:2,masks:[a,b],edge,rows:graph});
    }
    assert(flags.length===174&&raw.flags.length===174,"full flag count");
    flags.forEach((f,i)=>{
      const actual=raw.flags[i];
      assert(f.size===actual.size&&f.edge===actual.edge&&same(f.masks,actual.masks)&&same(f.rows,actual.rows),"complete literal flag records");
      assert(Number.isSafeInteger(actual.type)&&actual.type>=0&&actual.type<48965,"catalogue flag ID");
      f.type=actual.type;
    });
    assert(flags[0].type===42,"root catalogue ID");
    const singles=new Map(),pairs=new Map();
    flags.forEach((f,i)=>{
      if(f.size===1)singles.set(f.masks[0],i);
      if(f.size===2&&f.masks.every(m=>pop(m)>=3)){
        const k=f.masks.join(",");if(!pairs.has(k))pairs.set(k,[]);pairs.get(k).push(i);
      }
    });
    const lower=(a,b)=>Math.max(a,b)*(Math.max(a,b)+1)/2+Math.min(a,b);
    function partitions(T){
      if(T.length===0)return [[[0,0]]];
      if(T.length===1)return [[[singles.get(T[0]),0]]];
      if(T.length===2)return [(pairs.get(T.join(","))||[]).map(i=>[i,0]),[[singles.get(T[0]),singles.get(T[1])]]];
      if(T.length===3)return [0,1,2].map(s=>(pairs.get(T.filter((_m,i)=>i!==s).join(","))||[]).map(i=>[i,singles.get(T[s])]));
      return [[0,1,2,3],[0,2,1,3],[0,3,1,2]].map(([a,b,c,d])=>(pairs.get([T[a],T[b]].join(","))||[]).flatMap(i=>(pairs.get([T[c],T[d]].join(","))||[]).map(j=>[i,j])));
    }
    const expectedRowIds=[...new Set(rowOrbits.flatMap(q=>partitions(atoms[representatives[q]].masks).flatMap(p=>p.map(([a,b])=>lower(a,b)))))].sort((a,b)=>a-b);
    assert(same(expectedRowIds,scoped.representative_tensor_row_indices),"complete representative product rows");
    assert(raw.tensor.dtype==="int64"&&same(raw.tensor.shape,[15225,48965])&&same(raw.tensor.rows.map(r=>r.row),expectedRowIds),"selected tensor structure");
    const pool=scoped.representative_literal_class_records,memo=new Map();
    function literalClass(a){
      const key=a.join(",");if(memo.has(key))return memo.get(key);
      const matches=pool.map((g,i)=>a.length===g.rows.length&&isomorphisms(a,g.rows).count?i:null).filter(x=>x!==null);
      assert(matches.length===1,"literal graph class coverage");memo.set(key,matches[0]);return matches[0];
    }
    for(const g of pool)assert(isomorphisms(g.rows).count===g.automorphisms,"independent literal automorphism count");
    const contexts=[];
    for(const item of raw.tensor.rows){
      let a=Math.floor((Math.sqrt(8*item.row+1)-1)/2);
      while((a+1)*(a+2)/2<=item.row)a++;while(a*(a+1)/2>item.row)a--;
      const b=item.row-a*(a+1)/2,fa=flags[a],fb=flags[b];
      const T=[...new Set([...fa.masks,...fb.masks])].sort((x,y)=>x-y);
      assert(T.length===fa.masks.length+fb.masks.length&&T.length<=4&&T.every(m=>pop(m)>=3),"disjoint high-mask factors");
      const expected=new Map();
      for(const completion of completions(root,T)){
        let fits=true;
        for(const f of[fa,fb])if(f.size===2){
          const i=T.indexOf(f.masks[0]),j=T.indexOf(f.masks[1]);
          const edge=completion.edges.some(([x,y])=>x===Math.min(i,j)&&y===Math.max(i,j));
          if(Number(edge)!==f.edge)fits=false;
        }
        if(fits){const id=literalClass(completion.rows);expected.set(id,(expected.get(id)||0)+1);}
      }
      assert(item.indices.length===item.data.length,"sparse row lengths");
      const actual=new Map();
      item.indices.forEach((type,i)=>{
        assert(Number.isSafeInteger(type)&&type>=0&&type<48965&&(!i||item.indices[i-1]<type),"sparse type order");
        assert(Number.isSafeInteger(item.data[i])&&item.data[i]>0,"positive exact coefficient");
        actual.set(type,item.data[i]);
      });
      contexts.push({row:item.row,flags:[a,b],expected,actual});
    }
    const expectedColumns=pool.map(()=>[]),actualColumns=new Map();
    for(const context of contexts){
      for(const [id,c]of context.expected)expectedColumns[id].push([context.row,c]);
      for(const [type,c]of context.actual){
        if(!actualColumns.has(type))actualColumns.set(type,[]);
        actualColumns.get(type).push([context.row,c]);
      }
    }
    assert(pool.length===31&&actualColumns.size===31,"complete literal/catalogue inventory");
    const classByFingerprint=new Map(),typeByFingerprint=new Map();
    expectedColumns.forEach((column,id)=>{const k=JSON.stringify(column);assert(column.length&&!classByFingerprint.has(k),"singleton literal fingerprint");classByFingerprint.set(k,id);});
    for(const [type,column]of actualColumns){const k=JSON.stringify(column);assert(!typeByFingerprint.has(k),"singleton catalogue fingerprint");typeByFingerprint.set(k,type);}
    assert([...classByFingerprint.keys()].every(k=>typeByFingerprint.has(k)),"full fingerprint bijection");
    const classTypes=pool.map((_g,id)=>typeByFingerprint.get(JSON.stringify(expectedColumns[id]))),typeAut=new Map();
    const oldClassTypes=new Map(knownPreparation.catalogue_fingerprint_groups.map(g=>[g.literal_classes[0],g.catalogue_types[0]]));
    pool.forEach((g,id)=>{
      const type=classTypes[id],order=g.rows.length,bounds={6:[38,100],7:[100,308],8:[308,1224],9:[1224,6535],10:[6535,48965]}[order];
      assert(type>=bounds[0]&&type<bounds[1],"catalogue order");
      if(g.known_literal_class!==null)assert(oldClassTypes.get(g.known_literal_class)===type,"known catalogue identity");
      typeAut.set(type,BigInt(g.automorphisms));
    });
    for(const f of flags)if(f.masks.every(m=>pop(m)>=3))assert(classTypes[literalClass(f.rows)]===f.type,"direct flag catalogue anchor");
    for(const context of contexts){
      const expected=[...context.expected].map(([id,c])=>[classTypes[id],c]).sort((a,b)=>a[0]-b[0]);
      assert(same(expected,[...context.actual]),"exact literal product coefficients");
    }
    const rowMap=new Map(contexts.map(c=>[c.row,c])),orbitForms=new Map(),orbitPartitions=new Map();
    for(const q of rowOrbits){
      const all=partitions(atoms[representatives[q]].masks);let reference=null;
      for(const partition of all){
        const f=new Map();for(const [a,b]of partition)add(f,rowMap.get(lower(a,b)).actual);
        const current=form(f);if(reference===null)reference=current;else assert(same(reference,current),"all representative partitions agree");
      }
      const induced=reference.map(([type,c])=>[type,(BigInt(c)*typeAut.get(type)).toString()]);
      orbitForms.set(q,induced);orbitPartitions.set(q,all.map(p=>p.map(([a,b])=>lower(a,b))));
    }
    const transports=[],allForms=Array(253).fill(null),completionTransportChecks=[];
    for(const atom of atoms){
      const rep=atoms[representatives[atom.orbit]],transport=group.findIndex(p=>same(rep.masks.map(m=>moved(m,p)).sort((a,b)=>a-b),atom.masks));
      assert(transport>=0,"explicit root transport");transports.push(transport);
      if(atom.masks.length>4)continue;
      allForms[atom.index]=orbitForms.get(atom.orbit);
      const p=group[transport],permutation=p.concat(rep.masks.map(m=>6+atom.masks.indexOf(moved(m,p))));
      const image=completions(root,rep.masks).map(c=>relabel(c.rows,permutation).join(",")).sort();
      const target=completions(root,atom.masks).map(c=>c.rows.join(",")).sort();
      assert(same(image,target),"complete induced-completion transport");
      completionTransportChecks.push([atom.index,image.length]);
    }
    const five=atoms.filter(a=>a.masks.length===5).map(a=>a.index);
    assert(five.length===12&&new Set(five.map(i=>atoms[i].orbit)).size===1,"single fifth-moment orbit");
    const affine=[],stabilizerOrders=[];let freeActionChecks=0;
    for(const atom of atoms){
      const stabilizer=group.map((p,i)=>same(atom.masks.map(m=>moved(m,p)).sort((a,b)=>a-b),atom.masks)?i:null).filter(i=>i!==null);
      assert(stabilizer.length*sizes[atom.orbit]===24,"orbit-stabilizer identity");
      if(atom.masks.length===5)assert(stabilizer.length===2,"fifth atom stabilizer");
      for(const p of group){
        const orbit=new Set(stabilizer.map(i=>group[i].map(j=>p[j]).join(",")));
        assert(orbit.size===stabilizer.length,"free action on ordered root embeddings");freeActionChecks++;
      }
      const constant=new Map();
      for(const t of smallIds)if((atom.code&atoms[t].code)===atom.code)add(constant,allForms[t],((atoms[t].masks.length-atom.masks.length)&1)?-1n:1n);
      const containing=five.filter(i=>(atom.code&atoms[i].code)===atom.code);
      const slope=((5-atom.masks.length)&1?-1:1)*containing.length;
      const frozen=form(constant),stab=BigInt(stabilizer.length);
      assert(frozen.every(([_t,c])=>BigInt(c)%stab===0n),"coefficientwise constant stabilizer divisibility");
      assert(2n*BigInt(slope)%stab===0n,"even fifth moment supplies every stabilizer congruence");
      affine.push({atom_index:atom.index,masks:atom.masks,population:atom.masks.length,root_orbit:atom.orbit,
        induced_constant_form:frozen,fifth_moment_slope:slope,five_superset_indices:containing,stabilizer_indices:stabilizer,stabilizer_order:stabilizer.length});
      stabilizerOrders.push(stabilizer.length);
    }
    for(const atom of atoms){
      const lhs=new Map();let slope=0;
      for(const a of atoms)if((atom.code&a.code)===atom.code){add(lhs,affine[a.index].induced_constant_form);slope+=affine[a.index].fifth_moment_slope;}
      assert(same(form(lhs),atom.masks.length<=4?allForms[atom.index]:[])&&slope===(atom.masks.length===5?1:0),"all symbolic zeta equations");
    }
    for(let q=0;q<24;q++){
      const rep=affine[representatives[q]];
      assert(scoped.atom_orbits[q].members.every(i=>same(affine[i].induced_constant_form,rep.induced_constant_form)&&affine[i].fifth_moment_slope===rep.fifth_moment_slope),"affine orbit invariance");
    }
    for(let r=0;r<23;r++){
      const lhs=new Map();let slope=0;
      for(let q=0;q<24;q++){
        const multiplier=C[r][q]*sizes[q],a=affine[representatives[q]];
        add(lhs,a.induced_constant_form,BigInt(multiplier));slope+=multiplier*a.fifth_moment_slope;
      }
      const expected=new Map();add(expected,orbitForms.get(rowOrbits[r]),BigInt(sizes[rowOrbits[r]]));
      assert(same(form(lhs),form(expected))&&slope===0,"all symbolic quotient equations");
    }
    const controls=[];
    for(let test=0;test<3;test++){
      const w=atoms.map(a=>test===0?BigInt(stabilizerOrders[a.index]*(1+a.orbit%3)):test===1?BigInt(a.masks.length===5?2:0):BigInt(a.index===0?24:0));
      const m=atoms.map(t=>atoms.reduce((s,a)=>s+((t.code&a.code)===t.code?w[a.index]:0n),0n));
      const constants=atoms.map(a=>smallIds.reduce((s,t)=>s+((a.code&atoms[t].code)===a.code?((atoms[t].masks.length-a.masks.length)&1?-1n:1n)*m[t]:0n),0n));
      const slopes=affine.map(a=>a.fifth_moment_slope),u=w[five[0]],computed=constants.map((c,i)=>c+BigInt(slopes[i])*u);
      assert(computed.every((value,i)=>value===w[i]),"synthetic full distribution");
      const bounds=interval(constants,slopes);
      assert(bounds.real_feasible&&bounds.even_feasible&&u%2n===0n&&u*bounds.lower.value.d>=bounds.lower.value.n&&u*bounds.upper.value.d<=bounds.upper.value.n,"synthetic even interval");
      controls.push(wire({test,total_mass:m[0],fifth_moment:u,least_even_candidate:bounds.least_even_candidate,lower:bounds.lower,upper:bounds.upper}));
    }
    return {
      status:"POINT_INDEPENDENT_ROOT42_INTERVAL_PREPARATION_PASS",source_git_blob:sourceGitBlob||null,bindings:BINDINGS,
      root_type:42,root_rows:root,high_masks:high,actual_root_automorphisms:group,
      atoms:atoms.map(a=>({atom_index:a.index,code:a.code.toString(),masks:a.masks,orbit:a.orbit,transport_from_representative:transports[a.index]})),
      atom_orbits:scoped.atom_orbits,small_atom_ids:smallIds,supported_row_orbits:rowOrbits,
      quotient_coefficients:C,representatives,sizes,
      literal_classes:pool.map((g,id)=>({...g,catalogue_type:classTypes[id],column_fingerprint:expectedColumns[id]})),
      product_rows:contexts.map(c=>({row:c.row,flags:c.flags,literal_coefficients:[...c.expected].sort((a,b)=>a[0]-b[0]),catalogue_coefficients:[...c.actual]})),
      orbit_moment_forms:rowOrbits.map(q=>({orbit:q,representative:representatives[q],induced_count_form:orbitForms.get(q),product_partitions:orbitPartitions.get(q)})),
      all_small_moment_forms:smallIds.map(i=>({atom_index:i,induced_count_form:allForms[i]})),
      affine_atoms:affine,fifth_atom_indices:five,fifth_moment_integer_modulus:2,
      scalar_interpretation:"u is the common labelled-root moment and exact atom mass of each of the 12 size-five atoms.",
      divisibility_proof:"The root stabilizer of an exact high-set acts freely by precomposition on its injective ordered root embeddings. Every atom mass is divisible by its stabilizer order. The size-five stabilizer has order two. All constant-form coefficients and twice every slope satisfy the other stabilizer congruences.",
      summary:{root_automorphisms:24,all_presence_sets_checked:1024,atoms:253,lower_moments:241,moment_orbits:23,atom_orbits:24,
        fifth_atoms:12,fifth_orbits:1,literal_types:31,product_rows:67,product_nonzeros:contexts.reduce((s,c)=>s+c.actual.size,0),
        induced_completion_transports:completionTransportChecks.length,literal_completions_transported:completionTransportChecks.reduce((s,x)=>s+x[1],0),
        symbolic_zeta_equations:253,symbolic_quotient_equations:23,free_action_checks:freeActionChecks,synthetic_distribution_controls:controls.length},
      completion_transport_checks:completionTransportChecks,controls,
      count_point_loaded:false,optimizer_called:false
    };
  }
  function query(input,scope,knownPreparation,point,prepared,sourceGitBlob){
    const cold=prepare(input,scope,knownPreparation,sourceGitBlob);
    assert(same(cold,prepared),"cold exact interval preparation");
    assert(point.induced_counts.length===48965&&point.induced_counts.every(x=>Number.isSafeInteger(x)&&x>=0),"exact count point");
    assert(point.exact_count_and_held_cut_witness&&point.x521_zero&&point.required_zeros_hold,"point scope");
    const counts=point.induced_counts.map(BigInt),evaluate=f=>f.reduce((s,[t,c])=>s+BigInt(c)*counts[t],0n);
    const constants=prepared.affine_atoms.map(a=>evaluate(a.induced_constant_form)),slopes=prepared.affine_atoms.map(a=>a.fifth_moment_slope);
    const bounds=interval(constants,slopes),certificates=[];
    if(bounds.zeroFailures.length){
      for(const i of bounds.zeroFailures)certificates.push({kind:"negative_zero_slope_atom",atom:i,value:constants[i],induced_count_form:prepared.affine_atoms[i].induced_constant_form});
    }else if(!bounds.real_feasible){
      const i=bounds.lower.atom,j=bounds.upper.atom,out=new Map();
      add(out,prepared.affine_atoms[i].induced_constant_form,-BigInt(slopes[j]));
      add(out,prepared.affine_atoms[j].induced_constant_form,BigInt(slopes[i]));
      const f=form(out),value=evaluate(f);assert(value<0n,"exact scalar-eliminated separator");
      certificates.push({kind:"incompatible_real_interval",lower_atom:i,upper_atom:j,
        nonnegative_atom_coefficients:[-BigInt(slopes[j]),BigInt(slopes[i])],value,induced_count_form:f});
    }
    const base={
      source_git_blob:sourceGitBlob||null,bindings:BINDINGS,interval:bounds,
      integer_modulus:2,atom_constants:constants,atom_slopes:slopes,
      direct_induced_certificates:certificates,optimizer_called:false,full_graph_existence_resolved:false
    };
    if(!bounds.even_feasible){
      return wire({...base,status:bounds.real_feasible?"EXACT_ROOT42_STABILIZER_CONGRUENCE_OBSTRUCTION":"EXACT_ROOT42_MOMENT_OBSTRUCTION",
        arithmetic_scope:"Only this immutable count point and the complete root42 local moment model are tested.",
        optimizer_eligible:false});
    }
    const u=bounds.least_even_candidate,weights=constants.map((c,i)=>c+BigInt(slopes[i])*u);
    assert(u>=0n&&u%2n===0n&&weights.every(w=>w>=0n),"nonnegative even-parameter weights");
    weights.forEach((w,i)=>assert(w%BigInt(prepared.affine_atoms[i].stabilizer_order)===0n,"all integer stabilizer constraints"));
    const codes=prepared.atoms.map(a=>BigInt(a.code)),momentMap=new Map(prepared.all_small_moment_forms.map(m=>[m.atom_index,evaluate(m.induced_count_form)]));
    for(let i=0;i<253;i++){
      let value=0n;for(let j=0;j<253;j++)if((codes[i]&codes[j])===codes[i])value+=weights[j];
      assert(value===(momentMap.has(i)?momentMap.get(i):u),"all individual moment equations");
    }
    const orbitWeights=prepared.atom_orbits.map(o=>o.members.reduce((s,i)=>s+weights[i],0n));
    for(let r=0;r<23;r++){
      const q=prepared.supported_row_orbits[r],lhs=prepared.quotient_coefficients[r].reduce((s,c,j)=>s+BigInt(c)*orbitWeights[j],0n);
      assert(lhs===BigInt(prepared.sizes[q])*momentMap.get(prepared.representatives[q]),"all quotient equations");
    }
    const g=24n*counts[42];
    assert(weights.reduce((s,w)=>s+w,0n)===g&&momentMap.get(0)===g,"labelled root normalization");
    return wire({...base,status:"EXACT_ROOT42_INTEGER_ATOM_DISTRIBUTION",
      fifth_moment:u,labelled_root_mass:g,atom_weights:weights,orbit_weights:orbitWeights,
      positive_atoms:weights.filter(w=>w>0n).length,zero_atoms:weights.filter(w=>w===0n).length,
      all_individual_equations_checked:253,all_quotient_equations_checked:23,all_stabilizer_divisibilities_checked:253});
  }
  return {bindings:BINDINGS,prepare,query};
}

if(typeof module!=="undefined"&&module.exports) {
  module.exports={makeRoot42IntervalTools};
  if(require.main===module) {
    const fs=require("fs"),crypto=require("crypto"),path=require("path");
    function blob(p){const b=fs.readFileSync(p);return crypto.createHash("sha1").update("blob "+b.length+"\0").update(b).digest("hex");}
    const isoPath=path.join(__dirname,"root49_packing_moment_recovery_check.js");
    const scopeSourcePath=path.join(__dirname,"root42_packing_moment_scope.js");
    if(blob(isoPath)!=="d547df71ef544fc7e36a8580bc9f7bdc311d6871")throw Error("Frozen isomorphism dependency");
    if(blob(scopeSourcePath)!=="2ab3477323b6a4dff2e66c688fea7826a7490630")throw Error("Frozen scope dependency");
    const iso=require(isoPath).makeRoot49RecoveryTools().isomorphisms;
    const scoped=require(scopeSourcePath).root42Scope;
    const api=makeRoot42IntervalTools(iso,scoped);
    const [mode,inputPath,scopePath,knownPath,pointPath]=process.argv.slice(2);
    if(!["prepare","query"].includes(mode)||!inputPath||!scopePath||!knownPath)throw Error("Usage: node check.js prepare|query inputs.json scope.json known-small-preparation.json [point.json]");
    if(blob(inputPath)!==api.bindings.input_git_blob||blob(scopePath)!==api.bindings.scope_git_blob||blob(knownPath)!==api.bindings.known_preparation_git_blob)throw Error("Frozen input binding");
    const read=p=>JSON.parse(fs.readFileSync(p,"utf8")),input=read(inputPath),scope=read(scopePath),known=read(knownPath),sourceBlob=blob(__filename);
    const prepared=api.prepare(input,scope,known,sourceBlob);
    let result=prepared;
    if(mode==="query"){
      if(!pointPath||blob(pointPath)!==api.bindings.point_git_blob)throw Error("Immutable point binding");
      result=api.query(input,scope,known,read(pointPath),prepared,sourceBlob);
    }
    console.log(JSON.stringify(result,null,2));
  }
}
