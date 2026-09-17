---
title: "Linux入门基础"

date: "2025-08-12"
output: html_document
---

# Linux入门

## 01_Linux基础

### 登录服务器

```{bash}
用户名、密码和ip地址，登录方式为：`ssh   用户名@ip地址`，如
ssh  qingchuan28@94.191.82.93
#回车，然后输入密码
ssh -p 21041 t150618@biotree.top
```

### 查看帮助文档

```{bash}
#man 命令，help 命令，或者某个命令的  --help  参数
man  ls		## 用 man 命令查看 ls 命令的帮助文档	
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
conda install -y  trim-galore  hisat2   multiqc  samtools=1.14  salmon=1.4.0 fastp fastqc
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

### 

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

