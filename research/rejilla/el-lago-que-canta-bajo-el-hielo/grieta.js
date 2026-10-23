/* Máscara proyectada de la red real. s2 contiene aristas, s0 conserva el visor. */
window.instalarGrieta=function(m,red,P,W,H){
 const cv=document.createElement('canvas');cv.width=W;cv.height=H;window.__grietasCV=cv;const ctx=cv.getContext('2d');
 const edges=red.aristas,events=P.grietas,hue=180+P.semilla%90;
 function project(u,v){
  const S=m.S,t=1-v,r=Math.round(t*111),c=Math.round(u*260),rows=S.mixto&&S.mixRows?S.mixRows:S.rows;
  const altura=rows?rows[Math.max(0,Math.min(rows.length-1,r*261+c))]:0;
  const ancho=W*(1.08+.5*t),amp=H*.34*(.32+.95*t)*(S.cascada?1.1:S.exag),onda=(S.m*9*t+S.b*3)*(S.cascada?.25:1);
  return [W/2-ancho/2+u*ancho,H*.3+(H*.97-H*.3)*Math.pow(t,1.35)-altura*amp+Math.sin(u*11+S.t*2.2+r*.33)*onda];
 }
 function paso(t){
  ctx.fillStyle='#000';ctx.fillRect(0,0,W,H);const mem=new Float32Array(edges.length),flash=new Float32Array(edges.length);
  for(const e of events){if(e.t>t)break;mem[e.arista]=Math.min(.32,mem[e.arista]+.025);const dt=t-e.t;if(dt<1.5)flash[e.arista]+=Math.exp(-dt/(.12+.22*(1-e.lambda)));const da=t-e.llegada;if(da>=0&&da<.5)flash[e.arista]+=.35*Math.exp(-da/.15);}
  for(const e of edges){const a=mem[e.id]+flash[e.id];if(a<.001)continue;
   ctx.strokeStyle=`hsla(${hue+35*flash[e.id]},90%,${35+Math.min(1,flash[e.id])*50}%,${Math.min(1,a)})`;ctx.lineWidth=(1+3*flash[e.id])*W/1920;ctx.shadowBlur=flash[e.id]*12;ctx.shadowColor=`hsl(${hue},90%,75%)`;ctx.beginPath();e.puntos.forEach(([u,v],i)=>{const p=project(u,v);i?ctx.lineTo(...p):ctx.moveTo(...p);});ctx.stroke();
  }ctx.shadowBlur=0;
 }
 const code='s2.init({src:window.__grietasCV,dynamic:true});\nsrc(s0).add(src(s2).color(0.55,0.85,1),0.95)\n .blend(src(o0).scale(1.0005),0.14).out(o0)';
 m.hydra.PRESETS.push(['grieta',code]);m.hydra.usaPreset(m.hydra.PRESETS.length-1);m.hydra.mezcla(.8);
 return {paso,canvas:cv,project};
};
