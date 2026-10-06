import fs from 'node:fs/promises';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';
const [specPath,out]=process.argv.slice(2);
const spec=JSON.parse(await fs.readFile(specPath,'utf8'));
const wb=Workbook.create();
for(const {name,rows} of spec.sheets){
  const s=wb.worksheets.add(name);
  const values=rows.map(r=>r.map(v=>v===undefined?null:typeof v==='object'&&v!==null?JSON.stringify(v):v));
  const n=values.length,w=values[0].length;
  const range=s.getRangeByIndexes(0,0,n,w);
  range.setNumberFormat('@'); range.values=values;
  range.format.font={name:'Arial',size:11}; range.format.rowHeight=26;
  range.format.columnWidth=25;
  s.getRangeByIndexes(0,0,1,w).format={fill:'#E5E7EB',font:{bold:true,color:'#111827'},rowHeight:32};
  s.freezePanes.freezeRows(1); s.showGridLines=false;
  if(w===1)range.format.columnWidth=110;
  else {s.getRangeByIndexes(0,0,n,1).format.columnWidth=40;}
}
wb.recalculate();
console.log((await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!',options:{useRegex:true,maxResults:10},maxChars:1000})).ndjson);
await (await SpreadsheetFile.exportXlsx(wb)).save(out);
if(process.env.RENDER_XLSX==='1'){
 for(const {name,rows} of spec.sheets){
  const blob=await wb.render({sheetName:name,range:`A1:${rows[0].length===1?'A':'D'}${Math.min(rows.length,6)}`,scale:1.5,format:'png'});
  await fs.writeFile(out+'.'+name+'.png',new Uint8Array(await blob.arrayBuffer()));
 }
}
