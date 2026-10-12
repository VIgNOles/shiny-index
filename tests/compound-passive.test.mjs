import assert from 'node:assert/strict';
import test from 'node:test';
import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {detailSearch,detailMatches} from '../web/details.mjs';

const site=process.env.COMPOUND_SITE?pathToFileURL(path.resolve(process.env.COMPOUND_SITE)+path.sep):new URL('../site/',import.meta.url);
const read=path=>JSON.parse(fs.readFileSync(new URL(path,site),'utf8'));
const base=read('data/latest.json').dataset_version;
const version=read('details/latest.json').detail_version;
const cards=read(`data/${base}/cards.json`).cards;
const details=new Map(read(`details/${version}/details.json`).cards.map(card=>[card.card_id,card]));

// Fixed expectations transcribed from the approved r21 source names, independently
// of numeric_facts and the search implementation. No private prose is distributed.
const present='44939583-5f1e-43cb-8782-615453e9d7a8';
const stellar='3755c28c-6c1b-435b-9c3d-f39be28e4485';
const rain='5fbc8433-104d-4a6e-8c4c-0efff770375c';
const mamimi='239011cd-7318-413d-9545-0fa8aa2766e9';
const smile='02b4da0b-818f-474a-a83d-6ef67913ca2d';
const water='291c5746-e533-4e4b-8225-ab306a64d420';
const natural='48e12199-d102-4a67-8d1a-0ed9891bb604';
const asterism='ce60aff6-b209-4566-a867-68fbf23d6f4f';
const fixtures=[
 [present,'72c69a4a-44e0-48d8-8c1c-fd61e4a0449b',[['Vocal',30,'UP'],['Dance',30,'UP'],['Visual',30,'UP']],20],
 [present,'4522bc79-d08c-4163-9d08-4a84372e1b84',[['Vocal',140,'UP']],25],
 [stellar,'5b4f59fd-98a0-4d39-8b4d-84daaa914bcf',[['Visual',60,'UP'],['Vocal',30,'UP'],['Dance',30,'UP']],30],
 [stellar,'3951e102-44f8-4914-8236-5dbb7e260b72',[['Visual',120,'UP'],['Vocal',100,'UP'],['Dance',100,'UP']],20],
 [stellar,'5f4ef220-b31a-4612-9744-0de9ac59c6eb',[['Visual',100,'UP'],['Vocal',50,'UP'],['Dance',50,'UP']],30],
 [rain,'4ff78f93-b9cd-4000-8c7d-dad3bee5bdb0',[['Vocal',33,'UP'],['Visual',33,'UP'],['注目度',20,'DOWN']],33],
 [mamimi,'0dc87b57-bd8b-4a00-8283-26d8b5a0830a',[['Dance',50,'UP'],['Vocal',10,'DOWN'],['Visual',10,'DOWN']],40],
 [smile,'63b78689-d858-4785-8822-ed36f11b62cd',[['Dance',40,'UP'],['Visual',40,'UP']],20],
 [water,'c8eb9767-0130-4d9d-a0c1-7821a6b99cee',[['Vocal',25,'UP'],['Dance',25,'UP'],['Visual',25,'UP']],20],
 [asterism,'57ce9fe7-2726-420e-9882-3ffb8055b02e',[['Dance',30,'UP'],['Vocal',10,'UP'],['Visual',10,'UP']],30],
 [natural,'fb79c677-1a32-4c0b-b60c-55eb67e84b87',[['Visual',10,'UP'],['メンタルダメージ',10,'UP'],['注目度',10,'UP']],20]
];
const sorted=rows=>rows.map(row=>[...row]).sort((a,b)=>JSON.stringify(a).localeCompare(JSON.stringify(b),'en'));
const itemFor=(cid,id)=>{
 const item=details.get(cid)?.items.find(item=>item.detail_id===id);
 assert.ok(item,`missing fixed source item ${cid}/${id}`);
 return item;
};
const query=(type,target,word)=>new URLSearchParams({skill_kind:'panel_passive',effect_type:type,effect_target:target,skill_q:word});

test('published compound passive facts retain each source attribute, its amount and direction',()=>{
 for(const [cid,id,expected,probability] of fixtures){
  const item=itemFor(cid,id);
  assert.equal(item.kind,'panel_passive');
  const actual=item.numeric_facts.filter(fact=>fact.metric==='rate').flatMap(fact=>(fact.targets??[fact.target]).map(target=>[target,fact.value,fact.direction]));
  assert.deepEqual(sorted(actual),sorted(expected),id);
  assert.deepEqual(item.numeric_facts.filter(fact=>fact.metric==='activation_probability').map(fact=>fact.value),[probability],id);
 }
});

test('fixed real cards are found through every compound attribute and exclude unrelated rates',()=>{
 const cases=[
  [present,'passive_up','Vocal','30%UP',true],
  [present,'passive_up','Dance','30%UP',true],
  [present,'passive_up','Visual','30%UP',true],
  [present,'passive_up','Vocal','140%UP',true],
  [present,'passive_up','Vocal','20%UP',false],
  [present,'passive_up','注目度','30%UP',false],
  [present,'passive_down','Vocal','30%DOWN',false],
  [stellar,'passive_up','Vocal','30%UP',true],
  [stellar,'passive_up','Dance','30%UP',true],
  [stellar,'passive_up','Visual','60%UP',true],
  [stellar,'passive_up','Vocal','60%UP',false],
  [stellar,'passive_up','Dance','60%UP',false],
  [stellar,'passive_up','Visual','30%UP',false],
  [stellar,'passive_up','Visual','50%UP',false],
  [stellar,'passive_up','Vocal','20%UP',false],
  [rain,'passive_up','Vocal','33%UP',true],
  [rain,'passive_up','Visual','33%UP',true],
  [rain,'passive_up','Dance','33%UP',false],
  [rain,'passive_down','注目度','20%DOWN',true],
  [rain,'passive_down','Vocal','20%DOWN',false],
  [rain,'passive_up','Vocal','50%UP',false],
  [smile,'passive_up','Dance','40%UP',true],
  [smile,'passive_up','Visual','40%UP',true],
  [smile,'passive_up','Vocal','40%UP',false],
  [water,'passive_up','Vocal','25%UP',true],
  [water,'passive_up','Dance','25%UP',true],
  [water,'passive_up','Visual','25%UP',true],
  [asterism,'passive_up','Vocal','10%UP',true],
  [asterism,'passive_up','Visual','10%UP',true],
  [asterism,'passive_up','Dance','30%UP',true],
  [asterism,'passive_up','Vocal','30%UP',false],
  [natural,'passive_up','メンタルダメージ','10%UP',true],
  [natural,'passive_up','注目度','10%UP',true]
 ];
 for(const [cid,type,target,word,expected] of cases){
  const card=cards.find(card=>card.card_id===cid);
  assert.ok(card,`missing fixed base card ${cid}`);
  assert.deepEqual(detailSearch([card],query(type,target,word),details).map(card=>card.card_id),expected?[cid]:[],`${cid}: ${type}/${target}/${word}`);
 }
});

test('same fixed passive never borrows another attribute amount, direction or activation probability',()=>{
 const cases=[
  [stellar,'5b4f59fd-98a0-4d39-8b4d-84daaa914bcf','passive_up','Vocal','30%UP',true],
  [stellar,'5b4f59fd-98a0-4d39-8b4d-84daaa914bcf','passive_up','Vocal','60%UP',false],
  [stellar,'3951e102-44f8-4914-8236-5dbb7e260b72','passive_up','Vocal','20%',false],
  [stellar,'5f4ef220-b31a-4612-9744-0de9ac59c6eb','passive_up','Visual','50%UP',false],
  [mamimi,'0dc87b57-bd8b-4a00-8283-26d8b5a0830a','passive_down','Vocal','10%DOWN',true],
  [mamimi,'0dc87b57-bd8b-4a00-8283-26d8b5a0830a','passive_down','Visual','10%DOWN',true],
  [mamimi,'0dc87b57-bd8b-4a00-8283-26d8b5a0830a','passive_up','Vocal','50%UP',false],
  [mamimi,'0dc87b57-bd8b-4a00-8283-26d8b5a0830a','passive_down','Dance','10%DOWN',false],
  [mamimi,'0dc87b57-bd8b-4a00-8283-26d8b5a0830a','passive_down','Vocal','40%',false],
  [rain,'4ff78f93-b9cd-4000-8c7d-dad3bee5bdb0','passive_down','注目度','33%',false],
  [present,'72c69a4a-44e0-48d8-8c1c-fd61e4a0449b','passive_up','Vocal','20%',false],
  [asterism,'57ce9fe7-2726-420e-9882-3ffb8055b02e','passive_up','Vocal','30%UP',false],
  [natural,'fb79c677-1a32-4c0b-b60c-55eb67e84b87','passive_up','Vocal','10%UP',false],
  [natural,'fb79c677-1a32-4c0b-b60c-55eb67e84b87','passive_up','メンタルダメージ','20%',false]
 ];
 for(const [cid,id,type,target,word,expected] of cases){
  const item=itemFor(cid,id);
  assert.equal(detailMatches({items:[item]},query(type,target,word)).length>0,expected,`${id}: ${type}/${target}/${word}`);
 }
});
test('keyword combinations follow an explicitly shared group rather than separate equal amounts',()=>{
 const shared=itemFor(present,'72c69a4a-44e0-48d8-8c1c-fd61e4a0449b');
 assert.equal(detailMatches({items:[shared]},query('passive_up','Vocal','Vocal Dance Visual30%UP')).length,1);
 const mixed=itemFor(stellar,'5b4f59fd-98a0-4d39-8b4d-84daaa914bcf');
 assert.equal(detailMatches({items:[mixed]},query('passive_up','Vocal','Vocal Dance30%UP')).length,1);
 for(const word of ['Vocal Dance60%UP','Visual Vocal30%UP'])
  assert.equal(detailMatches({items:[mixed]},query('passive_up','Vocal',word)).length,0,word);
 const separate={kind:'panel_passive',name:'Vocal30%UP / Dance30%UP',numeric_facts:[
  {metric:'rate',target:'Vocal',value:30,unit:'percent',direction:'UP'},
  {metric:'rate',target:'Dance',value:30,unit:'percent',direction:'UP'}
 ]};
 assert.equal(detailMatches({items:[separate]},query('passive_up','Vocal','Vocal Dance30%UP')).length,0);
 const overlapping={kind:'panel_passive',name:'Vocal & Dance30%UP / Vocal & Visual30%UP',numeric_facts:[
  {metric:'rate',target:'Vocal',value:30,unit:'percent',direction:'UP'},
  {metric:'rate',target:'Dance',value:30,unit:'percent',direction:'UP'},
  {metric:'rate',target:'Visual',value:30,unit:'percent',direction:'UP'}
 ]};
 assert.equal(detailMatches({items:[overlapping]},query('passive_up','Vocal','Dance Visual30%UP')).length,0);
});