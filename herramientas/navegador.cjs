'use strict';
const {chromium}=require('playwright');
async function lanzarChromium(){
  if(process.env.REJILLA_CHROME_PATH)return chromium.launch({headless:true,executablePath:process.env.REJILLA_CHROME_PATH});
  const intentos=[{}, {channel:'chrome'}, {channel:'msedge'}];let ultimo;
  for(const op of intentos){try{return await chromium.launch({headless:true,...op})}catch(e){ultimo=e}}
  throw new Error('Falta Chromium/Chrome/Edge. Ejecuta npm ci y npx playwright install chromium. '+ultimo.message);
}
module.exports={lanzarChromium};
