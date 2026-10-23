import * as THREE from './vendor/three.module.js';
export const PALETTE=['#ff4f9a','#ff9b62','#e5ed69','#6cdddd','#b19bff','#8ce6b0','#ff686d','#f3b1e6'];
export function outline(theta,r){
 const scallop=1+.065*Math.cos(5*theta),rad=.28+(.98*scallop-.28)*r;
 return [Math.cos(theta)*rad*.64,Math.sin(theta)*rad*.83,.19*rad*rad+.045*Math.sin(3*theta)*r*r];
}
export function porcelainGeometry(){
 const seg=40,rings=6,p=[],indices=[];
 for(let side=0;side<2;side++)for(let j=0;j<=rings;j++)for(let i=0;i<=seg;i++){
  const a=outline(i/seg*Math.PI*2,j/rings);p.push(a[0],a[1],a[2]-(side?.075:0));
 }
 const size=(rings+1)*(seg+1);
 for(let side=0;side<2;side++)for(let j=0;j<rings;j++)for(let i=0;i<seg;i++){
  const a=side*size+j*(seg+1)+i,b=a+1,c=a+seg+1,d=c+1;
  if(side===0)indices.push(a,b,d,a,d,c);else indices.push(a,d,b,a,c,d);
 }
 for(const ring of [0,rings])for(let i=0;i<seg;i++){
  const a=ring*(seg+1)+i,b=a+1,c=a+size,d=b+size;
  if(ring===rings)indices.push(a,c,d,a,d,b);else indices.push(a,d,c,a,b,d);
 }
 const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(p,3));g.setIndex(indices);g.computeVertexNormals();g.computeBoundingSphere();return g;
}
export function rimGeometry(r){
 const points=Array.from({length:81},(_,i)=>{const p=outline(i/80*Math.PI*2,r);return new THREE.Vector3(...p);});
 return new THREE.TubeGeometry(new THREE.CatmullRomCurve3(points,true),80,r===1?.014:.011,5,true);
}
export function chamberCenter(family){
 return new THREE.Vector3(family&1?1.57:-1.57,(family&4)?.72:-.72,(family&2)?1.02:-1.02);
}
const zAxis=new THREE.Vector3(0,0,1);
export function poses(index,fold){
 const row=index>>3,col=index%8,phi=col/8*Math.PI*2+row*.06;
 const radius=1.12+1.2*(1-row/7)**1.25;
 const open=new THREE.Vector3(Math.sin(phi)*radius,-2.0+row*.57,Math.cos(phi)*radius);
 const c=chamberCenter(col),side=row&4?1:-1;
 const closed=c.clone().add(new THREE.Vector3(row&1?.41:-.41,row&2?.22:-.22,side*.095));
 const normalOpen=new THREE.Vector3(Math.sin(phi),.22,Math.cos(phi)).normalize();
 const normalClosed=new THREE.Vector3((row&1?.15:-.15),(row&2?.18:-.18),side).normalize();
 const qo=new THREE.Quaternion().setFromUnitVectors(zAxis,normalOpen),qc=new THREE.Quaternion().setFromUnitVectors(zAxis,normalClosed);
 return {position:open.lerp(closed,fold),quaternion:qo.slerp(qc,fold),scale:(.64+.16*(1-row/7))*(1-fold)+.36*fold};
}
export function makeBody(materials,rimMaterial){
 const root=new THREE.Group(),parts=[],geometry=porcelainGeometry(),outer=rimGeometry(1),inner=rimGeometry(0);
 for(let i=0;i<64;i++){
  const group=new THREE.Group(),mesh=new THREE.Mesh(geometry,materials[i%8].clone());mesh.userData.region=i;mesh.castShadow=true;mesh.receiveShadow=true;
  const rim=new THREE.Mesh(outer,rimMaterial),hole=new THREE.Mesh(inner,rimMaterial);group.add(mesh,rim,hole);root.add(group);
  const pose=poses(i,0);group.position.copy(pose.position);group.quaternion.copy(pose.quaternion);group.scale.setScalar(pose.scale);
  parts.push({group,mesh,rim,hole,index:i});
 }return {root,parts,geometry};
}
