### 09 样品间差异表达(DESeq2)

```{bash}

cd ../5DESeq2
#拷贝基因表达矩阵数据到当前目录
ln -s  ../3Salmon/quanti/ ./
ln -s ../4SampleHheatmapPCA/samples.txt ./

#创建一个包含所有处理的文本文件
# awk '!seen[$1]++ {print $1}' samples.txt：提取第一列并去除重复值，同时保持第一次出现的顺序
# seen[$1]++ 创建一个数组来跟踪已经见过的值
# !seen[$1]++ 只在第一次见到某个值时条件为真
# 这样会保持原始文件中分组名称的出现顺序
# tac：将行顺序倒置（从最后一行到第一行）
# > elements.txt：将结果保存到新文件
awk '!seen[$1]++ {print $1}' samples.txt | tac > elements.txt
#二选一，或者使用下列代码echo -e "ZT20\nZT16\nZT12\nZT8\nZT4\nZT1\nZT0" > elements.txt








####生成差异表达分析中需要比对的组合文件contrasts.txt
# 本 awk 脚本从名为 elements.txt 的文本文件中读取数据，并生成所有可能的两两组合。
# 脚本确保每个组合是唯一的，并且不考虑元素的顺序（例如，组合 "A B" 和 "B A" 视为相同，只生成 "A B"）。
# 这适用于需要从一组元素中快速生成配对的场景，如统计分析、数据处理和任何需要元素配对的应用。
# 输入文件：
# elements.txt - 此文件应包含您想要组合的所有元素，每个元素独占一行。
# 脚本参数和变量解释：
# NR - awk 的内置变量，代表当前读取的记录号（即行号），从1开始。
# lines[NR] - 一个数组，用于按行号索引存储输入文件中的每行数据。
# 输出文件：
# contrasts.txt - 包含生成的所有组合，每个组合占一行，元素之间由一个空格分隔。
# 使用说明：
# 确保 elements.txt 文件位于同一目录下或指定正确的文件路径。
# 在终端运行此脚本，组合结果将保存在 contrasts.txt 文件中。
awk '{
    # 主体块：读取每一行并存储
    # 将当前行的内容存储到 lines 数组中，索引为当前行号 NR。
    # 这允许在脚本的 END 块中使用所有已读取的数据。
    lines[NR] = $0
}
END {
    # 结束块：生成和打印组合
    # 在文件读取完毕后执行此代码块，生成所有唯一的两两组合。
    
    # 外层循环从第一行开始到倒数第二行，以确保至少可以与一行进行配对。
    for (i = 1; i < NR; i++) {
        # 内层循环从当前外层循环的行号 + 1开始，直到文件的最后一行。
        # 这样做避免了元素与自己组合，同时保证组合如 "A B" 和 "B A" 不会重复出现。
        for (j = i + 1; j <= NR; j++) {
            # 打印当前索引行和其后行的内容，两者之间用一个空格分隔。
            print lines[i], lines[j]
        }
    }
}' elements.txt > contrasts.txt







###差异表达分析
# 指定运行的 Perl 脚本路径 run_DE_analysis.pl
# 提供基因表达矩阵文件 quanti/genes.gene.counts.matrix
# 设置差异表达分析方法为 DESeq2
# 提供样本信息文件 samples.txt，包含样本和对应组信息
# 提供对比组文件 contrasts.txt，定义不同组之间的对比
# 设置输出目录为 DE_analysis
 # --contrasts contrasts.txt \注释掉，改为默认的两两比对，但是顺序是按照字母顺序排列
run_DE_analysis.pl \
  --matrix quanti/genes.gene.counts.matrix \
  --method DESeq2 \
  --samples_file samples.txt \
  --contrasts contrasts.txt \
  --output DE_analysis

# 使用 awk 处理所有 DE_results 文件，合并为一个结果文件
# FNR==1 && NR!=1：检查当前文件的第一行，跳过第一个文件的第一行（FNR为当前文件行号，NR为总行号）
# 在合并文件时，避免重复输出每个文件的表头（第一行）。只保留每个文件的数据行，第一行（表头）会被跳过
# {print}：打印当前行的内容
# 将所有 DE_analysis 目录下的 *DE_results 文件内容合并并输出到 quanti/de_result.tsv 文件中
# 结果文件将包含所有 DE_results 文件的内容，但去除了每个文件的表头（只保留一个表头）
awk 'FNR==1 && NR!=1{next}{print}' DE_analysis/*DE_results > de_result.tsv
# 第一列加上gene_id
sed -i '1s/^/gene_id	/' de_result.tsv
```

