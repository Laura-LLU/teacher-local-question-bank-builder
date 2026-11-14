"""Create author-written synthetic materials; no examination-board data is included."""
from pathlib import Path
import argparse,json
from PIL import Image,ImageDraw,ImageFont

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);args=ap.parse_args();root=Path(args.output).resolve()
    if root.exists():raise SystemExit('Choose a new demo directory')
    for course in ['9702','0625']:
        dest=root/course;(dest/'questions').mkdir(parents=True);(dest/'answers').mkdir()
        records=[]
        specs=[('mcq','1' if course=='9702' else '2',
                'A trolley moves at 3.0 m/s for 4.0 s. What distance does it travel?',
                'A 0.75 m     B 7.0 m     C 12 m     D 24 m','Answer C: distance = speed x time = 12 m.',1),
               ('structured','2' if course=='9702' else '4',
                'A trolley starts from rest with constant acceleration 2.0 m/s2.',
                '(a) Find its speed after 3.0 s. [2]   (b) Find the distance travelled. [2]',
                '(a) v = at = 6.0 m/s. [2]   (b) s = 0.5at2 = 9.0 m. [2]',4)]
        for n,(kind,paper,q,extra,a,marks) in enumerate(specs,1):
            ident=f'original-{course}-{n}'
            for side,text in [('questions',q+'\n\n'+extra),('answers',a)]:
                image=Image.new('RGB',(1200,480),'white');draw=ImageDraw.Draw(image)
                font=ImageFont.load_default(size=22)
                draw.text((30,24),'AUTHOR-WRITTEN DEMO | NOT AN OFFICIAL EXAM QUESTION',fill='black',font=font)
                draw.multiline_text((40,110),text,fill='black',font=font,spacing=20)
                image.save(dest/side/(ident+'.png'))
            records.append({'id':ident,'course':course,'paper':paper,'kind':kind,
                            'topics':['Topic 2 · Kinematics' if course=='9702' else '1 Motion, forces and energy'],
                            'subtopics':['2C · Uniformly accelerated motion' if course=='9702' else '1.2 Motion'],
                            'difficulty':'easy','difficulty_reason':'Direct standard formula application',
                            'marks':marks,'year':2026,'source_ref':ident+' | Original demo',
                            'question_image':'questions/'+ident+'.png','answer_image':'answers/'+ident+'.png'})
        (dest/'catalog.json').write_text(json.dumps({'course':course,'questions':records},ensure_ascii=False,indent=2))
    print(root)

if __name__=='__main__':main()
