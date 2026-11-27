import React, {useState} from "react";
import {createRoot} from "react-dom/client";

const copy={
  "en-LK":["My Farm","New season","Start a new season?","This clears the current crop details and keeps your field area.","Start","Cancel","Day","months"],
  "ta-LK":["என் வயல்","புதிய போகம்","புதிய போகத்தைத் தொடங்கவா?","வயலின் இடம் சேமிக்கப்படும். தற்போதைய பயிர் விவரங்கள் மீட்டமைக்கப்படும்.","தொடங்கு","ரத்து","நாள்","மாதங்கள்"],
  "si-LK":["මගේ කුඹුර","නව කන්නය","නව කන්නයක් අරඹන්නද?","කුඹුරේ ප්‍රදේශය තබා වත්මන් වගා විස්තර හිස් කරයි.","අරඹන්න","අවලංගු","දිනය","මාස"]
};
function FarmBar({farm,language,onReset}){
  const [open,show]=useState(false),[season,select]=useState(""),[busy,setBusy]=useState(false);
  const t=copy[language]||copy["en-LK"], p=farm.profile;
  if(!farm.area)return null;
  return <div className="rounded-lg border border-green-900 bg-white px-3 py-2 shadow-sm">
    <div className="flex items-center justify-between gap-2"><strong>{t[0]}</strong><button id="reset" onClick={()=>{select("");show(true)}}>{t[1]}</button></div>
    <div id="profile">{[farm.area,p.season_name,p.variety_name,p.planted,p.water,p.duration_months && p.duration_months+" "+t[7],p.crop_day && t[6]+" "+p.crop_day].filter(Boolean).join(" · ")}</div>
    {open && <form onSubmit={async e=>{e.preventDefault();setBusy(true);try{await onReset(season);show(false)}finally{setBusy(false)}}}>
      <fieldset disabled={busy}><legend>{t[2]}</legend><p>{t[3]}</p>
      {["Yala","Maha"].map(name=><label key={name} className="mr-3"><input type="radio" required name="season" value={name} checked={season===name} onChange={()=>select(name)}/>{name}</label>)}
      <div className="flex gap-2"><button disabled={!season}>{t[4]}</button><button type="button" onClick={()=>show(false)}>{t[5]}</button></div></fieldset>
    </form>}
  </div>
}
const root=createRoot(document.querySelector("#farmBar"));
export function renderFarm(props){root.render(<FarmBar {...props}/>)}
