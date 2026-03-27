# Vps_test

自动化执行vps测试脚本，并自动输出形成测试报告

- 自动抓取 16 个常用测试脚本到 `raw/`
- 自动识别脚本来源、依赖、交互风险
- 在目标 VPS 上顺序执行测试并保存完整原始日志
- 将结果注入 `Module.txt` 模板中的“脚本输出内容”区域
- 输出最终完整 VPS 测试报告

入口：

- `python tools/fetch_raw_sources.py`
- `python tools/analyze_sources.py`
- `python tools/run_suite.py --local`
- `python tools/run_remote_hosts.py --hosts-file hosts.json`

Debian 13 一键执行入口：

- `bash <(curl -fsSL https://raw.githubusercontent.com/pursork/Vps_test/main/bootstrap.sh)`

工作流：

1. 本地抓取并分析源脚本  
   `python tools/fetch_raw_sources.py`  
   `python tools/analyze_sources.py`
2. 在 Debian 13 本机执行  
   `python tools/run_suite.py --local --timeout-seconds 1200`
3. 从 Win11 远程批量执行  
   `python tools/run_remote_hosts.py --hosts-file hosts.json --timeout-seconds 1200`

输出：

- 本机执行结果：`artifacts/<run_id>/report.txt`
- 远程执行结果：`remote_runs/<host>/<run_id>/report.txt`

交互脚本默认策略：

- `NodeQuality`：4 次回车，接受默认测试项
- `ecs.sh`：改走参数模式，固定执行 `-m 1`
- `Media.Check.Place` / `RegionRestrictionCheck`：回车走全量检测
- `IP.Check.Place`：追加 `-y`，跳过安装确认
- `AutoTrace`：回车走默认测试项
- `taier.sh`：固定选择 `1`，即大陆三网单线程 IPv4

> 目前仅在Debian13完成测试
