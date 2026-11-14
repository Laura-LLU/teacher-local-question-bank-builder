"""Render an Agent/teacher-checked crop catalog into a local, paired sample bank."""
from pathlib import Path
import argparse, json
from PIL import Image
import pypdfium2 as pdfium
from homework import safe, normalize

def render(root,specs):
    if not specs:raise ValueError('Both question and answer crop specs are required')
    images=[]
    for s in specs:
        path=safe(root,s['pdf']);doc=pdfium.PdfDocument(str(path));page_no=s['page']
        if type(page_no) is not int or not 0<=page_no<len(doc):raise ValueError('Invalid zero-based PDF page')
        box=s['crop']
        if len(box)!=4 or not (0<=box[0]<box[2]<=1 and 0<=box[1]<box[3]<=1):raise ValueError('Invalid normalized crop')
        image=doc[page_no].render(scale=2).to_pil().convert('RGB');w,h=image.size;l,b,r,t=box
        images.append(image.crop((round(l*w),round((1-t)*h),round(r*w),round((1-b)*h))))
        doc.close()
    width=max(im.width for im in images)
    sheet=Image.new('RGB',(width,sum(im.height for im in images)+16*(len(images)-1)),'white')
    y=0
    for im in images:sheet.paste(im,((width-im.width)//2,y));y+=im.height+16
    return sheet

def main():
    ap=argparse.ArgumentParser();ap.add_argument('manifest');ap.add_argument('--source-root',required=True);ap.add_argument('--output',required=True)
    args=ap.parse_args();manifest=json.loads(Path(args.manifest).read_text());root=Path(args.source_root).resolve();out=Path(args.output).resolve()
    if out==root or root in out.parents or out in root.parents:raise ValueError('Keep sample-bank output independent of source material')
    if out.exists():raise ValueError('Use a new output folder')
    if manifest.get('reviewed') is not True:raise ValueError('Agent/teacher must inspect the crop specification first')
    ids=[r['id'] for r in manifest['questions']]
    if len(ids)!=len(set(ids)) or any(not __import__('re').fullmatch('[A-Za-z0-9_-]+',i) for i in ids):raise ValueError('Unique safe IDs required')
    # Validate all page/crop references before writing any files.
    for row in manifest['questions']:
        if not row.get('question_pages') or not row.get('answer_pages'):raise ValueError('Missing paired crop specification')
        for specs in [row['question_pages'],row['answer_pages']]:
            for s in specs:
                p=safe(root,s['pdf'])
                if not p.is_file():raise FileNotFoundError(p)
    (out/'questions').mkdir(parents=True);(out/'answers').mkdir()
    rows=[]
    for row in manifest['questions']:
        for side in ['question','answer']:
            render(root,row[side+'_pages']).save(out/(side+'s')/(row['id']+'.png'))
        item={k:v for k,v in row.items() if k not in ['question_pages','answer_pages']}
        item.update(question_image='questions/'+row['id']+'.png',answer_image='answers/'+row['id']+'.png')
        normalize(manifest['course'],item,out)
        rows.append(item)
    (out/'catalog.json').write_text(json.dumps({'course':manifest['course'],'questions':rows},ensure_ascii=False,indent=2))
    print(out/'catalog.json')

if __name__=='__main__':main()
