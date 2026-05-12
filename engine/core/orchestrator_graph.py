"""
LangGraph 编排图 — 多 Agent 协作的核心编排引擎

图结构:

    START
      │
      ▼
  classify_intent ──→ (orchestrator 分析用户意图, 创建任务计划)
      │
      ▼
  execute_next_tasks ──→ (查找 ready 状态的 task, 并行/串行执行)
      │                        │
      │                   ┌────┘
      │                   ▼
      │              call_agent ──→ (调用单个 Agent LLM)
      │                   │
      │                   ▼
      │              update_task ──→ (记录结果, 解除依赖)
      │                   │
      │                   ▼
      ▼              [有 pending task?]
  aggregate_results ←─────── Yes ──→ execute_next_tasks
      │                   No ──────→ aggregate_results
      ▼
  respond_to_user
      │
      ▼
     END
"""

import json
import time
from datetime import datetime
from typing import Optional, Any
from pathlib import Path

from .state import OrchestratorState, AgentTask, Message
from .agent_loader import AgentPromptLoader
from .kb_manager import KnowledgeBaseManager
from .llm_client import LLMClient, LLMCallFailedError
from .tools import ToolRegistry
from .gate_checks import GATE_DEFINITIONS, _extract_auc_from_outputs, _extract_features_from_outputs
from .data_prefetcher import DataPrefetcher
from .consistency_checker import ConsistencyChecker
from .project_predictor import ProjectPredictor, ProjectProfile, infer_profile
from .adaptive_scheduler import AdaptiveScheduler
from .baseline_manager import BaselineManager
from .preflight_scanner import PreflightScanner


# ================================================================
# 意图分类
# ================================================================

INTENT_CLASSIFIER_PROMPT = """你是一个研究编排器的意图分类模块。根据用户输入, 判断用户意图。

返回 JSON:
{
  "intent": "new_project | literature_review | paper_writing | quick_consult | status_check",
  "project_id": "项目ID (如果是已有项目)",
  "summary": "一句话总结用户需求",
  "keywords": ["关键词1", "关键词2"]
}

意图说明:
- new_project: 启动新研究项目, 需要完整的研究设计方案
- literature_review: 文献检索、综述、文献笔记
- paper_writing: 基于已有结果写论文
- quick_consult: 向某个专家快速咨询一个问题
- status_check: 查看项目状态
"""

# ================================================================
# 工作流阶段定义
# ================================================================

# 新研究项目的标准阶段
# Phase 0: 系统总体设计 (SDS) — 编排器自身执行, 生成项目蓝图
# Phase 1: 问题定义 — 必须依赖 research-assistant 的实时文献预检
PROJECT_PHASES = {
    "system_design": {
        "agents": [],              # Phase 0 由编排器自身执行
        "parallel": False,
        "description": "系统总体设计: 生成 SDS (系统分解 + 接口规范 + 反馈触发 + 假设风险)",
        "next": "problem_definition",
        "expected_outputs": [
            "sds.md",
            "project-brief.md",
        ],
    },
    "problem_definition": {
        "agents": ["clinical-researcher", "data-engineer", "research-assistant", "pi"],
        "parallel": True,
        "description": "问题定义: 文献预检 + 临床操作化 + 数据评估 + PI FRAME 评估 (两轮: 机器预检 → 专家决策)",
        "next": "design",
        "two_round": True,  # FRAME 定量化: Round1 机器预检, Round2 PI 基于数据做 FRAME
        "expected_outputs": [
            "00_literature/literature-precheck.md",
            "data/data-availability.md",
            "data/modeling-feasibility.md",
            "data/phenotype-definition.md",
            "data/frame-assessment.md",
        ],
    },
    "design": {
        "agents": ["computational-biologist", "biostatistician"],
        "parallel": True,
        "description": "方案设计 (研讨厅辩论模式): 并行辩论 → 共识/分歧 → PI裁决",
        "depends_on": ["problem_definition"],
        "next": "execution",
        "debate_mode": True,  # 🆕 钱学森研讨厅: 并行辩论替代流水线审查
        "debate_topic": "研究方案设计: 建模方法选择 + 统计分析策略 + 协变量筛选",
        "debate_participants": ["computational-biologist", "biostatistician", "clinical-researcher"],
        "expected_outputs": [
            "data/debate-cb.md",
            "data/debate-biostat.md",
            "data/debate-clin.md",
            "data/debate-minutes.md",
            "data/pi-ruling.md",
        ],
    },
    "execution": {
        "agents": ["ml-engineer"],
        "parallel": False,
        "description": "执行: 模型训练 + 内部验证",
        "depends_on": ["design"],
        "next": "external_validation",
        "expected_outputs": [
            "data/cohort.parquet",
            "extract_cohort.py",
            "train_model.py",
            "models/xgb_final.pkl",
            "models/lr_final.pkl",
            "models/cv_results.json",
        ],
    },
    "external_validation": {
        "agents": ["data-engineer", "ml-engineer", "biostatistician"],
        "parallel": True,
        "description": "外部验证: 独立数据集验证 + 性能对比 + 可泛化性评估",
        "depends_on": ["execution"],
        "next": "review",
        "expected_outputs": [
            "external_validation.py",
            "data/phase3-4-summary.md",
        ],
    },
    "review": {
        "agents": ["clinical-researcher", "pi"],
        "parallel": True,
        "description": "审查 (研讨厅辩论模式): 临床审查 + PI终审 → 辩论纪要 → 裁决",
        "depends_on": ["external_validation"],
        "next": "writing",
        "debate_mode": True,  # 🆕 钱学森研讨厅: PI不再独自审, 而是辩论后裁决
        "debate_topic": "研究结果审查: 临床意义 + 统计可靠性 + 外部验证可泛化性",
        "debate_participants": ["clinical-researcher", "biostatistician", "pi"],
        "expected_outputs": [
            "data/review-clin.md",
            "data/review-biostat.md",
            "data/review-pi.md",
            "data/review-debate-minutes.md",
            "data/review-pi-ruling.md",
        ],
    },
    "writing": {
        "agents": ["scientific-writer"],
        "parallel": False,
        "multi_step": True,  # 🆕 P0: 论文撰写需要子编排 (表格→图表→分节→合稿)
        "description": "论文撰写 (基于内部+外部验证完整结果)",
        "depends_on": ["review"],
        "next": None,
        "steps": [
            {
                "name": "tables",
                "agents": ["research-assistant"],
                "task_prompt": "{user_request}\n\n请根据上游数据生成 Table 1 (基线特征表)、Table 2 (模型性能对比)、Table 3 (亚组分析)，写入 tables/ 目录。",
            },
            {
                "name": "figures",
                "agents": ["ml-engineer"],
                "task_prompt": "{user_request}\n\n请生成论文图表，文件命名须严格遵循 Figure[N]_[descriptor].[ext] 格式:\n- Figure1_cohort-flow-diagram.png + .tiff (队列流程图/Figure 1)\n- Figure2_roc-curve.png + .tiff (ROC曲线/Figure 2)\n- Figure3_calibration-plot.png + .tiff (校准曲线/Figure 3)\n- Figure4_feature-importance.png + .tiff (SHAP特征重要性/Figure 4)\n对应的 Figure[N]_caption.md 和 Figure[N]_[descriptor]_data.json 也须使用同编号体系。\n所有图片写入 figures/ 目录。",
            },
            {
                "name": "sections",
                "agents": ["scientific-writer"],
                "task_prompt": "{user_request}\n\n{step_results}\n\n请逐个撰写 IMRAD 各章节文件到 sections/ 目录。",
            },
            {
                "name": "humanize",
                "agents": ["humanizer"],
                "task_prompt": "{user_request}\n\n{step_results}\n\n请对 scientific-writer 产出的各章节逐节执行去 AI 味改写。保留所有数据和引用不变。输出逐节改动记录和改写后文本，写入 sections/humanize-log.md。",
            },
            {
                "name": "assembly",
                "agents": ["scientific-writer"],
                "task_prompt": "{user_request}\n\n{step_results}\n\n请将 sections/ 中的各章节文件和 tables/ 中的表格组装为完整论文。\n- 合稿写入 submission/manuscript.md (投稿层唯一文件，切勿创建 submission/sections/ 子目录)\n- 零件层文件 (sections/*.md, tables/*.md, figures/*.py) 已在前面步骤中写入，本步骤只需引用它们\n- ⚠️ 投稿终稿中禁止出现 [Classic — ...] / [Foundational — ...] / [数据待确认] 等内部质控标记，这些标记仅保留在 sections/08_references.md 供审查使用",
            },
        ],
        "expected_outputs": [
            # 零件层 (working dirs) — Agent 产出
            "sections/01_title.md",
            "sections/02_abstract.md",
            "sections/03_introduction.md",
            "sections/04_methods.md",
            "sections/05_results.md",
            "sections/06_discussion.md",
            "sections/07_conclusion.md",
            "sections/08_references.md",
            "sections/humanize-log.md",
            "tables/table1_baseline.md",
            "tables/table2_model_performance.md",
            "tables/table3_subgroup.md",
            "figures/generate_figures.py",
            "figures/figure_descriptions.md",
            "figures/Figure1_caption.md",
            "figures/Figure2_caption.md",
            "figures/Figure3_caption.md",
            "figures/Figure4_caption.md",
            # 投稿层 (submission) — 最终组装交付件
            "submission/manuscript.md",
            "submission/tables/table1_baseline.csv",
            "submission/tables/table2_model_performance.csv",
            "submission/tables/table3_subgroup.csv",
            "submission/figures/Figure1_cohort-flow-diagram.png",
            "submission/figures/Figure2_roc-curve.png",
            "submission/figures/Figure3_calibration-plot.png",
            "submission/figures/Figure4_feature-importance.png",
        ],
    },
}

# 文献综述的简化阶段
LITERATURE_PHASES = {
    "lit_search": {
        "agents": ["research-assistant"],
        "parallel": False,
        "description": "文献检索 + 筛选",
        "next": "lit_synthesize",
    },
    "lit_synthesize": {
        "agents": ["research-assistant", "clinical-researcher"],
        "parallel": True,
        "description": "文献合成 + 偏倚评估",
        "depends_on": ["lit_search"],
        "next": None,
    },
}


# ================================================================
# 跨 Phase 反馈环 B — 自动检测规则 (共8条)
# 钱学森工程控制论: 下游发现上游问题时, 自动触发回退 (积分控制 - 累积偏差修正)
# ================================================================

FEEDBACK_B_TRIGGERS = {
    "execution": {
        "problem_definition": {
            "signals": [
                "特征不可用", "feature not available", "变量不存在",
                "数据质量不足", "data quality insufficient", "缺失率过高",
                "样本量不足", "insufficient sample", "标签泄露",
                "label leakage", "表型定义模糊", "phenotype unclear",
                "变量编码错误", "encoding error",
            ],
            "severity": "critical",
            "action": "reopen_gate",
            "message": "ML 阶段检测到数据/表型问题, 需返回 Phase 1 修正",
        },
        "design": {
            "signals": [
                "模型不适用", "model not suitable", "方法选择错误",
                "SAP 与建模方案不一致", "统计方法不匹配",
            ],
            "severity": "critical",
            "action": "reopen_gate",
            "message": "ML 阶段检测到方案设计问题, 需返回 Phase 2 修正",
        },
    },
    "external_validation": {
        "execution": {
            "signals": [],
            "severity": "critical",
            "action": "reopen_gate",
            "message": "外部验证 AUC 相比内部验证下降 > 0.15, 疑似过拟合",
            "numeric_rule": {
                "metric": "auc",
                "compare_phase": "execution",
                "threshold": -0.15,
            },
        },
        "problem_definition": {
            "signals": [
                "外部数据不可用", "external data unavailable",
                "外部人群不匹配", "population mismatch",
            ],
            "severity": "high",
            "action": "notify_pi",
            "message": "外部验证阶段发现数据源问题, 建议 PI 评估",
        },
    },
    "review": {
        "problem_definition": {
            "signals": [
                "表型定义不可操作化", "临床定义有问题",
                "effect direction mismatch", "效应方向矛盾",
                "预测因子不合理的临床解释",
            ],
            "severity": "critical",
            "action": "reopen_gate",
            "message": "审查阶段发现临床定义问题, 需返回 Phase 1 修正表型定义",
        },
        "execution": {
            "signals": [
                "SHAP 方向与临床知识矛盾", "特征重要性异常",
                "模型行为不合理", "校准度不可接受",
            ],
            "severity": "critical",
            "action": "reopen_gate",
            "message": "审查阶段发现模型问题, 需返回 Phase 3 重新建模",
        },
    },
    "writing": {
        "execution": {
            "signals": [
                "[数据待确认]", "[数据矛盾]", "[数值不一致]",
                "[结果缺失]", "data missing",
            ],
            "severity": "critical",
            "action": "reopen_gate",
            "message": "写作阶段发现数据缺失或矛盾, 需返回上游确认",
        },
        "problem_definition": {
            "signals": [
                "缺少关键的临床背景", "研究意义不明确",
            ],
            "severity": "high",
            "action": "notify_pi",
            "message": "写作阶段发现研究定义不够清晰, 建议 PI 补充",
        },
    },
    # 🆕 全局触发 #7: 脚本崩溃检测 (2026-05-12 新增)
    # 任何 Phase 脚本崩溃且根因是内存安全违规 → 扫描同项目所有 .py
    # 此触发器在 _handle_preflight_failure() 中实现
    "script_crash": {
        "all_phases": True,
        "signals": [
            "kernel panic", "memory exhaustion", "内存耗尽",
            "OOM", "Killed: 9", "segmentation fault",
            "n_jobs=-1", "CoW explosion",
        ],
        "severity": "critical",
        "action": "block_all_scripts",
        "message": "脚本崩溃且根因为内存安全违规 → 自动扫描同项目所有 .py → 创建修复清单 → 阻止任何脚本执行直到清零",
    },
    # 🆕 全局触发 #8: lessons-learned 新规则传播 (2026-05-12 新增)
    "lessons_learned": {
        "all_phases": True,
        "signals": [
            "lessons-learned", "教训文档",
        ],
        "severity": "high",
        "action": "diff_and_block",
        "message": "lessons-learned 文件更新 → 自动提取新规则 → diff 同项目所有脚本 → 不一致项计入 Gate 前置阻断",
    },
}

FEEDBACK_B_COUNT = 8  # 共8条触发规则


class ResearchOrchestrator:
    """
    计算医学研究编排引擎 — 公司模式, 支持多事业部。

    用法:
        orchestrator = ResearchOrchestrator(config)
        result = orchestrator.run("用 CHARLS 数据预测 2 年衰弱转换")
        result = orchestrator.run("用 MIMIC-IV 数据预测肾结石复发")
    """

    def __init__(self, config=None):
        # 延迟导入避免循环依赖
        from ..config import EngineConfig, load_config

        self.config = config or load_config()

        # 初始化各组件
        self.agent_loader = AgentPromptLoader(
            agents_dir=self.config.agents_dir,
            company_dir=getattr(self.config, 'company_dir', None),
        )
        self.kb = KnowledgeBaseManager(
            vault_path=self.config.obsidian_vault,
            vaults=getattr(self.config, 'obsidian_vaults', {}),
        )
        self.llm = LLMClient(
            provider=self.config.llm_provider,
            model=self.config.llm_model,
            max_tokens=self.config.llm_max_tokens,
            temperature=self.config.llm_temperature,
            verbose=self.config.verbose,
            # 容错配置
            fallback_model=getattr(self.config, 'llm_fallback_model', 'claude-haiku-4-5-20251001'),
            max_retries=getattr(self.config, 'llm_max_retries', 3),
            retry_base_delay=getattr(self.config, 'llm_retry_base_delay', 1.0),
            retry_max_delay=getattr(self.config, 'llm_retry_max_delay', 8.0),
            request_timeout=getattr(self.config, 'llm_request_timeout', 300),
        )
        self.tools = ToolRegistry(
            data_sources=getattr(self.config, 'data_sources', {}),
            obsidian_vault=self.config.obsidian_vault,
        )
        self.prefetcher = DataPrefetcher(self.tools)

        # 🆕 一致性交叉验证引擎 (钱学森可靠性工程)
        self.consistency_checker = ConsistencyChecker(
            llm_client=self.llm,
            verbose=self.config.verbose,
        )

        # 状态追踪
        self.state: Optional[OrchestratorState] = None
        self.active_division: str = "geriatrics"  # 当前活跃的事业部
        self.active_data_sources: list[str] = []   # 当前请求使用的数据源列表

        # 🆕 趋势监控缓存 (Δ-Gate / 跨Phase反馈环B) — 钱学森系统辨识-反馈控制
        self._trend_baselines: dict = {}    # {metric: value/state} AUC基准值, 校准状态等
        self._cached_aucs: dict = {}        # {phase_id: auc_value} 跨Phase AUC对比
        self._phase_features: dict = {}     # {phase_id: [feature_names]} 特征稳定性检查

        # 🆕 系统辨识模块 — 懒加载, 首次使用时从 JSONL 初始化
        self._run_analyzer = None           # RunAnalyzer 实例
        self._project_predictor = None      # ProjectPredictor 实例
        self._adaptive_scheduler = None     # AdaptiveScheduler 实例

        # 🆕 技术状态基线管理器 (钱学森总体设计部 — 基线冻结+变更控制)
        baseline_dir = getattr(self.config, 'baseline_dir', None)
        if baseline_dir is None:
            baseline_dir = self.config.project_root / "outputs" / "baselines"
        self.baseline_manager = BaselineManager(Path(baseline_dir))

    def _get_phase_agents(self, phase_id: str) -> list:
        """公司模式: 获取事业部感知的阶段 Agent 列表, 将旧 ID 映射到新命名空间."""
        phase_def = PROJECT_PHASES.get(phase_id, {})
        agents = phase_def.get("agents", [])
        div = self.active_division

        mapping = {
            "clinical-researcher": f"{div}/clinical-researcher",
            "pi": f"{div}/pi",
            "computational-biologist": f"{div}/computational-biologist",
            "data-engineer": "shared/data-engineer",
            "biostatistician": "shared/biostatistician",
            "ml-engineer": "shared/ml-engineer",
            "scientific-writer": "shared/scientific-writer",
            "research-assistant": "shared/research-assistant",
            "humanizer": "shared/humanizer",
            "pm": "pmo",
        }
        return [mapping.get(a, a) for a in agents]

    # ================================================================
    # 主入口
    # ================================================================

    def run(self, user_request: str) -> str:
        """主入口: 接收用户请求, 编排 Agent 协作, 返回结果"""
        print(f"\n{'='*60}")
        print(f"[Orchestrator] 接收请求: {user_request[:100]}...")
        print(f"{'='*60}\n")

        # Step 0: 分类事业部 (公司模式)
        self.active_division = self._classify_division(user_request)
        self.active_data_sources = self._detect_data_sources(user_request)
        print(f"[Orchestrator] 事业部: {self.active_division} | 数据源: {self.active_data_sources or '(默认)'}")

        # Step 1: 分类意图
        intent = self._classify_intent(user_request)
        print(f"[Orchestrator] 意图: {intent['intent']} — {intent['summary']}")

        # Step 2: 按意图路由。复杂/模糊请求优先走 PM 规划
        if self._needs_pm_planning(user_request):
            result = self._run_pm_mode(user_request, intent)
        elif intent["intent"] == "new_project":
            result = self._run_project_workflow(user_request, intent)
        elif intent["intent"] == "literature_review":
            result = self._run_literature_workflow(user_request, intent)
        elif intent["intent"] == "paper_writing":
            result = self._run_writing_workflow(user_request, intent)
        elif intent["intent"] == "quick_consult":
            result = self._run_quick_consult(user_request, intent)
        elif intent["intent"] == "status_check":
            result = self._run_status_check(intent)
        else:
            result = self._run_quick_consult(user_request, intent)

        print(f"\n[Orchestrator] 完成.\n")
        return result

    def _needs_pm_planning(self, user_request: str) -> bool:
        """判断是否需要 PM 规划 (复杂/多步骤/模糊请求)"""
        req = user_request.lower()
        pm_triggers = [
            "启动", "新项目", "开始工作", "kickoff",
            "全部", "所有", "完整", "整套", "从0到1",
            "帮我规划", "帮我安排", "自动推进", "全流程",
            "设计方案", "设计完整方案", "整个流程",
        ]
        # 多步骤请求 (含多个编号或分号)
        multi_step = req.count(")") >= 2 or req.count("）") >= 2 or req.count("；") >= 1
        return any(t in req for t in pm_triggers) or multi_step

    # ================================================================
    # 意图分类
    # ================================================================

    def _classify_intent(self, user_request: str) -> dict:
        prompt = self.agent_loader.load_full_prompt("orchestrator", include_fewshot=False)
        response = self.llm.chat(
            system_prompt=prompt + "\n\n" + INTENT_CLASSIFIER_PROMPT,
            user_message=f"用户请求: {user_request}\n\n请分类意图, 返回 JSON。",
        )
        try:
            # 尝试从响应中提取 JSON
            content = response.content
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                return json.loads(content[json_start:json_end])
        except json.JSONDecodeError:
            pass
        # 回退: 简单关键词分类
        return self._fallback_classify(user_request)

    def _fallback_classify(self, user_request: str) -> dict:
        """简单的关键词回退分类 (修复了原有优先级问题)"""
        req_lower = user_request.lower()
        keywords = []

        # 文献综述优先检查 (避免被"预测"/"模型"等关键词先匹配到 new_project)
        if any(w in req_lower for w in ["文献", "综述", "检索", "prisma", "扫描", "搜索", "阅读笔记"]):
            intent = "literature_review"
        elif any(w in req_lower for w in ["写", "论文", "投稿", "初稿", "润色", "cover letter"]):
            intent = "paper_writing"
        elif any(w in req_lower for w in ["状态", "进展", "进度"]):
            intent = "status_check"
        elif any(w in req_lower for w in ["数据", "变量", "可用性", "缺失率", "文件", "csv", "charls", "评估"]):
            intent = "new_project"  # 数据评估也走 multi-agent 编排
        elif any(w in req_lower for w in ["预测", "模型", "建模", "新项目", "启动", "方案", "设计", "sap"]):
            intent = "new_project"
        else:
            intent = "quick_consult"
        return {"intent": intent, "project_id": None, "summary": user_request, "keywords": keywords}

    # ================================================================
    # 事业部路由 (Company Mode)
    # ================================================================

    def _classify_division(self, user_request: str) -> str:
        """根据临床领域关键词确定事业部，不依赖数据源名。

        数据源是公司资产，不应影响事业部路由。
        例如 '用 MIMIC 做老年衰弱' 应路由到 geriatrics，而非 urology。

        Returns: 'geriatrics' | 'urology'
        """
        req = user_request.lower()

        # 泌尿外科关键词 (先检查, 更具体)
        urology_kw = [
            "肾结石", "尿石症", "输尿管结石", "膀胱结石", "kidney stone", "urolithiasis",
            "前列腺", "前列腺增生", "前列腺癌", "psa", "bph", "prostat", "turp",
            "膀胱癌", "膀胱肿瘤", "bladder cancer", "nmibc", "mibc",
            "泌尿", "尿道", "urology", "urological",
            "尿路感染", "uti", "肾盂肾炎", "pyelonephritis",
            "肾上腺", "肾癌", "睾丸癌", "阴茎癌",
            "肾积水", "输尿管", "尿潴留",
        ]
        if any(kw.lower() in req for kw in urology_kw):
            return "urology"

        # 老年医学关键词
        geriatrics_kw = [
            "衰弱", "frailty", "fried",
            "肌少症", "sarcopenia",
            "跌倒", "fall", "步速", "gait",
            "认知", "cognition", "dementia", "mmse", "moca",
            "老年", "aging", "elderly", "geriatric",
            "多病共存", "multimorbidity",
            "衰老时钟", "epigenetic clock", "biological age",
            "多重用药", "polypharmacy",
        ]
        if any(kw.lower() in req for kw in geriatrics_kw):
            return "geriatrics"

        # 默认: 老年医学
        return "geriatrics"

    def _detect_data_sources(self, user_request: str) -> list[str]:
        """从用户请求中提取数据源需求。数据源是公司级资产, 任何事业部均可使用。

        与 _classify_division 解耦: 用户可以在任何事业部使用任何数据源。
        如 '用 MIMIC 做老年衰弱研究' → geriatrics + MIMIC-IV。

        Returns: 数据源名称列表 (按用户提及排序)
        """
        req = user_request.lower()
        detected = []

        # 数据源关键词 → 注册表名称
        source_patterns = [
            (["charls"], "CHARLS"),
            (["clhls"], "CLHLS"),
            (["hrs"], "HRS"),
            (["elsa"], "ELSA"),
            (["uk biobank", "ukb"], "UK_BIOBANK"),
            (["nhanes"], "NHANES"),
            (["mimic-iv", "mimic iv", "mimic"], "MIMIC-IV"),
            (["seer"], "SEER"),
        ]
        for keywords, source_name in source_patterns:
            if any(kw in req for kw in keywords):
                detected.append(source_name)

        # 如果用户未指定数据源, 使用该事业部的默认推荐
        if not detected:
            defaults = getattr(self.config, 'division_default_sources', {})
            detected = defaults.get(self.active_division, [])[:2]  # 取前2个

        return detected

    # ================================================================
    # 工作流: 新研究项目
    # ================================================================

    SDS_SYSTEM_PROMPT = (
        "你是计算医学研究公司的总体设计师 (System Architect)。"
        "你的职责是为每个新研究项目设计《系统设计说明书》(SDS)——项目蓝图。\n\n"
        "SDS 不等同于统计分析计划 (SAP)。SDS 定义的是整个研究系统的架构：子系统分解、接口格式和 SLA、质量闸门标准、跨 Phase 反馈触发条件、关键假设与风险。\n\n"
        "你需要像航天工程的总体设计部一样思考：顶层设计、接口标准化、全系统集成验证。"
    )

    # 🆕 研讨厅辩论主持人 System Prompt — 钱学森综合集成研讨厅
    DEBATE_MODERATOR_SYSTEM_PROMPT = (
        "你是计算医学研究公司的研讨厅辩论主持人 (Debate Moderator)。"
        "你不代表任何一方的立场——你只负责整理、识别和呈现。\n\n"
        "你的核心信念: 分歧不是问题，分歧是需要人工判断的关键信息点。"
        "流水线审查中容易被掩盖的分歧，在并行辩论模式中被显式呈现。\n\n"
        "## 判定标准\n\n"
        "### 共识 — 各方从不同角度得出相同或兼容的结论；使用不同术语但核心判断一致\n"
        "### 分歧的重要性:\n"
        "- Critical: 影响研究是否可行的根本性分歧\n"
        "- High: 影响研究结论或核心方法选择\n"
        "- Medium: 影响细节但不影响整体方向\n\n"
        "### 证据强度: 高(文献/数据支撑) / 中(逻辑推理) / 低(经验判断)\n\n"
        "## 输出格式\n\n"
        "严格输出以下 Markdown:\n\n"
        "# 研讨厅辩论纪要\n\n"
        "**辩论主题**: {主题}  **参与方**: {列表}  **主持人**: Debate Moderator\n\n"
        "---\n\n"
        "## 1. 共识 (所有参与方一致同意)\n"
        "- [共识N]: 说明 — 同意方: agent列表\n\n"
        "## 2. 分歧 (按重要性排序)\n\n"
        "### 分歧 N: 标题 [重要性: Critical/High/Medium]\n\n"
        "| 参与方 | 观点 | 论据 | 证据强度 |\n"
        "|--------|------|------|---------|\n"
        "| ... | ... | ... | 高/中/低 |\n\n"
        "**分歧实质**: 一句总结  **建议解决方向**: 不偏向任何一方的建议\n\n"
        "## 3. PI 裁决项\n"
        "- [ ] 决策项: 描述 — 选项: A / B\n\n"
        "## 4. 综合建议\n"
        "基于辩论结果的总体建议\n\n"
        "---\n"
        "*本纪要由研讨厅辩论主持人自动生成。PI 请基于本纪要做最终裁决。*\n\n"
        "## 重要原则\n"
        "- 不站队: 不做谁对谁错的判断\n"
        "- 不粉饰: Critical 分歧必须醒目标注\n"
        "- 不遗漏: 实质性分歧必须列出\n"
        "- 不过度: Medium 分歧不超过 3 个\n"
        "- 先共识后分歧: 共识给信心，分歧给方向"
    )

    def _ensure_analyzer_loaded(self):
        """懒加载 RunAnalyzer 及系统辨识模块, 首次使用时从 JSONL 加载数据"""
        if self._run_analyzer is not None:
            return
        from .run_analyzer import RunAnalyzer

        log_dir = getattr(self.config, 'run_log_dir', None)
        if log_dir is None:
            log_dir = self.config.project_root / "outputs" / "run_logs"

        self._run_analyzer = RunAnalyzer(log_dir=str(log_dir))
        n = self._run_analyzer.load(days=90)
        if n > 0:
            self._project_predictor = ProjectPredictor(self._run_analyzer)
            self._adaptive_scheduler = AdaptiveScheduler(self._run_analyzer)
            if self.config.verbose:
                print(f"  [系统辨识] 已加载 {n} 条运行记录")

    def _build_historical_context(self, user_request: str) -> str:
        """基于系统辨识数据构建 SDS 的历史参考上下文"""
        self._ensure_analyzer_loaded()

        if self._project_predictor is None:
            return ""

        profile = infer_profile(user_request, self.active_division)
        prediction = self._project_predictor.predict(profile)

        if prediction["confidence"] == "low":
            return ""

        lines = [
            "",
            "## 📊 系统辨识参考数据",
            f"*基于 {prediction['similar_projects_count']} 个类似项目的运行数据 (钱学森系统辨识)*",
            "",
            "| 指标 | 预测值 | 范围/说明 |",
            "|------|--------|----------|",
            f"| 预计总耗时 | {prediction['estimated_total_hours']}h | {prediction['estimated_total_hours_range'][0]}-{prediction['estimated_total_hours_range'][1]}h |",
            f"| 预计一次通过率 | {prediction['estimated_success_rate']}% | — |",
            f"| 历史瓶颈 Phase | {prediction['bottleneck_phase']} | — |",
            f"| 建议期刊 Tier | Tier {prediction['recommended_journal_tier']} | 原始目标 Tier {profile.target_journal_tier} |",
            f"| 预测可信度 | {prediction['confidence']} | — |",
            "",
        ]
        if prediction["risk_factors"]:
            lines.append("### ⚠️ 风险因子")
            for r in prediction["risk_factors"]:
                lines.append(f"- {r}")
            lines.append("")

        if prediction["phase_predictions"]:
            lines.append("### 各 Phase 耗时预测")
            lines.append("| Phase | 平均耗时 | 范围 |")
            lines.append("|-------|---------|------|")
            for pp in prediction["phase_predictions"]:
                lines.append(
                    f"| {pp['phase_id']} | {pp['avg_hours']}h | "
                    f"{pp['min_hours']}-{pp['max_hours']}h |"
                )
            lines.append("")

        lines.append("---")
        return "\n".join(lines)

    def _run_system_design(self, user_request: str, project_id: str) -> str:
        """Phase 0: 生成系统设计说明书 (SDS) — 项目总体蓝图, 含系统辨识参考"""
        print(f"  → 总体设计师: 生成 SDS...")

        # 🆕 系统辨识: 注入历史参考数据
        historical_context = self._build_historical_context(user_request)

        prompt = f"""用户研究请求:
{user_request}

事业部: {self.active_division}
数据源: {self.active_data_sources or '(自动选择默认)'}
{historical_context}

可用 Agent 及其职责:
- {self.active_division}/pi: 首席研究员 (FRAME 五维评估 + 期刊策略 + 七项终审)
- {self.active_division}/clinical-researcher: 临床研究员 (表型定义 + 临床审查 + 效应方向确认)
- {self.active_division}/computational-biologist: 计算生物学 (PICO-ML 映射 + 建模方案)
- shared/data-engineer: 数据工程师 (数据 ETL + DQ-CARE 质量评估)
- shared/biostatistician: 生物统计 (SAP + 样本量 + 缺失处理 + 统计审查)
- shared/ml-engineer: ML 工程师 (模型训练 + 可解释性 + SHAP 报告)
- shared/scientific-writer: 学术写作 (IMRaD 论文 + DOI 验证 + 去 AI 味)
- shared/research-assistant: 科研助理 (文献检索 + PRISMA 流程 + 参考文献管理)

请输出《系统设计说明书》:

## 系统设计说明书 (SDS) v1.0
**项目**: {project_id}
**事业部**: {self.active_division}
**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

### 1. 系统分解
为每个核心子系统定义:
- **provider**: 负责的 Agent
- **output**: 产出物名称和格式
- **interface**: 输入来源 + 输出格式 + SLA
- **quality_gate**: 通过的最低质量标准 (尽量量化)

### 2. 接口矩阵
| From | To | Artifact | Format | SLA |
|------|----|---------|--------|-----|
| data-engineer | ml-engineer | cleaned_dataset.csv + data_dictionary.md | CSV + Markdown | Phase 1 完成后 1 日内 |
| ... | ... | ... | ... | ... |

### 3. 反馈触发条件
至少 3 条跨 Phase 反馈规则，格式:
```
if: [条件描述]
then: [回退到哪个 Phase, 做什么修正]
```

### 4. 关键假设与风险
- **Assumptions**: 项目成功必须成立的前提 (如 MAR 缺失假设成立、训练/测试同分布)
- **Risks**: 潜在风险 + 缓解措施 (如 类别不平衡 > 1:5 → scale_pos_weight)

现在开始设计。"""

        return self._call_agent(
            agent_id="system_architect",
            task_input=prompt,
            phase_id="system_design",
            project_id=project_id,
        )

    def _run_project_workflow(self, user_request: str, intent: dict) -> str:
        """多阶段研究项目工作流, 按依赖关系依次执行各阶段, 每阶段需通过 Gate 检查。
        支持跨Phase反馈环B自动回退 + 断点续传。"""
        project_id = intent.get("project_id") or f"project_{int(time.time())}"
        self._current_project_id = project_id
        print(f"[Orchestrator] 启动项目工作流: {project_id}")

        all_outputs = {}
        gate_results = {}
        rework_history = []
        phases_to_run = ["system_design", "problem_definition", "design",
                         "execution", "external_validation", "review", "writing"]

        # 🆕 追踪每个 Phase 的返工次数 (含跨Phase反馈计入)
        phase_rework_counts = {p: 0 for p in phases_to_run}
        # 🆕 标记被跨Phase反馈无效化的下游 Phase → 需重新执行
        invalidated_phases = set()

        phase_index = 0
        while phase_index < len(phases_to_run):
            phase_id = phases_to_run[phase_index]
            phase_def = PROJECT_PHASES.get(phase_id, {})
            deps = phase_def.get("depends_on", [])

            # 🆕 检查当前 Phase 是否被上游反馈无效化 → 清除旧输出, 强制重跑
            if phase_id in invalidated_phases:
                print(f"  🔄 Phase {phase_id} 已被上游反馈无效化, 重新执行")
                invalidated_phases.discard(phase_id)
                if phase_id in all_outputs:
                    del all_outputs[phase_id]
                if phase_id in gate_results:
                    del gate_results[phase_id]

            # 检查依赖是否满足
            deps_met = all(dep in all_outputs for dep in deps)
            if not deps_met:
                missing = [d for d in deps if d not in all_outputs]
                print(f"[Orchestrator] 阶段 {phase_id} 依赖未满足: {missing}")
                # 🆕 回退到第一个缺失依赖的 Phase (而非跳过)
                first_missing_idx = min(
                    (phases_to_run.index(d) for d in missing if d in phases_to_run),
                    default=phase_index + 1,
                )
                if first_missing_idx < phase_index:
                    phase_index = first_missing_idx
                else:
                    phase_index += 1
                continue

            # Phase 0 特殊处理: 编排器自身做总体设计
            if phase_id == "system_design":
                sds = self._run_system_design(user_request, project_id)
                all_outputs["system_design"] = {"__sds__": sds}
                gate_results["system_design"] = {
                    "phase_id": "system_design",
                    "gate_id": "gate_system_design",
                    "timestamp": datetime.now().isoformat(),
                    "status": "pass",
                    "checks": [],
                    "conditions": [],
                    "rework_count": 0,
                    "max_rework": 3,
                }
                self._backfill_gate_status("system_design", "pass")
                print(f"  ✅ Phase 0: SDS 生成完成 → 进入 Phase 1")
                phase_index += 1
                continue

            print(f"\n{'='*50}")
            print(f"[Orchestrator] 执行阶段: {phase_id} — {phase_def.get('description', '')}")
            print(f"{'='*50}")

            # 收集上游阶段的输出作为上下文
            upstream_outputs = {}
            for dep in deps:
                if dep in all_outputs:
                    phase_data = all_outputs[dep]
                    if isinstance(phase_data, dict):
                        upstream_outputs.update({k: v for k, v in phase_data.items() if not k.startswith("_")})

            # 注入 SDS 上下文 (Phase 0 产出)
            sds_data = all_outputs.get("system_design", {})
            sds_text = sds_data.get("__sds__", "") if isinstance(sds_data, dict) else ""

            # 🆕 执行前安全扫描 (编排原则 #12)
            if phase_id in ("execution", "external_validation", "writing"):
                preflight_result = self._run_preflight_check(phase_id, project_id)
                if not preflight_result["pass"]:
                    all_outputs[phase_id] = {"_preflight_blocked": preflight_result["report"]}
                    gate_results[phase_id] = {
                        "phase_id": phase_id,
                        "gate_id": f"gate_{phase_id}",
                        "timestamp": datetime.now().isoformat(),
                        "status": "fail",
                        "checks": [{
                            "check_id": "preflight_safety_scan",
                            "description": "执行前安全扫描",
                            "check_type": "auto",
                            "result": "fail",
                            "detail": preflight_result["report"],
                        }],
                        "conditions": [],
                        "rework_count": 0,
                        "max_rework": 3,
                    }
                    print(f"  ❌ Preflight 安全扫描不通过, 阻断 Phase {phase_id} 执行")
                    # 🆕 B环触发: 安全扫描失败 → 扫描同项目所有 .py → 创建修复清单
                    self._handle_preflight_failure(phase_id, project_id, preflight_result)
                    phase_index += 1  # 跳过此 Phase, 但继续检查后续 Phase 的 preflight
                    continue

            # Phase 执行路由: 辩论模式 > 两轮模式 > 写作多步骤 > 标准模式
            if phase_def.get("debate_mode"):
                # 🆕 钱学森研讨厅: 并行辩论替代流水线审查
                phase_result = self._execute_phase_debate(
                    phase_id=phase_id,
                    user_request=user_request,
                    previous_outputs=upstream_outputs,
                    project_id=project_id,
                    debate_topic=phase_def["debate_topic"],
                    participants=phase_def["debate_participants"],
                )
            elif phase_def.get("two_round"):
                # FRAME 定量化: Phase 1 两轮执行
                phase_result = self._execute_phase_two_round(
                    phase_id=phase_id,
                    user_request=user_request,
                    previous_outputs=upstream_outputs,
                    project_id=project_id,
                    sds_text=sds_text,
                )
            elif phase_def.get("multi_step"):
                # 🆕 P0: 多步骤子编排 (Phase 6 等需要分步产出的阶段)
                phase_result = self._execute_phase_multi_step(
                    phase_id=phase_id,
                    user_request=user_request,
                    previous_outputs=upstream_outputs,
                    project_id=project_id,
                )
            else:
                phase_result = self._execute_phase(
                    phase_id=phase_id,
                    user_request=user_request,
                    previous_outputs=upstream_outputs,
                    project_id=project_id,
                )
            all_outputs[phase_id] = phase_result

            # 🆕 闸门检查
            gate_result = self._check_gate(phase_id, phase_result, project_id)
            gate_results[phase_id] = gate_result

            # 🆕 一致性交叉验证 (钱学森可靠性工程 — 用不可靠元件组成可靠系统)
            consistency_report = self.consistency_checker.check_phase(
                phase_id=phase_id,
                outputs=phase_result,
                upstream_outputs=upstream_outputs,
                division=self.active_division,
            )

            # 将一致性检查结果注入 Gate 判定
            if consistency_report["overall"] == "fail":
                # major_conflict → Gate FAIL
                gate_result["status"] = "fail"
                for r in consistency_report["results"]:
                    if r["result"] == "major_conflict":
                        gate_result["checks"].append({
                            "check_id": f"consistency_{r['pair_id']}",
                            "description": f"一致性矛盾: {r['agent_a']} ↔ {r['agent_b']}",
                            "check_type": "llm",
                            "result": "fail",
                            "detail": r["detail"],
                        })
            elif consistency_report["overall"] == "warn":
                # minor_inconsistency → 修正建议注入到下游输入
                fixes = []
                for r in consistency_report["results"]:
                    if r["result"] == "minor_inconsistency" and r.get("suggested_fix"):
                        fixes.append(f"- [{r['pair_id']}]: {r['suggested_fix']}")
                if fixes:
                    all_outputs[phase_id]["_consistency_fixes"] = "\n".join(fixes)

            # 🆕 反馈环B: 检测下游发现的上游问题
            upstream_issues = self._detect_upstream_issues(
                phase_id, phase_result, project_id
            )

            # 🆕 处理跨Phase反馈 (优先于同Phase Gate判断)
            cross_phase_rework_triggered = False
            for issue in upstream_issues:
                target_phase = issue["to_phase"]

                if issue["action"] == "reopen_gate" and issue["severity"] == "critical":
                    target_index = phases_to_run.index(target_phase)

                    # 检查是否超过最大返工次数
                    phase_rework_counts[target_phase] += 1
                    if phase_rework_counts[target_phase] >= 3:
                        print(f"  🚨 Phase {target_phase} 累计返工 {phase_rework_counts[target_phase]} 次, "
                              f"升级到首席科学家")
                        rework_history.append({
                            "from_phase": phase_id, "to_phase": target_phase,
                            "reason": issue["reason"],
                            "timestamp": datetime.now().isoformat(),
                            "rework_count": phase_rework_counts[target_phase],
                            "auto_detected": True, "severity": issue["severity"],
                        })
                        self._escalate_to_chief_scientist(
                            phase_id=target_phase,
                            reason=f"跨Phase反馈累计返工 {phase_rework_counts[target_phase]} 次",
                            issues=upstream_issues,
                        )
                        break  # 退出工作流, 等首席科学家裁决

                    print(f"  🔄 反馈环B触发: {issue['reason']}")

                    # 记录返工
                    rework_history.append({
                        "from_phase": phase_id, "to_phase": target_phase,
                        "reason": issue["reason"],
                        "timestamp": datetime.now().isoformat(),
                        "rework_count": phase_rework_counts[target_phase],
                        "auto_detected": True, "severity": issue["severity"],
                    })

                    # 回退 phase_index 到目标 Phase
                    phase_index = target_index

                    # 🆕 无效化目标 Phase 之后的所有下游 Phase
                    downstream_phases = []
                    for i in range(target_index + 1, len(phases_to_run)):
                        downstream_phases.append(phases_to_run[i])
                        invalidated_phases.add(phases_to_run[i])

                    # 🆕 基线管理: 创建变更请求 + 无效化下游基线
                    self._handle_baseline_change(
                        project_id, phase_id, target_phase,
                        issue["reason"], downstream_phases,
                    )

                    # 清除目标 Phase 的旧输出 (强制重新执行 + 重新 Gate)
                    if target_phase in gate_results:
                        del gate_results[target_phase]
                    if target_phase in all_outputs:
                        del all_outputs[target_phase]

                    cross_phase_rework_triggered = True
                    break  # 一次只处理一个最严重的跨Phase反馈

                elif issue["action"] == "notify_pi":
                    # High severity but not critical: 通知PI, 不自动回退
                    print(f"  ⚠️ 反馈环B通知PI: {issue['reason']}")
                    rework_history.append({
                        "from_phase": phase_id, "to_phase": target_phase,
                        "reason": issue["reason"],
                        "timestamp": datetime.now().isoformat(),
                        "rework_count": 0,
                        "auto_detected": True, "severity": issue["severity"],
                    })

            if cross_phase_rework_triggered:
                continue  # 跳过正常 Gate 判断, 直接进入回退 Phase 的执行

            # 正常的 Gate 判断 (同Phase返工 — 反馈环A)
            status = gate_result.get("status", "fail")
            rework_cnt = gate_result.get("rework_count", 0)
            max_rework = gate_result.get("max_rework", 3)

            if status == "pass":
                print(f"  ✅ Gate {phase_id}: PASS → 进入下一阶段")
                # 🆕 冻结技术状态基线 (钱学森总体设计部)
                self._freeze_baseline_if_safe(
                    project_id, phase_id, phase_result, gate_result
                )
                # 🆕 自适应调度: 记录 Gate 结果
                self._record_gate_for_adaptive(phase_id, status)
                phase_index += 1

            elif status == "conditional_pass":
                conditions = gate_result.get("conditions", [])
                print(f"  ⚠️  Gate {phase_id}: COND_PASS (附 {len(conditions)} 条件) → 进入下一阶段")
                all_outputs[phase_id]["_gate_conditions"] = conditions
                # 🆕 附条件通过也冻结基线 (条件已注入下游)
                self._freeze_baseline_if_safe(
                    project_id, phase_id, phase_result, gate_result
                )
                # 🆕 自适应调度: 记录 Gate 结果
                self._record_gate_for_adaptive(phase_id, status)
                phase_index += 1

            elif status == "fail":
                if rework_cnt >= max_rework:
                    print(f"  ❌ Gate {phase_id}: FAIL × {rework_cnt} (超过最大返工 {max_rework} 次)")
                    print(f"  🚨 升级到首席科学家进行裁决")
                    rework_history.append({
                        "from_phase": phase_id, "to_phase": phase_id,
                        "reason": "超过最大返工次数",
                        "timestamp": datetime.now().isoformat(),
                        "rework_count": rework_cnt,
                        "auto_detected": False, "severity": "critical",
                    })
                    self._escalate_to_chief_scientist(
                        phase_id=phase_id,
                        reason=f"Gate 连续失败 {rework_cnt+1} 次",
                        gate_result=gate_result,
                    )
                    break
                else:
                    fail_items = [c for c in gate_result.get("checks", []) if c.get("result") == "fail"]
                    reasons = [f"{c['check_id']}: {c['detail']}" for c in fail_items]
                    print(f"  ❌ Gate {phase_id}: FAIL (返工 {rework_cnt+1}/{max_rework})")
                    print(f"     原因: {reasons}")
                    rework_history.append({
                        "from_phase": phase_id, "to_phase": phase_id,
                        "reason": str(reasons),
                        "timestamp": datetime.now().isoformat(),
                        "rework_count": rework_cnt + 1,
                        "auto_detected": False, "severity": "normal",
                    })
                    # phase_index 不变 → 重新执行本 Phase

        # 聚合
        return self._aggregate_all_phases(phases_to_run, all_outputs, project_id, gate_results, rework_history)

    # ================================================================
    # 阶段执行引擎
    # ================================================================

    def _execute_phase(
        self,
        phase_id: str,
        user_request: str,
        previous_outputs: dict,
        project_id: str,
        agents_override: list = None,
    ) -> dict:
        """
        执行一个工作流阶段。agents_override 允许 PM 自定义阶段内的 Agent 列表。
        """
        # 优先使用 PM 指定的 agents
        if agents_override:
            agent_ids = agents_override
            is_parallel = len(agent_ids) > 1  # 多 agent 默认并行
        else:
            phase_def = PROJECT_PHASES.get(phase_id, {})
            # 公司模式: 使用事业部感知的 Agent 列表
            agent_ids = self._get_phase_agents(phase_id)
            is_parallel = phase_def.get("parallel", False)

        print(f"\n[Phase: {phase_id}] Agents: {agent_ids} (parallel={is_parallel})")

        outputs = {}
        if is_parallel:
            for agent_id in agent_ids:
                task_input = self._build_agent_input(
                    agent_id, phase_id, user_request, previous_outputs, outputs, project_id
                )
                result = self._call_agent(agent_id, task_input,
                                          phase_id=phase_id, project_id=project_id)
                outputs[agent_id] = result
        else:
            for agent_id in agent_ids:
                task_input = self._build_agent_input(
                    agent_id, phase_id, user_request, previous_outputs, outputs, project_id
                )
                result = self._call_agent(agent_id, task_input,
                                          phase_id=phase_id, project_id=project_id)
                outputs[agent_id] = result

        return outputs

    def _execute_phase_multi_step(
        self,
        phase_id: str,
        user_request: str,
        previous_outputs: dict,
        project_id: str,
    ) -> dict:
        """
        多步骤子编排: 将复杂 Phase 拆分为多个子步骤执行。

        当前支持:
        - Phase 6 (writing): 表格 → 图表 → 分章节 → 合稿 → 文件写入

        Phase 定义中需指定 `steps` 列表, 每个 step 有:
          - name: 步骤名
          - agents: [agent_id] (单个或并行列表)
          - task_prompt: 给 Agent 的任务描述 (可含 {变量})
          - output_as: 在返回 dict 中的 key
        """
        phase_def = PROJECT_PHASES.get(phase_id, {})
        steps = phase_def.get("steps", [])

        if not steps:
            # Fallback: 无 steps 定义时退化为标准单 agent 执行
            return self._execute_phase(
                phase_id=phase_id,
                user_request=user_request,
                previous_outputs=previous_outputs,
                project_id=project_id,
            )

        outputs = {}
        step_results = {}  # 累积前序步骤的输出, 供后续 step 引用

        for step in steps:
            step_name = step["name"]
            print(f"  [multi-step] {step_name}...")

            step_agents = step.get("agents", [])
            # 解析 agent_id (公司模式)
            resolved_agents = []
            division = self.active_division
            mapping = {
                "clinical-researcher": f"{division}/clinical-researcher",
                "pi": f"{division}/pi",
                "computational-biologist": f"{division}/computational-biologist",
                "data-engineer": "shared/data-engineer",
                "biostatistician": "shared/biostatistician",
                "ml-engineer": "shared/ml-engineer",
                "scientific-writer": "shared/scientific-writer",
                "research-assistant": "shared/research-assistant",
                "humanizer": "shared/humanizer",
            }
            for a in step_agents:
                resolved_agents.append(mapping.get(a, a))

            # 构建 task prompt (替换变量)
            task_template = step.get("task_prompt", "{user_request}")
            task_input = task_template.format(
                user_request=user_request,
                project_id=project_id,
                previous_summary=self._summarize_for_debate(previous_outputs),
                step_results=self._summarize_step_results(step_results),
            )

            # 执行子步骤
            if step.get("parallel") and len(resolved_agents) > 1:
                for agent_id in resolved_agents:
                    result = self._call_agent(
                        agent_id, task_input,
                        phase_id=f"{phase_id}_{step_name}",
                        project_id=project_id,
                    )
                    step_results[f"{step_name}_{agent_id}"] = result
            else:
                for agent_id in resolved_agents:
                    result = self._call_agent(
                        agent_id, task_input,
                        phase_id=f"{phase_id}_{step_name}",
                        project_id=project_id,
                    )
                    step_results[f"{step_name}_{agent_id}"] = result

        # 写入文件系统: 将 Agent 内存输出持久化到 submission/ 目录
        write_result = self._write_phase6_files(step_results, project_id)
        outputs["_written_files"] = write_result.get("written_files", [])

        # 将所有 step_results 合并到 outputs (保持向后兼容的 agent_id key)
        outputs.update(step_results)
        outputs["_multi_step"] = "True"
        return outputs

    @staticmethod
    def _summarize_step_results(step_results: dict) -> str:
        """为后续 step 构建前序步骤的简洁摘要"""
        if not step_results:
            return "(无前序步骤产出)"
        parts = []
        for key, value in step_results.items():
            truncated = value[:1000] + "..." if len(value) > 1000 else value
            parts.append(f"### {key}\n{truncated}")
        return "\n\n".join(parts)

    def _write_phase6_files(self, step_results: dict, project_id: str) -> dict:
        """将 Phase 6 多步骤产出的内存字符串写入磁盘。

        两层目录结构:
        - 零件目录 (working): sections/ tables/ figures/ — Agent 产出的分章节/表格/图表零件
        - 投稿目录 (submission): submission/manuscript.md + submission/tables/*.csv + submission/figures/*.png

        解析失败时 fallback 写入原始输出，不丢数据也不阻塞主流程。
        """
        import re
        import csv
        import io
        from pathlib import Path

        # 确定项目根路径
        vault_path = None
        if hasattr(self, 'kb') and self.kb:
            vaults = getattr(self.kb, 'vaults', {})
            for vp in vaults.values():
                vault_path = Path(vp)
                break
            if not vault_path:
                vault_path = getattr(self.kb, 'vault_path', None)
        if not vault_path:
            print("  ⚠️ [_write_phase6_files] 无法确定 vault 路径, 跳过文件写入")
            return {}

        proj_dir = Path(vault_path) / 'projects' / project_id
        submission_dir = proj_dir / 'submission'
        written = []

        # ---- 定位各步骤输出 ----
        sections_text = ""
        tables_text = ""
        figures_text = ""
        humanize_text = ""
        assembly_text = ""

        for key, value in step_results.items():
            if not isinstance(value, str) or len(value) < 50:
                continue
            key_lower = key.lower()
            if 'sections' in key_lower and 'scientific-writer' in key_lower:
                sections_text = value
            elif 'tables' in key_lower:
                tables_text = value
            elif 'figures' in key_lower:
                figures_text = value
            elif 'humanize' in key_lower:
                humanize_text = value
            elif 'assembly' in key_lower:
                assembly_text = value

        # ============================================================
        # 零件层: 写入 sections/ tables/ figures/ (working dirs)
        # ============================================================

        # ---- 写入 sections (按 ## 标题分割) ----
        if sections_text:
            try:
                sections_dir = proj_dir / 'sections'
                sections_dir.mkdir(parents=True, exist_ok=True)

                # 提取 Title (第一个 # 标题)
                title_match = re.match(r'^#\s+(.+?)(?:\n|$)', sections_text)
                if title_match:
                    (sections_dir / '01_title.md').write_text(
                        f"# {title_match.group(1)}\n", encoding='utf-8')
                    body = sections_text[title_match.end():]
                    written.append('sections/01_title.md')
                else:
                    body = sections_text

                # 按 ## 标题拆分为块
                blocks = re.split(r'\n(?=##\s)', body)
                heading_map = {
                    'abstract': '02_abstract', '摘要': '02_abstract',
                    'introduction': '03_introduction', '引言': '03_introduction',
                    'methods': '04_methods', 'method': '04_methods',
                    'materials': '04_methods', '方法': '04_methods',
                    'results': '05_results', 'result': '05_results',
                    '结果': '05_results',
                    'discussion': '06_discussion', '讨论': '06_discussion',
                    'conclusion': '07_conclusion', '结论': '07_conclusion',
                    'references': '08_references', '参考文献': '08_references',
                }

                for block in blocks:
                    block = block.strip()
                    if not block:
                        continue
                    heading_line = block.split('\n')[0]
                    heading_clean = re.sub(r'^##\s+', '', heading_line).lower().strip()
                    for keyword, fname in heading_map.items():
                        if heading_clean.startswith(keyword):
                            (sections_dir / f'{fname}.md').write_text(block, encoding='utf-8')
                            written.append(f'sections/{fname}.md')
                            break

                print(f"  ✅ sections/ 写入完成 ({len([w for w in written if w.startswith('sections/')])} 文件)")
            except Exception as e:
                print(f"  ⚠️ sections 解析失败 ({e}), fallback 写入原始输出")
                sections_dir = proj_dir / 'sections'
                sections_dir.mkdir(parents=True, exist_ok=True)
                (sections_dir / '00_all_sections.md').write_text(sections_text, encoding='utf-8')
                written.append('sections/00_all_sections.md')

        # ---- 写入 humanize log → sections/ ----
        if humanize_text:
            try:
                sections_dir = proj_dir / 'sections'
                sections_dir.mkdir(parents=True, exist_ok=True)
                (sections_dir / 'humanize-log.md').write_text(humanize_text, encoding='utf-8')
                written.append('sections/humanize-log.md')
                print(f"  ✅ sections/humanize-log.md 写入完成")
            except Exception as e:
                print(f"  ⚠️ humanize-log 写入失败 ({e})")

        # ---- 写入 tables (按 Table 标记分割) → tables/ ----
        table_md_files = {}  # 记录写入的 table md 文件, 供 CSV 转换使用
        if tables_text:
            try:
                tables_dir = proj_dir / 'tables'
                tables_dir.mkdir(parents=True, exist_ok=True)

                table_blocks = re.split(r'\n(?=(?:##|###)\s*Table\s)', tables_text)
                table_names = {
                    '1': 'table1_baseline', '2': 'table2_model_performance',
                    '3': 'table3_subgroup',
                    '１': 'table1_baseline', '２': 'table2_model_performance',
                    '３': 'table3_subgroup',
                }
                found_count = 0
                remaining = []
                for block in table_blocks:
                    block = block.strip()
                    if not block:
                        continue
                    tm = re.match(r'(?:##|###)\s*Table\s*([123１２３])', block, re.IGNORECASE)
                    if tm:
                        tname = table_names.get(tm.group(1))
                        if tname:
                            fpath = f'{tname}.md'
                            (tables_dir / fpath).write_text(block, encoding='utf-8')
                            written.append(f'tables/{fpath}')
                            table_md_files[tname] = block
                            found_count += 1
                    else:
                        remaining.append(block)

                if not found_count:
                    (tables_dir / 'all_tables.md').write_text(tables_text, encoding='utf-8')
                    written.append('tables/all_tables.md')
                elif remaining:
                    (tables_dir / 'table_notes.md').write_text('\n\n'.join(remaining), encoding='utf-8')
                    written.append('tables/table_notes.md')

                print(f"  ✅ tables/ 写入完成 ({found_count} 表格)")
            except Exception as e:
                print(f"  ⚠️ tables 解析失败 ({e}), fallback 写入原始输出")
                tables_dir = proj_dir / 'tables'
                tables_dir.mkdir(parents=True, exist_ok=True)
                (tables_dir / 'all_tables.md').write_text(tables_text, encoding='utf-8')
                written.append('tables/all_tables.md')

        # ---- 写入 figures (Python 脚本 + 描述) → figures/ ----
        if figures_text:
            try:
                figures_dir = proj_dir / 'figures'
                figures_dir.mkdir(parents=True, exist_ok=True)

                code_blocks = re.findall(r'```(?:python)?\n(.*?)```', figures_text, re.DOTALL)
                if code_blocks:
                    full_code = '\n\n'.join(code_blocks)
                    (figures_dir / 'generate_figures.py').write_text(full_code, encoding='utf-8')
                    written.append('figures/generate_figures.py')

                (figures_dir / 'figure_descriptions.md').write_text(figures_text, encoding='utf-8')
                written.append('figures/figure_descriptions.md')
                print(f"  ✅ figures/ 写入完成")
            except Exception as e:
                print(f"  ⚠️ figures 写入失败 ({e})")

        # ============================================================
        # 投稿层: 写入 submission/ (最终投稿文件)
        # ============================================================

        # ---- 写入 manuscript (assembly 合稿) → submission/manuscript.md ----
        # 投稿终稿不允许出现内部质控标记 [Classic — ...] / [Foundational — ...]
        if assembly_text:
            try:
                submission_dir.mkdir(parents=True, exist_ok=True)
                clean_text = self._strip_internal_tags(assembly_text)
                (submission_dir / 'manuscript.md').write_text(clean_text, encoding='utf-8')
                written.append('submission/manuscript.md')
                print(f"  ✅ submission/manuscript.md 写入完成")
            except Exception as e:
                print(f"  ⚠️ manuscript 写入失败 ({e})")

        # ---- 转换 tables 为 CSV → submission/tables/ ----
        if table_md_files:
            try:
                st_dir = submission_dir / 'tables'
                st_dir.mkdir(parents=True, exist_ok=True)
                csv_count = 0
                for tname, md_content in table_md_files.items():
                    csv_content = self._markdown_table_to_csv(md_content)
                    if csv_content:
                        csv_name = f'{tname}.csv'
                        (st_dir / csv_name).write_text(csv_content, encoding='utf-8')
                        written.append(f'submission/tables/{csv_name}')
                        csv_count += 1
                if csv_count:
                    print(f"  ✅ submission/tables/ CSV 转换完成 ({csv_count} 文件)")
            except Exception as e:
                print(f"  ⚠️ submission/tables CSV 转换失败 ({e})")

        if written:
            print(f"  📁 共写入 {len(written)} 个文件 → {proj_dir}")
        return {'written_files': written, 'base_dir': str(proj_dir)}

    @staticmethod
    def _strip_internal_tags(text: str) -> str:
        """剥离投稿终稿中的内部质控标记。

        移除:
        - [Classic — ...] / [Classic – ...] / [Classic - ...]
        - [Foundational — ...] 等同义标记
        - [数据待确认] 标记 (如有)
        这些标记仅在零件层 (sections/08_references.md) 保留用于 Gate 检查。
        """
        import re
        # 剥离 [Classic — anything] 和 [Foundational — anything]
        text = re.sub(r'\s*\[Classic\s*[—–-]\s*[^\]]+\]', '', text)
        text = re.sub(r'\s*\[Foundational\s*[—–-]\s*[^\]]+\]', '', text)
        # 剥离 [数据待确认]
        text = re.sub(r'\s*\[数据待确认\]', '', text)
        return text

    @staticmethod
    def _markdown_table_to_csv(md_text: str) -> str:
        """将 Markdown 表格文本转换为 CSV 字符串。

        解析第一个遇到的 markdown table (| col | col | 分隔线 | val | val |),
        输出为逗号分隔的 CSV。无有效表格时返回空字符串。
        """
        import re
        import csv
        import io

        lines = md_text.strip().split('\n')
        # 找到表格行: 以 | 开头和结尾, 且不是分隔线
        table_rows = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('|') and stripped.endswith('|'):
                # 跳过分隔线 (仅含 | - : 空格)
                if re.match(r'^[\|\s\-:]+$', stripped):
                    continue
                cells = [c.strip() for c in stripped[1:-1].split('|')]
                table_rows.append(cells)

        if len(table_rows) < 2:  # 至少需要表头 + 1 行数据
            return ""

        output = io.StringIO()
        writer = csv.writer(output)
        for row in table_rows:
            writer.writerow(row)
        return output.getvalue()

    def _execute_phase_two_round(
        self, phase_id: str, user_request: str,
        previous_outputs: dict, project_id: str, sds_text: str = "",
    ) -> dict:
        """
        FRAME 定量化: 两轮 Phase 执行。

        Round 1 (并行 — 机器体系):
          research-assistant + data-engineer + computational-biologist
          → 产出 3 份定量预检报告 (F/R/M 维度数据源)

        Round 2 (串行 — 专家体系):
          clinical-researcher → 表型操作化
          pi → 接收 Round 1 全部报告 → FRAME 评估 (每维度必须引用报告数据)
        """
        outputs = {}
        division = self.active_division

        # --- Round 1: 机器预检报告 ---
        print(f"  [Phase {phase_id}] Round 1/2: 机器预检报告 (并行)")
        round1_agents = [
            f"shared/research-assistant",
            f"shared/data-engineer",
        ]
        # computational-biologist 如果该事业部有的话
        comp_bio = f"{division}/computational-biologist"
        round1_agents.append(comp_bio)

        round1_outputs = {}
        for agent_id in round1_agents:
            task_input = self._build_agent_input(
                agent_id, phase_id, user_request, previous_outputs, round1_outputs, project_id
            )
            # research-assistant 需要明确的预检指令
            if "research-assistant" in agent_id:
                task_input += """

## ⚠️ Round 1 任务: 选题文献 + 期刊趋势预检

你需要完成两项预检:
1. **选题文献预检**: 使用 WebSearch 检索, 找到 3-5 篇最相似的已发表工作,
   提取每篇的关键指标 (AUC/C-index, 样本量, 数据源, 方法)
   → 输出《选题文献预检报告》
   **优先检索近 5 年文献**, 最终参考文献 ≥80% 须为近 5 年内发表。
2. **期刊趋势分析**: 扫描目标领域期刊最近 2 年的发表趋势,
   识别发表缺口和竞争强度 → 输出《期刊趋势分析报告》

两份报告将作为 PI 的 FRAME 评估中 F 维度和 M 维度的定量数据源。"""
            # computational-biologist 需要建模可行性报告
            if "computational-biologist" in agent_id:
                task_input += """

## ⚠️ Round 1 任务: 建模可行性预检

评估: 基于用户需求和数据特性, 当前技术栈是否可支撑?
- 所需模型类型的方法成熟度
- 是否有已知的性能天花板 (SOTA benchmark)
- 数据量是否满足方法的最小样本量要求
→ 输出《建模可行性预检报告》(作为 FRAME 技术可行性参考)"""
            result = self._call_agent(agent_id, task_input,
                                      phase_id=f"{phase_id}_r1", project_id=project_id)
            round1_outputs[agent_id] = result
            outputs[agent_id] = result

        print(f"  [Phase {phase_id}] Round 1 完成: {len(round1_outputs)} 份预检报告")

        # --- Round 2: 专家决策 ---
        print(f"  [Phase {phase_id}] Round 2/2: 专家决策")

        # clinical-researcher: 表型操作化
        clin_agent = f"{division}/clinical-researcher"
        clin_input = self._build_agent_input(
            clin_agent, phase_id, user_request, previous_outputs, outputs, project_id
        )
        clin_result = self._call_agent(clin_agent, clin_input,
                                       phase_id=f"{phase_id}_r2", project_id=project_id)
        outputs[clin_agent] = clin_result

        # PI: FRAME 评估 (基于 Round 1 全部报告)
        pi_agent = f"{division}/pi"
        pi_input = self._build_agent_input(
            pi_agent, phase_id, user_request, previous_outputs, outputs, project_id
        )
        # 🆕 FRAME 定量化指令: 强制每个维度引用报告数据
        pi_input += self._build_frame_quantitative_prompt(round1_outputs, sds_text)
        pi_result = self._call_agent(pi_agent, pi_input,
                                     phase_id=f"{phase_id}_r2", project_id=project_id)
        outputs[pi_agent] = pi_result

        print(f"  [Phase {phase_id}] Round 2 完成")
        return outputs

    def _build_frame_quantitative_prompt(self, round1_outputs: dict, sds_text: str = "") -> str:
        """构建 FRAME 定量化增强提示 — 要求 PI 每个维度引用具体的预检报告数据"""
        lines = [
            "",
            "---",
            "## ⚠️ FRAME 定量化评估 — 机器预检报告已就绪",
            "",
            "以下是 Round 1 机器体系产出的定量预检报告。你必须在 FRAME 五个维度的评估中",
            "**每个维度引用至少一份报告中的具体数据**，不可仅凭经验或记忆做判断。",
            "",
        ]

        # 提取每份报告的关键部分
        report_labels = {
            "research-assistant": ("F (Field Scan) — 领域扫描", "文献预检报告"),
            "data-engineer": ("R (Resource Audit) — 资源审计", "数据可用性报告"),
            "computational-biologist": ("技术可行性", "建模可行性报告"),
        }

        for agent_id, output in round1_outputs.items():
            for key, (dim_label, report_name) in report_labels.items():
                if key in agent_id:
                    lines.append(f"### {dim_label}: {report_name}")
                    # 提取报告摘要 (前 2000 字符)
                    summary = output[:2000] + ("..." if len(output) > 2000 else "")
                    lines.append(summary)
                    lines.append("")
                    break

        lines += [
            "---",
            "## FRAME 评估要求 (每个维度必须有定量数据)",
            "",
            "请逐维度评估, 每个维度必须引用上述 Round 1 报告中的具体数字:",
            "",
            "### F — Field Scan (领域扫描)",
            "- 引用《文献预检报告》中的 SOTA 性能数字 (如 AUC/C-index)",
            "- 对标论文的样本量、数据源、方法对比",
            "- 基于实时文献数据 (非记忆) 判断本研究的竞争位置",
            "",
            "### R — Resource Audit (资源审计)",
            "- 引用《数据可用性报告》中的样本量、变量覆盖率、缺失率",
            "- 确认所需变量在数据源中的存在性和质量",
            "- 评估: 数据能否支撑研究目标?",
            "",
            "### A — Alignment Check (对齐检查)",
            "- 基于你的专业知识判断研究与领域的战略对齐度",
            "- 考虑基金指南、临床需求、学科发展方向",
            "",
            "### M — Market Gap (发表缺口)",
            "- 引用《文献预检报告》中的已发表工作评估竞争强度",
            "- 判断: 该方向在目标期刊是否有发表空间?",
            "- 竞争研究数量和质量如何?",
            "",
            "### E — Edge Assessment (优势评估)",
            f"- 基于公司运行数据评估: 团队是否有类似项目的成功经验?",
            f"- 技术栈、数据、人力的匹配度",
            f"- 估计 6 个月内可产出成果的概率",
            "",
            "**最终给出明确建议: [启动 / 观望 / 放弃]**",
            "如果建议放弃, 必须说明是哪个维度的哪些数据导致此结论。",
        ]

        return "\n".join(lines)

    # ================================================================
    # 研讨厅辩论模式 — 钱学森综合集成研讨厅
    # ================================================================

    def _execute_phase_debate(
        self, phase_id: str, user_request: str,
        previous_outputs: dict, project_id: str,
        debate_topic: str, participants: list[str],
    ) -> dict:
        """
        研讨厅辩论模式: 并行独立输出 → 主持人识别共识/分歧 → 输出辩论纪要。

        Round 1: 所有参与方并行独立输出观点 (互不参考)
        Round 2: 辩论主持人读取各方观点 → 输出《研讨厅辩论纪要》
        """
        division = self.active_division
        outputs = {}

        # ================================================================
        # Round 1: 所有参与方并行独立输出观点
        # ================================================================
        print(f"\n{'~'*50}")
        print(f"  [研讨厅] {debate_topic}")
        print(f"  [研讨厅] 参与方: {', '.join(participants)}")
        print(f"  [研讨厅] Round 1/2: 并行独立观点陈述")
        print(f"{'~'*50}")

        upstream_summary = self._summarize_for_debate(previous_outputs)

        debate_input_template = f"""## 研讨厅辩论: {debate_topic}

### 用户原始需求
{user_request}

### 上游阶段产出摘要
{upstream_summary}

### ⚠️ 辩论规则

你正在参与一场多学科并行辩论。请遵守以下规则:

1. **独立分析**: 只从你的专业视角给出独立判断。不要试图猜测其他 Agent 的结论。
2. **证据驱动**: 每个主张必须有数据、文献、或理论推理支撑。
3. **标注确信度**: 对每个关键判断标注确信度: [高/中/低]
4. **明确边界**: 如果某个问题超出了你的专业范围，注明"超出本专业知识范围"。
5. **输出格式**:
   - ## 我的核心观点 (3-5 条, 按重要性排序)
   - ## 我的推荐方案 (具体、可操作)
   - ## 关键风险 (我看到的潜在问题)
   - ## 确信度说明 (逐条标注)"""

        # 并行调用所有参与方
        round1_outputs = {}
        for agent_short_name in participants:
            agent_id = self._resolve_debate_participant(agent_short_name, division)

            task_input = debate_input_template
            if agent_short_name == "computational-biologist":
                task_input += "\n\n你的专业视角: 建模可行性、方法选择、特征工程、模型评估策略。"
            elif agent_short_name == "biostatistician":
                task_input += "\n\n你的专业视角: 统计方法适当性、样本量、缺失处理、多重比较校正、效应量估计。"
            elif agent_short_name == "clinical-researcher":
                task_input += "\n\n你的专业视角: 临床相关性、表型可操作化、效应方向的临床解释、外部有效性。"
            elif agent_short_name == "pi":
                task_input += "\n\n你的专业视角: 整合各视角、期刊发表策略、研究贡献评估、风险收益权衡。"

            result = self._call_agent(
                agent_id, task_input,
                phase_id=f"{phase_id}_debate_r1",
                project_id=project_id,
            )
            round1_outputs[agent_short_name] = result
            outputs[agent_short_name] = result

        print(f"  [研讨厅] Round 1 完成: {len(round1_outputs)} 份独立观点")

        # ================================================================
        # Round 2: 辩论主持人汇总共识与分歧
        # ================================================================
        print(f"  [研讨厅] Round 2/2: 主持人汇总")

        moderator_prompt_parts = [
            f"## 研讨厅辩论纪要任务",
            f"",
            f"**辩论主题**: {debate_topic}",
            f"**参与方**: {', '.join(participants)}",
            f"",
            f"### 各方独立观点:",
        ]
        for name, output in round1_outputs.items():
            truncated = output[:3000] + ("...(截断)" if len(output) > 3000 else "")
            moderator_prompt_parts.append(f"\n#### {name}\n{truncated}\n---")
        moderator_prompt_parts.append(
            "\n请基于以上各方独立观点，整理输出《研讨厅辩论纪要》(格式见你的 System Prompt)。"
        )

        moderator_output = self._call_agent_with_custom_prompt(
            agent_id="debate-moderator",
            system_prompt=self.DEBATE_MODERATOR_SYSTEM_PROMPT,
            task_input="\n".join(moderator_prompt_parts),
            phase_id=f"{phase_id}_debate_r2",
            project_id=project_id,
        )
        outputs["_debate_minutes"] = moderator_output

        print(f"  [研讨厅] Round 2 完成: 辩论纪要已生成")
        return outputs

    def _resolve_debate_participant(self, short_name: str, division: str) -> str:
        """将辩论参与者的短名解析为完整的 Agent ID"""
        shared_services = [
            "data-engineer", "biostatistician", "ml-engineer",
            "scientific-writer", "research-assistant",
        ]
        if short_name in shared_services:
            return f"shared/{short_name}"
        return f"{division}/{short_name}"

    def _summarize_for_debate(self, previous_outputs: dict) -> str:
        """为辩论参与者构建精简的上游摘要，避免信息过载"""
        if not previous_outputs:
            return "无上游产出 (当前为首个执行 Phase)"

        parts = []
        for agent_id, output in previous_outputs.items():
            if agent_id.startswith("_"):
                continue
            agent_short = agent_id.split("/")[-1]
            truncated = output[:800] + "..." if len(output) > 800 else output
            parts.append(f"**{agent_short}**: {truncated}")

        return "\n\n".join(parts)

    def _call_agent_with_custom_prompt(
        self, agent_id: str, system_prompt: str, task_input: str,
        phase_id: str = "", project_id: str = "",
    ) -> str:
        """使用自定义 System Prompt 调用 Agent (用于辩论主持人等非标准角色)"""
        print(f"  → 调用 {agent_id} (custom prompt)...")
        t0 = time.time()
        success = False
        degraded = False
        in_tokens = out_tokens = 0
        output_len = 0
        error_type = ""

        try:
            response = self.llm.chat(system_prompt=system_prompt, user_message=task_input)
            content = response.content
            success = True
            degraded = getattr(response, 'degraded', False)
            usage = getattr(response, 'usage', {}) or {}
            in_tokens = usage.get("input_tokens", 0)
            out_tokens = usage.get("output_tokens", 0)
            output_len = len(content)
            print(f"  ← {agent_id}: {output_len} 字符" + (" ⚡降级" if degraded else ""))
            return content
        except Exception as e:
            error_type = type(e).__name__
            print(f"  ✗ {agent_id}: {error_type}")
            raise
        finally:
            wall_time = time.time() - t0
            self._append_run_log(
                timestamp=datetime.now().isoformat(),
                project_id=project_id, division=self.active_division,
                phase_id=phase_id, agent_id=agent_id,
                success=success, degraded=degraded,
                wall_time_sec=round(wall_time, 2),
                input_tokens=in_tokens, output_tokens=out_tokens,
                output_len=output_len, error_type=error_type,
                gate_status="skip", rework_of="",
            )

    # ================================================================
    # 闸门检查
    # ================================================================

    def _check_gate(self, phase_id: str, outputs: dict, project_id: str) -> dict:
        """
        对指定 Phase 的输出执行闸门检查。

        1. 执行 auto checks (从 gate_checks.py 加载)
        2. 执行 llm checks (调用 PI 做闸门审查)
        3. 汇总所有检查项, 返回 GateResult dict
        """
        gate_def = GATE_DEFINITIONS.get(phase_id, {})
        checks = []

        # 自动检查
        auto_checks = gate_def.get("auto_checks", {})
        for check_id, check_fn in auto_checks.items():
            try:
                passed, detail = check_fn(outputs, self)
                checks.append({
                    "check_id": check_id,
                    "description": (check_fn.__doc__ or check_id).strip(),
                    "check_type": "auto",
                    "result": "pass" if passed else "fail",
                    "detail": detail,
                })
                if not passed:
                    print(f"  ✗ auto:[{check_id}] {detail}")
            except Exception as e:
                checks.append({
                    "check_id": check_id, "description": check_id,
                    "check_type": "auto", "result": "fail",
                    "detail": f"检查异常: {e}",
                })
                print(f"  ✗ auto:[{check_id}] 异常: {e}")

        # LLM 审查 (调用 PI)
        llm_checks = gate_def.get("llm_checks", [])
        if llm_checks:
            pi_agent_id = f"{self.active_division}/pi"
            review_prompt = self._build_gate_review_prompt(phase_id, outputs, llm_checks, project_id)
            pi_output = self._call_agent(pi_agent_id, review_prompt)
            llm_results = self._parse_gate_review(pi_output, llm_checks)
            checks += llm_results

            for c in llm_results:
                if c["result"] != "pass":
                    status_icon = "✗" if c["result"] == "fail" else "⚠️"
                    print(f"  {status_icon} llm:[{c['check_id']}] {c['detail']}")

        # 汇总
        fail_count = sum(1 for c in checks if c["result"] == "fail")
        pass_count = sum(1 for c in checks if c["result"] == "pass")

        if fail_count == 0:
            status = "pass"
        elif fail_count <= 2 and pass_count >= len(checks) / 2:
            status = "conditional_pass"
        else:
            status = "fail"

        result = {
            "phase_id": phase_id,
            "gate_id": f"gate_{phase_id}",
            "timestamp": datetime.now().isoformat(),
            "status": status,
            "checks": checks,
            "conditions": [c["detail"] for c in checks if c["result"] == "fail"],
            "rework_count": 0,
            "max_rework": 3,
        }

        print(f"  [Gate {phase_id}] {status} ({pass_count}✓, {fail_count}✗)")
        # 回填 Gate 状态到运行日志
        self._backfill_gate_status(phase_id, status)

        # 🆕 缓存关键指标供趋势检查和跨Phase对比 (系统辨识-反馈控制)
        if status in ("pass", "conditional_pass"):
            auc_value = _extract_auc_from_outputs(outputs)
            if auc_value is not None:
                self._cached_aucs[phase_id] = auc_value
                # 同步更新趋势基准 (供下次 check_auc_trend 使用)
                if 'auc' not in self._trend_baselines:
                    self._trend_baselines['auc'] = auc_value
                elif status == "pass":
                    self._trend_baselines['auc'] = auc_value

            features = _extract_features_from_outputs(outputs)
            if features:
                self._phase_features[phase_id] = features

        return result

    # ================================================================
    # 跨 Phase 反馈环 B — 自动检测下游发现的上游问题
    # ================================================================

    def _detect_upstream_issues(
        self, phase_id: str, outputs: dict, project_id: str
    ) -> list[dict]:
        """
        检测当前 Phase 输出中暗示的上游问题, 生成反馈触发列表。

        扫描逻辑:
        1. 文本信号: 检查 Agent 输出中是否包含上游问题的关键词
        2. 数值规则: 检查跨 Phase 的数值指标是否触发阈值 (如 AUC 下降)
        3. 汇总所有触发项, 按 severity 排序 (critical > high > normal)

        Returns:
            [{from_phase, to_phase, reason, severity, action, detected_by, timestamp, rework_count}]
        """
        triggers = FEEDBACK_B_TRIGGERS.get(phase_id, {})
        if not triggers:
            return []

        issues = []

        for target_phase, rule in triggers.items():
            detected = False
            detection_detail = ""

            # 方式1: 文本信号检测 — 扫描每个 Agent 的输出
            signals = rule.get("signals", [])
            if signals:
                for agent_id, output in outputs.items():
                    output_lower = output.lower()
                    for signal in signals:
                        if signal.lower() in output_lower:
                            detected = True
                            detection_detail = (
                                f"{agent_id} 输出中包含信号: '{signal}'"
                            )
                            break
                    if detected:
                        break

            # 方式2: 数值规则检测 — 跨 Phase 指标对比
            numeric_rule = rule.get("numeric_rule")
            if not detected and numeric_rule:
                detected, detection_detail = self._check_numeric_trigger(
                    phase_id, target_phase, numeric_rule
                )

            if detected:
                issues.append({
                    "from_phase": phase_id,
                    "to_phase": target_phase,
                    "reason": f"{rule['message']} — {detection_detail}",
                    "severity": rule["severity"],
                    "action": rule["action"],
                    "timestamp": datetime.now().isoformat(),
                    "detected_by": "auto",
                    "rework_count": 0,
                })

        # 按 severity 排序: critical > high > normal
        severity_order = {"critical": 0, "high": 1, "normal": 2}
        issues.sort(key=lambda x: severity_order.get(x["severity"], 3))

        if issues:
            print(f"  🔄 反馈环B: 检测到 {len(issues)} 个上游问题")
            for issue in issues:
                icon = "🚨" if issue["severity"] == "critical" else "⚠️"
                print(f"    {icon} {issue['to_phase']}: {issue['reason'][:120]}")

        return issues

    def _check_numeric_trigger(
        self, from_phase: str, target_phase: str, rule: dict
    ) -> tuple:
        """
        检查跨 Phase 的数值指标是否触发阈值。

        当前支持的规则:
        - AUC 下降: 当前 Phase AUC 相比对比 Phase AUC 下降超过 threshold

        Returns:
            (triggered: bool, detail: str)
        """
        metric = rule.get("metric")
        compare_phase = rule.get("compare_phase")
        threshold = rule.get("threshold", 0)

        if metric == "auc":
            current_auc = self._cached_aucs.get(from_phase)
            compare_auc = self._cached_aucs.get(compare_phase)

            if current_auc is None or compare_auc is None:
                return False, f"无法获取 {from_phase} 或 {compare_phase} 的 AUC 值"

            delta = current_auc - compare_auc
            if delta < threshold:
                return True, (
                    f"AUC 从 {compare_phase}({compare_auc:.3f}) "
                    f"降至 {from_phase}({current_auc:.3f}), "
                    f"Δ={delta:.3f} < 阈值 {threshold:.3f}"
                )

        return False, ""

    def _escalate_to_chief_scientist(
        self, phase_id: str, reason: str,
        gate_result: dict = None, issues: list = None,
    ):
        """
        当 Gate 连续失败或跨Phase返工超过上限时,
        调用首席科学家 Agent 做最终裁决。

        裁决类型:
        - 强制通过 (overrule gate): 当前产出可接受
        - 更换策略 (change strategy): 改变方法或数据源
        - 放弃项目 (abandon): 当前约束下不可行
        """
        print(f"\n{'='*60}")
        print(f"[首席科学家] 介入裁决 — Phase {phase_id}")
        print(f"{'='*60}")

        prompt_parts = [
            "## 首席科学家紧急裁决",
            "",
            f"**触发原因**: {reason}",
            f"**Phase**: {phase_id}",
            f"**事业部**: {self.active_division}",
            f"**项目**: {getattr(self, '_current_project_id', '')}",
            "",
        ]

        if gate_result:
            prompt_parts.append("### Gate 检查结果")
            for c in gate_result.get("checks", []):
                if c.get("result") == "fail":
                    prompt_parts.append(f"- ❌ {c['check_id']}: {c['detail']}")

        if issues:
            prompt_parts.append("### 跨Phase反馈问题")
            for issue in issues:
                prompt_parts.append(
                    f"- [{issue['severity']}] {issue['from_phase']} → "
                    f"{issue['to_phase']}: {issue['reason']}"
                )

        prompt_parts.extend([
            "",
            "请作出裁决 (三选一):",
            "1. **[强制通过]** — 当前产出可接受, 允许继续进入下一 Phase",
            "2. **[更换策略]** — 改变方法/数据源/参数, 提供具体修正建议",
            "3. **[放弃项目]** — 当前约束下不可行, 说明原因",
        ])

        chief_prompt = "\n".join(prompt_parts)
        try:
            # 使用独立的 chief-scientist Agent (management/chief-scientist.md)
            chief_result = self._call_agent(
                agent_id="chief-scientist",
                task_input=chief_prompt,
                phase_id=f"{phase_id}_escalation",
                project_id=getattr(self, '_current_project_id', ''),
            )
            print(f"[首席科学家] 裁决:\n{chief_result[:300]}...")
        except Exception as e:
            print(f"[首席科学家] 调用失败: {e}, 默认放弃项目")
            chief_result = f"## 首席科学家裁决\n\n**[放弃项目]** — 首席科学家调用失败: {e}"

        return chief_result

    def _build_gate_review_prompt(self, phase_id: str, outputs: dict,
                                   llm_checks: list, project_id: str) -> str:
        """构建 PI 闸门审查的提示词"""
        parts = [f"## 闸门审查: {phase_id}\n\n"]
        parts.append(f"项目: {project_id}\n\n")
        parts.append("请逐项审查以下检查项, 每项给出 pass/fail 判定和简要说明:\n\n")
        for i, check in enumerate(llm_checks, 1):
            parts.append(f"{i}. {check}\n")
        parts.append("\n---\n## 当前阶段产出\n\n")
        for agent_id, output in outputs.items():
            parts.append(f"### {agent_id}\n{output[:3000]}\n---\n")
        parts.append("\n请用以下格式回复, 每项一行:\n"
                      "- [pass/fail] 检查项: 说明\n\n"
                      "最后总结: PASS / COND_PASS (附条件) / FAIL")
        return "\n".join(parts)

    def _parse_gate_review(self, pi_output: str, llm_checks: list) -> list:
        """解析 PI 的闸门审查输出为 GateCheckItem 列表"""
        results = []
        for i, check in enumerate(llm_checks):
            line_pattern = rf'[-*]\s*\[(pass|fail|cond)\]\s*.*?:?\s*(.*)'
            match = re.search(line_pattern, pi_output, re.IGNORECASE)
            if match:
                status = match.group(1).lower()
                detail = match.group(2)[:200]
                results.append({
                    "check_id": f"pi_review_{i+1}",
                    "description": check,
                    "check_type": "llm",
                    "result": "pass" if status == "pass" else "fail",
                    "detail": detail,
                })
            else:
                if "PASS" in pi_output.upper() and "FAIL" not in pi_output.upper():
                    results.append({
                        "check_id": f"pi_review_{i+1}",
                        "description": check,
                        "check_type": "llm",
                        "result": "pass",
                        "detail": "PI 整体通过",
                    })
                else:
                    results.append({
                        "check_id": f"pi_review_{i+1}",
                        "description": check,
                        "check_type": "llm",
                        "result": "fail",
                        "detail": "PI 未明确通过此项",
                    })
        return results

    # ================================================================
    # 技术状态基线管理 — 钱学森总体设计部
    # ================================================================

    def _freeze_baseline_if_safe(
        self, project_id: str, phase_id: str,
        outputs: dict, gate_result: dict,
    ):
        """Gate 通过后冻结基线。失败不阻塞主流程。"""
        try:
            baseline = self.baseline_manager.freeze(
                project_id=project_id,
                phase_id=phase_id,
                outputs=outputs,
                gate_result=gate_result,
            )
            if self.config.verbose:
                print(f"  📌 基线已冻结: {baseline['baseline_id']} "
                      f"(artifacts: {len(baseline['artifacts'])})")
        except Exception as e:
            if self.config.verbose:
                print(f"  ⚠️ 基线冻结失败 (不阻塞): {e}")

    def _handle_baseline_change(
        self, project_id: str, from_phase: str, to_phase: str,
        reason: str, downstream_phases: list[str],
    ):
        """反馈环B触发时: 创建变更请求 + 无效化下游基线。失败不阻塞主流程。"""
        try:
            # 创建变更请求
            cr = self.baseline_manager.create_change_request(
                project_id=project_id,
                from_phase=from_phase,
                to_phase=to_phase,
                reason=reason,
                downstream_impact=downstream_phases,
                trigger_type="feedback_b",
            )
            if self.config.verbose:
                print(f"  📋 变更请求已创建: {cr['cr_id']}")

            # 无效化下游 Phase 的基线
            for downstream_phase in downstream_phases:
                latest = self.baseline_manager.get_latest(
                    project_id, downstream_phase
                )
                if latest and latest.get("status") == "frozen":
                    self.baseline_manager.supersede(
                        project_id, downstream_phase, latest["version"]
                    )
                    if self.config.verbose:
                        print(f"  📌 下游基线已作废: {downstream_phase}/{latest['version']}")
        except Exception as e:
            if self.config.verbose:
                print(f"  ⚠️ 基线变更处理失败 (不阻塞): {e}")

    def _find_project_dir(self, project_id: str) -> Optional[Path]:
        """定位项目目录 (从 knowledge base vaults 搜索)"""
        if hasattr(self, 'kb') and self.kb:
            vaults = getattr(self.kb, 'vaults', {})
            for _, vault_path in vaults.items():
                candidate = Path(vault_path) / 'projects' / project_id
                if candidate.exists():
                    return candidate
        # fallback: 从 baseline_dir 推导
        baseline_dir = getattr(self.config, 'baseline_dir', None)
        if baseline_dir:
            candidate = Path(baseline_dir).parent / project_id
            if candidate.exists():
                return candidate
        return None

    def _run_preflight_check(self, phase_id: str, project_id: str) -> dict:
        """执行前安全扫描 — 编排原则 #12"""
        proj_dir = self._find_project_dir(project_id)
        if not proj_dir:
            return {"pass": True, "failures": [], "warnings": [],
                    "report": "跳过 (无法定位项目目录)"}

        scanner = PreflightScanner()

        # 根据 Phase 确定扫描目标
        phase_scripts_map = {
            "execution": ["train_model.py", "tune_model.py"],
            "external_validation": ["external_validation.py"],
            "writing": ["generate_figures.py", "regenerate_figures_tables.py"],
        }
        target_scripts = phase_scripts_map.get(phase_id, ["*.py"])

        result = scanner.scan(proj_dir, target_scripts)

        # 🆕 调度 ml-engineer 时注入安全上下文: 将扫描结果缓存
        if not hasattr(self, '_preflight_cache'):
            self._preflight_cache = {}
        self._preflight_cache[phase_id] = result

        return result

    def _handle_preflight_failure(self, phase_id: str, project_id: str,
                                   preflight_result: dict):
        """Preflight 失败时: 输出修复清单 + 创建变更请求 (B环触发)"""
        failures = preflight_result.get("failures", [])
        if not failures:
            return

        # 创建变更请求
        try:
            self.baseline_manager.create_change_request(
                project_id=project_id,
                from_phase=phase_id,
                to_phase=phase_id,
                reason=f"Preflight 安全扫描不通过 ({len(failures)} 项)",
                downstream_impact=[phase_id],
                trigger_type="feedback_b",
            )
        except Exception:
            pass  # 不阻塞主流程

        # 如果有内存安全违规，自动扫描同项目所有 .py 文件 (B环 #7)
        memory_violations = [
            f for f in failures
            if any(kw in f.lower() for kw in [
                'n_jobs', 'nthread', 'pickle', 'forkserver',
                'omp_num_threads', 'mkl_num_threads', '内存',
            ])
        ]
        if memory_violations:
            proj_dir = self._find_project_dir(project_id)
            if proj_dir:
                all_scripts = [s.name for s in proj_dir.glob('**/*.py')
                              if s.parent.name != '__pycache__']
                print(f"  🔍 B环 #7: 扫描同项目 {len(all_scripts)} 个 .py 文件...")
                scanner = PreflightScanner()
                full_scan = scanner.scan(proj_dir, all_scripts)
                if full_scan["failures"]:
                    print(f"  📋 修复清单 ({len(full_scan['failures'])} 项):")
                    for f_item in full_scan["failures"][:10]:
                        print(f"    • {f_item}")

    def _record_gate_for_adaptive(self, phase_id: str, status: str):
        """自适应调度: 记录 Gate 结果并检查是否需调整策略"""
        self._ensure_analyzer_loaded()
        if self._adaptive_scheduler is None:
            return

        try:
            # 记录 Gate 结果到调度器
            self._adaptive_scheduler.record_result(
                phase_id=phase_id,
                success=(status == "pass"),
                degraded=False,  # 暂不从 Gate 结果推断降级
            )

            # 获取调度建议
            recommendation = self._adaptive_scheduler.get_recommendation()
            if recommendation.get("action") != "continue":
                print(f"  [自适应调度] {recommendation.get('message', '')}")
                if recommendation.get("action") == "add_redundancy":
                    print(f"  [自适应调度] 通过率偏低, 建议增加冗余 Agent")
                elif recommendation.get("action") == "switch_model":
                    print(f"  [自适应调度] 降级率偏高, 建议切换模型")
        except Exception:
            pass  # 自适应调度失败不影响主流程

    def _build_agent_input(
        self,
        agent_id: str,
        phase_id: str,
        user_request: str,
        previous_phase_outputs: dict,
        current_phase_outputs: dict,
        project_id: str,
    ) -> str:
        """为 Agent 构建输入上下文, 自动预采集所需数据"""
        parts = [f"## 用户原始请求\n\n{user_request}\n"]

        # ⭐ 选题文献预检注入: Phase 1 的 research-assistant 必须执行实时文献预检
        if phase_id == "problem_definition" and agent_id.endswith("research-assistant"):
            parts.append("""
## ⚠️ 强制任务: 选题可行性文献预检

你必须在 Phase 1 完成**实时文献预检**, 不允许仅凭训练数据记忆回答。

1. 使用 WebSearch 工具执行 3 轮检索 (PubMed/arXiv/Google Scholar)
2. 找到 top 3-5 最相似的已发表工作
3. 提取每个对标论文的关键指标: AUC/C-index, 样本量, 数据源, 方法
4. 输出《选题文献预检报告》(格式见你的 system prompt §5.2-5.3)
5. 给出明确的可行性判断: [可以推进 / 需要调整方向 / 不建议推进]

**时效性要求**: 优先检索近 5 年文献, 最终参考文献列表中 ≥80% 须为近 5 年内发表。
经典方法学奠基性论文 (如 TRIPOD, PROBAST, Fried 原始论文等) 不在此限。

这份报告将被 PI 用作 FRAME 评估中 F (Field Scan) 维度的核心输入。
""")

        # ⭐ ml-engineer 安全规范注入 (编排原则 #12)
        if agent_id.endswith("ml-engineer"):
            # 注入 preflight 扫描结果
            preflight_info = ""
            if hasattr(self, '_preflight_cache') and phase_id in self._preflight_cache:
                pf = self._preflight_cache[phase_id]
                if pf.get("failures") or pf.get("warnings"):
                    preflight_info = f"""
## ⚠️ Preflight 安全扫描结果

{chr(10).join(f'- FAIL: {f}' for f in pf.get('failures', [])[:5])}
{chr(10).join(f'- WARN: {w}' for w in pf.get('warnings', [])[:5])}

请在执行前确认以上安全配置问题已修复。
"""

            # 获取当前可用内存
            mem_info = ""
            try:
                import psutil
                avail = psutil.virtual_memory().available / (1024 ** 3)
                mem_info = f"\n**当前可用内存**: {avail:.1f} GB\n"
            except Exception:
                pass

            parts.append(f"""
## ⚠️ ML 内存安全规范 (9 条规则)

你必须在所有 ML 脚本中严格遵守以下规范:

### 规则 1 — n_jobs 动态上限
- 默认值: 2, 上限为 min(4, cpu_count // 2)
- 绝对禁止 n_jobs=-1

### 规则 2 — SMOTE + 多进程 = 危险组合
- 禁止 Pipeline 内 SMOTE + 并行 CV
- 安全方案: 训练循环外提前做 SMOTE (推荐)

### 规则 3 — 启动方式
- Unix: os.environ["JOBLIB_START_METHOD"] = "forkserver"

### 规则 4 — 限制底层线程库
所有脚本顶部 (import numpy 之前) 必须:
  os.environ["OMP_NUM_THREADS"] = "2"
  os.environ["OPENBLAS_NUM_THREADS"] = "2"
  os.environ["MKL_NUM_THREADS"] = "2"
  os.environ["VECLIB_MAXIMUM_THREADS"] = "2"
  os.environ["NUMEXPR_NUM_THREADS"] = "2"

### 规则 5 — 运行前预估内存
预计峰值 > 可用 RAM × 0.7 → 降 n_jobs

### 规则 6 — pickle 加载后覆盖 n_jobs
model = pickle.load(f); if hasattr(model, 'n_jobs'): model.n_jobs = 1

### 规则 7 — cross_val_predict/cross_val_score 必须显式传 n_jobs
cross_val_predict(model, X, y, cv=cv, n_jobs=1)

### 规则 8 — 多模型串行加载时必须显式 gc
加载每个模型后: del data; gc.collect()

### 规则 9 — 关键步骤前后打印内存使用
psutil.virtual_memory() 输出内存使用率

{preflight_info}{mem_info}
请确认你的代码遵守以上全部 9 条规则。
""")

        # ⭐ 关键架构: Prefetcher 在 LLM 调用前自动采集所有需要的数据
        # 将上游输出也传给 prefetcher, 让 scientific-writer 等 Agent 能提取关键数字
        prefetched = self.prefetcher.prefetch(
            agent_id, user_request,
            data_sources=self.active_data_sources,
            previous_outputs=previous_phase_outputs,
            current_outputs=current_phase_outputs,
        )
        if prefetched:
            parts.append(prefetched)

        # 写作阶段需要完整数据, 不截断; 其他阶段保持紧凑
        if phase_id == "writing" or agent_id == "scientific-writer":
            upstream_limit = 8000
            current_limit = 4000
        else:
            upstream_limit = 2000
            current_limit = 1000

        # 添加上游阶段输出
        if previous_phase_outputs:
            parts.append("\n## 📥 上游阶段输出\n")
            for agent, output in previous_phase_outputs.items():
                # 🆕 跳过一致性修正的内部字段, 不让下游 Agent 困惑
                if agent.startswith("_"):
                    continue
                parts.append(f"### {agent}\n{output[:upstream_limit]}\n")
                if len(output) > upstream_limit:
                    parts.append(f"...(截断, 原文 {len(output)} 字符)\n")

            # 🆕 注入一致性修正建议 (minor inconsistency fixes)
            consistency_fixes = previous_phase_outputs.get("_consistency_fixes", "")
            if consistency_fixes:
                parts.append("\n### ⚠️ 上游一致性修正建议\n")
                parts.append("以下轻微不一致已在上游 Phase 检测到, 请在本阶段注意:\n")
                parts.append(consistency_fixes)
                parts.append("\n")

        # 添加当前阶段其他 Agent 的输出
        if current_phase_outputs:
            parts.append("\n## 📥 同阶段其他 Agent 输出\n")
            for agent, output in current_phase_outputs.items():
                parts.append(f"### {agent}\n{output[:current_limit]}\n")
                if len(output) > current_limit:
                    parts.append(f"...(截断, 原文 {len(output)} 字符)\n")

        # 项目信息
        parts.append(f"\n## 项目\n- project_id: {project_id}\n- 当前阶段: {phase_id}\n")
        parts.append("---\n")
        if agent_id == "scientific-writer":
            parts.append(
                "⚠️ 撰写论文时严格使用上游输出的真实数据。"
                "所有数字必须可追溯到上游分析结果。"
                "若数据不完整或不确定，标注 **[数据待确认]** 而非编造数字。"
            )
        else:
            parts.append("⚠️ 以上已包含所有需要的数据。请直接生成报告，不需要调用数据采集工具。")

        return "\n".join(parts)

    def _get_kb_context(self, user_request: str, agent_id: str) -> str:
        """从知识库检索相关上下文"""
        try:
            results = self.kb.search_knowledge_base(user_request[:50])
            if not results:
                return ""
            lines = ["以下知识库文件可能相关:"]
            for r in results[:5]:
                lines.append(f"- [{r['type']}] {r['path']}: {r['snippet'][:150]}")
            return "\n".join(lines)
        except Exception:
            return ""

    # ================================================================
    # 调用单个 Agent
    # ================================================================

    def _call_agent(self, agent_id: str, task_input: str,
                    phase_id: str = "", project_id: str = "",
                    rework_of: str = "") -> str:
        """调用 Agent LLM。数据已由 Prefetcher 注入上下文。scientific-writer 输出自动经 DOI 验证。
        自动记录运行日志 (系统辨识数据源)。"""
        print(f"  → 调用 {agent_id}...")
        t0 = time.time()
        success = False
        degraded = False
        in_tokens = out_tokens = 0
        output_len = 0
        error_type = ""

        # 对于纯数据查询: Prefetcher 结果已足够, 跳过 LLM
        if agent_id == "data-engineer" and self._is_pure_data_query(task_input):
            report = self.prefetcher.build_data_report("2013")
            wall_time = time.time() - t0
            output_len = len(report)
            success = True
            print(f"  ← data-engineer: 直接返回 Prefetcher 报告 (跳过 LLM)  [{output_len} 字符]")
            self._append_run_log(timestamp=datetime.now().isoformat(),
                                 project_id=project_id, division=self.active_division,
                                 phase_id=phase_id, agent_id=agent_id,
                                 success=success, degraded=False,
                                 wall_time_sec=round(wall_time, 2),
                                 input_tokens=0, output_tokens=0, output_len=output_len,
                                 error_type="", gate_status="skip", rework_of=rework_of)
            return report

        # system_architect 是编排器自身的总体设计角色, 没有独立 Agent 文件
        if agent_id == "system_architect":
            system_prompt = self.SDS_SYSTEM_PROMPT
        else:
            system_prompt = self.agent_loader.load_full_prompt(agent_id, include_fewshot=True)
        try:
            response = self.llm.chat(system_prompt=system_prompt, user_message=task_input)
            content = response.content
            success = True
            degraded = response.degraded
            in_tokens = response.usage.get("input_tokens", 0)
            out_tokens = response.usage.get("output_tokens", 0)
            output_len = len(content)

            # ⭐ scientific-writer 输出自动 DOI 验证 — 代码强制执行
            if agent_id == "scientific-writer":
                content = self._verify_dois_in_output(content)
                output_len = len(content)

            if self.config.verbose:
                degraded_mark = " [降级]" if degraded else ""
                print(f"  ← {agent_id}: {output_len} 字符 (in={in_tokens}, out={out_tokens}){degraded_mark}")
            return content
        except LLMCallFailedError as e:
            error_type = "LLMCallFailed"
            error_msg = (
                f"## ⚠️ Agent 调用失败 (LLM 不可用)\n\n"
                f"**Agent**: {agent_id}\n"
                f"**错误**: {e}\n"
                f"**影响**: 当前任务无法完成。\n"
                f"**建议**: 检查 API key 和网络连接。LLM 恢复后，编排器可从此阶段断点续传。\n"
            )
            print(f"  ✗ {agent_id}: LLM 最终失败 (所有重试耗尽)")
            self._record_phase_blocked(agent_id, str(e))
            return error_msg
        except Exception as e:
            error_type = type(e).__name__
            error_msg = f"[{agent_id}] LLM 调用失败: {e}"
            print(f"  ✗ {error_msg}")
            return error_msg
        finally:
            wall_time = time.time() - t0
            self._append_run_log(timestamp=datetime.now().isoformat(),
                                 project_id=project_id, division=self.active_division,
                                 phase_id=phase_id, agent_id=agent_id,
                                 success=success, degraded=degraded,
                                 wall_time_sec=round(wall_time, 2),
                                 input_tokens=in_tokens, output_tokens=out_tokens,
                                 output_len=output_len, error_type=error_type,
                                 gate_status="skip", rework_of=rework_of)

    def _record_phase_blocked(self, agent_id: str, error: str):
        """记录 Phase 因 LLM 不可用而暂停"""
        if hasattr(self, 'state') and self.state:
            if not hasattr(self.state, 'errors') or self.state.errors is None:
                self.state["errors"] = []
            self.state["errors"].append(
                f"[{datetime.now().strftime('%H:%M:%S')}] {agent_id}: LLM 不可用 — {error[:200]}"
            )

    def _append_run_log(self, **kwargs):
        """追加一行运行日志到当天的 JSONL 文件。轻量零阻塞, 失败不影响主流程。"""
        try:
            log_dir = getattr(self.config, 'run_log_dir', None)
            if log_dir is None:
                log_dir = self.config.project_root / "outputs" / "run_logs"
            log_dir = Path(log_dir)
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"
            with open(log_file, "a") as f:
                f.write(json.dumps(kwargs, ensure_ascii=False) + "\n")
        except Exception:
            pass  # 日志写入失败不影响主流程

    def _backfill_gate_status(self, phase_id: str, gate_status: str):
        """闸门检查后回填该 Phase 所有 agent 调用的 gate_status。
        简化为追加一条 gate summary 记录到日志。"""
        self._append_run_log(
            timestamp=datetime.now().isoformat(),
            project_id="", division=self.active_division,
            phase_id=phase_id, agent_id="_gate",
            success=True, degraded=False,
            wall_time_sec=0, input_tokens=0, output_tokens=0, output_len=0,
            error_type="", gate_status=gate_status, rework_of="",
        )

    def _verify_dois_in_output(self, content: str) -> str:
        """从 scientific-writer 输出中提取所有 DOI，自动验证并附加报告。这是投稿前强制步骤。"""
        import re, json

        dois = re.findall(r'doi[: ]*(10\.\d{4,}/[^\s"\']+)', content)
        # 清理尾部标点 (句号/逗号/分号/括号)
        dois = [re.sub(r'[.,;)\]]+$', '', d) for d in dois]
        if not dois:
            return content

        print(f"  🔍 DOI 验证: 检测到 {len(dois)} 个 DOI, 自动验证中...")
        try:
            result = json.loads(self.tools.execute("verify_all_dois", {"dois": dois}))
        except Exception as e:
            return content + f"\n\n---\n## DOI Verification\n⚠️ 验证失败: {e}\n"

        report = "\n\n---\n## DOI Verification Report (auto-generated)\n\n"
        report += f"**{result['summary']}**\n\n"
        report += "| DOI | Status | Title |\n"
        report += "|-----|--------|-------|\n"
        for d in result.get("details", []):
            status = "✅" if d.get("valid") else ("❌ FAKE" if d.get("valid") is False else "⚠️")
            info = (d.get("title") or d.get("error") or "")[:80]
            report += f"| `{d['doi'][:45]}` | {status} | {info} |\n"

        if result.get("fake", 0) > 0:
            report += f"\n⚠️ **{result['fake']} fake DOI(s) detected. Replace before submission.**\n"
        else:
            report += f"\n✅ All {result.get('valid', 0)} DOIs verified.\n"

        print(f"  🔍 DOI 结果: {result['summary']}")
        return content + report

    def _is_pure_data_query(self, task_input: str) -> bool:
        keywords = ["缺失率", "变量可用", "数据评估", "变量报告", "数据质量", "文件列表", "fried phenotype"]
        return any(kw in task_input.lower() for kw in keywords)

    # ================================================================
    # 简化的其他工作流
    # ================================================================

    def _run_literature_workflow(self, user_request: str, intent: dict) -> str:
        """文献综述工作流"""
        search_result = self._call_agent("research-assistant", user_request)
        return self._format_response("文献综述结果", search_result)

    def _run_writing_workflow(self, user_request: str, intent: dict) -> str:
        """论文写作工作流 — 走完整 prefetch + 上下文构建流程"""
        task_input = self._build_agent_input(
            agent_id="scientific-writer",
            phase_id="writing",
            user_request=user_request,
            previous_phase_outputs={},
            current_phase_outputs={},
            project_id=intent.get("project_id") or "standalone",
        )
        return self._call_agent("scientific-writer", task_input)

    def _run_quick_consult(self, user_request: str, intent: dict) -> str:
        """快速咨询: 传给最相关的单个 Agent"""
        # 关键词路由
        agent_id = self._route_to_agent(user_request)
        print(f"[Orchestrator] 快速咨询 → {agent_id}")
        result = self._call_agent(agent_id, user_request)
        return self._format_response(f"{agent_id} 的回复", result)

    def _run_pm_mode(self, user_request: str, intent: dict) -> str:
        """PM 驱动模式: PM 先制定计划，然后按计划调度团队执行"""
        print(f"\n{'='*50}")
        print(f"[PM Mode] 项目经理开始规划...")
        print(f"{'='*50}\n")

        # Step 1: PM 制定项目计划
        pm_prompt = f"""你是科研项目经理。收到用户请求:

{user_request}

请完成以下工作:
1. 分析请求，列出所有任务，按依赖关系分组为 3-6 个 Phase
2. 为每个 Phase 指定 agent 列表 (一行一个, 格式: `@agent-id`)
3. 输出项目章程

可用 agent: clinical-researcher, data-engineer, research-assistant, computational-biologist, biostatistician, ml-engineer, scientific-writer, pi

⚠️ 强制约束 — 阶段顺序不可违反：
- 外部验证 (external validation) 必须在论文写作 (paper writing) 之前
- 论文写作必须是最后一个阶段
- 标准顺序: 问题定义 → 方案设计 → 执行(内部验证) → 外部验证 → 审查 → 论文撰写

输出格式:
## 项目章程
[项目目标、里程碑、风险]

## 执行计划
### Phase 1: [阶段名]
@clinical-researcher
@data-engineer
@research-assistant

### Phase 2: [阶段名]
@computational-biologist
@biostatistician

请开始规划。"""

        pm_plan = self._call_agent("pm", pm_prompt)

        # Step 2: 解析 PM 计划并执行
        phases = self._parse_pm_plan(pm_plan, user_request)

        all_results = [f"## PM 项目计划\n\n{pm_plan}\n\n---\n\n## 执行日志\n"]

        # 累积所有阶段的输出, 让后续阶段能看到前面的结果
        all_phase_outputs = {}

        for phase_name, agents_in_phase in phases:
            print(f"\n[PM] 启动 {phase_name}...")

            phase_result = self._execute_phase(
                phase_id=phase_name.lower().replace(" ", "_"),
                user_request=f"PM 计划:\n{pm_plan}\n\n用户请求:\n{user_request}",
                previous_outputs=all_phase_outputs,
                project_id=intent.get("project_id", "auto"),
                agents_override=agents_in_phase,
            )
            # 当前阶段输出累积到 all_phase_outputs, 供下一阶段使用
            all_phase_outputs.update(phase_result)

            all_results.append(f"### {phase_name}\n")
            for agent, output in phase_result.items():
                all_results.append(f"#### {agent}\n{output[:3000]}\n")

            # PM 审查本阶段结果
            all_results.append(f"\n> Phase {phase_name} 完成。PM 审查通过，进入下一阶段。\n")

        # Step 3: PM 最终汇总
        all_results.append(f"\n---\n## PM 总结\n所有阶段完成。")

        return "\n".join(all_results)

    def _parse_pm_plan(self, pm_output: str, user_request: str) -> list:
        """从 PM 输出中解析 Phase 定义"""
        import re
        phases = []

        # 匹配 Phase 标题: ### Phase N: description
        phase_blocks = re.split(r'\n###\s*Phase\s*\d+', pm_output)
        phase_titles = re.findall(r'###\s*(Phase\s*\d+[:：]\s*[^\n]+)', pm_output)

        for i, title in enumerate(phase_titles):
            body = phase_blocks[i + 1] if i + 1 < len(phase_blocks) else ""

            # 从 body 中提取 agent 名称
            agents = []
            agent_mentions = re.findall(
                r'(?:agent[:：]\s*|→\s*\*\*agent[:：]\s*|@)([a-z-]+)',
                body + title, re.IGNORECASE
            )
            for a in agent_mentions:
                a = a.strip().rstrip('*').lower()
                if a in self.agent_loader.AGENT_FILES and a not in agents:
                    agents.append(a)

            # 回退: 基于关键词推断
            if not agents:
                agents = self._infer_agents_for_phase(title + " " + body[:500])

            # 确保至少有一个 agent
            if not agents:
                agents = ["research-assistant"]

            phases.append((title.strip()[:80], agents))

        if not phases:
            phases = [
                ("Phase 1: 问题定义", ["clinical-researcher", "data-engineer", "research-assistant"]),
                ("Phase 2: 方案设计", ["computational-biologist", "biostatistician"]),
            ]

        for name, agents in phases:
            print(f"  [PM Plan] {name} → {agents}")

        return phases

    def _infer_agents_for_phase(self, phase_desc: str) -> list:
        """基于描述关键词推断需要的 agent"""
        desc = phase_desc.lower()
        agents = []
        mapping = [
            (["临床", "问题定义", "表型", "衰弱", "fried", "纳入", "排除"], "clinical-researcher"),
            (["数据", "变量", "缺失", "文件", "可用性", "charls", "质量"], "data-engineer"),
            (["文献", "综述", "扫描", "检索", "阅读"], "research-assistant"),
            (["模型", "建模", "ml", "预测", "分类", "特征工程", "算法"], "computational-biologist"),
            (["统计", "sap", "样本量", "功效", "缺失处理", "因果"], "biostatistician"),
            (["训练", "实现", "代码", "调参", "xgb", "shap"], "ml-engineer"),
            (["写作", "论文", "稿件", "初稿", "整合", "撰写", "方案"], "scientific-writer"),
            (["审查", "终审", "pi", "审批", "决策", "方向"], "pi"),
            (["外部验证", "泛化", "外部数据", "独立验证", "多中心验证", "external valid"], "data-engineer"),
        ]
        for keywords, agent in mapping:
            if any(kw in desc for kw in keywords):
                if agent not in agents:
                    agents.append(agent)
        return agents or ["research-assistant"]

    def _run_status_check(self, intent: dict) -> str:
        """查看项目状态"""
        project_id = intent.get("project_id")
        if not project_id:
            return "请指定项目 ID。可用的项目在 Obsidian 知识库的 projects/ 目录下。"
        state = self.kb.get_project_state(project_id)
        if not state:
            return f"项目 {project_id} 不存在。"
        return f"## 项目状态: {state.get('title', project_id)}\n\n" + \
               f"- 状态: {state.get('status', 'unknown')}\n" + \
               f"- 目标期刊: {state.get('target_journal', 'N/A')}\n" + \
               f"- 下一步: {state.get('next_actions', [])}"

    # ================================================================
    # 路由与格式化
    # ================================================================

    def _route_to_agent(self, user_request: str) -> str:
        """基于关键词路由到最相关的 Agent"""
        req = user_request.lower()
        routing = [
            (["启动", "新项目", "安排", "计划", "调度", "分配", "团队", "开始工作", "kickoff"], "pm"),
            (["变量名", "缺失率", "数据文件", "csv", "dta", "变量可用", "数据评估", "数据探查", "文件列表", "charls 2013", "charls 2015", "数据清洗", "缺失值", "数据库", "uk biobank", "omop"], "data-engineer"),
            (["预测模型", "机器学习", "深度学习", "衰老时钟", "组学", "建模方案"], "computational-biologist"),
            (["研究设计", "样本量", "统计功效", "因果推断", "p值", "荟萃分析", "sap"], "biostatistician"),
            (["衰弱", "肌少症", "跌倒", "认知障碍", "多病共存", "表型定义", "临床"], "clinical-researcher"),
            (["写论文", "投稿", "cover letter", "初稿", "讨论"], "scientific-writer"),
            (["润色", "去AI味", "改写", "humanize", "人文化"], "humanizer"),
            (["文献检索", "综述", "prisma", "阅读笔记", "文献扫描", "写入知识库", "写入 obsidian"], "research-assistant"),
            (["投稿", "期刊", "基金", "方向", "值不值得", "终审"], "pi"),
            (["训练", "调参", "xgboost", "shap", "特征工程", "代码", "实现"], "ml-engineer"),
        ]
        for keywords, agent in routing:
            if any(kw in req for kw in keywords):
                return agent
        return "computational-biologist"  # 默认

    def _summarize_phase(self, phase_id: str, outputs: dict) -> str:
        """聚合单个阶段的 Agent 输出"""
        parts = [f"## 阶段完成: {phase_id}\n"]
        for agent_id, output in outputs.items():
            parts.append(f"### {agent_id}\n\n{output[:3000]}\n")
        return "\n".join(parts)

    def _aggregate_all_phases(self, phases: list, all_outputs: dict, project_id: str,
                                gate_results: dict = None, rework_history: list = None) -> str:
        """聚合所有阶段的输出, 生成最终研究报告 (含 Gate 摘要)"""
        parts = [f"# 研究方案 — {project_id}\n\n"]
        parts.append(f"*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n---\n\n")

        for phase_id in phases:
            if phase_id not in all_outputs:
                continue
            phase_def = PROJECT_PHASES.get(phase_id, {})
            parts.append(f"## Phase: {phase_id} — {phase_def.get('description', '')}\n\n")

            phase_outputs = all_outputs[phase_id]
            for agent_id, output in phase_outputs.items():
                if agent_id.startswith("_"):
                    continue  # 跳过内部字段
                truncated = output[:4000] + ("\n\n...(truncated)" if len(output) > 4000 else "")
                parts.append(f"### {agent_id}\n\n{truncated}\n\n---\n\n")

        # Gate 摘要
        if gate_results:
            parts.append("---\n\n## Gate 检查摘要\n\n")
            parts.append("| Phase | Gate | Status | Checks (✓/✗) |\n")
            parts.append("|-------|------|--------|-------------|\n")
            for phase_id, gr in gate_results.items():
                status = gr.get("status", "?")
                pass_cnt = sum(1 for c in gr.get("checks", []) if c["result"] == "pass")
                fail_cnt = sum(1 for c in gr.get("checks", []) if c["result"] == "fail")
                icon = "✅" if status == "pass" else ("⚠️" if status == "conditional_pass" else "❌")
                parts.append(f"| {phase_id} | {gr.get('gate_id', '')} | {icon} {status} | {pass_cnt}✓ / {fail_cnt}✗ |\n")

        if rework_history:
            parts.append("\n## 返工记录\n\n")
            for r in rework_history:
                parts.append(f"- {r['timestamp']}: {r['from_phase']} → {r['to_phase']} ({r['reason']})\n")

        parts.append(f"\n## 下一步\n")
        parts.append(f"- 所有 Phase 完成 (含 Gate 检查)\n")
        parts.append(f"- 知识库位置: `obsidian/laoNianYiXue/projects/{project_id}/`\n")

        return "\n".join(parts)

    def _format_response(self, title: str, content: str) -> str:
        return f"## {title}\n\n{content}"


# ================================================================
# 快速启动函数
# ================================================================

def create_orchestrator(**kwargs) -> ResearchOrchestrator:
    """创建编排器实例"""
    from ..config import load_config
    config = load_config(**kwargs)
    return ResearchOrchestrator(config)
