"""Original SVG scenery and semantic lesson links for the independent Linux atlas."""
from html import escape


ZONES = (
    ('camp', '出发营地', '认识系统，准备出发', 'camp'),
    ('files', '文件林舍', '给每份记录安一个家', 'cabin'),
    ('clues', '线索瞭望台', '从文字里找到线索', 'tower'),
    ('stream', '溪边工坊', '让小工具接力工作', 'mill'),
    ('watch', '运行值守站', '看懂程序怎样运行', 'station'),
    ('scripts', '脚本工作室', '把重复交给脚本', 'studio'),
)


def tree(x, y, scale=1, shade=0, sway=False):
    colors = [('#719779', '#96b698'), ('#527e69', '#79a088'), ('#9bb58a', '#bfd0a4')]
    dark, light = colors[shade % len(colors)]
    motion = ' class="tree-crown atlas-moving"' if sway else ''
    return (f'<g transform="translate({x} {y}) scale({scale})"><ellipse cx="0" cy="8" rx="23" ry="8" fill="#476854" opacity=".12"/>'
            '<path d="M0 5V-56m0 30-13-14m13 4 12-17" fill="none" stroke="#718671" stroke-width="4" stroke-linecap="round"/>'
            f'<g{motion}><path d="M0-97C-11-80-27-58-29-31Q-13-18 0-21Q20-20 29-34C23-58 11-82 0-97Z" fill="{dark}"/>'
            f'<path d="M0-97C-10-76-15-52-15-32L0-23Z" fill="{light}"/>'
            '<path d="M0-81v46m0-20-10-9m10 0 9-11" fill="none" stroke="#eef4df" stroke-width="1.3" opacity=".4"/></g></g>')


def shrub(x, y, scale=1):
    return f'<g transform="translate({x} {y}) scale({scale})"><ellipse rx="21" ry="6" fill="#7c9a79" opacity=".14"/><path d="M-23 0Q-27-19-12-17Q-6-35 8-20Q27-22 26-2Z" fill="#aac09b"/><path d="M-9-4 0-15 9-6" fill="none" stroke="#e4ecd3" stroke-width="2"/></g>'


def flowers(x, y):
    return f'<g transform="translate({x} {y})" fill="#d9bb79"><path d="M0 3v-15m14 19V-6m-26 13V-4" stroke="#8da98d" stroke-width="2"/><circle cy="-13" r="4"/><circle cx="14" cy="-7" r="3"/><circle cx="-12" cy="-5" r="3"/></g>'


def rock(x, y, scale=1):
    return f'<g transform="translate({x} {y}) scale({scale})"><path d="M-15 1-8-12 8-15 19-3 13 7-8 9Z" fill="#bdc8b5"/><path d="m-15 1 15-6 19 2M0-5 8-15" fill="none" stroke="#d9dfd1" stroke-width="2"/></g>'


def cloud(x, y, scale=1, slow=False):
    return f'<g transform="translate({x} {y}) scale({scale})"><g class="cloud-drift atlas-moving {"cloud-slow" if slow else ""}"><path d="M-65 8Q-82-9-57-17Q-55-43-26-35Q-1-65 23-33Q54-37 57-14Q87-5 68 9Z" fill="#fffdf0" opacity=".78"/><path d="M-42 16H40" stroke="#b3c8b5" opacity=".3" stroke-width="3" stroke-linecap="round"/></g></g>'


def flock(x, y, scale=1):
    return f'''<g transform="translate({x} {y}) scale({scale})"><g class="bird-flight atlas-moving">
      <g class="bird-wing atlas-moving"><path d="M-18 2Q-7-9 0 1Q9-9 20 2"/></g>
      <g transform="translate(43 17) scale(.72)"><g class="bird-wing atlas-moving"><path d="M-18 2Q-7-9 0 1Q9-9 20 2"/></g></g>
      <g transform="translate(-38 26) scale(.57)"><g class="bird-wing atlas-moving"><path d="M-18 2Q-7-9 0 1Q9-9 20 2"/></g></g>
    </g></g>'''


def terminal(x, y, width=51, height=36):
    return (f'<g transform="translate({x} {y})"><rect width="{width}" height="{height}" rx="4" fill="#254f50" stroke="#1f4849" stroke-width="2"/>'
            '<path d="m9 12 6 5-6 5m13 0h10" fill="none" stroke="#f2e6b7" stroke-width="2.5" stroke-linecap="round"/>'
            f'<path d="M{width/2} {height}v8m-12 1h24" stroke="#6e8274" stroke-width="3"/></g>')


def window(x, y, w=24, h=29):
    return f'<g transform="translate({x} {y})"><rect width="{w}" height="{h}" rx="2" fill="#e9dab1" stroke="#496d63" stroke-width="3"/><path d="M{w/2} 0v{h}M0 {h/2}h{w}" stroke="#7f9983" stroke-width="2"/><path d="m4 4 7 0-7 9Z" fill="#fff8da" opacity=".7"/></g>'


def roof(x=52, y=42, width=166, height=43, color='#467669'):
    return (f'<path d="M{x-10} {y+height} {x+width/2} {y} {x+width+12} {y+height+8} {x+width+6} {y+height+17} {x+width/2} {y+13} {x-10} {y+height+10}Z" fill="{color}" stroke="#3d665b" stroke-width="2"/>'
            f'<path d="M{x+width/2} {y+13} {x+width/2} {y}" stroke="#a7bca0" stroke-width="2"/>')


def cabin(kind):
    wall = '#dbcd9f' if kind != 'studio' else '#d1dec1'
    s = '<ellipse cx="151" cy="167" rx="115" ry="14" fill="#4c755b" opacity=".14"/>'
    s += f'<path d="M65 78h146v81l-69 14-77-16Z" fill="{wall}" stroke="#718871" stroke-width="2"/>'
    s += '<path d="m142 84 69-6v81l-69 14Z" fill="#90ac90" opacity=".45"/>'
    for y in range(95, 160, 13):
        s += f'<path d="M67 {y}h74m4 2 64-10" stroke="#aeb794" opacity=".65"/>'
    s += '<path d="M119 111h30v57l-30-3Z" fill="#456c5e"/><circle cx="142" cy="143" r="2" fill="#e9c882"/>'
    s += window(80, 105, 25, 30) + window(168, 100, 26, 29)
    s += '<path d="m114 167 35 3 5 8-42-3Z" fill="#b0b8a0"/>'
    s += roof()
    if kind == 'cabin':
        s += '<path d="M30 123h45v43H30Z" fill="#a9895a" stroke="#6c7c5d" stroke-width="2"/>'
        for y in (127, 139, 151):
            s += f'<path d="M34 {y}h36v9H34Z" fill="#dbc78e"/><path d="M48 {y+5}h8" stroke="#937a51" stroke-width="2"/>'
        s += '<path d="M227 165v-48m-15 2h42v20h-42Z" fill="#e3d3a5" stroke="#79846b" stroke-width="3"/><path d="m222 127 20 0m-4-4 5 4-5 4" stroke="#527764" stroke-width="2" fill="none"/>'
    if kind == 'studio':
        s += '<path d="M195 55V18h7v41" stroke="#657e6c" stroke-width="3" fill="none"/><path d="M202 19h26l-8 10 8 8h-26Z" fill="#cc9360"/>'
        s += terminal(28, 116, 49, 34)
        s += '<path d="M23 160h63m-56 0v12m49-12v12" stroke="#8c795a" stroke-width="4"/>'
        s += '<g transform="translate(226 113)"><path d="M0 0h29v41H0Z" fill="#fcf7df" stroke="#a1aa86" stroke-width="2"/><path d="M6 9h18m-18 7h12m-12 7h18m-18 7h15" stroke="#8eaa93" stroke-width="2"/></g>'
    return s


def landmark(kind):
    s = ''
    if kind == 'camp':
        s = '<ellipse cx="147" cy="163" rx="118" ry="14" fill="#4c755b" opacity=".13"/><path d="M32 152 91 45 151 155Z" fill="#dfc794" stroke="#968667" stroke-width="2"/><path d="M91 45 192 64 231 156 151 155Z" fill="#92ae91" stroke="#688c74" stroke-width="2"/><path d="M63 153 93 91 119 154Z" fill="#436b5e"/><path d="M91 45v44m0-44-69 111m170-92 48 91" stroke="#a8ad83" stroke-width="2"/><path d="M19 159v-11m222 12v-13" stroke="#7d8970" stroke-width="3"/>'
        s += terminal(161, 113, 53, 36)
        s += '<path d="M150 158h78m-66 0v14m54-14v14" stroke="#9f8661" stroke-width="5"/>'
        s += '<path d="M44 93V42m-14 4h39v20H30Z" fill="#e7d8af" stroke="#8a9578" stroke-width="3"/><path d="m41 56 18 0m-5-4 5 4-5 4" fill="none" stroke="#577d69" stroke-width="2"/>'
    elif kind in ('cabin', 'studio'):
        s = cabin(kind)
    elif kind == 'tower':
        s = '<ellipse cx="152" cy="167" rx="99" ry="13" fill="#4c755b" opacity=".14"/><path d="M99 87 87 166m93-81 18 80m-85-78 9 80m44-80-7 81" stroke="#8a8e6b" stroke-width="8"/><path d="m96 101 92 49m-93 0 88-49M88 168h111" stroke="#687f65" stroke-width="4"/><path d="M88 72h104v36H88Z" fill="#e2d4ac" stroke="#73886e" stroke-width="3"/><path d="M91 88h100M105 73v32m22-32v32m23-32v32m22-32v32" stroke="#92a182" stroke-width="3"/>'
        s += roof(81, 20, 118, 43)
        s += '<path d="M145 66V49" stroke="#476e60" stroke-width="3"/><path d="m129 50 30-13 6 12-30 13Z" fill="#547f6f" stroke="#3b6259" stroke-width="2"/><path d="m160 36 8 16" stroke="#d7c791" stroke-width="4"/><path d="M130 115v53m20-53v53m-20-42h20m-20 13h20m-20 13h20" stroke="#adad85" stroke-width="3"/>'
        s += '<path d="M44 145h36v22H44Z" fill="#c5d2a5"/><path d="M49 142v-22h25v22" fill="#fbf4d8" stroke="#9aaa86" stroke-width="2"/><path d="M54 127h15m-15 6h12" stroke="#9aac90" stroke-width="2"/>'
    elif kind == 'mill':
        s = cabin('mill')
        s += '<path d="M11 164q26-14 58-7t52 7q37 9 68 3" stroke="#a5cbd0" stroke-width="17" fill="none"/><path d="M13 166q39-12 75 2m25 2 26 3" stroke="#eff8ee" stroke-width="2" fill="none"/>'
        s += '<g transform="translate(67 130)">'
        s += '<g class="waterwheel atlas-moving"><circle r="34" fill="#b39869" stroke="#6c7c61" stroke-width="4"/><circle r="25" fill="#dfd2a8" stroke="#8c9069" stroke-width="3"/>'
        for a in range(0, 360, 45):
            s += f'<path d="M0-31V31" transform="rotate({a})" stroke="#7d835f" stroke-width="3"/>'
        s += '<circle r="7" fill="#6e8265"/></g></g>'
    elif kind == 'station':
        s = '<ellipse cx="150" cy="165" rx="112" ry="14" fill="#4c755b" opacity=".14"/><path d="M116 61h90v100l-40 13-50-12Z" fill="#bdcbaa" stroke="#718b72" stroke-width="2"/><path d="M166 64h40v97l-40 13Z" fill="#88a58c"/><path d="M109 60h104l-10-18h-84Z" fill="#467569" stroke="#426959" stroke-width="2"/>'
        s += window(129, 80, 25, 27) + window(174, 81, 21, 26)
        s += '<path d="M135 125h26v45l-26-5Z" fill="#4a7562"/><path d="M153 41V10m0 8 23 11m-23-11-15 9" stroke="#687f6c" stroke-width="3"/><circle cx="153" cy="9" r="4" fill="#ddb679"/>'
        s += '<path d="M37 165v-50h16v50m33 0v-50h16v50" fill="#d5c699" stroke="#7e9476" stroke-width="2"/><path d="M49 124h41v26H49Z" fill="#97b08b" stroke="#6c896d" stroke-width="2"/><path d="M60 125v24m15-24v24" stroke="#e7e6c5" stroke-width="3"/>'
        s += '<circle cx="74" cy="98" r="13" fill="#ecdfba" stroke="#6f8c70" stroke-width="2"/><path d="M70 98v-4a4 4 0 0 1 8 0v4m-10 0h12v9h-12Z" stroke="#54745f" stroke-width="2" fill="none"/>'
    return f'<svg class="landmark" viewBox="0 0 290 190" aria-hidden="true" focusable="false">{s}</svg>'


def terrain(portrait=False):
    width, height = (600, 1900) if portrait else (1440, 1060)
    prefix = 'portrait' if portrait else 'landscape'
    s = f'<svg class="atlas-scenery atlas-{prefix}" viewBox="0 0 {width} {height}" preserveAspectRatio="none" aria-hidden="true" focusable="false">'
    s += f'<defs><pattern id="{prefix}-grain" width="17" height="17" patternUnits="userSpaceOnUse"><circle cx="3" cy="4" r=".7" fill="#809775" opacity=".16"/><path d="m10 12 2-2" stroke="#809775" opacity=".12"/></pattern></defs>'
    s += f'<rect width="{width}" height="{height}" fill="#e6efdf"/><rect width="{width}" height="{height}" fill="url(#{prefix}-grain)"/>'
    if portrait:
        s += '<path d="M0 30Q190 50 190 370T115 930 220 1510L160 1900H0Z" fill="#d3e2c9"/><path d="M600 90Q427 360 507 690T470 1220 530 1730L480 1900H600Z" fill="#d5e4d0"/>'
        river = 'M625 905C445 955 554 1032 408 1110S533 1250 613 1390'
        routes = [('camp','M111 100Q46 189 110 315'),('files','M110 315Q171 490 99 615'),('clues','M99 615Q45 770 108 915'),('stream','M108 915Q174 1080 104 1215'),('watch','M104 1215Q34 1390 107 1515'),('scripts','M107 1515Q171 1680 109 1810')]
        trees = [(35,130,.7,1),(553,175,.8,0),(568,420,.6,1),(31,454,.7,2),(44,705,.8,0),(568,750,.9,1),(31,975,.65,1),(561,1060,.9,2),(46,1260,.8,0),(558,1420,.75,0),(32,1580,.7,1),(552,1720,.9,1),(42,1840,.8,2)]
        clearings = [(130,185,130,90),(122,478,130,93),(125,775,126,94),(132,1080,125,84),(128,1380,126,80),(127,1690,128,91)]
    else:
        s += '<path d="M0 29Q195-10 354 68T730 41 1080 88 1440 36V210Q1250 152 1148 191T753 144 355 195 0 197Z" fill="#d7e5cd"/><path d="M0 585Q145 507 281 546T704 530 1048 557 1440 500V650Q1249 650 1078 621T704 631 358 610 0 704Z" fill="#cfdfc7"/><path d="M0 948Q167 881 313 953T664 925 1003 962 1440 905V1060H0Z" fill="#d5e3cd"/>'
        river = 'M1461 362C1310 350 1340 469 1214 485S986 431 895 504 1001 645 1125 650 1385 584 1469 704'
        routes = [('camp','M102 247Q169 143 286 222'),('files','M286 222Q487 78 711 171'),('clues','M711 171Q968 133 1139 222'),('stream','M1139 222C1360 230 1390 530 1151 669'),('watch','M1151 669Q921 748 724 724'),('scripts','M724 724Q489 640 287 674')]
        trees = [(67,148,.85,1),(112,116,.68,0),(35,219,.65,2),(413,109,.62,0),(466,77,.75,1),(508,111,.57,2),(904,85,.82,0),(952,103,.6,1),(1311,147,.9,1),(1360,186,.65,0),(1412,272,.76,2),(48,544,.9,0),(99,586,.6,1),(161,528,.72,2),(425,562,.72,1),(467,517,.82,0),(521,568,.6,2),(714,568,.68,0),(770,522,.78,1),(817,574,.61,2),(1349,639,.75,0),(1405,705,.9,1),(74,871,.7,0),(111,951,.85,1),(466,960,.65,0),(540,1010,.92,1),(623,964,.7,2),(912,957,.8,0),(978,1000,.6,2),(1364,916,.91,1),(1303,967,.72,0)]
        clearings = [(285,274,177,140),(711,218,170,128),(1139,273,181,143),(1151,724,180,137),(724,781,178,142),(287,728,183,146)]
    for x,y,rx,ry in clearings:
        s += f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" fill="#f0f2dd" opacity=".68"/>'
    s += f'<path d="{river}" fill="none" stroke="#b3cba5" stroke-width="72"/><path d="{river}" fill="none" stroke="#a6cbd0" stroke-width="56"/><path d="{river}" fill="none" stroke="#cae2df" stroke-width="34"/><path class="water-current atlas-moving" d="{river}" fill="none" stroke="#f4f7df" stroke-width="2" stroke-dasharray="15 29 37 64" opacity=".75"/>'
    for zone,route in routes:
        s += f'<g class="trail-section" data-route-zone="{zone}"><path d="{route}" fill="none" stroke="#c8bc93" stroke-width="24" stroke-linecap="round" opacity=".5"/><path d="{route}" fill="none" stroke="#ecddaf" stroke-width="18" stroke-linecap="round"/><path class="trail-highlight" d="{route}" fill="none" stroke="#ac9160" stroke-width="2.5" stroke-dasharray="2 10" stroke-linecap="round"/></g>'
    if not portrait:
        s += '<g transform="translate(1268 463) rotate(-26)"><path d="M-42-25h84v49h-84Z" fill="#bba77b" stroke="#798365" stroke-width="3"/>'
        for x in range(-35,42,12):s+=f'<path d="M{x}-25v49" stroke="#e6d2a6" stroke-width="2"/>'
        s += '<path d="M-48-31h96m-96 61h96" stroke="#7f8c6e" stroke-width="5"/></g>'
        s += '<g transform="translate(796 75)"><path d="M-39 0h77l-7 33H-33Z" fill="#b7c4a0" opacity=".55"/><path d="M-27 1q25-35 53 0" fill="#eef2df" stroke="#8baa89" stroke-width="2"/><path d="M0-22v23m-27 0h53" stroke="#8baa89" stroke-width="2"/></g>'
        s += flowers(606,551)+flowers(875,933)+flowers(178,188)+rock(1265,801)+rock(1318,820,.6)+rock(859,562,.7)
        s += '<g transform="translate(173 963)" stroke="#78957b" fill="none"><circle r="23" opacity=".45"/><path d="M0-33 9 12 0 4-9 12Z" fill="#78957b" stroke="none"/><path d="M-32 0h64M0 16v17" opacity=".55"/></g>'
        s += cloud(571,47,.8)+cloud(1066,526,.62,True)+flock(1120,82,.85)
    else:
        s += flowers(520,340)+flowers(40,1170)+flowers(523,1600)+rock(533,983,.7)+rock(63,1768,.7)
        s += cloud(400,67,.65)+cloud(386,1203,.57,True)+flock(346,70,.75)
    for i,(x,y,scale,shade) in enumerate(trees):
        s += tree(x,y,scale,shade,sway=i in (0,8,16))
        if i%4==0:s+=shrub(x+25,y+16,.6)
    return s+'</svg>'


def render_atlas(lessons):
    stages = list(dict.fromkeys(lesson['stage'] for lesson in lessons))
    assert len(stages) == len(ZONES)
    s = '<div id="atlas-map" class="atlas-map" role="region" aria-label="自然观察站学习地图" data-motion="paused">'
    s += terrain() + terrain(True)
    s += '<p class="map-corner-note"><span>FIELD NOTES / 01</span>一周的观察，从这里整理。</p>'
    for index, (ident, title, subtitle, kind) in enumerate(ZONES):
        selected = [lesson for lesson in lessons if lesson['stage'] == stages[index]]
        assert len(selected) == 3
        ids = ','.join(lesson['id'] for lesson in selected)
        s += f'<section class="atlas-zone zone-{ident}" data-zone="{ident}" data-zone-lessons="{ids}" aria-labelledby="zone-{ident}-title"><div class="zone-art">{landmark(kind)}</div><div class="zone-info">'
        s += f'<p class="zone-meta"><span>{selected[0]["id"]}—{selected[-1]["id"]}</span><span class="zone-progress">0 / 3 已读</span></p><h3 id="zone-{ident}-title">{title}</h3><p class="zone-subtitle">{subtitle}</p><ol class="zone-lessons">'
        for lesson in selected:
            ident_l = lesson['id']
            first = ident_l == lessons[0]['id']
            s += (f'<li><a class="map-lesson{" is-next" if first else ""}" data-course-lesson="{ident_l}" href="lessons/{ident_l}.html">'
                  f'<span class="map-lesson-number">{ident_l}</span><span class="map-lesson-title">{escape(lesson["title"])}</span>'
                  f'<span class="map-lesson-status" aria-hidden="true">{"→" if first else "↗"}</span><span class="map-state sr-only">{"建议下一站" if first else "未读"}</span></a></li>')
        s += '</ol></div></section>'
    s += '</div>'
    return s
