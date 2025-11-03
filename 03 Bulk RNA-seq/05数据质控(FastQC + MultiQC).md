

### 05 数据质控(FastQC + MultiQC)

```bash

################################################################
## 数据质控 (FastQC + MultiQC)
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

### 激活Conda生物信息学环境
conda activate rnaseq_up


cd $workdir/2data/rawdata
### 链接数据
ln -s ~/data/*.fastq.gz  ./
#### rename 's/旧模式/新模式/' 文件列表，，，，s 代表 substitute
rename 's/\.fastq\.gz$/.fq.gz/' *.fastq.gz

#使用FastQC软件对fastq文件进行质量评估，结果输出到qc/文件夹下，-t线程数
mkdir qc
mkdir multiqc
nohup fastqc -t 6 -o ./qc *.fq.gz >./qc/qc.log &

# 报告整合
# 可以参考这个链接学习如何解读报告 https://blog.csdn.net/qq_44520665/article/details/113779792

rawdata=$workdir/2data/rawdata
multiqc $rawdata/qc/*.zip -o $rawdata/multiqc/ >${rawdata}/multiqc/multiqc.log


###获取样本名ID
##使用双引号包裹sed的替换命令，这样shell会展开变量$workdir，替换成它的实际值。在单引号中，变量不会被展开。
ls $workdir/2data/rawdata/*_1.fq.gz | sed "s#$workdir/2data/rawdata/##g" | sed 's#_1.fq.gz##g' >ID



```







```
ascp -QT -l 300m -P33001 -i $HOME/.aspera/connect/etc/asperaweb_id_dsa.openssh era-fasp@fasp.sra.ebi.ac.uk:vol1/fastq/SRR260/020/SRR26039820/SRR26039820_1.fastq.gz . && mv SRR26039820_1.fastq.gz SRR26039820_GSM7776102_Leaves_2d_post_transition_ZT1_rep_1_Arabidopsis_thaliana_RNA-Seq_1.fastq.gz

ascp -QT -l 300m -P33001 -i $HOME/.aspera/connect/etc/asperaweb_id_dsa.openssh era-fasp@fasp.sra.ebi.ac.uk:vol1/fastq/SRR260/023/SRR26039823/SRR26039823_1.fastq.gz . && mv SRR26039823_1.fastq.gz SRR26039823_GSM7776099_Leaves_2d_post_transition_ZT16_rep_1_Arabidopsis_thaliana_RNA-Seq_1.fastq.gz

nohup ascp -QT -l 300m -P33001 -i $HOME/.aspera/connect/etc/asperaweb_id_dsa.openssh era-fasp@fasp.sra.ebi.ac.uk:vol1/fastq/SRR260/021/SRR26039821/SRR26039821_1.fastq.gz . && mv SRR26039821_1.fastq.gz SRR26039821_GSM7776101_Leaves_2d_post_transition_ZT16_rep_3_Arabidopsis_thaliana_RNA-Seq_1.fastq.gz &

nohup ascp -QT -l 300m -P33001 -i $HOME/.aspera/connect/etc/asperaweb_id_dsa.openssh era-fasp@fasp.sra.ebi.ac.uk:vol1/fastq/SRR260/026/SRR26039826/SRR26039826_1.fastq.gz . && mv SRR26039826_1.fastq.gz SRR26039826_GSM7776096_Leaves_2d_post_transition_ZT12_rep_1_Arabidopsis_thaliana_RNA-Seq_1.fastq.gz &


```

