# 文件用途｜第 18 章：用实际物种元数据调用 DIAMOND 路线的 OrgDb 构建。
# 运行位置：能看见 0script 的项目根目录。R 函数库通过 source 加载定义及共用依赖；调用函数才执行本文件
#   对应的分析/写出。
# 改参方式：在同编号 MD 的参数入口赋值，再执行下面的具名调用；函数默认值只在该形参未传入时使用。编辑文
#   件不会刷新内存中的旧函数/旧变量，需重新 source/赋值。
# 接口说明：每个函数前列出用途、形参和输出；嵌套函数读取的外层变量属于闭包，不能误当成漏传的独立参数。
# 共用语法：source 载入脚本；readRenviron 读取配置；Sys.getenv 取文本，as.numeric/as.integer 转数值；
#   local=TRUE 表示定义放在当前调用环境。
# 表格/图形约定：write.table 的 sep="\t" 用 TSV、quote=FALSE 不另加引号、row.names=FALSE 不写 R 行号；
#   check.names=FALSE 保留原 ID。ggsave 的图幅按英寸，dpi 主要控制 PNG。

# 接口｜run_diamond_orgdb：用实际物种元数据调用 DIAMOND 路线的 OrgDb 构建。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# tax_id（必填，无默认值）：字符形式的真实 NCBI taxonomy ID；写入自建 OrgDb 元数据，不是排除供体的税号
#   。案例为 3702，换物种应核实后改本章入口。
# genus（必填，无默认值）：字符属名；自建 OrgDb 元数据及包命名使用，案例 Arabidopsis。须与真实物种一致
#   ，不是矩阵 gene_id 前缀。
# species（必填，无默认值）：字符种加词；自建 OrgDb 使用，如 thaliana，不是任意项目显示名。换物种与
#   genus、tax_id 一起核实。
# 返回/写出与边界：构建第 18 章的局部数据库及派生表；不重新做蛋白搜索。需先完成代表验证和 eggNOG 注释。
run_diamond_orgdb <- function(tax_id, genus, species) {
  if (length(tax_id)!=1L || is.na(tax_id) || !grepl("^[1-9][0-9]*$", tax_id) ||
      length(genus)!=1L || is.na(genus) || !nzchar(genus) ||
      length(species)!=1L || is.na(species) || !nzchar(species))
    stop("先在第 18 章填写已核实的 tax_id、genus、species；函数不会借用案例物种")
  source("0script/tools/metadata.R", local = TRUE)
  source("0script/tools/outputs.R", local = TRUE)
  if (file.exists("0script/project.env")) readRenviron("0script/project.env")
  # 功能：载入已定义的建库函数及项目物种参数；真正建库在下一代码框显式调用。
  library(tidyverse)
  library(AnnotationForge)
  library(AnnotationDbi)
  source("0script/scripts/18_orgdb_builder.R", local = TRUE)
  readRenviron("0script/project.env")

  # 功能：明确传入物种元数据进行建库；已有完整 OrgDb 本次不重复运行。
  # 属名与种加词分开，如 Arabidopsis 与 thaliana；真实值来自项目入口。
  build_orgdb(method = "diamond", tax_id = tax_id, genus = genus, species = species)
}
