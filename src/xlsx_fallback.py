"""Minimal standards-based XLSX writer for environments without Artifact Tool.

This is selected explicitly with XLSX_BACKEND=stdlib. It writes text cells as
inline strings, so ISO dates, UUIDs and formula-like card names stay literal.
"""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from xml.etree import ElementTree as ET
from json import dumps
from datetime import datetime

NS='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
REL='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
PKG='http://schemas.openxmlformats.org/package/2006/relationships'
CONTENT='http://schemas.openxmlformats.org/package/2006/content-types'
ET.register_namespace('',NS)
ET.register_namespace('r',REL)

def node(parent,tag,attrs=None,text=None):
    el=ET.SubElement(parent,'{'+NS+'}'+tag,attrs or {})
    if text is not None:el.text=text
    return el

def letter(n):
    s=''
    while n:
        n,mod=divmod(n-1,26);s=chr(65+mod)+s
    return s

def xml(root):return ET.tostring(root,encoding='utf-8',xml_declaration=True)

def build(spec,path):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    sheets=spec['sheets'];assert sheets and all(s['rows'] for s in sheets)
    types=ET.Element('Types',xmlns=CONTENT)
    ET.SubElement(types,'Default',Extension='rels',ContentType='application/vnd.openxmlformats-package.relationships+xml')
    ET.SubElement(types,'Default',Extension='xml',ContentType='application/xml')
    for part,ctype in [('/xl/workbook.xml','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml'),('/xl/styles.xml','application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml')]+[(f'/xl/worksheets/sheet{i}.xml','application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml') for i in range(1,len(sheets)+1)]:
        ET.SubElement(types,'Override',PartName=part,ContentType=ctype)
    rootrels=ET.Element('Relationships',xmlns=PKG)
    ET.SubElement(rootrels,'Relationship',Id='rId1',Type=REL+'/officeDocument',Target='xl/workbook.xml')
    wb=ET.Element('{'+NS+'}workbook');book=node(wb,'sheets')
    for i,s in enumerate(sheets,1):
        ET.SubElement(book,'{'+NS+'}sheet',{'name':s['name'],'sheetId':str(i),'{'+REL+'}id':f'rId{i}'})
    wbrels=ET.Element('Relationships',xmlns=PKG)
    for i in range(1,len(sheets)+1):ET.SubElement(wbrels,'Relationship',Id=f'rId{i}',Type=REL+'/worksheet',Target=f'worksheets/sheet{i}.xml')
    ET.SubElement(wbrels,'Relationship',Id=f'rId{len(sheets)+1}',Type=REL+'/styles',Target='styles.xml')
    styles=ET.Element('{'+NS+'}styleSheet')
    fonts=node(styles,'fonts',{'count':'2'});node(node(fonts,'font'),'sz',{'val':'11'});font=node(fonts,'font');node(font,'b');node(font,'sz',{'val':'11'})
    fills=node(styles,'fills',{'count':'2'});node(node(fills,'fill'),'patternFill',{'patternType':'none'});node(node(fills,'fill'),'patternFill',{'patternType':'gray125'})
    borders=node(styles,'borders',{'count':'1'});node(borders,'border')
    cs=node(styles,'cellStyleXfs',{'count':'1'});node(cs,'xf',{'numFmtId':'0','fontId':'0','fillId':'0','borderId':'0'})
    xs=node(styles,'cellXfs',{'count':'2'});node(xs,'xf',{'numFmtId':'49','fontId':'0','fillId':'0','borderId':'0','xfId':'0'});node(xs,'xf',{'numFmtId':'49','fontId':'1','fillId':'0','borderId':'0','xfId':'0'})
    names=node(styles,'cellStyles',{'count':'1'});node(names,'cellStyle',{'name':'Normal','xfId':'0','builtinId':'0'})
    with ZipFile(path,'w',ZIP_DEFLATED) as z:
        for name,data in [('[Content_Types].xml',ET.tostring(types,encoding='utf-8',xml_declaration=True)),('_rels/.rels',ET.tostring(rootrels,encoding='utf-8',xml_declaration=True)),('xl/workbook.xml',xml(wb)),('xl/_rels/workbook.xml.rels',ET.tostring(wbrels,encoding='utf-8',xml_declaration=True)),('xl/styles.xml',xml(styles))]:z.writestr(name,data)
        for i,s in enumerate(sheets,1):
            ws=ET.Element('{'+NS+'}worksheet');view=node(node(ws,'sheetViews'),'sheetView',{'workbookViewId':'0'});node(view,'pane',{'ySplit':'1','topLeftCell':'A2','activePane':'bottomLeft','state':'frozen'})
            node(ws,'cols');data=node(ws,'sheetData')
            for rownum,rowvals in enumerate(s['rows'],1):
                row=node(data,'row',{'r':str(rownum)})
                for colnum,v in enumerate(rowvals,1):
                    if v is None:continue
                    if isinstance(v,(list,dict)):v=dumps(v,ensure_ascii=False,separators=(',',':'))
                    cell=node(row,'c',{'r':letter(colnum)+str(rownum),'s':'1' if rownum==1 else '0','t':'inlineStr'})
                    textnode=node(node(cell,'is'),'t',text=str(v))
                    if str(v).startswith(' ') or str(v).endswith(' '):textnode.set('{http://www.w3.org/XML/1998/namespace}space','preserve')
            if len(s['rows'])>1 and len(s['rows'][0])>1:node(ws,'autoFilter',{'ref':f'A1:{letter(len(s["rows"][0]))}{len(s["rows"])}'})
            z.writestr(f'xl/worksheets/sheet{i}.xml',xml(ws))
