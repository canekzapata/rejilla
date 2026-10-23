export function pcmWav(left,right,sr,metadata){
 const text=new TextEncoder().encode(JSON.stringify(metadata)),n=text.length+1,padded=n+(n%2),len=left.length;
 const b=new ArrayBuffer(44+len*4+20+padded),v=new DataView(b),put=(i,s)=>{for(let j=0;j<s.length;j++)v.setUint8(i+j,s.charCodeAt(j));};
 put(0,'RIFF');v.setUint32(4,b.byteLength-8,true);put(8,'WAVEfmt ');v.setUint32(16,16,true);v.setUint16(20,1,true);v.setUint16(22,2,true);v.setUint32(24,sr,true);v.setUint32(28,sr*4,true);v.setUint16(32,4,true);v.setUint16(34,16,true);put(36,'data');v.setUint32(40,len*4,true);
 for(let i=0;i<len;i++){v.setInt16(44+i*4,Math.round(Math.max(-1,Math.min(1,left[i]))*32767),true);v.setInt16(46+i*4,Math.round(Math.max(-1,Math.min(1,right[i]))*32767),true);}
 const at=44+len*4;put(at,'LIST');v.setUint32(at+4,12+padded,true);put(at+8,'INFOICMT');v.setUint32(at+16,n,true);new Uint8Array(b,at+20,text.length).set(text);return b;
}
const hex=b=>Array.from(new Uint8Array(b),v=>v.toString(16).padStart(2,'0')).join('');
export async function exportTake(take,image){
 const nonce=crypto.getRandomValues(new Uint8Array(24)),pcm=new Float32Array(take.left.length*2);
 for(let i=0;i<take.left.length;i++){pcm[2*i]=take.left[i];pcm[2*i+1]=take.right[i];}
 const picture=new TextEncoder().encode(image),version=new TextEncoder().encode('campana-padica-1.0.0');
 const bytes=new Uint8Array(pcm.byteLength+picture.length+version.length+nonce.length);bytes.set(new Uint8Array(pcm.buffer));bytes.set(picture,pcm.byteLength);bytes.set(version,pcm.byteLength+picture.length);bytes.set(nonce,pcm.byteLength+picture.length+version.length);
 const id=hex(await crypto.subtle.digest('SHA-256',bytes));
 const recipe={instrumento:'Campana de distancias imposibles',version:'1.0.0',semilla:20261021,ejecucion_sha256:id,nonce_hex:hex(nonce),
  audio_float32_sha256:hex(await crypto.subtle.digest('SHA-256',pcm.buffer)),imagen_sha256:hex(await crypto.subtle.digest('SHA-256',picture)),
  sample_rate:take.sr,duracion_s:take.left.length/take.sr,estado_inicial:take.initial,objetivos_iniciales:take.targets,eventos:take.events,
  identidad:'SHA256(audio Float32 entrelazado + imagen del cuerpo codificada como data URL + versión + nonce)',
  receta:'JSON dentro de LIST/INFO/ICMT del WAV; grafo de 64 regiones, vecindad 2-ádica finita.'};
 const buffer=pcmWav(take.left,take.right,take.sr,recipe);
 recipe.pcm16_sha256=hex(await crypto.subtle.digest('SHA-256',buffer.slice(44,44+take.left.length*4)));
 return {buffer:pcmWav(take.left,take.right,take.sr,recipe),recipe,name:'campana-padica-s20261021-'+id.slice(0,12)+'.wav'};
}
