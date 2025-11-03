### 17非模式生物GO和KEGG富集分析

```r
#安装
BiocManager::install("clusterProfiler")
BiocManager::install("enrichplot")
BiocManager::install("thomasp85/patchwork")
install.packages("magrittr")


# 其他物种的富集分析
## 准备基因列表
library(tidyverse)
library(magrittr)
library(clusterProfiler)
library(org.My.eg.db, lib.loc = "/u3/hekun/orgDb/egg2ord/orgdb_diamond/R_Library/")
library(patchwork)
library(ggplot2)
library(magrittr)
library(enrichplot)



load(file = "7volcano/de_result.Rdata")
load(file = "7volcano/my_de_result.Rdata")



# 1. 候选基因向量（gene）
# 一个字符型向量，包含感兴趣的基因，如差异表达基因、WGCNA 得到的关键模块里的基因,mfuzz中的模块基因等。
 gene <- filter(my_de_result, 
               direction != "ns") %>%
 pull(gene_id)
# 2. 基因差异向量（geneList）
# 一个有名向量，记录差异大小，名字为基因ID，值为 logFC，按 logFC 降序排列。
geneList <- my_de_result$log2FoldChange
names(geneList) <- my_de_result$gene_id
geneList <- sort(geneList, decreasing = T)


load(file = "9Enrichment_Analysis/geneList.Rdata")
load(file = "9Enrichment_Analysis/geneList.Rdata")








###GO富集分析
######参数	说明	常用值
#gene	输入基因列表	差异表达基因或其他感兴趣的基因集合
#universe	背景基因集	geneList中的基因名
#OrgDb	物种注释数据库	org.At.tair.db(拟南芥), org.Hs.eg.db(人类)等
#keyType	基因ID类型	"TAIR", "ENTREZID", "ENSEMBL", "SYMBOL"等
#ont	GO类别	"ALL", "BP", "MF", "CC"
#pAdjustMethod	p值校正方法	"fdr", "BH", "bonferroni"等
#pvalueCutoff	p值阈值	通常0.05或更严格
#qvalueCutoff	q值阈值	通常0.05或0.2
#readable	是否转换ID为可读名称	TRUE或FALSE
#minGSSize	基因集最小大小	10
#maxGSSize	基因集最大大小	500
######


keytypes(org.My.eg.db)
#GO富集分析
ego_CC <- enrichGO(gene=gene, universe = names(geneList),OrgDb= 'org.My.eg.db', keyType="GID", ont="CC", pvalueCutoff= 0.05,qvalueCutoff= 0.05,readable = FALSE,minGSSize = 10,maxGSSize = 500,pAdjustMethod = "BH")

ego_MF <- enrichGO(gene=gene, universe = names(geneList),OrgDb= 'org.My.eg.db', keyType="GID", ont="MF", pvalueCutoff= 0.05,qvalueCutoff= 0.05,readable = FALSE,minGSSize = 10,maxGSSize = 500,pAdjustMethod = "BH")

ego_BP <- enrichGO(gene=gene, universe = names(geneList),OrgDb= 'org.My.eg.db', keyType="GID", ont="BP", pvalueCutoff= 0.05,qvalueCutoff= 0.05,readable = FALSE,minGSSize = 10,maxGSSize = 500,pAdjustMethod = "BH")


ego_ALL <- enrichGO(gene=gene, universe = names(geneList),OrgDb= 'org.My.eg.db', keyType="GID", ont="ALL", pvalueCutoff= 0.05,qvalueCutoff= 0.05,readable = FALSE,minGSSize = 10,maxGSSize = 500,pAdjustMethod = "BH")




###KEGG富集分析




# # KEGG Pathway 的 ORA富集及可视化
# ## KEGG Pathway 富集
# 查询物种是否支持：https://www.genome.jp/kegg/catalog/org_list.html
# ### KEGG Pathway over-representation 富集
# 如果你研究的物种在 KEGG 数据库中包含，可以使用 enrichKEGG 来做富集。否则就需要使用 enricher() 这个通用的富集函数。
# enricher() 还需要提供两个变量：
# 1. TERM2GENE：Pathway 与基因的对应关系
# 2. TERM2NAME：Pathway 的ID与名称对应关系
#### 准备 TERM2NAME
#kegg
get_path2name <- function(){
  keggpathid2name.df <- clusterProfiler:::kegg_list("pathway")
  keggpathid2name.df[,1] %<>% gsub("path:map", "", .)
  colnames(keggpathid2name.df) <- c("path_id","path_name")
  return(keggpathid2name.df)
}
pathway2name <- get_path2name()
# 使用 gsub() 去掉 path_id 中的 "map"
pathway2name$path_id <- gsub("map", "", pathway2name$path_id)
# 查看结果
print(pathway2name)

#### 准备 TERM2GENE
emapper <- read_delim("/u3/hekun/orgDb/output_diamond/Taestivum.pep.emapper.annotations.bak", 
                      "\t", escape_double = FALSE, col_names = FALSE, 
                      comment = "#", trim_ws = TRUE) %>%
  dplyr::select(GID = X1, 
                COG = X7,
                Gene_Name = X8,
                Gene_Symbol = X9,
                GO = X10,
                KO = X12,
                Pathway = X13)

pathway2gene <- dplyr::select(emapper, Pathway, GID) %>%
  separate_rows(Pathway, sep = ',', convert = F) %>%
  filter(str_detect(Pathway, 'ko')) %>%
  mutate(Pathway = str_remove(Pathway, 'ko'))


ekg <- enricher(gene,
                TERM2GENE = pathway2gene,
                TERM2NAME = pathway2name,
                pvalueCutoff = 0.05,
                qvalueCutoff = 0.05)






#绘制条形图
p_BP_barplot <- barplot(ego_BP,showCategory = 10,label_format = 100) + ggtitle("Biological process")
p_CC_barplot <- barplot(ego_CC,showCategory = 10,label_format = 100) + ggtitle("Cellular component")
p_MF_barplot <- barplot(ego_MF,showCategory = 10,label_format = 100) + ggtitle("Molecular function")
p_ALL_barplot <- barplot(ego_ALL,showCategory = 10,label_format = 100) + ggtitle("GO")
p_KG_barplot <- barplot(ekg,showCategory = 10,label_format = 100) + ggtitle("KEGG Pathway")


#绘制点图
p_BP_dotplot <- dotplot(ego_BP,showCategory = 10,label_format = 100) + ggtitle("Biological process")
p_CC_dotplot <- dotplot(ego_CC,showCategory = 10,label_format = 100) + ggtitle("Cellular component")
p_MF_dotplot <- dotplot(ego_MF,showCategory = 10,label_format = 100) + ggtitle("Molecular function")
p_ALL_dotplot <- dotplot(ego_ALL,showCategory = 10,label_format = 100) + ggtitle("GO")
p_KG_dotplot <- dotplot(ekg,showCategory = 10,label_format = 100) + ggtitle("KEGG Pathway")

#单独保存每张图片
ggsave('9Enrichment_Analysis/ORA/p_BP_barplot.pdf', plot = p_BP_barplot, width = 10, height = 10)
ggsave('9Enrichment_Analysis/ORA/p_CC_barplot.pdf', plot = p_CC_barplot, width = 10, height = 10)
ggsave('9Enrichment_Analysis/ORA/p_MF_barplot.pdf', plot = p_MF_barplot, width = 10, height = 10)
ggsave('9Enrichment_Analysis/ORA/p_ALLGO_barplot.pdf', plot = p_ALL_barplot, width = 10, height = 10)
ggsave('9Enrichment_Analysis/ORA/p_KG_barplot.pdf', plot = p_KG_barplot, width = 10, height = 10)
ggsave('9Enrichment_Analysis/ORA/p_BP_dotplot.pdf', plot = p_BP_dotplot, width = 10, height = 10)
ggsave('9Enrichment_Analysis/ORA/p_CC_dotplot.pdf', plot = p_CC_dotplot, width = 10, height = 10)
ggsave('9Enrichment_Analysis/ORA/p_MF_dotplot.pdf', plot = p_MF_dotplot, width = 10, height = 10)
ggsave('9Enrichment_Analysis/ORA/p_ALLGO_dotplot.pdf', plot = p_ALL_dotplot, width = 10, height = 10)
ggsave('9Enrichment_Analysis/ORA/p_KG_dotplot.pdf', plot = p_KG_dotplot, width = 10, height = 10)


###拼图并保存
p1 <- (p_BP_barplot/p_CC_dotplot) |(p_MF_barplot/p_KG_barplot) 
ggsave('9Enrichment_Analysis/ORA/enrich_barplot.pdf', plot = p1, width = 20, height = 8)
p2 <- (p_BP_dotplot/p_CC_dotplot) |(p_MF_dotplot/p_KG_dotplot) 
ggsave('9Enrichment_Analysis/ORA/enrich_dotplot.pdf', plot = p2, width = 20, height = 8)



###保存结果为数据框
ego_BP_df <- data.frame(ego_BP)
ego_CC_df <- data.frame(ego_CC)
ego_MF_df <- data.frame(ego_MF)
ego_ALL_df <- data.frame(ego_ALL)
ego_df <- data.frame(ekg)
write.csv(ego_BP_df,'9Enrichment_Analysis/ORA/enrichGO_BP.csv')
write.csv(ego_CC_df,'9Enrichment_Analysis/ORA/enrichGO_CC.csv')
write.csv(ego_MF_df,'9Enrichment_Analysis/ORA/enrichGO_MF.csv')
write.csv(ego_ALL_df,'9Enrichment_Analysis/ORA/enrichGO_ALL.csv')
write.csv(ekg_df,'9Enrichment_Analysis/ORA/enrichKEGG.csv')






```

