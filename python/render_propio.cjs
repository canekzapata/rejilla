// Adaptador del paquete: llama motores originales; no depende del equipo del autor.
const fs=require('fs'),path=require('path'),vm=require('vm');
const ROOT=path.resolve(__dirname,'..'),request=JSON.parse(fs.readFileSync(process.argv[2],'utf8')),out=process.argv[3];
const rows=JSON.parse(fs.readFileSync(path.join(ROOT,'MOTORES-NUEVOS.json'),'utf8'));
const row=rows.find(r=>r.id===request.motor_propio);if(!row)throw Error('Motor desconocido');
const c=Object.assign({},row.config,request.config||{});let sr=48000;
function modulo(p){return require(path.join(ROOT,p))}
function vozGuia(d){const V=modulo('research/rejilla/objetos/motor/vozagua.js');return V.render({dur:d,semilla:c.semilla||2038,eventos:[{t:.1,dur:d-.3,texto:'todavía estoy aquí',nota:57,modo:'canto',voz:1,v:.7}]},48000)}
function monoWav(file){const b=fs.readFileSync(file);if(b.toString('ascii',0,4)!=='RIFF')throw Error('La guía debe ser WAV PCM16 a 48 kHz');let fmt,data;for(let i=12;i+8<=b.length;){let id=b.toString('ascii',i,i+4),n=b.readUInt32LE(i+4);if(id==='fmt ')fmt=i+8;if(id==='data')data=[i+8,n];i+=8+n+(n%2)}if(!fmt||!data||b.readUInt16LE(fmt)!==1||b.readUInt16LE(fmt+14)!==16||b.readUInt32LE(fmt+4)!==48000)throw Error('Guía: WAV PCM16, 48 kHz');const ch=b.readUInt16LE(fmt+2),a=new Float32Array(data[1]/(2*ch));for(let i=0;i<a.length;i++){for(let k=0;k<ch;k++)a[i]+=b.readInt16LE(data[0]+(i*ch+k)*2)/32768/ch}return a}
async function run(){let result,meta={motor:row.id,origen:row.archivo,config:c},parts={};
 if(row.tipo==='siringua'){
  sr=24000;const S=modulo(row.archivo),item={id:'demostracion-local',text:c.texto||'todavía estoy aquí'};const canto=await S.preparar(item,{language:c.language||'es-MX',semilla:c.semilla||181026});const a=S.render(canto,sr);result=a.samples;parts.agua=a.water;parts.ave=a.bird;meta.partitura=canto;
 }else if(row.tipo==='siringua-vocoder'){
  sr=24000;const S=modulo('research/rejilla/aves-que-aprenden/siringua-mensajes.js');const canto=await S.preparar({id:'siringua-vocoder',text:c.texto},{language:c.language,semilla:c.semilla});const V=modulo('research/rejilla/objetos/motor/vozagua.js'),P=modulo('research/rejilla/objetos/motor/pajaro.js');const code=fs.readFileSync(path.join(ROOT,'research/rejilla/objetos/motor/pajaro.js'),'utf8'),needle='s += out * (k ? .8 : 1);';if(!code.includes(needle))throw Error('Cambió el original de siringe; revisar adaptación explícita');const sandbox={module:{exports:{}}};vm.runInNewContext(code.replace(needle,'s += src * (k ? .8 : 1);'),sandbox);const Raw=sandbox.module.exports;
  const dur=canto.duration,events=canto.waterEvents;parts.agua=V.render({dur,eventos:events,semilla:c.semilla},sr);const high=events.flatMap((e,i)=>[{t:e.t,dur:e.dur,m:84+i%4,m2:91-i%3,tipo:'silbido',voz:0,v:.65},{t:e.t+.03,dur:e.dur-.03,m:91-i%3,tipo:'silbido',voz:1,v:.45}]);parts.ave=P.render({dur,eventos:high,semilla:c.semilla},sr);const low=events.flatMap((e,i)=>[{t:e.t,dur:e.dur,m:57+i%3,tipo:'ronco',voz:0,v:.8},{t:e.t,dur:e.dur,m:62-i%3,tipo:'ronco',voz:1,v:.65}]);parts.portadora=Raw.render({dur,eventos:low,semilla:c.semilla},sr);meta.segmentos=events.flatMap(e=>V.segmentos(e));meta.partitura=canto;result=parts.agua;
 }else if(row.tipo==='traductor'){
  c.guia=c.guia_wav?monoWav(path.resolve(c.guia_wav)):vozGuia(c.dur);if(c.guia.length<Math.ceil(c.dur*sr)){const p=new Float32Array(Math.ceil(c.dur*sr));p.set(c.guia);c.guia=p}const a=modulo(row.archivo).render(c,sr);result=a.y;parts.guia=c.guia;meta.trazas={coeficientes_lpc:a.k};meta.guia=c.guia_wav?'WAV proporcionado por la persona':'VozAgua procedural, no Sabina';delete meta.config.guia;
 }else if(row.tipo==='volcan'){
  const a=modulo(row.archivo).render(c,sr,modulo('research/rejilla/lo-que-tapa-la-traspuesta/motor/garganta.js'));parts.garganta=a.voz;parts.caldera=a.caldera;result=new Float32Array(a.voz.length);for(let i=0;i<result.length;i++)result[i]=a.voz[i]*.7+a.caldera[i]*.3;
 }else{result=modulo(row.archivo).render(c,sr)}
 let channels=1,y;if(result.L&&result.R){channels=2;y=new Float32Array(result.L.length*2);for(let i=0;i<result.L.length;i++){y[2*i]=result.L[i];y[2*i+1]=result.R[i]}}else y=result.y||result.samples||result;
 if(!ArrayBuffer.isView(y))throw Error('Salida no reconocida');let peak=0;for(const x of y){if(!Number.isFinite(x))throw Error('Señal no finita');peak=Math.max(peak,Math.abs(x))}if(peak<1e-8)throw Error('Señal silenciosa');
 fs.writeFileSync(out,Buffer.from(y.buffer,y.byteOffset,y.byteLength),{flag:'wx'});
 const saved={};for(const[name,a]of Object.entries(parts)){const f=out+'.'+name+'.f32';fs.writeFileSync(f,Buffer.from(a.buffer,a.byteOffset,a.byteLength),{flag:'wx'});saved[name]=path.basename(f)}
 fs.writeFileSync(out+'.json',JSON.stringify({...meta,sr,channels,frames:y.length/channels,peak,partes:saved},null,2),{flag:'wx'});console.log(JSON.stringify({motor:row.id,sr,channels,frames:y.length/channels,peak}));
}
run().catch(e=>{console.error(e.stack);process.exitCode=1});
