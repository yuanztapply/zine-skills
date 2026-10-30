const MM=96/25.4;
const NS='http://www.w3.org/2000/svg';
function makeNode(tag,attrs={}){const e=document.createElementNS(NS,tag);for(const[k,v]of Object.entries(attrs))e.setAttribute(k,String(v));return e}
function hash(s){let n=2166136261;for(const c of s)n=Math.imul(n^c.charCodeAt(0),16777619);return n>>>0}
function random(seed){let n=seed>>>0;return()=>{n=(Math.imul(1664525,n)+1013904223)>>>0;return n/4294967296}}
function localPosition(w,e){let x=0,y=0,n=w;while(n&&n!==e){x+=n.offsetLeft;y+=n.offsetTop;n=n.offsetParent}return{x,y}}
function inkColor(e,name,fallback){return getComputedStyle(e).getPropertyValue(name).trim()||fallback}

function packContour(e){
 const profile=JSON.parse(e.dataset.profile);
 const style=getComputedStyle(e),fontPx=parseFloat(style.fontSize),step=fontPx/MM*1.055;
 let words=[...e.querySelectorAll('.word')];
 if(!words.length)return;
 const ctx=document.createElement('canvas').getContext('2d');ctx.font=`${style.fontWeight} ${style.fontSize} ${style.fontFamily}`;
 const space=ctx.measureText(' ').width+fontPx*.03;
 const widths=words.map(w=>w.offsetWidth+parseFloat(getComputedStyle(w).marginRight||0));
 e.innerHTML='';e.style.padding='0';
 let index=0,row=0;
 while(index<words.length){
  const [left,width]=profile[Math.min(row,profile.length-1)];
  const line=document.createElement('div');line.className='contour-line';
  line.style.cssText=`left:${left}mm;top:${row*step}mm;width:${width}mm`;
  let used=0;
  while(index<words.length){
   const next=widths[index]+(used?space:0);
   if(used&&used+next>width*MM-1.8)break;
   if(used)line.appendChild(document.createTextNode(' '));
   line.appendChild(words[index]);used+=next;index++;
  }
  e.appendChild(line);row++;
 }
 e.style.height=`${row*step+fontPx/MM*.25}mm`;
 e.dataset.spillLines=String(Math.max(0,row-profile.length));
 e.dataset.lines=String(row);
}

function paperGround(e){
 e.querySelectorAll(':scope > .paper-ground').forEach(n=>n.remove());
 if(!e.classList.contains('paper')&&!e.classList.contains('blackslip'))return;
 const spans=[...e.querySelectorAll('.word,.g')].filter(w=>w.textContent.trim());
 if(!spans.length)return;
 const display=e.classList.contains('display'),padX=(display?4.3:2.7)*MM,padY=(display?2.8:1.35)*MM;
 const rows=[];
 for(const w of spans){
  const p=localPosition(w,e),top=p.y,bottom=top+w.offsetHeight;
  let row=rows.find(r=>Math.abs(r.top-top)<2.5);
  if(!row){row={left:p.x,right:p.x+w.offsetWidth,top,bottom};rows.push(row)}
  else{row.left=Math.min(row.left,p.x);row.right=Math.max(row.right,p.x+w.offsetWidth);row.bottom=Math.max(row.bottom,bottom)}
 }
 const rects=rows.map(r=>({left:r.left-padX,right:r.right+padX,top:r.top-padY,bottom:r.bottom+padY}));
 const ys=[...new Set(rects.flatMap(r=>[r.top,r.bottom]))].sort((a,b)=>a-b);
 const strips=[];
 for(let i=0;i<ys.length-1;i++){
  const mid=(ys[i]+ys[i+1])/2,active=rects.filter(r=>mid>=r.top&&mid<=r.bottom);
  if(active.length)strips.push({top:ys[i],bottom:ys[i+1],left:Math.min(...active.map(r=>r.left)),right:Math.max(...active.map(r=>r.right))});
 }
 if(!strips.length)return;
 const rnd=random(hash(e.dataset.raw||e.innerText));
 const points=[];
 const first=strips[0],last=strips[strips.length-1];
 // Only the paper is torn. Every ink-bearing row has an untouched safety margin.
 for(let x=first.left;x<first.right;x+=MM*(2.6+rnd()*3.8))points.push([x,first.top-MM*(.15+rnd()*1.05)]);
 points.push([first.right,first.top]);
 for(const s of strips){points.push([s.right,s.top]);for(let y=s.top+MM*.8;y<s.bottom;y+=MM*(1.2+rnd()*1.7))points.push([s.right+MM*(.1+rnd()*.9),y]);points.push([s.right,s.bottom])}
 for(let x=last.right;x>last.left;x-=MM*(2.8+rnd()*3.3))points.push([x,last.bottom+MM*(.1+rnd()*.9)]);
 points.push([last.left,last.bottom]);
 for(const s of [...strips].reverse()){points.push([s.left,s.bottom]);for(let y=s.bottom-MM*.8;y>s.top;y-=MM*(1.1+rnd()*1.9))points.push([s.left-MM*(.1+rnd()*.95),y]);points.push([s.left,s.top])}
 const w=e.offsetWidth,h=e.offsetHeight;
 const svg=makeNode('svg',{class:'paper-ground',viewBox:`0 0 ${w} ${h}`,width:w,height:h,'aria-hidden':'true'});
 svg.style.cssText=`left:0;top:0;width:${w}px;height:${h}px;overflow:visible`;
 const path=makeNode('path',{d:'M'+points.map(p=>p.map(v=>v.toFixed(2)).join(' ')).join('L')+'Z',fill:e.classList.contains('blackslip')?inkColor(e,'--ink','#111110'):inkColor(e,'--paper','#e8e8e2')});
 svg.appendChild(path);
 if(hash(e.dataset.raw||'')%3===0){
  for(let i=0;i<4;i++){
   const s=strips[Math.floor(rnd()*strips.length)],y=s.top+rnd()*(s.bottom-s.top),x=s.right;
   svg.appendChild(makeNode('path',{d:`M${x-.2} ${y}l${MM*(.45+rnd()*.8)} ${MM*(rnd()-.5)}`,stroke:path.getAttribute('fill'),'stroke-width':.55,'stroke-linecap':'round'}));
  }
 }
 e.prepend(svg);
}

function fitCurve(e){
 const text=e.querySelector('text'),path=e.querySelector('defs path'),tp=e.querySelector('textPath');
 if(!text||!path||!tp)return;
 const desired=Number(text.dataset.originalSize||text.getAttribute('font-size'));
 text.dataset.originalSize=String(desired);
 text.setAttribute('font-size',String(desired));
 const available=path.getTotalLength()-7;
 let length=text.getComputedTextLength();
 const minimum=Number(e.dataset.minPt||18)*25.4/72;
 if(length>available){text.setAttribute('font-size',String(Math.max(minimum,desired*available/length)));length=text.getComputedTextLength()}
 e.dataset.actualPt=String(Number(text.getAttribute('font-size'))*72/25.4);
 e.dataset.curveFit=length<=available+.05?'true':'false';
}

function restyleAll(){document.querySelectorAll('.contour').forEach(packContour);document.querySelectorAll('.curve-wrap').forEach(fitCurve);document.querySelectorAll('.paper,.blackslip').forEach(paperGround)}
window.contourReady=document.fonts.ready.then(()=>{restyleAll();return true});

function toggleEdit(){
 const on=!document.body.classList.contains('editing');document.body.classList.toggle('editing',on);
 document.querySelectorAll('[data-edit]').forEach(e=>{e.contentEditable=on&&!e.classList.contains('curve-wrap')?'true':'false';e.tabIndex=on?0:-1});
 document.getElementById('editBtn').textContent=on?'Finish editing':'Edit text';
}
document.querySelectorAll('[data-edit]').forEach(e=>{
 if(e.classList.contains('curve-wrap')){
  const edit=()=>{if(!document.body.classList.contains('editing'))return;const raw=prompt('Edit curved text:',e.dataset.raw);if(raw!==null){e.dataset.raw=raw;e.querySelector('textPath').textContent=raw;fitCurve(e)}};
  e.addEventListener('click',edit);e.addEventListener('keydown',ev=>{if(ev.key==='Enter'){ev.preventDefault();edit()}});
 }else e.addEventListener('blur',()=>{
  e.dataset.raw=e.innerText.replace(/\s+/g,' ').trim();
  if(e.classList.contains('contour')){
   const raw=e.dataset.raw;e.innerHTML='';
   raw.split(' ').forEach((word,i)=>{if(i)e.appendChild(document.createTextNode(' '));const span=document.createElement('span');span.className='word';span.textContent=word;e.appendChild(span)});
   packContour(e);
  }
  paperGround(e);
 });
});
function saveCopy(){
 document.activeElement?.blur();
 const d=document.documentElement.cloneNode(true);d.querySelector('body').classList.remove('editing');
 d.querySelectorAll('[contenteditable]').forEach(e=>e.removeAttribute('contenteditable'));
 d.querySelector('#editBtn').textContent='Edit text';
 const blob=new Blob(['<!DOCTYPE html>\n'+d.outerHTML],{type:'text/html;charset=utf-8'}),a=document.createElement('a');
 a.href=URL.createObjectURL(blob);a.download='ethnography_zine_edited.html';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),2000);
}
