### 15模式生物GO和KEGG的基因集富集分析（GSEA）

```r
# GO 的GSEA富集及可视化
## GO GSEA 富集
# KEGG Pathway 的 GSEA富集及可视化
### KEGG Pathway GSEA 富集
library(clusterProfiler)
library(org.At.tair.db)
library(enrichplot)

library(tidyverse)
library(magrittr)
library(patchwork)
library(ggplot2)


load(file = "9Enrichment_Analysis/geneList.Rdata")
load(file = "9Enrichment_Analysis/gene.Rdata")




#富集分析

####
#参数	说明	常用值/建议
#geneList	排序的命名数值向量	按log2FC排序
#OrgDb	物种注释数据库	与研究对象物种对应
#keyType	基因ID类型	"TAIR", "ENTREZID"等
#ont	GO类别	"ALL", "BP", "MF", "CC"
#minGSSize	基因集最小大小	通常10-25，过滤太小基因集
#maxGSSize	基因集最大大小	通常500-1000，过滤太大基因集
#eps	p值计算精度	通常1e-10，避免数值问题
#pvalueCutoff	p值阈值	通常0.05
#pAdjustMethod	p值校正方法	"BH", "fdr", "bonferroni"等
#verbose	显示运行信息	TRUE或FALSE
#simplify  简化结果,simplify only applied to output from gseGO and enrichGO...
#cutoff 值，用于判断两个GO术语是否相似，使用0.75表示当两个GO术语的相似性达到75%时，视为冗余
#by	"p.adjust"	选择统计最显著的术语
#select_fun	min	配合p值使用，选择最显著的值，min表示选择校正p值最小的（最显著的）那个术语
####
ego2_ALL <- gseGO(geneList = geneList,
  OrgDb= org.At.tair.db,
  keyType = "TAIR",
  ont  = "ALL",
  minGSSize = 10,
  maxGSSize = 500,
  eps =0,
  pvalueCutoff = 0.05,
  pAdjustMethod = "BH",
  verbose = TRUE) %>%
  clusterProfiler::simplify(cutoff=0.75, 
                            by="p.adjust", 
                            select_fun=min)


ego2_BP <- gseGO(geneList = geneList,
  OrgDb= org.At.tair.db,
  keyType = "TAIR",
  ont = "BP",
  minGSSize = 10,
  maxGSSize = 500,
  eps =0,
  pvalueCutoff = 0.05,
  pAdjustMethod = "BH",
  verbose = TRUE) %>%
  clusterProfiler::simplify(cutoff=0.75, 
                            by="p.adjust", 
                            select_fun=min)

ego2_CC <- gseGO(geneList     = geneList,
  OrgDb        = org.At.tair.db,
  keyType      = "TAIR",
  ont          = "CC",
  minGSSize = 10,
  maxGSSize = 500,
  eps =0,
  pvalueCutoff = 0.05,
  pAdjustMethod = "BH",
  verbose = TRUE) %>%
  clusterProfiler::simplify(cutoff=0.75, 
  by="p.adjust", 
  select_fun=min) %>%
  clusterProfiler::simplify(cutoff=0.75, 
                            by="p.adjust", 
                            select_fun=min)

ego2_MF <- gseGO(geneList     = geneList,
  OrgDb= org.At.tair.db,
  keyType = "TAIR",
  ont = "MF",
  minGSSize = 10,
  maxGSSize = 500,
  eps =0,
  pvalueCutoff = 0.05,
  pAdjustMethod = "BH",
  verbose = TRUE) %>%
  clusterProfiler::simplify(cutoff=0.75, 
                            by="p.adjust", 
                            select_fun=min)

ekg2 <- gseKEGG(
  geneList,
  organism = "ath",
  keyType = "kegg",
  minGSSize = 10,
  maxGSSize = 500,
  eps =0,
  pvalueCutoff = 0.05,
  pAdjustMethod = "BH",
  verbose = TRUE) 





## 画图
p_ego2_ALL = gseaplot2(ego2_ALL, geneSetID = 1:10,
  title = "Biological process",
  pvalue_table = FALSE)

p_ego2_BP = gseaplot2(ego2_BP, geneSetID = 1:10,
  title = "Biological process",
  pvalue_table = FALSE)

p_ego2_MF = gseaplot2(ego2_MF, geneSetID = 1:10,
  title = "Molecular function",
  pvalue_table = FALSE)

p_ego2_CC = gseaplot2(ego2_CC, geneSetID = 1:10,
  title = "Cellular component",
  pvalue_table = FALSE)


p_ekg2 = gseaplot2(ekg2, geneSetID = 1:10,
  title = "KEGG Pathway",
  pvalue_table = FALSE)



#保存图片
ggsave('9Enrichment_Analysis/GSEA/ego2_ALL.pdf', plot = p_ego2_ALL, width = 8, height = 6)
ggsave('9Enrichment_Analysis/GSEA/ego2_CC.pdf', plot = p_ego2_CC, width = 8, height = 6)
ggsave('9Enrichment_Analysis/GSEA/ego2_BP.pdf', plot = p_ego2_BP, width = 8, height = 6)
ggsave('9Enrichment_Analysis/GSEA/ego2_MF.pdf', plot = p_ego2_MF, width = 8, height = 6)
ggsave('9Enrichment_Analysis/GSEA/ekg2.pdf', plot = p_ekg2, width = 8, height = 6)









###保存结果为数据框
ego2_ALL_df <- data.frame(ego2_ALL)
ego2_BP_df <- data.frame(ego2_BP)
ego2_CC_df <- data.frame(ego2_CC)
ego2_MF_df <- data.frame(ego2_MF)
ekg2_df <- as.data.frame(ekg2)

write.csv(ego2_ALL_df,'9Enrichment_Analysis/GSEA/enrichGO_ALL.csv')
write.csv(ekg2_df,'9Enrichment_Analysis/GSEA/ekg2_df.csv')
write.csv(ego2_BP_df,'9Enrichment_Analysis/GSEA/enrichGO_BP.csv')
write.csv(ego2_CC_df,'9Enrichment_Analysis/GSEA/enrichGO_CC.csv')
write.csv(ego2_MF_df,'9Enrichment_Analysis/GSEA/enrichGO_MF.csv')


```

