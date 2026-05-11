#!/usr/bin/env python3
"""
计算老年医学研究 Agent 编排引擎 — 启动入口

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
        description="计算老年医学研究 Agent 编排引擎",
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
                        choices=["auto", "new_project", "literature", "paper", "quick", "status"],
                        help="工作流类型 (默认: auto 自动判断)")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    parser.add_argument("--dry-run", action="store_true", help="仅显示编排计划, 不实际调用 LLM")
    parser.add_argument("--analyze", action="store_true", help="生成运行状态报告 (不执行项目)")
    parser.add_argument("--analyze-days", type=int, default=90, help="运行报告分析天数 (默认 90)")
    parser.add_argument("--analyze-output", default=None, help="运行报告输出文件 (默认 stdout)")
    parser.add_argument("--analyze-json", action="store_true", help="运行报告以 JSON 格式输出")

    args = parser.parse_args()

    # --analyze 模式: 只生成运行报告, 不执行项目
    if args.analyze:
        from engine.core.run_analyzer import RunAnalyzer
        config = load_config()
        log_dir = getattr(config, 'run_log_dir', None)
        if log_dir is None:
            log_dir = config.project_root / "outputs" / "run_logs"

        analyzer = RunAnalyzer(log_dir=str(log_dir))
        count = analyzer.load(days=args.analyze_days)

        if count == 0:
            print("无运行数据。运行至少一个项目后数据将自动采集到 outputs/run_logs/。")
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

    # 检查 API Key
    if not os.getenv("ANTHROPIC_API_KEY") and not args.dry_run:
        print("⚠️  未设置 ANTHROPIC_API_KEY 环境变量")
        print("   请运行: export ANTHROPIC_API_KEY='your-key-here'")
        print("   或使用 --dry-run 查看编排计划而不实际调用 LLM\n")

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
║     计算老年医学研究 Agent 编排引擎 v0.1                    ║
║     Computational Geriatrics Research Orchestrator       ║
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
        result = orchestrator.run(user_request)
        print("\n" + "=" * 60)
        print(result)
        print("=" * 60)


if __name__ == "__main__":
    main()
