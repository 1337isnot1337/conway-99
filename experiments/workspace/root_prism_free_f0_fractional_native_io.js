"use strict";

// Hash-bound exact export and independent BigInt certificate replay.

function parseExactInteger(value) {
  if(typeof value==="number"){if(!Number.isSafeInteger(value))throw new Error("unsafe exact integer");return BigInt(value);}
  if(typeof value!=="string"||!/^(-?(0|[1-9][0-9]*))$/.test(value))throw new Error("integer string required");
  return BigInt(value);
}

function evaluateNativeFarkas(matrix,certificate) {
  const n=matrix.variables;
  if(certificate.equality_multipliers.length!==matrix.equalities.length||
     certificate.inequality_multipliers.length!==matrix.inequalities.length)throw new Error("multiplier dimensions");
  const lambda=certificate.equality_multipliers.map(parseExactInteger);
  const mu=certificate.inequality_multipliers.map(parseExactInteger);
  if(mu.some(x=>x<0n))throw new Error("negative inequality multiplier");
  const combined=Array(n).fill(0n);let rhs=0n;
  function add(rows,multipliers){rows.forEach((row,i)=>{
    const t=multipliers[i];rhs+=t*BigInt(row.rhs);
    for(const[j,c]of row.terms)combined[j]+=t*BigInt(c);
  });}
  add(matrix.equalities,lambda);add(matrix.inequalities,mu);
  const upperDeficit=combined.reduce((s,c)=>s+(c<0n?-c:0n),0n);
  const gap=rhs+upperDeficit;
  return {rhs:String(rhs),upper_deficit_sum:String(upperDeficit),gap:String(gap),
    strict_infeasibility:gap<0n,variables:n,
    equality_rows:lambda.length,inequality_rows:mu.length};
}

function nativeIoControls() {
  const check=(ok,m)=>{if(!ok)throw new Error(m);};
  const model={variables:2,equalities:[{terms:[[0,1],[1,1]],rhs:1}],inequalities:[{terms:[[0,1],[1,-1]],rhs:0}]};
  let tested=0;
  for(let l=-8;l<=8;l++)for(let u=0;u<=8;u++){
    const value=evaluateNativeFarkas(model,{equality_multipliers:[l],inequality_multipliers:[u]});
    check(BigInt(value.gap)>=0n,"feasible box cannot have a strict ray");tested++;
  }
  const equalityBad={variables:2,equalities:[{terms:[[0,1],[1,1]],rhs:3}],inequalities:[]};
  check(evaluateNativeFarkas(equalityBad,{equality_multipliers:[-1],inequality_multipliers:[]}).gap==="-1","equality ray sign");
  const inequalityBad={variables:1,equalities:[],inequalities:[{terms:[[0,1]],rhs:-1}]};
  check(evaluateNativeFarkas(inequalityBad,{equality_multipliers:[],inequality_multipliers:[1]}).gap==="-1","inequality ray sign");
  let rejected=false;try{evaluateNativeFarkas(model,{equality_multipliers:[0],inequality_multipliers:[-1]});}catch(e){rejected=true;}
  check(rejected,"negative multiplier rejection");
  const large=1n<<130n;
  check(evaluateNativeFarkas(equalityBad,{equality_multipliers:[String(-large)],inequality_multipliers:[]}).gap===String(-large),"large exact ray");
  return {status:"PASS: exact finite-box certificate controls",feasible_box_multiplier_checks:tested,strict_infeasible_controls:3,negative_inequality_multiplier_rejected:true,largest_multiplier_bits:131,optimizer_calls:0};
}

const MODEL_SHA256 = "a30179bd5b2b7c58bb5458a3371a947997da17288a355452469d47a59ab81413";
const MATRIX_SHA256 = "30bd8808dcd0490fa9ae124abb2ef060cfc8bfcbc57b78eaac0a67fe89f0dd55";
const VALIDATION_SHA256 = "baeeafa1485d9b9eadb4b62584b7e5c055ee7ce71a3c68a4a01f3df8b6f2743d";
if(typeof module!=="undefined")module.exports={evaluateNativeFarkas,nativeIoControls};
if(typeof require!=="undefined"&&require.main===module){
  const fs=require("node:fs"),path=require("node:path"),crypto=require("node:crypto");
  const check=(ok,m)=>{if(!ok)throw new Error(m);};
  const canonical=x=>JSON.stringify(x);
  const sha=raw=>crypto.createHash("sha256").update(raw).digest("hex");
  const jsonHash=x=>sha(canonical(x));
  const args=process.argv.slice(2),mode=args[0];
  function writeFresh(p,data){check(!fs.existsSync(p),"fresh output required");fs.mkdirSync(path.dirname(p),{recursive:true});fs.writeFileSync(p,JSON.stringify(data,null,2)+"\n");}
  function readBound(p,expected){const raw=fs.readFileSync(p);const blob=crypto.createHash("sha1").update("blob "+raw.length+"\0").update(raw).digest("hex");check(blob===expected,"literal input binding");return JSON.parse(raw.toString("utf8"));}
  function modules(){
    const names=[
      ["root_prism_free_f0_fractional_structural_recovery.js","0a1beefc85a807d5073676b0de380ff714d855e8a9a84c8e6010786a18e39b2b"],
      ["root_prism_free_f0_fractional_baseline_recovery.js","2c7f4cf9965426d97eb025793d5912d2b51cc56dc9fced76fd66219333263af1"]
    ];
    return names.map(([name,digest])=>{const p=path.join(__dirname,name);check(sha(fs.readFileSync(p))===digest,"frozen model source");return require(p);});
  }
  if(mode==="controls"){
    check(args.length===2,"controls output.json");
    const report=nativeIoControls();report.source_sha256=sha(fs.readFileSync(__filename));writeFresh(args[1],report);
  }else if(mode==="export"){
    check(args.length===5,"export structural-input.json motif-input.json interior-certificate.json output-directory");
    const[structural,baseline]=modules();
    const core=readBound(args[1],"fbe9445d9f247fbbfbaccff367b0ff05afb2442a");
    const motif=readBound(args[2],"41b0f73b9f6a0061d49859fbd4e32564cea2db17");
    const interior=readBound(args[3],"6396da7dd3d5fd1df30a88cc3ea847154d62ef38");
    structural.checkHashControls();
    const built=structural.buildF0FractionalStructure(core),s=built.specification;
    const completed=baseline.completeF0FractionalBaseline(s,motif,structural.sha256Ascii),b=completed.specification;
    const positiveControl=baseline.checkF0BaselineInteriorProjection(s,b,interior);
    const validation={core:s.core,triples:s.triples,targets:s.targets,edges:s.edges,selector_orbits:s.selector_orbits,edge_orbits:s.edge_orbits,motif_pairs:b.motif_pairs};
    const payload={
      schema:"conway99.f0-fractional-native-model.v1",
      matrix:b.matrix,
      validation,
      bindings:{structural_specification_sha256:"5b2a8715c9cad3217b72479dd12c733f5b8b73d878cbb70df154167b7e386525",baseline_specification_sha256:"32172068b93386040b2c3ef0a351d44cfb57484f3ad335ad28f9760516efe1bf",matrix_sha256:MATRIX_SHA256,validation_sha256:VALIDATION_SHA256},
      scope:{joint_baseline:true,fixed_selector_point:false,terminal_selector_registry_included:false,earlier_12_weighted_rows_included:false,conditional_component_zero:true}
    };
    check(jsonHash(payload.matrix)===MATRIX_SHA256&&jsonHash(validation)===VALIDATION_SHA256&&jsonHash(payload)===MODEL_SHA256,"literal native payload");
    const destination=path.join(args[4],"model.json");check(!fs.existsSync(destination),"fresh native model");
    fs.mkdirSync(args[4],{recursive:true});fs.writeFileSync(destination,canonical(payload)+"\n");
    writeFresh(path.join(args[4],"io-controls.json"),nativeIoControls());
    writeFresh(path.join(args[4],"export.json"),{
      status:"PASS: exact joint baseline exported; no optimizer",
      source_sha256:sha(fs.readFileSync(__filename)),
      model_canonical_sha256:MODEL_SHA256,model_file_sha256:sha(fs.readFileSync(destination)),
      model_file_bytes:fs.statSync(destination).size,matrix_sha256:MATRIX_SHA256,validation_sha256:VALIDATION_SHA256,
      variables:5847,equalities:686,inequalities:11373,nonzeros:57801,
      positive_selector_projection_control:positiveControl,
      terminal_selector_cut_registry_included:false,optimizer_called:false
    });
  }else if(mode==="replay"){
    check(args.length===4,"replay model.json exact.json output.json");
    const[,baseline]=modules();
    const payload=JSON.parse(fs.readFileSync(args[1],"utf8")),exact=JSON.parse(fs.readFileSync(args[2],"utf8"));
    check(jsonHash(payload)===MODEL_SHA256&&jsonHash(payload.matrix)===MATRIX_SHA256&&jsonHash(payload.validation)===VALIDATION_SHA256,"native model replay binding");
    check(exact.model_sha256===MODEL_SHA256,"certificate model binding");
    let report;
    if(exact.kind==="point"){
      check(!exact.certificate,"one certificate kind");
      const result=baseline.inspectF0FractionalBaseline(payload.validation,{motif_pairs:payload.validation.motif_pairs,matrix:payload.matrix},exact.point);
      check(result.status==="PASS: exact fractional baseline point","full primary rational replay");
      report={status:"PASS: independent exact full-row fractional point replay",exact_feasible_baseline:true,exact_infeasible_baseline:false,check:result};
    }else if(exact.kind==="farkas"){
      check(!exact.point,"one certificate kind");
      const result=evaluateNativeFarkas(payload.matrix,exact.certificate);
      check(result.strict_infeasibility,"strict exact finite-box gap");
      report={status:"PASS: independent exact quotient Farkas replay",exact_feasible_baseline:false,exact_infeasible_baseline:true,check:result,
        full_model_implication:"Uses the separately checked complete twelve-map averaging and literal quotient proof"};
    }else{
      check(exact.kind==="unresolved"&&!exact.point&&!exact.certificate,"explicit unresolved record");
      report={status:"UNRESOLVED: no exact point or Farkas certificate to replay",exact_feasible_baseline:false,exact_infeasible_baseline:false};
    }
    report.source_sha256=sha(fs.readFileSync(__filename));report.model_sha256=MODEL_SHA256;
    report.certificate_file_sha256=sha(fs.readFileSync(args[2]));report.optimizer_called=false;
    writeFresh(args[3],report);
  }else throw new Error("mode must be controls, export or replay");
}
