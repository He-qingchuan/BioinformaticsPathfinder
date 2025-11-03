### 下载测序数据

```sh
#如文章给出GSM号如GSE242964，则打开网页到最后找到BioProject编号如PRJNA1015621，在https://sra-explorer.info/中搜索，并选择需要的fastq文件以及下载需要的metadata文件
# 安装下载所用的软件
wget https://download.asperasoft.com/download/sw/connect/3.9.1/ibm-aspera-connect-3.9.1.171801-linux-g2.12-64.tar.gz
tar zxvf ibm-aspera-connect-3.9.1.171801-linux-g2.12-64.tar.gz
bash ibm-aspera-connect-3.9.1.171801-linux-g2.12-64.sh
#加入环境路径
echo 'export PATH=$PATH:~/.aspera/connect/bin' >>~/.profile
source ~/.profile


#在https://sra-explorer.info/中搜索，并选择需要的fastq文件下载的代码文件sra_explorer_fastq_aspera_download.sh，并上传到服务器存放数据的目录
#然后运行并下载文件
#下载完成后，每个样本会有2个fastq文件，分别对应*_1.fastq.gz和*_2.fastq.gz，但是也有可能多一个只有几百K没什么用的fastq文件，通常这个多余的fastq文件我都不关心，直接删掉就行
nohup bash sra_explorer_fastq_aspera_download.sh &

#修改文件名使其更简约明了，可以使用deepseek帮忙改代码，例如（我有一些下面的文件，但是命名不是我想要的格式，我想使用while循环改一下，以SRR26039809_GSM7776113_Leaves_2d_post_transition_ZT8_rep_3_Arabidopsis_thaliana_RNA-Seq_1.fastq.gz为例，我想改为ZT8_rep_3_1.fastq.gz。后面加上一些自己的文件名示例）
# 使用while循环处理每个.fastq.gz文件
ls *.fastq.gz | while read original; do
    # 提取ZTx_rep_y部分（例如 ZT8_rep_3）
    zt_rep=$(echo "$original" | grep -o 'ZT[0-9]\+_rep_[0-9]\+')
    # 提取末尾的配对编号（1或2）
    pair_num=$(echo "$original" | sed 's/.*_\([12]\)\.fastq\.gz$/\1/')
    # 构建新文件名（格式：ZTx_rep_y_pairnum.fastq.gz）
    newname="${zt_rep}_${pair_num}.fastq.gz"
    # 重命名文件（安全起见先打印确认）
    echo "Renaming: $original  ->  $newname"
    mv -- "$original" "$newname"
done













# 第二种方法


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



















```



