#!/usr/bin/env python3
"""
Phase 7 临床 Web 工具 — 启动入口

加载项目 supplements/app.py 并启动 Streamlit 服务。
项目编译后 supplements/run_webapp.py 可直接 `python supplements/run_webapp.py` 启动。

用法:
    python supplements/run_webapp.py
    python supplements/run_webapp.py --port 8080
    python engine/scripts/run_webapp.py --project-dir projects/prostate-cancer

环境变量:
    STREAMLIT_SERVER_PORT    服务端口 (默认 8501)
    STREAMLIT_SERVER_ADDRESS 绑定地址 (默认 localhost)
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Phase 7 — 启动临床预测 Web 工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--project-dir", "-d",
        default=".",
        help="项目目录 (默认当前目录, 需含 supplements/app.py 和 models/)",
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=None,
        help="服务端口 (默认 8501, 也可用 STREAMLIT_SERVER_PORT 环境变量)",
    )
    parser.add_argument(
        "--address",
        default=None,
        help="绑定地址 (默认 localhost, 0.0.0.0 允许外部访问)",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="仅检查 supplements 文件完整性, 不启动服务",
    )

    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()
    supp_dir = project_dir / "supplements"

    # ── Validate deployment files ────────────────────────────────
    required_files = {
        "app.py": supp_dir / "app.py",
        "model_info.json": supp_dir / "model_info.json",
        "feature_config.json": supp_dir / "feature_config.json",
        "requirements.txt": supp_dir / "requirements.txt",
    }

    missing = []
    for desc, path in required_files.items():
        if not path.exists():
            missing.append(f"  ❌ {desc} ({path})")

    if missing:
        print("Phase 7 deployment check FAILED — 缺失文件:")
        for m in missing:
            print(m)
        sys.exit(1)

    print("✅ All deployment files present:")
    for desc, path in required_files.items():
        print(f"  ✅ {path}")

    # ── Validate model files ─────────────────────────────────────
    model_files = list(project_dir.glob("models/*.pkl"))
    if model_files:
        print(f"  ✅ models/ ({len(model_files)} model files)")
    else:
        print(f"  ⚠️  models/ (no .pkl files found — app.py may load from alternate path)")

    if args.check_only:
        print("\n✅ Check-only mode — deployment files validated.")
        return

    # ── Launch Streamlit ─────────────────────────────────────────
    port = args.port or int(os.environ.get("STREAMLIT_SERVER_PORT", "8501"))
    address = args.address or os.environ.get("STREAMLIT_SERVER_ADDRESS", "localhost")

    print(f"\n🚀 Launching clinical prediction tool...")
    print(f"   URL: http://{address}:{port}")
    print(f"   Press Ctrl+C to stop.\n")

    app_path = supp_dir / "app.py"

    # Change to project dir so relative paths in app.py resolve correctly
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        str(app_path),
        "--server.port", str(port),
        "--server.address", address,
        "--browser.serverAddress", address,
    ]

    try:
        subprocess.run(cmd, cwd=str(project_dir))
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped.")
    except FileNotFoundError:
        print(
            "❌ Streamlit not found. Install with:\n"
            "   pip install streamlit"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
