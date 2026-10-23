import {render} from './fuelle.mjs';import fs from 'node:fs';import path from 'node:path';
const O=fs.readFileSync('ULTIMA.txt','utf8').trim(),R=path.join('render',O.split('-').pop());
for(const p of [.5,.85]){const y=render({midi:57,m2:57,dur:5,presion:p,aire:1,vel:.7},65536,1);fs.writeFileSync(path.join(R,'prueba-fuelle-'+p+'.f32'),Buffer.from(y.buffer),{flag:'wx'});}
