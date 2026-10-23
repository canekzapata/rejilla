// Linear decomposition of the SAME two pickups before their output protection.
// Sum of the eight apertures equals (unclipped L + unclipped R) / 2.
export function familySignals(q,left,right,out){
 out.fill(0);for(let i=0;i<64;i++)out[i&7]+=.39*q[i]*(left[i]+right[i]);return out;
}
