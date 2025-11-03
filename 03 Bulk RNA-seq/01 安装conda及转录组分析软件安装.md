## Linux之安装conda

### 0修改命令行配

```sh
#感兴趣的自行更改
#\[\033]2;\h:\u \w\007\]  # 设置终端窗口标题：主机名:用户名 工作目录
#\033[33;1m\u            # 黄色加粗显示用户名
#\033[35;1m\t            # 紫色加粗显示24小时制时间 (HH:MM:SS)
#\033[0m                 # 重置颜色属性
#\033[36;1m\w            # 青色加粗显示当前工作目录
#\033[0m                 # 再次重置颜色
#\n                      # 换行到新提示符行
#\[\e[32;1m\]$           # 绿色加粗显示$符号（root用户时为#）
#\[\e[0m\]               # 最终重置所有颜色属性
echo  'export PS1="\[\033]2;\h:\u \w\007\033[33;1m\]\u \033[35;1m\t\033[0m \[\033[36;1m\]\w\[\033[0m\]\n\[\e[32;1m\]$ \[\e[0m\]" ' >> ~/.bashrc
source  ~/.bashrc
#`~/.bashrc`：系统配置文件，包含专用于你的 bash shell 的bash信息、设置，每次登录或打开新的 shell 时，该文件会被自动读取和执行。
```



### 1下载

```{bash}
cd ~
nohup wget -c https://repo.anaconda.com/archive/Anaconda3-2025.06-1-Linux-x86_64.sh &
#在conda文件的目录下输入命令安装，一路回车，直到他要求输入yes
bash Anaconda3-2025.06-1-Linux-x86_64.sh

```

### 2配置镜像源

```{bash}
####
## 配置镜像
# 下面四行配置北京外国语大学的conda的channel地址（其实现在北京外国语也转用清华的镜像了）
conda config --add channels https://mirrors.bfsu.edu.cn/anaconda/pkgs/main/ 
conda config --add channels https://mirrors.bfsu.edu.cn/anaconda/cloud/conda-forge/ 
conda config --add channels https://mirrors.bfsu.edu.cn/anaconda/cloud/bioconda/ 
conda config --set show_channel_urls yes 

# 下面这四行配置清华大学的conda的channel地址（如果体验不好再换成清华）
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main/
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge/
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/bioconda/
conda config --set show_channel_urls yes

# 下面这四行配置中科大的conda的channel地址
rm ~/.condarc
conda config --add channels https://mirrors.ustc.edu.cn/anaconda/pkgs/main/
conda config --add channels https://mirrors.ustc.edu.cn/anaconda/pkgs/free/
conda config --add channels https://mirrors.ustc.edu.cn/anaconda/cloud/conda-forge/
conda config --add channels https://mirrors.ustc.edu.cn/anaconda/cloud/msys2/
rm ~/.condarc
#配置南方科技大学conda镜像 
conda config --add channels https://mirrors.sustech.edu.cn/anaconda/cloud/bioconda/
conda config --add channels https://mirrors.sustech.edu.cn/anaconda/cloud/conda-forge/
conda config --add channels https://mirrors.sustech.edu.cn/anaconda/pkgs/main/
conda config --set show_channel_urls yes





# 如果需要官方频道，可以添加下面这两行配置官网的channel地址（不推荐）
conda config --add channels conda-forge 
conda config --add channels bioconda



# 配置好镜像之后，清空一下环境中的缓存
conda clean -i 

# 删除defaults频道
sed -i '/defaults/d' ~/.condarc

## 配置镜像成功
# 查看配置结果
cat ~/.condarc
```

### 3安装mamba

```{bash}
conda install mamba
```



### 4创建小环境和安装软件

```{bash}
## 2.环境创建和安装软件
# 创建名为rnaseq_up的软件环境来安装转录组学分析的生物信息学软件
# 在小环境中安装生信软件——使用connda  or  mamba
mamba create -n rnaseq_up  fastqc fastp multiqc salmon  trinity -y
#conda create -n rnaseq_up  fastqc fastp multiqc salmon  trinity -y 

# 每次运行前，激活创建的小环境rna
conda activate rnaseq_up
fastqc --version
fastp --version
multiqc --version
salmon --version
Trinity --version

# multiqc
multiqc --help
# salmon
salmon --help
# fastp
fastp --help

# 查看当前conda环境
conda info -e
conda env list

# 退出小环境
conda deactivate



```





### 5conda其他用法更新软件：conda update 软件名，卸载软件，删除环境，克隆环境，查找软件

```{bash}
# 更新软件：conda  update  软件名
# 卸载软件：conda  remove  软件名
# 删除环境：conda  remove  -n   环境名
# 克隆环境：conda  create –n 新环境名 –clone  旧环境名
# 查找软件：conda  search  软件名
# 查找软件常用的链接：
# 
# - https://anaconda.org/search
# 
# - [https://bioconda.github.io](https://bioconda.github.io/)[/](https://bioconda.github.io/)

```





#### 

