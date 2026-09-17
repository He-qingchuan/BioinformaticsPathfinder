# 文件用途｜把已验证参数安全传入原章节入口，并定位现有软件。
# 使用：由 0script/tools/run_chapter.py 导入；只提供规则/函数，不作为单独分析步骤执行。输入输出与每个
#   参数见下面接口注释。
# 注释用 # 独立行说明；现有 docstring 和程序帮助文本保持原样，不把注释变成执行时读取的新配置。

"""只负责执行适配：参数注入、原工具定位与固定步骤调度，不包含统计算法。"""
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys



# 接口｜r_literal：将已校验的 JSON 值转成 R 字面量。
# 参数：
# value（必填，无默认值）：已通过 validate_parameters 的标量或列表；不能把任意字典/程序文本直接当 R 表
#   达式。
# 返回/写出与边界：返回 R 代码片段字符串：None→NULL、布尔→TRUE/FALSE、列表→c()，空列表→logical()；字符
#   串用 JSON 转义，不执行值中的代码。
def r_literal(value):
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, list):
        return "c(" + ",".join(r_literal(x) for x in value) + ")" if value else "logical()"
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    return repr(value)


# 接口｜inject_parameters：只在唯一的显式入口标记处插入已验证参数。
# 参数：
# code（必填，无默认值）：从 MD 提取的原始代码字符串，含默认赋值、标记和函数调用。
# block（必填，无默认值）：执行单元名称，如 volcano，用来定位 # interface-parameters 标记。
# language（必填，无默认值）：字符串 r 或 bash；分别使用 R 字面量或 shell 安全引用。
# values（必填，无默认值）：该单元已经验证的参数字典；在默认赋值之后、函数调用之前覆盖本次入口值。
# 返回/写出与边界：返回新代码字符串，不修改输入 code。无参数原样返回，标记缺失/重复或 shell 收到数组时
#   报错；执行发生在外层。
def inject_parameters(code, block, language, values):
    """仅在显式注释点注入已验证的标量/向量，不搜索替换代码中的数字。"""
    if not values:
        return code
    marker = "# interface-parameters: " + block
    if code.count(marker) != 1:
        raise ValueError(f"{block} 缺少唯一参数入口；拒绝猜测或改写其他代码")
    if language == "r":
        additions = [f"{key} <- {r_literal(value)}" for key, value in values.items()]
    else:
        if any(isinstance(value, (list, dict)) for value in values.values()):
            raise ValueError("Shell 参数仅接受已验证标量")
        additions = [key + "=" + shlex.quote(str(value)) for key, value in values.items()]
    return code.replace(marker, marker + "\n# 以下值来自本次运行的参数快照。\n" + "\n".join(additions))


# 接口｜tool_environment：根据真实 Conda 环境补齐 Trinity 附带脚本位置。
# 参数：
# conda（必填，无默认值）：Conda 可执行文件路径字符串。
# environment（必填，无默认值）：已有环境名字符串；rnaseq 额外查找 Trinity util/差异分析目录。
# 返回/写出与边界：返回环境变量字典，供当前子进程使用；不永久修改系统 PATH，不创建个人软链接。
def tool_environment(conda, environment):
    """从实际 Conda 环境定位 Trinity 附带脚本，不依赖个人软链接/包装器。"""
    result = subprocess.run([conda, "run", "-n", environment, "python", "-c",
                             "import sys; print(sys.prefix)"], capture_output=True, text=True, check=True)
    prefix = Path(result.stdout.strip().splitlines()[-1])
    directories = [prefix / "bin"]
    if environment == "rnaseq":
        directories += [prefix / "bin/util", prefix / "bin/util/support_scripts",
                        prefix / "bin/Analysis/DifferentialExpression"]
        directories += list(prefix.glob("opt/trinity*/util"))
        directories += list(prefix.glob("opt/trinity*/util/support_scripts"))
        directories += list(prefix.glob("opt/trinity*/Analysis/DifferentialExpression"))
    env = os.environ.copy()
    env["PATH"] = os.pathsep.join(str(p) for p in directories if p.is_dir()) + os.pathsep + env.get("PATH", "")
    return env

