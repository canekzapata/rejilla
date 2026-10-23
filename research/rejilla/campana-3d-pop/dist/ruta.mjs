export const INITIAL={fold:.08,depth:.7,tension:7,damping:.24,midi:48,pickup:1,region:9,inside:false};
const bounds={fold:[0,1],depth:[0,2],tension:[.2,14],damping:[.08,3],midi:[36,72],pickup:[0,7],region:[0,63]};
export function cleanRoute(input={}){
 const p={...INITIAL};for(const [k,[lo,hi]] of Object.entries(bounds)){
  const v=Number(input[k]);if(input[k]!==undefined&&Number.isFinite(v))p[k]=Math.max(lo,Math.min(hi,v));
 }p.pickup=Math.round(p.pickup);p.region=Math.round(p.region);p.midi=Math.round(p.midi);p.inside=input.inside===true||input.inside==='1';return p;
}
export function readRoute(hash=''){
 const u=new URLSearchParams(hash.replace(/^#/,'')),map={fold:'pliegue',depth:'profundidad',tension:'tension',damping:'caida',midi:'nota',pickup:'familia',region:'zona',inside:'dentro'},p={};
 for(const [key,name] of Object.entries(map))if(u.has(name))p[key]=u.get(name);return cleanRoute(p);
}
export function encodeRoute(p){const s=cleanRoute(p),u=new URLSearchParams();for(const [name,key] of [['familia','pickup'],['zona','region'],['pliegue','fold'],['profundidad','depth'],['tension','tension'],['caida','damping'],['nota','midi']])u.set(name,Number(s[key].toFixed(3)));if(s.inside)u.set('dentro','1');return '#'+u.toString();}
export function audioParams(p){return Object.fromEntries(['fold','depth','tension','damping','midi','pickup'].map(k=>[k,p[k]]));}
