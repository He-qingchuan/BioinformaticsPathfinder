##
## 转录组测序分析
## https://github.com/826hekun/BioinformaticsPathfinder.git




## 1.转录组文件准备
################################################################################
# 创建并激活名为"sra-tools"的conda虚拟环境，用于管理软件依赖
# - conda create -n <env_name> 创建新环境
# - conda activate <env_name> 激活指定环境
# - conda install -y 自动确认安装过程
################################################################################
conda create -n sra-tools
conda activate sra-tools
conda install sra-tools -y

################################################################################
# 使用prefetch工具批量下载SRA数据
# --option-file 指定包含SRA编号列表的文件（需预先准备srr.txt）
# 下载的.sra文件会存储在对应SRR编号的目录中
################################################################################
prefetch --option-file srr.txt

################################################################################
# 处理第一个样本SRR1039512
# 流程说明：
# 1. cd进入样本目录
# 2. fasterq-dump转换.sra为fastq格式：
#    -p 显示进度条
#    -e 24 使用24个线程
#    --split-3 自动拆分双端测序数据
#    -O ./ 输出到当前目录
# 3. 批量重命名并压缩：
#    - 将.fastq后缀改为.fq
#    - 使用gzip压缩生成.fq.gz文件
################################################################################
cd SRR1039512
fasterq-dump -p -e 24 --split-3 -O ./ SRR1039512.sra
for file in *.fastq; do
    mv "$file" "${file%.fastq}.fq"
    gzip "${file%.fastq}.fq"
done

# 处理第二个样本SRR1039517（流程与第一个样本完全相同）
cd ../SRR1039517
fasterq-dump  -p -e 24 --split-3 -O ./ SRR1039517.sra
for file in *.fastq; do
    mv "$file" "${file%.fastq}.fq"
    gzip "${file%.fastq}.fq"
done 

# 退出conda虚拟环境
conda deactivate

# 注意事项：
# 1. 需确保srr.txt文件存在且包含正确的SRR编号
# 2. 线程数(-e参数)应根据实际CPU核心数调整
# 3. 最终生成压缩格式.fq.gz，节省存储空间
# 4. --split-3参数会根据元数据自动拆分单端/双端测序数据
# 5. 原始.sra文件仍会保留，需手动清理以释放空间


##
##
##



################################################################
## 2.环境创建和安装软件
conda create -n rnaseq_up -c bioconda -c conda-forge fastqc fastp multiqc salmon -y 
conda activate rnaseq_up
fastqc --version
fastp --version
multiqc --version
salmon --version

#若主环境中不兼容Salmon，则新建一个环境安装Salmon
# 创建一个名为trim-env的环境，
conda create -n salmon
# 激活这个环境
conda activate salmon
# 在这个环境中安装Salmon，
conda install -c salmon
#若遇见报错，参考https://blog.csdn.net/qq_45794091/article/details/140313385#:~:text=Linux%E5%AE%9E%E6%93%8D%E2%80%94%E2%80%94s
conda install salmon=1.10.3=hb7e2ac5_1
# 下次直接激活小环境
conda activate salmon
##
##
##



################################################################
## 3. 工作目录创建
## 功能：创建项目目录结构，设置工作环境变量
## 参数说明：
##   mkdir -p : 递归创建目录，忽略已存在目录
##   workdir=./workdir : 定义工作目录变量
##   tree : 可视化目录结构（需提前安装）
################################################################
conda activate rnaseq_up
mkdir -p workdir
cd workdir
#等号两边不能有空格，否则会报错。
workdir=$(pwd)
#workdir=`pwd`
mkdir -p 1database/GRCh38.105
mkdir -p 2data/rawdata 2data/cleandata/fastp
mkdir -p 3Salmon 3Salmon/index
tree

##
##
##


################################################################
## 4 参考基因组准备
## 功能：下载参考基因组相关文件
## 参数说明：
##   axel参数:
##     -n 100 : 使用100个连接加速下载
##     -o 下载后的文件名
##   gunzip : 解压基因组文件
## 文件说明:
##   dna.primary_assembly.fa : 主要基因组序列
##   cdna.all.fa : 全部转录本序列
##   .gtf.gz : 基因结构注释文件
################################################################
## 参考基因组准备:注意参考基因组版本信息
# 下载，Ensembl：http://asia.ensembl.org/index.html
# http://ftp.ensembl.org/pub/release-104/fasta/homo_sapiens/dna/
# 进入到参考基因组目录

mkdir -p $workdir/1database/GRCh38.111
cd $workdir/1database/GRCh38.111
# 下载基因组序列axel  curl  
nohup axel -n 10 -o dna.fa.gz https://ftp.ensembl.org/pub/release-111/fasta/homo_sapiens/dna/Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz >dna.log &
# 下载转录组序列
nohup axel -n 10 -o cdna.fa.gz http://ftp.ensembl.org/pub/release-111/fasta/homo_sapiens/cdna/Homo_sapiens.GRCh38.cdna.all.fa.gz >rna.log &
# 下载基因组注释文件
nohup axel -n 10 -o gtf.fa.gz https://ftp.ensembl.org/pub/release-111/gtf/homo_sapiens/Homo_sapiens.GRCh38.111.gtf.gz >gtf.log &
nohup axel -n 10 -o gff3.fa.gz https://ftp.ensembl.org/pub/release-111/gff3/homo_sapiens/Homo_sapiens.GRCh38.111.gff3.gz >gff.log&



# 上述文件下载完整后，再解压；否则文件不完整就解压会报错
# 再次强调，一定要在文件下载完后再进行解压！！！
# nohup gunzip Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz Homo_sapiens.GRCh38.cdna.all.fa.gz >unzip.log &

##
##
##

################################################################
## 5. 数据质控模块 (FastQC + MultiQC)
## 功能：原始数据质量评估与结果整合
## 参数说明：
##   conda activate rnaseq_up : 激活Conda生物信息学环境
##   ln -s : 创建符号链接避免数据冗余
##   fastqc参数:
##     -t 6 : 使用6个线程
##     -o ./ : 输出到当前目录
##   nohup ... & : 后台运行并重定向日志
##   multiqc参数:
##     *.zip : 处理所有FastQC的zip报告
##     -o : 指定输出目录
################################################################

cd $workdir/2data/rawdata


ln -s /u3/hekun/GSE52778/SRR1039512/*.fq.gz  ./
ln -s /u3/hekun/GSE52778/SRR1039517/*.fq.gz  ./


# 使用FastQC软件对fastq文件进行质量评估，结果输出到qc/文件夹下，-t线程数
mkdir qc
mkdir multiqc
nohup fastqc -t 6 -o ./qc *.fq.gz >./qc/qc.log &

# 报告整合
# 可以参考这个链接学习如何解读报告 https://blog.csdn.net/qq_44520665/article/details/113779792
fq_dir=$workdir/2data/rawdata
outdir=$workdir/2data/rawdata
multiqc $outdir/qc/*.zip -o $outdir/multiqc/ >${fq_dir}/multiqc/multiqc.log


##使用双引号包裹sed的替换命令，这样shell会展开变量$workdir，替换成它的实际值。在单引号中，变量不会被展开。
ls $workdir/2data/rawdata/*_1.fq.gz | sed "s#$workdir/2data/rawdata/##g" | sed 's#_1.fq.gz##g' >ID

##
##
##

################################################################
## 6. 数据过滤模块 (fastp)
## 功能：原始数据质量控制与过滤
## 参数说明：
## fastp过滤,c++写的，运行速度更快,样本越多越推荐
## -l 20: 设置过滤后的最短序列长度为20，如果小于这个长度，序列会被丢弃。
## -q 20: 设置过滤后的最低平均质量值为20，如果低于这个值，序列会被丢弃。
## --compression 6: 设置输出文件的压缩等级为6，范围是1到9，1最快，9最小，默认是4。
## -i ${rawdata}/${id}_1.fq.gz: 设置输入文件的路径和名称，这里使用了变量rawdata和id，表示原始数据的目录和样本的编号，_1表示第一条链。
## -I ${rawdata}/${id}_2.fq.gz: 设置另一个输入文件的路径和名称，这里使用了变量rawdata和id，表示原始数据的目录和样本的编号，_2表示第二条链。
## -o ${cleandata}/${id}_clean_1.fq.gz: 设置输出文件的路径和名称，这里使用了变量cleandata和id，表示清洗数据的目录和样本的编号，_clean_1表示第一条链的清洗结果。
## -O ${cleandata}/${id}_clean_2.fq.gz: 设置另一个输出文件的路径和名称，这里使用了变量cleandata和id，表示清洗数据的目录和样本的编号，_clean_2表示第二条链的清洗结果。
## -R ${cleandata}/${id}: 设置输出文件的前缀，这里使用了变量cleandata和id，表示清洗数据的目录和样本的编号。
## -h ${cleandata}/${id}.fp.html: 为质控报告文件，设置输出的HTML格式的质控报告的路径和名称，这里使用了变量cleandata和id，表示清洗数据的目录和样本的编号。
##  -j ${cleandata}/${id}.fp.json: 为质控报告文件,设置输出的JSON格式的质控报告的路径和名称，这里使用了变量cleandata和id，表示清洗数据的目录和样本的编号。
## 以下三个参数教程源代码没有，但是根据教程所学知识添加的
## -n/--n base limit 限制N个数
## -u设置允许不合格碱基阈值，超过比例时，整条read将被丢弃，默认为40。
## -w设置软件可用线程数，默认为2
##   nohup bash ... & : 后台运行批量处理脚本
##   multiqc *json : 整合所有样本的JSON报告
################################################################

cd ../cleandata/
# 打印打印输出代码 fastp.sh
cleandata=$workdir/2data/cleandata/fastp
rawdata=$workdir/2data/rawdata
cat ../rawdata/ID | while read id
do echo "
fastp -l 20 -q 20 -w 6 -n 5 -u 40 --compression=6 \
  -i ${rawdata}/${id}_1.fq.gz \
  -I ${rawdata}/${id}_2.fq.gz \
  -o ${cleandata}/${id}_1.fq.gz \
  -O ${cleandata}/${id}_2.fq.gz \
  -R ${cleandata}/${id} \
  -h ${cleandata}/${id}.fp.html \
  -j ${cleandata}/${id}.fp.json 
  "
done >fastp.sh
nohup bash fastp.sh >fastp.log &
# 上面运行结束后在运行下面的，使用multiqc对json进行整理，但结果挺简单的，html不能被multiqc整理
cd fastp/
multiqc *json

##
##
##



################################################################
## 7 Salmon定量
################################################################################
# 退出conda虚拟环境并进入salmon环境
conda deactivate
conda activate salmon

##----构建索引

cd $workdir/3Salmon/index
ln -s $workdir/1database/GRCh38.111/*.gz  ./

cd $genomedir/


#Salmon 索引需要基因组靶标的名称
grep "^>" <(gunzip -c dna.fa.gz) | cut -d " " -f 1 >decoys.txt
sed -i.bak -e 's/>//g' decoys.txt
#salmon还需要串联的转录组和基因组参考文件作为索引。注意：基因组靶标应位于转录组之后
cat cdna.fa.gz dna.fa.gz > gentrome.fa.gz
#开始构建
nohup salmon index -t gentrome.fa.gz -d decoys.txt -p 12 -i salmon_index -k 31  >salmon-index.log &
# 进入salmon文件夹
cd $workdir/3Salmon



# Salmon转录本定量分析命令说明
# 功能：使用salmon工具对双端测序数据进行转录本定量分析
# 参数详解：
# -i ${index}      : 指定Salmon索引目录路径（需提前构建）
# -l A             : 自动检测测序文库类型（A=Automatic detection）
# -1/-2            : 输入双端测序文件路径（预处理后的clean data）
#                    ${input} 表示输入文件目录路径变量
#                    ${id} 表示样本ID变量
#                    _1_val_1/_2_val_2 表示经过质控的双端测序文件命名
# -p 5             : 使用5个CPU线程加速计算
# --gcBias         : 启用GC含量偏倚校正（提高定量准确性）
# --seqBias        : 启用序列特异性偏倚校正（提高定量准确性）
# --validateMappings: 使用更严格的可信映射验证（推荐用于提高准确性）
# -o ${outdir}/${id}.quant : 指定输出目录路径（包含样本ID的定量结果目录）
################################################################################
# 编写脚本，使用salmon批量对目录下所有fastq文件进行定量

genomedir=/u3/hekun/jinengshu-rnaseq/database/Taestivum.58/
index=$workdir/3Salmon/index/salmon_index
input=$workdir/2data/cleandata/fastp
outdir=$workdir/3Salmon
cat $workdir/2data/rawdata/ID |while read id 
do echo "
  salmon quant -i ${index} \
  -l A -1 ${input}/${id}_1_val_1.fq.gz \
  -2 ${input}/${id}_2_val_2.fq.gz \
  -p 5 \
  --gcBias \
  --seqBias \
  --validateMappings \
  -o ${outdir}/${id}.quant
   "
done >salmon.sh

# 注意事项：
# 1. 输入文件需确保是经过质控处理的clean data（通常来自trim_galore/fastp等工具）
# 2. ${index}需要预先使用salmon index命令构建（参考基因组/转录组索引）
# 3. 线程数(-p)应根据实际计算资源调整（建议不超过可用CPU核心数）
# 4. --gcBias和--seqBias会略微增加计算时间，但显著提高定量准确性
# 5. 输出目录将包含quant.sf（定量结果文件）、logs（日志文件）等重要文件




#运行
nohup bash salmon.sh >salmon.log &

##用于生成得到矩阵的命令
##----合并表达矩阵
# 原始count值矩阵
# 原始表达矩阵
salmon quantmerge --quants {SRR1039510.quant,SRR1039511.quant,SRR1039512.quant} --names {SRR1039510,SRR1039511,SRR1039512} --column numreads  --output raw_count.txt
# tpm矩阵
salmon quantmerge --quants {SRR1039510.quant,SRR1039511.quant,SRR1039512.quant} --names {SRR1039510,SRR1039511,SRR1039512} --column tpm  --output tpm.txt

## 完整版（一步生成上述命令，然后运行）：
# 原始表达矩阵
ls -d *quant |tr '\n' ',' |sed 's/,$//' |awk '{print "{"$0"}"}'  | perl -ne 'chomp;$a=$_;$a=~s/\.quant//g;print"salmon quantmerge --quants $_ --names $a --column numreads  --output raw_count.txt \n";'
# tpm矩阵
ls -d *quant |tr '\n' ',' |sed 's/,$//' |awk '{print "{"$0"}"}'  | perl -ne 'chomp;$a=$_;$a=~s/\.quant//g;print"salmon quantmerge --quants $_ --names $a --column tpm  --output tpm.txt \n";'






# 至此非基于比对的转录组上游分析已全部结束




