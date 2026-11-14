"""Package the standard Agent Skill with optional WorkBuddy marketplace metadata."""
from pathlib import Path
import argparse,json,re,zipfile

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--platform',choices=['standard','workbuddy'],default='standard');ap.add_argument('--output',required=True)
    args=ap.parse_args();root=Path(__file__).resolve().parents[1];skill=root/'skill/physics-homework'
    text=(skill/'SKILL.md').read_text();_,header,body=text.split('---',2)
    if args.platform=='workbuddy':
        metadata=json.loads(next(line.split(':',1)[1].strip() for line in header.splitlines() if line.startswith('metadata:')))
        name=next(line.split(':',1)[1].strip() for line in header.splitlines() if line.startswith('name:'))
        description=json.loads(next(line.split(':',1)[1].strip() for line in header.splitlines() if line.startswith('description:')))
        fields={'name':name,'description':description,**metadata['workbuddy']}
        text='---\n'+'\n'.join(k+': '+json.dumps(v,ensure_ascii=False) for k,v in fields.items())+'\n---'+body
    output=Path(args.output).expanduser().resolve();output.parent.mkdir(parents=True,exist_ok=True)
    if output.exists():raise SystemExit('Choose a new archive path')
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(skill.rglob('*')):
            if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc':
                name=str(p.relative_to(skill.parent))
                if p.name=='SKILL.md':z.writestr(name,text)
                else:z.write(p,name)
        z.write(root/'LICENSE',skill.name+'/LICENSE')
    with zipfile.ZipFile(output) as z:
        if z.testzip():raise SystemExit('Archive check failed')
    print(output)

if __name__=='__main__':main()
