"""Course-aware, local-only question-bank adapter, search and paired PDF export."""
from pathlib import Path
import json, argparse, re, datetime, os, sys

HERE=Path(__file__).resolve().parent
PROFILES=json.loads((HERE.parent/'references/course-profiles.json').read_text())

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def safe(root, value):
    root=Path(root).resolve();p=(root/str(value)).resolve()
    if not p.is_relative_to(root) or p==root:raise ValueError('Asset escapes provided material directory')
    return p

def paper_num(value):
    match=re.fullmatch(r'(?:Paper\s+)?([1-6])(?:[1-9])?',str(value).strip(),re.I)
    if not match:raise ValueError('Missing paper component')
    return match[1]

def topic_matches(query, label):
    q=str(query).strip()
    code=re.fullmatch(r"(?:Topic\s*)?(\d+(?:\.\d+|[A-Z])?)",q,re.I)
    if code:
        target=re.match(r"^(?:Topic\s+)?(\d+(?:\.\d+|[A-Z])?)(?:\s|[·:]|$)",label,re.I)
        return bool(target and target[1].casefold()==code[1].casefold())
    return q.casefold() in label.casefold()

def normalize(course, row, source):
    q=dict(row)
    if str(q.get('course',course))!=course:raise ValueError('Cross-course bank record')
    q['course']=course;q['paper']=paper_num(q['paper'])
    kinds={'9702':{'1':'mcq'},'0625':{'1':'mcq','2':'mcq'}}
    expected=kinds[course].get(q['paper'],'structured')
    if q.get('kind',expected)!=expected:raise ValueError('Question kind conflicts with paper')
    q['kind']=expected
    if not isinstance(q.get('id'),str) or not q['id']:raise ValueError('Question ID required')
    q['topics']=q.get('topics',[]);q['subtopics']=q.get('subtopics',[])
    if not q['topics']:raise ValueError('Question topics required')
    q['difficulty']=str(q.get('difficulty','')).lower()
    if q['difficulty'] not in {'easy','medium','hard'}:raise ValueError('Difficulty must be easy/medium/hard')
    q['marks']=q.get('marks')
    if q['marks'] is not None and (type(q['marks']) is not int or q['marks']<1):raise ValueError('Known marks must be positive integers')
    for key in ['question_image','answer_image']:
        p=safe(source,q[key])
        if not p.is_file():raise FileNotFoundError('Missing '+key+': '+str(p))
        q[key]=str(p)
    q['corrected_marks']=q['marks'] or 0
    q['paper_type']='MCQ' if q['kind']=='mcq' else 'Structured'
    q['source_ref']=q.get('source_ref',q['id'])
    return q

def import_bank(course, source):
    """Import only current-visible entries; external data never enters the source distribution."""
    source=Path(source).resolve()
    if (source/'catalog.json').is_file():
        data=read(source/'catalog.json')
        if str(data.get('course'))!=course:raise ValueError('Catalog course mismatch')
        raw=data['questions']
    elif course=='9702' and (source/'03_Question_Bank/question_answer_map.json').is_file():
        mapping=read(source/'03_Question_Bank/question_answer_map.json')
        parity=read(source/'06_Manual_Homework_Builder_v1/web_filter_parity.json')['questions']
        excluded={x['id'] for x in read(source/'03_Question_Bank/excluded_from_current_syllabus.json')['entries']}
        approved=read(source/'03_Question_Bank/approved_classification_2026-09-16.json')['entries']
        reviewed=read(source/'03_Question_Bank/assistant_classification_2026-09-17.json')['entries']
        raw=[]
        for r in mapping:
            ident=r['id']
            if ident not in parity or ident in excluded:continue
            if approved.get(ident,{}).get('status')=='withheld_pending_review' and ident not in reviewed:continue
            p=parity[ident]
            raw.append({'id':ident,'paper':r['paper'],'topics':p.get('topics',[p['topic']]),'subtopics':p.get('subtopics',[]),
                        'difficulty':p['difficulty'],'difficulty_reason':r.get('difficulty_reason',''),
                        'marks':p.get('marks') or None,'year':int(r['year']),
                        'question_image':'03_Question_Bank/'+r['question_image'],
                        'answer_image':'03_Question_Bank/'+r['answer_image'],
                        'source_ref':ident,'search_text':r.get('snippet',''),
                        'classification_provenance':'existing local visibility/filter contract; not all individually teacher approved'})
    elif course=='0625' and (source/'03_Metadata/questions.json').is_file():
        parity=read(source/'04_App/web_filter_parity.json')['questions'];raw=[]
        for r in read(source/'03_Metadata/questions.json'):
            ident=r['question_id'];f=r.get('facets',{});c=r.get('classification',{})
            if ident not in parity or f.get('visible_in_filter_bank',True) is False:continue
            if f.get('classification_status') in {'needs_review','unclassified_out_of_current_syllabus'}:continue
            if not c.get('primary_topic') or not c.get('subtopics'):continue
            p=parity[ident]
            if len(r['assets']['question'])!=1 or len(r['assets']['answer'])!=1:raise ValueError('Use one complete paired image per indexed item')
            raw.append({'id':ident,'paper':r['source']['paper'],'topics':p.get('topics',[p['topic']]),'subtopics':p.get('subtopics',[]),
                        'difficulty':p['difficulty'],'difficulty_reason':r['assessment'].get('difficulty_reason',''),
                        'marks':p.get('marks') or None,'year':int(r['source']['year']),
                        'question_image':r['assets']['question'][0]['path'],'answer_image':r['assets']['answer'][0]['path'],
                        'source_ref':ident,'search_text':r.get('search_text',''),
                        'classification_provenance':f.get('classification_method','existing local classification')})
    else:
        raise ValueError('No supported index found. Follow references/first-bank.md to make a checked sample catalog from your own QP/MS.')
    normalized=[normalize(course,r,source) for r in raw]
    ids=[r['id'] for r in normalized]
    if len(ids)!=len(set(ids)):raise ValueError('Duplicate bank IDs')
    return normalized

def allowed(course,level):
    try:p=PROFILES[course]['levels'][level]
    except KeyError:raise ValueError('Level does not belong to selected course')
    return set(p['mcq']+p['structured'])

def load_bank(workspace,course):
    data=read(workspace/course/'bank.json')
    if data['course']!=course:raise ValueError('Cross-course bank file')
    return data['questions']

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--workspace',default=str(Path.home()/'codex/physics-homework'))
    sub=ap.add_subparsers(dest='cmd',required=True)
    prep=sub.add_parser('prepare');prep.add_argument('--course',choices=PROFILES,required=True);prep.add_argument('--source-root',required=True)
    search=sub.add_parser('search');search.add_argument('--course',choices=PROFILES,required=True);search.add_argument('--level',required=True)
    search.add_argument('--topic');search.add_argument('--query');search.add_argument('--difficulty',choices=['easy','medium','hard'])
    search.add_argument('--kind',choices=['mcq','structured']);search.add_argument('--limit',type=int,default=20)
    search.add_argument('--exclude-id',action='append',default=[]);search.add_argument('--include-used',action='store_true')
    export=sub.add_parser('export');export.add_argument('--course',choices=PROFILES,required=True);export.add_argument('--level',required=True)
    export.add_argument('--year',type=int,required=True);export.add_argument('--title',default='Physics Homework');export.add_argument('--checked',action='store_true')
    export.add_argument('--output-dir');export.add_argument('ids',nargs='+')
    info=sub.add_parser('info');info.add_argument('--course',choices=PROFILES,required=True)
    args=ap.parse_args();workspace=Path(args.workspace).expanduser().resolve()
    if args.cmd=='prepare':
        source=Path(args.source_root).expanduser().resolve()
        if workspace==source or source in workspace.parents:raise ValueError('Keep working data outside the read-only source directory')
        rows=import_bank(args.course,source)
        target=workspace/args.course/'bank.json'
        if target.exists():raise ValueError('Index already exists; use a new workspace rather than overwrite')
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(json.dumps({'course':args.course,'source_root':str(source),'questions':rows},ensure_ascii=False))
        print(json.dumps({'course':args.course,'count':len(rows),'index':str(target)},ensure_ascii=False));return
    rows=load_bank(workspace,args.course)
    if args.cmd=='info':
        from collections import Counter
        print(json.dumps({'course':args.course,'count':len(rows),'papers':dict(Counter(r['paper'] for r in rows)),
                          'syllabus_years':PROFILES[args.course]['years'],'levels':list(PROFILES[args.course]['levels'])},ensure_ascii=False,indent=2));return
    papers=allowed(args.course,args.level)
    history=workspace/args.course/'history.jsonl'
    if args.cmd=='search':
        pattern=re.compile(args.query,re.I) if args.query else None
        excludes=set(args.exclude_id)
        if history.is_file() and not args.include_used:
            for line in history.read_text().splitlines():excludes.update(json.loads(line)['ids'])
        matches=[]
        for r in rows:
            if r['id'] in excludes or r['paper'] not in papers:continue
            if args.kind and r['kind']!=args.kind:continue
            if args.difficulty and r['difficulty']!=args.difficulty:continue
            if args.topic and not any(topic_matches(args.topic,x) for x in r['topics']+r['subtopics']):continue
            if pattern and not pattern.search(' '.join([r.get('search_text',''),*r['topics'],*r['subtopics']])):continue
            matches.append(r)
        matches.sort(key=lambda r:(r.get('year',0),r['id']),reverse=True)
        print(json.dumps({'matches':len(matches),'candidates':matches[:max(0,args.limit)],
                          'note':'Tags only shortlist. Inspect complete questions and answers against the lesson boundary.'},ensure_ascii=False,indent=2));return
    if not args.checked:raise ValueError('Inspect complete questions, answers and lesson boundaries first; then use --checked')
    if args.year not in PROFILES[args.course]['years']:raise ValueError('Syllabus year not supported by this course profile')
    if not 1<=len(args.ids)<=80 or len(args.ids)!=len(set(args.ids)):raise ValueError('Choose 1-80 unique IDs')
    by_id={r['id']:r for r in rows}
    if any(i not in by_id for i in args.ids):raise ValueError('Unknown or cross-course ID')
    selected=[by_id[i] for i in args.ids]
    if any(r['paper'] not in papers for r in selected):raise ValueError('Question paper does not match selected course/level')
    import pdf_engine
    pdf_engine.CURRENT_COURSE=args.course
    sources=[Path(r[k]).resolve() for r in rows for k in ['question_image','answer_image']]
    out=Path(args.output_dir).expanduser().resolve() if args.output_dir else workspace/args.course/'output'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    if any(p==out or out in p.parents for p in sources):raise ValueError('Output directory overlaps source assets')
    if any((out/n).exists() for n in ['student.pdf','answers.pdf','selection.json']):raise ValueError('Do not overwrite existing output')
    for r in selected:
        for k in ['question_image','answer_image']:
            if not Path(r[k]).is_file():raise FileNotFoundError('Missing selected asset')
    # Exporter uses absolute user-supplied files, not a fixed machine's bank folder.
    pdf_engine.BANK_ROOT=Path(os.path.commonpath([str(p.parent) for p in sources]))
    out.mkdir(parents=True,exist_ok=True)
    metadata={'showSource':True,'totalMarks':sum(r['marks'] or 0 for r in selected),'marksIncomplete':sum(r['marks'] is None for r in selected)}
    for answer,name in [(False,'student.pdf'),(True,'answers.pdf')]:pdf_engine.build_pdf(selected,out/name,args.title[:48],metadata,answer)
    selection={'course':args.course,'level':args.level,'syllabus_year':args.year,'title':args.title,'ids':args.ids,
               'sources':[r['source_ref'] for r in selected],'teacher_review_required':True}
    (out/'selection.json').write_text(json.dumps(selection,ensure_ascii=False,indent=2))
    history.parent.mkdir(parents=True,exist_ok=True)
    with history.open('a') as f:f.write(json.dumps(selection,ensure_ascii=False)+'\n')
    print(json.dumps({'student':str(out/'student.pdf'),'answers':str(out/'answers.pdf'),'selection':str(out/'selection.json')},ensure_ascii=False,indent=2))

if __name__=='__main__':
    try:main()
    except (ValueError,FileNotFoundError,KeyError) as exc:raise SystemExit(str(exc))
