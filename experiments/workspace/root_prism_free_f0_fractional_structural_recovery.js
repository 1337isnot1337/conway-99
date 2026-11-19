"use strict";

// Exact structural preparation only. No optimizer, motif rows or terminal cut rows.
// Reusable pure functions and a standard-library Node replay entry point.

function sha256Ascii(text) {
  if ([...text].some(c=>c.charCodeAt(0)>127)) throw new Error("ASCII hash input required");
  const k=[0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2];
  let h=[0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19];
  const bytes=Array.from(text,c=>c.charCodeAt(0)), bits=bytes.length*8;
  bytes.push(128); while(bytes.length%64!==56)bytes.push(0);
  for(const part of [Math.floor(bits/4294967296),bits>>>0])for(let s=24;s>=0;s-=8)bytes.push(part>>>s&255);
  const rr=(x,n)=>(x>>>n)|(x<<(32-n));
  for(let off=0;off<bytes.length;off+=64){
    const w=Array(64).fill(0);
    for(let i=0;i<16;i++)w[i]=(bytes[off+4*i]<<24)|(bytes[off+4*i+1]<<16)|(bytes[off+4*i+2]<<8)|bytes[off+4*i+3];
    for(let i=16;i<64;i++){const a=w[i-15],b=w[i-2];w[i]=(w[i-16]+(rr(a,7)^rr(a,18)^(a>>>3))+w[i-7]+(rr(b,17)^rr(b,19)^(b>>>10)))|0;}
    let[a,b,c,d,e,f,g,z]=h;
    for(let i=0;i<64;i++){const t1=(z+(rr(e,6)^rr(e,11)^rr(e,25))+((e&f)^(~e&g))+k[i]+w[i])|0;const t2=((rr(a,2)^rr(a,13)^rr(a,22))+((a&b)^(a&c)^(b&c)))|0;z=g;g=f;f=e;e=(d+t1)|0;d=c;c=b;b=a;a=(t1+t2)|0;}
    h=h.map((v,i)=>(v+[a,b,c,d,e,f,g,z][i])|0);
  }
  return h.map(v=>(v>>>0).toString(16).padStart(8,"0")).join("");
}

function buildF0FractionalStructure(input) {
  const check=(ok,msg)=>{if(!ok)throw new Error(msg);};
  const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
  const hash=x=>sha256Ascii(JSON.stringify(x));
  const hist=xs=>{const r={};for(const x of xs)r[x]=(r[x]||0)+1;return r;};
  const range=n=>Array.from({length:n},(_,i)=>i);
  function pop(x){let n=0;while(x){x&=x-1;n++;}return n;}
  check(input.source_sha256==="7ab2ec935cdbbb7035a0fd95d5a7ca514aed508b7d5efbe953c5265176733589","published input binding");
  const core=input.component_core_rows;
  check(core.length===21&&core.every(x=>Number.isSafeInteger(x)&&x>=0&&x<2**21),"core range");
  for(let i=0;i<21;i++){check(!(core[i]>>i&1),"core loop");for(let j=0;j<21;j++)check((core[i]>>j&1)===(core[j]>>i&1),"core symmetry");}
  for(let i=0;i<3;i++)check(pop(core[i])===8,"central degree");
  const adj=core.slice(3).map(x=>x>>>3);
  for(let i=0;i<18;i++)check((core[i+3]&7)===(1<<Math.floor(i/6))&&pop(adj[i])===3,"component degree/fiber");
  const gram=range(18).map(i=>range(18).map(j=>12*Number(i===j)+2-pop(core[i+3]&core[j+3])-(core[i+3]>>(j+3)&1)));
  check(gram.every((r,i)=>r[i]===10),"Gram diagonal");
  const actions=input.component_actions;
  check(actions.length===12&&new Set(actions.map(x=>x.join(","))).size===12,"twelve actions");
  const coreActions=actions.map(move=>{
    check(same([...move].sort((a,b)=>a-b),range(18)),"component permutation");
    const fibers=range(3).map(f=>{
      const images=new Set(range(6).map(j=>Math.floor(move[6*f+j]/6)));
      check(images.size===1,"fiber map");return [...images][0];
    });
    check(same([...fibers].sort((a,b)=>a-b),range(3)),"central permutation");
    const full=[...fibers,...move.map(j=>j+3)];
    for(let i=0;i<21;i++)for(let j=0;j<21;j++)check((core[i]>>j&1)===(core[full[i]]>>full[j]&1),"full core action");
    return full;
  });
  const actionLookup=new Map(actions.map((x,i)=>[x.join(","),i]));
  const identity=actionLookup.get(range(18).join(","));check(identity!==undefined,"identity");
  const multiplication=actions.map(g=>actions.map(h=>{
    const ix=actionLookup.get(h.map(i=>g[i]).join(","));check(ix!==undefined,"group closure");return ix;
  }));
  const inverses=range(12).map(g=>{
    const h=multiplication[g].indexOf(identity);check(h>=0&&multiplication[h][g]===identity,"inverse");return h;
  });
  const triples=[],masks=[],targets=[];
  for(let a=0;a<18;a++)for(let b=a+1;b<18;b++)for(let c=b+1;c<18;c++){
    const h=[a,b,c],mask=(1<<a)|(1<<b)|(1<<c);
    if(range(3).some(f=>h.filter(i=>Math.floor(i/6)===f).length>2))continue;
    if(gram[a][b]===0||gram[a][c]===0||gram[b][c]===0)continue;
    const q=range(18).map(i=>2-Number(mask>>i&1)-pop(adj[i]&mask));
    if(q.some(v=>v<0))continue;
    check(q.every(v=>v<=2)&&q.reduce((x,y)=>x+y,0)===24,"mixed target");
    triples.push(h);masks.push(mask);targets.push(q);
  }
  const n=triples.length;check(n===480,"complete triple count");
  const tripleLookup=new Map(triples.map((h,a)=>[h.join(","),a]));
  const sigActions=actions.map(move=>triples.map(h=>{
    const a=tripleLookup.get(h.map(i=>move[i]).sort((a,b)=>a-b).join(","));check(a!==undefined,"triple transport");return a;
  }));
  for(let g=0;g<12;g++)for(let a=0;a<n;a++)for(let i=0;i<18;i++)check(targets[a][i]===targets[sigActions[g][a]][actions[g][i]],"mixed target transport");
  const edges=[],incident=range(n).map(()=>[]),edgeLookup=new Map();
  for(let a=0;a<n;a++)for(let b=a+1;b<n;b++){
    if(pop(masks[a]&masks[b])>1)continue;
    if(triples[b].some(i=>targets[a][i]===0)||triples[a].some(i=>targets[b][i]===0))continue;
    const e=edges.length;edges.push([a,b]);incident[a].push([b,e]);incident[b].push([a,e]);edgeLookup.set(n*a+b,e);
  }
  check(edges.length===68394,"complete eligible edges");
  const edgeActions=sigActions.map(move=>{
    const seen=new Uint8Array(edges.length);
    const result=edges.map(([a,b])=>{
      let x=move[a],y=move[b];if(x>y)[x,y]=[y,x];
      const e=edgeLookup.get(n*x+y);check(e!==undefined&&!seen[e],"edge transport/permutation");seen[e]=1;return e;
    });return result;
  });
  const mixedActions=sigActions.map((move,g)=>range(n*18).map(r=>18*move[Math.floor(r/18)]+actions[g][r%18]));
  const gramPairs=[];for(let i=0;i<18;i++)for(let j=i;j<18;j++)gramPairs.push([i,j]);
  const gpLookup=new Map(gramPairs.map((p,i)=>[p.join(","),i]));
  const gramActions=actions.map(move=>gramPairs.map(([i,j])=>{
    let a=move[i],b=move[j];if(a>b)[a,b]=[b,a];check(gram[i][j]===gram[a][b],"Gram transport");return gpLookup.get(a+","+b);
  }));
  function orbits(length,maps){
    const ids=Array(length).fill(-1),groups=[];
    for(let a=0;a<length;a++)if(ids[a]<0){
      const group=[...new Set(maps.map(p=>p[a]))].sort((x,y)=>x-y),id=groups.length;
      for(const b of group){check(ids[b]<0,"orbit overlap");ids[b]=id;}
      groups.push(group);
    }
    for(const p of maps)for(let a=0;a<length;a++)check(ids[p[a]]===ids[a],"orbit invariant");
    const fixed=maps.map(p=>p.reduce((s,b,a)=>s+Number(a===b),0));
    check(fixed.reduce((s,x)=>s+x,0)===12*groups.length,"Burnside equality");
    return {ids,groups,fixed};
  }
  const so=orbits(n,sigActions),eo=orbits(edges.length,edgeActions),mo=orbits(n*18,mixedActions),go=orbits(171,gramActions);
  check(so.groups.length===42&&same(hist(so.groups.map(x=>x.length)),{6:4,12:38}),"known selector orbits");
  const edgeFixedDirect=sigActions.map(p=>edges.reduce((s,[a,b])=>s+Number((p[a]===a&&p[b]===b)||(p[a]===b&&p[b]===a)),0));
  const mixedFixedDirect=sigActions.map((p,g)=>p.filter((b,a)=>a===b).length*actions[g].filter((b,a)=>a===b).length);
  check(same(edgeFixedDirect,eo.fixed)&&same(mixedFixedDirect,mo.fixed),"independent fixed-point counts");
  const nx=so.groups.length,ny=eo.groups.length,nv=nx+ny;
  const add=(m,j,v)=>{m.set(j,(m.get(j)||0)+v);};
  const terms=m=>[...m.entries()].filter(([,v])=>v!==0).sort((a,b)=>a[0]-b[0]);
  const mixedRows=[],mixedRowIds=[],mixedRowLookup=new Map();
  for(let a=0;a<n;a++){
    const rows=range(18).map(()=>new Map());
    for(let i=0;i<18;i++)add(rows[i],so.ids[a],-targets[a][i]);
    for(const[b,e]of incident[a])for(const i of triples[b])add(rows[i],nx+eo.ids[e],1);
    const total=new Map();for(const row of rows)for(const[j,c]of row)add(total,j,c);
    const degree=new Map();add(degree,so.ids[a],-24);for(const[,e]of incident[a])add(degree,nx+eo.ids[e],3);
    check(same(terms(total),terms(degree)),"degree redundancy, literal quotient");
    for(const row of rows){
      const t=terms(row),key=JSON.stringify(t);
      if(!mixedRowLookup.has(key)){mixedRowLookup.set(key,mixedRows.length);mixedRows.push(t);}
      mixedRowIds.push(mixedRowLookup.get(key));
    }
  }
  for(const group of mo.groups)check(new Set(group.map(i=>mixedRowIds[i])).size===1,"mixed orbit literal quotient");
  const gramRows=[],gramRowIds=[],gramRowLookup=new Map();
  for(const[i,j]of gramPairs){
    const row=new Map();for(let a=0;a<n;a++)if((masks[a]>>i&1)&&(masks[a]>>j&1))add(row,so.ids[a],1);
    const full={terms:terms(row),rhs:gram[i][j]},key=JSON.stringify(full);
    if(!gramRowLookup.has(key)){gramRowLookup.set(key,gramRows.length);gramRows.push(full);}
    gramRowIds.push(gramRowLookup.get(key));
  }
  for(const group of go.groups)check(new Set(group.map(i=>gramRowIds[i])).size===1,"Gram orbit literal quotient");
  const activationRows=[],activationLookup=new Map(),activationIds=[];
  for(let e=0;e<edges.length;e++)for(const a of edges[e]){
    const row=[[so.ids[a],-1],[nx+eo.ids[e],1]],key=JSON.stringify(row);
    if(!activationLookup.has(key)){activationLookup.set(key,activationRows.length);activationRows.push(row);}
    activationIds.push(activationLookup.get(key));
  }
  for(let e=0;e<edges.length;e++){
    const representative=edges[eo.groups[eo.ids[e]][0]];
    check(same(edges[e].map(a=>so.ids[a]).sort((a,b)=>a-b),representative.map(a=>so.ids[a]).sort((a,b)=>a-b)),"edge orbit endpoint types");
  }
  const population=so.groups.map((group,i)=>[i,group.length]);
  let literalChecks=0;
  for(let control=0;control<4;control++){
    const z=range(nv).map(j=>(17*j+11+13*control)%23);
    for(let a=0;a<n;a++)for(let i=0;i<18;i++){
      let direct=-targets[a][i]*z[so.ids[a]];
      for(const[b,e]of incident[a])if(masks[b]>>i&1)direct+=z[nx+eo.ids[e]];
      const quotient=mixedRows[mixedRowIds[18*a+i]].reduce((s,[j,c])=>s+c*z[j],0);
      check(direct===quotient,"literal mixed evaluation");literalChecks++;
    }
    for(let p=0;p<gramPairs.length;p++){
      const[i,j]=gramPairs[p];let direct=0;
      for(let a=0;a<n;a++)if((masks[a]>>i&1)&&(masks[a]>>j&1))direct+=z[so.ids[a]];
      const quotient=gramRows[gramRowIds[p]].terms.reduce((s,[j,c])=>s+c*z[j],0);
      check(direct===quotient,"literal Gram evaluation");literalChecks++;
    }
    for(let e=0;e<edges.length;e++)for(let endpoint=0;endpoint<2;endpoint++){
      const direct=z[nx+eo.ids[e]]-z[so.ids[edges[e][endpoint]]];
      const quotient=activationRows[activationIds[2*e+endpoint]].reduce((s,[j,c])=>s+c*z[j],0);
      check(direct===quotient,"literal activation evaluation");literalChecks++;
    }
  }
  const nonzeroMixed=mixedRows.filter(r=>r.length>0);
  const nonzeroGram=gramRows.filter(r=>r.terms.length>0||r.rhs!==0);
  const spec={core,core_actions:coreActions,group_multiplication:multiplication,group_inverses:inverses,triples,targets,edges,selector_orbits:so.groups,edge_orbits:eo.groups,mixed_row_orbits:mo.groups,gram_row_orbits:go.groups,mixed_rows:mixedRows,mixed_row_ids:mixedRowIds,gram_rows:gramRows,gram_row_ids:gramRowIds,activation_rows:activationRows,activation_ids:activationIds,population};
  const report={
    status:"PASS: exact structural quotient prepared; no cuts, motifs, optimizer or feasibility claim",
    input_git_blob:"fbe9445d9f247fbbfbaccff367b0ff05afb2442a",
    published_source_sha256:input.source_sha256,
    counts:{core_vertices:21,component_vertices:18,triples:n,eligible_edges:edges.length,full_variables:n+edges.length,group_order:12,selector_orbits:nx,edge_orbits:ny,quotient_variables:nv,full_mixed_rows:n*18,mixed_row_orbits:mo.groups.length,distinct_literal_mixed_rows:mixedRows.length,nonzero_literal_mixed_rows:nonzeroMixed.length,full_gram_rows:171,gram_row_orbits:go.groups.length,distinct_literal_gram_rows:gramRows.length,nonzero_literal_gram_rows:nonzeroGram.length,full_activation_rows:2*edges.length,distinct_literal_activation_rows:activationRows.length},
    orbit_size_histograms:{selectors:hist(so.groups.map(x=>x.length)),edges:hist(eo.groups.map(x=>x.length)),mixed_rows:hist(mo.groups.map(x=>x.length)),gram_rows:hist(go.groups.map(x=>x.length))},
    burnside_fixed_points:{selectors:so.fixed,edges:eo.fixed,mixed_rows:mo.fixed,gram_rows:go.fixed},
    core_degree_histogram:hist(core.map(pop)),
    eligible_degree_histogram:hist(incident.map(x=>x.length)),
    mixed_target_histogram:hist(targets.flat()),
    matrix_nonzeros:{mixed_nonzero_rows:nonzeroMixed.reduce((s,r)=>s+r.length,0),gram_nonzero_rows:nonzeroGram.reduce((s,r)=>s+r.terms.length,0),activation_rows:activationRows.length*2,population:nx},
    integer_controls:{literal_full_to_quotient_row_evaluations:literalChecks,test_denominator:23,all_480_degree_redundancy_checks:true,all_144_group_compositions_checked:true,full_21_core_actions_checked:true,independent_edge_and_mixed_Burnside_counts_checked:true},
    bindings:{core_and_actions_sha256:hash([core,coreActions]),triples_sha256:hash(triples),targets_sha256:hash(targets),edges_sha256:hash(edges),selector_orbits_sha256:hash(so.groups),edge_orbits_sha256:hash(eo.groups),mixed_row_orbits_sha256:hash(mo.groups),literal_mixed_rows_sha256:hash(mixedRows),mixed_row_map_sha256:hash(mixedRowIds),literal_gram_rows_sha256:hash(gramRows),literal_activation_rows_sha256:hash(activationRows),activation_row_map_sha256:hash(activationIds),structural_specification_sha256:hash(spec)},
    scope:{motif_rows_added:false,terminal_4404_cuts_added:false,full_fractional_model_complete:false,optimizer_called:false,feasible_point_found:false,component_excluded:false}
  };
  return {report,specification:spec};
}

function checkHashControls() {
  const tests = [
    ["", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"],
    ["abc", "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"],
    ["abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq",
      "248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1"]
  ];
  for (const [text, expected] of tests) {
    if (sha256Ascii(text) !== expected) throw new Error("SHA256 control");
  }
  return tests.length;
}

if (typeof module !== "undefined") {
  module.exports = {buildF0FractionalStructure, sha256Ascii, checkHashControls};
}
if (typeof require !== "undefined" && require.main === module) {
  const fs = require("node:fs"), path = require("node:path"), crypto = require("node:crypto");
  const root = path.resolve(__dirname, "../..");
  const inputPath = process.argv[2] || path.join(root,
    "experiments/logs/root-prism-free/f0-fractional-structural-recovery-input.json");
  const raw = fs.readFileSync(inputPath);
  const blob = crypto.createHash("sha1").update("blob " + raw.length + "\0").update(raw).digest("hex");
  if (blob !== "fbe9445d9f247fbbfbaccff367b0ff05afb2442a") {
    throw new Error("literal input Git blob mismatch");
  }
  const hashControls = checkHashControls();
  const built = buildF0FractionalStructure(JSON.parse(raw.toString("utf8")));
  const native = crypto.createHash("sha256").update(JSON.stringify(built.specification)).digest("hex");
  if (native !== built.report.bindings.structural_specification_sha256) {
    throw new Error("native and portable specification hashes disagree");
  }
  built.report.hash_controls = hashControls;
  built.report.source_path = "experiments/workspace/root_prism_free_f0_fractional_structural_recovery.js";
  built.report.source_sha256 = crypto.createHash("sha256").update(fs.readFileSync(__filename)).digest("hex");
  built.report.literal_input_sha256 = crypto.createHash("sha256").update(raw).digest("hex");
  process.stdout.write(JSON.stringify(built.report, null, 2) + "\n");
}
