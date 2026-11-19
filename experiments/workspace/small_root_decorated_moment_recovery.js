"use strict";

/* Complete high-graph moments for the 33 roots with high population at most4.
   Preparation is point-independent. The separate query uses BigInt only.
   Literal catalogue identities and coefficients are bound to frozen public
   preparation artifacts; no new global graph catalogue is assumed. */

function makeDecoratedSmallRootTools(isomorphisms) {
  const BINDINGS = {
    small32_preparation_git_blob: "537b722f2dd4f964c5fa053d5398e41c60b4ed9d",
    small32_preparation_sha256: "7ff07b4098759a56844b346087ea16cc66584b79b3b7d89d110ae97dc06f67ca",
    small32_source_git_blob: "34085dd6833ab816968ede0ba4637e44713b37fc",
    root49_preparation_git_blob: "051d30abea64b1e4060e51f103c619844ba864e7",
    root49_preparation_sha256: "b134b6c61042335fcd96d3bc227218590be6885fba80377ab9542029dfd20bac",
    isomorphism_dependency_git_blob: "d547df71ef544fc7e36a8580bc9f7bdc311d6871",
    count_point_git_blob: "c881dae3be05cf289fcc45a99d72c405ac863c46",
    count_point_sha256: "0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df"
  };
  function assert(ok, message) { if (!ok) throw Error(message); }
  function same(a,b) { return JSON.stringify(a) === JSON.stringify(b); }
  function popcount(x) { let n=0; for (;x;x&=x-1) n++; return n; }
  function tick(deadline) { if (Date.now()>deadline) throw Error("60-second exact preparation/query bound"); }
  function choose(items, k) {
    const result=[];
    function visit(at, current) {
      if (current.length===k) { result.push(current.slice()); return; }
      for (let i=at; i<=items.length-k+current.length; i++) {
        current.push(items[i]); visit(i+1,current); current.pop();
      }
    }
    visit(0,[]); return result;
  }
  function sparse(map) {
    const result=[...map].filter(([_i,c])=>c).sort((a,b)=>a[0]-b[0]);
    assert(result.every(([i,c])=>Number.isSafeInteger(i)&&Number.isSafeInteger(c)), "safe exact sparse coefficients");
    return result;
  }
  function add(map, index, value) {
    const next=(map.get(index)||0)+value;
    assert(Number.isSafeInteger(next),"safe coefficient addition"); map.set(index,next);
  }
  function key(masks, edges) { return masks.join(",")+"|"+edges.map(e=>e.join(":")).join(","); }
  function sortedEdges(edges) {
    return edges.map(([a,b])=>a<b?[a,b]:[b,a]).sort((a,b)=>a[0]-b[0]||a[1]-b[1]);
  }
  function attach(root, masks, maskEdges=[]) {
    const rows=root.slice();
    masks.forEach((mask,j)=>{
      rows.push(mask);
      for (let i=0;i<6;i++) if ((mask>>i)&1) rows[i]|=1<<(6+j);
    });
    const at=new Map(masks.map((mask,i)=>[mask,6+i]));
    for (const [a,b] of maskEdges) {
      assert(at.has(a)&&at.has(b)&&a<b,"literal mask edge");
      rows[at.get(a)]|=1<<at.get(b); rows[at.get(b)]|=1<<at.get(a);
    }
    return rows;
  }
  function violation(rows) {
    for (let i=0;i<rows.length;i++) for (let j=i+1;j<rows.length;j++) {
      const adjacent=(rows[i]>>j)&1, common=popcount(rows[i]&rows[j]);
      if (adjacent+common>2) return [i,j,adjacent,common];
    }
    return null;
  }
  function verifyPermutation(left,right,p) {
    assert(p.length===left.length&&same(p.slice().sort((a,b)=>a-b),Array.from({length:p.length},(_,i)=>i)), "isomorphism permutation");
    for (let i=0;i<left.length;i++) for (let j=0;j<left.length;j++)
      assert(((left[i]>>j)&1)===((right[p[i]]>>p[j])&1), "literal isomorphism edge");
  }
  function mappedMask(mask,p) {
    let result=0; for(let i=0;i<6;i++) if((mask>>i)&1) result|=1<<p[i]; return result;
  }
  function invert(root, moments) {
    return root.states.map(state=>state.extension_states.reduce((sum,t)=>{
      const sign=(root.states[t].population-state.population)&1?-1n:1n;
      return sum+sign*moments[t];
    },0n));
  }
  function checkMoments(root,moments,weights) {
    for (const state of root.states) {
      const reconstructed=state.extension_states.reduce((sum,t)=>sum+weights[t],0n);
      assert(reconstructed===moments[state.state],"every decorated moment reconstructed");
    }
    const presenceMoments=root.presence_atoms.map(atom=>atom.states.reduce((sum,s)=>sum+moments[s],0n));
    const presenceWeights=root.presence_atoms.map(atom=>atom.states.reduce((sum,s)=>sum+weights[s],0n));
    for (const atom of root.presence_atoms) {
      let reconstructed=0n, mobius=0n;
      for (const extension of root.presence_atoms) if(atom.masks.every(mask=>extension.masks.includes(mask))) {
        reconstructed+=presenceWeights[extension.atom];
        mobius+=((extension.masks.length-atom.masks.length)&1?-1n:1n)*presenceMoments[extension.atom];
      }
      assert(reconstructed===presenceMoments[atom.atom]&&mobius===presenceWeights[atom.atom],
        "decorated sums agree with every presence moment and exact weight");
    }
    assert(weights.reduce((sum,v)=>sum+v,0n)===moments[0],"total decorated mass is the labelled root moment");
    return {presenceMoments,presenceWeights};
  }
  function prepare(small32,root49,sourceGitBlob=null) {
    const started=Date.now(), deadline=started+60000;
    assert(small32.status==="POINT_INDEPENDENT_COMPLETE_SMALL_ROOT_PREPARATION_PASS","small32 status");
    assert(small32.source_git_blob===BINDINGS.small32_source_git_blob,"small32 source");
    assert(small32.count_point_loaded===false&&small32.optimizer_called===false,"small32 point-independent input");
    assert(root49.status==="POINT_INDEPENDENT_ROOT49_PREPARATION_PASS"&&root49.root_type===49,"root49 status");
    assert(root49.point_loaded===false&&root49.optimizer_called===false&&root49.all_pair_edges_forbidden===true,"root49 scope");
    assert(small32.roots.length===32&&root49.supported.length===80,"complete root counts");
    assert(small32.summary.literal_completions===1195&&small32.summary.supported_monomials===1035,"small32 coverage");
    assert(small32.catalogue_fingerprint_groups.length===294&&small32.literal_graph_classes.length===294,"all singleton type factors");
    const types=new Map(), classTypes=new Map();
    let automorphismRecounts=0, literalIsomorphismChecks=0, productRowsChecked=0;
    function register(type,rows,aut,provenance) {
      assert(Number.isSafeInteger(type)&&type>=0&&type<48965&&Number.isSafeInteger(aut)&&aut>0,"type factor");
      assert(violation(rows)===null,"type representative caps");
      if (!types.has(type)) {
        tick(deadline);
        assert(isomorphisms(rows).count===aut,"independent type automorphism recount");
        automorphismRecounts++;
        types.set(type,{catalogue_type:type,representative_rows:rows.slice(),automorphisms:aut,provenance:[provenance]});
      } else {
        assert(types.get(type).automorphisms===aut,"same catalogue type factor");
        types.get(type).provenance.push(provenance);
      }
    }
    for (const group of small32.catalogue_fingerprint_groups) {
      assert(group.singleton_identification&&group.literal_classes.length===1&&group.catalogue_types.length===1,"singleton fingerprint required");
      const cls=group.literal_classes[0], type=group.catalogue_types[0], graph=small32.literal_graph_classes[cls];
      assert(graph.literal_class===cls&&!classTypes.has(cls),"complete literal classes");
      assert(graph.automorphisms===group.common_automorphisms,"fingerprint automorphism factor");
      classTypes.set(cls,type);
      register(type,graph.rows,graph.automorphisms,{input:"small32",literal_class:cls,fingerprint_group:group.fingerprint_group});
    }
    assert(classTypes.size===294&&types.size===294,"distinct complete singleton type map");
    for (const row of small32.literal_product_rows) {
      const mapped=new Map();
      for(const [cls,multiplicity] of row.literal_multiplicities) {
        assert(classTypes.has(cls)&&Number.isSafeInteger(multiplicity)&&multiplicity>0,"product literal multiplicity");
        add(mapped,classTypes.get(cls),multiplicity);
      }
      assert(same(sparse(mapped),row.catalogue_multiplicities),"all frozen product coefficients agree with singleton type map");
      productRowsChecked++;
    }
    assert(productRowsChecked===2450,"all product contexts bound");

    const inputs=small32.roots.map(r=>({
      root_type:r.root_type,root_rows:r.root_rows,high_masks:r.high_masks,
      group:r.actual_root_automorphisms,
      atoms:r.monomials.map(m=>({
        masks:m.masks,original_atom:m.atom_index,presence_form:m.induced_count_form,
        completions:m.completions.map(c=>{
          assert(classTypes.has(c.literal_class),"completion class binding");
          const type=classTypes.get(c.literal_class), factor=types.get(type).automorphisms;
          const edges=sortedEdges(c.edges.map(([a,b])=>[m.masks[a],m.masks[b]]));
          return {edges,type,factor,source:{input:"small32",literal_class:c.literal_class,fingerprint_group:c.catalogue_fingerprint_group}};
        })
      }))
    }));
    for(const atom of root49.supported) {
      assert(atom.labelled_embedding_coefficient===1&&atom.induced_count_coefficient===atom.unrooted_automorphisms,"root49 literal coefficient");
      register(atom.catalogue_type,atom.literal_graph_rows,atom.unrooted_automorphisms,
        {input:"root49",presence_atom:atom.atom_index});
    }
    inputs.push({
      root_type:49,root_rows:root49.root_rows,high_masks:root49.high_masks,
      group:root49.complete_actual_root_automorphisms,
      atoms:root49.supported.map(atom=>({
        masks:atom.masks,original_atom:atom.atom_index,
        presence_form:[[atom.catalogue_type,atom.unrooted_automorphisms]],
        completions:[{edges:[],type:atom.catalogue_type,factor:atom.unrooted_automorphisms,
          source:{input:"root49",presence_atom:atom.atom_index}}]
      }))
    });
    inputs.sort((a,b)=>a.root_type-b.root_type);
    assert(new Set(inputs.map(r=>r.root_type)).size===33,"distinct complete root family");
    const universal=Array.from({length:64},(_,i)=>i).filter(i=>popcount(i)>=3);
    const roots=[];
    let rawPresenceChecked=0, edgeAssignmentsChecked=0, fiveSubsetsChecked=0;
    let restrictionsChecked=0, atomicIndicatorChecks=0, presenceFormChecks=0, groupStateTransports=0, stabilizerDivisibilityChecks=0;
    let strictCoarseningControl=null;
    for(const input of inputs) {
      tick(deadline);
      const high=universal.filter(mask=>violation(attach(input.root_rows,[mask]))===null);
      assert(same(high,input.high_masks),"complete literal single-high domain");
      const states=[],presence=[],lookup=new Map(),presenceLookup=new Map();
      for(const atom of input.atoms) {
        assert(atom.masks.length<=4&&same(atom.masks,atom.masks.slice().sort((a,b)=>a-b)),"ordered presence masks");
        const pkey=atom.masks.join(",");
        assert(!presenceLookup.has(pkey),"unique presence atom");
        const index=presence.length; presenceLookup.set(pkey,index);
        const entry={atom:index,original_presence_atom:atom.original_atom,masks:atom.masks.slice(),states:[],presence_moment_form:atom.presence_form};
        const aggregate=new Map();
        for(const completion of atom.completions) {
          const edges=completion.edges, skey=key(atom.masks,edges), rows=attach(input.root_rows,atom.masks,edges);
          assert(same(edges,sortedEdges(edges))&&new Set(edges.map(e=>e.join(","))).size===edges.length,"canonical simple edge decoration");
          assert(!lookup.has(skey)&&violation(rows)===null,"unique cap-valid decorated state");
          const type=types.get(completion.type);
          assert(type&&type.automorphisms===completion.factor,"complete decorated moment factor");
          tick(deadline);
          const iso=isomorphisms(rows,type.representative_rows,true);
          assert(iso.count===completion.factor&&iso.first!==null,"literal state isomorphism and Aut factor");
          verifyPermutation(rows,type.representative_rows,iso.first);
          literalIsomorphismChecks++;
          const id=states.length;lookup.set(skey,id);entry.states.push(id);
          states.push({state:id,presence_atom:index,population:atom.masks.length,
            masks:atom.masks.slice(),edges:edges.map(e=>e.slice()),literal_rows:rows,
            catalogue_type:completion.type,moment_coefficient:completion.factor,
            type_binding_source:completion.source,literal_to_type_isomorphism:iso.first,
            restriction_states:[],extension_states:[]});
          add(aggregate,completion.type,completion.factor);
        }
        assert(same(sparse(aggregate),atom.presence_form),"every sum of decorated moments equals frozen presence form");
        presenceFormChecks++;presence.push(entry);
      }
      assert(states.length>0&&states[0].population===0&&states[0].edges.length===0,"empty decorated state first");
      const independentlyEnumerated=new Set();
      for(let size=0;size<=4;size++) for(const masks of choose(high,size)) {
        rawPresenceChecked++;
        if(violation(attach(input.root_rows,masks))!==null) {
          assert(!presenceLookup.has(masks.join(",")),"forbidden presence atom absent");
          continue;
        }
        assert(presenceLookup.has(masks.join(",")),"every possible presence atom included");
        const pairs=choose(masks,2);
        for(let bitset=0;bitset<(1<<pairs.length);bitset++) {
          edgeAssignmentsChecked++;
          const edges=pairs.filter((_edge,j)=>(bitset>>j)&1);
          const rows=attach(input.root_rows,masks,edges);
          const skey=key(masks,edges);
          if(violation(rows)===null) {
            assert(lookup.has(skey),"every cap-valid high-edge decoration included");
            independentlyEnumerated.add(skey);
          } else assert(!lookup.has(skey),"forbidden decorated state absent");
        }
      }
      assert(independentlyEnumerated.size===states.length,"complete decorated-state coverage");
      const fiveWitnesses=[];
      for(const masks of choose(high,5)) {
        const bad=violation(attach(input.root_rows,masks));
        assert(bad!==null,"all five-high subsets visibly impossible");
        fiveWitnesses.push({masks,witness:bad});fiveSubsetsChecked++;
      }
      for(const state of states) {
        for(let bits=0;bits<(1<<state.population);bits++) {
          const masks=state.masks.filter((_mask,i)=>(bits>>i)&1);
          const selected=new Set(masks), edges=state.edges.filter(([a,b])=>selected.has(a)&&selected.has(b));
          const id=lookup.get(key(masks,edges));
          assert(id!==undefined,"every induced restriction is a decorated state");
          state.restriction_states.push(id);states[id].extension_states.push(state.state);
          restrictionsChecked++;
        }
        assert(new Set(state.restriction_states).size===(1<<state.population),"one restriction per mask subset");
      }
      for(const state of states) state.extension_states.sort((a,b)=>a-b);
      const root={root_type:input.root_type,root_rows:input.root_rows,high_masks:high,
        maximum_population:4,presence_atoms:presence,states,
        five_subset_exclusion_witnesses:fiveWitnesses,root_automorphisms:input.group,decorated_orbits:[]};
      for(const state of states) {
        const form=new Map();
        for(const t of state.extension_states) {
          const extension=states[t], sign=(extension.population-state.population)&1?-1:1;
          add(form,extension.catalogue_type,sign*extension.moment_coefficient);
        }
        state.exact_state_induced_count_form=sparse(form);
      }
      // Test every column of the finite zeta/Mobius identity, not a random sample.
      for(const actual of states) {
        const restrictionSet=new Set(actual.restriction_states);
        const moments=states.map(state=>restrictionSet.has(state.state)?1n:0n);
        const weights=invert(root,moments);
        assert(weights.every((w,s)=>w===(s===actual.state?1n:0n)),"complete atomic-indicator inversion control");
        checkMoments(root,moments,weights);
        atomicIndicatorChecks+=states.length;
      }
      const group=input.group;
      assert(group.length===isomorphisms(input.root_rows).count&&new Set(group.map(p=>p.join(","))).size===group.length,"complete root automorphism group");
      const actions=[];
      for(const p of group) {
        verifyPermutation(input.root_rows,input.root_rows,p);
        const action=states.map(state=>{
          const masks=state.masks.map(m=>mappedMask(m,p)).sort((a,b)=>a-b);
          const edges=sortedEdges(state.edges.map(([a,b])=>[mappedMask(a,p),mappedMask(b,p)]));
          const image=lookup.get(key(masks,edges));
          assert(image!==undefined,"root action closes decorated domain");
          assert(states[image].catalogue_type===state.catalogue_type&&states[image].moment_coefficient===state.moment_coefficient,"type-factor invariance under root action");
          assert(same(states[image].exact_state_induced_count_form,state.exact_state_induced_count_form),"exact-state form invariance under root action");
          groupStateTransports++;return image;
        });
        assert(new Set(action).size===states.length,"decorated action is a permutation");actions.push(action);
      }
      const seen=new Set();
      for(const state of states) if(!seen.has(state.state)) {
        const members=[...new Set(actions.map(action=>action[state.state]))].sort((a,b)=>a-b);
        const stabilizer=actions.filter(action=>action[state.state]===state.state).length;
        assert(members.length*stabilizer===group.length,"orbit-stabilizer count");
        members.forEach(id=>seen.add(id));
        for(const id of members) {
          states[id].stabilizer_order=stabilizer;
          assert(states[id].exact_state_induced_count_form.every(([_type,c])=>c%stabilizer===0),"coefficientwise exact-state stabilizer divisibility");
          stabilizerDivisibilityChecks++;
        }
        root.decorated_orbits.push({orbit:root.decorated_orbits.length,representative:state.state,members,stabilizer_order:stabilizer});
      }
      if(strictCoarseningControl===null) {
        for(const a of states) {
          const siblings=presence[a.presence_atom].states.filter(s=>s!==a.state);
          const extension=a.extension_states.find(t=>states[t].population>a.population);
          if(siblings.length&&extension!==undefined) {
            const b=siblings[0],w=states.map(()=>0n);w[a.state]=-1n;w[b]=1n;w[extension]=1n;
            const moments=states.map(s=>s.extension_states.reduce((sum,t)=>sum+w[t],0n));
            assert(moments.every(x=>x>=0n),"negative-decoration synthetic control has nonnegative partial moments");
            const recovered=invert(root,moments);assert(recovered.every((x,i)=>x===w[i]),"negative-decoration control recovered");
            const checked=checkMoments(root,moments,recovered);
            assert(checked.presenceWeights.every(x=>x>=0n),"negative decoration hidden in nonnegative presence weights");
            strictCoarseningControl={root_type:input.root_type,negative_state:a.state,positive_same_presence_state:b,positive_extension_state:extension,
              complete_partial_moments_nonnegative:true,complete_presence_weights_nonnegative:true,decorated_weight_negative:true,
              catalogue_consistent_count_point_claimed:false};
            break;
          }
        }
      }
      roots.push(root);
    }
    assert(strictCoarseningControl!==null,"strict coarsening negative control exists");
    assert(roots.length===33&&roots.reduce((n,r)=>n+r.presence_atoms.length,0)===1115,"all33 presence coverage");
    assert(roots.reduce((n,r)=>n+r.states.length,0)===1275,"all1275 decorated states");
    tick(deadline);
    return {
      status:"POINT_INDEPENDENT_COMPLETE_DECORATED_SMALL_ROOT_PREPARATION_PASS",
      source_git_blob:sourceGitBlob,bindings:BINDINGS,
      roots,type_factor_table:[...types.values()].sort((a,b)=>a.catalogue_type-b.catalogue_type),
      summary:{roots:33,presence_atoms:1115,decorated_states:1275,
        roots_with_nonempty_high_edges:roots.filter(r=>r.states.some(s=>s.edges.length)).length,
        decorated_orbits:roots.reduce((n,r)=>n+r.decorated_orbits.length,0),
        distinct_catalogue_types:types.size,automorphism_recounts:automorphismRecounts,literal_isomorphism_checks:literalIsomorphismChecks,
        frozen_product_rows_checked:productRowsChecked,raw_presence_sets_checked:rawPresenceChecked,
        internal_edge_assignments_checked:edgeAssignmentsChecked,five_subsets_checked:fiveSubsetsChecked,
        induced_restrictions_checked:restrictionsChecked,atomic_indicator_equalities_checked:atomicIndicatorChecks,
        presence_form_equalities_checked:presenceFormChecks,root_group_state_transports_checked:groupStateTransports,
        stabilizer_divisibility_forms_checked:stabilizerDivisibilityChecks},
      strict_coarsening_synthetic_control:strictCoarseningControl,
      normalization:"One fixed literal decorated pattern has moment Aut(F)*N_F because high masks identify its free vertices uniquely.",
      inversion:"w(A,E)=sum_{(T,D) restricting to(A,E)}(-1)^(|T|-|A|)*m(T,D).",
      catalogue_scope:"Uses frozen singleton fingerprints and root49 literal anchors; the global catalogue is not regenerated.",
      count_point_loaded:false,optimizer_called:false,full_graph_existence_resolved:false
    };
  }
  function query(small32,root49,point,prepared,sourceGitBlob=null) {
    const cold=prepare(small32,root49,sourceGitBlob);
    assert(same(cold,prepared),"complete point-independent cold preparation replay");
    const deadline=Date.now()+60000;
    assert(point.induced_counts.length===48965&&point.induced_counts.every(n=>Number.isSafeInteger(n)&&n>=0),"exact count-point coordinates");
    assert(point.exact_count_and_held_cut_witness&&point.required_zeros_hold&&point.x521_zero,"frozen count-point scope");
    const counts=point.induced_counts.map(BigInt),results=[];
    for(const root of prepared.roots) {
      tick(deadline);
      const moments=root.states.map(state=>BigInt(state.moment_coefficient)*counts[state.catalogue_type]);
      const weights=invert(root,moments);
      const aggregate=checkMoments(root,moments,weights);
      for(const state of root.states) {
        const direct=state.exact_state_induced_count_form.reduce((sum,[type,c])=>sum+BigInt(c)*counts[type],0n);
        assert(direct===weights[state.state],"every exact-state induced form evaluated");
        assert(weights[state.state]%BigInt(state.stabilizer_order)===0n,"exact-state mass divisibility");
      }
      for(const orbit of root.decorated_orbits)
        assert(orbit.members.every(s=>weights[s]===weights[orbit.representative]),"decorated exact-state orbit invariance");
      for(const atom of root.presence_atoms) {
        const direct=atom.presence_moment_form.reduce((sum,[type,c])=>sum+BigInt(c)*counts[type],0n);
        assert(direct===aggregate.presenceMoments[atom.atom],"all frozen presence moments recovered");
      }
      const negative=root.states.filter(state=>weights[state.state]<0n);
      const certificates=negative.map(state=>({
        state:state.state,masks:state.masks,edges:state.edges,value:weights[state.state],
        direct_induced_count_form:state.exact_state_induced_count_form,
        extension_terms:state.extension_states.map(t=>[t,(root.states[t].population-state.population)&1?-1:1]),
        exact_atom_indicator_checked_against_all_decorated_states:root.states.length
      }));
      results.push({root_type:root.root_type,status:negative.length?"EXACT_NEGATIVE_DECORATED_STATE":"EXACT_NONNEGATIVE_DECORATED_DISTRIBUTION",
        decorated_states:root.states.length,decorated_orbits:root.decorated_orbits.length,
        labelled_root_mass:moments[0],positive_weights:weights.filter(w=>w>0n).length,
        zero_weights:weights.filter(w=>w===0n).length,negative_weights:negative.length,
        partial_pattern_moments:moments,exact_state_weights:weights,
        presence_moments:aggregate.presenceMoments,presence_exact_weights:aggregate.presenceWeights,
        negative_certificates:certificates,
        all_decorated_moments_reconstructed:true,all_presence_sums_and_weights_checked:true});
    }
    const result={
      status:results.some(r=>r.negative_weights)?"EXACT_SMALL_ROOT_DECORATED_SEPARATORS":"EXACT_ALL33_SMALL_ROOT_DECORATED_DISTRIBUTIONS",
      source_git_blob:sourceGitBlob,bindings:BINDINGS,roots:results,
      summary:{roots:33,decorated_states:1275,presence_atoms:1115,
        negative_roots:results.filter(r=>r.negative_weights).length,
        negative_states:results.reduce((n,r)=>n+r.negative_weights,0)},
      optimizer_called:false,full_graph_existence_resolved:false
    };
    return JSON.parse(JSON.stringify(result,(_key,value)=>typeof value==="bigint"?value.toString():value));
  }
  return {bindings:BINDINGS,prepare,query};
}

if (typeof module!=="undefined"&&module.exports) {
  module.exports={makeDecoratedSmallRootTools};
  if(require.main===module) {
    const fs=require("fs"),crypto=require("crypto"),path=require("path");
    function blob(file) { const bytes=fs.readFileSync(file);return crypto.createHash("sha1").update("blob "+bytes.length+"\0").update(bytes).digest("hex"); }
    const dependency=path.join(__dirname,"root49_packing_moment_recovery_check.js");
    if(blob(dependency)!=="d547df71ef544fc7e36a8580bc9f7bdc311d6871") throw Error("Frozen isomorphism dependency");
    const tools=makeDecoratedSmallRootTools(require(dependency).makeRoot49RecoveryTools().isomorphisms);
    const [mode,small32Path,root49Path,pointPath]=process.argv.slice(2);
    if(!["prepare","query"].includes(mode)||!small32Path||!root49Path)
      throw Error("Usage: node checker.js prepare|query small32-preparation.json root49-preparation.json [point.json]");
    if(blob(small32Path)!==tools.bindings.small32_preparation_git_blob||blob(root49Path)!==tools.bindings.root49_preparation_git_blob)
      throw Error("Frozen preparation input binding");
    const read=p=>JSON.parse(fs.readFileSync(p,"utf8"));
    const small32=read(small32Path),root49=read(root49Path),sourceBlob=blob(__filename);
    const prepared=tools.prepare(small32,root49,sourceBlob);let result=prepared;
    if(mode==="query") {
      if(!pointPath||blob(pointPath)!==tools.bindings.count_point_git_blob) throw Error("Frozen count-point binding");
      result=tools.query(small32,root49,read(pointPath),prepared,sourceBlob);
    }
    console.log(JSON.stringify(result,null,2));
  }
}
