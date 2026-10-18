"""Download Lovdata NLOD public datasets. No credentials required."""
import argparse
import bz2
import io
import os
import tarfile
import xml.etree.ElementTree as ET
import httpx
from .core import connect

BASE=os.getenv('LOVDATA_PUBLIC_API_BASE_URL','https://api.lovdata.no').rstrip('/')
DEFAULT=['gjeldende-lover','gjeldende-sentrale-forskrifter']

def ingest_xml(data):
    root=ET.fromstring(data)
    text=' '.join(t.strip() for t in root.itertext() if t and t.strip())
    attrs={}
    for tag in root.iter():
        name=tag.tag.rsplit('}',1)[-1].lower()
        if name in ('title','tittel','doktitle','shorttitle') and tag.text and not attrs.get('title'):
            attrs['title']=tag.text.strip()
    return attrs.get('title') or text[:100] or 'Uten tittel', text

def sync(names):
    total=0
    with httpx.Client(timeout=120,follow_redirects=True) as client:
        for name in names:
            if '/' in name or '..' in name: raise ValueError('Ugyldig datasett')
            resp=client.get(f'{BASE}/v1/publicData/get/{name}.tar.bz2')
            resp.raise_for_status()
            with tarfile.open(fileobj=io.BytesIO(resp.content), mode='r:bz2') as archive:
                with connect() as con:
                    for item in archive:
                        if not item.isfile() or not item.name.lower().endswith('.xml') or item.size > 12_000_000: continue
                        stream=archive.extractfile(item)
                        if stream is None: continue
                        try: title,text=ingest_xml(stream.read())
                        except ET.ParseError: continue
                        if not text: continue
                        doc_id=item.name.removesuffix('.xml').lstrip('./')
                        con.execute('INSERT OR REPLACE INTO documents(doc_id,title,text,source) VALUES (?,?,?,?)',(doc_id,title,text,name))
                        total+=1
            print(f'Indeksert {name}; totalt {total} dokumenter')
    return total

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--matching',action='append',default=[])
    parser.add_argument('--list',action='store_true')
    args=parser.parse_args()
    if args.list:
        with httpx.Client(timeout=30) as client:
            r=client.get(f'{BASE}/v1/publicData/list');r.raise_for_status();print(r.text[:20000]);return
    sync(args.matching or DEFAULT)
if __name__=='__main__':main()
