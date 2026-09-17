# 文件用途｜校验命令行 JSON 参数，不运行任何统计算法。
# 使用：由 0script/tools/run_chapter.py 导入；只提供规则/函数，不作为单独分析步骤执行。输入输出与每个
#   参数见下面接口注释。
# 注释用 # 独立行说明；现有 docstring 和程序帮助文本保持原样，不把注释变成执行时读取的新配置。

"""仅校验 CLI JSON 参数，不依赖网页或后台任务。"""
import math
from catalog import PARAMETERS

# 接口｜boolean：把布尔或 TRUE/FALSE 文本规范成 Python bool。
# 参数：
# value（必填，无默认值）：bool 或大小写不限的 TRUE/FALSE 文本；不接受随意的 yes/1 代替规范值。
# 返回/写出与边界：返回 True/False；其他字符串报错，不把非空的 FALSE 字符串误判为真。
def boolean(value):
    if isinstance(value, bool): return value
    if str(value).upper() in ("TRUE", "FALSE"): return str(value).upper() == "TRUE"
    raise ValueError("布尔值须为 TRUE 或 FALSE")

# 接口｜validate_parameters：逐个校验 CLI 参数名、类型、范围和组合约束。
# 参数：
# parameters（必填，无默认值）：按执行单元分组的 JSON 字典，例如 volcano 下放 top_n；不是 project.env
#   的全部字段。
# action（默认 'analyse'）：字符串 analyse 或 redraw；redraw 只允许 catalog 标为 style=True 的参数。
# 返回/写出与边界：返回只含用户实际提供项的规范字典，不补齐全部默认值；未知参数、分析参数用于 redraw、
#   矛盾范围时报错，不执行任何代码。
def validate_parameters(parameters, action="analyse"):
    clean = {}
    # 按单元和白名单逐项验证，而不是把 JSON 当任意 R/Bash 程序执行。列表和标量分别转换，禁止未知参数静默失
    #   效。
    for block, values in parameters.items():
        if block not in PARAMETERS or not isinstance(values, dict):
            raise ValueError(f"未知参数组: {block}")
        clean[block] = {}
        for name, value in values.items():
            spec = PARAMETERS[block].get(name)
            if not spec:
                raise ValueError(f"未知参数: {block}.{name}")
            if action == "redraw" and not spec["style"]:
                raise ValueError(f"{block}.{name} 改变分析，不属于仅重绘参数")
            kind = spec["type"]
            array = kind in ("numbers", "integers", "strings", "booleans")
            if array and not isinstance(value, list):
                raise ValueError(f"{block}.{name} 应为数组")
            values_to_check = value if array else [value]
            if array and not value and name not in ("pvalue_tables", "line_variants"):
                raise ValueError(f"{block}.{name} 不能为空")
            converted = []
            for item in values_to_check:
                if kind in ("boolean", "booleans"):
                    item = boolean(item)
                elif kind in ("integer", "integers", "number", "numbers"):
                    if isinstance(item, bool):
                        raise ValueError(f"{name} 应为数值，不是布尔值")
                    number = float(item)
                    if not math.isfinite(number) or (kind in ("integer", "integers") and not number.is_integer()):
                        raise ValueError(f"{name} 数值无效")
                    if spec["minimum"] is not None and number < spec["minimum"] or spec["maximum"] is not None and number > spec["maximum"]:
                        raise ValueError(f"{name} 超出允许范围")
                    item = int(number) if kind in ("integer", "integers") else number
                elif not isinstance(item, str):
                    raise ValueError(f"{name} 应为文本")
                if spec["choices"] is not None and item not in spec["choices"]:
                    raise ValueError(f"{name} 不在允许选项内")
                converted.append(item)
            clean[block][name] = converted if array else converted[0]
    # 范围逐项合格后还需检查组合：最小基因集不能大于最大值，PCA 两轴不能相同，周期上下界不能倒置。
    for block, values in clean.items():
        defaults={name:spec["default"] for name,spec in PARAMETERS[block].items()}
        effective={**defaults,**values}
        if "minGSSize" in effective and "maxGSSize" in effective and effective["minGSSize"] > effective["maxGSSize"]:
            raise ValueError(f"{block}: 最小基因集大于最大基因集")
        if block=="sample_relationships" and effective["pca_x"]==effective["pca_y"]:
            raise ValueError("PCA 横轴和纵轴不能是同一个主成分")
    if clean.get("jtk_analysis", {}).get("minper", 20) > clean.get("jtk_analysis", {}).get("maxper", 28):
        raise ValueError("最小周期不能大于最大周期")
    return clean


