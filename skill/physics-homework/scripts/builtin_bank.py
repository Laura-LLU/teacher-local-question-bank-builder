"""Built-in metadata + integrity-checked, on-demand material cache. No user board upload."""
from pathlib import Path
import json,re,hashlib,sys,time,urllib.request,urllib.parse,subprocess,shutil,io
from concurrent.futures import ThreadPoolExecutor
from PIL import Image

RESOURCES=Path(__file__).resolve().parents[1]/'resources'
PROVIDER=json.loads((RESOURCES/'builtin-provider.json').read_text())

def get_origin_url(origin,asset):
    if origin not in PROVIDER['origins']:raise ValueError('Unknown bank origin')
    if not re.fullmatch(r'assets/(?:questions|answers)/(?:9702|0625)/[A-Za-z0-9_-]+\.webp\?v=[0-9a-f]{12}',asset):raise ValueError('Invalid material path')
    return origin+'/'+asset

def verify_image(path,expected):
    try:
        raw=path.read_bytes()
        if not raw or len(raw)>12*1024*1024 or not hashlib.sha256(raw).hexdigest().startswith(expected):return False
        with Image.open(io.BytesIO(raw)) as im:im.verify()
        return True
    except (OSError,ValueError):return False

def ensure_index(workspace,course):
    workspace=Path(workspace).resolve();target=workspace/course/'bank.json'
    if target.is_file():return target
    payload=json.loads((RESOURCES/('builtin-'+course+'.json')).read_text())
    if payload['course']!=course or len(payload['questions'])!=PROVIDER['counts'][course]:raise ValueError('Built-in index damaged')
    rows=[];ids=set()
    for source in payload['questions']:
        ident=source['id']
        if not re.fullmatch(r'[A-Za-z0-9_-]+',ident) or ident in ids:raise ValueError('Invalid built-in ID')
        ids.add(ident);q={**source,'course':course,'source_kind':'builtin','corrected_marks':source['marks'] or 0,
                          'paper_type':'MCQ' if source['kind']=='mcq' else 'Structured',
                          'search_text':' '.join(source.get('keywords',[]))}
        for side,folder in [('question','questions'),('answer','answers')]:
            asset=source[side+'_asset']
            if not re.fullmatch(r'assets/'+folder+'/'+course+'/'+re.escape(ident)+r'\.webp\?v=[0-9a-f]{12}',asset):raise ValueError('Invalid material URL')
            digest=urllib.parse.parse_qs(urllib.parse.urlsplit(asset).query)['v'][0]
            q[side+'_image']=str(workspace/'builtin-assets'/course/(ident+'-'+side+'-'+digest+'.webp'))
        rows.append(q)
    target.parent.mkdir(parents=True,exist_ok=True)
    temp=target.with_suffix('.pending')
    temp.write_text(json.dumps({'course':course,'source_kind':'builtin','source_version':payload['version'],'questions':rows},ensure_ascii=False))
    temp.replace(target)
    print('内置'+course+'题库索引已就绪：'+str(len(rows))+'题。题目与答案将在使用时自动缓存。',file=sys.stderr)
    return target

def fetch_one(row,side):
    if row.get('source_kind')!='builtin':return
    asset=row[side+'_asset'];expected=urllib.parse.parse_qs(urllib.parse.urlsplit(asset).query)['v'][0]
    path=Path(row[side+'_image'])
    if verify_image(path,expected):return
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix('.pending')
    errors=[]
    for origin in PROVIDER['origins']:
        url=get_origin_url(origin,asset)
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'PhysicsBoardHomework/0.4'})
            with urllib.request.urlopen(req,timeout=25) as response:
                if urllib.parse.urlsplit(response.geturl()).netloc not in [urllib.parse.urlsplit(x).netloc for x in PROVIDER['origins']]:raise ValueError('Unexpected material redirect')
                raw=response.read(12*1024*1024+1)
            temp.write_bytes(raw)
            if not verify_image(temp,expected):raise ValueError('Image or content hash does not match built-in metadata')
            temp.replace(path);return
        except Exception as exc:errors.append(str(exc))
        # Some networks truncate urllib transfers; curl is a transport fallback, not a TLS bypass.
        if shutil.which('curl'):
            try:
                cp=subprocess.run(['curl','--silent','--show-error','--fail','--location','--max-time','25','--output',str(temp),url],capture_output=True,text=True,timeout=30)
                if cp.returncode==0 and verify_image(temp,expected):temp.replace(path);return
            except (OSError,subprocess.TimeoutExpired) as exc:errors.append(str(exc))
    temp.unlink(missing_ok=True)
    raise RuntimeError(row['id']+' '+side+'：题库素材暂时无法取得，请检查网络后重试。'+(' '+errors[-1] if errors else ''))

def ensure_assets(rows):
    jobs=[(row,side) for row in rows for side in ['question','answer'] if row.get('source_kind')=='builtin']
    missing=sum(not verify_image(Path(row[side+'_image']),urllib.parse.parse_qs(urllib.parse.urlsplit(row[side+'_asset']).query)['v'][0]) for row,side in jobs)
    if missing:print('正在自动准备'+str(missing)+'张题目/答案图片；已缓存的内容会直接复用。',file=sys.stderr)
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(lambda pair:fetch_one(*pair),jobs))
