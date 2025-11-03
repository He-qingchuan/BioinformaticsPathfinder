### 16非模式生物OrgDb构建



# 富集分析构建orgdb

## 0创建环境

```{bash}

conda create -n OrgDb eggnog-mapper pygtftk seqtk seqkit -y
conda activate OrgDb

#设置工作目录
cd workdir
#等号两边不能有空格，否则会报错。
workdir=$(pwd)

```

## 1提取最长转录本

```{bash}
# 进入目录
cd ./9Enrichment_Analysis/OrgDb/
#先进入
cp $workdir/1database/TAIR10/dna.fa.gz  ./
cp $workdir/1database/TAIR10/pep.fa.gz  ./
cp $workdir/1database/TAIR10/dna.gtf.gz ./
# 解压
gunzip dna.* 


# 统计GTF文件中的特征数量（查看是否注释到转录本）
# 使用dna.gtf作为输入
gtftk count -i dna.gtf

# 提取最长转录本并生成转录本ID到基因ID的映射文件
# -l 参数表示选择最长的转录本
# 管道操作：先提取最长转录本，然后筛选出transcript特征，最后制表输出关键字段
gtftk short_long -l -i dna.gtf | gtftk select_by_key -k feature -v transcript | gtftk tabulate -k transcript_id,gene_id > longest_mapid.txt

# 从蛋白序列文件中提取最长转录本对应的蛋白序列
# sed '1d' 删除第一行（通常是表头）
# cut -f 1 提取第一列（转录本ID）
# seqtk subseq 根据ID列表从蛋白序列文件中提取相应序列
sed '1d' longest_mapid.txt | cut -f 1 | seqtk subseq pep.fa - > longest_transcript.proteins.fa

# 将蛋白序列文件中的转录本ID替换为基因ID
# 使用seqkit的replace功能，基于映射文件(longest_mapid.txt)进行替换
# -p '^(\S+).*'  匹配整个序列ID,\S ：匹配任何一个非空白字符。这包括字母、数字、标点符号等，但不包括空格、制表符 (\t)、换行符 (\n) 等。+ ：量词。表示前面的元素（这里的 \S）必须出现一次或多次（至少一次）。
# -r '{kv}' 使用键值对替换
# -k 指定键值对文件

seqkit replace -p '^(\S+).*' -r '{kv}' -k longest_mapid.txt longest_transcript.proteins.fa > proteins.fa



# 检查文件大小
ls -lh dna.gtf
# 检查系统内存使用情况
free -h
# 尝试处理文件的一小部分进行测试
head -n 10000 dna.gtf > test.gtf
gtftk count -i test.gtf



```

## 2下载diamond数据库

```{bash}
download_eggnog_data.py -h
#可选参数:
#  -h, --help        显示此帮助信息并退出
#  -D                 不安装 diamond 数据库 (默认值: False)
#  -F                 安装新家族(novel families) diamond 及注释数据库，为 "emapper.py -m #novel_fams" 所必需 (默认值: False)
#  -P                 安装 Pfam 数据库，为从头(denovo)注释或重新比对(realignment)所必需 (默认#值: False)
#  -M                 安装 MMseqs2 数据库，为 "emapper.py -m mmseqs" 所必需 (默认值: False)
#  -H                 安装通过 "-d TAXID" 指定的 HMMER 数据库。为 "emapper.py -m hmmer -d #TAXID" 所必需 (默认值: False)
#  -d HMMER_DBS       要下载的 eggNOG HMM 数据库的物种分类编号(Tax ID)。例如，针对细菌#(Bacteria)使用 "-H -d 2"。
#                      若指定 "-H" 则此参数为必需。可用的物种分类编号(Tax IDs)可在
#                      http://eggnog5.embl.de/#/app/downloads 查询。(默认值: None)
#  --dbname DBNAME    要下载的 eggNOG HMM 数据库的物种分类编号(Tax ID)。例如，使用 "-H -d 2 --dbname 'Bacteria'" 
#                      将下载细菌(分类编号 2)的数据并存储到名为 'Bacteria' 的目录中 (默认值: None)
#  -y                 对所有询问默认回答 "yes" (默认值: False)
##  -f                 即使文件已存在也强制重新下载 (默认值: False)
#  -s                 模拟运行并打印命令。实际不会下载任何内容 (默认值: False)
#  -q                 静默模式 (默认值: False)
#  --data_dir         用于 DATA_PATH 的目录。(默认值: None)




##二选一就可以，其中hmm较慢，但结果相对更好


#可用的物种分类编号(Tax IDs)可在http://eggnog5.embl.de/#/app/downloads 查询
#物种的TaxIDs在https://www.ncbi.nlm.nih.gov/Taxonomy/
#下载hmm数据库
# 下载eggnog_db, eggnog_proteins.dmnd.gz和33090_hmms.tar.gz
download_eggnog_data.py --data_dir $workdir/9Enrichment_Analysis/OrgDb/eggnog_database -H -d 33090 --dbname Viridiplantae -y

nohup download_eggnog_data.py --data_dir /home/data/t150618/data/OrgDb/eggnog_database_hmm/ -H -d 33090 --dbname Viridiplantae -y &


#下载diamond数据库
download_eggnog_data.py --data_dir $workdir/9Enrichment_Analysis/OrgDb/eggnog_database -y -F

nohup download_eggnog_data.py --data_dir /home/data/t150618/data/OrgDb/eggnog_database_dia/ -y -F &

```

## 比对

```{bash}
#HMMER 搜索选项:
#  -d HMMER_DB_PREFIX, --database HMMER_DB_PREFIX
#                        指定序列搜索的目标数据库。可选值包括: euk（真核）, bact（细菌）, #arch（古菌）, 或服务器上加载的数据库,
#                        db.hmm:host:port (参见 hmm_server.py) (默认值: None)
#  --servers_list FILE   包含远程 hmmpgmd 服务器列表的 FILE 文件。文件中每行代表一个服务器，格式为 'host:port'。
#                        如果指定了 --servers_list，则将忽略 -d 选项中指定的主机(host)和端口(port)。 (默认值: None)
#  --qtype {hmm,seq}     输入数据(-i)的类型。 (默认值: seq)
#  --dbtype {hmmdb,seqdb}
#                        数据库(-db)中数据的类型。 (默认值: hmmdb)
#  --usemem              使用此选项通过 hmmpgmd 将整个数据库(-d)加载到内存中。如果 --dbtype 为 hmm，则数据库必须是经过
#                        hmmpress 处理的数据库。如果 --dbtype 为 seqdb，则数据库必须是使用 esl-reformat 创建的 HMMER 格式数据库。
#                        数据库将在执行后卸载。请注意，这仅适用于基于 HMMER 的搜索。要将 eggnog-mapper 注释数据库加载到内存中，请使用 --dbmem。 (默认值: False)




输入数据选项:
#  -i FASTA_FILE         输入FASTA文件，包含查询序列（默认为蛋白质；参见--itype和--translate）。除非使用-m no_search模式，否则为必需参数。(默认值: None)
#  --itype {CDS,proteins,genome,metagenome}
#                        输入(-i)文件中数据的类型。(默认值: proteins)
#  --translate           当--itype为CDS时，在搜索前将编码序列(CDS)翻译为蛋白质。
#                        当--itype为genome/metagenome且使用--genepred search时，将来自blastx命中的预测CDS翻译为蛋白质。(默认值: False)
#  --annotate_hits_table SEED_ORTHOLOGS_FILE
#                        使用包含4个字段的TSV格式表格进行注释，字段为：query（查询）, hit（命中）, evalue（期望值）, score（分数）。
#                        通常为之前emapper.py运行生成的.seed_orthologs文件。要求使用-m no_search模式。(默认值: None)
#  -c FILE, --cache FILE
#                        包含查询的注释和md5哈希值的缓存文件。如果使用-m cache模式则为必需参数。(默认值: None)
#  --data_dir DIR        eggnog-mapper数据库的路径。默认为"data/"或在环境变量EGGNOG_DATA_DIR中指定的路径。(默认值: None)









##搜索比对，使用diamond，e值太大的话会有误差，e值可以先设置大一些，观察以后再筛选合适的值
#使用proteins.fa
nohup emapper.py -i proteins.fa -o pep --dmnd_db ../9Enrichment_Analysis/OrgDb/eggnog_database/eggnog_proteins.dmnd  --data_dir $workdir/9Enrichment_Analysis/OrgDb/eggnog_database/ --cpu 10 --output_dir $workdir/9Enrichment_Analysis/OrgDb/output --override -m diamond --seed_ortholog_evalue 1e-5  >emapper.log&

#搜过比对，使用hmm，慢，内存要求太大

nohup emapper.py -m hmmer --data_dir $workdir/9Enrichment_Analysis/OrgDb/eggnog_database/ -d Viridiplantae -i proteins.fa -o output --cpu 10 --dbmem --excel --override --seed_ortholog_evalue 1e-10 --output_dir $workdir/9Enrichment_Analysis/OrgDb/output >emapper.log&
```

## 构建orgdb

```{r}
#安装emcp依赖，进入R
options(repos="http://mirrors.tuna.tsinghua.edu.cn/CRAN/")
options(BioC_mirror="http://mirrors.tuna.tsinghua.edu.cn/bioconductor/")

if (!requireNamespace("devtools", quietly = TRUE)) {install.packages("devtools")}
if (!requireNamespace("tidyverse", quietly = TRUE)) {install.packages("tidyverse")}
if (!requireNamespace("argparser", quietly = TRUE)) {install.packages("argparser")}
if (!requireNamespace("seqinr", quietly = TRUE)) {install.packages("seqinr")}
if (!requireNamespace("formattable", quietly = TRUE)) {install.packages("formattable")}
if (!requireNamespace("pkgbuild", quietly = TRUE)) {install.packages("pkgbuild")}
if (!requireNamespace("BiocManager", quietly = TRUE)) {install.packages("BiocManager")}
if (!requireNamespace("AnnotationForge", quietly = TRUE)) {BiocManager::install("AnnotationForge")}
if (!requireNamespace("clusterProfiler", quietly = TRUE)) {BiocManager::install("clusterProfiler")}

#这次安装所有依赖包很麻烦，换了好几个版本的R，最终在R=4.3.3时，所有包能同时安装，这也说明如果有些报错，不一定是服务器系统的问题，很可能是版本的问题
#如果一個环境下安装没成功，另一个环境成功了，可以直接制定R包位置去跨环境读取读取
library("tidyverse", lib.loc="/home/hekun/anaconda3/envs/RStudio/lib/R/library/")
library("clusterProfiler", lib.loc="/home/hekun/anaconda3/envs/RStudio/lib/R/library/")

#如果使用服务器报错了一些包，可以使用conda安装，例如，但会比较慢
#conda install -c bioconda bioconductor-clusterprofiler
#conda install bioconda::bioconductor-clusterprofiler
#conda install -c conda-forge r-tidyverse

#加载包查看是否成功安装
library(tidyverse, quietly = TRUE)
library(argparser, quietly = TRUE)
library(seqinr, quietly = TRUE)
library(formattable, quietly = TRUE)
library(pkgbuild, quietly = TRUE)
library(AnnotationForge, quietly = TRUE)
library(clusterProfiler, quietly = TRUE)
```

```{bash}
#备份原始文件
cp "/u3/hekun/orgDb/output_diamond/pep.emapper.annotations" "/u3/hekun/orgDb/output_diamond/pep.emapper.annotations.bak"

    



mkdir $workdir/egg2ord
mkdir $workdir/egg2ord/orgdb
cd $workdir/egg2ord
#下载emcp
git clone http://git.genek.cn:3333/zhxd2/emcp.git
#运行#有两个位置参数，先写egg的注释文件，再写最长转录本的蛋白文件
cd $workdir/egg2ord/orgdb
Rscript /u3/hekun/orgDb/egg2ord/emcp/emapperx.R ../../output_diamond/pep.emapper.annotations /u3/hekun/orgDb/genome/gene.pep.fasta

Rscript /u3/hekun/orgDb/egg2ord/emcp/emapperx.R ../../output_hmm/pep.emapper.annotations /u3/hekun/orgDb/genome/gene.pep.fasta








```

```{r}
#加载包
library(org.My.eg.db, lib.loc = "./R_Library/") 


columns(org.My.eg.db)

library(AnnotationDbi)
# 假设 org.My.eg.db 是已经加载的 OrgDb 数据库对象
key_list <- keys(org.My.eg.db)

# 查看所有列的注释信息
gene_info <- AnnotationDbi::select(org.My.eg.db, keys = head(key_list), columns = keytypes(org.My.eg.db), keytype = "GID")
head(all_gene_info)


gene_symbol_info <- AnnotationDbi::select(org.My.eg.db, keys = key_list, columns = "Gene_Symbol", keytype = "GID")
head(gene_symbol_info)



```


