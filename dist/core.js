export const letters = ['A','B','C','D'];
export function selectQuestions(pool, count, seen=[], random=Math.random) {
 const shuffle = a => {a=[...a]; for(let i=a.length-1;i>0;i--){const j=Math.floor(random()*(i+1));[a[i],a[j]]=[a[j],a[i]];}return a;};
 const old=new Set(seen); const unique=[...new Map(pool.map(q=>[q.id,q])).values()];
 return [...shuffle(unique.filter(q=>!old.has(q.id))),...shuffle(unique.filter(q=>old.has(q.id)))].slice(0,count);
}
export function remaining(deadline,now=Date.now()){return Math.max(0,Math.ceil((deadline-now)/1000));}
export function score(questions,answers){
 const correct=questions.filter(q=>answers[q.id]===q.correct_option).length;
 const attempted=questions.filter(q=>letters.includes(answers[q.id])).length;
 const wrong=attempted-correct;
 return {total:questions.length,attempted,correct,wrong,unanswered:questions.length-attempted,marks:correct-wrong/3,accuracy:attempted?correct/attempted*100:0};
}
export function breakdown(questions,answers,field){
 const groups=new Map();for(const q of questions){const key=field==='topic'?q.subject+' · '+(q.layer==='new'?q.subtopic:q.topic):q[field];if(!groups.has(key))groups.set(key,[]);groups.get(key).push(q);}
 return [...groups].map(([name,qs])=>({name,...score(qs,answers)})).sort((a,b)=>b.wrong-a.wrong||a.name.localeCompare(b.name));
}
// Repair common mojibake only at display time. Source records remain unchanged.
export function display(value){
 let s=typeof value==='string'?value:value==null?'':JSON.stringify(value);
 const map={'€':128,'‚':130,'ƒ':131,'„':132,'…':133,'†':134,'‡':135,'ˆ':136,'‰':137,'Š':138,'‹':139,'Œ':140,'Ž':142,'‘':145,'’':146,'“':147,'”':148,'•':149,'–':150,'—':151,'˜':152,'™':153,'š':154,'›':155,'œ':156,'ž':158,'Ÿ':159};
 for(let i=0;i<2;i++){if(!/[ÂÃâ]/.test(s))break;try{const bytes=[...s].map(c=>map[c]??c.charCodeAt(0));if(bytes.some(b=>b>255))break;const fixed=new TextDecoder('utf-8',{fatal:true}).decode(new Uint8Array(bytes));if(fixed===s)break;s=fixed;}catch{break;}}
 return s;
}

export const ORIGINAL_LABEL = 'ORIGINAL BANK';
export const NEW_LABEL = 'NEW — BANK-BASED PRACTICE';
export const layerOf = q => q?.layer === 'new' ? 'new' : 'original';
export function choosePractice({original,newBank,count=100,pool='original',originalPercent=50,originalHistory=[],newHistory=[],random=Math.random}) {
 const pick=(bank,n,history)=>{
  const unique=[...new Map(bank.map(q=>[q.id,q])).values()];
  const used=new Set(history);const fresh=selectQuestions(unique.filter(q=>!used.has(q.id)),n,[],random);
  if(fresh.length<n){const chosen=new Set(fresh.map(q=>q.id));const order=new Map(history.map((id,i)=>[id,i]));const old=unique.filter(q=>!chosen.has(q.id)).sort((a,b)=>(order.get(a.id)??-1)-(order.get(b.id)??-1));fresh.push(...old.slice(0,n-fresh.length));}
  return fresh;
 };
 let nOriginal=pool==='original'?count:pool==='new'?0:pool==='auto'?Math.min(count,original.filter(q=>!new Set(originalHistory).has(q.id)).length):Math.round(count*originalPercent/100);
 let nNew=count-nOriginal;
 if(pool==='mixed'||pool==='auto'){
  if(nOriginal>original.length){nNew+=nOriginal-original.length;nOriginal=original.length;}
  if(nNew>newBank.length){nOriginal=Math.min(original.length,nOriginal+nNew-newBank.length);nNew=newBank.length;}
 }
 const chosen=[...pick(original,nOriginal,originalHistory),...pick(newBank,nNew,newHistory)];
 return selectQuestions(chosen,chosen.length,[],random);
}
export function rememberQuestions(history,ids){const current=new Set(ids);return [...history.filter(id=>!current.has(id)),...ids];}
