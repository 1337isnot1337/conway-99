((P) => {
"use strict";
function insist(ok,message){if(!ok)throw Error(message);}
function enc(n){let v=BigInt(n);if(v<0n)v+=(1n<<64n);const a=[];do{let b=Number(v&127n);v>>=7n;if(v)b|=128;a.push(b);}while(v);return a;}
function message(field,payload){return [...enc(field*8+2),...enc(payload.length),...payload];}
function variable(values,packed=true){const p=packed?message(2,values.flatMap(enc)):values.flatMap(v=>[16,...enc(v)]);return message(2,p);}
const controls=[],rejections=[];
for(const packed of [false,true]){
 const data=Uint8Array.from([...variable([-6,-1,1,6],packed),...variable([0,0],packed),...message(3,[]),...message(3,[])]);
 const out=P.variableDomains(data);
 insist(JSON.stringify(out.domains)==="[[-6,-1,1,6],[0,0]]"&&out.constraint_messages===2,"valid protobuf control");
 controls.push({packed,pass:true});
}
function reject(label,b){let caught=false;try{P.variableDomains(Uint8Array.from(b));}catch(e){caught=true;}insist(caught,"bad protobuf accepted "+label);rejections.push(label);}
reject("truncated varint",[128]);
reject("uint64 overflow",Array(10).fill(255));
reject("odd domain",variable([0]));
reject("overlap",variable([0,3,2,5]));
reject("adjacent intervals",variable([0,1,2,3]));
reject("unsafe endpoint",variable([0,9007199254740992n]));
reject("bad variable wire",[16,0]);
reject("truncated message",[18,10,16,0]);
return {status:"PASS",controls,rejections,optimizer_calls:0};
})
