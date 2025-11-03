###  06 数据过滤 (fastp)

```bash
################################################################
## 06. 数据过滤 (fastp)
## 功能：原始数据质量控制与过滤
## 参数说明：
## fastp过滤,c++写的，运行速度更快,样本越多越推荐
## -l 20: 设置过滤后的最短序列长度为20，如果小于这个长度，序列会被丢弃。
## -q 20: 设置过滤后的最低平均质量值为20，如果低于这个值，序列会被丢弃。
## --compression 6: 设置输出文件的压缩等级为6，范围是1到9，1最快，9最小，默认是4。
## -i ${rawdata}/${id}_1.fq.gz: 设置输入文件的路径和名称，这里使用了变量rawdata和id，表示原始数据的目录和样本的编号。
## -I ${rawdata}/${id}_2.fq.gz: 设置另一个输入文件的路径和名称，这里使用了变量rawdata和id，表示原始数据的目录和样本的编号。
## -o ${cleandata}/${id}_clean_1.fq.gz: 设置输出文件的路径和名称，这里使用了变量cleandata和id，表示清洗数据的目录和样本的编号。
## -O ${cleandata}/${id}_clean_2.fq.gz: 设置另一个输出文件的路径和名称，这里使用了变量cleandata和id，表示清洗数据的目录和样本的编号。
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
  -o ${cleandata}/${id}_clean_1.fq.gz \
  -O ${cleandata}/${id}_clean_2.fq.gz \
  -R ${cleandata}/${id} \
  -h ${cleandata}/${id}.fp.html \
  -j ${cleandata}/${id}.fp.json 
  "
done >fastp.sh

###运行代码
nohup bash fastp.sh >fastp.log &
# 上面运行结束后在运行下面的，使用multiqc对json进行整理，但结果挺简单的，html不能被multiqc整理
cd fastp/
multiqc *json

```

