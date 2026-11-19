"use strict";

/* Independent artifact-only arithmetic replay. No subject checker import,
   graph generation, tensor generation, or optimizer. */

function replayRoot49Distribution(prepared,point,result,sourceGitBlob=null){
  function assert(x,m){if(!x)throw Error(m);}
  const expected={checker:"d547df71ef544fc7e36a8580bc9f7bdc311d6871",preparation:"051d30abea64b1e4060e51f103c619844ba864e7",result:"1b80dd8bc11ac4e396d987431fd93e56f9a04eb1",point:"c881dae3be05cf289fcc45a99d72c405ac863c46"};
  assert(prepared.source_git_blob===expected.checker&&result.source_git_blob===expected.checker,"checker source binding");
  assert(prepared.status==="POINT_INDEPENDENT_ROOT49_PREPARATION_PASS"&&result.status==="EXACT_ROOT49_COMPLETE_PACKING_MOMENT_DISTRIBUTION","exact statuses");
  assert(prepared.supported.length===80&&prepared.orbits.length===19&&result.atom_weights.length===80&&result.orbit_weights.length===19,"complete sizes");
  const counts=point.induced_counts;assert(counts.length===48965&&counts.every(x=>Number.isSafeInteger(x)&&x>=0),"point integers");
  const codes=[],weights=[],moments=[];
  for(let i=0;i<80;i++){
    const p=prepared.supported[i],r=result.atom_weights[i];
    assert(p.atom_index===i&&r.atom_index===i&&p.global_atom_code===r.global_atom_code,"atom identity");
    assert(p.catalogue_type===r.catalogue_type&&p.unrooted_automorphisms===r.automorphisms&&p.induced_count_coefficient===r.automorphisms,"literal count factor");
    assert(JSON.stringify(p.masks)===JSON.stringify(r.masks),"mask binding");
    const m=BigInt(r.automorphisms)*BigInt(counts[r.catalogue_type]),w=BigInt(r.weight);
    assert(m===BigInt(r.moment)&&w>=0n,"exact moment and nonnegative mass");
    codes.push(BigInt(r.global_atom_code));weights.push(w);moments.push(m);
  }
  for(let i=0;i<80;i++){
    let sum=0n;for(let j=0;j<80;j++)if((codes[i]&codes[j])===codes[i])sum+=weights[j];
    assert(sum===moments[i],"full individual moment equation");
  }
  const orbitWeights=prepared.orbits.map((o,k)=>{
    assert(o.orbit===k&&o.members.length===o.size,"orbit coverage");
    let sum=0n;
    for(const i of o.members){assert(weights[i]===weights[o.representative],"constant mass on root orbit");sum+=weights[i];}
    assert(sum===BigInt(result.orbit_weights[k]),"total orbit mass");return sum;
  });
  for(let i=0;i<19;i++){
    const row=prepared.quotient_coefficients[i];assert(row.length===19,"quotient row size");
    const value=row.reduce((s,a,j)=>s+BigInt(a)*orbitWeights[j],0n);
    assert(value===BigInt(prepared.orbits[i].size)*moments[prepared.orbits[i].representative],"all quotient equations");
  }
  assert(codes[0]===0n&&moments[0]===6n*BigInt(counts[49])&&moments[0]===11975040n,"root normalization");
  assert(BigInt(result.labelled_root_mass)===moments[0]&&weights.reduce((s,x)=>s+x,0n)===moments[0],"total mass");
  assert(result.negative_atoms===0&&result.negative_certificates.length===0&&!result.optimizer_called,"scope");
  function gcd(a,b){while(b)[a,b]=[b,a%b];return a;}
  const divisor=weights.reduce((g,w)=>gcd(g,w),moments[0]);
  return {
    status:"INDEPENDENT_ARTIFACT_ARITHMETIC_REPLAY_PASS",source_git_blob:sourceGitBlob,
    bindings:expected,root_type:49,individual_equations:80,quotient_equations:19,
    nonnegative_integer_atom_masses:80,positive_atom_masses:weights.filter(x=>x>0n).length,
    zero_atom_masses:weights.filter(x=>x===0n).length,
    labelled_root_mass:moments[0].toString(),mass_common_gcd:divisor.toString(),
    normalized_probability_common_denominator:(moments[0]/divisor).toString(),
    literal_graph_or_tensor_rebuilt:false,preparation_proof_reused:true,
    optimizer_called:false,graph_existence_claimed:false
  };
}

if (typeof module !== "undefined" && module.exports) {
  module.exports={replayRoot49Distribution};
  if (require.main === module) {
    const fs=require("fs"),crypto=require("crypto");
    function blob(path){const b=fs.readFileSync(path);return crypto.createHash("sha1").update("blob "+b.length+"\0").update(b).digest("hex");}
    const [prepPath,pointPath,resultPath]=process.argv.slice(2);
    if(!prepPath||!pointPath||!resultPath)throw Error("Usage: node replay.js preparation.json point.json result.json");
    if(blob(prepPath)!=="051d30abea64b1e4060e51f103c619844ba864e7"||blob(pointPath)!=="c881dae3be05cf289fcc45a99d72c405ac863c46"||blob(resultPath)!=="1b80dd8bc11ac4e396d987431fd93e56f9a04eb1")throw Error("Input blob binding");
    const read=p=>JSON.parse(fs.readFileSync(p,"utf8"));
    console.log(JSON.stringify(replayRoot49Distribution(read(prepPath),read(pointPath),read(resultPath),blob(__filename)),null,2));
  }
}
