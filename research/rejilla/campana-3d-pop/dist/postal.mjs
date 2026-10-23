const enc=new TextEncoder();
function crc(bytes){let c=0xffffffff;for(const b of bytes){c^=b;for(let j=0;j<8;j++)c=(c>>>1)^((c&1)?0xedb88320:0);}return (c^0xffffffff)>>>0;}
export async function postcard(png,state){
 const bytes=new Uint8Array(await png.arrayBuffer()),nonce=crypto.getRandomValues(new Uint8Array(24)),version=enc.encode('p-adic-bell-1.2.0');
 const joined=new Uint8Array(bytes.length+nonce.length+version.length);joined.set(bytes);joined.set(version,bytes.length);joined.set(nonce,bytes.length+version.length);
 const hex=b=>Array.from(b,v=>v.toString(16).padStart(2,'0')).join(''),hash=hex(new Uint8Array(await crypto.subtle.digest('SHA-256',joined)));
 const recipe={version:'1.2.0',seed:20261021,sha256:hash,nonce:hex(nonce),image_sha256:hex(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))),state};
 const payload=enc.encode('Receta\0\0\0\0\0'+JSON.stringify(recipe)),type=enc.encode('iTXt'),chunk=new Uint8Array(12+payload.length),view=new DataView(chunk.buffer);view.setUint32(0,payload.length);chunk.set(type,4);chunk.set(payload,8);view.setUint32(8+payload.length,crc(chunk.subarray(4,8+payload.length)));
 return {blob:new Blob([bytes.subarray(0,bytes.length-12),chunk,bytes.subarray(bytes.length-12)],{type:'image/png'}),filename:'p-adic-bell-s20261021-'+hash.slice(0,12)+'.png',recipe};
}
