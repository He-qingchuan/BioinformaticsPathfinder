"""Original SVG artwork for the teaching archipelago; no external art assets."""
from pathlib import Path
import random
ROOT=Path(__file__).resolve().parents[1]

def make_art():
    symbols={
      'leaf':'<path d="M35 91C14 42 61 14 104 17c2 47-16 79-64 73Z" fill="#89ad72"/><path d="M34 103 87 34M50 83l-6-26m19 10 24-4m-13-9-1-19" fill="none"/><path d="M32 101h52l-9 14H40Z" fill="#d99e67"/>',
      'port':'<path d="M12 83h100l-17 25H35Z" fill="#b98559"/><path d="M62 15v68M66 20l40 51H66Z" fill="#fff9de"/><path d="m56 32-31 37h31Z" fill="#cf8468"/><path d="M14 114q14-10 28 0t28 0t28 0" fill="none" stroke="#59909a"/>',
      'library':'<path d="M23 51h80v59H23Z" fill="#f8e6b5"/><path d="m14 50 50-32 48 32Z" fill="#769d90"/><path d="M31 59v43m19-43v43m21-43v43m21-43v43M17 111h93M21 104h85" fill="none"/><path d="M57 35h15v10H57Z" fill="#fffaf0"/>',
      'lighthouse':'<path d="m39 105 9-66h29l11 66Z" fill="#fffbeb"/><path d="m45 66 36 0 4 19H42Z" fill="#cf8061"/><path d="M41 24h44v17H41Z" fill="#f2cf70"/><path d="m37 24 26-17 27 17ZM34 106h60v8H34Z" fill="#769d90"/><path d="M57 91h13v15H57ZM26 31 9 25m17 15L8 47m93-18 15-5m-15 16 17 7" fill="none"/>',
      'workshop':'<path d="M19 49h87v62H19Z" fill="#f4d8a5"/><path d="m12 49 46-27 56 27Z" fill="#7aa28e"/><path d="M85 36V16h11v26" fill="#ead6af"/><path d="M51 75h29v36H51ZM28 62h14v17H28ZM87 62h12v17H87Z" fill="#c1dce0"/><path d="M29 107h10m56 0h8M56 83h17" fill="none"/>',
      'salmon':'<path d="M15 50h97v52H15Z" fill="#efd8a7"/><path d="M9 49 63 18l55 31Z" fill="#6f9f9a"/><path d="M24 85q29-41 62-6l19-11v25L87 82q-31 31-63 3Z" fill="#d89372"/><circle cx="37" cy="80" r="2" fill="#294e54"/><path d="M16 110h98m-66-8v8m42-8v8" fill="none"/>',
      'matrix':'<path d="M15 42h95v70H15Z" fill="#f5e5bc"/><path d="M9 42 30 22h66l20 20Z" fill="#749ca3"/><path d="M28 55h70v45H28Z" fill="#e8f1e3"/><path d="M28 70h70M28 85h70M45 55v45M63 55v45M81 55v45" fill="none"/><path d="M46 71h16v13H46ZM82 56h15v13H82Z" fill="#d19469"/>',
      'telescope':'<path d="M26 109h67M49 101l12-42 16 42M59 71l-17 24m19-25 22 18" fill="none"/><g transform="rotate(-28 65 44)"><path d="M27 30h69v26H27Z" fill="#dca774"/><path d="M89 26h13v34H89Z" fill="#719da7"/><path d="M14 34h13v18H14Z" fill="#f5e8be"/></g><path d="m22 9 2 6 6 2-6 2-2 6-2-6-6-2 6-2Z" fill="#d3b25d"/>',
      'research':'<path d="M20 47h87v65H20Z" fill="#f0dfb6"/><path d="M14 47h99L67 14Z" fill="#b68570"/><path d="M29 57h18v20H29ZM77 57h19v20H77Z" fill="#b8d6d5"/><path d="M57 63v20l-14 20q18 14 36 0L67 83V63m-15 0h20" fill="#f9f1d8"/><path d="M51 94h22l6 9q-17 12-36 0Z" fill="#82ac9c"/>',
      'bridge':'<path d="M7 91q56-61 112 0v17q-57-44-112 0Z" fill="#dac093"/><path d="M19 80v28m20-41v31m24-38v31m24-24v30m20-17v27M9 86q55-58 108 0" fill="none"/><path d="M18 119q14-9 28 0t28 0t28 0" fill="none" stroke="#619ea6"/><circle cx="40" cy="24" r="17" fill="#b4d4c3"/><circle cx="64" cy="24" r="17" fill="#e8bd87"/><circle cx="87" cy="24" r="17" fill="#99bfca"/>',
      'volcano':'<path d="M8 112 47 43h26l45 69Z" fill="#c19c80"/><path d="m33 68 14-25h26l18 28-20-7-11 12-12-12Z" fill="#f0d5ae"/><path d="m57 54 9 15 8 25" fill="none" stroke="#cc7157" stroke-width="6"/><path d="M56 37q-18-16-2-21 8-14 20-3 20-2 17 13" fill="#f8efd9"/><path d="M18 101h21m49 6h19" fill="none"/>',
      'books':'<path d="M18 47h91v64H18Z" fill="#f3dfb5"/><path d="m10 47 55-29 52 29Z" fill="#83a178"/><path d="M28 59h29v37H28ZM70 59h29v37H70Z" fill="#fff7df"/><path d="M36 61v32m9-32v32m33-32v32m11-32v32" fill="none" stroke="#a97658" stroke-width="6"/><path d="M54 89h18v22H54Z" fill="#648e8b"/><path d="m36 17 27-5 27 5v13l-27-6-27 6Z" fill="#fffae9"/>',
      'rank':'<path d="M17 60h92v51H17Z" fill="#e8dab4"/><path d="M27 39h72v24H27Z" fill="#b8d0b6"/><path d="M39 21h47v19H39Z" fill="#c3d9de"/><path d="M24 75h9v25h-9ZM43 66h9v34h-9ZM62 80h9v20h-9ZM81 88h9v12h-9Z" fill="#cb8f6e"/><path d="m105 38 10 5-10 5M8 112h111" fill="none"/>',
      'waves':'<path d="M16 45h95v65H16Z" fill="#e9dfbd"/><path d="m9 45 54-28 56 28Z" fill="#789c94"/><path d="M28 59h70v40H28Z" fill="#fff8e4"/><path d="M30 88q14-45 28-12t38-4" fill="none" stroke="#c88463"/><path d="M29 70q20 35 39 0t27 13" fill="none" stroke="#6297a0"/><path d="M8 113h110" fill="none"/>',
      'clock':'<path d="M35 111V43h54v68Z" fill="#edd6a6"/><path d="M29 44 61 10l34 34Z" fill="#7a9d9c"/><circle cx="62" cy="59" r="19" fill="#fff9e7"/><path d="M62 45v14l11 8M53 92h18v19H53ZM26 113h72" fill="none"/><circle cx="62" cy="59" r="2" fill="#355d63"/>',
      'explorer':'<path d="M13 68 45 26l32 42v42H13Z" fill="#e8d4a3"/><path d="m45 26 45 9 25 75H77V68Z" fill="#85a490"/><path d="M26 110V72h37v38Z" fill="#476f73"/><path d="M40 72v38M20 59h45" fill="none"/><path d="m76 19 18-7 17 7v24l-17-5-18 5Z" fill="#fff2d6"/><path d="M94 13v25m-11-14 6-3m11 2 5 4" fill="none"/>'
    }
    defs=''.join(f'<symbol id="building-{k}" viewBox="0 0 125 125"><g stroke="#385d60" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">{v}</g></symbol>' for k,v in symbols.items())
    (ROOT/'assets/symbols.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" class="symbol-sheet" aria-hidden="true"><defs>'+defs+'</defs></svg>')
    land=[
      ('M55 243Q75 180 174 176L252 125Q327 106 385 149L478 181Q535 222 525 282L486 331Q529 377 487 465Q444 502 371 472L290 450Q214 472 171 435L94 399Q33 348 55 243Z','#a8c799'),
      ('M99 587Q152 511 235 530L313 559Q387 574 461 634L509 725Q521 792 442 833Q367 865 322 819L255 770Q170 786 102 725Q71 660 99 587Z','#acd0ad'),
      ('M575 283Q609 236 680 253L749 276Q815 225 877 261L930 312Q963 356 917 406L891 467Q905 541 838 600Q772 637 727 596L682 521Q617 511 575 449Q542 366 575 283Z','#c0d2a1'),
      ('M955 112Q1011 64 1085 90L1164 71Q1250 78 1334 125L1390 193Q1414 258 1362 295L1288 310Q1271 385 1188 407Q1130 414 1084 367L1021 316Q948 300 941 232Z','#b8c79e'),
      ('M1258 457Q1312 408 1383 451L1450 474Q1509 485 1541 553L1578 645Q1593 711 1532 741Q1477 771 1431 710L1390 661Q1307 664 1279 597Q1221 527 1258 457Z','#bed2a0'),
      ('M656 776Q691 713 775 725L845 742Q870 788 921 791Q1004 782 1044 838L1076 912Q1070 974 1000 991L931 1002Q875 987 845 943L800 914Q739 953 675 902Q629 864 656 776Z','#a5cbb4'),
      ('M1165 824Q1220 772 1302 794L1377 811Q1465 799 1510 862L1532 941Q1491 1003 1412 1006L1336 977Q1260 1010 1198 973L1149 913Q1122 864 1165 824Z','#afc294')
    ]
    coast=''
    for d,c in land:
        coast+=f'<path d="{d}" fill="none" stroke="#f6fbef" stroke-width="42" opacity=".56"/><path d="{d}" fill="#eed7a6" stroke="#a5bcab" stroke-width="2"/><path d="{d}" fill="{c}" stroke="#7f9f82" stroke-width="2" transform="translate(8 8) scale(.985)"/>'
    rng=random.Random(19); waves=''
    for i in range(100):
        x=rng.randint(10,1570);y=rng.randint(40,1020)
        waves+=f'<path d="M{x} {y}q6-4 12 0t12 0" stroke="#82b7c0" stroke-width="1.4" fill="none" opacity=".38"/>'
    tree='<g stroke="#5f846e" stroke-width="1.4"><path d="M0 6v14"/><path d="m-11 8 11-24L11 8Z" fill="#789f79"/><path d="m-8 1 8-19L8 1Z" fill="#92b28b"/></g>'
    trees=''
    for x,y,n in [(97,240,4),(244,332,4),(382,474,3),(105,671,3),(338,627,3),(489,726,2),(592,389,3),(730,280,2),(855,571,3),(958,237,2),(1080,120,3),(1373,236,3),(1290,566,2),(1522,625,2),(702,881,4),(873,912,3),(1231,957,3),(1439,878,5)]:
        for i in range(n):trees+=f'<g transform="translate({x+i*21} {y+rng.randint(-10,10)})">{tree}</g>'
    hills=''
    for x,y in [(353,338),(156,558),(795,464),(1089,269),(1218,266),(849,841),(1405,940)]:
        hills+=f'<path d="m{x-24} {y+15} 26-43 28 43Z" fill="#96ad8e" stroke="#7f987d" stroke-width="1.6"/><path d="m{x-4} {y-16} 6-12 8 13-8-3Z" fill="#e8e9cb"/>'
    labels=''
    for x,y,t in [(176,143,'准备大陆'),(155,512,'质控海湾'),(651,226,'表达工坊岛'),(1050,57,'差异火山岛'),(1374,421,'已有注释航道'),(704,705,'时间群岛'),(1280,767,'自建注释航道')]:
        labels+=f'<text x="{x}" y="{y}" fill="#426d71" font-family="STKaiti,KaiTi,Noto Serif CJK SC,serif" font-size="22" font-weight="600" letter-spacing="3">{t}</text>'
    routes='''<g fill="none" stroke="#719fa4" stroke-width="2.4" stroke-dasharray="5 10" opacity=".65">
      <path d="M443 457Q309 447 204 576"/><path d="M443 712Q553 622 611 376"/>
      <path d="M865 297Q907 177 1001 176"/><path d="M1164 379Q1206 475 1316 510"/>
      <path d="M794 592Q697 655 744 780"/><path d="M1322 650Q1250 706 1302 841"/>
      </g>'''
    extras='''<g transform="translate(91 900)" stroke="#5f9098" fill="none" stroke-width="1.7"><circle r="43"/><circle r="36" stroke-dasharray="2 7"/><path d="M0-62V62M-62 0H62"/><path d="M0-49 10 0 0 49-10 0Z" fill="#eff6e7"/><path d="M0-49 10 0H0Z" fill="#608b91"/><text y="-70" text-anchor="middle" stroke="none" fill="#4b7a82" font-size="13">N</text></g>
      <g transform="translate(1060 648) rotate(-15)" stroke="#769ca1" stroke-width="2" fill="#f1ead2"><path d="M-33 6h65L19 24h-39Z"/><path d="M0 5v-55l26 44H3"/><path d="m-5-37-20 27h20Z"/></g>
      <g transform="translate(539 914)" stroke="#6899a0" stroke-width="2" fill="none"><path d="M-48 0q30-44 72 0 19 6 30-13-3 30-30 23Q-8 36-48 0Z" fill="#8fbec3"/><path d="m-21-15-9-19m11 17 6-19"/><circle cx="-35" cy="0" r="2" fill="#3c717b"/></g>
      <text x="541" y="1020" fill="#5f9098" font-size="15" letter-spacing="6">RNA 探 索 海 域</text>'''
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1040"><defs><pattern id="grain" width="8" height="8" patternUnits="userSpaceOnUse"><circle cx="1" cy="3" r=".5" fill="#6f9ea5" opacity=".14"/></pattern></defs><rect width="1600" height="1040" fill="#d7edf0"/><rect width="1600" height="1040" fill="url(#grain)"/>{waves}{coast}{routes}{hills}{trees}{labels}{extras}</svg>'
    (ROOT/'assets/world.svg').write_text(svg)

if __name__=='__main__':make_art()
