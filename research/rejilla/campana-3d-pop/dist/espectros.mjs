import * as THREE from './vendor/three.module.js';
import {poses,PALETTE} from './forma.mjs';

// Logarithmic frequency rows, from a real post-engine stereo-to-mono analyser.
export function spectralRows(db,sampleRate,fftSize,rows=96){
 const result=new Float32Array(rows),nyquist=sampleRate/2,high=Math.min(6000,nyquist),low=45;
 for(let y=0;y<rows;y++){
  const lo=high*(low/high)**((y+1)/rows),hi=high*(low/high)**(y/rows);
  const a=Math.max(1,Math.floor(lo/nyquist*db.length)),b=Math.min(db.length-1,Math.max(a,Math.ceil(hi/nyquist*db.length)));let peak=-Infinity;
  for(let k=a;k<=b;k++)peak=Math.max(peak,db[k]);result[y]=Number.isFinite(peak)?Math.max(0,Math.min(1,(peak+86)/66)):0;
 }return result;
}
export class SpectralPetals{
 constructor(scene,camera){this.scene=scene;this.camera=camera;this.items=[];this.last=0;this.frames=0;this.peak=0;this.total=0;}
 strike(region,now){
  if(this.items.length>=3)this.remove(this.items[0]);
  const canvas=document.createElement('canvas');canvas.width=192;canvas.height=96;const pen=canvas.getContext('2d'),texture=new THREE.CanvasTexture(canvas);texture.minFilter=THREE.LinearFilter;texture.magFilter=THREE.NearestFilter;
  const mesh=new THREE.Mesh(new THREE.PlaneGeometry(1,.5),new THREE.MeshBasicMaterial({map:texture,transparent:true,depthWrite:false,depthTest:false,toneMapped:false,side:THREE.DoubleSide}));mesh.renderOrder=10;
  this.scene.add(mesh);this.items.push({region,born:now,canvas,pen,texture,mesh,columns:0});this.total++;
 }
 remove(item){this.scene.remove(item.mesh);item.texture.dispose();item.mesh.geometry.dispose();item.mesh.material.dispose();this.items.splice(this.items.indexOf(item),1);}
 update(now,analyser,fold,reduced,viewportHeight,viewportWidth){
  const sample=analyser&&now-this.last>=.04;let rows;
  if(sample){this.last=now;const db=new Float32Array(analyser.frequencyBinCount);analyser.getFloatFrequencyData(db);rows=spectralRows(db,analyser.context.sampleRate,analyser.fftSize);this.peak=Math.max(...rows);this.frames++;}
  const right=new THREE.Vector3().setFromMatrixColumn(this.camera.matrixWorld,0),up=new THREE.Vector3().setFromMatrixColumn(this.camera.matrixWorld,1);
  for(const item of [...this.items]){
   const age=now-item.born;if(age>6){this.remove(item);continue;}
   const anchor=poses(item.region,fold).position;
   const projected=anchor.clone().project(this.camera);item.mesh.visible=Math.abs(projected.x)<1.2&&Math.abs(projected.y)<1.2&&projected.z<1&&projected.z>-1;
   const forward=this.camera.getWorldDirection(new THREE.Vector3()),depth=Math.max(.05,anchor.clone().sub(this.camera.position).dot(forward)),half=Math.tan(this.camera.fov*Math.PI/360),pixels=Math.min(170,Math.max(115,viewportWidth*.3)),width=depth*2*half*pixels/viewportHeight,side=projected.x>0?-1:1;
   item.mesh.position.copy(anchor).addScaledVector(right,side*width*.42).addScaledVector(up,(projected.y>0?-1:1)*width*.28);
   const screen=item.mesh.position.clone().project(this.camera),mx=Math.max(.05,1-pixels/viewportWidth-.035),my=Math.max(.05,1-pixels*.5/viewportHeight-.035);
   item.mesh.position.addScaledVector(right,(THREE.MathUtils.clamp(screen.x,-mx,mx)-screen.x)*depth*half*this.camera.aspect).addScaledVector(up,(THREE.MathUtils.clamp(screen.y,-my,my)-screen.y)*depth*half);item.mesh.quaternion.copy(this.camera.quaternion);item.mesh.scale.setScalar(width*(reduced?1:Math.min(1,.55+age*1.6)));
   item.mesh.material.opacity=Math.min(1,age*6)*Math.min(1,(6-age)/1.5)*.94;
   if(!rows)continue;const p=item.pen;
   if(reduced){p.clearRect(0,0,192,96);}else{p.drawImage(item.canvas,-2,0);p.clearRect(190,0,2,96);}
   for(let y=0;y<96;y++){
    const v=rows[y];if(v<.32)continue;const x=reduced?0:190,w=reduced?Math.ceil(v*190):2;
    // Dark underprint keeps the light spectral ridges visible on pastel porcelain.
    p.globalAlpha=v**1.8*.75;p.fillStyle='#442343';p.fillRect(x,y,w,1);
    p.globalAlpha=Math.min(1,v**1.15);p.fillStyle=v>.52?'#fff4d4':v>.42?PALETTE[item.region%8]:'#9c387e';if(reduced||v>.48||item.columns%3!==0)p.fillRect(x,y,w,.7);
   }p.globalAlpha=1;item.columns++;item.texture.needsUpdate=true;
  }
 }
}
