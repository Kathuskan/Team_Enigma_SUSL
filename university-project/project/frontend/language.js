const labels=[
 ["#voiceLabel","Voice conversation · read replies aloud","குரல் உரையாடல் · பதிலை வாசிக்கவும்","හඬ සංවාදය · පිළිතුර කියවන්න"],
 ["#stopVoice","Stop playback","வாசிப்பை நிறுத்து","කියවීම නවත්වන්න"],
 ["h1","My paddy field","எனது நெல் வயல்","මගේ කුඹුර"],
 ["label[for=area]","Where is your field?","உங்கள் வயல் எங்கே உள்ளது?","ඔබේ කුඹුර පිහිටා ඇත්තේ කොහේද?"],
 ["#field button","Confirm field","வயலை உறுதிப்படுத்து","කුඹුර තහවුරු කරන්න"],
 ["#reset","Start new season","புதிய போகத்தைத் தொடங்கு","නව කන්නයක් අරඹන්න"],
 ["section h2","Field conversation","வயல் உரையாடல்","කුඹුර ගැන කතාබහ"],
 ["label[for=message]","Ask about field conditions","வயல் நிலை பற்றிக் கேளுங்கள்","කුඹුරේ තත්ත්වය ගැන අසන්න"],
 ["label[for=window]","Check the next 12 hours starting","அடுத்த 12 மணிநேரம் தொடங்கும் நேரம்","ඉදිරි පැය 12 ඇරඹෙන වේලාව"],
 ["#window option[value=tomorrow]","Tomorrow at 6 am","நாளை காலை 6 மணி","හෙට පෙ.ව. 6"],
 ["#window option[value=now]","This hour","இந்த மணி நேரம்","මෙම පැය"],
 ["label[for=photo]","Attach a leaf or pest photo","இலை அல்லது பூச்சியின் படத்தைச் சேர்க்கவும்","පත්‍රයක හෝ කෘමියෙකුගේ ඡායාරූපයක් එක් කරන්න"],
 ["#remove","Remove photo","படத்தை நீக்கு","ඡායාරූපය ඉවත් කරන්න"],
 ["#send","Send","அனுப்பு","යවන්න"],
 ["aside h2","Decision record","முடிவுப் பதிவு","තීරණ වාර්තාව"],
 [".hint","Dictation may send audio to a cloud speech service. Review your words before sending. Attached photos are sent for analysis when you press Send.","குரல் பதிவு மேகச் சேவைக்கு அனுப்பப்படலாம். அனுப்பும் முன் எழுத்தைச் சரிபாருங்கள். அனுப்பு என்பதை அழுத்தும்போது படம் ஆய்விற்கு அனுப்பப்படும்.","හඬ පටිගත කිරීම වලාකුළු සේවාවකට යැවිය හැක. යැවීමට පෙර වචන බලන්න. යවන්න එබූ විට ඡායාරූපය විශ්ලේෂණයට යැවේ."]
];
export function localize(tag){
  const i={"en-LK":1,"ta-LK":2,"si-LK":3}[tag]||1;
  document.documentElement.lang=tag;
  for(const row of labels)document.querySelector(row[0]).textContent=row[i];
}

