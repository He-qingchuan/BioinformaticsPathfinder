### 13top基因热图

```{r}
library(tidyverse)
library(readr)
library(pheatmap)
library(scales)
library("RColorBrewer")




load(file = "4SampleHheatmapPCA/gene_exp.Rdata")
load(file = "4SampleHheatmapPCA/sample_info.Rdata")

#读取数据
de_result <- read_delim("5DESeq2/de_result.tsv", 
    delim = "\t", escape_double = FALSE, 
    trim_ws = TRUE)
#选出变化倍数最大的30个基因
top_de <- filter(de_result, 
                       sampleA == "ZT20",
                       sampleB == "ZT0") %>%
  arrange(desc(abs(log2FoldChange))) %>%
  slice(1:30) %>%
  pull(gene_id)



#提取目标基因矩阵
top_de_exp = gene_exp[top_de,]


#绘图1
pdf("8topgene_pheatmap/topgene_pheatmap1A.pdf", width = 12, height = 8)
pheatmap(log2(top_de_exp + 1), 
       #  color = brewer.pal(12, "YlOrRd"),
         cluster_rows = T, 
         cluster_cols = F, # 列不聚类
         border_color = "white", # 边框颜色
         fontsize = 8, # 字体大小
         angle_col = 45, # 列倾斜
         display_numbers = T, # 显示数值
         scale = 'row',# 按行进行scale，防止极值影响颜色观察
         fontsize_number = 5) # 数值字体大小
# 关闭 PDF 设备
dev.off()




show_col(brewer.pal(12, "YlOrRd"))
pdf("8topgene_pheatmap/topgene_pheatmap1B.pdf", width = 12, height = 8)
pheatmap(log2(top_de_exp + 1), 
         color = brewer.pal(12, "YlOrRd"),
         cluster_rows = T, 
         cluster_cols = F, # 列不聚类
         border_color = "white", # 边框颜色
         fontsize = 8, # 字体大小
         angle_col = 45, # 列倾斜
         display_numbers = T, # 显示数值
         scale = 'row',# 按行进行scale，防止极值影响颜色观察
         fontsize_number = 5) # 数值字体大小
# 关闭 PDF 设备
dev.off()



#绘图2
pdf("8topgene_pheatmap/topgene_pheatmap2A.pdf", width = 12, height = 8)
pheatmap(log2(top_de_exp + 1), 
       #  color = brewer.pal(12, "YlOrRd"),
         cluster_rows = T, 
         cluster_cols = F, # 列不聚类
         border_color = "white", # 边框颜色
         fontsize = 8, # 字体大小
         angle_col = 45, # 列倾斜
        # display_numbers = T, # 显示数值
         scale = 'row',# 按行进行scale，防止极值影响颜色观察
         fontsize_number = 5) # 数值字体大小
# 关闭 PDF 设备
dev.off()



pdf("8topgene_pheatmap/topgene_pheatmap2B.pdf", width = 12, height = 8)
pheatmap(log2(top_de_exp + 1), 
       #  color = brewer.pal(12, "YlOrRd"),
         cluster_rows = T, 
         cluster_cols = F, # 列不聚类
         border_color = "white", # 边框颜色
         fontsize = 8, # 字体大小
         angle_col = 45, # 列倾斜
         display_numbers = T, # 显示数值
         scale = 'row',# 按行进行scale，防止极值影响颜色观察
         fontsize_number = 5) # 数值字体大小
# 关闭 PDF 设备
dev.off()








#绘图3


pdf("8topgene_pheatmap/topgene_pheatmap3A.pdf", width = 12, height = 8)
pheatmap(log2(top_de_exp + 1), 
       #  color = brewer.pal(12, "YlOrRd"),
         cluster_rows = T, 
         cluster_cols = F, # 列不聚类
         border_color = "white", # 边框颜色
         fontsize = 8, # 字体大小
         angle_col = 45, # 列倾斜
        # display_numbers = T, # 显示数值
         scale = 'row',# 按行进行scale，防止极值影响颜色观察
         fontsize_number = 5,
         annotation_col = sample_info,annotation_names_col = 45) # 数值字体大小
# 关闭 PDF 设备
dev.off()



pdf("8topgene_pheatmap/topgene_pheatmap3B.pdf", width = 12, height = 8)
pheatmap(log2(top_de_exp + 1), 
       #  color = brewer.pal(12, "YlOrRd"),
         cluster_rows = T, 
         cluster_cols = F, # 列不聚类
         border_color = "white", # 边框颜色
         fontsize = 8, # 字体大小
         angle_col = 45, # 列倾斜
         display_numbers = T, # 显示数值
         scale = 'row',# 按行进行scale，防止极值影响颜色观察
         fontsize_number = 5,
         annotation_col = sample_info,annotation_names_col = 45) # 数值字体大小
# 关闭 PDF 设备
dev.off()

```

