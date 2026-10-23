const fs=require('fs'),path=require('path');
const out=path.resolve(process.argv[2]),P=JSON.parse(fs.readFileSync(path.join(out,'partitura.json'),'utf8')),SR=48000,D=P.duracion;
const base=path.resolve(__dirname,'../objetos/motor');
function save(name,y){let peak=0;for(const x of y){if(!Number.isFinite(x))throw Error(name+' no finito');peak=Math.max(peak,Math.abs(x));}fs.writeFileSync(path.join(out,'render',name+'.f32'),Buffer.from(y.buffer),{flag:'wx'});console.log(name,'pico',peak.toFixed(3));}
const Metal=require(base+'/metal.js'),Cuerda=require(base+'/cuerda.js'),Piano=require(base+'/piano.js');
save('trompeta',Metal.render({dur:D,voz:'trompeta',sordina:'abierta',notas:P.trompeta,semilla:P.semilla},SR));
const G=require('../lo-que-tapa-la-traspuesta/motor/garganta.js');
save('garganta',G.render({dur:D,perfil:Float32Array.from({length:96},(_,i)=>.5+.23*Math.sin(i*.14)+.12*Math.cos(i*.33)),largo:1,eventos:P.garganta.map(e=>({...e,nota:e.m,fonemas:e.fonemas||[e.vocal||'a'],aprende:.94})),semilla:P.semilla},SR));
for(const arco of [true,false])save(arco?'chelo-arco':'chelo-pizz',Cuerda.render({dur:D,instrumento:'chelo',eventos:P.chelo.filter(e=>['arco','tasto','ponticello','armonico','tremolo'].includes(e.tipo)===arco),semilla:P.semilla},SR));
save('piano',Piano.render({dur:D,eventos:P.piano,prepara:m=>m<60?Piano.PREP.goma:Piano.PREP.papel,semilla:P.semilla},SR));
// Reed scheduler and post-gate: the existing sax model otherwise continues after breath ends.
const Objeto=require(base+'/objeto.js'),notes=P.sax.slice().sort((a,b)=>a.t-b.t),hz=m=>440*2**((m-69)/12);
function idx(t){let lo=0,hi=notes.length-1;if(t<notes[0].t)return -1;while(lo<hi){const m=(lo+hi+1)>>1;if(notes[m].t<=t)lo=m;else hi=m-1;}return lo;}
function breath(t){const k=idx(t);let v=0;for(const j of [k-1,k]){if(j<0)continue;const e=notes[j],u=t-e.t;if(u<-.003||u>e.dur+.035)continue;let a=e.v;if(u<.018&&e.lengua)a*=.4+.6*Math.max(0,u)/.018;if(u>e.dur)a*=Math.max(0,1-(u-e.dur)/.035);v=Math.max(v,a);}return v;}
function freq(t){const k=idx(t);if(k<0)return hz(notes[0].m+.18);const e=notes[k],u=(t-e.t)/.012;if(k>0&&u<1&&e.t-(notes[k-1].t+notes[k-1].dur)<.05)return hz(notes[k-1].m+(e.m-notes[k-1].m)*Math.max(0,u)+.18);return hz(e.m+.18);}
const S=Objeto.PURO.saxofon;
const y=Objeto.render({dur:D,f:freq,w:()=>[1,0,0],soplo:breath,pos:()=>S.pos,disp:()=>0,perdida:()=>S.perdida,brillo:()=>S.brillo,ruido:()=>S.ruido,vibrato:[5.4,.025],semilla:P.semilla%9973},SR);
let g=0;for(let i=0;i<y.length;i++){const v=breath(i/SR)>0?1:0;g+=(v-g)*(1-Math.exp(-1/((v>g?.002:.08)*SR)));y[i]*=g;}save('sax',y);
