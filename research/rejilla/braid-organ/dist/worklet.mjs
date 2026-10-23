import {Voice} from './voice.mjs';
import {coefficients,identity} from './algebra.mjs';
class BraidProcessor extends AudioWorkletProcessor{
 constructor(){super();this.voice=new Voice(sampleRate,coefficients(identity()));this.out=new Float64Array(3);this.port.onmessage=({data:d})=>{if(d.values)this.voice.set(d.values);if(d.gate!==undefined)this.voice.gate=d.gate;if(d.frequency)this.voice.aim=d.frequency;};}
 process(_,outputs){for(let i=0;i<outputs[0][0].length;i++){this.voice.sample(this.out);for(let k=0;k<3;k++)outputs[k][0][i]=this.out[k];}return true;}
}
registerProcessor('braid-voice',BraidProcessor);
