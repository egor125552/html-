"use strict";
(async()=>{
  const decode=async b64=>{
    const raw=atob(b64);
    const bytes=new Uint8Array(raw.length);
    for(let i=0;i<raw.length;i++) bytes[i]=raw.charCodeAt(i);
    const stream=new Blob([bytes]).stream().pipeThrough(new DecompressionStream("gzip"));
    return await new Response(stream).text();
  };
  try{
    for(const payload of [window.__c9Core,window.__c9App]){
      const script=document.createElement("script");
      script.textContent=await decode(payload);
      document.body.appendChild(script);
    }
  }catch(error){
    const start=document.getElementById("startButton");
    if(start){start.disabled=true;start.textContent="Ошибка загрузки игры";}
    const panel=document.getElementById("startPanel");
    if(panel){const p=document.createElement("p");p.textContent="Браузер не смог распаковать игровое ядро: "+error;panel.appendChild(p);}
  }
})();
