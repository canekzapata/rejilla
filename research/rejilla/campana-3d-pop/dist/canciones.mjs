// Five deterministic scores for ONE retuned resonating body, not sampled chords.
function score(id,title,duration,initial){return {id,title,duration,initial,events:[]};}
function note(s,t,hit,vel){s.events.push({t,hit,vel});}
function change(s,t,params){s.events.push({t,params});}
const rain=score('porcelain-rain','Porcelain Rain',42,{fold:.06,depth:.55,tension:4.6,damping:.55,midi:60,pickup:1});
const rainNotes=[60,64,67,62,60,55,57,60,64,62,60,55],rainZones=[9,41,25,57,17,49];
for(let bar=0;bar<12;bar++){
 const base=bar*3;change(rain,base,{midi:rainNotes[bar],fold:[.06,.14,.25,.4,.62,.72,.48,.27,.12,.55,.82,.16][bar]});
 const rhythm=bar===0?[.16,1.16,2.16]:[.16,.66,1.16,1.66,2.16];
 rhythm.forEach((beat,j)=>note(rain,base+beat,rainZones[(j+bar)%6],[.39,.21,.3,.23,.31][j]));
}
const garden=score('folded-garden','Folded Garden',48,{fold:.96,depth:1.6,tension:9.5,damping:.82,midi:48,pickup:5});
const gardenNotes=[48,48,55,53,48,50,55,48],gardenZones=[13,45,29,61,5,37,21,53];
for(let bar=0;bar<16;bar++){
 const base=bar*2.4;change(garden,base,{midi:gardenNotes[Math.floor(bar/2)],fold:bar<4?.96:bar<8?.5:bar<12?.83:1,depth:bar<8?1.6:1.9});
 [.14,.74,1.04,1.64,1.94,2.24].forEach((beat,j)=>note(garden,base+beat,gardenZones[(bar+j*3)%8],[.42,.24,.3,.36,.22,.27][j]));
 if(bar%4===3)note(garden,base+1.64,gardenZones[(bar+4)%8],.13);
}
const tide=score('binary-tide','Binary Tide',54,{fold:1,depth:1.85,tension:11.2,damping:.24,midi:36,pickup:6});
for(let bar=0;bar<8;bar++){
 const base=bar*6,zone=[6,38,22,54,14,46,30,62][bar];
 change(tide,base,{midi:[36,43,41,38,36,41,43,38][bar],depth:bar%2?1.35:1.85});
 note(tide,base+.18,zone,.43);note(tide,base+2.28,zone^32,.21);note(tide,base+3.93,zone^16,.17);
 change(tide,base+1.38,{fold:bar%2?.92:.04});change(tide,base+4.38,{fold:bar%2?.15:1});
}
const orchard=score('glass-orchard','Glass Orchard',50,{fold:.42,depth:1.1,tension:3.7,damping:.4,midi:64,pickup:3});
for(let bar=0;bar<10;bar++){
 const base=bar*4;change(orchard,base,{midi:[64,71,67,69,62,64,59,64,67,62][bar],fold:[.42,.16,.08,.37,.7,.88,.6,.28,.11,.52][bar]});
 [.18,.98,1.78,2.98].forEach((beat,j)=>note(orchard,base+beat,[3,35,19,51,11,43,27,59][(bar*2+j)%8],[.34,.22,.27,.18][j]));
}
const waltz=score('afterimage-waltz','Afterimage Waltz',57,{fold:.7,depth:.85,tension:6.2,damping:.46,midi:57,pickup:2});
for(let bar=0;bar<22;bar++){
 const base=bar*2;change(waltz,base,{midi:[57,60,64,62,55,57,60,59,57,52,55][Math.floor(bar/2)],fold:bar<4?.7:bar<8?.18:bar<12?.5:bar<16?.94:bar<20?.35:.08});
 [.16,.8266666667,1.4933333333].forEach((beat,j)=>note(waltz,base+beat,[10,42,26,58,18,50][(bar+j*2)%6],[.36,.2,.24][j]));
 if(bar%4===3)note(waltz,base+1.8266666667,(bar*8+2)%64,.12);
}
export const SONGS=[rain,garden,tide,orchard,waltz].map(s=>({...s,events:s.events.sort((a,b)=>a.t-b.t)}));
export function songById(id){return SONGS.find(s=>s.id===id);}
