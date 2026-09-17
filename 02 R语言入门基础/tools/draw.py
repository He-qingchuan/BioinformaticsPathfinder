"""Original, editable SVG concept diagrams; numeric statistical plots come from R."""
from pathlib import Path
from html import escape as E
ROOT=Path(__file__).resolve().parents[1]
INK='#173a50'; BLUE='#256187'; GREEN='#36866f'; CORAL='#b9553d'; PALE='#dce9f0'
FIGURES={
'rstack':('R、RStudio 与包','从编辑界面到执行环境，再到结果。RStudio 帮助组织工作，R 执行代码，包提供额外功能。'),
'project':('文件都有自己的位置','从 r-lab 项目根目录出发，用相对路径连接原始数据、脚本和输出。移动整个项目后内部路径仍成立。'),
'vector':('一列值，一起计算','上排是四个原温度，下排是分别加一后的新值。位置一一对应，原对象只有在赋值时才改变。'),
'mask':('一张对齐的逻辑筛网','先判断每一项是否至少为 29，再保留 TRUE 对应的原值。筛选保留原始顺序，不自动排序。'),
'missing':('未知，不能替换成零','默认均值保留缺失提示；明确忽略缺失时得到 28，但只用了两项记录。数据没有被补齐。'),
'factor':('类别标签与内部编码','10、20 是示例标签，1、2 是因子内部编码。先转回文字再转数字，才能恢复这些数值标签。'),
'containers':('矩阵、表格与列表','矩阵强调同类值的二维结构，数据框允许各列不同类型，列表允许每个元素装不同结构。'),
'io':('文本文件与 R 对象','CSV 按格式约定读成表；写出 CSV 便于交换，RDS 保存单个 R 对象的结构。'),
'table':('行保持关系，列记录变量','每行是一条记录，每列是一个变量。框出的第二行把地点与温度绑定在同一条观察中。'),
'center':('同一组数的两个中心','图中四个点为 26、27、28、39。均值是 30，中位数是 27.5；改变高值会以不同方式影响两个中心。'),
'pipe':('让整理步骤接力','每一站接收上一步结果，再交给下一站。示意中的管道顺序是选行、选列、排序；每步都可以停下来核对。'),
'join':('连接看键，也看行数','两条 P01 记录连接唯一一条地点资料，仍得到两行。右侧键重复时可能复制左侧记录，必须检查关系。'),
'pivot':('改变摆放，不增加信息','左边三地点各有两个时段，右边变成六条地点与时段组合。六个温度值保持对应。'),
'layers':('把一幅图拆成可解释的层','数据规定有哪些记录，映射决定位置，点图层决定画成点，标签和单位让图可以独立阅读。'),
'units':('记录行数与独立单位','左边是三个地点的重复记录，右边是分别观测一次的独立装置。编号数量不能代替对采样设计的判断。'),
'sampling':('重新抽样，再算一次','每次拿到新的独立样本，再求一个均值；收集均值才得到抽样分布。这里是流程示意，数值结果见真实 R 图。'),
'coverage':('真值固定，区间在变','竖线代表固定的总体真值；各横线来自不同样本。示意只画六次，不用于估计 95% 覆盖比例。'),
'null':('在指定假设下看两侧极端','示意以 30 为中心，均值 31.2 距它 1.2，因此双侧也计算不高于 28.8 的一端。实际概率由本节 R 代码计算。'),
'regression':('斜率带着单位','直线的斜率是响应变化量除以解释变量变化量。图是概念示意，不代替实际样本的拟合结果。'),
'residual':('观察值减去拟合值','每条竖线连接观察点与同一横坐标的拟合值；在线上方残差为正，下方为负。'),
'workflow':('从输入到可追溯的结果','观察表先检查再去掉完全重复，汇总时记录有效数；独立实验和横断面资料沿各自设计进行推断。'),
}
def text(x,y,s,size=19,color=INK,anchor='middle',weight='400'):
 return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" text-anchor="{anchor}" font-weight="{weight}">{E(str(s))}</text>'
def rect(x,y,w,h,fill=PALE,stroke='none',rx=9):
 return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}"/>'
def box(x,y,w,h,label,fill=PALE,size=19):return rect(x,y,w,h,fill)+text(x+w/2,y+h/2+7,label,size)
def line(x1,y1,x2,y2,color=BLUE,arrow=False,dash=False):
 return f'<path d="M{x1} {y1}L{x2} {y2}" fill="none" stroke="{color}" stroke-width="2.5"'+(' marker-end="url(#arrow)"' if arrow else '')+(' stroke-dasharray="6 6"' if dash else '')+'/>'
def circle(x,y,r=7,color=BLUE):return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{color}"/>'
def table(x,y,headers,rows,widths,row=44,highlight=None):
 s='';xx=x
 for h,w in zip(headers,widths):s+=box(xx,y,w-2,row,h,'#c9dfe9',16);xx+=w
 for i,data in enumerate(rows):
  xx=x
  for j,(v,w) in enumerate(zip(data,widths)):
   fill='#deeee6' if i==highlight else '#f2f6f8'
   s+=box(xx,y+(i+1)*row,w-2,row-2,v,fill,17);xx+=w
 return s

def drawing(name):
 if name=='rstack':
  s=box(55,145,230,110,'RStudio：编辑与组织')+box(345,145,230,110,'R：计算与执行')+box(635,145,230,110,'表格 · 图形 · 报告')
  s+=line(288,200,337,200,arrow=True)+line(578,200,627,200,arrow=True)
  s+=box(345,305,230,55,'包：扩充功能','#deeee6')+line(460,300,460,265,GREEN,True)
  return s+text(170,286,'界面可以更换',17)+text(755,286,'结果可以保存与复查',17)
 if name=='project':
  s=box(65,166,220,70,'r-lab / 项目根目录','#c9dfe9')
  for y,a,b in [(113,'data/','原始记录'),(190,'lessons/ 与 scripts/','可执行步骤'),(267,'results/','图、表与简报')]:
   s+=line(285,201,373,y+23,arrow=True)+box(385,y,235,51,a)+text(720,y+32,b,20)
  return s+text(460,374,'data/sites.csv 从项目根目录出发；不用写用户名或电脑盘符。',18)
 if name in ['vector','mask']:
  s='';values=[27,29,28,31]
  for i,v in enumerate(values):
   x=150+i*165;s+=text(x+55,127,f'位置 {i+1}',17)+box(x,144,110,60,v)
   if name=='vector':s+=line(x+55,210,x+55,267,arrow=True)+text(x+77,243,'+1',16)+box(x,283,110,60,v+1,'#deeee6')
   else:s+=box(x,222,110,45,'TRUE' if v>=29 else 'FALSE','#deeee6' if v>=29 else '#f1e0db',17)
  if name=='mask':s+=text(100,247,'≥ 29',20)+line(370,275,370,312,arrow=True)+line(700,275,535,312,arrow=True)+box(320,325,110,52,29,'#deeee6')+box(485,325,110,52,31,'#deeee6')
  return s
 if name=='missing':
  s=''.join(box(225+i*170,135,130,58,v,'#f1e0db' if v=='NA' else PALE) for i,v in enumerate([27,'NA',29]))
  return s+line(460,205,240,267,arrow=True)+line(460,205,680,267,arrow=True)+box(75,282,330,58,'mean(x) → NA','#f1e0db')+box(500,282,330,58,'mean(x, na.rm=TRUE) → 28','#deeee6',17)+text(665,375,'有效数 2；缺失仍然存在',18)
 if name=='table':
  return table(135,135,['编号','地点','温度 °C'],[['O01','P01',27],['O02','P02',30],['O03','P03',26]],[150,190,190],highlight=1)+text(737,255,'← 第二行',21)+text(400,369,'行绑定一条记录，列描述一个变量。',19)
 if name=='factor':
  s=text(240,127,'类别标签',20)+text(680,127,'内部编码',20)
  for i,(a,b) in enumerate([('"10"',1),('"20"',2),('"10"',1)]):
   y=149+i*62;s+=box(145,y,190,48,a)+line(345,y+24,575,y+24,arrow=True)+box(590,y,180,48,b,'#f1e0db')
  return s+text(460,381,'数字标签 → 先转字符 → 再转数值；不要把编码当测量值。',18)
 if name=='containers':
  s=text(165,124,'矩阵',22)+text(460,124,'数据框',22)+text(755,124,'列表',22)
  s+=table(54,152,['早','晚'],[[1,4],[2,5],[3,6]],[110,110],37)+table(325,152,['地点','温度'],[['P01',27],['P02',30],['P03',26]],[135,135],37)
  for i,label in enumerate(['标题：文字','读数：矩阵','检查：TRUE']):s+=box(650,152+57*i,210,47,label,'#deeee6',18)
  return s+text(165,353,'同类型 · 两维',17)+text(460,353,'各列可不同类型',17)+text(755,353,'各元素可不同结构',17)
 if name=='io':
  s=box(65,185,190,72,'CSV 文本文件')+box(365,185,190,72,'R 数据框','#deeee6')
  s+=line(265,220,355,220,arrow=True)+text(310,164,'读取',18)
  for y,label in [(130,'CSV：交换表格'),(285,'RDS：保存对象')]:s+=line(565,220,662,y+27,arrow=True)+box(675,y,200,60,label)
  return s+text(460,390,'检查表头、分隔符、编码、列类型与缺失规则。',19)
 if name=='center':
  s=line(120,350,815,350,INK)+line(120,350,120,118,INK)
  for val,col,label in [(30,CORAL,'均值 30'),(27.5,GREEN,'中位数 27.5')]:
   y=350-(val-20)*11;s+=line(130,y,800,y,col,dash=True)+text(795,y-9,label,17,col,'end')
  for i,v in enumerate([26,27,28,39]):x=200+i*160;y=350-(v-20)*11;s+=circle(x,y,8)+text(x,y-15,v,19)+text(x,380,f'记录 {i+1}',16)
  return s+text(100,110,'°C',17)
 if name=='pipe':
  labels=['原始表','filter 选行','select 选列','arrange 排序'];s=''
  for i,label in enumerate(labels):
   x=38+i*225;s+=box(x,175,170,90,label,PALE,19)
   if i<3:s+=line(x+178,221,x+217,221,arrow=True)
  return s+text(460,335,'每一步都返回一个结果；可先保存中间对象，核对后再连接。',18)
 if name=='join':
  s=table(38,157,['记录','地点'],[['O01','P01'],['O07','P01']],[100,100],46)
  s+=text(351,143,'地点键唯一',18)+table(265,162,['地点','名称'],[['P01','河畔']],[90,105],46)
  s+=line(475,235,526,235,arrow=True)+table(540,157,['记录','地点','名称'],[['O01','P01','河畔'],['O07','P01','河畔']],[108,100,108],46)
  return s+text(460,361,'2 条记录 × 1 个匹配 → 2 行；若右表键重复，先停下来检查。',18)
 if name=='pivot':
  s=table(32,164,['地点','morning','afternoon'],[['P01',27.8,31.1],['P02',29.6,33],['P03',26.9,29.7]],[100,108,110],44)
  s+=line(365,236,442,236,arrow=True)+text(406,210,'变长',17)
  s+=table(462,113,['地点','时段','温度'],[['P01','morning',27.8],['P01','afternoon',31.1],['P02','morning',29.6],['P02','afternoon',33],['P03','morning',26.9],['P03','afternoon',29.7]],[105,165,125],35)
  return s+text(197,386,'3 行，6 个温度',17)+text(660,386,'6 行，仍是这 6 个温度',17)
 if name=='layers':
  s=''
  for i,(label,col) in enumerate([('数据：有哪些点',PALE),('映射：点放在哪里','#deeee6'),('图层：画成点','#f3e7c9'),('标签：名称与单位','#e5dce9')]):s+=box(45,112+i*67,270,51,label,col,18)
  s+=line(335,245,425,245,arrow=True)+line(505,329,837,329,INK)+line(505,329,505,120,INK)
  for i,(x,y) in enumerate([(520,150),(568,181),(610,190),(668,235),(718,221),(780,275)]):s+=circle(x,y,7)
  return s+text(675,372,'冠层覆盖（%）',19)+text(665,114,'温度（°C）',18)
 if name=='units':
  s=text(240,133,'3 个地点的重复记录',21)+text(698,133,'48 个独立装置，各测一次',21)
  for c in range(3):
   s+=rect(91+c*99,155,86,175,'#e3edf2')+text(134+c*99,361,f'P0{c+1}',18)
   for i in range(14):s+=circle(119+c*99+(i%2)*30,175+(i//2)*22,6,BLUE)
  for i in range(48):s+=rect(527+(i%8)*43,172+(i//8)*28,27,19,'#87b8a4',rx=4)
  return s+text(239,393,'42 行 ≠ 42 个独立地点',18,CORAL)+text(694,393,'独立性来自设计与条件',18)
 if name=='sampling':
  s=box(35,179,155,87,'模拟总体')
  for i in range(3):
   y=112+i*90;s+=line(198,223,265,y+30,arrow=True)+rect(280,y,165,66,'#deeee6')
   for j in range(20):s+=circle(301+(j%5)*29,y+12+(j//5)*14,3,GREEN)
   s+=line(454,y+33,525,y+33,arrow=True)+box(540,y+7,153,51,f'样本均值 {i+1}')
  return s+line(705,223,765,223,arrow=True)+box(777,150,120,145,'收集均值',PALE,17)+text(460,393,'每份样本 n = 20；重复次数不是单份样本量。',18)
 if name=='coverage':
  s=line(475,114,475,358,CORAL,dash=True)+text(475,104,'固定的真值',18,CORAL)
  pairs=[(330,570),(425,675),(205,430),(372,603),(519,737),(341,520)]
  for i,(a,b) in enumerate(pairs):
   y=144+i*38;col=BLUE if a<=475<=b else CORAL;s+=line(a,y,b,y,col)+circle(a,y,3,col)+circle(b,y,3,col)+text(155,y+7,f'样本 {i+1}',17)
  return s+text(460,401,'只画 6 次帮助理解；覆盖比例要靠大量重复抽样考察。',18)
 if name=='null':
  s=line(90,326,838,326,INK)
  s+='<path d="M100 325 C260 325 310 120 460 120 S665 325 820 325" fill="none" stroke="'+BLUE+'" stroke-width="4"/>'
  for x,label,col in [(278,'28.8',CORAL),(460,'30',INK),(642,'31.2',CORAL)]:s+=line(x,330,x,170,col,dash=True)+text(x,363,label,20,col)
  return s+line(271,289,151,289,CORAL,True)+line(650,289,776,289,CORAL,True)+text(181,259,'更低的一端',17,CORAL)+text(737,259,'更高的一端',17,CORAL)+text(460,402,'假定均值为 30 及模型成立；两边都算“至少同样远”。',18)
 if name in ('regression','residual'):
  s=line(120,354,825,354,INK)+line(120,354,120,112,INK)+line(170,150,765,310,GREEN)
  points=[(220,140),(330,217),(430,191),(570,296),(680,264)]
  for x,y in points:
   fit=150+(x-170)*160/595
   if name=='residual':s+=line(x,y,x,fit,CORAL)+circle(x,fit,4,GREEN)
   s+=circle(x,y,7)
  if name=='regression':s+=line(330,193,590,193,CORAL)+line(590,193,590,263,CORAL)+text(460,182,'Δx',19,CORAL)+text(623,233,'Δy',19,CORAL)
  return s+text(460,397,'斜率 = Δy / Δx；解释时带上变量单位。' if name=='regression' else '竖线长度表示偏离；残差 = 观察值 − 拟合值。',19)
 if name=='workflow':
  s=''
  for i,(a,b) in enumerate([('观察表 43 行','检查 → 去重 → 42 行'),('独立装置 48 个','随机分组 → Welch 比较'),('独立地点 30 个','横断面 → 回归与诊断')]):
   y=126+i*83;s+=box(35,y,215,58,a)+line(260,y+29,307,y+29,arrow=True)+box(320,y,280,58,b,'#deeee6',18)+line(610,y+29,675,245,arrow=True)
  return s+box(694,189,195,114,'图表与分析简报')+text(460,405,'分别保留设计与有效数，不能拼在一起扩大“样本量”。',18)
 raise ValueError(name)

def main():
 dest=ROOT/'assets/illustrations';dest.mkdir(exist_ok=True)
 for name,(title,desc) in FIGURES.items():
  svg=f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 920 440" role="img" aria-labelledby="title desc"><title id="title">{E(title)}</title><desc id="desc">{E(desc)}</desc><defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10Z" fill="{BLUE}"/></marker></defs><rect width="920" height="440" rx="18" fill="#fbfdfe"/><g font-family="Noto Sans CJK SC,Microsoft YaHei,PingFang SC,sans-serif">{text(38,50,title,27,anchor='start',weight='700')}{text(38,82,'数据调查小镇 / 概念图解',13,BLUE,anchor='start')}{drawing(name)}</g></svg>'''
  (dest/f'{name}.svg').write_text(svg)
if __name__=='__main__':main()
