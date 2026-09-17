---
title: "R语言入门基础"

date: "2025-08-12"
output: html_document
---

# R语言入门

## R语言基础

### 1.向量

```{r}

# 1.向量生成🌟#####
#(1)用 c() 结合到一起
c(2,5,6,2,9) 
c("a","f","md","b")
#(2)连续的数字用冒号“:” 
1:5
#(3)有重复的用rep(),有规律的序列用seq(),随机数用rnorm()
rep("x",times=3)  
seq(from=3,to=21,by=3)
rnorm(n=3)
#(4)通过组合,产生更为复杂的向量。
paste0(rep("x",times=3),1:3)

#####2.2对单个向量进行的操作####
#(1)赋值给一个变量名
x = c(1,3,5,1) #随意的写法
x
x <- c(1,3,5,1) #规范的赋值符号 Alt+减号
x

#赋值+输出一起实现
x <- c(1,3,5,1);x
(x <- c(1,3,5,1))

#(2)简单数学计算
x+1
log(x)
sqrt(x)

#(3)根据某条件进行判断,生成逻辑型向量
x>3
x==3
#(4)初级统计
max(x) #最大值
min(x) #最小值
mean(x) #均值
median(x) #中位数
var(x) #方差
sd(x) #标准差
sum(x) #总和

length(x) #长度
unique(x) #去重复
duplicated(x) #对应元素是否重复
table(x) #重复值统计
sort(x)
sort(x,decreasing = F)
sort(x,decreasing = T)
#####2.3.对两个向量进行的操作#####
x = c(1,3,5,1)
y = c(3,2,5,6)
#(1)比较运算，生成等长的逻辑向量
x == y 
y == x
#(2)数学计算
x + y
#(3)连接
paste(x,y,sep=",")

#paste与paste0的区别
paste(x,y)

paste0(x,y)
paste(x,y,sep = "")

paste(x,y,sep = ",")
#当两个向量长度不一致
x = c(1,3,5,6,2)
y = c(3,2,5)
x == y # Warning: 长的对象长度不是短的对象长度的整倍数[1] FALSE FALSE  TRUE FALSE  TRUE
#循环补齐

#利用循环补齐简化代码
paste0(rep("x",3),1:3)
paste0("x",1:3)

#(4)交集、并集、差集
intersect(x,y)
union(x,y)
setdiff(x,y)
setdiff(y,x)

x %in% y #x的每个元素在y中存在吗
y %in% x #y的每个元素在x中存在吗

#####2.4.向量筛选(取子集)--看ppt#####

x <- 8:12
#根据逻辑值取子集
x[x==10]
x[x<12]
x[x %in% c(9,13)]
#根据位置取子集
x[4]
x[2:4]
x[c(1,5)]
x[-4]
x[-(2:4)]

####2.5.修改向量中的某个/某些元素：取子集+赋值
x
#改一个元素
x[4] <- 40
x
#改多个元素
x[c(1,5)] <- c(80,20)
x

#### 2.6 简单向量作图
k1 = rnorm(12);k1
k2 = rep(c("a","b","c","d"),each = 3);k2
plot(k1)
boxplot(k1~k2) #课后试着搜索boxplot表达什么意思


# 1.生成1到15之间所有偶数
seq(from = 1,to = 15,by = 2)
seq(from = 2,to = 15,by = 2)
# 2.生成向量，内容为："student2"  "student4"  "student6"  "student8"  "student10" "student12" "student14" 
# 提示：paste0
paste0(rep("student",times = 7),seq(from = 2, to = 15,by = 2))
# 3.将两种不同类型的数据用c()组合在一起，看输出结果
c(1,"a")
c(TRUE,"a")
c(1,TRUE)

# 4.用函数计算向量g的长度
load("gands.Rdata")
length(g)
# 5.筛选出向量g中下标为偶数的基因名。
seq(2,100,2)
g[seq(2,100,2)]
# 6.向量g中有多少个元素在向量s中存在(要求用函数计算出具体个数)？将这些元素筛选出来
# 提示：%in%
table(g %in% s)
g[g %in% s]
# 7.生成10个随机数: rnorm(n=10,mean=0,sd=18)，用向量取子集的方法，取出其中小于-2的值
z = rnorm(n=10,mean=0,sd=18)
z
z[z<-2]
z

z = rnorm(n=10,mean=0,sd=18)
z
z[z< -2]
z[z<(-2)]

```

### 2.数据框，矩阵，列表

```{r}
#重点：数据框
#1.数据框来源
# （1）用代码新建
# （2）由已有数据转换或处理得到
# （3）读取表格文件
# （4）R语言内置数据

#2.新建和读取数据框
df1 <- data.frame(gene   = paste0("gene",1:4),
                 change  = rep(c("up","down"),each = 2),
                 score   = c(5,3,-2,-4))
df1

df2 <- read.csv("gene.csv")
df2

#3.数据框属性
#
dim(df1)
nrow(df1)
ncol(df1)
#
rownames(df1)
colnames(df1)

#4.数据框取子集
df1$gene  #删掉score，按tab键试试
mean(df1$score)

## 按坐标
df1[2,2]
df1[2,]
df1[,2]
df1[c(1,3),1:2]
## 按名字
df1[,"gene"]
df1[,c('gene','change')]
## 按条件（逻辑值）
df1[df1$score>0,]

## 代码思维
#如何取数据框的最后一列？
df1[,3]
df1[,ncol(df1)]
#如何取数据框除了最后一列以外的其他列？
df1[,-ncol(df1)]

#筛选score > 0的基因
df1[df1$score > 0,1]
df1$gene[df1$score > 0]

#5.数据框修改

#改一个格
df1[3,3] <- 5
df1
#改一整列
df1$score <- c(12,23,50,2)     
df1
#？
df1$p.value <- c(0.01,0.02,0.07,0.05) 
df1

#改行名和列名
rownames(df1) <- c("r1","r2","r3","r4")
#只修改某一行/列的名
colnames(df1)[2] <- "CHANGE"

#6.两个数据框的连接
test1 <- data.frame(name = c('jimmy','nicker','Damon','Sophie'), 
                    blood_type = c("A","B","O","AB"))
test1
test2 <- data.frame(name = c('Damon','jimmy','nicker','tony'),
                    group = c("group1","group1","group2","group2"),
                    vision = c(4.2,4.3,4.9,4.5))
test2

test3 <- data.frame(NAME = c('Damon','jimmy','nicker','tony'),
                    weight = c(140,145,110,138))
test3
merge(test1,test2,by="name") #取交集了
merge(test1,test3,by.x = "name",by.y = "NAME")

##### 矩阵和列表
m <- matrix(1:9, nrow = 3)
colnames(m) <- c("a","b","c") #加列名
m
m[2,]
m[,1]
m[2,3]
m[2:3,1:2]
m
t(m)
as.data.frame(m)
#列表
l <- list(m1 = matrix(1:9, nrow = 3),
          m2 = matrix(2:9, nrow = 2))
l

l[[2]]
l$m1

# 补充：元素的名字

scores = c(100,59,73,95,45)
names(scores) = c("jimmy","nicker","Damon","Sophie","tony")
scores
scores["jimmy"]
scores[c("jimmy","nicker")]

names(scores)[scores>60]

# 删除 
rm(l)
rm(df1,df2)
rm(list = ls()) 

# match练习题
load("matchtest.Rdata")


```

### 3.循环和写函数

```{r}
jimmy <- function(a,b,m = 2){
  (a+b)^m
}
jimmy(a = 1,b = 2)
jimmy(1,2)
jimmy(3,6)
jimmy(3,6,-2)

#复习：绘图函数plot()
par(mfrow = c(2,2)) #把画板分成四块，两行两列
#如果报错，把右下角画板拉大一点即可
x = c(2,5,6,2,9);plot(x)
x = seq(2,80,4);plot(x)
x = rnorm(10);plot(x)
x = iris$Sepal.Length;plot(x)

#思考：plot画iris的前四列？
plot(iris[,1],col = iris[,5])
plot(iris[,2],col = iris[,5])
plot(iris[,3],col = iris[,5])
plot(iris[,4],col = iris[,5])

#当一个代码需要复制粘贴三次，就应该写成函数或使用循环

jimmy <- function(i){
  plot(iris[,i],col=iris[,5])
}

jimmy(1)
jimmy(2)
jimmy(3)
jimmy(4)
```

### 4.R包安装及使用

```{r}
# R包安装

options("repos"=c(CRAN="http://mirrors.tuna.tsinghua.edu.cn/CRAN/"))
options(BioC_mirror="http://mirrors.ustc.edu.cn/bioc/")
# 清华镜像
# http://mirrors.tuna.tsinghua.edu.cn/CRAN/
# http://mirrors.tuna.tsinghua.edu.cn/bioconductor/
  
# 中科大镜像
# http://mirrors.ustc.edu.cn/CRAN/
# http://mirrors.ustc.edu.cn/bioc/

install.packages("tidyr")
install.packages('BiocManager')
#BiocManager::install可以安装三个来源的包
BiocManager::install("ggplot2")
BiocManager::install("jmzeng1314/idmap1")
BiocManager::install("tidyr")
install.packages('devtools')
devtools::install_github("jmzeng1314/idmap1") #括号里写作者用户名加包名



  
library(tidyr)
require(tidyr)

# 分情况讨论

if(!require(stringr))install.packages("stringr")

# 获取帮助
?seq
library(stringr)
browseVignettes("stringr")
ls("package:stringr")


```

### 5.文件读写

```{r}
#文件读写部分
#1.读取ex1.txt
ex1 <- read.table("ex1.txt")
ex1 <- read.table("ex1.txt",header = T)
#2.读取ex2.csv
ex2 <- read.csv("ex2.csv")
ex2 <- read.csv("ex2.csv",row.names = 1,check.names = F)

#注意：数据框不允许重复的行名
rod = read.csv("rod.csv",row.names = 1)
rod = read.csv("rod.csv")

#3.读取soft.txt
soft <- read.table("soft.txt")
soft <- read.table("soft.txt",header = T,fill = T) #其实不对
soft2 <- read.table("soft.txt",header = T,sep = "\t")

#4.soft 的行数列数是多少？列名是什么
dim(soft)
colnames(soft)
#5.将soft导出为csv
write.csv(soft,file = "soft.csv")
#6.将soft保存为Rdata并加载。
save(soft,file = "soft.Rdata")
rm(list = ls())
load(file = "soft.Rdata")


```

### 6.基础作图

#### 1.作图分三类

```{r}


#1.基础包 略显陈旧 了解一下
plot(iris[,1],iris[,3],col = iris[,5]) 
text(6.5,4, labels = 'hello')

dev.off() #关闭画板

#2.ggplot2 中坚力量，语法有个性
library(ggplot2)
ggplot(data = iris)+
  geom_point(mapping = aes(x = Sepal.Length,
                           y = Petal.Length,
                           color = Species))

#3.ggpubr 新手友好型 ggplot2简化和美化 褒贬不一
library(ggpubr)
ggscatter(iris,
          x="Sepal.Length",
          y="Petal.Length",
          color="Species")

```

#### 2.ggplot2

```{r}
library(ggplot2)
#1.入门级绘图模板：作图数据，横纵坐标
ggplot(data = iris)+
  geom_point(mapping = aes(x = Sepal.Length,
                           y = Petal.Length))
#2.属性设置（颜色、大小、透明度、点的形状，线型等）

#2.1 手动设置，需要设置为有意义的值

ggplot(data = iris) + 
  geom_point(mapping = aes(x = Sepal.Length,
                           y = Petal.Length), 
             color = "blue")

ggplot(data = iris) + 
  geom_point(mapping = aes(x = Sepal.Length, y = Petal.Length), 
             size = 5,     # 点的大小5mm
             alpha = 0.5,  # 透明度 50%
             shape = 21)  # 点的形状

#2.2 映射：按照数据框的某一列来定义图的某个属性
ggplot(data = iris)+
  geom_point(mapping = aes(x = Sepal.Length,
                           y = Petal.Length,
                           color = Species))

## Q1 能不能自行指定映射的具体颜色？

ggplot(data = iris)+
  geom_point(mapping = aes(x = Sepal.Length,
                           y = Petal.Length,
                           color = Species))+
  scale_color_manual(values = c("blue","grey","red"))

## Q2 区分color和fill两个属性
### Q2-1 空心形状和实心形状都用color设置颜色
ggplot(data = iris)+
  geom_point(mapping = aes(x = Sepal.Length,
                           y = Petal.Length,
                           color = Species),
             shape = 17) #17号，实心的例子

ggplot(data = iris)+
  geom_point(mapping = aes(x = Sepal.Length,
                           y = Petal.Length,
                           color = Species),
             shape = 2) #2号，空心的例子
### Q2-2 既有边框又有内心的，才需要color和fill两个参数

ggplot(data = iris)+
  geom_point(mapping = aes(x = Sepal.Length,
                           y = Petal.Length,
                           color = Species),
             shape = 24,
             fill = "black") #24号，双色的例子

#3.分面
ggplot(data = iris) + 
  geom_point(mapping = aes(x = Sepal.Length, y = Petal.Length)) + 
  facet_wrap(~ Species) 
#双分面
dat = iris
dat$Group = sample(letters[1:5],150,replace = T)
ggplot(data = dat) + 
  geom_point(mapping = aes(x = Sepal.Length, y = Petal.Length)) + 
  facet_grid(Group ~ Species) 

#4.几何对象

#局部设置和全局设置

ggplot(data = iris) + 
  geom_smooth(mapping = aes(x = Sepal.Length, 
                          y = Petal.Length))+
  geom_point(mapping = aes(x = Sepal.Length, 
                           y = Petal.Length))

ggplot(data = iris,mapping = aes(x = Sepal.Length, y = Petal.Length))+
  geom_smooth()+
  geom_point()

#5.统计变换-直方图
View(diamonds)
table(diamonds$cut)

ggplot(data = diamonds) + 
  geom_bar(mapping = aes(x = cut))

ggplot(data = diamonds) + 
  stat_count(mapping = aes(x = cut))

#统计变换使用场景
#5.1.不统计，数据直接做图
fre = as.data.frame(table(diamonds$cut))
fre

ggplot(data = fre) +
  geom_bar(mapping = aes(x = Var1, y = Freq), stat = "identity")
#5.2count改为prop
ggplot(data = diamonds) + 
  geom_bar(mapping = aes(x = cut, y = ..prop.., group = 1))


#6.位置关系

# 6.1抖动的点图
ggplot(data = iris,mapping = aes(x = Species, 
                                 y = Sepal.Width,
                                 fill = Species)) + 
  geom_boxplot()+
  geom_point()

ggplot(data = iris,mapping = aes(x = Species, 
                                 y = Sepal.Width,
                                 fill = Species)) + 
  geom_boxplot()+
  geom_jitter()

# 6.2堆叠直方图
ggplot(data = diamonds) + 
  geom_bar(mapping = aes(x = cut,fill=clarity))

# 6.3 并列直方图
ggplot(data = diamonds) + 
  geom_bar(mapping = aes(x = cut, fill = clarity), position = "dodge")

#7.坐标系

#翻转coord_flip()

ggplot(data = mpg, mapping = aes(x = class, y = hwy)) + 
  geom_boxplot() +
  coord_flip()
#极坐标系coord_polar()
bar <- ggplot(data = diamonds) + 
  geom_bar(
    mapping = aes(x = cut, fill = cut), 
    width = 1
  ) + 
  theme(aspect.ratio = 1) +
  labs(x = NULL, y = NULL)
bar
bar + coord_flip()
bar + coord_polar()



```

#### 3.ggpubr

```{r}
# ggpubr 搜代码直接用，基本不需要系统学习

# sthda上有大量ggpubr出的图
library(ggpubr)
ggscatter(iris,x="Sepal.Length",
          y="Petal.Length",
          color="Species")

p <- ggboxplot(iris, x = "Species", 
               y = "Sepal.Length",
               color = "Species", 
               shape = "Species",
               add = "jitter")
p
my_comparisons <- list( c("setosa", "versicolor"), 
                        c("setosa", "virginica"), 
                        c("versicolor", "virginica") )
p + stat_compare_means(comparisons = my_comparisons)+ # Add pairwise comparisons p-value
  stat_compare_means(label.y = 9) 

```

#### 4.图片保存的三种方法

```{r}
#图片保存的三种方法

#1.基础包作图的保存
pdf("iris_box_ggpubr.pdf")
boxplot(iris[,1]~iris[,5])
text(6.5,4, labels = 'hello')
dev.off()

#2.ggplot系列图(包括ggpubr)通用的简便保存 ggsave
p <- ggboxplot(iris, x = "Species", 
               y = "Sepal.Length",
               color = "Species", 
               shape = "Species",
               add = "jitter")
ggsave(p,filename = "iris_box_ggpubr.png")

#3.eoffice包 导出为ppt,全部元素都是可编辑模式
library(eoffice)
topptx(p,"iris_box_ggpubr.pptx")

#https://mp.weixin.qq.com/s/p7LLLvzR5LPgHhuRGhYQBQ

```

### 7.tidyverse基础

#### 1.tidyverse软件安装

```{r}
options("repos" = c(CRAN="http://mirrors.tuna.tsinghua.edu.cn/CRAN/"))
if(!require(tidyr))install.packages("tidyr",update = F,ask = F)
if(!require(dplyr))install.packages("dplyr",update = F,ask = F)
if(!require(stringr))install.packages('stringr',update = F,ask = F)
if(!require(tibble))install.packages('tibble',update = F,ask = F)
library(tidyr)
library(dplyr)
library(stringr)
library(tibble)
#或者
if(!require(tidyr))install.packages("tidyverse",update = F,ask = F)
library(tidyverse)

```

#### 2.玩转字符串stringr

```{r}
rm(list = ls())
if(!require(stringr))install.packages('stringr')
library(stringr)

x <- "The birch canoe slid on the smooth planks."
x
### 1.检测字符串长度
str_length(x)
length(x)
### 2.字符串拆分
str_split(x," ")
x2 = str_split(x," ")[[1]];x2

y = c("jimmy 150","nicker 140","tony 152")
str_split(y," ")
str_split(y," ",simplify = T)

### 3.按位置提取字符串
str_sub(x,5,9)

### 4.字符检测
str_detect(x2,"h")
str_starts(x2,"T")
str_ends(x2,"e")
### 5.字符串替换
x2
str_replace(x2,"o","A")
str_replace_all(x2,"o","A")

### 6.字符删除
x
str_remove(x," ")
str_remove_all(x," ")

```

#### 3.玩转数据框dplyr

```{r}
test <- iris[c(1:2,51:52,101:102),]
rownames(test) =NULL # 去掉行名，NULL是“什么都没有”
test

# arrange，数据框按照某一列排序

library(dplyr)
arrange(test, Sepal.Length) #从小到大
arrange(test, desc(Sepal.Length)) #从大到小

# distinct，数据框按照某一列去重复
distinct(test,Species,.keep_all = T)

# mutate，数据框新增一列,或者修改原来地列
mutate(test, new = Sepal.Length * Sepal.Width)

# 连续的步骤

# 1.多次赋值，产生多个变量

x1 = filter(iris,Sepal.Width>3)
x2 = select(x1, Sepal.Length,Sepal.Width)
x3 = arrange(x2,Sepal.Length)

# 2.管道符号传递，简洁明了
x = iris %>% 
  filter(Sepal.Width>3) %>% 
  select(Sepal.Length,Sepal.Width)%>%
  arrange(Sepal.Length)

# 3. 嵌套，代码不易读
arrange(select(filter(iris,Sepal.Width>3),
               Sepal.Length,Sepal.Width),
        Sepal.Length)

```

## 




# 小技巧

### 一些报错的r包，可以使用conda安装

```{bash}
#例如，但会比较慢
conda install -c bioconda bioconductor-clusterprofiler
conda install bioconda::bioconductor-clusterprofiler
conda install -c conda-forge r-tidyverse
```

### 调用其他conda环境下的R包

```{r}
#方法一：指定R包位置去跨环境读取读取
#如果一個环境下安装没成功，另一个环境成功了，可以直接指定R包位置去跨环境读取读取
library("tidyverse", lib.loc="/home/hekun/anaconda3/envs/RStudio/lib/R/library/")
library("clusterProfiler", lib.loc="/home/hekun/anaconda3/envs/RStudio/lib/R/library/")
#方法二：临时添加.libPaths()的新的读取路径，重启R后失效
.libPaths()
.libPaths("/home/hekun/anaconda3/envs/RStudio/lib/R/library/")

#方法三：永久添加.libPaths()的新的读取路径，改.Rprofile，在.Rprofile中添加以下代码行来设置额外的库路径：
vim /home/hekun/.Rprofile
.libPaths(c("/home/hekun/anaconda3/envs/RStudio/lib/R/library", .libPaths()))
```

### 安装指定版本包

```{r}
#安装用来装旧包的包
install.packages("remotes")
#安装要装的已安装的包
remove.packages("matrixStats")
remotes::install_version("matrixStats", version = "1.1.0")


```

### R绘图指令

普通图绘制
```{r}
# 设置保存路径为PDF文件
pdf("samples_cor.pdf", width = 10, height = 10) 

# 绘制热图
pheatmap(sample_cor, 
         cluster_rows = F, cluster_cols = F, # 不聚类
         cellwidth = 15, cellheight = 15, # cell 大小
         border_color = "white", # 边框颜色
         fontsize = 8, # 字体大小
         angle_col = 45, # 列倾斜
         display_numbers = T, # 显示数值
         fontsize_number = 5) # 数值字体大小

# 关闭设备，确保文件保存
dev.off()


```

