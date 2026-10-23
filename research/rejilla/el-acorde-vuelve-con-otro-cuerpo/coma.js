/* Preset coma: partitura, envolvente medida y dos memorias; Hydra procesa el campo. */
(async()=>{try{
 const [P,B,A]=await Promise.all(['partitura.json','batidos.json','audio-visual.json'].map(f=>fetch('/data/'+f).then(r=>{if(!r.ok)throw Error(f);return r.json();}))),W=innerWidth,H=innerHeight,C=document.getElementById('pantalla');C.width=W;C.height=H;
 const base=document.createElement('canvas');base.width=W;base.height=H;const g=base.getContext('2d'),mask=document.createElement('canvas');mask.width=W;mask.height=H;const m=mask.getContext('2d');let T=0,beat=0,energy=0;
 const hydra=new Hydra({canvas:C,width:W,height:H,detectAudio:false,autoLoop:false,makeGlobal:true});s0.init({src:base});s1.init({src:mask});
 src(s0).blend(src(o0).scale(()=>1.001+beat*.0014).rotate(()=>.0004*(beat-.5)),.12).add(src(s1).color(.32,.16,.06),()=>.035+energy*.05).saturate(1.04).out(o0);
 const colors=['#edbc82','#74bfc0'];const lerp=(a,b,u)=>a+(b-a)*u;
 function at(t){let i=Math.min(A.rms.length-1,Math.max(0,Math.floor(t*A.hz)));return A.rms[i]||0;}
 function freq(e,t){let u=Math.min(1,Math.max(0,(t-e.t)/e.dur));u=u*u*(3-2*u);return e.midi+((e.m2??e.midi)-e.midi)*u;}
 function path(j,shift,alpha,fold,t){const cx=W*.5,cy=H*.48;g.beginPath();for(let i=0;i<=720;i++){const u=i/720,th=2*Math.PI*u;
  const r=1+.065*Math.cos(5*th+T*.14)+.035*Math.sin(9*th-T*.11),sep=shift*W*.018;
  const x=cx+W*(.335-j*.0032)*Math.cos(th)*r+sep*Math.sin(th*3+T*.2);
  const y=cy+H*(.29-j*.0022)*Math.sin(th)*r+fold*H*.11*Math.sin(2*th+j*.08)+H*.032*Math.sin(th*4+T*.2+j*.13)*Math.cos(th);
  i?g.lineTo(x,y):g.moveTo(x,y);
 }g.closePath();g.strokeStyle=alpha;g.lineWidth=.7*W/1280;g.stroke();}
 function paso(t,dt=1/30){T=t;const sec=P.secciones.find(s=>t>=s.t&&t<s.t1)||P.secciones.at(-1),tau=Math.max(0,t-52*P.compas),travel=Math.min(1,tau/(12*P.compas)),cross=sec.id==='IV';
  const ix=Math.min(B.picos_s.length-1,Math.max(0,B.picos_s.findIndex(p=>p>=tau%64))),near=B.picos_s[ix]??0;beat=t<52*P.compas?0:Math.exp(-Math.pow(((tau%64)-near)/.15,2));energy=at(t);const env=Math.abs(Math.cos(Math.PI*B.diferencia_Hz*tau));
  g.fillStyle='#10191f';g.fillRect(0,0,W,H);const grd=g.createRadialGradient(W*.51,H*.45,H*.04,W*.5,H*.5,W*.65);grd.addColorStop(0,'#243139');grd.addColorStop(1,'#0a1116');g.fillStyle=grd;g.fillRect(0,0,W,H);
  g.save();g.translate(W*.5,H*.47);g.rotate(-.14);g.translate(-W*.5,-H*.47);
  let folding=cross?Math.sin((t-40*P.compas)/(12*P.compas)*Math.PI*3):.2*Math.sin(t*.07);
  for(let side=0;side<2;side++)for(let j=0;j<35;j++){const a=.12+.5*(1-j/40);path(j,(side?1:-1)*(1+travel*3.5+env),side?`rgba(116,191,192,${a})`:`rgba(237,188,130,${a})`,folding*(side?1:-1)+travel*.42*(side?1:-1),t);}
  // Las notas y los cruces proceden de la partitura; no se generan al azar por cuadro.
  for(const [c,col] of [['ep-tema',colors[0]],['fuelle-alto',colors[1]],['fuelle-bajo',colors[0]],['chelo','#ddaab7']])for(const e of P.eventos[c]){
   const age=t-e.t;if(age<-.4||age>e.dur+3)continue;const note=freq(e,t),u=Math.max(0,age)/(e.dur+3),theta=(note-33)/48*Math.PI*1.4+.3;
   const x=W*.5+Math.cos(theta)*(W*.3)*(1-u*.08),y=H*.48+Math.sin(theta)*H*.25;g.globalAlpha=Math.min(1,Math.max(0,1-u))*.8;g.strokeStyle=col;g.lineWidth=1.3;g.beginPath();g.arc(x,y,(3+e.vel*5+energy*4)*W/1280,0,2*Math.PI);g.stroke();g.globalAlpha=1;
  }
  if(t>=52*P.compas){g.strokeStyle=`rgba(233,222,204,${.12+.22*env})`;g.lineWidth=.6;for(let j=0;j<9;j++){g.beginPath();g.ellipse(W*.5,H*.48,W*(.11+j*.006)*(1+.08*env),H*(.09+j*.005),travel*.15,0,2*Math.PI);g.stroke();}}
  g.restore();
  // Treinta pequeños pentagramas: memoria de las entradas, cada capa con pausa propia.
  const names=Object.keys(P.eventos);for(let j=0;j<names.length;j++){const y=H*(.77+j*.0046),on=P.eventos[names[j]].filter(e=>e.t<=t&&e.t+Math.min(e.dur,4)>=t);g.strokeStyle=j<14?'#b08f6b':'#507d83';g.globalAlpha=.1;g.beginPath();g.moveTo(W*.12,y);g.lineTo(W*.88,y);g.stroke();g.globalAlpha=.7;for(const e of on){let x=W*(.12+.76*((t-e.t)/Math.max(4,e.dur)));g.fillStyle=j<14?colors[0]:colors[1];g.fillRect(x,y,Math.max(2,W*.003),1.2);}g.globalAlpha=1;}
  m.clearRect(0,0,W,H);m.strokeStyle=`rgba(240,183,120,${beat*.25})`;m.lineWidth=1;m.beginPath();m.ellipse(W*.5,H*.48,W*.37,H*.31,0,0,Math.PI*2);m.stroke();
  hydra.tick(Math.max(0,dt)*1000);const active=P.solo_D.filter(e=>e.t<=t).at(-1);window.coma.estado={t,seccion:sec.id,protagonista:sec.protagonista,coma_cents:P.coma_cents,raiz_Hz:active?.root_Hz??220,envolvente:env,disparo:beat,hydra:true};return window.coma.estado;
 }
 window.coma={paso,base,estado:{},hydra};window.lista=true;paso(0,0);const render=new URLSearchParams(location.search).has('render');document.body.classList.toggle('render',render);let playing=true,last=performance.now(),cursor=0;const slider=document.getElementById('posicion');slider.max=P.duracion;slider.oninput=()=>{cursor=+slider.value;paso(cursor,1/30);};document.getElementById('play').onclick=()=>playing=!playing;
 function frame(now){let dt=Math.min(.05,(now-last)/1000);last=now;if(!render&&playing){cursor=(cursor+dt)%P.duracion;paso(cursor,dt);slider.value=cursor;document.getElementById('tiempo').textContent=Math.floor(cursor/60)+':'+String(Math.floor(cursor%60)).padStart(2,'0');}requestAnimationFrame(frame);}requestAnimationFrame(frame);
}catch(e){window.errorComa=String(e);document.body.textContent=String(e);}})();
