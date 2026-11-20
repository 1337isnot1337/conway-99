/* Independent controls for the exact signed-radix utility.
 * Pure V8/Node-compatible IIFE; no model, optimizer, filesystem, or network.
 * The tiny auxiliary projection enumerates native rows directly and does not
 * call completeWitness/checkWitness to decide encoded feasibility.
 */
(() => {
  "use strict";
  const UTILITY_SHA256="e484e0e374e5579c75f3bfe9bdac2fa837acf75525d42d6c8f231a560856446c";
  function check(c,m){if(!c)throw Error(m);}
  function clone(x){return JSON.parse(JSON.stringify(x));}
  function scalar(row,bits,offset=0){
    let a=0n;for(const [id,c] of row.terms)a+=BigInt(c)*BigInt(bits[id-offset]);return a;
  }
  function bits(value,n){return Array.from({length:n},(_,i)=>(value>>i)&1);}
  function rowFrom(coefficients,rhs,offset=0){
    return {terms:coefficients.flatMap((c,i)=>c===0?[]:[[offset+i,String(c)]]),rhs:String(rhs)};
  }
  function rawNativeCount(e,binaryValues,tick,counts){
    const values=new Map();
    binaryValues.forEach((v,i)=>values.set(e.parameters.binaryOffset+i,BigInt(v)));
    let feasible=0,visited=0;
    function recurse(t){
      if(t===e.auxiliary_variables.length){
        tick();visited++;counts.bruteforce_auxiliary_assignments++;
        let ok=true;
        for(const row of e.linear_rows){
          let activity=0n;
          for(const [id,c] of row.terms){check(values.has(id),"raw unknown ID");activity+=BigInt(c)*values.get(id);}
          if(activity<BigInt(row.domain[0])||activity>BigInt(row.domain[1])){ok=false;break;}
        }
        if(ok)feasible++;
        return;
      }
      const v=e.auxiliary_variables[t];
      for(let n=BigInt(v.domain[0]);n<=BigInt(v.domain[1]);n++){
        values.set(v.id,n);recurse(t+1);
      }
      values.delete(v.id);
    }
    recurse(0);return {feasible,visited};
  }
  function runControls(utilitySource,options={}){
    const seconds=options.seconds===undefined?30:options.seconds;
    check(Number.isSafeInteger(seconds)&&seconds>=1&&seconds<=60,"control time limit");
    const start=Date.now(),deadline=start+1000*seconds;
    const U=eval(utilitySource);
    const counts={small_rows:0,small_boolean_assignments:0,small_satisfying_assignments:0,
      small_rejected_assignments:0,bruteforce_rows:0,bruteforce_boolean_assignments:0,
      bruteforce_auxiliary_assignments:0,bruteforce_unique_witnesses:0,
      large_rows:0,large_assignments:0,constant_rows:0,malformed_inputs_rejected:0,
      encoding_mutations_rejected:0,witness_mutations_rejected:0,wide_row_assignments:0};
    let phase="hash controls";
    const report={schema:"conway99.signed-radix-controls.v1",status:"RUNNING",
      utility_sha256:UTILITY_SHA256,scope:"synthetic utility controls only",
      actual_4416_rows_loaded:false,native_model_built:false,native_solver_calls:0,
      native_model_validator_executed:false,declared_seconds:seconds,counts};
    function tick(){if(Date.now()>deadline)throw Error("control deadline exceeded");}
    function reject(f,label){
      let threw=false;try{f();}catch(error){threw=true;check(error instanceof Error,"non-Error refusal");}
      check(threw,"mutation was accepted: "+label);
    }
    try{
      check(U.sha256(utilitySource)===UTILITY_SHA256,"utility source hash");
      check(U.sha256("")==="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855","SHA256 empty");
      check(U.sha256("abc")==="ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad","SHA256 abc");
      const E=U.bindSource(UTILITY_SHA256),smallLedger=[],bruteLedger=[];
      phase="complete small signed rows";
      for(const baseBits of [1,2])for(let a=-2;a<=2;a++)for(let b=-2;b<=2;b++)for(let c=-2;c<=2;c++)for(let rhs=-3;rhs<=3;rhs++){
        tick();const row=rowFrom([a,b,c],rhs),p={binaryCount:3,firstAux:3,baseBits,maxDigits:128};
        const e=E.encodeRow(row,p);check(E.verifyEncoding(e,row,p).status==="EXACT_ENCODING_VERIFIED","small verifier");
        counts.small_rows++;let accepted=0;
        for(let mask=0;mask<8;mask++){
          const x=bits(mask,3),expected=scalar(row,x)<=BigInt(rhs),w=E.completeWitness(e,x);
          counts.small_boolean_assignments++;
          if(expected){
            check(w.status==="EXACT_AUXILIARY_WITNESS"&&w.check.status==="EXACT_AUXILIARY_WITNESS_CHECKED","small satisfying witness");
            check(BigInt(w.check.slack)===BigInt(rhs)-scalar(row,x),"small exact slack");
            accepted++;counts.small_satisfying_assignments++;
          }else{
            check(w.status==="ORIGINAL_ROW_VIOLATED"&&w.auxiliary_values===null,"small false row");
            counts.small_rejected_assignments++;
          }
        }
        smallLedger.push([baseBits,a,b,c,rhs,e.digits,accepted]);
      }
      check(counts.small_rows===1750&&counts.small_boolean_assignments===14000,"small complete coverage");
      report.small_decision_ledger_sha256=U.sha256(U.canonical(smallLedger));
      phase="independent tiny auxiliary projection";
      for(const baseBits of [1,2])for(let a=-2;a<=2;a++)for(let b=-2;b<=2;b++)for(let rhs=-2;rhs<=2;rhs++){
        tick();const row=rowFrom([a,b],rhs),e=E.encodeRow(row,{binaryCount:2,firstAux:2,baseBits,maxDigits:128});
        if(e.digits>2)continue;
        counts.bruteforce_rows++;
        for(let mask=0;mask<4;mask++){
          const x=bits(mask,2),expected=scalar(row,x)<=BigInt(rhs);
          const actual=rawNativeCount(e,x,tick,counts);
          check(actual.feasible===(expected?1:0),"independent native projection mismatch");
          counts.bruteforce_boolean_assignments++;counts.bruteforce_unique_witnesses+=actual.feasible;
          bruteLedger.push([baseBits,a,b,rhs,mask,actual.feasible,actual.visited]);
        }
      }
      report.bruteforce_decision_ledger_sha256=U.sha256(U.canonical(bruteLedger));
      phase="large signed integers";
      const B=1n<<30n,K=151115862703648029875148n,T=(1n<<201n)+19n;
      const largeRows=[
        {terms:[[0,K.toString()]],rhs:(K-1n).toString()},
        {terms:[[0,(-K).toString()]],rhs:(-K).toString()},
        {terms:[[0,K.toString()],[1,(-K).toString()]],rhs:"0"},
        {terms:[[0,K.toString()],[1,(-K-B*B-17n).toString()],[2,T.toString()]],rhs:((1n<<150n)+31n).toString()},
        {terms:[[0,(-T).toString()],[1,(T+K).toString()],[2,(-K).toString()]],rhs:(-(1n<<130n)+7n).toString()},
        {terms:[[0,(-(B**3n)).toString()]],rhs:"0"},
        {terms:[[0,"1"]],rhs:(B**3n).toString()}
      ];
      report.large_cases=[];
      for(const row of largeRows){
        tick();const e=E.encodeRow(row,{binaryCount:3,firstAux:100,baseBits:30,maxDigits:128});
        E.verifyEncoding(e,row);counts.large_rows++;let positive=0;
        for(let mask=0;mask<8;mask++){
          const x=bits(mask,3),expected=scalar(row,x)<=BigInt(row.rhs),w=E.completeWitness(e,x);
          check((w.status==="EXACT_AUXILIARY_WITNESS")===expected,"large witness iff");
          counts.large_assignments++;if(expected)positive++;
        }
        report.large_cases.push({original_row_sha256:e.original_row_sha256,digits:e.digits,
          coefficient_bits:row.terms.map(x=>(BigInt(x[1])<0n?-BigInt(x[1]):BigInt(x[1])).toString(2).length),
          rhs_bits:(BigInt(row.rhs)<0n?-BigInt(row.rhs):BigInt(row.rhs)).toString(2).length,
          satisfying_assignments:positive,maximum_residual_absolute_bound:e.native_audit.maximum_residual_absolute_bound});
      }
      check(report.large_cases[5].digits===4&&report.large_cases[6].digits===4,"strict power boundary");
      report.supplied_large_coefficient={value:K.toString(),bits:K.toString(2).length};
      check(report.supplied_large_coefficient.bits===78,"reference coefficient bit length");
      phase="zero-variable constants";
      for(const baseBits of [1,2,30])for(let rhs=-5;rhs<=5;rhs++){
        const row={terms:[],rhs:String(rhs)},e=E.encodeRow(row,{binaryCount:0,firstAux:0,baseBits});
        E.verifyEncoding(e,row);const w=E.completeWitness(e,[]);
        check((w.status==="EXACT_AUXILIARY_WITNESS")===(rhs>=0),"constant row");
        counts.constant_rows++;
      }
      phase="literal offset and boundary IDs";
      const offsetRow={terms:[[17,"-9"],[19,"7"]],rhs:"-2"};
      const offsetEncoding=E.encodeRow(offsetRow,{binaryCount:3,binaryOffset:17,firstAux:30,baseBits:2});
      E.verifyEncoding(offsetEncoding,offsetRow);
      for(let mask=0;mask<8;mask++){
        const x=bits(mask,3),w=E.completeWitness(offsetEncoding,x);
        check((w.status==="EXACT_AUXILIARY_WITNESS")===(scalar(offsetRow,x,17)<=-2n),"offset witness");
      }
      phase="malformed original input refusals";
      const good={terms:[[0,"-17"],[1,"9"]],rhs:"-3"},p={binaryCount:2,firstAux:2,baseBits:2};
      const badInputs=[
        ["duplicate",()=>E.encodeRow({terms:[[0,"1"],[0,"2"]],rhs:"0"},p)],
        ["unsorted",()=>E.encodeRow({terms:[[1,"1"],[0,"2"]],rhs:"0"},p)],
        ["zero term",()=>E.encodeRow({terms:[[0,"0"]],rhs:"0"},p)],
        ["coefficient Number",()=>E.encodeRow({terms:[[0,17]],rhs:"0"},p)],
        ["rhs Number",()=>E.encodeRow({terms:[[0,"1"]],rhs:0},p)],
        ["Boolean ID",()=>E.encodeRow({terms:[[false,"1"]],rhs:"0"},p)],
        ["out of range ID",()=>E.encodeRow({terms:[[2,"1"]],rhs:"0"},p)],
        ["negative ID",()=>E.encodeRow({terms:[[-1,"1"]],rhs:"0"},p)],
        ["decimal zero sign",()=>E.encodeRow({terms:[[0,"1"]],rhs:"-0"},p)],
        ["decimal leading zero",()=>E.encodeRow({terms:[[0,"01"]],rhs:"0"},p)],
        ["fraction",()=>E.encodeRow({terms:[[0,"1.0"]],rhs:"0"},p)],
        ["base zero",()=>E.encodeRow(good,{...p,baseBits:0})],
        ["base above 30",()=>E.encodeRow(good,{...p,baseBits:31})],
        ["too many digits",()=>E.encodeRow(good,{...p,maxDigits:1})],
        ["overlapping IDs",()=>E.encodeRow(good,{...p,firstAux:1})],
        ["ID allocation overflow",()=>E.encodeRow(good,{...p,firstAux:2147483647})],
        ["nonliteral option",()=>E.encodeRow(good,{...p,secret:1})],
        ["more than 480 binary bits",()=>E.encodeRow(good,{...p,binaryCount:481,firstAux:481})]
      ];
      for(const [name,f] of badInputs){reject(f,name);counts.malformed_inputs_rejected++;}
      phase="independent encoding mutation refusals";
      const goodEncoding=E.encodeRow(good,p),mutations=[
        ["signed literal digit",e=>{e.linear_rows[0].terms.find(t=>t[0]===0)[1]="1";}],
        ["outgoing carry sign",e=>{e.linear_rows[0].terms.find(t=>t[1]==="-4")[1]="4";}],
        ["incoming carry sign",e=>{e.linear_rows[1].terms.find(t=>t[0]===5)[1]="-1";}],
        ["slack sign",e=>{e.linear_rows[0].terms.find(t=>t[0]===2)[1]="-1";}],
        ["slack lower",e=>{e.auxiliary_variables[0].domain[0]="-1";}],
        ["slack upper",e=>{e.auxiliary_variables[0].domain[1]="4";}],
        ["carry lower",e=>{e.auxiliary_variables[3].domain[0]="-5";}],
        ["carry upper",e=>{e.auxiliary_variables[3].domain[1]="5";}],
        ["carry alias",e=>{e.auxiliary_variables[3].id=0;}],
        ["rhs sign",e=>{e.linear_rows[0].domain=["3","3"];}],
        ["rhs unequal bounds",e=>{e.linear_rows[0].domain[1]="-2";}],
        ["missing first slack",e=>{e.linear_rows[0].terms=e.linear_rows[0].terms.filter(t=>t[0]!==2);}],
        ["nonzero initial carry",e=>{e.linear_rows[0].terms.push([99,"1"]);}],
        ["nonzero terminal carry",e=>{e.linear_rows[2].terms.push([99,"-4"]);}],
        ["extra terminal carry variable",e=>{e.auxiliary_variables.push({id:7,kind:"carry",limb:3,domain:["-4","4"]});}],
        ["duplicate native term",e=>{e.linear_rows[0].terms.unshift(clone(e.linear_rows[0].terms[0]));}],
        ["truncated high row",e=>{e.linear_rows.pop();}],
        ["wrong original coefficient",e=>{e.original_row.terms[0][1]="-18";}],
        ["wrong source hash",e=>{e.source_sha256="0".repeat(64);}],
        ["wrong audit bound",e=>{e.native_audit.new_variable_domain_sum="0";}],
        ["native digit equals base",e=>{e.linear_rows[0].terms.find(t=>t[0]===1)[1]="4";}],
        ["noncanonical decimal",e=>{e.linear_rows[0].terms.find(t=>t[0]===1)[1]="01";}]
      ];
      for(const [name,mutate] of mutations){
        const e=clone(goodEncoding);mutate(e);reject(()=>E.verifyEncoding(e,good,p),name);
        counts.encoding_mutations_rejected++;
      }
      phase="witness mutation refusals";
      const witness=E.completeWitness(goodEncoding,[1,0]);
      const a=clone(witness.auxiliary_values);a[0][1]=(BigInt(a[0][1])+1n).toString();
      const b=clone(witness.auxiliary_values);b[3][1]=(BigInt(b[3][1])+1n).toString();
      const c=clone(witness.auxiliary_values);c[0][1]="-1";
      const badWitnesses=[
        ["slack digit",()=>E.checkWitness(goodEncoding,[1,0],a)],
        ["carry value",()=>E.checkWitness(goodEncoding,[1,0],b)],
        ["negative slack",()=>E.checkWitness(goodEncoding,[1,0],c)],
        ["different input",()=>E.checkWitness(goodEncoding,[0,0],witness.auxiliary_values)],
        ["Boolean bit",()=>E.checkWitness(goodEncoding,[true,0],witness.auxiliary_values)],
        ["fractional bit",()=>E.checkWitness(goodEncoding,[0.5,0],witness.auxiliary_values)],
        ["missing auxiliary",()=>E.checkWitness(goodEncoding,[1,0],witness.auxiliary_values.slice(1))]
      ];
      for(const [name,f] of badWitnesses){reject(f,name);counts.witness_mutations_rejected++;}
      phase="480-term arithmetic bounds";
      const big=B*B-1n,wide={terms:Array.from({length:480},(_,i)=>[i,(i%2?-big:big).toString()]),rhs:(B-1n).toString()};
      const wideEncoding=E.encodeRow(wide,{binaryCount:480,firstAux:480,baseBits:30});
      E.verifyEncoding(wideEncoding,wide);
      for(const x of [Array(480).fill(0),Array(480).fill(1),
        Array.from({length:480},(_,i)=>i%2),Array.from({length:480},(_,i)=>1-i%2)]){
        const w=E.completeWitness(wideEncoding,x);
        check((w.status==="EXACT_AUXILIARY_WITNESS")===(scalar(wide,x)<=B-1n),"wide witness");
        counts.wide_row_assignments++;
      }
      check(BigInt(wideEncoding.native_audit.universal_residual_bound)===964n*B,"480-term residual bound");
      check(BigInt(wideEncoding.native_audit.universal_residual_bound)<1n<<40n,"residual under 2^40");
      report.wide_row={digits:wideEncoding.digits,native_audit:wideEncoding.native_audit};
      tick();report.status="PASS: complete declared synthetic radix controls";
      report.small_boolean_domain_complete=true;report.tiny_auxiliary_projection_complete=true;
      report.auxiliary_witness_unique_in_all_bruteforce_controls=true;
      report.phase="complete";
    }catch(error){
      report.status="INCOMPLETE_OR_FAILED: no complete control claim";report.phase=phase;
      report.error={name:error.name,message:error.message};
    }
    report.elapsed_milliseconds=Date.now()-start;
    return report;
  }
  return Object.freeze({utility_sha256:UTILITY_SHA256,runControls});
})()
