from pathlib import Path
import json,hashlib,re,collections
from sklearn.feature_extraction.text import TfidfVectorizer
ROOT=Path(__file__).resolve().parents[2]
old=json.loads((ROOT/'dist/questions.json').read_text());new=json.loads((ROOT/'dist/layer2.json').read_text());report=json.loads((ROOT/'dist/layer2-summary.json').read_text())
assert hashlib.sha256((ROOT/'dist/questions.json').read_bytes()).hexdigest()==report['original_sha256']
def norm(s):return ' '.join(re.sub(r'[^a-z0-9 ]',' ',re.sub(r'\d+(?:\.\d+)?',' NUMBER ',s.lower())).split())
texts=[q['question_text'] for q in old+new];normalized=[norm(t) for t in texts]
assert len(new)==1000 and len(set(normalized[len(old):]))==1000
assert not(set(normalized[:len(old)])&set(normalized[len(old):]))
v=TfidfVectorizer(preprocessor=norm,ngram_range=(1,2),stop_words='english',sublinear_tf=True);m=v.fit_transform(texts);sim=(m[len(old):]@m.T).toarray()
for i in range(len(new)):sim[i,len(old)+i]=0
assert float(sim.max())<report['near_duplicate_threshold']
report['max_new_to_original_similarity']=round(float(sim[:,:len(old)].max()),4);report['max_new_to_new_similarity']=round(float(sim[:,len(old):].max()),4)
(ROOT/'dist/layer2-summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print('Final duplicate audit passed:',report['max_new_to_original_similarity'],report['max_new_to_new_similarity'])
