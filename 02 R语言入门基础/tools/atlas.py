"""Original Data Town atlas. Scenery is SVG; every learning link remains HTML."""
from html import escape as E
POSITIONS=[(160,195),(455,170),(800,240),(820,520),(535,460),(220,510),(245,795),(690,780)]

def tree(x,y,scale=1,sway=False):
 return f'<g transform="translate({x} {y}) scale({scale})"><ellipse cy="5" rx="18" ry="7" fill="#93adb0" opacity=".2"/><path d="M0 3v-39" stroke="#68858c" stroke-width="6"/><g class="{"tree-sway atlas-moving" if sway else ""}"><ellipse cy="-49" rx="24" ry="35" fill="#82ad9b"/><ellipse cx="-7" cy="-57" rx="13" ry="23" fill="#a8cabc"/><path d="M0-62v37" stroke="#dbeadd" stroke-width="2" opacity=".6"/></g></g>'

def cloud(x,y,scale=1):
 return f'<g transform="translate({x} {y}) scale({scale})"><g class="cloud-drift atlas-moving"><path d="M-58 9Q-79-15-46-20Q-35-58-6-31Q22-51 39-20Q71-16 61 10Z" fill="#fff" opacity=".85"/></g></g>'

def landmark(kind,x=90,y=128):
 s=f'<g transform="translate({x-85} {y-115})"><ellipse cx="85" cy="123" rx="87" ry="20" fill="#7695a0" opacity=".16"/>'
 roofs={'welcome':'#467a9c','objects':'#537f72','tidy':'#b6805e','charts':'#627ba3','scripts':'#467a9c','sampling':'#699a81','evidence':'#5a83a3','report':'#a77950'}
 roof=roofs[kind]
 if kind=='sampling':
  s+='<ellipse cx="85" cy="113" rx="71" ry="31" fill="#b2d1b8"/><ellipse cx="85" cy="113" rx="47" ry="22" fill="#d7e6d1"/><path d="M34 94V45h103v52" fill="none" stroke="#8caa9e" stroke-width="7"/><path d="M21 48 85 5 149 48Z" fill="#6f9f8b"/><path d="M85 5 149 48H87Z" fill="#598672"/><path d="M49 96h72v13H49Z" fill="#d6bc86"/>'
  for i in range(5):s+=f'<circle cx="{60+i*13}" cy="81" r="5" fill="{["#256187","#b9553d","#36866f"][i%3]}"/>'
 elif kind=='evidence':
  s+='<path d="M28 70Q26 4 86 6Q146 4 144 70Z" fill="#a9c8d5" stroke="#5d889a" stroke-width="3"/><path d="M85 7V69M28 70h116M40 38h92M85 8Q49 31 50 68M85 8q37 24 38 60" fill="none" stroke="#7fa9b8" stroke-width="3"/><path d="M27 72h118v48H27Z" fill="#e5e4cd"/><path d="M41 82h84v43H41Z" fill="#3b6475"/><path d="M50 91v25h63m-57-6 15-11 18 6 14-16" fill="none" stroke="#d7e4cf" stroke-width="2"/>'
 else:
  s+='<path d="M22 50h130v65l-61 16-69-17Z" fill="#e5dfc7"/><path d="M91 51h61v64l-61 16Z" fill="#c7cdbd"/>'
  if kind=='tidy':s+=f'<path d="M11 53V35l40-23v23l43-23v24l68 0v21Z" fill="{roof}"/><path d="M124 35V0h12v37" fill="#8296a0"/>'
  else:s+=f'<path d="M10 54 87 8 164 55l-8 13-69-42-72 39Z" fill="{roof}"/><path d="m87 8 77 47-8 13-69-42Z" fill="#173a50" opacity=".15"/>'
  s+='<path d="M72 83h29v45l-29-6Z" fill="#597b85"/><circle cx="94" cy="104" r="2.5" fill="#f1d48a"/>'
  for wx in [34,112]:s+=f'<rect x="{wx}" y="70" width="23" height="25" rx="2" fill="#9abccc" stroke="#68848c" stroke-width="2"/><path d="M{wx+11} 71v23M{wx+1} 82h21" stroke="#e7eee8" stroke-width="2"/>'
  if kind=='welcome':s+='<path d="M76 54h25v22H76Z" fill="#faf4d9"/><text x="88" y="72" text-anchor="middle" fill="#256187" font-size="18" font-family="Georgia">R</text><path d="M13 79V9" stroke="#6a8792" stroke-width="3"/><path class="flag-wave atlas-moving" d="M14 10h35l-8 12 8 11H14Z" fill="#c79a63"/>'
  if kind=='objects':
   for i in range(3):s+=f'<rect x="{5+i*24}" y="{119-i*8}" width="24" height="20" rx="2" fill="#bf9c66" stroke="#977f59"/><path d="M{11+i*24} {129-i*8}h11" stroke="#ebd9ac" stroke-width="2"/>'
  if kind in ('charts','scripts'):
   s+='<rect x="8" y="94" width="65" height="45" rx="3" fill="#2d586b" stroke="#72929b" stroke-width="3"/>'
   if kind=='charts':
    for i,h in enumerate([12,22,30,19]):s+=f'<rect x="{17+i*12}" y="{132-h}" width="8" height="{h}" fill="{["#d1ae78","#8fbca4"][i%2]}"/>'
   else:s+='<path d="m20 107-7 8 7 8m35-16 7 8-7 8m-15-20-8 22" stroke="#b9d4bd" fill="none" stroke-width="3"/>'
  if kind=='tidy':s+='<rect x="3" y="103" width="54" height="27" rx="5" fill="#7b9399"/><path d="M9 115h42" stroke="#d3dfd7" stroke-width="5"/><circle cx="16" cy="130" r="8" fill="#547785"/><circle cx="47" cy="130" r="8" fill="#547785"/>'
  if kind=='report':s+='<path d="M20 61h130v7H20Z" fill="#f4e6c4"/><path d="M36 68v45m100-45v45" stroke="#f4e6c4" stroke-width="10"/><path d="M65 82h41v-23H65Z" fill="#eeeccf"/><path d="M71 66h29m-29 7h20" stroke="#65818b" stroke-width="3"/><path d="M5 131h155v9H5Z" fill="#bbc7c2"/>'
 return s+'</g>'

def scene(zones):
 s='<svg class="town-scene" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 1000" aria-hidden="true"><defs><pattern id="survey-grid" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M40 0H0V40" fill="none" stroke="#b6cbd4" stroke-width=".6" opacity=".3"/></pattern></defs><rect width="1000" height="1000" fill="#e5eef1"/><rect width="1000" height="1000" fill="url(#survey-grid)"/>'
 s+='<path d="M0 60Q200-13 330 63T650 32 1000 80V0H0Z" fill="#cbded6"/><path d="M0 693Q70 638 115 711T123 1000H0Z" fill="#c2dce3"/><path class="water-flow atlas-moving" d="M15 760q95 65 43 227" fill="none" stroke="#e6f3f4" stroke-width="3" stroke-dasharray="14 25"/><path d="M867 748q88-86 133-40v292H833q-71-107 34-252Z" fill="#d1e2d5"/>'
 # Roads link the eight districts in course order, with small side streets.
 road='M90 206Q263 139 455 198T820 260Q970 370 822 548Q666 626 535 489T220 540Q98 668 248 816Q460 941 697 809'
 s+=f'<path d="{road}" fill="none" stroke="#c2cecc" stroke-width="49" stroke-linecap="round"/><path d="{road}" fill="none" stroke="#f6f2dc" stroke-width="39" stroke-linecap="round"/><path d="{road}" fill="none" stroke="#d1c49f" stroke-width="2" stroke-dasharray="7 12"/>'
 s+='<path d="M455 201 528 488M220 540 248 816M535 489 695 809" fill="none" stroke="#d1dadd" stroke-width="13" stroke-linecap="round"/><path d="M455 201 528 488M220 540 248 816M535 489 695 809" fill="none" stroke="#f5f4e7" stroke-width="7"/>'
 # Quiet central garden, survey markers, benches and lamps.
 s+='<ellipse cx="442" cy="672" rx="119" ry="82" fill="#d0e2cd"/><ellipse cx="441" cy="670" rx="73" ry="47" fill="#b5d5dc"/><ellipse cx="441" cy="670" rx="55" ry="33" fill="#c5e2e7"/><path d="M438 658v-31m-12 13 12-13 13 13" stroke="#f1f9f6" fill="none" stroke-width="3"/>'
 for x,y,scale in [(42,347,.8),(85,383,1),(350,380,.65),(652,106,.9),(917,183,1),(934,650,.85),(83,888,.7),(462,873,.7),(842,900,.9),(887,854,.7),(104,611,.8),(356,594,.55)]:s+=tree(x,y,scale,sway=x in [85,917,842])
 for x,y in [(290,123),(613,328),(867,684),(172,740),(583,831)]:s+=f'<g transform="translate({x} {y})"><path d="M0 0V-32h15" fill="none" stroke="#718b96" stroke-width="3"/><circle cx="15" cy="-31" r="6" fill="#e5c994"/></g>'
 for zone,(x,y) in zip(zones,POSITIONS):s+=landmark(zone['id'],x,y)
 s+=cloud(279,64,.75)+cloud(725,359,.55)+cloud(764,947,.7)
 s+='<g transform="translate(757 82)"><g class="bird-flight atlas-moving" fill="none" stroke="#466b80" stroke-width="2.5" stroke-linecap="round"><g class="bird-wing atlas-moving"><path d="M-18 2Q-8-8 0 1Q8-8 18 2"/></g><path d="M32 20q10-10 19 0 10-10 19 0"/></g></g>'
 s+='<g fill="#6f919f" font-family="Georgia,serif"><text x="55" y="945" font-size="15" letter-spacing="4">DATA TOWN</text><text x="55" y="967" font-size="11">A FIELD GUIDE TO R</text></g></svg>'
 return s

def render_atlas(lessons,zones):
 s='<div id="atlas-map" class="atlas-map" data-motion="paused"><div class="town-landscape" aria-label="八个街区的学习地图">'+scene(zones)
 for zone,(x,y) in zip(zones,POSITIONS):
  ls=[l for l in lessons if l['zone']==zone['id']];ids=','.join(l['id'] for l in ls)
  s+=f'<a class="town-stop" style="--x:{x/10}%;--y:{(y+10)/10}%" href="#district-{zone["id"]}" data-select-zone="{zone["id"]}" data-zone-lessons="{ids}"><span class="stop-range">{ls[0]["id"]}—{ls[-1]["id"]}</span><strong>{E(zone["title"])}</strong><span class="zone-progress">0 / {len(ls)} 已读</span></a>'
 s+='</div><div class="district-panels" aria-label="街区课程">'
 for zi,zone in enumerate(zones):
  ls=[l for l in lessons if l['zone']==zone['id']];ids=','.join(l['id'] for l in ls)
  s+=f'<section class="district-panel" id="district-{zone["id"]}" data-panel-zone="{zone["id"]}" data-zone-lessons="{ids}" aria-labelledby="title-{zone["id"]}"><div class="district-portrait"><svg viewBox="0 0 180 160" aria-hidden="true">{landmark(zone["id"])}</svg></div><p class="eyebrow">第 {zi+1} 街区 / {ls[0]["id"]}—{ls[-1]["id"]}</p><h3 id="title-{zone["id"]}">{E(zone["title"])}</h3><p class="district-subtitle">{E(zone["subtitle"])}</p><p class="zone-progress">0 / {len(ls)} 已读</p><ol class="zone-lessons">'
  for l in ls:
   s+=f'<li><a class="map-lesson" href="lessons/{l["id"]}.html" data-course-lesson="{l["id"]}"><span class="map-lesson-number">{l["id"]}</span><span class="map-lesson-title">{E(l["title"])}</span><span class="map-lesson-status" aria-hidden="true">↗</span><span class="map-state sr-only">未读</span></a></li>'
  s+='</ol><p class="district-note">每一站都能自由进入。读完后，可在章节末尾记录进度。</p></section>'
 return s+'</div></div>'
