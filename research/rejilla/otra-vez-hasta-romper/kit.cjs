const fs=require('fs'),path=require('path');
const {chromium}=require('C:/Users/HP-PC/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const out=path.resolve(process.argv[2]),base=path.resolve(__dirname,'../catalogo-agua-que-habla/instrumentos-48b8a06e1049');
(async()=>{const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});try{
const page=await browser.newPage();await page.setContent('<title>Kit local</title>');await page.addScriptTag({content:fs.readFileSync(path.join(base,'motores/web.js'),'utf8')});
for(const pieza of ['kick','snare','rim','clap','hat','openhat','spray','tomlo']){
const bytes=await page.evaluate(async({ficha,pieza})=>{const ctx=new OfflineAudioContext(1,48000,24000);Instrumentos.tocar(ctx,ctx.destination,ficha,{t:0,midi:60,vel:.8,dur:.3,pieza},{tonica:'A'});const b=await ctx.startRendering(),y=b.getChannelData(0);return Array.from(y);},{pieza,ficha:JSON.parse(fs.readFileSync(path.join(base,'fichas/bateria-frito.json'),'utf8'))});
const y=Float32Array.from(bytes);fs.writeFileSync(path.join(out,'render','kit-'+pieza+'.f32'),Buffer.from(y.buffer),{flag:'wx'});
}console.log('8 piezas del kit original renderizadas');}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
