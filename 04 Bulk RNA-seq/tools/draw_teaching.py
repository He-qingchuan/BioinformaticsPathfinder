"""Fourteen original vector explanations; illustrative data are explicitly labelled."""
from pathlib import Path
from html import escape
import math

ROOT=Path(__file__).resolve().parents[1]
INK='#254c52'; GREEN='#54867b'; BLUE='#397f9d'; ORANGE='#c17c50'; PALE='#e2eee0'; MUTED='#61796f'; RED='#b65f58'
class Art:
    def __init__(self,title,description,height=440):
        self.title=title;self.description=description;self.height=height;self.parts=[]
    def add(self,s):self.parts.append(s)
    def text(self,x,y,s,size=18,color=INK,anchor='start',weight=400):
        self.add(f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" text-anchor="{anchor}" font-weight="{weight}">{escape(str(s))}</text>')
    def lines(self,x,y,lines,size=17,color=INK,step=27,anchor='start'):
        for i,s in enumerate(lines):self.text(x,y+i*step,s,size,color,anchor)
    def rect(self,x,y,w,h,fill=PALE,stroke='none',rx=10):self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}"/>')
    def line(self,x1,y1,x2,y2,color=MUTED,width=2,dash=''):
        self.add(f'<path d="M{x1},{y1} L{x2},{y2}" fill="none" stroke="{color}" stroke-width="{width}" stroke-dasharray="{dash}"/>')
    def circle(self,x,y,r=8,fill=GREEN,stroke='none',width=2):self.add(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>')
    def arrow(self,x1,y1,x2,y2,color=MUTED):
        self.line(x1,y1,x2,y2,color,2)
        a=math.atan2(y2-y1,x2-x1)
        for d in [-.55,.55]:self.line(x2,y2,x2-9*math.cos(a+d),y2-9*math.sin(a+d),color,2)
    def path(self,points,color=GREEN,width=3,dash=''):
        self.add('<polyline points="'+' '.join(f'{x:.2f},{y:.2f}' for x,y in points)+f'" stroke="{color}" fill="none" stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round" stroke-dasharray="{dash}"/>')
    def save(self,name):
        out=ROOT/'assets/illustrations'/f'{name}.svg';out.parent.mkdir(parents=True,exist_ok=True)
        svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="900" height="{self.height}" viewBox="0 0 900 {self.height}" role="img" aria-labelledby="title desc"><title id="title">{escape(self.title)}</title><desc id="desc">{escape(self.description)}</desc><rect width="900" height="{self.height}" rx="16" fill="#f8fbf4"/><g font-family="Noto Sans CJK SC,Microsoft YaHei,sans-serif">'+''.join(self.parts)+'</g></svg>'
        out.write_text(svg+'\n')

def make_teaching_art():
    a=Art('7 个时期，21 个文库，42 个文件','实验数量来自本案例；试管和片段形状为示意。三份生物学重复分别建库，每个文库含 R1 和 R2 两端文件。',470)
    a.text(30,37,'先分清：时期、重复、文库、测序端',23,weight=600)
    colors=['#ec9182','#b59d43','#7baf50','#55a899','#50a8bd','#9987bd','#c88cba']
    for i,h in enumerate([0,1,4,8,12,16,20]):
        x=48+i*120;a.text(x+32,77,f'ZT{h}',18,anchor='middle',weight=600)
        for r in range(3):
            xx=x+r*23;a.rect(xx,94,17,65,'white',GREEN,7);a.rect(xx+3,122,11,32,colors[i],rx=4);a.line(xx-1,94,xx+18,94,INK,3)
        a.text(x+32,185,'3 个重复',15,anchor='middle')
    a.text(450,224,'7 × 3 = 21 份独立文库',21,anchor='middle',weight=600)
    a.line(30,245,870,245,'#c9d9c6',1)
    a.lines(35,291,['放大其中一份文库','ZT4_rep_1'],18)
    a.rect(270,276,295,45,'#d4e6dc',GREEN,5);a.text(418,305,'一个待测片段',18,anchor='middle')
    a.arrow(292,265,368,265,BLUE);a.text(300,253,'R1 →',16,BLUE)
    a.arrow(545,334,469,334,ORANGE);a.text(490,360,'← R2',16,ORANGE)
    a.arrow(593,295,660,295);a.lines(690,285,['R1.fastq','R2.fastq'],18)
    a.text(450,411,'21 个文库 × 每库 2 端 = 42 个 FASTQ 文件',20,anchor='middle',weight=600)
    a.text(450,445,'同一片段的两端提供配对信息，不能算作两个生物学重复。',17,MUTED,'middle');a.save('replicates')

    a=Art('FASTQ：一条 read 的四行记录','教学示意使用 Phred+33 编码；每个碱基对应一个质量字符。',420)
    a.text(30,38,'同一条 read，有“读到了什么”和“有多确定”两条信息',22,weight=600)
    labels=['① 名称','② 碱基序列','③ 分隔行','④ 质量字符'];values=['@toy_read_001','ACGTACGT','+','IIII?555']
    for i,(label,value) in enumerate(zip(labels,values)):
        y=91+i*55;a.text(35,y,label,18);a.rect(215,y-29,355,43, '#e5eee2' if i in [1,3] else '#eef3e9',rx=5)
        a.add(f'<text x="237" y="{y}" font-family="monospace" font-size="26" letter-spacing="4" fill="{INK}">{escape(value)}</text>')
    a.lines(617,130,['8 个碱基','↕ 一一对应','8 个质量字符'],18)
    a.line(30,309,870,309,'#c9d9c6',1)
    a.text(36,349,'本图的质量字符示意：',18,weight=600)
    for x,char,q in [(305,'I','Q40'),(480,'?','Q30'),(655,'5','Q20')]:
        a.rect(x,323,145,46,'#dce9e0');a.text(x+72,352,f'{char} → {q}',21,anchor='middle')
    a.text(450,398,'字符先按正确编码解码，才得到质量值；这里不是本案例的一条真实 read。',16,MUTED,'middle');a.save('fastq')

    a=Art('修剪与过滤：剪短，还在；丢弃，才减少条数','两条简化 read 展示处理动作。剪去接头后仍可保留 read，整条不符合规则才丢弃。')
    a.text(30,40,'剪掉一截，与丢弃整条，是两件事',23,weight=600)
    for y in [123,259]:
        a.rect(55,y-28,227,44,'#c9dfc5',GREEN,4);a.rect(282,y-28,102,44,'#edd0b4',ORANGE,4)
        a.text(168,y,'待测序列',18,anchor='middle');a.text(333,y,'接头',17,anchor='middle')
    a.circle(417,96,7,'none',ORANGE);a.circle(417,118,7,'none',ORANGE);a.line(423,99,455,124,ORANGE,3);a.line(423,116,455,91,ORANGE,3)
    a.arrow(464,111,530,111);a.rect(557,95,235,44,'#c9dfc5',GREEN,4);a.text(674,123,'修剪后仍保留',18,anchor='middle')
    a.text(557,170,'read 条数不变，碱基总数减少',17,GREEN)
    a.line(70,234,267,285,RED,3);a.line(70,282,267,235,RED,3);a.text(65,319,'例：主体序列质量不满足规则',17,RED)
    a.arrow(420,251,530,251);a.rect(581,218,68,64,'#eadbd5',RED,4);a.line(572,214,658,214,RED,4);a.line(597,228,597,270,RED);a.line(633,228,633,270,RED)
    a.text(680,250,'丢弃整条',18,RED);a.text(555,318,'read 条数与碱基总数都减少',17,RED)
    a.rect(30,365,840,49,'#e6eee0');a.text(450,396,'所以：reads 保留很多，仍可能已经剪掉不少接头碱基。',19,anchor='middle');a.save('trimming')

    a=Art('decoy：给片段一个更完整的来源参照','某片段与目标转录本局部相似，却与基因组其他位置更吻合；竞争比较有助减少错误归属。')
    a.text(30,39,'不要把“有点像”直接当成“来自它”',23,weight=600)
    a.rect(35,170,180,66,'#e6d9b9',ORANGE);a.text(125,210,'待判断的片段',18,anchor='middle')
    a.arrow(229,199,335,112);a.arrow(229,210,335,297)
    a.rect(358,78,305,101,'#dfecda');a.text(380,108,'候选 A：目标转录本',19,weight=600)
    for i in range(10):a.rect(382+i*24,129,17,18,GREEN if i<6 else '#e7ccb4',rx=2)
    a.text(697,127,'局部相似',18,MUTED)
    a.rect(358,245,305,101,'#dcebed');a.text(380,276,'候选 B：基因组 decoy',19,weight=600)
    for i in range(10):a.rect(382+i*24,296,17,18,BLUE,rx=2)
    a.text(697,294,'更吻合',18,BLUE,weight=600)
    a.text(450,387,'引入 decoy 竞争比较，帮助识别不宜强行计入目标 RNA 的片段。',18,anchor='middle')
    a.text(450,419,'形状为示意；decoy 是参考序列，不是新样本，也不作为目标转录本报告丰度。',16,MUTED,'middle');a.save('decoy')

    a=Art('把转录本归到基因，再把样本排成列','简化计数示意。一个基因的两个转录本先按明确映射汇总，之后形成基因乘样本矩阵。')
    a.text(30,40,'矩阵的一格，是“这个基因 × 这份样本”',23,weight=600)
    a.text(40,90,'样本 A 的转录本计数',19,weight=600)
    for i,(name,val) in enumerate([('G1 · 转录本 a',3),('G1 · 转录本 b',2),('G2 · 转录本 a',4)]):
        y=126+i*60;a.text(40,y,name,17)
        for k in range(val):a.rect(198+k*23,y-18,17,22,GREEN if i<2 else BLUE,rx=3)
    a.add(f'<path d="M320 112h15v61h-15" fill="none" stroke="{GREEN}" stroke-width="2"/>');a.arrow(346,143,425,143);a.text(368,126,'3+2',16,GREEN)
    a.arrow(325,241,425,241,BLUE)
    a.text(530,98,'样本 A',18,anchor='middle');a.text(678,98,'样本 B',18,anchor='middle')
    for i,(gene,vs) in enumerate([('G1',[5,10]),('G2',[4,1])]):
        y=122+i*87;a.text(431,y+40,gene,20)
        for j,v in enumerate(vs):a.rect(478+j*147,y,106,63,'#dbeada' if i==0 else '#dce9ed',INK,5);a.text(531+j*147,y+41,v,26,anchor='middle',weight=600)
    a.rect(30,331,840,75,'#e9efe2');a.lines(54,361,['先核对转录本—基因对应关系，再对齐样本列名。','图中数值为教学示意；真实 Salmon estimated counts 可以包含小数。'],18);a.save('matrix_build')

    a=Art('PCA 的一个点来自样本的一整列表达','左侧简化表达矩阵的三列分别代表三个样本。PCA 为每一列样本计算主成分坐标，右侧位置仅为示意。')
    a.text(30,40,'从“一整列基因表达”，到“一个样本点”',23,weight=600)
    a.text(42,93,'简化表达矩阵',19,weight=600)
    for j,label in enumerate(['A1','A2','B1']):a.text(158+j*65,126,label,17,anchor='middle')
    for i in range(6):
        a.text(58,163+i*28,f'G{i+1}',15)
        for j in range(3):a.rect(134+j*65,142+i*28,47,23,(['#a1bb9d','#b0c7a5','#bdd4d8'][i%3] if j==1 else ['#9bb89a','#afc6a1','#b4d2d9'][(i+j//2)%3]),rx=2)
    a.rect(126,135,59,181,'none',GREEN,5);a.text(105,351,'框出的一列 = 一份样本',17,GREEN)
    a.arrow(350,219,465,219);a.lines(352,169,['按基因组合','计算投影'],17)
    a.line(524,322,842,322);a.line(524,322,524,110);a.text(832,351,'PC1',17);a.text(510,97,'PC2',17)
    for x,y,c,label in [(575,254,GREEN,'A1'),(618,228,GREEN,'A2'),(773,151,BLUE,'B1')]:a.circle(x,y,12,c);a.text(x+14,y-13,label,18)
    a.text(450,405,'一个点保留样本身份；坐标由许多基因共同决定，图中位置不是实测 PCA 得分。',16,MUTED,'middle');a.save('matrix_pca')

    a=Art('同样均值差，不同组内波动','两幅示意散点图有相同组均值差，右图重复之间更分散。未在示意数据上计算统计 P 值。')
    a.text(30,40,'不只问差多少，还要看重复有多稳',23,weight=600)
    for offset,values,label in [(35,[[4.8,5,5.2],[8.8,9,9.2]],'组内较集中'),(483,[[1,5,9],[5,9,13]],'组内较分散')]:
        a.rect(offset,65,378,294,'#edf3e8');a.text(offset+189,99,label,20,anchor='middle',weight=600)
        a.line(offset+54,301,offset+341,301);a.line(offset+54,301,offset+54,122)
        for v in [0,5,10,15]:a.text(offset+43,306-v*11,v,13,MUTED,'end')
        for j,vs in enumerate(values):
            x=offset+133+j*133;color=GREEN if j==0 else ORANGE
            for k,v in enumerate(vs):a.circle(x+(k-1)*12,301-v*11,7,color)
            mean=sum(vs)/3;a.line(x-27,301-mean*11,x+27,301-mean*11,INK,3);a.text(x,333,'组 A' if j==0 else '组 B',17,anchor='middle')
        a.text(offset+343,126,'示意表达值',13,MUTED,'end')
    a.text(450,391,'两边都是：组 A 均值 5，组 B 均值 9；均值差同为 4。',19,anchor='middle',weight=600)
    a.text(450,424,'点是生物学重复，短黑线是组均值；统计判断还需要模型，不能只比较均值。',16,MUTED,'middle');a.save('variation')

    a=Art('把名单、韦恩图和 UpSet 对上','两个教学集合 A={a,b} 与 B={b,c}。韦恩交集只有基因 b；UpSet 用深浅点表示同一成员关系。')
    a.text(30,40,'同一批成员，可以用不同方式排给你看',23,weight=600)
    a.rect(30,92,186,219,'#e6eee0');a.lines(51,127,['比较 A 的名单','a    b','','比较 B 的名单','b    c'],18)
    a.arrow(231,200,285,200)
    a.circle(345,199,66,'#c2d9c6',GREEN);a.circle(419,199,66,'#d4e3e8',BLUE)
    a.circle(345,199,66,'none',GREEN);a.circle(419,199,66,'none',BLUE)
    a.text(314,204,'a',25,GREEN);a.text(383,204,'b',25,INK,'middle',600);a.text(447,204,'c',25,BLUE)
    a.text(321,106,'集合 A',17,GREEN);a.text(424,106,'集合 B',17,BLUE)
    a.text(382,305,'重叠区：只有基因 b',17,anchor='middle')
    a.arrow(505,200,555,200)
    a.text(663,91,'同一个交集，换成点阵',17,anchor='middle')
    for j,label in enumerate(['a','b','c']):
        x=650+j*72;a.rect(x-14,122,28,52,BLUE,rx=0);a.text(x,112,'1',17,anchor='middle');a.text(x,323,label,18,anchor='middle')
        included=[[True,False],[True,True],[False,True]][j]
        if all(included):a.line(x,220,x,267,INK,3)
        for i,val in enumerate(included):a.circle(x,220+i*47,8,INK if val else '#d9e3d8')
    a.text(588,226,'A',18);a.text(588,273,'B',18);a.line(610,177,841,177)
    a.text(677,360,'柱上数字 = 基因数',17,BLUE,'middle')
    a.text(450,412,'中间一列：A、B 都为深色，表示同时入选两份名单的基因 b。',18,anchor='middle');a.save('sets_logic')

    a=Art('同一个基因，在三种结果里的位置','假设基因 Gx 的 log2FC=2，padj=0.01；火山点落在 (2,2)。热图一行展开六个样本，统计值和颜色均为教学示意。',470)
    a.text(30,40,'同一个基因：表里一行，火山图一个点，热图一整行',22,weight=600)
    a.rect(30,76,839,81,'#e5eee0');a.text(53,106,'教学假设 · 比较方向：B 相对 A',15,MUTED)
    a.text(53,140,'Gx',22,weight=600);a.text(168,138,'log₂FC = +2',22);a.text(393,138,'padj = 0.01',22);a.text(627,138,'−log₁₀(0.01) = 2',20)
    a.arrow(251,169,251,202);a.arrow(654,169,654,202)
    a.line(65,370,395,370);a.line(219,370,219,220);a.text(57,217,'−log₁₀(padj)',15);a.text(342,419,'log₂FC',16,anchor='middle')
    for x,label in [(91,'−2'),(219,'0'),(347,'+2')]:a.text(x,390,label,14,anchor='middle')
    a.circle(347,264,11,ORANGE);a.text(321,248,'Gx',18,ORANGE,weight=600);a.line(219,264,347,264,MUTED,1,'4 4');a.text(208,269,'2',15,anchor='end')
    a.text(488,238,'组 A 的重复',16);a.text(686,238,'组 B 的重复',16)
    for i in range(6):
        x=484+i*57;a.rect(x,262,51,56, ['#b5cedd','#a3c1d5','#c7d9df','#deb78f','#cf9c69','#c18b54'][i],rx=2);a.text(x+25,345,str(i%3+1),16,anchor='middle')
    a.text(445,296,'Gx',18,weight=600);a.text(641,387,'一格 = 一份样本的行 Z-score',16,anchor='middle')
    a.text(450,445,'图中为示意值：火山图概括组间检验，热图展开样本表达；两者不是独立实验。',16,MUTED,'middle');a.save('gene_views')

    a=Art('富集先问：候选中的比例比背景高吗','教学集合含 20 个背景基因，其中 4 个属于橙色功能。圈出的 5 个候选中有 3 个属于该功能。候选是背景的子集。')
    a.text(30,39,'只看到“有 3 个”不够，还要知道它们从哪里来',23,weight=600)
    a.rect(30,74,402,272,'#e7f0e1');a.text(50,107,'背景：20 个可注释基因',19,weight=600)
    for i in range(20):
        x=83+(i%5)*64;y=143+(i//5)*49;a.circle(x,y,14,ORANGE if i<4 else GREEN)
        if i in [0,1,2,4,5]:a.circle(x,y,21,'none',INK,2)
    a.text(52,328,'橙色功能：4 / 20 = 20%',18)
    a.arrow(447,204,502,204)
    a.rect(526,74,344,272,'#f0e6d3');a.text(549,107,'候选：圈出的 5 个基因',19,weight=600)
    for i in range(5):a.circle(565+i*60,183,17,ORANGE if i<3 else GREEN)
    a.text(546,262,'橙色功能：3 / 5 = 60%',19,weight=600)
    a.text(546,310,'候选比例是背景的 3 倍',18,ORANGE)
    a.text(450,389,'这里比较的是功能成员比例，不是两个组的表达倍数。',19,anchor='middle')
    a.text(450,424,'20 个圆点与数值都是教学示意；正式 ORA 还需统计检验与多重校正。',16,MUTED,'middle');a.save('ora_background')

    a=Art('GSEA：沿队伍走，遇到成员就加分','12 个基因按方向排队，其中 4 个橙色基因属于同一功能。采用等权示意：命中加 1/4，非命中减 1/8，结束回到零。',490)
    a.text(30,40,'同一个功能的成员，是否挤在队伍的一端？',23,weight=600)
    a.text(87,79,'正向端',17,ORANGE);a.text(730,79,'负向端',17,BLUE)
    hit={0,1,3,4}
    for i in range(12):
        x=135+i*58;a.rect(x-19,96,38,38,ORANGE if i in hit else '#b5ced0',rx=4);a.text(x,122,i+1,16,'white' if i in hit else INK,'middle')
        if i in hit:a.line(x,144,x,165,INK,3)
    a.text(52,196,'累计分数',16);a.line(86,382,850,382,MUTED,1,'4 4');a.line(86,210,86,395)
    for score in [0,.5,1]:a.text(73,387-score*164,f'{score:g}',14,MUTED,'end')
    points=[(106,382)];score=0
    for i in range(12):
        score += .25 if i in hit else -.125;points.append((135+i*58,382-score*164))
    a.path(points,GREEN,4);a.text(450,248,'前端命中密集，分数先明显上升',18,GREEN,weight=600)
    a.text(450,436,'这里采用等权示意：命中 +1/4，未命中 −1/8。',18,anchor='middle')
    a.text(450,471,'真实 GSEA 还会考虑排序权重、标准化和统计检验；这些位置不是本案例的基因排名。',16,MUTED,'middle');a.save('gsea_walk')

    a=Art('表达量不同，也可能唱出相似的旋律','教学基因 A 与 B 的原始量级不同，但变化形状一致。按基因标准化后形状重合，模糊隶属度是归属程度而非 P 值。')
    a.text(30,40,'先比较形状，再谈模块归属',23,weight=600)
    a.text(52,92,'原始量级不同',20,weight=600);a.text(375,92,'标准化后形状一致',20,weight=600);a.text(681,92,'允许模糊归属',20,weight=600)
    a.line(50,306,273,306);a.line(50,306,50,125)
    for vals,color,name in [([2,4,6,4,2],GREEN,'A'),([20,40,60,40,20],ORANGE,'B')]:
        pts=[(65+i*46,306-v*2.5) for i,v in enumerate(vals)];a.path(pts,color);a.text(260,pts[-1][1]-6,name,18,color)
    a.text(49,326,'示意时期 1 → 5',15,MUTED);a.text(41,145,'60',13,MUTED,'end');a.text(41,307,'0',13,MUTED,'end')
    a.arrow(290,215,332,215)
    a.line(363,252,574,252,MUTED,1,'4 4');a.line(363,314,363,132)
    vals=[2,4,6,4,2];mean=sum(vals)/5;sd=math.sqrt(sum((v-mean)**2 for v in vals)/4)
    pts=[(373+i*45,252-(v-mean)/sd*55) for i,v in enumerate(vals)];a.path(pts,GREEN,5);a.path(pts,ORANGE,2,'6 6')
    a.text(355,257,'0',13,MUTED,'end')
    a.text(362,341,'同一行减均值、除标准差',15,MUTED)
    a.arrow(595,215,643,215)
    a.rect(672,142,178,66,'#dce9dd');a.text(761,168,'另一个示意基因 C',16,anchor='middle');a.text(761,193,'有些像两种模式',16,anchor='middle')
    a.rect(672,237,107,35,GREEN,rx=0);a.rect(779,237,71,35,ORANGE,rx=0);a.text(721,261,'0.6',17,'white','middle');a.text(814,261,'0.4',17,'white','middle')
    a.lines(672,310,['模块 1 / 模块 2','隶属度表示相符程度'],15)
    a.text(450,398,'标准化让我们看相对形状；相似的表达轨迹并不自动等于同一生物通路。',17,anchor='middle');a.save('fuzzy_shapes')

    a=Art('周期、相位、幅度各问一个问题','正弦曲线仅为原理示意：周期 24 小时、峰相位 6 小时、相对中线的振幅 2。不是对案例 JTK 的拟合或 AMP 参数复算。',480)
    a.text(30,40,'一轮多久？峰在何时？离中线多高？',23,weight=600)
    x=lambda h:84+h*15.2;y=lambda v:341-v*32
    a.line(x(0),y(0),x(49),y(0));a.line(x(0),y(0),x(0),y(7));a.line(x(0),y(4),x(48),y(4),MUTED,1,'5 5')
    points=[(x(h/4),y(4+2*math.cos(2*math.pi*(h/4-6)/24))) for h in range(193)];a.path(points,GREEN,4)
    for h in [0,6,12,18,24,30,36,42,48]:a.text(x(h),369,h,14,MUTED,'middle')
    for v in [0,2,4,6]:a.text(69,y(v)+5,v,14,MUTED,'end')
    a.text(790,397,'小时',17);a.text(32,106,'示意信号',15)
    a.line(x(6),y(6)-9,x(6),89,GREEN,1,'3 3');a.line(x(30),y(6)-9,x(30),89,GREEN,1,'3 3')
    a.arrow(x(6),92,x(30),92,GREEN);a.arrow(x(30),92,x(6),92,GREEN);a.text(x(18),78,'周期 = 24 h',18,GREEN,'middle',600)
    a.arrow(x(0),396,x(6),396,ORANGE);a.text(91,425,'峰相位 = 6 h',17,ORANGE)
    a.arrow(x(30)+30,y(4),x(30)+30,y(6),BLUE);a.arrow(x(30)+30,y(6),x(30)+30,y(4),BLUE);a.text(x(30)+105,y(6),'振幅 = 2',17,BLUE)
    a.text(450,459,'这是理想波形的概念示意；真实 JTK 参数按软件定义估计，观测折线不是拟合波形。',16,MUTED,'middle');a.save('cycle_terms')

    a=Art('让自定义基因编号连上功能字典','原理示意展示代表蛋白和同源证据形成的基因—功能多对多映射。没有证据的基因保留未知，不强行赋予功能。')
    a.text(30,40,'编号本身没有功能，注释要有证据作桥梁',23,weight=600)
    a.text(54,90,'本物种基因',19,weight=600);a.text(302,90,'对应代表蛋白',19,weight=600);a.text(633,90,'有证据支持的功能标签',19,weight=600)
    for i,g in enumerate(['Gene_A','Gene_B','Gene_C']):
        yy=135+i*82;a.rect(44,yy-23,151,45,'#dfe9da');a.text(119,yy+7,g,18,anchor='middle');a.arrow(207,yy,282,yy)
        pts=[(305+j*16,yy+math.sin(j*1.5)*12) for j in range(9)];a.path(pts,[GREEN,BLUE,MUTED][i],5)
    a.text(465,254,'同源搜索',16);a.text(465,281,'与注释转移',16)
    a.arrow(451,135,632,134,GREEN);a.arrow(451,143,632,224,GREEN);a.arrow(451,216,632,224,BLUE)
    a.rect(648,109,205,53,'#e5ead4');a.text(750,142,'GO 功能 α',18,anchor='middle');a.rect(648,202,205,53,'#dce9ec');a.text(750,235,'KEGG 功能 β',18,anchor='middle')
    a.line(462,299,618,299,MUTED,2,'5 5');a.text(660,307,'暂缺功能证据',18,MUTED)
    a.text(450,373,'一个基因可以关联多个功能，一个功能也可以关联多个基因。',19,anchor='middle')
    a.text(450,412,'图中名称为示意；实际映射以代表蛋白、数据库与筛选记录为依据。',17,MUTED,'middle');a.save('annotation_map')

if __name__=='__main__':
    make_teaching_art()
    print('Created 14 original teaching SVGs from local source.')
