07 定量(Salmon)

```bash
## 07 Salmon定量
################################################################################
# 退出conda虚拟环境并进入salmon环境
conda deactivate
conda activate salmon

##----构建索引

cd $workdir/3Salmon/index
ln -s $workdir/1database/TAIR10/*.gz  ./


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
#                    _clean_1/_clean_2 表示经过质控的双端测序文件命名
# -p 5             : 使用5个CPU线程加速计算
# --gcBias         : 启用GC含量偏倚校正（提高定量准确性）
# --seqBias        : 启用序列特异性偏倚校正（提高定量准确性）
# --validateMappings: 使用更严格的可信映射验证（推荐用于提高准确性）
# -o ${outdir}/${id}.quant : 指定输出目录路径（包含样本ID的定量结果目录）
################################################################################
# 编写脚本，使用salmon批量对目录下所有fastq文件进行定量

genomedir=$workdir/1database/TAIR10
index=$workdir/3Salmon/index/salmon_index
input=$workdir/2data/cleandata/fastp
outdir=$workdir/3Salmon
cat $workdir/2data/rawdata/ID |while read id 
do echo "
  salmon quant -i ${index} \
  -l A -1 ${input}/${id}_clean_1.fq.gz \
  -2 ${input}/${id}_clean_2.fq.gz \
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
# 原始表达矩阵
ls -d *quant |tr '\n' ',' |sed 's/,$//' |awk '{print "{"$0"}"}'  | perl -ne 'chomp;$a=$_;$a=~s/\.quant//g;print"salmon quantmerge --quants $_ --names $a --column numreads  --output raw_count.txt \n";' >count.sh

# tpm矩阵
ls -d *quant |tr '\n' ',' |sed 's/,$//' |awk '{print "{"$0"}"}'  | perl -ne 'chomp;$a=$_;$a=~s/\.quant//g;print"salmon quantmerge --quants $_ --names $a --column tpm  --output tpm.txt \n";' >tpm.sh


bash count.sh >count.log 
bash tpm.sh >tpm.log 

```

