// PCM WAV + embedded INFO recipe. Fresh nonce and full execution hash per export.
export function wav(data,metadata=null,sr=32768){
 const text=metadata?new TextEncoder().encode(JSON.stringify(metadata)):null;
 const textLength=text?text.length+1:0,padded=textLength+(textLength%2);
 const extra=text?20+padded:0,b=new ArrayBuffer(44+data.length*2+extra),d=new DataView(b);
 const s=(i,t)=>{for(let j=0;j<t.length;j++)d.setUint8(i+j,t.charCodeAt(j))};
 s(0,'RIFF');d.setUint32(4,b.byteLength-8,true);s(8,'WAVEfmt ');d.setUint32(16,16,true);d.setUint16(20,1,true);d.setUint16(22,1,true);d.setUint32(24,sr,true);d.setUint32(28,sr*2,true);d.setUint16(32,2,true);d.setUint16(34,16,true);s(36,'data');d.setUint32(40,data.length*2,true);
 for(let i=0;i<data.length;i++)d.setInt16(44+2*i,Math.round(Math.max(-1,Math.min(1,data[i]))*32767),true);
 if(text){const p=44+data.length*2;s(p,'LIST');d.setUint32(p+4,12+padded,true);s(p+8,'INFOICMT');d.setUint32(p+16,textLength,true);new Uint8Array(b,p+20,text.length).set(text);}
 return b;
}
const hex=b=>Array.from(new Uint8Array(b),x=>x.toString(16).padStart(2,'0')).join('');
export async function exportWav(data,settings,midi){
 const raw=wav(data),nonce=crypto.getRandomValues(new Uint8Array(24)),version=new TextEncoder().encode('telar-de-fase-1.0.0');
 const combined=new Uint8Array(raw.byteLength+nonce.length+version.length);combined.set(new Uint8Array(raw));combined.set(nonce,raw.byteLength);combined.set(version,raw.byteLength+nonce.length);
 const id=hex(await crypto.subtle.digest('SHA-256',combined));
 const recipe={instrumento:'Telar de fase',version:'1.0.0',semilla:20261021,ejecucion_sha256:id,nonce_hex:hex(nonce),
   pcm16_sha256:hex(await crypto.subtle.digest('SHA-256',raw.slice(44))),midi,controles:settings,
   identidad:'SHA256(WAV PCM sin receta + nonce + versión)',receta:'Este JSON está en LIST/INFO/ICMT del WAV.'};
 return {buffer:wav(data,recipe),name:'telar-de-fase-s20261021-'+id.slice(0,12)+'.wav',recipe};
}
