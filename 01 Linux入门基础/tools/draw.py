"""Original, editable SVG illustrations. No network or raster dependencies."""
from pathlib import Path
from html import escape as E

ROOT = Path(__file__).resolve().parents[1]
INK = '#163d43'
TEAL = '#28766f'
MOSS = '#dcebdc'
SKY = '#dceef0'
SAND = '#f5e6c9'
PAPER = '#f5f8f5'


def text(x, y, value, size=20, fill=INK, anchor='start', weight='400'):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" font-weight="{weight}">{E(str(value))}</text>'


def rect(x, y, w, h, fill=PAPER, radius=14, stroke='#a5c2bd'):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'


def arrow(x1, y1, x2, y2, color=TEAL):
    return f'<path d="M{x1} {y1} L{x2} {y2}" fill="none" stroke="{color}" stroke-width="3" marker-end="url(#arrow)"/>'


def folder(x, y, label, color=SAND, w=160):
    return (f'<path d="M{x} {y+17}v-8q0-9 9-9h{w*.4}l13 16h{w*.45}q12 0 12 12v62q0 12-12 12H{x+12}q-12 0-12-12Z" '
            f'fill="{color}" stroke="#76998e" stroke-width="2"/>' + text(x+15,y+62,label,18,weight='600'))


def sheet(x,y,lines,w=168):
    s=rect(x,y,w,120,'#ffffff',5)
    for i,line in enumerate(lines):
        s+=text(x+14,y+28+i*25,line,15)
    return s


def terminal(x,y,w,lines):
    s=rect(x,y,w,42+len(lines)*30,'#163d43',12,INK)
    for i,color in enumerate(['#e7b97b','#86a98a','#86b4ba']):
        s+=f'<circle cx="{x+20+i*18}" cy="{y+20}" r="4" fill="{color}"/>'
    for i,line in enumerate(lines):
        s+=text(x+18,y+54+i*30,line,17,'#f3f8f3')
    return s


FIGURES = {
    'system': ('从窗口到系统', '终端展示文字，Shell 解释命令，工具通过系统使用资源。箭头表示这次操作的层次，不是完整操作系统结构。'),
    'command': ('把一条命令拆开看', '命令名告诉 Shell 做什么；选项改变行为；路径等参数指定操作对象。空格分隔各项，引号可以保护一项内部的空格。'),
    'tree': ('一棵目录树，一枚位置图钉', 'linux-lab 是练习根目录。notes、logs、tables、tools 和 results 都在它下面；箭头标出从 notes 经父目录进入 tables 的路线。'),
    'files': ('复制与移动，留下的东西不同', '复制在目标处产生副本，原文件仍在；移动或改名改变原来的位置或名称。操作前看清已有目标是否会被覆盖。'),
    'text': ('从不同的窗口看同一份文本', 'head 看开头，tail 看末尾，less 用于翻阅。wc -l 统计换行符；本例每行都有换行，得到 4。'),
    'streams': ('结果和诊断走不同通道', '标准输出编号为 1，标准错误为 2。重定向可以分别保存；普通管道默认接走标准输出。箭头表示数据流向。'),
    'pipeline': ('小工具怎样合作', '相同名称先排在一起，uniq -c 才能合并相邻行并计数。这是记录条数，不能直接当作鸟的数量。'),
    'table': ('先知道一行与一列代表什么', '每行是一次记录，species 是物种，count 是这一次的观测数量。高亮列帮助你对照 cut 的字段编号。'),
    'archive': ('把文件装箱，再压缩', 'tar 保存文件与目录层次，gzip 压缩归档。查看清单后在新目录解开，才能看清有没有多一层目录。'),
    'permissions': ('一份文件，三组基本权限', '从左到右是所有者、所属组和其他人。本图展示普通文件的 640：所有者读写、组只读、其他人无权限；目录含义另作说明。'),
    'pathenv': ('沿 PATH 寻找外部程序', 'Shell 按搜索顺序查找外部命令；前面的目录可能遮住后面的同名程序。示意不包含别名、函数和内建命令等其他处理。'),
    'process': ('同一个程序，可以有不同的运行实例', '程序文件好比保存的步骤，进程是正在运行的一次。PID 用于识别进程，图中的编号仅为示意。'),
    'loop': ('每次拿一份，做相同的检查', 'for 依次给变量赋一个路径；if 先检查，再执行动作。下一次循环换一个路径，动作仍然相同。'),
}


def art(key):
    if key == 'system':
        return (terminal(35,70,250,['$ ls notes','morning.txt','evening.txt'])+arrow(300,145,350,145)+
                rect(365,70,170,160,MOSS)+text(450,135,'Bash',30,anchor='middle',weight='700')+text(450,177,'解释这条命令',18,anchor='middle')+
                arrow(548,145,597,145)+rect(612,70,215,160,SKY)+text(720,128,'工具与内核',26,anchor='middle',weight='600')+
                text(720,174,'读取目录信息',18,anchor='middle')+text(162,285,'终端：看见与输入',20,anchor='middle')+text(450,285,'Shell：解释与组织',20,anchor='middle')+text(720,285,'系统：使用资源',20,anchor='middle'))
    if key == 'command':
        s=terminal(75,50,700,['$ ls -l notes'])
        for x,label,sub,color in [(120,'ls','命令名称',MOSS),(350,'-l','详细列表选项',SAND),(610,'notes','目标目录参数',SKY)]:
            s+=rect(x,190,150,90,color)+text(x+75,229,label,26,anchor='middle',weight='700')+text(x+75,259,sub,16,anchor='middle')
        return s+text(425,325,'只输入命令；$ 是示意提示符。',19,anchor='middle')
    if key == 'tree':
        s=folder(333,20,'linux-lab',MOSS,175)
        for x,name in [(35,'notes'),(300,'logs'),(570,'tables')]:
            s+=arrow(425,125,x+85,178)+folder(x,190,name)
        s+=text(117,335,'morning.txt',17,anchor='middle')+text(390,335,'day-01.log',17,anchor='middle')+text(657,335,'observations.tsv',17,anchor='middle')
        s+=text(730,57,'同级目录还有',15)+text(730,83,'tools / results',15)
        s+='<path d="M155 188Q255 105 360 110M490 110Q620 115 656 179" fill="none" stroke="#ad7143" stroke-width="4" stroke-dasharray="7 6" marker-end="url(#arrow)"/>'
        return s+text(193,144,'.. 返回父目录',16,'#8b552f')+text(574,144,'进入 tables',16,'#8b552f')
    if key == 'files':
        return (sheet(30,65,['原件','morning.txt'])+arrow(215,120,320,120)+sheet(345,65,['副本','morning-copy.txt'])+
                text(267,92,'cp',22,anchor='middle',weight='600')+text(117,238,'原件还在',22,anchor='middle')+
                arrow(534,120,640,120)+folder(662,70,'backup')+text(587,92,'mv',22,anchor='middle',weight='600')+
                text(670,260,'副本换了位置',20)+text(425,323,'先认清源路径，再认清目标路径。',20,anchor='middle'))
    if key == 'text':
        s=rect(75,40,460,260,'#fff')
        for i,line in enumerate(['08:00 INFO start','08:05 INFO lake ready','08:10 WARN battery low','08:20 INFO saved']):
            s+=rect(88,61+i*54,433,40,SKY if i<2 else (SAND if i==3 else PAPER),4,'none')+text(105,87+i*54,f'{i+1}  {line}',19)
        return s+text(585,101,'head -n 2',23)+text(585,241,'tail -n 1',23)+text(585,299,'wc -l → 4',23)+text(95,335,'less：按自己的速度翻阅；q 退出。',18)
    if key == 'streams':
        return (rect(45,107,200,145,MOSS)+text(145,179,'正在运行的工具',21,anchor='middle',weight='600')+
                arrow(257,136,517,82)+arrow(257,224,517,271)+sheet(550,28,['正常结果','output.txt'],225)+sheet(550,217,['诊断信息','error.txt'],225)+
                text(330,75,'1 · stdout   >',20,TEAL)+text(323,280,'2 · stderr   2>',20,'#9a5d39'))
    if key == 'pipeline':
        return (sheet(30,80,['sparrow','magpie','sparrow','…'],195)+arrow(239,145,302,145)+sheet(320,80,['magpie','magpie','sparrow','…'],195)+
                arrow(529,145,592,145)+sheet(610,80,['2 magpie','4 sparrow'],195)+text(267,115,'sort',19,anchor='middle')+
                text(566,115,'uniq -c',18,anchor='middle')+text(425,287,'每一段都可以单独看，再接成管道。',21,anchor='middle')+text(425,322,'这里数的是记录，不是每次看到的鸟数。',18,anchor='middle'))
    if key == 'table':
        s=''
        for i,row in enumerate([['date','site','species','count'],['04-01','lake','sparrow','12'],['04-01','wood','magpie','3'],['04-02','lake','sparrow','8'],['04-02','wood','sparrow','5']]):
            for j,col in enumerate(row):
                s+=rect(50+j*185,55+i*48,185,48,MOSS if j==2 else (SKY if i==0 else '#fff'),0)+text(70+j*185,86+i*48,col,20)
        return s+text(512,33,'第 3 列',18,anchor='middle')+text(425,335,'一行是一条记录；列名说明每个值的含义。',20,anchor='middle')
    if key == 'archive':
        return (folder(35,104,'notes')+arrow(218,166,305,166)+rect(330,65,195,208,SAND,7)+text(428,124,'TAR',34,anchor='middle',weight='700')+
                text(428,166,'目录与文件',20,anchor='middle')+text(428,210,'完整装箱',18,anchor='middle')+arrow(540,166,624,166)+
                rect(650,102,160,135,MOSS)+text(730,155,'.tar.gz',25,anchor='middle',weight='600')+text(730,196,'gzip 压缩',18,anchor='middle')+
                text(425,329,'t 查看清单  ·  x 解压  ·  在新目录核对内容',19,anchor='middle'))
    if key == 'permissions':
        s=''
        for x,title,letters,num,color in [(35,'所有者','r  w  −','6',MOSS),(315,'所属组','r  −  −','4',SKY),(595,'其他人','−  −  −','0',SAND)]:
            s+=rect(x,52,225,220,color)+f'<circle cx="{x+113}" cy="98" r="19" fill="{TEAL}"/><path d="M{x+74} 145q0-33 39-33t39 33" fill="{TEAL}"/>'+text(x+113,181,title,22,anchor='middle')+text(x+113,222,letters,27,anchor='middle')+text(x+113,310,num,30,anchor='middle',weight='700')
        return s
    if key == 'pathenv':
        s=text(40,60,'输入一个外部命令名 → 按目录顺序查找',23,weight='600')
        for i,(name,note,color) in enumerate([('~/bin','个人工具',SAND),('/usr/local/bin','本机安装',MOSS),('/usr/bin','系统工具',SKY)]):
            x=35+i*282
            s+=folder(x,110,name,color,225)+text(x+110,255,note,19,anchor='middle')
            if i<2:s+=arrow(x+238,157,x+274,157)
        return s+text(425,323,'command -v 名称：先看当前环境会找到什么。',19,anchor='middle')
    if key == 'process':
        return (sheet(30,113,['程序文件','sleep'],180)+arrow(226,154,356,87)+arrow(226,187,356,267)+
                rect(380,32,398,114,MOSS)+text(408,74,'一次运行 · PID 1201',24,weight='600')+text(408,116,'等待 5 秒 → 正常结束',20)+
                rect(380,215,398,114,SKY)+text(408,257,'另一次运行 · PID 1202',24,weight='600')+text(408,299,'等待 15 秒 → 正常结束',20))
    if key == 'loop':
        return (sheet(32,85,['day-01.log','day-02.log'],190)+arrow(238,147,319,147)+rect(340,62,205,190,MOSS)+text(442,113,'record',27,anchor='middle',weight='600')+
                text(442,158,'检查是普通文件',18,anchor='middle')+text(442,208,'显示名字、数行',18,anchor='middle')+arrow(561,147,620,147)+sheet(640,85,['day-01.log: 4','day-02.log: 4'],185)+
                '<path d="M510 271Q423 350 325 271" stroke="#ad7143" stroke-width="3" fill="none" marker-end="url(#arrow)"/>'+text(425,344,'换下一个路径，再做一次',18,anchor='middle'))
    raise KeyError(key)


def svg(body,title,desc,w=850,h=370):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title desc"><title id="title">{E(title)}</title><desc id="desc">{E(desc)}</desc><defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0 0L6 3L0 6" fill="none" stroke="{TEAL}" stroke-width="1.5"/></marker></defs><g font-family="'Noto Sans SC','Microsoft YaHei',sans-serif">{body}</g></svg>'''


def hero():
    s='<path d="M0 320Q170 140 330 300T850 200V570H0Z" fill="#dcebdc"/><path d="M0 370Q280 275 460 355T850 300V570H0Z" fill="#c4ded3"/>'
    s+=rect(45,60,370,445,'#fff',18)+text(76,101,'观察站 · 文件柜',24,weight='600')
    for y,label,color in [(141,'notes / 观察笔记',SAND),(254,'logs / 设备日志',SKY),(367,'tables / 小小数据表',MOSS)]:
        s+=folder(79,y,label,color,278)
    s+=terminal(445,160,375,['$ pwd','/home/river/linux-lab','$ ls','notes  logs  tables','$ _'])
    s+=rect(424,417,410,20,'#b98f61',5,'#ad8051')+f'<path d="M455 438v68m348-68v68" stroke="#ad8051" stroke-width="14"/>'
    s+='<path d="M546 102q14-18 28 0q14-18 28 0M659 69q12-15 24 0q12-15 24 0" fill="none" stroke="#537d74" stroke-width="3"/>'
    s+=text(630,480,'一个文件，一条线索。',21,anchor='middle')
    return svg(s,'从观察站的文件柜走进 Linux','笔记、日志与表格放入不同目录，终端用文字操作同一批文件。',850,540)


def main():
    dest=ROOT/'assets/illustrations'
    dest.mkdir(parents=True,exist_ok=True)
    for key,(title,desc) in FIGURES.items():
        (dest/f'{key}.svg').write_text(svg(art(key),title,desc),encoding='utf-8')
    (dest/'workbench.svg').write_text(hero(),encoding='utf-8')


if __name__=='__main__':
    main()
