# 设计构想

## 思路

- 以 Debian 13 为标准运行环境
- 自动运行 16 个 VPS 检测脚本
- 自动将每个脚本输出注入 `Module.txt`
- 保留完整原始日志与清洗后日志
- 支持 Win11 本机统一调度多台远程 VPS

## 架构

### 1. `raw/`

- 抓取测试源脚本或二进制
- 记录最终跳转 URL、内容类型、大小、落盘路径
- 静态扫描交互痕迹，如 `read`、`select`、`clear`、`whiptail`

输出：

- `raw/metadata.json`
- `raw/analysis.json`

### 2. `runner`

- Debian 13 上顺序执行测试项
- 每项单独工作目录
- 每项单独超时和退出码
- 使用伪终端兼容部分交互式脚本
- 自动对常见确认提示输入 `y` 或回车

输出：

- `artifacts/<run_id>/<index_name>/raw_output.txt`
- `artifacts/<run_id>/<index_name>/clean_output.txt`
- `artifacts/<run_id>/results.json`

### 3. `report`


- 读取 `templates/Module.txt`
- 根据编号将清洗后的输出精确回填
- 生成完整最终报告

输出：

- `artifacts/<run_id>/report.txt`

### 4. `remote`

- Win11 本机使用 Python SSH 到远程 VPS
- 自动上传当前仓库快照
- 自动安装依赖并执行测试
- 自动抓回报告和日志

输出：

- `remote_runs/<host>/<run_id>/session.log`
- `remote_runs/<host>/<run_id>/report.txt`
