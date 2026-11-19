(() => {
"use strict";
function insist(ok,message){if(!ok)throw Error(message);}
function variableDomains(bytes) {
  insist(bytes instanceof Uint8Array,"Uint8Array required");
  const two63=1n<<63n,two64=1n<<64n,maxSafe=BigInt(Number.MAX_SAFE_INTEGER);
  function unsigned(state,end) {
    let v=0n;
    for(let k=0;k<10;++k) {
      insist(state.p<end,"truncated protobuf varint");
      const b=bytes[state.p++];
      if(k===9)insist(b<=1,"uint64 varint overflow");
      v|=BigInt(b&127)<<BigInt(7*k);
      if(!(b&128))return v;
    }
    throw Error("overlong protobuf varint");
  }
  function integer(state,end) {
    let v=unsigned(state,end);if(v>=two63)v-=two64;
    insist(v>=-maxSafe&&v<=maxSafe,"unsafe Number domain endpoint");
    return Number(v);
  }
  function sized(state,end) {
    const n=unsigned(state,end);
    insist(n<=BigInt(end-state.p),"truncated protobuf length");
    const stop=state.p+Number(n);return stop;
  }
  function skip(state,end,wire) {
    if(wire===0){unsigned(state,end);return;}
    if(wire===2){state.p=sized(state,end);return;}
    const n=wire===1?8:wire===5?4:0;insist(n>0&&state.p+n<=end,"unsupported/truncated protobuf wire");state.p+=n;
  }
  function tag(state,end) {
    const t=unsigned(state,end);insist(t>0n&&t<=0xffffffffn,"invalid protobuf tag");
    return [Number(t>>3n),Number(t&7n)];
  }
  function domain(start,end) {
    const state={p:start},values=[];
    while(state.p<end) {
      const [field,wire]=tag(state,end);
      if(field===1){insist(wire===2,"bad variable-name wire");state.p=sized(state,end);}
      else {
        insist(field===2&&(wire===0||wire===2),"unexpected variable field/wire");
        if(wire===0)values.push(integer(state,end));
        else {const stop=sized(state,end);while(state.p<stop)values.push(integer(state,stop));insist(state.p===stop,"packed domain boundary");}
      }
    }
    insist(values.length>=2&&values.length%2===0,"empty/odd domain");
    for(let i=0;i<values.length;i+=2) {
      insist(values[i]<=values[i+1],"empty interval");
      if(i)insist(values[i-1]+1<values[i],"overlapping or unmerged intervals");
    }
    return values;
  }
  const state={p:0},domains=[],topLevelFields={},forbiddenFields=[];
  let constraintCount=0;
  while(state.p<bytes.length) {
    const [field,wire]=tag(state,bytes.length);
    topLevelFields[field]=(topLevelFields[field]||0)+1;
    if(field===2) {
      insist(wire===2,"bad variable message wire");
      const stop=sized(state,bytes.length);
      domains.push(domain(state.p,stop));state.p=stop;
    } else if(field===3) {
      insist(wire===2,"bad constraint message wire");++constraintCount;state.p=sized(state,bytes.length);
    } else {
      if(field!==1)forbiddenFields.push(field);
      skip(state,bytes.length,wire);
    }
  }
  return {domains,variables:domains.length,constraint_messages:constraintCount,top_level_fields:topLevelFields,other_fields:forbiddenFields};
}
return {variableDomains};
})()
