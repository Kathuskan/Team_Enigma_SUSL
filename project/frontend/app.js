import {renderFarm} from "./farm.bundle.js";
import {localize} from "./language.js";
import {compressPhoto,recordSpeech} from "./media.js";

let photo="", recorder, photoVersion=0;
const $ = id => document.getElementById(id);
let farm;
let selectedArea;
let recognition;
let retry;

// ── Localised fallback replies ───────────────────────────────────────────────
const replies = {
  en: {delay:"Delay spraying during this window. The field forecast shows a risk of wash-off or spray drift.", unavailable:"The weather could not be verified. Check field conditions before making a spray decision.", review:"The forecast alone cannot confirm a treatment.", end:"Ask an Agricultural Instructor to review the crop before choosing a treatment."},
  ta: {delay:"இந்த நேரத்தில் தெளிப்பதை ஒத்திவைக்கவும். மழை அல்லது காற்றால் மருந்து வீணாகலாம்.", unavailable:"வானிலைத் தகவலை உறுதிப்படுத்த முடியவில்லை. தெளிப்பதற்கு முன் வயல் நிலையைச் சரிபார்க்கவும்.", review:"வானிலைத் தகவலை மட்டும் வைத்து சிகிச்சையைத் தேர்வு செய்ய முடியாது.", end:"சிகிச்சையைத் தேர்வு செய்வதற்கு முன் விவசாயப் போதனாசிரியரிடம் பயிரைக் காட்டவும்."},
  si: {delay:"මෙම කාලය තුළ ඉසීම කල් දමන්න. වර්ෂාවෙන් සේදී යාමට හෝ සුළඟින් ගසාගෙන යාමට ඉඩ ඇත.", unavailable:"කාලගුණය තහවුරු කරගත නොහැකි විය. ඉසීමට පෙර කුඹුරේ තත්ත්වය පරීක්ෂා කරන්න.", review:"කාලගුණ අනාවැකියෙන් පමණක් ප්‍රතිකාරයක් තීරණය කළ නොහැක.", end:"ප්‍රතිකාරයක් තෝරා ගැනීමට පෙර කෘෂිකර්ම උපදේශකවරයාට වගාව පෙන්වන්න."}
};

// ── Helpers ──────────────────────────────────────────────────────────────────
function status(message){$("status").textContent=message}
function el(tag,text){const node=document.createElement(tag);node.textContent=text;return node}

async function api(path, body){
  const options = body ? {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)} : {};
  const response = await fetch("/api/"+path,options);
  if(!response.ok){const data=await response.json(); throw Error(typeof data.detail==="string"?data.detail:"Check your input and try again.")}
  return response.json();
}

// ── Playback ─────────────────────────────────────────────────────────────────
let playing, playbackVersion=0;
function stopPlayback(){
  playbackVersion++;window.speechSynthesis?.cancel();
  if(playing){playing.pause();URL.revokeObjectURL(playing.src);playing=null}
  $("stopVoice").hidden=true;
}
$("stopVoice").onclick=stopPlayback;
$("voiceChat").onchange=()=>{if($("voiceChat").checked)$("dictate").click();else stopPlayback()};

async function speak(text,lang,id){
  stopPlayback();const version=playbackVersion;
  const synth=window.speechSynthesis;
  const voice=synth?.getVoices().find(v=>v.lang.split("-")[0]===lang.split("-")[0]);
  if(!voice){
    if(!farm.cloud_speech||!id){status("Enable cloud playback or install a voice for this language.");return}
    try{
      const res=await fetch("/api/speech/"+id);
      if(!res.ok)throw Error((await res.json()).detail);
      const clip=await res.blob();if(version!==playbackVersion)return;
      const url=URL.createObjectURL(clip);playing=new Audio(url);$("stopVoice").hidden=false;
      playing.onended=stopPlayback;await playing.play();
    }catch(err){status(err.message)}
    return;
  }
  const line=new SpeechSynthesisUtterance(text);line.voice=voice;line.lang=voice.lang;line.onend=()=>{if(version===playbackVersion)$("stopVoice").hidden=true};$("stopVoice").hidden=false;synth.speak(line);
}

function voiceCopy(){
  return {"en-LK":{speak:"Speak your question",stop:"Stop recording",play:"▶ Play reply"},
    "ta-LK":{speak:"கேள்வியைப் பேசுங்கள்",stop:"பதிவை நிறுத்து",play:"▶ பதிலைக் கேட்க"},
    "si-LK":{speak:"ප්‍රශ්නය කියන්න",stop:"පටිගත කිරීම නවත්වන්න",play:"▶ පිළිතුර අසන්න"}}[$("lang").value];
}

// ── Crop stage helper ─────────────────────────────────────────────────────────
// Derive a rough stage from crop_day (days after transplanting).
// If the backend profile gives explicit data we use it; otherwise we infer.
function inferStage(cropDay){
  if(!cropDay)return null;
  if(cropDay<=21)return 0;   // Seedling
  if(cropDay<=55)return 1;   // Vegetative
  if(cropDay<=80)return 2;   // Flowering
  return 3;                   // Harvest
}
const STAGE_NAMES=["Seedling","Vegetative","Flowering","Harvest"];

function renderStages(profile){
  const stageItems=$("stageList").querySelectorAll("li");
  const cropDay=profile?.crop_day;
  const stageIdx=inferStage(cropDay);
  stageItems.forEach((li,i)=>{
    li.className="";
    if(stageIdx===null)return;
    if(i<stageIdx)li.className="done";
    else if(i===stageIdx)li.className="active";
  });
  const note=$("stageNote");
  if(cropDay){
    note.innerHTML="<strong>Day "+cropDay+" after transplanting</strong>Advice is tuned to protect the crop at this stage.";
    note.hidden=false;
  } else {
    note.hidden=true;
  }
}

// ── Sidebar: active field ─────────────────────────────────────────────────────
function renderSidebar(){
  const hasField=!!farm.area;
  $("sideFieldLabel").hidden=!hasField;
  $("sideActiveField").hidden=!hasField;
  if(hasField){
    $("activeName").textContent=farm.area;
    const p=farm.profile;
    const parts=[p.season_name||("Season "+farm.season)];
    if(p.crop_day)parts.push("Day "+p.crop_day);
    $("activeMeta").textContent=parts.join(" · ");
  }
  const p=farm.profile;
  const hasSeasonInfo=!!(p.season_name||p.crop_day);
  $("sideSeasonCard").hidden=!hasField||!hasSeasonInfo;
  if(hasField&&hasSeasonInfo){
    $("sideSeasonName").textContent=p.season_name ? p.season_name+" season" : "Season "+farm.season;
    const stageIdx=inferStage(p.crop_day);
    $("sideCropDay").textContent=p.crop_day
      ? "Day "+p.crop_day+(stageIdx!==null?" · "+STAGE_NAMES[stageIdx]+" stage":"")
      : "";
  }
}

// ── Field brief ───────────────────────────────────────────────────────────────
function renderBrief(){
  const hasField=!!farm.area;
  $("heroRow").hidden=!hasField;
  $("noFieldHint").hidden=hasField;
  if(!hasField)return;
  const p=farm.profile;
  $("briefWhere").textContent=farm.area;
  // Crop stage facts
  const stageIdx=inferStage(p.crop_day);
  if(stageIdx!==null){$("briefStage").textContent=STAGE_NAMES[stageIdx];$("briefStageFact").hidden=false;}else{$("briefStageFact").hidden=true;}
  if(p.season_name){$("briefSeason").textContent=p.season_name;$("briefSeasonFact").hidden=false;}else{$("briefSeasonFact").hidden=true;}
  if(p.crop_day){$("briefDay").textContent="Day "+p.crop_day;$("briefDayFact").hidden=false;}else{$("briefDayFact").hidden=true;}
  // Season progress bar (if duration_months known)
  if(p.crop_day&&p.duration_months){
    const total=Math.round(parseFloat(p.duration_months)*30);
    const pct=Math.min(100,Math.round(p.crop_day/total*100));
    const bar=$("briefBar");
    bar.setAttribute("aria-valuenow",pct);
    $("briefBarFill").style.width=pct+"%";
    $("briefPct").textContent=pct+"% of season";
    bar.hidden=false;$("briefPct").hidden=false;
  } else {
    $("briefBar").hidden=true;$("briefPct").hidden=true;
  }
  // Brief title/text
  const lastTurn=farm.turns.at(-1);
  if(lastTurn?.answer){
    $("briefTitle").textContent=farm.area+" — latest advice";
    $("briefText").textContent=lastTurn.answer.slice(0,160)+(lastTurn.answer.length>160?"…":"");
  } else {
    $("briefTitle").textContent="Your field is confirmed.";
    $("briefText").textContent="Ask a question below to get advice tailored to your field, weather, and crop stage.";
  }
}

// ── Weather card ─────────────────────────────────────────────────────────────
// Show live weather from the last turn's weather object (returned by /api/chat)
function renderWeather(){
  const lastTurn=farm.turns.at(-1);
  const w=lastTurn?.weather;
  if(!farm.area){$("wxTitle").textContent="—";$("wxList").hidden=true;$("wxBest").hidden=true;$("wxHint").hidden=false;$("wxLoc").textContent="";$("wxTemp").textContent="";return;}
  $("wxLoc").innerHTML=farm.area+' <span class="livedot">Live</span>';
  if(!w){
    $("wxTitle").textContent="Ask a question to load weather";
    $("wxHint").hidden=false;
    $("wxList").hidden=true;
    $("wxBest").hidden=true;
    $("wxTemp").textContent="";
    return;
  }
  $("wxHint").hidden=true;
  // Build summary from weather object: {start, probability, rain_mm, wind_kmh, humidity, wash_off, drift, humid}
  const good=!w.wash_off&&!w.drift&&!w.humid;
  $("wxTitle").textContent=good?"Conditions look suitable":"Check conditions before spraying";
  $("wxTemp").textContent="";
  const list=$("wxList");
  list.innerHTML="";
  const makeRow=(label,value,note)=>{const li=document.createElement("li");li.innerHTML=`<b>${label}</b><span>${value}</span><span>${note}</span>`;return li;};
  list.append(
    makeRow("Rain",w.rain_mm+" mm",w.probability+"% chance"),
    makeRow("Wind",w.wind_kmh+" km/h",w.drift?"⚠ Drift risk":"OK"),
    makeRow("Humidity",w.humidity+"%",w.humid?"⚠ High":"OK")
  );
  list.hidden=false;
  const best=$("wxBest");
  const startFmt=w.start?w.start.slice(0,16).replace("T"," "):"";
  best.innerHTML=`<strong>${good?"Suitable window":"Caution advised"}</strong><small>12 h from ${startFmt} · ${w.rain_mm} mm rain · ${w.wind_kmh} km/h wind</small>`;
  best.hidden=false;
}

// ── Main render ───────────────────────────────────────────────────────────────
function render(){
  if(!recognition&&!recorder)$("dictate").textContent=voiceCopy().speak;
  localize($("lang").value);
  const words=replies[$("lang").value.slice(0,2)];

  // Populate area dropdown once
  if(!$("area").options.length) $("area").replaceChildren(new Option("Select field area",""),...farm.areas.map(a=>new Option(a,a)));
  $("area").value=selectedArea ?? farm.area ?? "";

  // FarmBar (React: season reset widget)
  renderFarm({farm,language:$("lang").value,onReset:async season=>{
    try{await api("season",{season:farm.season,confirmed:true,season_name:season});retry=null;await refresh()}
    catch(err){status(err.message);throw err}
  }});

  // Send button enabled only when selected area matches confirmed area
  $("send").disabled=!farm.area || $("area").value!==farm.area;

  // Sync indicator
  $("syncStatus").innerHTML='<i></i>Synced just now';

  // Sidebar
  renderSidebar();

  // Field brief
  renderBrief();

  // Weather
  renderWeather();

  // Crop stage tracker
  renderStages(farm.profile);

  // Conversation history
  $("history").replaceChildren();
  for(const t of farm.turns){
    const article=el("article","");article.className="turn";
    const answer=t.answer || words[t.outcome]+" "+words.end;
    article.append(el("strong",t.question),el("p",answer));
    if(t.weather){
      const w=t.weather;
      article.append(el("p",t.area+" · "+w.start.slice(0,16).replace("T"," ")+" · 12 h · "+w.rain_mm+" mm · "+w.probability+"% rain · "+w.wind_kmh+" km/h"));
    }
    const play=el("button",voiceCopy().play);play.className="turn-btn";play.onclick=()=>speak(answer,t.language||$("lang").value,t.id);article.append(play);
    if(t.outcome==="advice")for(const ref of t.references||[])article.append(el("small",ref.title+" · "+ref.section));
    if(t.decision==="ESCALATE_HUMAN"){
      const share=el("button","Share instructor summary");share.className="turn-btn";
      share.onclick=async()=>{
        const text=[t.area,t.question,answer,t.vision?.signs,JSON.stringify(t.referral_profile||farm.profile)].filter(Boolean).join("\n");
        try{
          const payload={title:"PaddyGuard field case",text};
          if(t.referral_photo){
            const res=await fetch("/api/referral/"+t.id+"/photo");
            if(!res.ok)throw Error("Could not load the referral photo.");
            const file=new File([await res.blob()],"field-photo.jpg",{type:"image/jpeg"});
            if(navigator.canShare?.({files:[file]}))payload.files=[file];
            else{
              const link=el("a","Save referral photo");link.href="/api/referral/"+t.id+"/photo";link.download="field-photo.jpg";
              if(!article.querySelector("a[download]"))article.append(link);
            }
          }
          if(navigator.share)await navigator.share(payload);else{await navigator.clipboard.writeText(text);status("Case summary copied.")}
        }catch(err){if(err.name!=="AbortError")status(err.message)}
      };article.append(share);
    }
    $("history").append(article);
  }

  // Decision trace (last turn)
  $("trace").replaceChildren(...(farm.turns.at(-1)?.trace||[]).map(x=>el("li",x)));
}

async function refresh(){farm=await api("farm");render()}

// ── Form events ───────────────────────────────────────────────────────────────
$("area").onchange=()=>{selectedArea=$("area").value;$("send").disabled=selectedArea!==farm.area};
$("field").onsubmit=async e=>{
  e.preventDefault();
  try{await api("field",{area:$("area").value});selectedArea=undefined;await refresh();status("Field confirmed: "+farm.area+".")}
  catch(err){status(err.message)}
};
$("chat").onsubmit=async e=>{
  e.preventDefault();
  if($("area").value!==farm.area){status("Confirm the selected field first.");return}
  const text=$("message").value.trim();if(!text&&!photo){status("Enter a question or attach a crop photo.");return}
  const payload={text:text||"Inspect this crop photo",photo,language:$("lang").value,window:$("window").value,season:farm.season};
  const signature=JSON.stringify([farm.area,payload]);
  if(retry?.signature!==signature)retry={signature,id:crypto.randomUUID()};
  $("send").disabled=true;
  status({"en-LK":"Reading your question…","ta-LK":"உங்கள் கேள்வியை வாசிக்கிறோம்…","si-LK":"ඔබේ ප්‍රශ්නය කියවනවා…"}[$("lang").value]||"Reading your question…");
  let waiting=true;
  const poll=setInterval(async()=>{
    try{const data=await api("progress/"+retry.id);if(waiting&&data.events.length)$("trace").replaceChildren(...data.events.map(x=>el("li",x)))}catch{}
  },900);
  try{
    const sentId=retry.id;
    const reply=await api("chat",{...payload,id:sentId});
    if(reply.language){$("lang").value=reply.language;localStorage.setItem("language",reply.language)}
    await refresh();$("message").value="";clearPhoto();retry=null;status("");
    if($("voiceChat").checked)await speak(reply.answer,reply.language||payload.language,sentId)
  }catch(err){status(err.message)}
  finally{waiting=false;clearInterval(poll);$("send").disabled=!farm.area}
};

$("lang").onchange=()=>{
  recognition?.abort();window.speechSynthesis?.cancel();
  localStorage.setItem("language",$("lang").value);
  if(farm)render()
};

// ── Photo ─────────────────────────────────────────────────────────────────────
function clearPhoto(){
  photoVersion++;photo="";$("photo").value="";$("preview").removeAttribute("src");$("attachment").hidden=true;
}
$("remove").onclick=clearPhoto;
$("photo").onchange=async()=>{
  const file=$("photo").files[0];clearPhoto();if(!file)return;
  const version=photoVersion;
  $("send").disabled=true;
  try{const encoded=await compressPhoto(file);if(version!==photoVersion)return;
    photo=encoded;$("preview").src="data:image/jpeg;base64,"+photo;$("attachment").hidden=false;
  }catch(err){status(err.message)}finally{if(version===photoVersion)$("send").disabled=!farm?.area}
};

// ── Dictate ───────────────────────────────────────────────────────────────────
$("dictate").onclick=async()=>{
  if(recorder?.state==="recording"){recorder.stop();return}
  if(recognition){recognition.stop();return}
  stopPlayback();
  const lang=$("lang").value;
  const done=()=>{recognition=null;recorder=null;$("dictate").textContent=voiceCopy().speak;$("dictate").disabled=false};
  const append=text=>{$("message").value=[$("message").value,text].filter(Boolean).join(" ");status(({"en-LK":"Check crop names, numbers and units before sending.","ta-LK":"அனுப்பும் முன் பயிர் பெயர்கள், எண்கள் மற்றும் அலகுகளைச் சரிபாருங்கள்.","si-LK":"යැවීමට පෙර බෝග නාම, සංඛ්‍යා සහ ඒකක පරීක්ෂා කරන්න."})[lang])};
  try{
    $("dictate").disabled=true;
    if(farm?.cloud_speech||(await api("farm")).cloud_speech){
      recorder=await recordSpeech(async audio=>{
        $("dictate").disabled=true;status("Transcribing…");
        try{const result=await api("transcribe",{language:lang,audio});append(result.transcript)}finally{done()}
      },err=>{done();status(err.message)});
    }else{
      const Speech=window.SpeechRecognition||window.webkitSpeechRecognition;
      if(!Speech)throw Error("Cloud transcription needs GEMINI_API_KEY on the server. Refresh after it is configured.");
      const rec=new Speech();rec.lang=lang;
      rec.onresult=e=>append(e.results[0][0].transcript);
      rec.onerror=e=>status("Browser speech service: "+e.error+". Configure server cloud transcription if this continues.");
      rec.onend=done;rec.start();recognition=rec;
    }
    $("dictate").disabled=false;$("dictate").textContent=voiceCopy().stop;status("Listening…");
  }catch(err){done();status(err.message)}
};

// ── Init ──────────────────────────────────────────────────────────────────────
// Dynamic today date
(function(){
  const d=new Date();
  const el=document.getElementById("todayDate");
  if(el){
    const days=["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"];
    const months=["January","February","March","April","May","June","July","August","September","October","November","December"];
    el.textContent=days[d.getDay()]+", "+d.getDate()+" "+months[d.getMonth()]+" "+d.getFullYear();
  }
})();

$("lang").value=localStorage.getItem("language")||"en-LK";
refresh().catch(err=>{status(err.message);$("syncStatus").textContent="Offline"});
if("serviceWorker" in navigator)navigator.serviceWorker.register("/sw.js").catch(()=>{});
