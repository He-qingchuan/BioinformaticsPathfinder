# 文件用途｜从 Markdown 标记识别执行单元，不创建另一套分析逻辑。
# 使用：由 0script/tools/run_chapter.py 导入；只提供规则/函数，不作为单独分析步骤执行。输入输出与每个
#   参数见下面接口注释。
# 注释用 # 独立行说明；现有 docstring 和程序帮助文本保持原样，不把注释变成执行时读取的新配置。

"""Read executable Markdown sections without maintaining a second analysis script.

Consecutive fences with the same execution name form one process. Explanatory
prose and unmarked, optional examples between them are not executed. A task name
must not recur after another task has begun: silently reordering it is unsafe.
"""
import re


# 接口｜chapter_id：规范化章节编号而保留 04.5 的小数部分。
# 参数：
# value（必填，无默认值）：可转为字符串的编号；不要先 int() 截掉 4.5。
# 返回/写出与边界：返回字符串：04→4、04.5→4.5；仅允许 1–20 和 4.5，非法编号报错。
def chapter_id(value):
    """Canonical textual ID: 04 and 4 are 4; 04.5 is 4.5, never truncated."""
    text = str(value)
    if not re.fullmatch(r"\d+(?:\.\d+)?", text):
        raise ValueError("章节编号须为整数或 4.5")
    parts = tuple(int(x) for x in text.split("."))
    if len(parts) == 2 and parts != (4, 5):
        raise ValueError("当前小数章节仅支持 4.5")
    if not 1 <= parts[0] <= 20: raise ValueError("章节编号范围为 1–20，另含 4.5")
    return ".".join(str(x) for x in parts)


# 接口｜chapter_prefix：生成文件使用的两位章节前缀。
# 参数：
# value（必填，无默认值）：有效章节编号，规则同 chapter_id。
# 返回/写出与边界：返回 01、12 或 04.5 等字符串，先调用 chapter_id 校验；不生成文件。
def chapter_prefix(value):
    parts = chapter_id(value).split(".")
    return f"{int(parts[0]):02d}" + ("." + parts[1] if len(parts) > 1 else "")


# 接口｜chapter_from_filename：从约定文件名识别章节。
# 参数：
# name（必填，无默认值）：文件名字符串；应以两位编号（可加 .5）及空格或下划线开头。
# 返回/写出与边界：返回规范章节字符串，无匹配前缀时返回 None，不把附录或任意数字当章节。
def chapter_from_filename(name):
    match = re.match(r"^(\d{2}(?:\.\d+)?)(?:\s|_)", name)
    return chapter_id(match[1]) if match else None


# 接口｜extract_blocks：提取带 execute 标记的 MD 代码单元。
# 参数：
# body（必填，无默认值）：整篇 Markdown 文本字符串；标记须紧邻 bash/r 代码围栏，章节正文不当作代码。
# 返回/写出与边界：返回 (name,environment,language,code) 元组列表；同名相邻单元合并，不连续重现或环境/
#   语言冲突报错。无标记示例不会执行。
def extract_blocks(body):
    pattern = r"<!-- execute: ([a-z0-9_]+) env=([a-z0-9_]+) -->\s*```(bash|r)\n(.*?)\n```"
    blocks = []
    seen = set()
    for name, environment, language, code in re.findall(pattern, body, re.S):
        if blocks and blocks[-1][0] == name:
            previous = blocks[-1]
            if previous[1:3] != (environment, language):
                raise ValueError(f"Task {name}: cannot mix environments or languages")
            blocks[-1] = (*previous[:3], previous[3] + "\n\n" + code)
        else:
            if name in seen:
                raise ValueError(f"Task {name}: execution sections must be consecutive")
            blocks.append((name, environment, language, code))
            seen.add(name)
    return blocks
