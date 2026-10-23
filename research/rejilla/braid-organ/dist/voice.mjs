// Shared by the live AudioWorklet and offline verification. No random oscillators.
// Three just-intonation voices: root, major third, fifth; four partials per voice.
export const RATIOS=[1,2,3,4,1.25,2.5,3.75,5,1.5,3,4.5,6];
export class Voice{
 constructor(rate,values){this.rate=rate;this.now=Float64Array.from(values);this.target=Float64Array.from(values);this.phase=new Float64Array(12);this.frequency=130.8128;this.aim=130.8128;this.level=0;this.gate=0;this.t=0;}
 set(values){this.target.set(values);}
 sample(out){const smooth=1-Math.exp(-1/(this.rate*.14));this.level+=(this.gate-this.level)*(1-Math.exp(-1/(this.rate*.35)));this.frequency+=(this.aim-this.frequency)*smooth;out.fill(0);
  for(let k=0;k<12;k++){const j=2*k;this.now[j]+=(this.target[j]-this.now[j])*smooth;this.now[j+1]+=(this.target[j+1]-this.now[j+1])*smooth;
   const f=this.frequency*RATIOS[k];if(f>this.rate*.44)continue;
   this.phase[k]=(this.phase[k]+2*Math.PI*f/this.rate)%(2*Math.PI);
   const p=this.phase[k]+.002*Math.sin(this.t*.7+k),weight=.26/Math.pow(RATIOS[k],.53);
   out[Math.floor(k/4)]+=weight*(this.now[j]*Math.cos(p)-this.now[j+1]*Math.sin(p))*this.level;
  }this.t+=1/this.rate;return out;
 }
}
