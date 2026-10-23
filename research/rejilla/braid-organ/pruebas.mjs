import assert from 'node:assert/strict';
import {A,B,mm,adj,identity,wordMatrix,coefficients,norm,BraidState} from './dist/algebra.mjs';
import {Voice} from './dist/voice.mjs';
const distance=(a,b)=>Math.max(...a.flat(Infinity).map((v,i)=>Math.abs(v-b.flat(Infinity)[i]))),tol=1e-11;
const report={unitaryA:distance(mm(adj(A),A),identity()),unitaryB:distance(mm(adj(B),B),identity()),braidRelation:distance(wordMatrix('ABA'),wordMatrix('BAB')),noncommutative:distance(wordMatrix('AB'),wordMatrix('BA'))};
assert(report.unitaryA<tol&&report.unitaryB<tol&&report.braidRelation<tol);assert(report.noncommutative>.1);
const state=new BraidState(),initial=state.values;for(const g of 'ABaBABAb')state.cross(g);report.normDrift=Math.abs(norm(initial)-norm(state.values));assert(report.normDrift<tol);for(let i=0;i<8;i++)state.undo();report.undo=distance(initial,state.values);assert(report.undo<tol);
const render=word=>{const v=new Voice(48000,coefficients(wordMatrix(word)));v.gate=1;const signal=new Float64Array(48000),out=new Float64Array(3);for(let i=0;i<signal.length;i++){v.sample(out);signal[i]=out.reduce((a,b)=>a+b,0);}return signal;};
const ab=render('AB'),ba=render('BA'),aba=render('ABA'),bab=render('BAB');let diff=0,base=0,eq=0,peak=0;for(let i=0;i<ab.length;i++){assert(Number.isFinite(ab[i]));diff+=(ab[i]-ba[i])**2;base+=ab[i]**2;eq=Math.max(eq,Math.abs(aba[i]-bab[i]));peak=Math.max(peak,Math.abs(ab[i]),Math.abs(ba[i]));}report.audioOrderResidual=Math.sqrt(diff/base);report.audioEquivalentError=eq;report.peak=peak;assert(report.audioOrderResidual>.1);assert(eq<tol);assert(peak<.95);
// Long word and exact inverse: no normalization hides drift.
const many='ABaBAb'.repeat(200),s=new BraidState();for(const g of many)s.cross(g);for(let i=0;i<many.length;i++)s.undo();report.longUndo=distance(s.values,initial);assert(report.longUndo<tol);
console.log(JSON.stringify({result:'PASS',...report},null,2));
