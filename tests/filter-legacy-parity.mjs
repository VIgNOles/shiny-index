import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {detailSearch,effectNames,searchEffects} from '../web/details.mjs';
const root=path.resolve(process.argv[2]??'site');
const before=await import(pathToFileURL(path.resolve(process.argv[3])).href);
const bp=JSON.parse(await readFile(path.join(root,'data/latest.json'),'utf8'));
const dp=JSON.parse(await readFile(path.join(root,'details/latest.json'),'utf8'));
const basic=JSON.parse(await readFile(path.join(root,'data',bp.dataset_version,'cards.json'),'utf8'));
const detail=JSON.parse(await readFile(path.join(root,'details',dp.detail_version,'details.json'),'utf8'));
const map=new Map(detail.cards.map(c=>[c.card_id,c]));let cases=0;
for(const type of Object.keys(before.effectNames)){
 const casesForType=[new URLSearchParams({effect_type:type})];
 const effect=detail.cards.flatMap(c=>c.items.flatMap(i=>i.effect_details?.effects??[])).find(e=>before.effectMatches(e,casesForType[0]));
 if(effect?.targets?.[0])casesForType.push(new URLSearchParams({effect_type:type,effect_target:effect.targets[0]}));
 casesForType.push(new URLSearchParams({effect_type:type,effect_turns:'3'}));
 for(const params of casesForType){
  const old=before.detailSearch(basic.cards,params,map).map(c=>c.card_id),now=detailSearch(basic.cards,params,map).map(c=>c.card_id);assert.deepEqual(now,old,params.toString());cases++;
 }
 assert.ok(effectNames[type]);
}
console.log(JSON.stringify({legacy_types:Object.keys(before.effectNames).length,exact_card_sets:cases,base_version:bp.dataset_version,detail_version:dp.detail_version}));
