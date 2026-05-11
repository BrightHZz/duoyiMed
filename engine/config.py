"""引擎配置管理"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


# ================================================================
# 数据源配置 — 公司级资产, 不绑定到任何事业部
# ================================================================

@dataclass
class DataSourceConfig:
    """公司级数据源注册项。数据源是公司资产, 所有事业部均可使用。"""
    name: str                              # "CHARLS"
    path: Path                             # 数据目录
    category: str                          # "cohort" | "ehr" | "registry" | "claims"
    description: str                       # 一句话简介
    supported_tools: list = field(default_factory=list)     # 可用的工具函数名列表
    prefetcher_key: str = ""               # DataPrefetcher 中对应的方法名后缀

    def __hash__(self):
        return hash(self.name)


# 默认数据源注册表 — 公司级共享
DEFAULT_DATA_SOURCES: dict[str, DataSourceConfig] = {
    "CHARLS": DataSourceConfig(
        name="CHARLS",
        path=Path("/Users/wuyouhang/Documents/trae_projects/related to Sarcopenia/charls"),
        category="cohort",
        description="中国健康与养老追踪调查 (China Health and Retirement Longitudinal Study), ≥45 岁",
        supported_tools=[
            "list_datasource_files", "read_datasource_headers",
            "read_datasource_sample", "search_datasource_variable",
            "get_variable_distribution",
            "generate_frailty_variable_report",
        ],
        prefetcher_key="cohort",
    ),
    "CLHLS": DataSourceConfig(
        name="CLHLS",
        path=Path(""),  # 待配置
        category="cohort",
        description="中国老年健康影响因素跟踪调查 (Chinese Longitudinal Healthy Longevity Survey), ≥65 岁",
        supported_tools=["list_datasource_files", "read_datasource_headers"],
        prefetcher_key="cohort",
    ),
    "HRS": DataSourceConfig(
        name="HRS",
        path=Path(""),  # 待配置
        category="cohort",
        description="美国健康与退休研究 (Health and Retirement Study), ≥50 岁",
        supported_tools=["list_datasource_files", "read_datasource_headers"],
        prefetcher_key="cohort",
    ),
    "ELSA": DataSourceConfig(
        name="ELSA",
        path=Path(""),  # 待配置
        category="cohort",
        description="英国老龄化纵向研究 (English Longitudinal Study of Ageing), ≥50 岁",
        supported_tools=["list_datasource_files", "read_datasource_headers"],
        prefetcher_key="cohort",
    ),
    "UK_BIOBANK": DataSourceConfig(
        name="UK_BIOBANK",
        path=Path(""),  # 待配置
        category="cohort",
        description="英国生物银行 (UK Biobank), 40-69 岁, 含基因+影像+EHR 链接",
        supported_tools=["list_datasource_files", "read_datasource_headers"],
        prefetcher_key="cohort",
    ),
    "NHANES": DataSourceConfig(
        name="NHANES",
        path=Path(""),  # 待配置
        category="cohort",
        description="美国国家健康与营养调查 (National Health and Nutrition Examination Survey)",
        supported_tools=["list_datasource_files", "read_datasource_headers"],
        prefetcher_key="cohort",
    ),
    "MIMIC-IV": DataSourceConfig(
        name="MIMIC-IV",
        path=Path(""),  # 通过环境变量 MIMIC_DATA_DIR 配置
        category="ehr",
        description="ICU 电子健康记录数据库 (Medical Information Mart for Intensive Care IV), 含诊断/药物/实验室/微生物",
        supported_tools=[
            "list_datasource_files", "read_datasource_headers",
            "read_datasource_sample", "search_datasource_variable",
        ],
        prefetcher_key="ehr",
    ),
    "SEER": DataSourceConfig(
        name="SEER",
        path=Path(""),  # 通过环境变量 SEER_DATA_DIR 配置
        category="registry",
        description="美国癌症统计数据库 (Surveillance, Epidemiology, and End Results), 含诊断/治疗/生存数据",
        supported_tools=["list_datasource_files", "read_datasource_headers"],
        prefetcher_key="registry",
    ),
}

# 事业部常用数据源 (仅作为默认推荐, 不限制使用)
DIVISION_DEFAULT_SOURCES: dict[str, list[str]] = {
    "geriatrics": ["CHARLS", "CLHLS", "HRS", "ELSA", "UK_BIOBANK", "NHANES"],
    "urology": ["MIMIC-IV", "SEER", "NHANES"],
}


@dataclass
class EngineConfig:
    """Agent 编排引擎的全局配置 — 支持公司模式多事业部"""

    # --- 路径 ---
    project_root: Path = field(default_factory=lambda: Path(__file__).parent.parent)
    agents_dir: Path = field(default=None)  # Legacy agents/ dir
    company_dir: Path = field(default=None)  # NEW: company/ dir

    # --- 公司模式 ---
    active_divisions: list = field(default_factory=lambda: ["geriatrics", "urology"])

    # --- 多知识库 ---
    obsidian_vault: Path = field(
        default_factory=lambda: Path(
            "/Users/wuyouhang/Documents/trae_projects/obsidian/laoNianYiXue"
        )
    )
    # 各事业部的知识库路径
    obsidian_vaults: dict = field(default_factory=lambda: {
        "geriatrics": Path("/Users/wuyouhang/Documents/trae_projects/obsidian/laoNianYiXue/"),
        "urology": Path("/Users/wuyouhang/Documents/trae_projects/obsidian/miNiaoWaiKe/"),
    })

    # --- 多数据源 (公司级资产, 所有事业部均可使用) ---
    data_sources: dict = field(default_factory=lambda: dict(DEFAULT_DATA_SOURCES))

    # 事业部常用数据源 (仅默认推荐, 不限制实际使用)
    division_default_sources: dict = field(default_factory=lambda: dict(DIVISION_DEFAULT_SOURCES))

    # --- LLM ---
    llm_provider: str = "anthropic"  # anthropic | openai | deepseek
    llm_model: str = "claude-sonnet-4-6"
    llm_max_tokens: int = 8192
    llm_temperature: float = 0.1

    # --- LLM 容错 ---
    llm_fallback_model: str = "claude-haiku-4-5-20251001"
    llm_max_retries: int = 3           # 最大重试次数 (不含首次)
    llm_retry_base_delay: float = 1.0  # 退避基础延迟 (秒)
    llm_retry_max_delay: float = 8.0   # 退避最大延迟 (秒)
    llm_request_timeout: int = 300     # 单次请求超时 (秒)

    # --- 编排 ---
    max_parallel_agents: int = 3
    default_timeout_seconds: int = 300
    verbose: bool = True

    # --- 运行日志 ---
    run_log_dir: Path = field(default=None)  # 运行日志目录, None=自动设为 outputs/run_logs/

    # --- 共享服务 ---
    shared_services_pool_size: int = 1  # 每个共享服务同时服务的事业部数

    # --- 向后兼容属性 ---
    @property
    def charls_data_dir(self) -> Path:
        """向后兼容: 返回 CHARLS 数据源路径"""
        if "CHARLS" in self.data_sources:
            return self.data_sources["CHARLS"].path
        return self.project_root

    @property
    def data_dirs(self) -> dict:
        """向后兼容: 返回 {division: primary_datasource_path} 映射。
        新代码应使用 data_sources 和 division_default_sources。"""
        result = {}
        for div in self.active_divisions:
            defaults = self.division_default_sources.get(div, [])
            if defaults:
                ds_name = defaults[0]
                if ds_name in self.data_sources:
                    result[div] = self.data_sources[ds_name].path
                    continue
            result[div] = self.project_root
        return result

    def get_datasource(self, name: str) -> Optional[DataSourceConfig]:
        """按名称获取数据源配置"""
        return self.data_sources.get(name)

    def get_available_sources(self, division: str = None) -> list[str]:
        """获取可用数据源列表。如果指定事业部, 将其默认源排在前面。"""
        all_sources = list(self.data_sources.keys())
        if division:
            defaults = self.division_default_sources.get(division, [])
            # 将默认源排到前面
            ordered = [s for s in defaults if s in self.data_sources]
            ordered += [s for s in all_sources if s not in ordered]
            return ordered
        return all_sources

    def __post_init__(self):
        if self.agents_dir is None:
            self.agents_dir = self.project_root / "agents"
        if self.company_dir is None:
            self.company_dir = self.project_root / "company"


def load_config(**overrides) -> EngineConfig:
    """加载配置, 支持环境变量覆盖"""
    config = EngineConfig()

    # 环境变量覆盖
    if os.getenv("LLM_PROVIDER"):
        config.llm_provider = os.getenv("LLM_PROVIDER")
    if os.getenv("LLM_MODEL"):
        config.llm_model = os.getenv("LLM_MODEL")
    if os.getenv("OBSIDIAN_VAULT"):
        config.obsidian_vault = Path(os.getenv("OBSIDIAN_VAULT"))
    if os.getenv("ANTHROPIC_API_KEY"):
        config.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

    # 公司模式环境变量 — 知识库
    if os.getenv("GERIATRICS_VAULT"):
        config.obsidian_vaults["geriatrics"] = Path(os.getenv("GERIATRICS_VAULT"))
    if os.getenv("UROLOGY_VAULT"):
        config.obsidian_vaults["urology"] = Path(os.getenv("UROLOGY_VAULT"))

    # 公司模式环境变量 — 数据源 (公司级资产)
    if os.getenv("CHARLS_DATA_DIR"):
        if "CHARLS" in config.data_sources:
            config.data_sources["CHARLS"].path = Path(os.getenv("CHARLS_DATA_DIR"))
    if os.getenv("CLHLS_DATA_DIR"):
        if "CLHLS" in config.data_sources:
            config.data_sources["CLHLS"].path = Path(os.getenv("CLHLS_DATA_DIR"))
    if os.getenv("MIMIC_DATA_DIR"):
        if "MIMIC-IV" in config.data_sources:
            config.data_sources["MIMIC-IV"].path = Path(os.getenv("MIMIC_DATA_DIR"))
    if os.getenv("SEER_DATA_DIR"):
        if "SEER" in config.data_sources:
            config.data_sources["SEER"].path = Path(os.getenv("SEER_DATA_DIR"))
    if os.getenv("ACTIVE_DIVISIONS"):
        config.active_divisions = os.getenv("ACTIVE_DIVISIONS").split(",")

    # 参数覆盖
    for key, value in overrides.items():
        if hasattr(config, key):
            setattr(config, key, value)

    return config
