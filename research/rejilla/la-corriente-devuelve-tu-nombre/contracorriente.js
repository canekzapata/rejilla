/* Contracorriente: mismas trayectorias de coeficientes y reloj que el audio.
   Las líneas son líneas de corriente de un corte instantáneo; no trayectorias 3D. */
(async()=>{'use strict';
const get=p=>fetch(p).then(r=>{if(!r.ok)throw Error(p+' '+r.status);return r.json();});
const [P,E,AV]=await Promise.all([get('/data/partitura.json'),get('/data/eco.json'),get('/data/audio-visual.json')]);
const W=innerWidth,H=innerHeight,cv=document.getElementById('salida');cv.width=W;cv.height=H;
const base=document.createElement('canvas'),mask=document.createElement('canvas'),fx=document.createElement('canvas');base.width=fx.width=W;base.height=fx.height=H;mask.width=64;mask.height=36;
const cx=base.getContext('2d'),mx=mask.getContext('2d'),dst=cv.getContext('2d'),K=E.K,M=E.dimension,N=E.N;
let data={};for(const c of ['ideal','viscoso'])for(const f of ['ida','vuelta'])data[c+'-'+f]=new Float32Array(await fetch('/data/'+c+'-'+f+'.f32').then(r=>r.arrayBuffer()));
let hydra=new Hydra({canvas:fx,width:W,height:H,detectAudio:false,enableStreamCapture:false,autoLoop:false,makeGlobal:false});hydra.setResolution(W,H);hydra.synth.s0.init({src:base,dynamic:true});hydra.synth.s1.init({src:mask,dynamic:true});
const estado={t:0,bajo:0,residuo:0,hydra:true,error:'',preset:'contracorriente'};
new Function('synth','control',`with(synth){src(s0).modulate(src(s1),()=>.018+control.bajo*.018).blend(src(o0).scale(1.0015),.16).add(src(s1).color(.12,.035,.22),.16).out(o0);}`)(hydra.synth,estado);
const pos=K.map((k,i)=>({k,i})).filter(({k})=>k[0]>0||(k[0]===0&&k[1]>0)||(k[0]===0&&k[1]===0&&k[2]>0));
function coefficients(t,c){let a=P.eco_musical.fin_ida,b=P.eco_musical.fin_vuelta;if(t>=b)return Float32Array.from(E[c].retornado);let f=t<a?'ida':'vuelta',q=Math.max(0,Math.min(1,t<a?t/a:(t-a)/(b-a)))*N,i=Math.floor(q),j=Math.min(N,i+1),r=q-i,u=data[c+'-'+f],v=new Float32Array(M);for(let k=0;k<M;k++)v[k]=u[i*M+k]*(1-r)+u[j*M+k]*r;return v;}
function field(u,x,y,z){let v=[0,0,0];for(let {k,i} of pos){let a=k[0]*x+k[1]*y+k[2]*z,c=Math.cos(a),s=Math.sin(a);for(let j=0;j<3;j++)v[j]+=2*(u[i*6+j*2]*c-u[i*6+j*2+1]*s);}return v;}
function project(x,y,z){return [W*(.06+.88*x/(Math.PI*2)),H*(.22+.6*y/(Math.PI*2))-z*H*.043];}
function paso(t,dt=1/30){estado.t=t;estado.bajo=AV.bajo[Math.min(AV.bajo.length-1,Math.round(t*AV.fps))]||0;const ideal=coefficients(t,'ideal'),visc=coefficients(t,'viscoso'),diff=Float32Array.from(visc,(x,i)=>x-ideal[i]);estado.residuo=Math.sqrt(diff.reduce((a,b)=>a+b*b,0));
 cx.fillStyle='#090b19';cx.fillRect(0,0,W,H);
 const grad=cx.createRadialGradient(W*.5,H*.55,0,W*.5,H*.55,W*.65);grad.addColorStop(0,'#17122b');grad.addColorStop(1,'#090b19');cx.fillStyle=grad;cx.fillRect(0,0,W,H);
 for(const [u,col] of [[ideal,'#9c8aff'],[visc,'#f68e60']]){
  cx.strokeStyle=col;cx.lineWidth=(.65+estado.bajo*.7)*W/1280;cx.globalAlpha=.72;
  for(let row=0;row<11;row++)for(let coln=0;coln<17;coln++){
   let x=.2+coln*.35,y=.25+row*.54,z=.4;cx.beginPath();let a=project(x,y,0);cx.moveTo(...a);
   for(let j=0;j<13;j++){let v=field(u,x,y,z);x+=v[0]*.11;y+=v[1]*.11;z+=v[2]*.11;let p=project(x,y,z-.4);cx.lineTo(...p);}cx.stroke();
  }
 }
 cx.globalAlpha=1;const image=mx.createImageData(64,36);
 for(let y=0;y<36;y++)for(let x=0;x<64;x++){let v=field(diff,x/64*Math.PI*2,y/36*Math.PI*2,.4),n=Math.min(1,Math.hypot(...v)*1.8),i=(y*64+x)*4;image.data[i]=n*150;image.data[i+1]=n*90;image.data[i+2]=n*225;image.data[i+3]=255;}mx.putImageData(image,0,0);
 hydra.tick(dt*1000);dst.drawImage(fx,0,0);
 const sec=P.secciones.find(s=>t>=s.t&&t<s.t1),title=sec?sec.nombre.toUpperCase():'EL NOMBRE QUE QUEDÓ';dst.fillStyle='#e5dff4';dst.font=`${Math.round(H*.024)}px Consolas,monospace`;dst.fillText(title,W*.055,H*.10);
 dst.font=`${Math.round(H*.018)}px Consolas,monospace`;dst.fillStyle='#a99ccb';dst.fillText('LA CORRIENTE DEVUELVE TU NOMBRE',W*.055,H*.92);dst.fillStyle='#dd997e';dst.fillText('CANEK ZAPATA · 2026',W*.055,H*.96);
 return estado;
}
window.corriente={paso,estado,base,mask,P,E};window.lista=true;paso(0,0);
})().catch(e=>{window.errorCorriente=String(e);document.getElementById('fallo').textContent=e.message;});
