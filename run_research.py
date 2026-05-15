#!/usr/bin/env python3
"""
DuoyiMed Agent 编排引擎 — 启动入口

用法:
    # 交互模式
    python run_research.py

    # 单次请求
    python run_research.py "用 CHARLS 数据预测 2 年衰弱转换, 帮我设计方案"

    # 指定 LLM
    python run_research.py --model claude-opus-4-6 "评估这个研究方向"

    # 文献综述
    python run_research.py --workflow literature "近2年表观遗传时钟预测衰弱的文献"

环境变量:
    ANTHROPIC_API_KEY    Anthropic API 密钥
    LLM_MODEL            LLM 模型名
    OBSIDIAN_VAULT       Obsidian vault 路径
"""

import sys
import os
import json
import argparse
from pathlib import Path

# 确保项目根目录在 Python path 中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.core.orchestrator_graph import ResearchOrchestrator
from engine.config import load_config


def main():
    parser = argparse.ArgumentParser(
        description="DuoyiMed Agent 编排引擎",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run_research.py "用 CHARLS 预测 2 年衰弱转换, 设计完整方案"
  python run_research.py --model claude-opus-4-6 "评估这个建模方案"
  python run_research.py --workflow literature "机器学习预测肌少症的文献综述"
  python run_research.py --workflow quick "Fried Phenotype 在 CHARLS 中怎么操作化?"
        """,
    )
    parser.add_argument("request", nargs="?", help="研究请求 (不提供则进入交互模式)")
    parser.add_argument("--model", "-m", default=None, help="LLM 模型名 (默认: claude-sonnet-4-6)")
    parser.add_argument("--provider", "-p", default=None, help="LLM 提供商 (anthropic/deepseek/openai)")
    parser.add_argument("--workflow", "-w", default="auto",
                        choices=["auto", "new_project", "literature", "paper", "quick", "status", "kb_enrich"],
                        help="工作流类型 (默认: auto 自动判断)")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    parser.add_argument("--dry-run", action="store_true", help="仅显示编排计划, 不实际调用 LLM")
    parser.add_argument("--analyze", action="store_true", help="生成运行状态报告 (不执行项目)")
    parser.add_argument("--analyze-days", type=int, default=90, help="运行报告分析天数 (默认 90)")
    parser.add_argument("--analyze-output", default=None, help="运行报告输出文件 (默认 stdout)")
    parser.add_argument("--analyze-json", action="store_true", help="运行报告以 JSON 格式输出")
    parser.add_argument("--division", "-d", default="all",
                        choices=["all", "geriatrics", "urology"],
                        help="限定事业部 (默认: all, 用于 kb_enrich 等工作流)")
    parser.add_argument("--resume", "-r", default=None, metavar="PROJECT_ID",
                        help="续传已存在的项目 (从中断点继续)")
    parser.add_argument("--list-projects", action="store_true",
                        help="列出所有项目及其状态")
    parser.add_argument("--project-status", default=None, metavar="PROJECT_ID",
                        help="查询指定项目的详细状态")
    parser.add_argument("--worker", action="store_true",
                        help="启动 Worker 守护进程 (消费项目队列)")
    parser.add_argument("--workers", type=int, default=1,
                        help="Worker 进程数 (默认 1, 与 --worker 配合使用)")
    parser.add_argument("--cleanup-locks", action="store_true",
                        help="清理所有过期锁文件 (手动恢复)")
    parser.add_argument("--project-dir", default=None, metavar="PATH",
                        help="显式指定项目工作目录 (跳过自动发现)")

    args = parser.parse_args()

    # --analyze 模式: 只生成运行报告, 不执行项目
    if args.analyze:
        from engine.core.run_analyzer import RunAnalyzer
        config = load_config()
        log_dir = getattr(config, 'run_log_dir', None)
        if log_dir is None:
            log_dir = config.projects_output_dir

        analyzer = RunAnalyzer(log_dir=str(log_dir))
        count = analyzer.load(days=args.analyze_days)

        if count == 0:
            print("无运行数据。运行至少一个项目后数据将自动采集到 outputs/projects/。")
        elif args.analyze_json:
            print(json.dumps(analyzer.generate_json_summary(), ensure_ascii=False, indent=2))
        else:
            report = analyzer.generate_report()
            if args.analyze_output:
                Path(args.analyze_output).write_text(report)
                print(f"报告已保存到 {args.analyze_output}")
            else:
                print(report)
        return

    # --list-projects / --project-status / --resume: 项目管理员命令, 不需要用户请求
    if args.list_projects or args.project_status or args.resume:
        config = load_config()
        orchestrator = ResearchOrchestrator(config)

        if args.list_projects:
            print("=" * 60)
            print("项目列表")
            print("=" * 60)
            print(orchestrator.list_projects())
            return

        if args.project_status:
            print(orchestrator.project_status(args.project_status))
            return

        if args.resume:
            print(f"续传项目: {args.resume}")
            result = orchestrator.run_resume(args.resume)
            print("\n" + "=" * 60)
            print(result)
            print("=" * 60)
            return

    # --worker: 启动 Worker 守护进程
    if args.worker:
        from engine.core.worker import WorkerDaemon

        config = load_config()
        num_workers = min(args.workers, os.cpu_count() or 2, 3)

        if num_workers == 1:
            worker = WorkerDaemon(config, worker_id=0)
            worker.run_forever()
        else:
            import multiprocessing
            print(f"启动 {num_workers} 个 Worker 进程...")

            def _run_worker(wid: int):
                worker = WorkerDaemon(config, worker_id=wid)
                worker.run_forever()

            procs = []
            for i in range(num_workers):
                p = multiprocessing.Process(target=_run_worker, args=(i,))
                p.start()
                procs.append(p)

            try:
                for p in procs:
                    p.join()
            except KeyboardInterrupt:
                print("\n收到中断信号, 停止所有 Worker...")
                for p in procs:
                    p.terminate()
                for p in procs:
                    p.join()
        return

    # --cleanup-locks: 清理过期锁
    if args.cleanup_locks:
        from engine.core.project_lock import cleanup_stale_locks
        config = load_config()
        n = cleanup_stale_locks(config.projects_output_dir)
        print(f"已清理 {n} 个过期锁文件。")
        return

    # 检查 API Key (根据 provider 检查对应的 key)
    provider = os.getenv("LLM_PROVIDER", "anthropic")
    key_env_map = {
        "anthropic": "ANTHROPIC_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
        "openai": "OPENAI_API_KEY",
    }
    key_var = key_env_map.get(provider, "ANTHROPIC_API_KEY")
    if not os.getenv(key_var) and not args.dry_run:
        print(f"⚠️  未设置 {key_var} 环境变量")
        print(f"   请运行: export {key_var}='your-key-here'")
        print(f"   或使用 --dry-run 查看编排计划而不实际调用 LLM\n")

    # 加载配置
    overrides = {"verbose": args.verbose}
    if args.model:
        overrides["llm_model"] = args.model
    if args.provider:
        overrides["llm_provider"] = args.provider

    config = load_config(**overrides)

    # 创建编排器
    orchestrator = ResearchOrchestrator(config)

    # 打印启动信息
    print("""
╔══════════════════════════════════════════════════════════╗
║     DuoyiMed Agent 编排引擎 v0.1                           ║
║     DuoyiMed Research Orchestrator                        ║
╚══════════════════════════════════════════════════════════╝
""")
    print(f"  LLM: {config.llm_provider}/{config.llm_model}")
    print(f"  知识库: {config.obsidian_vault}")
    # 列出所有已配置路径的数据源
    avail = [(n, s) for n, s in config.data_sources.items() if str(s.path) and s.path.name]
    print(f"  数据源 ({len(avail)} 个已配置):")
    for name, ds in avail:
        print(f"    - {name}: {ds.path} [{ds.category}]")
    if not avail:
        print(f"  (无数据源已配置路径)")
    print()

    # kb_enrich 工作流: 直接路由, 无需 LLM 意图分类, 也无需用户输入
    if args.workflow == "kb_enrich":
        result = orchestrator.run_kb_enrich(
            divisions=[args.division] if args.division != "all" else None)
        print("\n" + "=" * 60)
        print(result)
        print("=" * 60)
        return

    # 获取用户请求
    if args.request:
        user_request = args.request
    else:
        # 交互模式
        print("输入研究请求 (或 /quit 退出, /help 帮助):\n")
        user_request = input("> ").strip()
        if not user_request or user_request.lower() in ("/quit", "/exit", "q"):
            return

    # 执行
    if args.dry_run:
        intent = orchestrator._classify_intent(user_request)
        print(f"\n意图分类: {intent['intent']}")
        print(f"摘要: {intent['summary']}")
        print("\n[DRY RUN] 未实际调用 LLM。")
    else:
        result = orchestrator.run(user_request, project_dir=args.project_dir)
        print("\n" + "=" * 60)
        print(result)
        print("=" * 60)


if __name__ == "__main__":
    main()
