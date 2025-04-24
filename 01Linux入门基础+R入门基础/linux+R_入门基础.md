---
title: "LINUX+R"

date: "2024-10-12"
output: html_document
---

```{r setup, include=FALSE}
knitr::opts_chunk$set(echo = TRUE)
```

# Linux入门

## 01_Linux基础

### 登录服务器

```{bash}
用户名、密码和ip地址，登录方式为：`ssh   用户名@ip地址`，如：
ssh  vip28@94.191.82.93
#回车，然后输入密码
```

### 查看帮助文档

```{bash}
#man 命令，help 命令，或者某个命令的  --help  参数
man  ls		## 用 man 命令查看 ls 命令的帮助文档
help  ls	## 用 help 命令查看 ls 命令的帮助文档	
ls  --help	## 用 --help 参数查看 ls 命令的帮助文档
```

### 常见的环境变量：\$HOME ，PS1 \$PATH

```{bash}
#`$HOME` 记录了用户的家目录所在的路径

#`PS1` 命令行配色
$ echo  $HOME
/trainee2/vip28

$ echo  $PS1
\[\033]2;\h:\u \w\007\033[33;1m\]\u \033[35;1m\t\033[0m \[\033[36;1m\]\w\[\033[0m\]\n\[\e[32;1m\]$ \[\e[0m\]

$ echo  $PATH
/trainee2/vip28/miniconda3/condabin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin

```

#### 修改命令行配色

```{bash}
#感兴趣的自行搜索
echo  'export PS1="\[\033]2;\h:\u \w\007\033[33;1m\]\u \033[35;1m\t\033[0m \[\033[36;1m\]\w\[\033[0m\]\n\[\e[32;1m\]$ \[\e[0m\]" ' >> ~/.bashrc
source  ~/.bashrc
#`~/.bashrc`：系统配置文件，包含专用于你的 bash shell 的bash信息、设置，每次登录或打开新的 shell 时，该文件会被自动读取和执行。
```

#### PATH

```{bash}
#`$PATH`：输入命令时Linux会去查找PATH里面记录的路径，如果命令存在某一个路径中，就可以成功调用。

#`<PATH1>:<PATH2>:<PATH3>:------:<PATHN>`

#打个比方，PATH 是一个工具箱，有很多层（对应很多个路径），每一层放着各式各样的工具（对应各种命令）。
$ echo $PATH
/trainee2/vip28/miniconda3/condabin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin

# 可以把 : 替换成换行符 \n 
$ echo $PATH | tr ':'  '\n'
/trainee2/vip28/miniconda3/condabin
/usr/local/sbin
/usr/local/bin
/usr/sbin
/usr/bin
/sbin
/bin
/usr/games
/usr/local/games
/snap/bin

# 比如 ls 命令存在
$ ls  
$ which ls 
/bin/ls

#### 如何管理 PATH

#如何管理 `$PATH`：理解环境变量 `$PATH`  是非常重要的，对后续的环境和软件管理都非常重要。

#推荐方法：在自己家目录下创建一个 `~/bin/` 文件夹并将其添加到环境变量，后续安装软件，就将软件的可执行文件拷贝或软链接（绝对路径）到这个 bin 文件夹：
mkdir  ~/bin 
echo  'export "PATH=~/bin:$PATH" ' >> ~/.bashrc 
source  ~/.bashrc
```

### Linux常用命令

#### ls 命令

```{bash}
#列出目录文件情况
ls				## 列出当前目录的文件
ls  ./			## 同上，‘.’号代表当前目录
ls  ./*txt		## 列出当前目录下以 txt 结尾的文件
ls  ../ 		## 列出上层目录的文件
ls  -a			## 列出当前目录下的所有文件，包括隐藏文件
ls  -l			## 列出当前目录下文件的详细信息
ll				## ls  -la 的简写
ls  -lh 		## 加上 -h 参数，以 K、M、G 的形式显示文件大小
ls  -lh  /		## 列出根目录下文件的详细信息
```

#### cd 命令

```{bash}
cd  ..       ## 切换到上层目录，相对路径
cd  /        ## 切换到根目录
cd  /teach/  ## 切换到根目录下的teach，绝对路径
cd  -        ## 返回上一次的工作目录
cd  ~        ## 回到用户家目录
cd           ## 同上，回到用户家目录
```

#### mkdir

```{bash}
# 创建目录
mkdir dir0
ls
mkdir dir0/sub1/sub2
ls
ls dir0
mkdir -p dir0/sub1/sub2
ls dir0
ls dir0/sub1/
mkdir -p  test{1..3}/test{1..3}
tree
```

#### touch

```{bash}
ls
touch  file.txt  new.txt
ls
touch  file{1..5}
ls
```

#### rm

```         
rm  -i  file.txt
ls  file*
rm  file*
rm  -rf  test1
```

#### mv

```{bash}
mv  file1   Data/file2
```

#### cp

```{bash}
cp   readme.txt   Data/
mkdir  dir0
cp  -r  dir0  Data/

```

#### ln

```{bash}
ln -s /teach/software/Miniconda3-latest-Linux-x86_64.sh  ./

```

#### tar

```{bash}
## 解压
tar  -zxvf  Data.tar.gz
## 压缩
tar  -zcvf  Data.tar.gz    Data  ...

```

#### cat

```{bash}
cat  readme.txt
cat  -n  readme.txt
## 写入文件
cat >file
Welcome to Biotrainee() !
^C			## 这里是按Crtl  C
## 查看
cat file
Welcome to Biotrainee() !

```

#### head、tail

```{bash}
head  -n  20  Data/example.fq
## 查看 .bashrc 的最后 10 行
tail  ~/.bashrc
## 查看第20行
head  -n  20  Data/example.fq | tail -1

```

#### less

按 q 退出

```{bash}
less  Data/example.fq
less -S Data/example.fq
less -N Data/example.fq
zless -N Data/reads.1.fq.gz

```

#### wc

```{bash}
cat -n readme.txt  # 显示readme.txt文件内容并加上行号
cat readme.txt | wc  # 输出readme.txt文件的单词数、行数和字节数
wc -l readme.txt  # 只输出readme.txt文件的行数
```

#### cut

```{bash}
less -S Data/example.gtf | cut -f 1,3-5  # 显示example.gtf文件的第1列和第3到5列
less -S Data/example.gtf | cut -d 'h' -f 1  # 使用'h'作为分隔符，显示example.gtf文件的第一列
```

#### sort

```{bash}
less -S Data/example.gtf | sort -k 4 | less -S  # 按第4列排序example.gtf文件内容后显示
less -S Data/example.gtf | sort -n -k 4 | less -S  # 按第4列数值排序example.gtf文件内容后显示

```

#### uniq

```{bash}
less -S Data/example.gtf | cut -f 3 | sort | uniq -c  # 统计example.gtf文件第3列的唯一值及其出现次数

```

#### paste

```{bash}
less -S Data/example.fq | paste - - - | less -S  # 将example.fq文件的每一行与三个空输入合并成一行后显示
paste file1 file2  # 将file1和file2的每一行合并成一行
```

#### tr

```{bash}

cat readme.txt | tr 'e' 'E'  # 将readme.txt文件中的'e'替换为'E'
cat readme.txt | tr '\n' '\t'  # 将readme.txt文件中的换行符替换为制表符
cat readme.txt | tr -d 'e'  # 删除readme.txt文件中的所有'e'
```

#### grep

```{bash}
#多看看生信技能书的三驾马车
# grep：一种强大的文本搜索工具，它能使用正则表达式匹配模式搜
# 索文本，并把匹配的行打印出来
# 格式：grep [options] pattern file
# 常见参数：
# -w：word 精确查找某个关键词 pattern
# -c：统计匹配成功的行的数量
# -v：反向选择，即输出没有没有匹配的行
# -n：显示匹配成功的行所在的行号
# -r：从目录中查找pattern
# -e：指定多个匹配模式
# -f：从指定文件中读取要匹配的 pattern
# -i：忽略大小写

grep Biotrainee -r ./  # 在当前目录下递归搜索包含'Biotrainee'的所有文件
less -S Data/example.fq | grep 'gene'  # 在example.fq文件中搜索包含'gene'的行
less -S Data/example.fq | grep -w 'gene'  # 在example.fq文件中搜索完全匹配'gene'的行
less -S Data/example.fq | grep -v -w 'gene'  # 在example.fq文件中搜索不包含'gene'的行

```

#### 正则表达式

```{bash}
# ^ 行首
# $ 行尾
# . 换行符之外的任意单个字符
# ? 匹配之前项0次或者一次
# + 匹配1次或者多次
# * 匹配0次或者多次
# {n} 匹配n次
# {n,} 匹配至少n次
# {m,n} 至少m,最多n
# [] 匹配任意一个
# [^] 排除字符
# | 或者
cat readme.txt  | grep '^T'  # 匹配以'T'开头的行
cat readme.txt  | grep ')$'  # 匹配以')'结尾的行
cat readme.txt  | grep 'f.ee'  # 匹配形如'fee', 'f1ee', 'f2ee'等的行，`.` 表示任意单个字符。
cat readme.txt  | grep 'f\?ee'  # 匹配'fee'或'free'， `\?` 表示零个或一个前面的字符。
cat readme.txt  | grep 're\+'  # 匹配一个或多个'r'后跟'e'，`\+` 表示一个或多个前面的字符。
cat readme.txt  | grep [bB]  # 匹配包含'b'或'B'的行，`[bB]` 表示括号内的任何一个字符。
```

#### sed

```{bash}
# 在readme.txt的第一行前插入一行 "Welcome to Biotrainee()"
cat readme.txt | sed '1i Welcome to Biotrainee() '

# 在readme.txt的第一行后追加一行 "Welcome to Biotrainee()"
cat readme.txt | sed '1a Welcome to Biotrainee() '

# 将readme.txt的第一行替换为 "Welcome to Biotrainee()"
cat readme.txt | sed '1c Welcome to Biotrainee()'

# 将readme.txt中的所有 "is" 替换为 "IS"，s/is/IS/g 表示全局替换（g 代表全局）。
cat readme.txt | sed 's/is/IS/g'

# 删除readme.txt中的所有空行，s/is/IS/g 表示全局替换（g 代表全局）。
cat readme.txt | sed '/^$/d'

# 将readme.txt中的所有 'a' 替换为 'A'，'b' 替换为 'B'，'c' 替换为 'C'，y/abc/ABC/ 表示将 abc 中的每个字符替换为 ABC 中对应的字符。
cat readme.txt | sed 'y/abc/ABC/'
```

#### awk

```{bash}
# 打印 example.gtf 文件的第9列
less -S Data/example.gtf | awk '{print $9}' | less -S

# 打印 example.gtf 文件的第9列和第10列
less -S Data/example.gtf | awk '{print $9, $10}' | less -S

# 使用制表符作为分隔符，打印 example.gtf 文件的第9列
less -S Data/example.gtf | awk -F '\t' '{print $9}' | less -S

# 如果第3列是 "gene"，则打印整行
less -S Data/example.gtf | awk '{if($3 == "gene") print $0}' | less -S

# 如果第3列是 "gene"，则打印整行；否则打印 "$3 is not gene"
less -S Data/example.gtf | awk '{if($3 == "gene") {print $0} else {print $3 " is not gene "}}' | less -S

# 如果行中包含 "gene"，则打印整行
less -S Data/example.gtf | awk '/gene/{print $0}' | less -S

# 在开始时打印 "find UTR feature"，如果行中包含 "UTR" 则打印整行，在结束时打印 "end"，BEGIN{print "find UTR feature"} 在开始时打印 "find UTR feature"。/UTR/{print $0} 如果行中包含 "UTR"，则打印整行。END{print "end"} 在结束时打印 "end"。
less -S Data/example.gtf | awk 'BEGIN{print "find UTR feature"} /UTR/{print $0} END{print "end"}'

# 使用制表符作为分隔符，打印 example.gtf 文件的第9列，BEGIN{FS="\t"} 设置制表符作为分隔符。
less -S Data/example.gtf | awk 'BEGIN{FS="\t"} {print $9}' | less -S

# 使用制表符作为输入和输出分隔符，将第3列中的 "gene" 替换为 "Gene"，然后打印整行，BEGIN{FS="\t";OFS="\t"} 设置制表符作为输入和输出分隔符。，{gsub("gene", "Gene", $3); print $0} 将第3列中的 "gene" 替换为 "Gene"，然后打印整行。
less -S Data/example.gtf | awk 'BEGIN{FS="\t";OFS="\t"} {gsub("gene", "Gene", $3); print $0}' | less -S

```

### Linux常用命令场景练习

#### 场景一：pwd、cd、ls 练习

> 场景意图：
>
> 1.  练习一次进入多层文件夹
>
> 2.  习惯用tab键补全文件和文件夹
>
> 3.  熟悉命令的各种参数
>
> 4.  熟悉文件权限

1.  进入根目录下的var文件夹下的spool文件夹，并打印出当前目录位置, 查看当前文件夹内容

```{bash}
cd /var/spool/
pwd
ls
```

2.  一步回到家目录(提供至少3种解法)

```{bash}
cd ~
cd 
cd /trainee2/Mar25 # 此处替换成自己的家目录路径
```

3.  一步返回刚才的文件夹（提示：与“-”有关）

```{bash}
cd -
```

4.  查看家目录下的所有文件及文件夹的详细信息，回答：.bashrc文件的权限是？（谁可读、谁可写、谁可执行）

```{bash}
ls -la # 或者ll -a
.bashrc文件所属者可读可写不可执行，所属组和其他人均只可读不可写不可执行
```

5.  一步进入家目录的上层目录下的你的编号±1的用户的目录(如果不满足条件，则随机进入两个即可)

```{bash}
cd ../Mar24/
cd ../Mar26/
# 此处以Mar25为例, 做题时替换成你自己的用户名即可。
```

#### 场景二：mkdir、touch、tree练习

> 出题意图：
>
> 1.  学会批量创建文件和文件夹
> 2.  熟悉mkdir的选项
> 3.  熟悉tree命令

1.  在当前目录创建形如 1/2/3/4/5/6/7/8/9 格式的文件夹系列

```{bash}
mkdir -p 1/2/3/4/5/6/7/8/9
```

2.  在不使用cd命令的前提下，在上一题创建的1/2/3/4/5/6/7/8/9下 创建文本文件findMe.txt

```{bash}
touch 1/2/3/4/5/6/7/8/9/findMe.txt
# 此处记得用tab补齐噢
```

3.  用一条命令批量创建testDir1\~10这十个文件夹

```{bash}
mkdir testDir{1..10}
```

4.  用一条命令在每个testDir1\~10文件夹中创建一个myFile文件

```{bash}
touch ./testDir{1..10}/myFile
```

5.  将自己的家目录文件夹以树的结构展示出来

```{bash}
tree ~
# 或者先cd，后tree . 也可。 但是不够简洁
```

#### 场景三：mv、cp和rm

> 出题意图：
>
> 1.  熟悉并分辨mv的移动和重命名功能
> 2.  熟悉cp命令
> 3.  熟悉rm命令的交互式和递归删除

准备工作：创建两个文件file1和file2，创建两个文件夹myDir1和myDir2。

1.  把file1重命名成file3

```{bash}
mv file1 file3
```

2.  把file2重命名成file3

```{bash}
mv file2 file3
```

3.  把file3移动进myDir1

```{bash}
mv file3 myDir1
```

4.  把myDir1移动进myDir2

```{bash}
mv myDir1 myDir2
```

5.  把myDir2重命名成myDir3

```{bash}
mv myDir2 myDir3
```

6.  用一行命令将1/2/3/4/5/6/7/8/9下的findMe.txt文件复制到当前文件夹并命名成findMe

```{bash}
cp 1/2/3/4/5/6/7/8/9/findMe.txt ./fineMe
```

7.  把场景二中创建的1/2/3/4/5/6/7/8/9和findMe.txt文件用交互式的方式删除

```{bash}
rm -ri 1
```

#### 场景四：ln 练习

> 出题意图：
>
> 学会使用ln -s创建软连接

将/home/t_linux/Miniconda3-latest-Linux-x86_64.sh文件链接至自己的家目录

```{bash}
cd ~
ln -s /home/t_linux/Miniconda3-latest-Linux-x86_64.sh .
```

#### 场景五：tar练习

> 学会用tar进行压缩和解压

1.  用tar将家目录下的readme.txt文件和软连接过来的Miniconda3-latest-Linux-x86_64.sh文件创建压缩成test.tar.gz文件

```{bash}
tar -zcvf test.tar.gz readme.txt Miniconda3-latest-Linux-x86_64.sh
```

2.  创建一个test文件夹（若已存在则不用创建），将test.tar.gz文件移动到test中并解压开。

```{bash}
mkdir test
mv test.tar.gz
tar -zxvf test.tar.gz
```

## 02Linux之安装conda

### 1下载

```{bash}
cd ~
wget -c https://repo.anaconda.com/archive/Anaconda3-2024.06-1-Linux-x86_64.sh
#在conda文件的目录下输入命令安装，一路回车，直到他要求输入yes
bash Anaconda3-2024.06-1-Linux-x86_64.sh
#在末尾添加环境变量
vim ~/.bashrc
export PATH=~/anaconda3/bin:$PATH
#刷新环境变量
source ~/.bashrc
#最后conda -V要是正常就安装成功了
```

### 2配置镜像源

```{bash}
vim ~/.condarc
channels:
  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free/
  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main/
  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/pytorch/
  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/msys2/
show_channel_urls: true
 
ssl_verify: true
allow_conda_downgrades: true


####
## 配置镜像

# 下面四行配置北京外国语大学的conda的channel地址（首选）
conda config --add channels https://mirrors.bfsu.edu.cn/anaconda/pkgs/main/ 
conda config --add channels https://mirrors.bfsu.edu.cn/anaconda/cloud/conda-forge/ 
conda config --add channels https://mirrors.bfsu.edu.cn/anaconda/cloud/bioconda/ 
conda config --set show_channel_urls yes 

# 下面这四行配置清华大学的conda的channel地址（首选北外，如果体验不好再换成清华）
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main/
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge/
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/bioconda/
conda config --set show_channel_urls yes

# 如果需要官方频道，可以添加下面这两行配置官网的channel地址（不推荐）
conda config --add channels conda-forge 
conda config --add channels bioconda

# 删除defaults频道
sed -i '/defaults/d' ~/.condarc

## 配置镜像成功
# 查看配置结果
cat ~/.condarc
```

### 3创建环境，并安装rstudio

```{bash}
conda create -n rstudio r=4.2.0 -y #有版本要求，试了别的版本不成功
conda activate rstudio
#安装RStudio：
conda install -c r rstudio --yes
#安装R包
options(repos="http://mirrors.tuna.tsinghua.edu.cn/CRAN/")
options(BioC_mirror="http://mirrors.tuna.tsinghua.edu.cn/bioconductor/")
install.packages("devtools")
install.packages("BiocManager")
#运行
rstudio
```

## 03Linux之软件安装

### 创建小环境

```{bash}
# 创建名为rna的软件环境来安装转录组学分析的生物信息学软件
conda create -y -n  rna  python=3.7
# 创建小环境成功，并成功安装python3版本
# 每建立一个小环境，安装一个python=3的软件作为依赖

# 查看当前conda环境
conda info -e
conda env list

# 每次运行前，激活创建的小环境rna
conda activate rna

# 退出小环境
conda deactivate
```

### 在小环境中安装生信软件——使用connda和mamba

```{bash}
# 激活环境
#注：软件都要安装在小环境中，不要安装在 base 
### rna环境
conda activate rna
# 安装 fastqc 软件
conda  install  fastqc

# 调出帮助文档
fastqc --help

# 可以指定软件版本
conda install -y samtools=1.14 

# aspera 
conda install -y -c hcc aspera-cli
ascp --help

# 可以一次安装多个软件
conda install -y python=3.7 libstdcxx-ng=9.1.0 trim-galore  hisat2  subread  multiqc  samtools=1.14  salmon=1.4.0 fastp fastqc
# mamba install -y python=3.7 libstdcxx-ng=9.1.0 trim-galore  hisat2  subread  multiqc  samtools=1.14  salmon=1.4.0 fastp fastqc

## 不是通过软件名来调用帮助文档，而是软件的命令
# sra-tools
prefetch --help
fastq-dump --help
which prefetch

#  trim-galore
trim_galore --help

# hisat2
hisat2 --help

# subread
featureCounts --help

# multiqc
multiqc --help

# samtools
samtools --help

# salmon
salmon --help

# fastp
fastp --help

### R4环境

# 创建R4环境
conda create -y -n R4 python=3.8

# 激活R4环境
conda activate R4

# (可选步骤：在R4里安装mamba)
# conda install mamba

# 安装R语言本体
conda install -y r-base=4.1.2
## 或者使用mamba安装： mamba install -y r-base=4.1.2

# 安装R语言软件包
conda install -y r-getopt r-tidyverse r-ggplot2=3.3.5 bioconductor-limma bioconductor-edger bioconductor-deseq2 bioconductor-clusterprofiler bioconductor-org.hs.eg.db=3.13.0
## 或者使用mamba安装：mamba install -y r-getopt r-tidyverse r-ggplot2=3.3.5 bioconductor-limma bioconductor-edger bioconductor-deseq2 bioconductor-clusterprofiler bioconductor-org.hs.eg.db=3.13.0
```

```{bash}
#Q: 如何验证R语言的包安装情况？
#A: 进入R语言环境中用`library()` 
# 输入R进入R语言的交互
R
#在R语言里验证安装包：
library(getopt)
library(tidyverse)
library(ggplot2)
library(limma)
library(edgeR)
library(DESeq2)
library(clusterProfiler)
library(org.Hs.eg.db)
<!-- Q: 如何知道这些包到底叫啥？哪儿该大写哪儿该小写？ -->

<!-- A: [Bioconductor - Home](https://bioconductor.org/) 在Bioconductor的官网搜索即可。 -->
```

### 在小环境中安装生信软件——直接导入yaml配置文件以安装软件

```{bash}
conda env create -n rna -f rna.yaml
# 如果有mamba的话可以用mamba安装
# mamba env create -n rna -f rna.yaml
conda env create -n R4 -f R4.yaml
```

### conda其他用法更新软件：conda update 软件名，卸载软件，删除环境，克隆环境，查找软件

```{bash}
# 更新软件：conda  update  软件名
# 卸载软件：conda  removRe  软件名
# 删除环境：conda  remove  -n   环境名
# 克隆环境：conda  create –n 新环境名 –clone  旧环境名
# 查找软件：conda  search  软件名
# 查找软件常用的链接：
# 
# - https://anaconda.org/search
# 
# - [https://bioconda.github.io](https://bioconda.github.io/)[/](https://bioconda.github.io/)

```

### 手动安装安装软件以及软连接

```{bash}
mkdir ~/biosoft 
cd ~/biosoft
# wget -c https://cloud.biohpc.swmed.edu/index.php/s/oTtGWbWjaxsQ2Ho/download -O hisat2-2.2.1-Linux_x86_64.zip
ln  -s  /teach/software/hisat2-2.2.1-Linux_x86_64.zip  ./
unzip hisat2-2.2.1-Linux_x86_64.zip
cd hisat2-2.2.1/
./hisat2 --help
# echo 'export PATH="${HOME}/biosoft/hisat2-2.2.1/:$PATH" ' >> ~/.bashrc 
ln  -s  ~/biosoft/hisat2-2.2.1/hisat2*   ~/bin/
#也可以将其他环境下的R或者其他语言拷到~/bin/，可以使得在家目录也可以运行
ln -s ~/anaconda3/envs/rstudio/bin/R ~/bin/

```

## Linux系统环境+Linux编程

### 文件系统结构

```{bash}
/ 		虚拟目录的根目录。通常不会在这里存储文件
/bin	二进制目录，存放许多用户级的GNU工具
/boot	启动目录，存放启动文件
/dev	设备目录，Linux在这里创建设备节点
/etc	系统配置文件目录
/home	主目录，Linux在这里创建用户目录
/lib	库目录，存放系统和应用程序的库文件
/media	媒体目录，可移动媒体设备的常用挂载点
/root	root用户的主目录
/sbin	系统二进制目录，存放许多GNU管理员级工具
/run	运行目录，存放系统运作时的运行时数据
/tmp	临时目录，可以在该目录中创建和删除临时工作文件
/usr	用户二进制目录，大量用户级的GNU工具和数据文件都存储在这里
```

### 查看系统资源

```{bash}

查看CPU信息：lscpu
查看内存信息：free  -h
查看硬盘信息：df  -h
查看文件大小：du  -h  -d  1
查看文件大小：du  -h  -d  1
查看系统进程：top 或者 ps -ef 或者 jobs

```

### 变量

```{bash}

环境变量、状态变量、位置参数变量、自定义变量，调用变量时，要在变量前面加一个 `$ `符号

环境变量：用于存储有关shell会话和工作环境的系统变量

状态变量：用于记录命令的运行结果

位置参数变量：用于用于向命令或程序脚本中传递信息

自定义变量：由用户自行定义的变量，可用于用户编写的脚本，多个命令间的值传递等
```

### 结构化语句

#### 条件语句 if

```{bash}
#有头有尾，一个` if ` 就要对应一个 ` fi ` 。有三种结构：
# 1
if [ condition ]
then
	commands
fi

# 2
if [ condition ]
then
	commands
else
	commands
fi

# 3
if [ condition ]
then
	commands
else
	if [ condition ]
	then
		commands
	fi
fi
# (else if 可以缩写为 elif )
if [ condition ]
then
	commands
elif [ condition ]
	then
		commands
	fi
fi

#示例：
# 数值判断
if [ 1 -eq 1 ]
then
  echo  "Welcome to Biotrainee() !"
else
  echo  "**************"
fi

# 结合状态参数 $?
if [ $? -eq 0 ]
then
  touch  ok.txt
fi

# 文件判断
if [ ! -f ok.txt ]
then
  touch  ok.txt
fi

```

#### for 循环语句

```{bash}
for i in  1 2 3 4 5 
do
  echo ${i} "Welcome to Biotrainee() !"
done

for i in {1..10}
do
  touch  file${i}
done

list="CDS exon gene start_codon stop_codon transcript UTR"
for i in ${list}
do
  echo  "This feature is ${i}"
done
```

#### while 循环

```{bash}
ls file* | while  read  id;
do 
  mv ${id} ${id}.txt ; 
done


ls  file* > config
cat config | while  read id
do 
  mv  ${id}  ${id%.txt}
done
```

#### 结构化语句练习题

```{bash}
id=example
fastqc ~/Data/${id}.fq
if [ $? -eq 0 ]
then
  echo "yes"
else 
  echo "no"
fi
```

```{bash}
touch  file{1..10}

ls file* | while read id
do 
  echo  "xxx"  > ${id}
done

```

### shell 脚本以及脚本运行

#### test.sh

```{bash}
$ vim  test.sh
#!/bin/bash
echo "Welcome to Biotrainee() !"

$ bash  test.sh

# 1标准输出  和  2标准误输出，但有些软件不规范，所有输出都在2
$ bash  test.sh  1>test.log  2>&1


# 可执行权限
$ ls -lh test.sh 

$ chmod  764 test.sh 

$ ls -lh test.sh 

# 路径调用可执行文件
./test.sh  

```

#### test2.sh

```{bash}
$ cat  test2.sh
#!/bin/bash
cat  $1

$ bash  test2.sh  readme.txt

```

#### test3.sh

```{bash}
$ cat  test3.sh
#!/bin/bash
echo  "Start"
sleep  100s
echo  "End"



```

#### shell脚本后台运行

```{bash}
$ bash  test3.sh  

$ nohup  bash  test3.sh  &

$ nohup  bash  test3.sh   1>test3.log  2>&1  &

$ top

$ ps -ef | grep test3

```

### 在 Linux 中使用其他编程语言

#### R 语言脚本

```{bash}
$ cat test.R 
#!/usr/bin/Rscript
a = 1:10
paste0("gene",a)

$ Rscript test.R 
 [1] "gene1"  "gene2"  "gene3"  "gene4"  "gene5"  
 [6] "gene6"  "gene7"  "gene8"  "gene9"  "gene10"

```

#### Python 脚本

```{bash}
$ cat test.py 
#!/usr/bin/python3

print("Hello World")

$ python3 test.py 
Hello World

```

### 扩展:自己写的命令实现行列转换，功能类似 R 语言中的 `t( )` 函数

```{bash}
$ cat  > row2col
awk 'BEGIN{FS="\t";OFS="\t"}{i=1;while(i <= NF){col[i]=col[i] $i "\t";i=i+1}} END {i=1;while(i<=NF){print i,col[i];i=i+1}}'

$ chmod 764  row2col

$ mv  row2col  ~/bin

$ head -n 2 ~/Data/example.gtf  |  row2col
```

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

