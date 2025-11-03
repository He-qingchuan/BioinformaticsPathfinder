### 18非模式生物GO和KEGG的基因集富集分析（GSEA）

```R
# GO 的GSEA富集及可视化
## GO GSEA 富集
# KEGG Pathway 的 GSEA富集及可视化
### KEGG Pathway GSEA 富集
library(org.My.eg.db, lib.loc = "/u3/hekun/orgDb/egg2ord/orgdb_diamond/R_Library/")
library(enrichplot)
library(clusterProfiler)
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

ego2_ALL <- gseGO(geneList     = geneList,
  OrgDb = org.At.tair.db,
  keyType = "GID",
  ont  = "ALL",
  minGSSize = 10,
  maxGSSize = 500,
  eps =0,
  pvalueCutoff = 0.05,
  pAdjustMethod = "BH",
  verbose = TRUE)



ego2_BP <- gseGO(geneList = geneList,
  OrgDb= org.My.eg.db,
  keyType = "GID",
  ont = "BP",
  minGSSize = 10,
  maxGSSize = 500,
  eps =0,
  pvalueCutoff = 0.05,
  pAdjustMethod = "BH",
  verbose = TRUE) %>%
  filter(!str_detect(Description, "drug")) %>% 
  filter(!str_detect(Description, "cancer")) %>% 
  clusterProfiler::simplify(cutoff=0.75, 
                            by="p.adjust", 
                            select_fun=min)

ego2_CC <- gseGO(geneList     = geneList,
              OrgDb        = org.My.eg.db,
              keyType      = "GID",
              ont          = "CC",
  minGSSize = 10,
  maxGSSize = 500,
  eps =0,
  pvalueCutoff = 0.05,
  pAdjustMethod = "BH",
  verbose = TRUE) %>%
  filter(!str_detect(Description, "drug")) %>% 
  filter(!str_detect(Description, "cancer")) %>% 
  clusterProfiler::simplify(cutoff=0.75, 
  by="p.adjust", 
  select_fun=min)

ego2_MF <- gseGO(geneList  = geneList,
  OrgDb= org.My.eg.db,
  keyType = "GID",
  ont = "MF",
  minGSSize = 10,
  maxGSSize = 500,
  eps =0,
  pvalueCutoff = 0.05,
  pAdjustMethod = "BH",
  verbose = TRUE) %>%
  filter(!str_detect(Description, "drug")) %>% 
  filter(!str_detect(Description, "cancer")) %>% 
  clusterProfiler::simplify(cutoff=0.75, 
                            by="p.adjust", 
                            select_fun=min)





ekp2 = GSEA(
  geneList,
  TERM2GENE = pathway2gene,
  TERM2NAME = pathway2name,
  minGSSize = 10,
  maxGSSize = 500,
  pvalueCutoff = 0.05) %>%
  filter(!str_detect(Description, "drug")) %>% 
  filter(!str_detect(Description, "cancer")) %>% 
  filter(!str_detect(ID, "05322")) %>% 
  filter(!str_detect(ID, "04217")) %>% 
  filter(!str_detect(ID, "05146")) %>% 
  filter(!str_detect(ID, "04973")) %>% 
  filter(!str_detect(ID, "04970")) %>% 
  filter(!str_detect(ID, "04612")) %>% 
  filter(!str_detect(ID, "04911")) %>% 
  filter(!str_detect(ID, "04914")) %>% 
  filter(!str_detect(ID, "02026"))


ego2_BP_df <- data.frame(ego2_BP)
ego2_CC_df <- data.frame(ego2_CC)
ego2_MF_df <- data.frame(ego2_MF)
ekp2_df <- as.data.frame(ego2)

write.csv(ekp2_df,'ekp2_df.csv')
write.csv(ego2_BP_df,'enrichGO_BP.csv')
write.csv(ego2_CC_df,'enrichGO_CC.csv')
write.csv(ego2_MF_df,'enrichGO_MF.csv')


## 画图


p_ego2_BP = gseaplot2(ego2_BP, geneSetID = 1:10,
  title = "Biological process",
  pvalue_table = FALSE
)
p_ego2_MF = gseaplot2(ego2_MF, geneSetID = 1:10,
  title = "Molecular function",
  pvalue_table = FALSE
)

p_ego2_CC = gseaplot2(ego2_CC, geneSetID = 1:10,
  title = "Cellular component",
  pvalue_table = FALSE
)


p_ekp2 = gseaplot2(ekp2, geneSetID = 1:10,
  title = "KEGG Pathway",
  pvalue_table = FALSE
)




ggsave('p15_ego2_CC.pdf', plot = p_ego2_CC, width = 15, height = 12)
ggsave('p15_ego2_BP.pdf', plot = p_ego2_BP, width = 15, height = 12)
ggsave('p15_ego2_MF.pdf', plot = p_ego2_MF, width = 15, height = 12)
ggsave('p15_ekp2.pdf', plot = p_ekp2, width = 15, height = 12)



```

