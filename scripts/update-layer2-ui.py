from pathlib import Path
p=Path('dist/app.js');s=p.read_text()
s=s.replace('breakdown,display}', 'breakdown,display,choosePractice,rememberQuestions,layerOf,ORIGINAL_LABEL,NEW_LABEL}')
s=s.replace("let theme=", "let newBank=[],allBank=[],newSeen=read('seen.new',[]),pool='original',bankLayer='original',originalPercent=50;\nconst isFull=()=>['full','new','mixed','auto'].includes(mode);\nconst poolLabel=q=>layerOf(q)==='new'?NEW_LABEL:ORIGINAL_LABEL;\nconst scopedBank=()=>bankLayer==='new'?newBank:bankLayer==='mixed'?allBank:bank;\nconst available=()=>pool==='new'?newBank:pool==='original'?eligible:[...eligible,...newBank];\nconst topicsFor=source=>[...new Set(source.filter(q=>!subject||q.subject===subject).flatMap(q=>q.related_topics||[q.topic]))].sort();\nlet theme=")
s=s.replace("session.ids.map(id=>bank.find(q=>q.id===id))", "session.ids.map(id=>allBank.find(q=>q.id===id))")
s=s.replace('THE COMPLETE SESSION','THE ORIGINAL BANK')
s=s.replace('<h2>Full Mock Test</h2>', '<h2>Original Bank CBT</h2>')
s=s.replace("${button('Full Mock Test','mode'", "${button('Full Mock — Original Bank','mode'")
# Insert a separate Layer-2 section; original home remains the default entry.
s=s.replace('<section class="subject-strip">', '${layer2Home()}<section class="subject-strip">')
pos=s.index('function select(')
s=s[:pos]+'''function layer2Home(){const used=eligible.filter(q=>seen.includes(q.id)).length;return `<section class="layer-section"><div class="section-heading"><div><div class="eyebrow">A SECOND PRACTICE LAYER</div><h2>Go beyond your original bank</h2></div><span class="layer-label new">${newBank.length} new questions</span></div><p class="muted">NEW — BANK-BASED PRACTICE. Paired application cases with worked explanations; not official PYQs.</p><div class="layer-cards"><section class="panel"><h2>New Bank-Based CBT</h2><p>100 new questions · 90 minutes<br>Two independent cases in each question.</p>${button('Start New CBT','mode','primary','data-mode="new" '+(newBank.length>=100?'':'disabled'))}</section><section class="panel"><h2>Mixed CBT</h2><p>Choose your Original + New split.<br>The pool is labelled on every question.</p>${button('Configure Mixed CBT','mode','secondary','data-mode="mixed" '+(newBank.length>=100?'':'disabled'))}</section><section class="panel"><h2>Continue with unseen questions</h2><p>${used} / 431 original questions seen. Fill a 100-question test with unseen originals, then new questions.</p>${button('Continue practice','mode','secondary','data-mode="auto" '+(newBank.length>=100?'':'disabled'))}</section></div><p class="small muted">This is a finite bank of 1,000 distinct paired-case combinations. Individual cases recur in different combinations. After a pool is exhausted, its least recently used questions return.</p>${newBank.length?'':'<p class="notice">The new bank could not load. Original Bank CBT remains available; reload to retry Layer 2.</p>'}</section>`;}
function poolControls(){return `<label>Question pool<select data-field="pool"><option value="original" ${pool==='original'?'selected':''}>Original bank</option><option value="new" ${pool==='new'?'selected':''}>New — Bank-Based Practice</option><option value="mixed" ${pool==='mixed'?'selected':''}>Original + New</option></select></label>${pool==='mixed'?ratioControl():''}`;}
function ratioControl(){return `<label>Original / New split<select data-field="ratio">${[0,25,50,75,100].map(n=>`<option value="${n}" ${originalPercent===n?'selected':''}>${n}% original / ${100-n}% new</option>`).join('')}</select></label>`;}
''' +s[pos:]
s=s.replace("function filtered(source=eligible){return source.filter(q=>(!subject||q.subject===subject)&&(!topic||q.topic===topic)&&(!difficulty||q.difficulty===difficulty));}", "function filtered(source=available()){return source.filter(q=>(!subject||q.subject===subject)&&(!topic||q.topic===topic||q.related_topics?.includes(topic))&&(!difficulty||q.difficulty===difficulty));}")
s=s.replace("{full:'Full Mock Test',subject:", "{full:'Full Mock — Original Bank',new:'Full Mock — New Practice',mixed:'Mixed Full Mock',auto:'Continue Practice',subject:")
s=s.replace("const pool=mode==='full'||mode==='quick'?eligible:filtered();const n=mode==='full'?100:Math.min(count,pool.length);", "const candidates=isFull()||mode==='quick'?available():filtered();const n=isFull()?Math.min(100,candidates.length):Math.min(count,candidates.length);")
s=s.replace("<h2>Make this session yours</h2>", "<h2>Make this session yours</h2>${mode==='mixed'?ratioControl():!isFull()?poolControls():''}${mode==='auto'?'<p class=\"notice\">Unseen original questions are used first. Any remaining places use the new practice bank.</p>':''}")
s=s.replace("[...new Set(eligible.filter(q=>q.subject===subject).map(q=>q.topic))].sort()", "topicsFor(available())")
s=s.replace("mode!=='full'?", "!isFull()?")
s=s.replace("mode==='full'?90", "isFull()?90")
s=s.replace('${pool.length} eligible questions.', '${candidates.length} eligible questions.')
start=s.index('function start()');end=s.index('function explanation(',start)
s=s[:start]+'''function start(){const candidates=isFull()||mode==='quick'?available():filtered();const qs=choosePractice({original:candidates.filter(q=>layerOf(q)==='original'),newBank:candidates.filter(q=>layerOf(q)==='new'),count:isFull()?100:count,pool,originalPercent,originalHistory:seen,newHistory:newSeen});if(!qs.length)return;seen=rememberQuestions(seen,qs.filter(q=>layerOf(q)==='original').map(q=>q.id));newSeen=rememberQuestions(newSeen,qs.filter(q=>layerOf(q)==='new').map(q=>q.id));write('seen',seen);write('seen.new',newSeen);session={id:crypto.randomUUID(),name:{full:'Full Mock Test',new:'Full Mock — New Practice',mixed:'Mixed Full Mock',auto:'Continue Practice',subject:subject+' Practice',topic:topic+' Practice',quick:'Quick Practice'}[mode],practicePool:pool,ids:qs.map(q=>q.id),answers:{},marked:{},index:0,started:Date.now(),deadline:Date.now()+(isFull()?90:Math.max(1,Math.ceil(qs.length*.9)))*60000,submitted:false};save();view='practice';reviewResult=false;render();window.scrollTo(0,0);}
''' +s[end:]
s=s.replace('<div class="subject-line">${esc(q.subject)} <span>/</span> ${esc(q.topic)}</div>', '<div class="subject-line"><span class="layer-label ${layerOf(q)}">${poolLabel(q)}</span><br>${esc(q.subject)} <span>/</span> ${esc(q.layer===\'new\'?q.subtopic:q.topic)}</div>')
s=s.replace("result.ids.map(id=>bank.find(q=>q.id===id))", "result.ids.map(id=>allBank.find(q=>q.id===id))")
s=s.replace('<section class="panel"><h2>Subject performance</h2>', '${layerResults(qs,result.answers)}<section class="panel"><h2>Subject performance</h2>')
pos=s.index('function browse()')
s=s[:pos]+'''function layerResults(qs,answers){if(!qs.some(q=>layerOf(q)==='new'))return '';return `<section class="panel"><h2>Performance by question pool</h2>${performanceTable(['original','new'].map(layer=>({name:layer==='new'?NEW_LABEL:ORIGINAL_LABEL,...score(qs.filter(q=>layerOf(q)===layer),answers)})))}</section>`;}
''' +s[pos:]
s=s.replace('const qs=filtered(bank),pages=', 'const qs=filtered(scopedBank()),pages=')
s=s.replace('All 432 supplied questions, with their answers and explanations.', "Original records and new practice are kept in separate pools. Answers are shown only when you open the explanation.")
s=s.replace('<div class="filters">', '<div class="filters"><label>Question pool<select data-field="bankLayer"><option value="original" ${bankLayer===\'original\'?\'selected\':\'\'}>Original bank (432)</option><option value="new" ${bankLayer===\'new\'?\'selected\':\'\'}>New practice (${newBank.length})</option><option value="mixed" ${bankLayer===\'mixed\'?\'selected\':\'\'}>Both pools</option></select></label>')
s=s.replace("[...new Set(bank.filter(q=>!subject||q.subject===subject).map(q=>q.topic))].sort()", "topicsFor(scopedBank())")
s=s.replace('<span class="source-tag">${esc(q.source_type)}</span>', '<span class="layer-label ${layerOf(q)}">${poolLabel(q)}</span><span class="source-tag">${esc(q.source_type)}</span>')
s=s.replace("'generation_method'].filter", "'generation_method','related_topics'].filter")
s=s.replace("case 'bank':view='bank';subject='';", "case 'bank':view='bank';bankLayer='original';subject='';")
s=s.replace("case 'mode':mode=b.dataset.mode;subject=", "case 'mode':mode=b.dataset.mode;pool=mode==='new'?'new':mode==='mixed'?'mixed':mode==='auto'?'auto':'original';subject=")
s=s.replace("eligible.find(q=>q.subject===subject)?.topic", "available().find(q=>q.subject===subject)?.topic")
s=s.replace("if(k==='subject')", "if(k==='pool'){pool=e.target.value;topic='';}if(k==='ratio')originalPercent=Number(e.target.value);if(k==='bankLayer'){bankLayer=e.target.value;subject='';topic='';difficulty='';}if(k==='subject')")
s=s.replace("bank=await r.json();eligible=", "bank=await r.json();try{const extra=await fetch('/layer2.json');if(extra.ok)newBank=await extra.json();}catch{newBank=[];}allBank=[...bank,...newBank];eligible=")
s=s.replace("!bank.some(q=>q.id===id)", "!allBank.some(q=>q.id===id)")
# Storage warnings and original-data defaults remain unchanged.
p.write_text(s)
p=Path('dist/core.js');s=p.read_text().replace("q.subject+' · '+q.topic", "q.subject+' · '+(q.layer==='new'?q.subtopic:q.topic)");p.write_text(s)
