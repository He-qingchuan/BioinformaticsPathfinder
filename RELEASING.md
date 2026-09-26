# 统一版本管理与发布

BioinformaticsPathfinder 是一个项目。Linux、R、Python、转录组和单细胞等课程共享同一发布编号。每个 Git 标签标识当时整个仓库的完整状态，即使该次只更新了一门课程。

## 编号与说明

- 标签：`v1.0.0`，格式为 `v主版本号.次版本号.修订号`。
- 发布标题：`v1.0.0 · 项目统一版本基线`；以后如 `v1.1.0 · R 课程增补`。
- 修订号：文字、链接、排版或代码问题修复，如 `1.0.0 → 1.0.1`。
- 次版本号：增加章节、课程能力或完成某门教材重构，如 `1.0.1 → 1.1.0`。
- 主版本号：项目整体体系或使用方式发生重大变化，如 `1.1.0 → 2.0.0`。

这是本项目对教材发布的约定，不要求每次提交都增加版本号。更新说明写明涉及的课程或模块、新增内容、改进、修复、使用注意事项及验证范围；不要把原有内容全部描述为本次新增。

## 唯一版本来源

根目录 `VERSION` 是唯一手动维护的当前版本。课程目录的 `VERSION`、Linux/R 的课程配置版本、各 README 的版本区块由 `python tools/project_release.py sync` 生成，目的是让单独下载的课程也能离线重建。它们是项目版本的快照，不是独立课程版本，不能单独递增。

`CHANGELOG.md` 在根目录统一记录新发布。课程内旧 CHANGELOG 仅保留迁移前历史。不要新增 `linux-v…`、`r-v…` 等课程标签；旧标签和附件不得覆盖或移动。

## 发布步骤

1. 在当前项目目录的工作分支完成修改，更新根 VERSION，并在根 CHANGELOG 顶部填写对应版本说明。
2. 安装构建依赖：`python -m pip install -r tools/requirements.txt`。
3. 运行 `python tools/project_release.py sync` 同步快照和 README，再运行 `python tools/project_release.py build` 重建各课程页面。
4. 将源文件和生成页面加入 Git。运行 `python tools/project_release.py check`、受影响课程的检查以及 `python tools/project_release.py package`。打包仅使用 Git 索引列出的文件，未纳入 Git 的文件不会被静默发布。
5. 检查完整包、课程分包及 SHA256SUMS，提交并通过 CI 后合并到 main。
6. 在已验证提交上创建与根 VERSION 一致的注释标签（如 `git tag -a v1.0.1 -m 'v1.0.1：修复课程链接'`），推送这个标签。已发布标签不重写。
7. 从该标签检出或确认当前提交与标签一致，运行打包；创建同名 GitHub Release，上传全部 `dist/BioinformaticsPathfinder-v版本号*.zip` 与 `dist/SHA256SUMS`。正式发布使用 Latest，预发布不使用。
8. 核对线上页面、发布附件及校验值。GitHub 默认的源码归档与附加的离线教材包用途不同，阅读教材优先使用附加 ZIP。

自动检查只验证和打包，不自动推送标签或发布未审查的修改。仓库保留一个正式项目目录，使用分支、提交与标签管理历史。

## 统一发布的附件

例如项目 `v1.0.0`：

- `BioinformaticsPathfinder-v1.0.0.zip`：所有课程与项目维护资料。
- `BioinformaticsPathfinder-v1.0.0-linux.zip`、`…-r.zip`、`…-python.zip`、`…-rnaseq.zip`、`…-scrna.zip`：按课程分包，属于同一项目版本。
- `SHA256SUMS`：上述文件的 SHA-256 校验值。

历史课程 Release 保留原标签和原附件，只在标题及说明中注明“历史课程独立发布”。最新项目版本统一使用根级 `v…` 标签。
