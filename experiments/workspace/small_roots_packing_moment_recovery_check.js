"use strict";

/* Exact remaining32 population-at-most-four root models.
   Preparation retains every literal high-edge completion and uses full
   product-column fingerprints. Count evaluation is a separate BigInt call. */

function makeSmallRootMomentTools(isomorphisms) {
  "use strict";
  const BINDINGS={
    commit:"a20ec755c7364c4b7a6e40317e5a7a745224679d",
    dependency_git_blob:"d547df71ef544fc7e36a8580bc9f7bdc311d6871",
    input_git_blob:"a2188e546dfa72363ef464c11bf89caeec547254",
    extraction_request_git_blob:"a00bcf9304019e39ed3a07e576d6f07d22658f64",
    scope_git_blob:"4bc0045ae1447160dbf667a1918e32a9f4e3c454",
    arrays_sha256:"4af4af187681c33af2ce0d64fc1e7c3e7afb30e37eec181c741776883d602533",
    tensors_sha256:"84d69eb567b961f8cdce332f66b152a2cac803feb50a5a7b161d67479b31fb5c",
    point_git_blob:"c881dae3be05cf289fcc45a99d72c405ac863c46",
    point_sha256:"0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df"
  };
  function assert(x,m){if(!x)throw Error(m);}
  function same(a,b){return JSON.stringify(a)===JSON.stringify(b);}
  function pc(x){let n=0;for(;x;x&=x-1)n++;return n;}
  function choose(a,k){const out=[];function rec(at,b){if(b.length===k){out.push(b.slice());return;}for(let i=at;i<=a.length-k+b.length;i++){b.push(a[i]);rec(i+1,b);b.pop();}}rec(0,[]);return out;}
  const universal=Array.from({length:64},(_,m)=>m).filter(m=>pc(m)>=3);
  const ui=new Map(universal.map((m,i)=>[m,i]));
  function codeOf(masks){return masks.reduce((s,m)=>s|(1n<<BigInt(ui.get(m))),0n);}
  function attach(root,masks,edges=[]){
    const rows=root.slice();masks.forEach((m,j)=>{rows.push(m);for(let i=0;i<6;i++)if((m>>i)&1)rows[i]|=1<<(6+j);});
    for(const [a,b]of edges){rows[6+a]|=1<<(6+b);rows[6+b]|=1<<(6+a);}return rows;
  }
  function violation(rows){for(let i=0;i<rows.length;i++)for(let j=i+1;j<rows.length;j++){const a=(rows[i]>>j)&1,c=pc(rows[i]&rows[j]);if(a+c>2)return [i,j,a,c];}return null;}
  function lower(a,b){if(a<b)[a,b]=[b,a];return a*(a+1)/2+b;}
  function counterKey(map){return JSON.stringify([...map].filter(([_k,v])=>v).sort((a,b)=>a[0]-b[0]));}
  function addCounter(target,source){for(const [i,c]of source)target.set(i,(target.get(i)||0)+c);}
  function wire(x){return JSON.parse(JSON.stringify(x,(_k,v)=>typeof v==="bigint"?v.toString():v));}
  function invert(codes,populations,moments){
    const order=codes.map((_,i)=>i).sort((a,b)=>populations[b]-populations[a]||a-b);
    const weights=Array(codes.length).fill(0n);
    for(const i of order){let value=moments[i];for(const j of order)if(populations[j]>populations[i]&&(codes[i]&codes[j])===codes[i])value-=weights[j];weights[i]=value;}
    for(let i=0;i<codes.length;i++){
      let sum=0n,mobius=0n;
      for(let j=0;j<codes.length;j++)if((codes[i]&codes[j])===codes[i]){
        sum+=weights[j];mobius+=((populations[j]-populations[i])&1?-1n:1n)*moments[j];
      }
      assert(sum===moments[i]&&mobius===weights[i],"independent moment/Mobius replay");
    }
    return weights;
  }
  function embeddingCount(root,host,masks){
    const image=Array(6).fill(-1);let used=0,count=0;
    function rec(at){
      if(at===6){
        const seen=new Set();for(let x=0;x<host.length;x++)if(!((used>>x)&1)){
          let mask=0;for(let i=0;i<6;i++)if((host[x]>>image[i])&1)mask|=1<<i;
          if(pc(mask)>=3){assert(!seen.has(mask),"literal high-class uniqueness");seen.add(mask);}
        }
        if(masks.every(m=>seen.has(m)))count++;return;
      }
      for(let x=0;x<host.length;x++)if(!((used>>x)&1)){
        let ok=true;for(let i=0;i<at;i++)if(((root[at]>>i)&1)!==((host[x]>>image[i])&1)){ok=false;break;}
        if(ok){image[at]=x;used|=1<<x;rec(at+1);used^=1<<x;image[at]=-1;}
      }
    }
    rec(0);return count;
  }
  function prepare(input,scope,sourceGitBlob=null){
    assert(input.source_commit===BINDINGS.commit&&input.extraction_request_git_blob===BINDINGS.extraction_request_git_blob,"input provenance");
    assert(!input.count_point_loaded&&!input.optimizer_called&&!input.mathematical_reconstruction_performed,"extraction scope");
    assert(input.input_bindings["order10-high-mask-packing-other-roots-scope01-arrays.npz"].sha256===BINDINGS.arrays_sha256,"array hash");
    assert(input.input_bindings["prism-zero-order10-r6s2-blocks.pickle.gz"].sha256===BINDINGS.tensors_sha256,"tensor hash");
    const selected=scope.roots.filter(r=>r.atom_orbits===r.supported_monomial_orbits&&r.root_type!==49);
    assert(scope.complete&&selected.length===32&&input.root_count===32,"complete selected-root scope");
    assert(same(input.roots.map(r=>r.root_type),selected.map(r=>r.root_type)),"exact root order");
    const pool=[],buckets=new Map(),literalMemo=new Map();let isomorphismComparisons=0;
    function poolClass(rows){
      const literal=rows.join(",");if(literalMemo.has(literal))return literalMemo.get(literal);
      const degrees=rows.map(pc);
      const vertexKeys=rows.map((row,i)=>JSON.stringify([degrees[i],rows.map((_r,j)=>j).filter(j=>(row>>j)&1).map(j=>degrees[j]).sort((a,b)=>a-b)]));
      const key=rows.length+"|"+vertexKeys.sort().join("|");
      if(!buckets.has(key))buckets.set(key,[]);
      for(const id of buckets.get(key)){
        isomorphismComparisons++;const iso=isomorphisms(rows,pool[id].rows);
        if(iso.count){assert(iso.count===pool[id].automorphisms,"literal iso factor");literalMemo.set(literal,id);return id;}
      }
      const automorphisms=isomorphisms(rows).count;assert(automorphisms>0,"literal automorphism count");
      const id=pool.length;pool.push({literal_class:id,rows:rows.slice(),automorphisms});
      buckets.get(key).push(id);literalMemo.set(literal,id);return id;
    }
    const contexts=[],contextLookup=new Map(),roots=[],anchors=new Map();
    let totalRaw=0,totalSupported=0,totalCompletions=0,totalFive=0;
    for(let ri=0;ri<selected.length;ri++){
      const saved=selected[ri],received=input.roots[ri],root=saved.root_rows,n=saved.visible_atoms,o=saved.atom_orbits;
      function arr(name,shape,dtype){const item=received.scope_arrays["r"+saved.root_type+"_"+name];assert(item&&same(item.shape,shape)&&item.dtype===dtype,"array "+saved.root_type+" "+name);return item.data;}
      const atomNumbers=arr("atom_codes",[n],"uint64"),labels=arr("labels",[n],"int32");
      const representatives=arr("representatives",[o],"int32"),sizes=arr("sizes",[o],"int32"),C=arr("quotient_coefficients",[o,o],"int64");
      assert(same(arr("small_atom_ids",[n],"int32"),Array.from({length:n},(_,i)=>i)),"all atoms small");
      assert(same(arr("supported_row_orbits",[o],"int32"),Array.from({length:o},(_,i)=>i)),"all orbit rows present");
      assert(atomNumbers[0]===0&&atomNumbers.every((x,i)=>Number.isSafeInteger(x)&&x>=0&&(!i||atomNumbers[i-1]<x)),"ordered safe atom codes");
      const codes=atomNumbers.map(BigInt),lookup=new Map(codes.map((x,i)=>[x.toString(),i]));
      const high=universal.filter(m=>!violation(attach(root,[m])));
      assert(same(high,saved.high_masks),"complete high-mask domain");
      const atoms=codes.map((code,i)=>({index:i,code,masks:universal.filter((_m,j)=>Boolean(code&(1n<<BigInt(j)))),orbit:labels[i]}));
      assert(atoms.every(a=>a.masks.length<=4&&a.masks.every(m=>high.includes(m))),"atom mask domain");
      const flags=[{size:0,masks:[],edge:0,rows:root}];
      for(const m of high)flags.push({size:1,masks:[m],edge:0,rows:attach(root,[m])});
      for(let a=0;a<64;a++)for(let b=a+1;b<64;b++)for(const edge of[0,1]){
        if(Math.min(pc(a),pc(b))+edge<3)continue;
        const rows=attach(root,[a,b],edge?[[0,1]]:[]);
        if(!violation(rows))flags.push({size:2,masks:[a,b],edge,rows});
      }
      assert(received.flags.length===flags.length,"complete flag count");
      flags.forEach((f,i)=>{const actual=received.flags[i];assert(actual.size===f.size&&actual.edge===f.edge&&same(actual.masks,f.masks)&&same(actual.rows,f.rows),"complete literal flag ordering");assert(Number.isSafeInteger(actual.type)&&actual.type>=0&&actual.type<48965,"flag type");f.type=actual.type;});
      assert(flags[0].type===saved.root_type,"root catalogue identity");
      const singles=new Map(),pairs=new Map();flags.forEach((f,i)=>{if(f.size===1)singles.set(f.masks[0],i);if(f.size===2&&f.masks.every(m=>pc(m)>=3)){const key=f.masks.join(",");if(!pairs.has(key))pairs.set(key,[]);pairs.get(key).push(i);}});
      const tensor=received.tensor;
      assert(tensor.dtype==="int64"&&same(tensor.shape,[flags.length*(flags.length+1)/2,48965]),"tensor shape");
      const rowData=new Map();
      for(const item of tensor.rows){
        assert(Number.isSafeInteger(item.row)&&item.row>=0&&item.row<tensor.shape[0]&&!rowData.has(item.row),"unique selected row");
        assert(item.indices.length===item.data.length,"sparse row lengths");
        const counter=new Map();item.indices.forEach((index,j)=>{assert(Number.isSafeInteger(index)&&index>=0&&index<48965&&(!j||item.indices[j-1]<index),"sparse type order");assert(Number.isSafeInteger(item.data[j])&&item.data[j]>0,"positive sparse coefficient");counter.set(index,item.data[j]);});rowData.set(item.row,counter);
      }
      const monomials=Array(n).fill(null),unsupported=[];let raw=0,completionCount=0;
      for(let degree=0;degree<=4;degree++)for(const T of choose(high,degree)){
        raw++;const code=codeOf(T),bad=violation(attach(root,T));
        if(bad){assert(!lookup.has(code.toString()),"unsupported atom omitted");unsupported.push([Number(code),...bad]);continue;}
        assert(lookup.has(code.toString()),"every literal supported atom retained");
        const atom=lookup.get(code.toString()),eligible=[];
        for(let i=0;i<T.length;i++)for(let j=i+1;j<T.length;j++)if(!violation(attach(root,[T[i],T[j]],[[0,1]])))eligible.push([i,j]);
        const completions=[];let rejected=0;
        for(let edgeCode=0;edgeCode<(1<<eligible.length);edgeCode++){
          const edges=eligible.filter((_e,i)=>(edgeCode>>i)&1),rows=attach(root,T,edges);
          if(violation(rows)){rejected++;continue;}
          const cls=poolClass(rows);completions.push({edge_code:edgeCode,edges,literal_class:cls});
          if(T.length<=2){
            const fi=T.length===0?0:T.length===1?singles.get(T[0]):(pairs.get(T.join(","))||[]).find(i=>flags[i].edge===(edges.length?1:0));
            assert(fi!==undefined,"direct flag anchor");
            if(anchors.has(cls))assert(anchors.get(cls)===flags[fi].type,"consistent literal flag anchors");else anchors.set(cls,flags[fi].type);
          }
        }
        assert(completions.length>0,"empty induced completion");completionCount+=completions.length;
        const partitions=[];
        if(T.length===0)partitions.push([[0,0]]);
        if(T.length===1)partitions.push([[singles.get(T[0]),0]]);
        if(T.length===2){partitions.push((pairs.get(T.join(","))||[]).map(i=>[i,0]));partitions.push([[singles.get(T[0]),singles.get(T[1])]]);}
        if(T.length===3)for(let s=0;s<3;s++)partitions.push((pairs.get(T.filter((_x,i)=>i!==s).join(","))||[]).map(i=>[i,singles.get(T[s])]));
        if(T.length===4)for(const [a,b,c,d]of[[0,1,2,3],[0,2,1,3],[0,3,1,2]])partitions.push((pairs.get([T[a],T[b]].join(","))||[]).flatMap(i=>(pairs.get([T[c],T[d]].join(","))||[]).map(j=>[i,j])));
        const partitionContexts=[];
        const fullExpected=new Map();for(const c of completions)fullExpected.set(c.literal_class,(fullExpected.get(c.literal_class)||0)+1);
        for(const recipes of partitions){
          const partitionExpected=new Map(),ids=[];
          for(const [a,b]of recipes){
            const row=lower(a,b);assert(rowData.has(row),"requested supported product row present");
            const expected=new Map();
            for(const completion of completions){
              let good=true;
              for(const f of [flags[a],flags[b]])if(f.size===2){
                const i=T.indexOf(f.masks[0]),j=T.indexOf(f.masks[1]);
                const present=completion.edges.some(e=>e[0]===Math.min(i,j)&&e[1]===Math.max(i,j));
                if(Number(present)!==f.edge)good=false;
              }
              if(good)expected.set(completion.literal_class,(expected.get(completion.literal_class)||0)+1);
            }
            addCounter(partitionExpected,expected);
            const key=saved.root_type+":"+row;let id=contextLookup.get(key);
            if(id===undefined){id=contexts.length;contextLookup.set(key,id);contexts.push({context:id,root_type:saved.root_type,tensor_row:row,flags:[a,b],expected,actual:rowData.get(row)});}
            else assert(counterKey(contexts[id].expected)===counterKey(expected),"repeated row literal identity");
            ids.push(id);
          }
          assert(counterKey(partitionExpected)===counterKey(fullExpected),"complete disjoint-label product expansion");
          partitionContexts.push(ids);
        }
        monomials[atom]={atom_index:atom,global_atom_code:Number(code),masks:T,root_orbit:labels[atom],eligible_high_edges:eligible,
          completions,rejected_internal_edge_assignments:rejected,product_partitions:partitionContexts};
      }
      assert(raw===saved.raw_monomials&&monomials.every(Boolean)&&monomials.length===saved.supported_monomials,"complete monomial coverage");
      assert([...rowData.keys()].every(r=>contextLookup.has(saved.root_type+":"+r)),"no unused extracted row");
      let fiveChecks=0;for(const T of choose(high,5)){assert(violation(attach(root,T))!==null,"literal five-class exclusion");fiveChecks++;}
      const group=saved.complete_root_automorphisms;assert(group.length===saved.automorphism_order&&isomorphisms(root).count===group.length,"complete actual root group");
      assert(new Set(group.map(p=>p.join(","))).size===group.length,"distinct group maps");
      for(const p of group){assert(same(p.slice().sort((a,b)=>a-b),[0,1,2,3,4,5]),"root permutation");assert(root.every((row,i)=>root.every((_r,j)=>((row>>j)&1)===((root[p[i]]>>p[j])&1))),"root automorphism");}
      function moved(mask,p){let x=0;for(let i=0;i<6;i++)if((mask>>i)&1)x|=1<<p[i];return x;}
      const orbits=[];
      for(let q=0;q<o;q++){
        const members=atoms.filter(a=>a.orbit===q).map(a=>a.index),rep=representatives[q];
        assert(members[0]===rep&&members.length===sizes[q],"orbit ledger");
        const images=new Set(group.map(p=>lookup.get(codeOf(atoms[rep].masks.map(m=>moved(m,p))).toString())));
        assert(same([...images].sort((a,b)=>a-b),members),"literal orbit coverage");
        orbits.push({orbit:q,representative:rep,members,size:members.length});
      }
      assert(orbits.reduce((s,q)=>s+q.members.length,0)===n,"all atom labels covered");
      for(let q=0;q<o;q++)for(let r=0;r<o;r++){
        const expected=atoms.filter(a=>a.orbit===r&&(a.code&atoms[representatives[q]].code)===a.code).length;
        assert(C[r][q]===expected,"complete exact quotient coefficient");
      }
      const populations=atoms.map(a=>a.masks.length);
      for(let control=0;control<2;control++){
        const w=atoms.map((_a,i)=>control===0?BigInt(1+i%5):BigInt(i===n-1));
        const m=atoms.map(a=>atoms.reduce((s,b,j)=>s+((a.code&b.code)===a.code?w[j]:0n),0n));
        assert(invert(codes,populations,m).every((x,i)=>x===w[i]),"synthetic exact distribution");
      }
      roots.push({root_type:saved.root_type,root_rows:root,high_masks:high,flag_count:flags.length,maximum_population:4,
        raw_monomials:raw,supported_monomials:n,unsupported_zero_witnesses:unsupported,
        five_class_subsets_checked:fiveChecks,monomials,orbits,quotient_coefficients:C,
        actual_root_automorphisms:group,literal_completions:completionCount});
      totalRaw+=raw;totalSupported+=n;totalCompletions+=completionCount;totalFive+=fiveChecks;
    }
    assert(totalRaw===4975&&totalSupported===1035&&totalCompletions===1195&&contexts.length===2450,"complete extraction-plan totals");
    const expectedColumns=pool.map(()=>new Map()),actualColumns=new Map();
    for(const ctx of contexts){
      for(const [g,c]of ctx.expected)expectedColumns[g].set(ctx.context,c);
      for(const [type,c]of ctx.actual){if(!actualColumns.has(type))actualColumns.set(type,new Map());actualColumns.get(type).set(ctx.context,c);}
    }
    const expectedGroups=new Map(),actualGroups=new Map();
    for(let g=0;g<pool.length;g++){assert(expectedColumns[g].size>0,"every literal class appears");const key=counterKey(expectedColumns[g]);if(!expectedGroups.has(key))expectedGroups.set(key,[]);expectedGroups.get(key).push(g);}
    for(const [type,col]of actualColumns){const key=counterKey(col);if(!actualGroups.has(key))actualGroups.set(key,[]);actualGroups.get(key).push(type);}
    assert(expectedGroups.size===actualGroups.size&&[...expectedGroups.keys()].every(k=>actualGroups.has(k)),"complete fingerprint blocks");
    const groups=[],classGroup=Array(pool.length),typeAut=new Map();
    for(const [signature,literalClasses]of expectedGroups){
      const types=actualGroups.get(signature).sort((a,b)=>a-b),aut=pool[literalClasses[0]].automorphisms;
      assert(literalClasses.length===types.length,"fingerprint-block bijection cardinality");
      assert(literalClasses.every(g=>pool[g].automorphisms===aut),"ambiguous types require common independently counted Aut");
      const order=pool[literalClasses[0]].rows.length,bounds={6:[38,100],7:[100,308],8:[308,1224],9:[1224,6535],10:[6535,48965]}[order];
      assert(literalClasses.every(g=>pool[g].rows.length===order)&&types.every(t=>t>=bounds[0]&&t<bounds[1]),"catalogue graph order");
      for(const g of literalClasses)if(anchors.has(g))assert(types.includes(anchors.get(g)),"known literal flag type anchor");
      const id=groups.length;
      groups.push({fingerprint_group:id,literal_classes:literalClasses,catalogue_types:types,common_automorphisms:aut,
        singleton_identification:types.length===1,column_signature:JSON.parse(signature)});
      for(const g of literalClasses)classGroup[g]=id;for(const type of types)typeAut.set(type,aut);
    }
    for(const ctx of contexts){
      const reconstructed=new Map();
      for(const group of groups){
        const c=ctx.expected.get(group.literal_classes[0])||0;
        assert(group.literal_classes.every(g=>(ctx.expected.get(g)||0)===c),"literal fingerprint equality");
        if(c)for(const type of group.catalogue_types)reconstructed.set(type,c);
      }
      assert(counterKey(reconstructed)===counterKey(ctx.actual),"all exact catalogue product rows");
    }
    let normalizedControls=0;
    for(const root of roots){
      for(const monomial of root.monomials){
        let rawForm=null;
        for(const ids of monomial.product_partitions){
          const form=new Map();for(const id of ids)addCounter(form,contexts[id].actual);
          if(rawForm===null)rawForm=form;else assert(counterKey(rawForm)===counterKey(form),"all presence partitions agree");
        }
        const literalCounts=new Map();for(const c of monomial.completions)literalCounts.set(c.literal_class,(literalCounts.get(c.literal_class)||0)+1);
        const literalForm=new Map();
        for(const group of groups){
          const c=literalCounts.get(group.literal_classes[0])||0;
          assert(group.literal_classes.every(g=>(literalCounts.get(g)||0)===c),"presence form respects fingerprint tie");
          if(c)for(const type of group.catalogue_types)literalForm.set(type,c);
        }
        assert(counterKey(literalForm)===counterKey(rawForm),"complete literal presence form");
        monomial.labelled_embedding_form=[...rawForm].sort((a,b)=>a[0]-b[0]);
        monomial.induced_count_form=monomial.labelled_embedding_form.map(([type,c])=>[type,c*typeAut.get(type)]);
        for(const c of monomial.completions)c.catalogue_fingerprint_group=classGroup[c.literal_class];
      }
      for(const orbit of root.orbits)assert(orbit.members.every(i=>same(root.monomials[i].induced_count_form,root.monomials[orbit.representative].induced_count_form)),"exact moment constancy under root group");
      const test=root.monomials.slice().sort((a,b)=>b.completions.length-a.completions.length||b.masks.length-a.masks.length)[0];
      const checked=new Set(),controls=[];
      for(const completion of test.completions)if(!checked.has(completion.literal_class)){
        checked.add(completion.literal_class);
        const host=attach(root.root_rows,test.masks,completion.edges);
        const direct=embeddingCount(root.root_rows,host,test.masks);
        const multiplicity=test.completions.filter(c=>c.literal_class===completion.literal_class).length;
        const expected=pool[completion.literal_class].automorphisms*multiplicity;
        assert(direct===expected,"direct presence-normalization host control");
        controls.push({masks:test.masks,host_rows:host,unrooted_automorphisms:pool[completion.literal_class].automorphisms,
          isomorphic_literal_completions:multiplicity,direct_labelled_root_embeddings:direct});normalizedControls++;
      }
      root.direct_presence_normalization_controls=controls;
    }
    return {
      status:"POINT_INDEPENDENT_COMPLETE_SMALL_ROOT_PREPARATION_PASS",source_git_blob:sourceGitBlob,bindings:BINDINGS,
      dependency_isomorphism_function:"makeRoot49RecoveryTools().isomorphisms",
      roots,literal_graph_classes:pool,catalogue_fingerprint_groups:groups,
      literal_product_rows:contexts.map(c=>({context:c.context,root_type:c.root_type,tensor_row:c.tensor_row,flags:c.flags,
        literal_multiplicities:[...c.expected].sort((a,b)=>a[0]-b[0]),catalogue_multiplicities:[...c.actual].sort((a,b)=>a[0]-b[0])})),
      summary:{roots:32,raw_monomials:totalRaw,supported_monomials:totalSupported,structurally_zero_monomials:totalRaw-totalSupported,
        moment_orbits:roots.reduce((s,r)=>s+r.orbits.length,0),literal_completions:totalCompletions,
        literal_unrooted_graph_classes:pool.length,catalogue_types:actualColumns.size,fingerprint_groups:groups.length,
        ambiguous_fingerprint_groups:groups.filter(g=>g.catalogue_types.length>1).length,product_rows:contexts.length,
        product_nonzeros:contexts.reduce((s,c)=>s+c.actual.size,0),literal_type_isomorphism_comparisons:isomorphismComparisons,
        five_class_subsets_checked:totalFive,direct_presence_normalization_controls:normalizedControls,synthetic_distribution_controls:64},
      tied_type_policy:"Only the common-Aut sum of counts is used; no individual ID or type-specific filter is inferred inside a tied fingerprint block.",
      catalogue_scope:"Indices are matched to literal product-column fingerprints within this finite family; the global catalogue is not regenerated.",
      unsupported_scope:"Every unsupported monomial has a literal cap violation before adding free edges. Adding edges cannot repair it. Unsupported tensor rows were not extracted.",
      count_point_loaded:false,optimizer_called:false
    };
  }
  function query(input,scope,point,prepared,sourceGitBlob=null){
    const cold=prepare(input,scope,sourceGitBlob);assert(same(cold,prepared),"complete preparation replay");
    assert(point.induced_counts.length===48965&&point.induced_counts.every(c=>Number.isSafeInteger(c)&&c>=0),"exact point counts");
    assert(point.exact_count_and_held_cut_witness&&point.required_zeros_hold&&point.x521_zero,"point binding scope");
    const counts=point.induced_counts,results=[];
    for(const root of prepared.roots){
      const codes=root.monomials.map(m=>BigInt(m.global_atom_code)),pop=root.monomials.map(m=>m.masks.length);
      const moments=root.monomials.map(m=>m.induced_count_form.reduce((s,[i,c])=>s+BigInt(c)*BigInt(counts[i]),0n));
      const weights=invert(codes,pop,moments),orbitWeights=root.orbits.map(o=>o.members.reduce((s,i)=>s+weights[i],0n));
      assert(moments[0]===BigInt(root.actual_root_automorphisms.length)*BigInt(counts[root.root_type]),"root normalization");
      if(moments[0]===0n)assert(moments.every(m=>m===0n),"zero-root extension moments");
      for(const o of root.orbits)assert(o.members.every(i=>weights[i]===weights[o.representative]),"orbit-invariant exact masses");
      for(let r=0;r<root.orbits.length;r++){
        const value=root.quotient_coefficients[r].reduce((s,c,o)=>s+BigInt(c)*orbitWeights[o],0n);
        assert(value===BigInt(root.orbits[r].size)*moments[root.orbits[r].representative],"complete quotient equality");
      }
      const negative=weights.map((w,i)=>({w,i})).filter(x=>x.w<0n).sort((a,b)=>a.w<b.w?-1:a.w>b.w?1:a.i-b.i);
      const certificates=[];
      for(const {w,i}of negative.slice(0,8)){
        const form=new Map(),terms=[];
        for(let t=0;t<codes.length;t++)if((codes[i]&codes[t])===codes[i]){
          const sign=(pop[t]-pop[i])&1?-1:1;terms.push([t,sign]);
          for(const [type,c]of root.monomials[t].induced_count_form)form.set(type,(form.get(type)||0n)+BigInt(sign)*BigInt(c));
        }
        for(let a=0;a<codes.length;a++){
          const value=terms.reduce((s,[t,sign])=>s+((codes[t]&codes[a])===codes[t]?BigInt(sign):0n),0n);
          assert(value===(a===i?1n:0n),"universal atom-indicator inequality");
        }
        const sparse=[...form].filter(([_type,c])=>c).sort((a,b)=>a[0]-b[0]);
        assert(sparse.reduce((s,[type,c])=>s+c*BigInt(counts[type]),0n)===w,"exact direct induced separator");
        certificates.push({atom_index:i,masks:root.monomials[i].masks,exact_value:w,monomial_terms:terms,
          direct_induced_count_form:sparse,full_structural_atoms_checked:codes.length,optimizer_eligible:false});
      }
      results.push({root_type:root.root_type,status:negative.length?"EXACT_NEGATIVE_ATOM":"EXACT_NONNEGATIVE_ATOM_DISTRIBUTION",
        labelled_root_mass:moments[0],atom_count:codes.length,orbit_count:root.orbits.length,
        positive_weights:weights.filter(w=>w>0n).length,zero_weights:weights.filter(w=>w===0n).length,negative_weights:negative.length,
        atom_moments:moments,atom_weights:weights,orbit_weights:orbitWeights,negative_certificates:certificates,
        all_individual_moment_equations_checked:true,all_quotient_equations_checked:true});
    }
    return wire({status:results.some(r=>r.negative_weights)?"EXACT_SMALL_ROOT_MOMENT_SEPARATORS":"EXACT_ALL_SMALL_ROOT_MOMENT_DISTRIBUTIONS",
      source_git_blob:sourceGitBlob,bindings:BINDINGS,complete_roots:32,roots:results,
      summary:{negative_roots:results.filter(r=>r.negative_weights).length,negative_atoms:results.reduce((s,r)=>s+r.negative_weights,0),
        individual_equations:results.reduce((s,r)=>s+r.atom_count,0),quotient_equations:results.reduce((s,r)=>s+r.orbit_count,0)},
      optimizer_called:false,full_graph_existence_resolved:false});
  }
  return {bindings:BINDINGS,prepare,query};
}

if (typeof module !== "undefined" && module.exports) {
  module.exports={makeSmallRootMomentTools};
  if(require.main===module){
    const fs=require("fs"),crypto=require("crypto"),path=require("path");
    function blob(file){const b=fs.readFileSync(file);return crypto.createHash("sha1").update("blob "+b.length+"\0").update(b).digest("hex");}
    const dependency=path.join(__dirname,"root49_packing_moment_recovery_check.js");
    if(blob(dependency)!=="d547df71ef544fc7e36a8580bc9f7bdc311d6871")throw Error("Frozen isomorphism dependency");
    const api=makeSmallRootMomentTools(require(dependency).makeRoot49RecoveryTools().isomorphisms);
    const [mode,inputPath,scopePath,pointPath]=process.argv.slice(2);
    if(!["prepare","query"].includes(mode)||!inputPath||!scopePath)throw Error("Usage: node checker.js prepare|query inputs.json scope.json [point.json]");
    if(blob(inputPath)!==api.bindings.input_git_blob||blob(scopePath)!==api.bindings.scope_git_blob)throw Error("Public input binding");
    const read=p=>JSON.parse(fs.readFileSync(p,"utf8")), input=read(inputPath),scope=read(scopePath),sourceBlob=blob(__filename);
    const prepared=api.prepare(input,scope,sourceBlob);let result=prepared;
    if(mode==="query"){if(!pointPath||blob(pointPath)!==api.bindings.point_git_blob)throw Error("Point binding");result=api.query(input,scope,read(pointPath),prepared,sourceBlob);}
    console.log(JSON.stringify(result,null,2));
  }
}
