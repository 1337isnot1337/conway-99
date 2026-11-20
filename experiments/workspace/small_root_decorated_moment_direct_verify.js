"use strict";

/* Artifact-only direct verification of the decorated small-root distributions.
   No inversion, optimizer, original query or stored extension lists are used. */
function verifyDecoratedSmallRootResult(prepared,point,result) {
  function check(ok,message){if(!ok)throw Error(message);}
  function same(a,b){return JSON.stringify(a)===JSON.stringify(b);}
  function integer(s){check(typeof s==="string"&&/^-?(0|[1-9][0-9]*)$/.test(s),"canonical exact integer");return BigInt(s);}
  function pop(x){let n=0;for(;x;x&=x-1)n++;return n;}
  function edgeSet(state){return new Set(state.edges.map(([a,b])=>a+":"+b));}
  function key(masks,edges){return masks.join(",")+"|"+edges.map(e=>e.join(":")).join(",");}
  function moved(mask,p){let m=0;for(let i=0;i<6;i++)if((mask>>i)&1)m|=1<<p[i];return m;}
  function restricted(part,whole,partialEdges,wholeEdges) {
    if(!part.masks.every(m=>whole.masks.includes(m)))return false;
    for(let i=0;i<part.masks.length;i++)for(let j=i+1;j<part.masks.length;j++){
      const pair=part.masks[i]+":"+part.masks[j];
      if(partialEdges.has(pair)!==wholeEdges.has(pair))return false;
    }
    return true;
  }
  check(prepared.status==="POINT_INDEPENDENT_COMPLETE_DECORATED_SMALL_ROOT_PREPARATION_PASS","preparation status");
  check(result.status==="EXACT_ALL33_SMALL_ROOT_DECORATED_DISTRIBUTIONS","claimed result");
  check(result.source_git_blob===prepared.source_git_blob&&same(result.bindings,prepared.bindings),"source and input binding");
  check(prepared.roots.length===33&&result.roots.length===33,"complete root family");
  check(point.induced_counts.length===48965&&point.induced_counts.every(n=>Number.isSafeInteger(n)&&n>=0),"exact point integers");
  const counts=point.induced_counts.map(BigInt);
  const types=new Map(prepared.type_factor_table.map(t=>[t.catalogue_type,t]));
  let momentEquations=0,presenceEquations=0,forms=0,transports=0,divisibilities=0;
  let positive=0,zero=0,incidencePairsTested=0,literalTypeMaps=0;
  const summaries=[];
  for(let ri=0;ri<33;ri++){
    const root=prepared.roots[ri],saved=result.roots[ri],states=root.states;
    check(saved.root_type===root.root_type&&saved.decorated_states===states.length,"root order/count");
    check(saved.exact_state_weights.length===states.length&&saved.partial_pattern_moments.length===states.length,"complete point vectors");
    const weights=saved.exact_state_weights.map(integer),moments=saved.partial_pattern_moments.map(integer);
    check(weights.every(w=>w>=0n),"every exact-state mass nonnegative");
    const edgeSets=states.map(edgeSet),lookup=new Map(states.map(s=>[key(s.masks,s.edges),s.state]));
    check(lookup.size===states.length,"unique decorated states");
    let rootPositive=0,rootZero=0;
    for(const state of states){
      const i=state.state,type=types.get(state.catalogue_type);
      check(type&&type.automorphisms===state.moment_coefficient,"full type factor");
      const permutation=state.literal_to_type_isomorphism;
      check(same(permutation.slice().sort((a,b)=>a-b),Array.from({length:state.literal_rows.length},(_,j)=>j)),"literal permutation");
      for(let a=0;a<permutation.length;a++)for(let b=0;b<permutation.length;b++)
        check(((state.literal_rows[a]>>b)&1)===((type.representative_rows[permutation[a]]>>permutation[b])&1),"literal-to-type adjacency");
      literalTypeMaps++;
      const expected=BigInt(state.moment_coefficient)*counts[state.catalogue_type];
      check(moments[i]===expected,"each original induced-pattern moment");
      let actual=0n;
      for(const whole of states){
        incidencePairsTested++;
        if(restricted(state,whole,edgeSets[i],edgeSets[whole.state]))actual+=weights[whole.state];
      }
      check(actual===expected,"direct pattern-incidence sum");
      momentEquations++;
      const formValue=state.exact_state_induced_count_form.reduce((sum,[t,c])=>sum+BigInt(c)*counts[t],0n);
      check(formValue===weights[i],"induced certificate form agrees with saved state mass");forms++;
      if(weights[i]>0n)rootPositive++;else rootZero++;
    }
    const rootMass=moments[0];
    check(integer(saved.labelled_root_mass)===rootMass&&weights.reduce((s,w)=>s+w,0n)===rootMass,"total labelled root mass");
    for(const atom of root.presence_atoms){
      const expected=atom.presence_moment_form.reduce((sum,[t,c])=>sum+BigInt(c)*counts[t],0n);
      const moment=states.reduce((sum,t)=>sum+(atom.masks.every(m=>t.masks.includes(m))?weights[t.state]:0n),0n);
      const exact=states.reduce((sum,t)=>sum+(same(atom.masks,t.masks)?weights[t.state]:0n),0n);
      check(moment===expected&&integer(saved.presence_moments[atom.atom])===expected,"every original presence moment");
      check(integer(saved.presence_exact_weights[atom.atom])===exact,"every coarsened exact presence weight");presenceEquations++;
    }
    for(const state of states){
      let stabilizer=0;
      for(const p of root.root_automorphisms){
        const masks=state.masks.map(m=>moved(m,p)).sort((a,b)=>a-b);
        const edges=state.edges.map(([a,b])=>[moved(a,p),moved(b,p)].sort((x,y)=>x-y)).sort((a,b)=>a[0]-b[0]||a[1]-b[1]);
        const image=lookup.get(key(masks,edges));
        check(image!==undefined&&weights[image]===weights[state.state],"every actual-root transport preserves mass");
        transports++;if(image===state.state)stabilizer++;
      }
      check(stabilizer===state.stabilizer_order&&weights[state.state]%BigInt(stabilizer)===0n,"literal stabilizer and divisibility");divisibilities++;
    }
    check(rootPositive===saved.positive_weights&&rootZero===saved.zero_weights&&saved.negative_weights===0,"all mass signs");
    check(saved.negative_certificates.length===0,"no negative certificate omitted");
    positive+=rootPositive;zero+=rootZero;
    summaries.push({root_type:root.root_type,states:states.length,positive:rootPositive,zero:rootZero,labelled_root_mass:rootMass.toString()});
  }
  check(momentEquations===1275&&presenceEquations===1115&&positive+zero===1275,"complete equation counts");
  check(result.summary.negative_roots===0&&result.summary.negative_states===0,"terminal summary");
  return {
    status:"PASS: artifact-only direct decorated-incidence verification",
    roots:33,decorated_states:1275,positive_weights:positive,zero_weights:zero,
    direct_induced_pattern_equations:momentEquations,original_presence_equations:presenceEquations,
    state_induced_forms:forms,literal_type_isomorphisms_checked:literalTypeMaps,
    direct_state_pair_incidence_tests:incidencePairsTested,
    root_state_transports:transports,stabilizer_divisibilities:divisibilities,
    root_summaries:summaries,
    stored_extension_lists_used:false,inversion_used:false,
    original_query_called:false,optimizer_called:false,
    mathematical_scope:"This immutable count point passes all33 complete decorated small-root distributions. No graph-existence assertion."
  };
}
if(typeof module!=="undefined"&&module.exports){
  module.exports={verifyDecoratedSmallRootResult};
  if(require.main===module){
    const fs=require("fs"),crypto=require("crypto");
    const [preparedPath,pointPath,resultPath]=process.argv.slice(2);
    const blob=p=>{const b=fs.readFileSync(p);return crypto.createHash("sha1").update("blob "+b.length+"\0").update(b).digest("hex");};
    if(blob(preparedPath)!=="683261d3bce6c56eafe9398f9da466f96dc687d7"||
       blob(pointPath)!=="c881dae3be05cf289fcc45a99d72c405ac863c46"||
       blob(resultPath)!=="c1921a56faa99313bcb5d641bfd66754b45ad9eb")throw Error("Immutable artifact binding");
    const read=p=>JSON.parse(fs.readFileSync(p,"utf8"));
    console.log(JSON.stringify(verifyDecoratedSmallRootResult(read(preparedPath),read(pointPath),read(resultPath)),null,2));
  }
}
