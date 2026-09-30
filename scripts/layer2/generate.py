"""Build a finite bank of distinct paired-case questions, without changing source data.
Each pair has two substantively different cases. Never emit a second version of a pair.
Numbers are fixed in authored cases; no numeric-parameter question multiplication.
"""
from pathlib import Path
import json,hashlib,re,random,ast,math,collections,itertools
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
ROOT=Path(__file__).resolve().parents[2]
ORIGINAL_SHA='d0048cb99f595e07544e1c17c05cd60034e6a1f5094f55ff9afe1a2cf637830b'
assert hashlib.sha256((ROOT/'dist/questions.json').read_bytes()).hexdigest()==ORIGINAL_SHA
original=json.loads((ROOT/'dist/questions.json').read_text())
quotas={'Science & Engineering':300,'Computers':245,'Mathematics':220,'Reasoning':190,'General Awareness':45}
files=['science','computers','mathematics','reasoning','awareness']
def evaluate(s):
 tree=ast.parse(s,mode='eval')
 allowed=(ast.Expression,ast.BinOp,ast.UnaryOp,ast.Constant,ast.Add,ast.Sub,ast.Mult,ast.Div,ast.Pow,ast.Mod,ast.USub,ast.UAdd,ast.Load)
 assert all(isinstance(n,allowed) for n in ast.walk(tree)),s
 return eval(compile(tree,'<numeric-check>','eval'),{'__builtins__':{}},{})
def norm(s):
 s=s.lower();s=re.sub(r'\d+(?:\.\d+)?',' NUMBER ',s)
 s=re.sub(r'[^a-z0-9 ]',' ',s)
 return ' '.join(s.split())
cases=[];numeric_checks=0
for subject,file in zip(quotas,files):
 for i,line in enumerate((ROOT/f'scripts/layer2/{file}.txt').read_text().splitlines()):
  topic,scenario,truth,false,reason,formula,checks=line.split('|')
  refs=[q['id'] for q in original if q['subject']==subject and q['topic']==topic]
  assert refs,(subject,topic)
  assert truth!=false
  for check in checks.split(';'):
   if check.strip():
    expr,expected=check.strip().rsplit('=',1)
    assert math.isclose(evaluate(expr),float(expected),rel_tol=1e-9,abs_tol=1e-9),(file,i,check)
    numeric_checks+=1
  cases.append(dict(id=f'{file}-{i+1:03}',subject=subject,topic=topic,scenario=scenario,truth=truth,false=false,reason=reason,formula=formula,checks=checks,refs=refs))
# Filter cases whose setup itself is close to an original question, including digit-normalized comparisons.
vec=TfidfVectorizer(preprocessor=norm,ngram_range=(1,2),stop_words='english',sublinear_tf=True)
texts=[q['question_text'] for q in original]+[c['scenario'] for c in cases]
mat=vec.fit_transform(texts);sim=(mat[len(original):]@mat[:len(original)].T).toarray()
excluded=[]
# Editorial exclusions: setups too close to supplied items, even when text similarity alone is lower.
editorial_exclusions={'science-001','science-006','science-020','science-022','science-034','science-042','science-043','science-055','science-058','computers-005','computers-006','computers-021','computers-031','computers-036','computers-039','mathematics-014','mathematics-017','mathematics-019','mathematics-024','mathematics-030','mathematics-032','mathematics-041','mathematics-044','mathematics-045','mathematics-051','mathematics-052','reasoning-014','reasoning-016','reasoning-031','reasoning-035','awareness-019'}
for c,row in zip(cases,sim):
 c['closest_original_setup_similarity']=float(row.max())
 if row.max()>=.50 or c['id'] in editorial_exclusions:excluded.append({'case':c['id'],'original':original[int(row.argmax())]['id'],'similarity':round(float(row.max()),4)})
valid=[c for c in cases if c['id'] not in {x['case'] for x in excluded}]
# Select balanced unique unordered pairs; disallow combining two cases on the same topic.
# The resulting format is explicitly disclosed as paired-case practice, not 1,000 independent case narratives.
rng=random.Random(20260930);questions=[];exposure=collections.Counter();signatures=set()
options=[('Only conclusion I is correct.',(True,False)),('Only conclusion II is correct.',(False,True)),('Both conclusions are correct.',(True,True)),('Neither conclusion is correct.',(False,False))]
for subject,target in quotas.items():
 cs=[c for c in valid if c['subject']==subject]
 candidates=[(a,b) for a,b in itertools.combinations(cs,2) if a['topic']!=b['topic'] and .45<len(a['scenario'])/len(b['scenario'])<2.2]
 rng.shuffle(candidates)
 taken=[]
 while len(taken)<target:
  assert candidates,(subject,len(taken),target)
  # Prefer least-used cases, distributing practice across the authored topics.
  idx=min(range(len(candidates)),key=lambda i:(max(exposure[candidates[i][0]['id']],exposure[candidates[i][1]['id']]),sum(exposure[c['id']] for c in candidates[i])))
  a,b=candidates.pop(idx);sig='::'.join(sorted([a['id'],b['id']]))
  assert sig not in signatures
  local=random.Random(hashlib.sha256(sig.encode()).hexdigest())
  state=(local.choice([True,False]),local.choice([True,False]))
  claims=[a['truth'] if state[0] else a['false'],b['truth'] if state[1] else b['false']]
  stem=f"Evaluate the two independent cases. A conclusion is correct only if it follows from its own case; a claim that is merely possible is not sufficient.\n\nI. {a['scenario']} A trainee concludes: {claims[0]}\n\nII. {b['scenario']} A trainee concludes: {claims[1]}\n\nWhich conclusion or conclusions are correct?"
  # Reject near-duplicate composite stems before admitting them.
  comparison=[q['question_text'] for q in original]+[q['question_text'] for q in questions+taken]+[stem]
  # Fitted case-level vocabulary gives a stable comparison without a re-fit for every pair.
  # Include conclusions in comparison; a final independent full-bank audit follows below.
  candidate_vec=vec.transform([stem]);prior=vec.transform(comparison[:-1]);closest=float((candidate_vec@prior.T).max())
  if closest>=.72:continue
  opts=options[:];local.shuffle(opts);key='ABCD'[[v[1] for v in opts].index(state)]
  reasons=[f"Conclusion {'I' if j==0 else 'II'} is {'correct' if state[j] else 'incorrect'}. {c['reason']}" for j,c in enumerate([a,b])]
  wrong={}
  for l,(label,assertions) in zip('ABCD',opts):
   mismatches=[f"It treats conclusion {'I' if j==0 else 'II'} as {'correct' if assertions[j] else 'incorrect'}, but it is {'correct' if state[j] else 'incorrect'}. {c['reason']}" for j,c in enumerate([a,b]) if assertions[j]!=state[j]]
   wrong[l]=' '.join(mismatches) if mismatches else 'This option matches both independently checked conclusions. '+ ' '.join(reasons)
  steps='\n'.join(f"Case {'I' if j==0 else 'II'}: {c['reason']}" for j,c in enumerate([a,b]))
  formulas='\n'.join(f"Case {'I' if j==0 else 'II'}: {c['formula']}" for j,c in enumerate([a,b]) if c['formula'])
  calculations='\n'.join(f"Case {'I' if j==0 else 'II'}: {c['reason']}" for j,c in enumerate([a,b]) if c['checks'])
  complexity=sum(bool(c['checks']) for c in [a,b])+sum(len(c['reason'])>190 for c in [a,b])
  operation_count=sum(sum(isinstance(n,ast.BinOp) for n in ast.walk(ast.parse(check.strip().rsplit('=',1)[0],mode='eval'))) for c in [a,b] for check in c['checks'].split(';') if check.strip())
  difficulty='Hard' if all(c['checks'] for c in [a,b]) and operation_count>=5 else 'Medium-Hard' if complexity>=1 else 'Medium'
  q=dict(id='l2-'+hashlib.sha256(sig.encode()).hexdigest()[:16],question_text=stem,correct_option=key,subject=subject,topic=a['topic'],subtopic=f"{a['topic']} + {b['topic']}",related_topics=[a['topic'],b['topic']],difficulty=difficulty,explanation='\n'.join(reasons),concept=f"Apply {a['topic']} and {b['topic']} to the two cases separately. Accept an option only if it correctly classifies both conclusions.",formula=formulas or None,given=f"Case I: {a['scenario']}\nCase II: {b['scenario']}",calculation=calculations or None,final_answer=opts['ABCD'.index(key)][0],why_correct='\n'.join(reasons),why_wrong=wrong,source_type='BANK_BASED_PRACTICE',layer='new',label='NEW — BANK-BASED PRACTICE',status='ACTIVE',verification_status='GENERATED_RULE_CHECKED',source_reference='New paired-case practice based on topics represented in the supplied bank. Not an official RRB question or PYQ.',exam='RRB Technician Grade-I Signal',generation_method='authored-case-composition-v1',generation_metadata={'format':'two independent application cases','case_ids':[a['id'],b['id']],'truth_values':list(state),'option_truth_values':{l:list(v[1]) for l,v in zip('ABCD',opts)},'concept_reference_ids':sorted(set(a['refs']+b['refs'])),'numeric_checks':[c['checks'] for c in [a,b] if c['checks']],'difficulty_status':'EDITORIAL_ESTIMATE','review_status':'Automated structure, arithmetic and similarity checks; not independent expert certification.'})
  for l,(label,_) in zip('abcd',opts):q['option_'+l]=label
  taken.append(q);signatures.add(sig);exposure[a['id']]+=1;exposure[b['id']]+=1
 questions.extend(taken)
 print(subject,len(taken),flush=True)
assert len(questions)==1000
# Independent vocabulary fitted on final corpus. Do not silently lower the final audit threshold.
all_stems=[q['question_text'] for q in original+questions]
final_vec=TfidfVectorizer(preprocessor=norm,ngram_range=(1,2),stop_words='english',sublinear_tf=True)
m=final_vec.fit_transform(all_stems);scores=(m[len(original):]@m.T).toarray()
for i in range(len(questions)):scores[i,len(original)+i]=0
candidates=[]
for i,row in enumerate(scores):
 for j in np.flatnonzero(row>=.78):
  if j<len(original) or j-len(original)>i:candidates.append({'new':questions[i]['id'],'other':(original+questions)[j]['id'],'similarity':round(float(row[j]),4)})
assert not candidates,candidates[:10]
normalized=[norm(q['question_text']) for q in original+questions]
assert len(set(normalized[len(original):]))==1000
assert not(set(normalized[:len(original)])&set(normalized[len(original):]))
manifest={'original_sha256':ORIGINAL_SHA,'original_count':432,'original_scored_count':431,'layer2_count':1000,'subject_counts':dict(collections.Counter(q['subject'] for q in questions)),'primary_topic_counts':dict(collections.Counter(q['subject']+' / '+q['topic'] for q in questions)),'covered_topics':len(set((q['subject'],t) for q in questions for t in q['related_topics'])),'difficulty_counts':dict(collections.Counter(q['difficulty'] for q in questions)),'authored_cases':len(cases),'retained_cases':len(valid),'case_exclusions':excluded,'arithmetic_equations_checked':numeric_checks,'exact_duplicates':0,'digit_normalized_duplicates':0,'near_duplicate_threshold':.78,'near_duplicate_candidates':candidates,'max_new_to_original_similarity':round(float(scores[:,:len(original)].max()),4),'max_new_to_new_similarity':round(float(scores[:,len(original):].max()),4),'format_limitation':'Finite bank of distinct two-case combinations. Component cases intentionally recur in different combinations; no numeric-only variants are generated. Automated text similarity cannot prove absence of semantic duplicates.','case_exposure_range':[min(exposure.values()),max(exposure.values())]}
(ROOT/'dist/layer2.json').write_text(json.dumps(questions,ensure_ascii=False,separators=(',',':')))
(ROOT/'dist/layer2-summary.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
(ROOT/'scripts/layer2/cases.json').write_text(json.dumps(cases,ensure_ascii=False,indent=2))
print(json.dumps({k:v for k,v in manifest.items() if k!='primary_topic_counts'},indent=2))
