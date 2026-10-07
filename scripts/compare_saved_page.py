"""Compare two saved Wiki responses offline; never fetch or adopt data."""
import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlsplit, unquote

from bs4 import BeautifulSoup


def load_saved(directory):
    directory=Path(directory)
    report=json.loads((directory/'fetch.json').read_text(encoding='utf-8'))
    if report.get('status')!='fetched':
        raise ValueError('Only complete fetched responses can be compared')
    raw=(directory/'response.html').read_bytes()
    digest=hashlib.sha256(raw).hexdigest()
    if digest!=report.get('sha256'):
        raise ValueError('Saved response hash mismatch')
    document=BeautifulSoup(raw,'html.parser')
    content=document.select_one('#content')
    canonical=document.find('link',rel='canonical')
    if content is None or canonical is None or not canonical.get('href'):
        raise ValueError('Wiki content or canonical URL missing')
    def normalize(value):
        return unquote(urlsplit(value).path)
    if normalize(canonical['href'])!=normalize(report['url']):
        raise ValueError('Saved response belongs to another page')
    lines=[re.sub(r'\s+',' ',line).strip() for line in content.get_text('\n').splitlines()]
    lines=[line for line in lines if line]
    links=[(re.sub(r'\s+',' ',a.get_text(' ',strip=True)),a.get('href'))
           for a in content.find_all('a',href=True)]
    return {'url':report['url'],'sha256':digest,'fetched_at':report['fetched_at'],
            'text_lines':lines,'links':links}


def compare(old_directory,new_directory):
    old=load_saved(old_directory)
    new=load_saved(new_directory)
    if old['url']!=new['url']:
        raise ValueError('Cannot compare different Wiki pages')
    return {'url':old['url'],'old_fetched_at':old['fetched_at'],
            'new_fetched_at':new['fetched_at'],'old_sha256':old['sha256'],
            'new_sha256':new['sha256'],'same_response_bytes':old['sha256']==new['sha256'],
            'same_visible_text':old['text_lines']==new['text_lines'],
            'same_content_links':old['links']==new['links'],
            'old_text_lines':len(old['text_lines']),'new_text_lines':len(new['text_lines']),
            'old_links':len(old['links']),'new_links':len(new['links'])}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('old_directory')
    parser.add_argument('new_directory')
    args=parser.parse_args()
    print(json.dumps(compare(args.old_directory,args.new_directory),ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
