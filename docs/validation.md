# 真机验证

验证时间：2026-03-26

环境：

- 2 台远程 VPS
- Debian GNU/Linux 13 (trixie)
- x86_64

结论：

- 16/16 测试项在两台机器上均成功完成
- `NodeQuality` 与 `IP.Check.Place` 原始退出码为 `1`，但输出中已出现完整报告链接，因此执行器按完成标记归一为成功
- 远程调度已改为 `nohup + 状态轮询`，规避长任务绑定单一 SSH 通道导致的中断

关键产物：

- `remote_runs/<host>/<run_id>/session.log`
- `remote_runs/<host>/<run_id>/results.json`
- `remote_runs/<host>/<run_id>/report.txt`
