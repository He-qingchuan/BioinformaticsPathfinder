## A. SSH 与文件传输

这一节只供已经有服务器账号的人选读。没有服务器不影响完成全部主线。

使用提供给你的真实账号和主机地址替换以下大写占位符；示例不是可直接连接的服务器：

```bash
ssh USERNAME@HOST
```

有指定端口时使用 `ssh -p PORT USERNAME@HOST`。首次连接会显示主机密钥指纹，应向服务器提供方核对。登录后先用 `pwd` 和 `whoami` 确认当前位置与身份；`exit` 退出远程 Shell。

文件不会因为登录而自动从本机传过去。在本机终端可以使用 `scp -r linux-lab USERNAME@HOST:~/` 上传整个练习目录；scp 的端口选项是大写 `-P`，与 ssh 不同。路径中的空格与远程路径解析更容易出错，初次使用可选图形化文件传输工具。

`nohup 命令 >日志 2>&1 &` 是常见的后台运行形式；它忽略挂断信号并安排输出，但仍不是保证任务成功、机器不重启的服务托管。长任务还应保存输入、版本、日志和结果。

## B. Conda：在需要时再准备一个工具箱

Conda 用于管理一组软件及依赖。它不是 Linux 入门的前提，也不是虚拟机。需要时按 [Miniforge 官方说明](https://github.com/conda-forge/miniforge)安装适合自己操作系统和处理器架构的版本；核对下载来源，不照抄陌生安装脚本。

已经安装且完成 Shell 初始化后，可练习以下基本操作（会联网下载软件）：

```bash
conda create -n text-lab -c conda-forge --strict-channel-priority tree
conda activate text-lab
tree --version
command -v tree
conda deactivate
```

这里用 tree 这样的小工具观察环境的作用，不需要为每个环境额外安装 Python。`conda env list` 查看已有环境，`conda env remove -n text-lab` 删除这个专门创建的练习环境。删除前退出环境并确认名称。

如果创建环境提示同名已存在，先查看列表；不要为了重做示例删除自己仍在使用的环境。软件环境与数据目录是两回事，激活环境不会自动把你带到 linux-lab。

## C. sed 与 awk：从一个小用途开始

下面在 linux-lab 中操作。sed 的这条替换只输出变更后的文本，不改写原文件；先理解输出，再决定是否保存到新文件。

```bash
sed 's/Lake:/Water:/g' notes/morning.txt
```

awk 可按字段处理简单表格，下面使用制表符分隔，跳过表头，再筛选 site 为 lake 的记录，输出物种与数量。

```bash
awk -F '\t' 'NR > 1 && $2 == "lake" {print $3, $4}' tables/observations.tsv
```

这里 NR 是当前记录编号，$2 是 awk 看到的第二个字段。它与 Shell 脚本的第二个位置参数不是同一种上下文；外层单引号让 Shell 把这段程序完整交给 awk。不要让两个语言的变量规则混在一起。

## D. 配置文件与常见报错

Bash 的启动方式影响哪些配置文件会被读取。`.bashrc` 常用于交互式非登录 Bash 的设置；登录 Shell 会读取对应登录配置，有些发行版再由那里载入 `.bashrc`。不能简单说“所有 Shell 每次启动都读取同一个文件”。修改前先备份，并在另一个终端验证。

| 现象 | 先检查什么 |
| --- | --- |
| No such file or directory | pwd、大小写、路径、材料是否复制完整 |
| command not found | 拼写、是否已安装、PATH、当前激活环境 |
| Permission denied | 身份、文件与父目录权限、是否需要执行权限 |
| 屏幕停在一个查看界面 | 是否仍在 less、nano 或 top，查看它的退出方式 |
| 文件看起来为空 | 是否被 > 覆盖，程序是否把诊断写到标准错误 |
| 带空格的文件打不开 | 参数是否使用合适的引号 |
| 脚本报 fi 或 done 的语法错 | 检查配对与空格，用 bash -n 检查语法 |

## E. 原始资料与延伸阅读

正文为本轮重新编写，练习数据为虚构小数据，插图为本教材生成的 SVG。旧教材保存在仓库重构前的 Git 历史中。下列原始文档用于核对术语、语法和操作条件；点击外链时需要联网。

- [Linux 内核项目：Linux 与发行版](https://www.kernel.org/linux.html)
- [GNU Bash 手册](https://www.gnu.org/software/bash/manual/)
- [GNU Coreutils 手册](https://www.gnu.org/software/coreutils/manual/)
- [GNU grep 手册](https://www.gnu.org/software/grep/manual/)
- [GNU tar 手册](https://www.gnu.org/software/tar/manual/)
- [Ubuntu 命令行入门](https://documentation.ubuntu.com/desktop/en/latest/tutorial/the-linux-command-line-for-beginners/)
- [Microsoft：安装 WSL](https://learn.microsoft.com/en-us/windows/wsl/install)
- [Conda：管理环境](https://docs.conda.io/projects/conda/en/stable/user-guide/tasks/manage-environments.html)
