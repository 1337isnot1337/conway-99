(() => {
"use strict";
function need(x,m){if(!x)throw Error(m);}
function key(center,star){need(Number.isSafeInteger(center),"center integer");let last=-1;for(const e of star){need(Number.isSafeInteger(e)&&e>last,"sorted unique star");last=e;}return JSON.stringify([center,star]);}
function inclusion(star,mixed){return new Set(star).size===star.length&&star.every(e=>mixed.get(e)===1);}
function run(configurationText,codecText,sourceText,inventorySourceText){
 const started=Date.now(),c=eval(codecText),cfg=JSON.parse(configurationText);
 const tick=()=>need(Date.now()-started<10000,"ten-second exact-controls deadline");
 need(cfg.schema==="conway99.f0.four-star-channel-controls-configuration.v1","controls schema");
 need(cfg.maximum_ms===10000,"fixed bound");
 need(c.sha256(c.utf8(codecText))==="fbccc2396bfbe6085576f02468ef0acd23182445837c02abd5d05e00b9e87a00","codec");
 need(c.sha256(c.utf8(sourceText))===cfg.source.sha256&&c.gitBlob(c.utf8(sourceText))===cfg.source.git_blob,"controls source binding");
 need(c.sha256(c.utf8(inventorySourceText))===cfg.inventory_source.sha256&&c.gitBlob(c.utf8(inventorySourceText))===cfg.inventory_source.git_blob,"unexecuted inventory source binding");
 let gridPoints=0,feasibleOriginalRows=0,uniqueExtensions=0,booleanClauseCases=0,mixedPoints=0,mixedSubsets=0;
 for(const D of [1,2,4])for(let xb=0;xb<=D;xb++)for(let xc=0;xc<=D;xc++)
 for(let L=0;L<=xb;L++)for(let R=0;R<=xc;R++)for(let y=0;y<=Math.min(xb,xc);y++){
  tick();const p=xb-L,q=xc-R,old=y+L+R-xb-xc,fresh=y-p-q;
  need(p>=0&&p<=xb&&q>=0&&q<=xc,"quota-one residual bounds");
  need(old===fresh,"exact scaled integer identity");
  need((old>=-2*D&&old<=0)===(fresh>=-2*D&&fresh<=0),"same linear row domain");
  let extensions=0;
  for(let u=0;u<=D;u++)for(let v=0;v<=D;v++)if(u+L===xb&&v+R===xc){extensions++;need(u===p&&v===q,"same unique extension");}
  need(extensions===1,"exactly one box extension");uniqueExtensions++;gridPoints++;
  if(old<=0)feasibleOriginalRows++;
  if(D===1){need((fresh<=0)===(y===0||p===1||q===1),"Boolean three-literal clause");booleanClauseCases++;}
 }
 for(let mask=0;mask<16;mask++)for(let x=0;x<2;x++){
  const edges=[0,1,2,3].map(i=>(mask>>>i)&1);
  if(edges.reduce((a,b)=>a+b,0)!==x)continue;mixedPoints++;
  for(let subset=1;subset<16;subset++){
   const star=[0,1,2,3].filter(i=>(subset>>>i)&1),L=star.reduce((v,i)=>v+edges[i],0),p=x-L;
   need(p===0||p===1,"actual quota-one sum gives Boolean residual");
   need(inclusion(star,new Map([[0,1],[1,1],[2,1],[3,1]])),"coefficient-one support inclusion");mixedSubsets++;
  }
 }
 need(!inclusion([0,4],new Map([[0,1],[1,1]])),"absent mixed term rejected");
 need(!inclusion([0,1],new Map([[0,1],[1,2]])),"wrong coefficient rejected");
 need(!inclusion([0,0],new Map([[0,1]])),"duplicate star term rejected");
 const keys=[key(7,[11,13]),key(7,[11,13]),key(7,[11,17]),key(8,[11,13])];
 need(new Set(keys).size===3,"same center and exact support deduplication");
 const merged=new Map();[[keys[0],0],[keys[1],1],[keys[2],2],[keys[3],3]].forEach(([k,origin])=>{if(!merged.has(k))merged.set(k,[]);merged.get(k).push(origin);});
 need(JSON.stringify(merged.get(keys[0]))==="[0,1]","all merged origins retained");
 const edgeVariable=540+42,left=68934,right=68935,literals=[-edgeVariable-1,left,right];
 let literalCases=0;
 for(let mask=0;mask<8;mask++){
  const y=mask&1,p=(mask>>>1)&1,q=(mask>>>2)&1,values=new Map([[edgeVariable,y],[left,p],[right,q]]);
  const clause=literals.some(l=>l>=0?values.get(l)===1:values.get(-l-1)===0);
  need(clause===(y-p-q<=0),"native signed literal interpretation");literalCases++;
 }
 tick();
 const report={schema:"conway99.f0.four-star-channel-controls.v1",status:"PASS_EXACT_STAR_CHANNEL_IDENTITY_AND_DOMAIN_CONTROLS",
  source:cfg.source,inventory_source:cfg.inventory_source,configuration_sha256:c.sha256(c.utf8(configurationText)),
  exact_scaled_denominators:[1,2,4],grid_points:gridPoints,original_row_feasible_points:feasibleOriginalRows,
  unique_channel_extensions_checked:uniqueExtensions,boolean_clause_grid_points:booleanClauseCases,
  actual_quota_one_binary_points:mixedPoints,coefficient_one_subsets_checked:mixedSubsets,
  rejected_inclusion_mutations:3,exact_key_deduplication_and_all_origins_checked:true,native_literal_assignments:literalCases,
  no_floating_point_arithmetic_in_identities:true,inventory_factory_evaluated:false,inventory_main_calls:0,
  actual_case_data_read:false,native_model_builds:0,solver_calls:0,seconds_before_serialization:(Date.now()-started)/1000};
 const serialized=JSON.stringify(report)+"\n",elapsed=Date.now()-started;
 return {report,serialized,finalization:{status:elapsed<10000?"PASS_CONTROLS_AND_SERIALIZATION":"UNACCEPTED_CONTROLS_BOUND",
  elapsed_ms:elapsed,maximum_ms:10000,report_bytes:c.utf8(serialized).length,main_calls:1,inventory_main_calls:0}};
}
return {run};
})()
