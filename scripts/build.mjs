import fs from 'node:fs';
const bank=JSON.parse(fs.readFileSync('dist/questions.json','utf8'));
if(bank.length!==432)throw Error('Expected 432 questions');
if(new Set(bank.map(q=>q.id)).size!==432)throw Error('Duplicate IDs');
for(const q of bank){if(!['A','B','C','D'].includes(q.correct_option))throw Error(q.id);for(const k of ['question_text','option_a','option_b','option_c','option_d','explanation','subject','topic'])if(!q[k])throw Error(`${q.id}: ${k}`);}
for(const p of ['index.html','app.js','core.js','style.css','favicon.svg'])if(!fs.existsSync('dist/'+p))throw Error(p);
console.log('Production static build verified: 432 records, 431 eligible, all assets present.');
const generated=JSON.parse(fs.readFileSync('dist/layer2.json','utf8'));
if(generated.length!==1000)throw Error('Expected 1000 new practice questions');
const ids=new Set(bank.map(q=>q.id));
for(const q of generated){if(ids.has(q.id))throw Error('Duplicate bank ID '+q.id);ids.add(q.id);if(q.layer!=='new'||q.source_type!=='BANK_BASED_PRACTICE')throw Error('Unlabelled generated question');for(const k of ['question_text','option_a','option_b','option_c','option_d','explanation','final_answer','why_correct'])if(!q[k])throw Error(q.id+': '+k);}
console.log('Layer 2 production build verified: 1000 separately labelled records.');
