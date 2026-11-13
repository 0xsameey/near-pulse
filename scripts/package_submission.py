"""Prepare reviewable local source/static archives. Never deploys or uses APIs."""
import json,zipfile,hashlib,sys
from pathlib import Path
from dotenv import dotenv_values

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.provenance import load_export

def main():
    files=set()
    for directory in ('src','scripts','sql','tests','docs','public/data','data/processed','validation-evidence'):
        files.update(p for p in (ROOT/directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc')
    for name in ('README.md','THESIS.md','VALIDATION.md','LICENSE','.env.example','.gitignore','package.json','package-lock.json','tsconfig.json','vite.config.ts','vercel.json','index.html','requirements.txt','requirements-bigquery.txt','pytest.ini','data/manifest.json','data/schema.json','data/raw/README.md'):
        path=ROOT/name
        if path.is_file():files.add(path)
    for source in ('network','intents','price'):
        manifest=ROOT/f'data/raw/{source}.manifest.json'
        if not manifest.exists():continue
        meta=json.loads(manifest.read_text(encoding='utf-8'))
        load_export(ROOT/'data/raw',source,meta['start'],meta['end'],require_coverage=False)
        files.add(manifest);files.add(ROOT/'data/raw'/meta['path'])
        files.update(ROOT/'data/raw'/page['path'] for page in meta.get('response_pages',[]))
    for path in (ROOT/'data/raw/history').rglob('*.json'):
        if path.name[:64]!=hashlib.sha256(path.read_bytes()).hexdigest():raise RuntimeError('Historical snapshot hash mismatch')
        files.add(path)
    secrets=[v.encode() for k,v in dotenv_values(ROOT/'.env').items() if v and k in ('INTENTS_EXPLORER_JWT','COINGECKO_API_KEY','OPENAI_API_KEY')]
    if any(secret in path.read_bytes() for path in files for secret in secrets):raise RuntimeError('Credential-bearing archive input rejected')
    output=ROOT/'artifacts';output.mkdir(exist_ok=True)
    source_zip=output/'near-pulse-source.zip'
    with zipfile.ZipFile(source_zip,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for path in sorted(files):archive.write(path,path.relative_to(ROOT).as_posix())
    static_zip=output/'near-pulse-static.zip'
    with zipfile.ZipFile(static_zip,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for path in sorted((ROOT/'dist').rglob('*')):
            if path.is_file():
                if any(secret in path.read_bytes() for secret in secrets):raise RuntimeError('Credential-bearing static asset rejected')
                archive.write(path,path.relative_to(ROOT/'dist').as_posix())
    records=[]
    for path in (source_zip,static_zip):
        with zipfile.ZipFile(path) as archive:
            assert archive.testzip() is None
            assert '.env' not in archive.namelist()
            members=len(archive.namelist())
        checksum=hashlib.sha256(path.read_bytes()).hexdigest()
        records.append({'path':path.name,'bytes':path.stat().st_size,'sha256':checksum,'members':members,'crc_valid':True})
        print(path.name,path.stat().st_size,'bytes',checksum)
    (output/'manifest.json').write_text(json.dumps({'archives':records,'credentials_excluded':True},indent=2)+'\n')

if __name__=='__main__':main()
