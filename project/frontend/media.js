const read64 = blob => new Promise((ok,fail)=>{
  const reader=new FileReader();
  reader.onload=()=>ok(reader.result.split(",")[1]);
  reader.onerror=()=>fail(new Error("Could not read the file."));
  reader.readAsDataURL(blob);
});
export async function compressPhoto(file){
  const image=await createImageBitmap(file);
  try{
    const scale=Math.min(1,1500/Math.max(image.width,image.height));
    const canvas=document.createElement("canvas");
    canvas.width=Math.max(1,Math.round(image.width*scale));
    canvas.height=Math.max(1,Math.round(image.height*scale));
    canvas.getContext("2d").drawImage(image,0,0,canvas.width,canvas.height);
    for(const quality of [.85,.7,.5,.35]){
      const blob=await new Promise(resolve=>canvas.toBlob(resolve,"image/jpeg",quality));
      if(blob && blob.size<1000000)return read64(blob);
    }
    throw Error("Choose a smaller photo.");
  }finally{image.close()}
}
async function wav64(blob){
  const context = new AudioContext();
  let decoded;
  try{decoded=await context.decodeAudioData(await blob.arrayBuffer())}finally{await context.close()}
  const length=Math.min(60*16000,Math.ceil(decoded.duration*16000));
  const offline=new OfflineAudioContext(1,length,16000);
  const source=offline.createBufferSource();source.buffer=decoded;source.connect(offline.destination);source.start();
  const samples=(await offline.startRendering()).getChannelData(0);
  const bytes=new ArrayBuffer(44+length*2), view=new DataView(bytes);
  function ascii(i,s){for(let n=0;n<s.length;n++)view.setUint8(i+n,s.charCodeAt(n))}
  ascii(0,"RIFF");view.setUint32(4,bytes.byteLength-8,true);ascii(8,"WAVE");ascii(12,"fmt ");
  view.setUint32(16,16,true);view.setUint16(20,1,true);view.setUint16(22,1,true);
  view.setUint32(24,16000,true);view.setUint32(28,32000,true);view.setUint16(32,2,true);view.setUint16(34,16,true);
  ascii(36,"data");view.setUint32(40,length*2,true);
  samples.forEach((v,i)=>view.setInt16(44+i*2,Math.max(-1,Math.min(1,v))*32767,true));
  return read64(new Blob([bytes]));
}
export async function recordSpeech(onAudio,onError){
  const stream=await navigator.mediaDevices.getUserMedia({audio:true});
  let recorder;
  try{recorder=new MediaRecorder(stream)}catch(err){stream.getTracks().forEach(t=>t.stop());throw err}
  const chunks=[];let timer;
  recorder.ondataavailable=e=>{if(e.data.size)chunks.push(e.data)};
  recorder.onstop=async()=>{
    clearTimeout(timer);stream.getTracks().forEach(t=>t.stop());
    try{await onAudio(await wav64(new Blob(chunks,{type:recorder.mimeType})))}catch(err){onError(err)}
  };
  recorder.start();timer=setTimeout(()=>{if(recorder.state==="recording")recorder.stop()},59000);
  return recorder;
}

