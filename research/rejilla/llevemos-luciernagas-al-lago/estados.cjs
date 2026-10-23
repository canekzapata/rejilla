/* Sampled observations of GuitarraMemoria and the fixed Schmitt organ.
 * Modal state is never cleared by an output gate. No family/preset substitution.
 */
const fs=require('fs'),path=require('path');
const zlib=require('zlib');
const BASE=__dirname,OUT=process.env.LUCI_AUDIO_OUT||path.join(BASE,fs.readFileSync(path.join(BASE,'REALIZACION-ACTUAL.txt'),'utf8').trim());
const FIX=path.join(BASE,'luciernagas-reescritura-s1-29d4afe5aad2');
const P=JSON.parse(fs.readFileSync(path.join(OUT,'partitura.json'),'utf8')),SR=48000,N=Math.ceil(P.duracion*SR),TAU=2*Math.PI;
const hz=m=>440*2**((m-69)/12),clamp=(x,l,h)=>Math.max(l,Math.min(h,x));
const save=(name,a)=>{const f=path.join(OUT,'render',name+'.f32.gz');if(fs.existsSync(f))throw Error('No sobrescribir '+f);fs.writeFileSync(f,zlib.gzipSync(Buffer.from(a.buffer),{level:3}));};
function interp(points,t){if(t<=points[0][0])return points[0][1];let l=0,r=points.length-1;while(l+1<r){const m=(l+r)>>1;if(points[m][0]<=t)l=m;else r=m;}if(t>=points[r][0])return points[r][1];return points[l][1]+(points[r][1]-points[l][1])*(t-points[l][0])/(points[r][0]-points[l][0]);}
function guitar(){
 const start=Date.now(),evs=P.eventos.guitarra.slice().sort((a,b)=>a.t-b.t),M=144;
 const re=new Float64Array(M),im=new Float64Array(M),phase=new Float64Array(M),mid=new Float64Array([40,45,50,55,59,64]);
 const out=new Float32Array(N*2),events=evs.map(e=>[Math.round(e.t*SR),e]);let ei=0,seed=P.semilla>>>0;
 const rng=()=>{seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return (seed>>>0)/4294967296*2-1;};
 const route=JSON.parse(fs.readFileSync(path.join(FIX,'datos/recorrido.json'),'utf8')).muestras.map(e=>[e.t,e.pendiente]);
 const enc=JSON.parse(fs.readFileSync(path.join(FIX,'datos/encuentros.json'),'utf8'));
 const shifts=[0,1,2].map(j=>[[0,0],...enc.flatMap(e=>[[e.t,e.antes[j]],[e.t+.03,e.despues[j]]])]);
 const contacts=evs.filter(e=>e.contacto).map(e=>({...e,load:0,last:-1}));let noiseLP=0;const metrics=[];
 const cap=evs.find(e=>e.id==='r00117');
 function gesture(e){const p=e.parametros_motor;if(!p)return;
  const s=p.cuerda,c=p.caja,kind=p.gesto;mid[s]=p.midi;
  if(kind==='contacto')return;
  // r00117 is the pickup of the slip already injected by contact, not a second pluck.
  if(e.id==='r00117')return;
  if(kind==='apagar'){for(let j=s*24;j<(s+1)*24;j++){re[j]*=.04;im[j]*=.04;}return;}
  for(let h=1;h<=8;h++){
   let z=Math.sin(Math.PI*h*clamp(p.nodo,.01,.99))/h**1.2;
   if(kind==='armonico')z=Math.sin(Math.PI*h*.17)/h**1.2*Math.exp(-.5*((h-p.parcial)/.35)**2)*Math.exp(-((Math.sin(Math.PI*h*p.nodo)/.12)**2));
   if(kind==='madera')z=Math.cos(h*1.37)/(h+.5)**.8;
   if(kind==='roce')z*=Math.cos(h*2.1)*.38;
   const j=s*24+c*8+h-1;re[j]+=p.vel*z;im[j]+=.2*p.vel*z;
  }
 }
 for(let a=0;a<N;){
  while(ei<events.length&&events[ei][0]<=a)gesture(events[ei++][1]);
  let b=Math.min(N,a+240,ei<events.length?events[ei][0]:N);if(b<=a){a++;continue;}
  const size=b-a,dt=size/SR,now=a/SR,oldre=re.slice(),oldim=im.slice();let scratch=0;
  for(const e of contacts){const rel=now-e.t;if(rel<0||rel>e.dur)continue;
   const index=Math.floor(rel/.005+1e-5),pres=interp(e.contacto.curva,rel),film=e.contacto.pelicula;
   if(index>e.last){for(let k=e.last+1;k<=index;k++){
    const tt=k*.005,p=interp(e.contacto.curva,tt);e.load+=.005*(p-.72*e.load);
    const slip=e.load>=e.contacto.umbral;if(slip)e.load*=.18;
    const drive=Math.max(0,p-e.contacto.umbral)*.055+(slip?.28:0);
    for(let h=1;h<=8;h++){const j=e.cuerda*24+e.caja*8+h-1,A=drive*Math.sin(Math.PI*h*.17)/h**1.2,ph=h*(.37+tt*.8);re[j]+=A*Math.cos(ph);im[j]+=A*Math.sin(ph);}
   }e.last=index;}
   scratch+=.028*pres*(1+film);
  }
  const humidity=now<29.1?.05:.65,pressure=clamp(.3+6*Math.abs(interp(route,now)),0,1);
  const w=[.7,.3,1],norm=Math.hypot(...w),theta=norm*(.1+pressure)*dt,c=Math.cos(theta),s=Math.sin(theta),v=w.map(x=>x/norm);
  const R=Array.from({length:3},(_,i)=>Array.from({length:3},(_,j)=>c*(i===j?1:0)+(1-c)*v[i]*v[j]));
  R[0][1]-=s*v[2];R[0][2]+=s*v[1];R[1][0]+=s*v[2];R[1][2]-=s*v[0];R[2][0]-=s*v[1];R[2][1]+=s*v[0];
  for(let st=0;st<6;st++)for(let h=1;h<=8;h++){
   const decay=Math.exp(-dt*(.4+.13*h+1.2*humidity)),rr=[],ii=[];
   for(let box=0;box<3;box++){const j=st*24+box*8+h-1;rr.push(re[j]*decay);ii.push(im[j]*decay);}
   for(let box=0;box<3;box++){const j=st*24+box*8+h-1;re[j]=R[box].reduce((z,g,k)=>z+g*rr[k],0);im[j]=R[box].reduce((z,g,k)=>z+g*ii[k],0);}
  }
  const shift=shifts.map(p=>interp(p,now+dt/2));
  for(let st=0;st<6;st++)for(let box=0;box<3;box++)for(let h=1;h<=8;h++){
   const j=st*24+box*8+h-1,f=hz(mid[st])*2**(shift[box]/1200)*h,step=TAU*f/SR;
   if(Math.max(Math.abs(re[j]),Math.abs(im[j]),Math.abs(oldre[j]),Math.abs(oldim[j]))<1e-9){phase[j]=(phase[j]+step*size)%TAU;continue;}
   let cr=Math.cos(phase[j]),ci=Math.sin(phase[j]);const sr=Math.sin(step),co=Math.cos(step);
   const pan=-.78+.22*box+.08*(st-2.5),angle=(pan+1)*Math.PI/4;
   const readout=st===4?clamp(Math.min((now-cap.t)/.012,(cap.t+cap.dur-now)/.012),0,1):0;
   const selection=h===5?1+2*readout:1-.95*readout;
   const gl=Math.cos(angle)*[1,.2,-.15][box]*selection,gr=Math.sin(angle)*[1,.2,-.15][box]*selection;
   for(let k=0;k<size;k++){const u=k/size,zr=oldre[j]*(1-u)+re[j]*u,zi=oldim[j]*(1-u)+im[j]*u,y=zr*cr-zi*ci;
    out[2*(a+k)]+=y*gl;out[2*(a+k)+1]+=y*gr;const nr=cr*co-ci*sr;ci=ci*co+cr*sr;cr=nr;}
   phase[j]=(phase[j]+step*size)%TAU;
  }
  if(scratch>0)for(let k=a;k<b;k++){const x=rng();noiseLP+=.35*(x-noiseLP);const y=(x-noiseLP)*scratch;out[2*k]+=y*.8;out[2*k+1]+=y*.3;}
  if(a%(SR*3)<240){let norm2=0;for(let j=0;j<M;j++)norm2+=re[j]**2+im[j]**2;metrics.push([now,norm2,...shift,pressure,humidity]);}
  a=b;
 }
 const label=process.argv[3]||'guitarra';save(label,out);fs.writeFileSync(path.join(OUT,label+'-estados.json'),JSON.stringify({dt_max:.005,metodo:'mismas envolventes, damping y rotación ortogonal de GuitarraMemoria; osciladores de fase persistente',captacion_parcial_5:{evento:cap.id,seleccion:'ganancia 3 en modo 5; .05 en los otros durante la captación; sin nueva excitación'},contactos:contacts.map(e=>({id:e.id,carga_final:e.load})),traza:metrics}));console.log(label,Date.now()-start,'ms');
}
function organ(){
 const es=P.eventos.organo.slice().sort((a,b)=>a.t-b.t),pres=P.controles.organo.controles.presion;
 const div=[1,2,3,5,7,9],state=div.map(()=>false),gain=div.map(()=>0),phase=div.map(()=>0),out=new Float32Array(N*2),changes=[];
 const lp=Math.exp(-1/(SR*.065)),pitchlp=Math.exp(-1/(SR*.009));let idx=-1,target=hz(86),logf=Math.log(target);
 for(let i=0;i<N;i++){
  const t=i/SR;while(idx+1<es.length&&es[idx+1].t<=t){idx++;target=hz(es[idx].midi);}
  logf=pitchlp*logf+(1-pitchlp)*Math.log(target);const f=Math.exp(logf),p=interp(pres,t);let amp=0;
  if(idx>=0){const e=es[idx],r=t-e.t;if(r>=0&&r<e.dur){const at=e.ataque??.04,rel=e.soltar??.09; amp=e.vel*Math.sin(Math.min(1,r/at)*Math.PI/2)**2*Math.sin(Math.min(1,(e.dur-r)/rel)*Math.PI/2)**2;}}
  for(let j=0;j<6;j++){
   const on=.12+.125*j,off=Math.max(0,on-.20),old=state[j];if(p>=on)state[j]=true;else if(p<=off)state[j]=false;
   if(old!==state[j])changes.push({t,divisor:div[j],activo:state[j],presion:p});
   gain[j]=lp*gain[j]+(1-lp)*(state[j]?1:0);phase[j]=(phase[j]+TAU*f/div[j]/SR)%TAU;
   const y=Math.sin(phase[j]+.006*Math.sin(t*(.4+j*.1)))*gain[j]*amp*.19/(1+j*.25),pan=(j%2?-.75:.75)*j/5,a=(pan+1)*Math.PI/4;
   out[2*i]+=y*Math.cos(a);out[2*i+1]+=y*Math.sin(a);
  }
 }
 save('organo',out);fs.writeFileSync(path.join(OUT,'organo-estados.json'),JSON.stringify({cambios:changes,modelo:'Schmitt y osciladores del motor fijado; memoria durante salida cerrada'}));console.log('organo listo',changes.length,'cambios');
}
if(process.argv[2]==='guitarra')guitar();else organ();
