# 09样本关系pheatmap和PCA以及表达基因数量统计



```{r}
#安装包
if (!require("BiocManager", quietly = TRUE))
    install.packages("BiocManager")
BiocManager::install("PCAtools")
BiocManager::install("hrbrmstr/ggalt")
BiocManager::install("hadley/scales")



install.packages("tidyverse")
install.packages("pheatmap")
install.packages("RColorBrewer")





library(tidyverse)
library(pheatmap)
library(RColorBrewer)
library(scales)
library(PCAtools)
library(ggalt)

setwd("workdir/")


```

1. 导入表达矩阵

```{r}
gene_exp <- read.delim("4SampleHheatmapPCA/quanti/genes.gene.TMM.EXPR.matrix", row.names=1)

```

2. 导入样本信息表

```{r}

read.table(file = "4SampleHheatmapPCA/samples.txt") %>%
  rename(group = "V1", sample = "V2") %>%
  column_to_rownames(var = "sample") -> sample_info
```

样本相关性

1.计算样本间相关系数

```{r}
sample_cor = round(cor(gene_exp, use = "pairwise.complete.obs",method = "pearson"), digits = 2)
```

2. 绘制热图

调整热图颜色，调色板：https://github.com/EmilHvitfeldt/r-color-palettes

```{r}


# 开始 PDF 设备，指定文件名和大小
pdf("4SampleHheatmapPCA/samples_corcluster1.pdf", width = 15, height = 12)

# 生成热图
pheatmap(sample_cor, 
         cluster_rows = FALSE, cluster_cols = FALSE,  # 不聚类
         cellwidth = 15, cellheight = 15,            # cell 大小
         border_color = "white",                     # 边框颜色
         fontsize = 8,                               # 字体大小
         angle_col = 45,                             # 列倾斜角度
         display_numbers = TRUE,                     # 显示数值
         fontsize_number = 5)                        # 数值字体大小

# 关闭 PDF 设备
dev.off()



# 开始 PDF 设备，指定文件名和大小
pdf("4SampleHheatmapPCA/samples_corcluster2.pdf", width = 15, height = 12)
show_col(brewer.pal(9, "OrRd"))
pheatmap(sample_cor, 
         color = brewer.pal(9, "OrRd"),
         breaks = seq(0.7, 1, 0.05),#热图标尺
         cluster_rows = F, cluster_cols = F, # 不聚类
         cellwidth = 15, cellheight = 15, # cell 大小
         border_color = "white", # 边框颜色
         fontsize = 8, # 字体大小
         angle_col = 45, # 列倾斜
         display_numbers = T, # 显示数值
         fontsize_number = 5) # 数值字体大小

# 关闭 PDF 设备
dev.off()

```

样本聚类


```{r}
# 开始 PDF 设备，指定文件名和大小
pdf("4SampleHheatmapPCA/samples_clustertree.pdf", width = 15, height = 12)
plot(hclust(dist(t(gene_exp))))
# 关闭 PDF 设备
dev.off()


```
主成分分析

```{r}


# 开始 PDF 设备，指定文件名和大小
pdf("4SampleHheatmapPCA/samples_pca_hist.pdf", width = 15, height = 12)

p1 = pca(gene_exp, metadata = sample_info, removeVar = 0.3)
screeplot(p1)

# 关闭 PDF 设备
dev.off()

#removeVar = 0.3去除波动最小的30%的基因，有利于pca分析

#如果原始数据表现不好，也可以取对数
p2 = pca(log2(gene_exp+1 ), metadata = sample_info, removeVar = 0.3)

#或标准化和中心化
p3 = pca(gene_exp, metadata = sample_info, removeVar = 0.3, center = T, scale =T)
```

```{r}

# 开始 PDF 设备，指定文件名和大小
pdf("4SampleHheatmapPCA/samples_pca12A.pdf", width = 15, height = 12)

biplot(p1,
       x = 'PC1',
       y = 'PC2',
       colby = "group",
       hline = 0, vline = 0,
       encircle = T, encircleFill = T,
       ellipse = T,#加置信区间
      max.overlaps = Inf)
# 关闭 PDF 设备
dev.off()


# 开始 PDF 设备，指定文件名和大小
pdf("4SampleHheatmapPCA/samples_pca12B.pdf", width = 15, height = 12)


biplot(p1,
       x = 'PC1',
       y = 'PC2',
       colby = "group",
       hline = 0, vline = 0,
       encircle = T, encircleFill = T,
      # ellipse = T,#加置信区间
      max.overlaps = Inf
      
       )
# 关闭 PDF 设备
dev.off()

```





不同分组表达基因数量统计折线图和条形图

```r
# 从数据框的列名中提取唯一的组名（如ZT0, ZT1等）
# sub()函数使用正则表达式"_rep_.*"匹配并替换列名中的"_rep_"及后面的所有字符为空字符串
# 这样就从"ZT0_rep_1"这样的列名中提取出了"ZT0"
# unique()函数确保每个组名只出现一次
group_names <- unique(sub("_rep_.*", "", colnames(gene_exp)))
# 创建一个新的空数据框用于存储计算结果
# row.names参数设置为原始数据框的行名，确保新数据框的行与原始数据框一致
# 这样新数据框将包含相同的基因名称作为行标识
gene_exp_avg <- data.frame(row.names = rownames(gene_exp))

# 使用for循环遍历每个组名，计算每个组的平均值
for (group in group_names) {
  # 使用grep函数查找属于当前组的所有列
  # paste0("^", group, "_rep_")创建正则表达式模式，例如"^ZT0_rep_"
  # "^"表示字符串开头，确保只匹配以当前组名开头的列
  # 这样可以精确匹配到当前组的所有重复列（如ZT0_rep_1, ZT0_rep_2, ZT0_rep_3）
  group_cols <- grep(paste0("^", group, "_rep_"), colnames(gene_exp))
  
  # 计算当前组所有列的行平均值
  # gene_exp[, group_cols, drop = FALSE] 选择当前组的所有列
  # drop = FALSE 确保即使只选择一列，结果也保持为数据框格式（这里每组有三列，所以不是必须的，但这是一个好习惯）
  # rowMeans() 函数计算每一行的平均值
  # 将计算结果添加到新数据框中，列名为当前组名
  gene_exp_avg[group] <- rowMeans(gene_exp[, group_cols, drop = FALSE])
}

# 查看计算结果的前几行
# head()函数显示数据框的前6行，方便快速检查计算结果
head(gene_exp_avg)

# 使用 apply 函数统计 gene_exp_avg 数据框中每列大于 1 的元素个数
# apply() 函数对数组或矩阵的边际（行或列）应用函数
# 第一个参数 gene_exp_avg: 要处理的数据框
# 第二个参数 2: 表示按列应用函数（1表示按行）
# 第三个参数 function(x) sum(x > 1): 匿名函数，计算每列中大于1的元素个数
# x > 1 创建一个逻辑向量，指示每个元素是否大于1
# sum() 函数将逻辑向量转换为数值（TRUE=1, FALSE=0），从而计算大于1的元素数量
greater_than_one_count <- apply(gene_exp_avg, 2, function(x) sum(x > 1))

# 显示统计结果
# 这将输出一个命名向量，其中名称是列名，值是对应列中大于1的元素个数
greater_than_one_count


# 假设 greater_than_one_count 是已经计算得到的向量
# 创建一个新的数据框来存储这些统计结果，便于后续分析或可视化
# data.frame() 函数创建数据框
# rep = names(greater_than_one_count): 将向量的名称作为数据框的第一列，命名为"rep"
# count = greater_than_one_count: 将向量的值作为数据框的第二列，命名为"count"
counts <- data.frame(rep = names(greater_than_one_count), count = greater_than_one_count)






# 加载ggplot2包
library(ggplot2)
# 使用ggplot创建可视化
# 将rep列转换为因子，保持原始顺序
counts$rep <- factor(counts$rep, levels = counts$rep)
ggplot(counts, aes(x = rep, y = count, fill = rep)) +  # 设置数据源和基本美学映射
  geom_bar(stat = "identity", width = 0.7) +           # 添加条形图，stat="identity"表示使用数据中的实际值
  labs(title = "Number of Genes with Expression > 1 by Time Point",  # 设置标题
       x = "Time Point (ZT)",                         # 设置x轴标签
       y = "Number of Genes",                         # 设置y轴标签
       fill = "Time Point") +                         # 设置图例标题
 #theme_minimal() +                                   # 使用简洁的主题
  theme_classic() +                                   # 使用经典主题，带有清晰的坐标轴
  theme(axis.text.x = element_text(angle = 45, hjust = 1),  # 旋转x轴标签45度，提高可读性
        plot.title = element_text(hjust = 0.5)) +     # 标题居中
  scale_fill_brewer(palette = "Set2")                 # 使用ColorBrewer的Set2调色板
  ###保存
  ggsave(
    filename = "4SampleHheatmapPCA/gene_num_bar.pdf",
    device = "pdf",
    width = 10,      # 宽度（英寸）
    height = 8,      # 高度（英寸）
    dpi = 300
)

  # 加载ggplot2包
library(ggplot2)
# 将rep列转换为因子，保持原始顺序
counts$rep <- factor(counts$rep, levels = counts$rep)
# 使用ggplot创建折线图可视化
ggplot(counts, aes(x = rep, y = count, group = 1)) +  # 设置数据源和基本美学映射
  geom_line(color = "steelblue", size = 1.5) +        # 添加折线，设置颜色和粗细
  geom_point(color = "steelblue", size = 3) +         # 添加数据点，与折线颜色一致
  labs(title = "Number of Genes with Expression > 1 by Time Point",  # 设置标题
       x = "Time Point (ZT)",                         # 设置x轴标签
       y = "Number of Genes") +                       # 设置y轴标签
 # theme_minimal() +                                   # 使用简洁的主题
  theme_classic() +                                   # 使用经典主题，带有清晰的坐标轴
  theme(axis.text.x = element_text(angle = 45, hjust = 1),  # 旋转x轴标签45度，提高可读性
        plot.title = element_text(hjust = 0.5, size = 14, face = "bold"),  # 标题居中并加粗
        axis.title = element_text(size = 12)) +       # 设置坐标轴标题字体大小
  scale_y_continuous(expand = expansion(mult = c(0.05, 0.1)))  # 调整y轴范围，留出适当边距
  
    ggsave(
    filename = "4SampleHheatmapPCA/gene_num_line.pdf",
    device = "pdf",
    width = 10,      # 宽度（英寸）
    height = 8,      # 高度（英寸）
    dpi = 300
)
  

```



```
save(gene_exp,gene_exp,file = "4SampleHheatmapPCA/gene_exp.Rdata")
save(gene_exp,gene_exp_avg,file = "4SampleHheatmapPCA/gene_exp_avg.Rdata")
save(sample_info,gene_exp_avg,file = "4SampleHheatmapPCA/sample_info.Rdata")

```

