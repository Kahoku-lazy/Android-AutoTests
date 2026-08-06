"""tests/ 共享 fixtures — 所有测试模块共用的前置依赖。"""

import json
import os
import platform
import sys

from pathlib import Path

import pytest
import requests

# ── 环境配置 ──

BASE_URL = os.environ.get("TEST_BASE_URL", "http://localhost:8766")
LOGIN_PATH = "/api/ai/auth/login"

# ── Allure 元数据文件生成 ──


def _write_allure_metadata(config: pytest.Config) -> None:
    """在测试运行前生成 Allure 环境/类别/运行器元数据文件。

    四个报告页签的对应关系：
      - 趋势（Trends）     → Allure 自动从 history/ 目录合并，无需手动配置
      - 类别（Categories） → categories.json — 失败用例缺陷分类
      - 环境（Environment）→ environment.properties — 被测环境键值清单
      - 运行器（Executors）→ executor.json — 谁执行的、用什么工具
    """
    allure_dir = Path(str(config.rootpath)) / "tests" / "allure-results"
    allure_dir.mkdir(parents=True, exist_ok=True)

    # ── 1. environment.properties ──
    _write_environment(allure_dir)

    # ── 2. categories.json ──
    _write_categories(allure_dir)

    # ── 3. executor.json ──
    _write_executor(allure_dir)


def _write_environment(allure_dir: Path) -> None:
    """写入被测环境参数 — 报告"环境"页签的数据来源。"""
    props = [
        f"被测服务={BASE_URL}",
        f"Python={sys.version.split()[0]}",
        f"平台={platform.system()} {platform.release()}",
        f"处理器={platform.machine()}",
    ]
    # 如果 Django 可用则追加版本号
    try:
        import django  # noqa: F401
    except ImportError:
        pass
    else:
        props.append(f"Django={django.VERSION[0]}.{django.VERSION[1]}")
    (allure_dir / "environment.properties").write_text("\n".join(props) + "\n", encoding="utf-8")


def _write_categories(allure_dir: Path) -> None:
    """写入缺陷分类规则 — 报告"类别"页签的数据来源。

    Allure 内置默认两类：Product Defects（failed）和 Test Defects（broken）。
    这里覆盖为中文名称，并新增业务相关的消息正则分类。
    """
    categories = [
        {
            "name": "产品缺陷",
            "description": "被测代码逻辑有 bug — 断言不通过，产品行为不符合预期",
            "matchedStatuses": ["failed"],
            "flaky": False,
        },
        {
            "name": "测试代码缺陷",
            "description": "测试代码自身出错 — 未跑到断言即崩溃（KeyError / ConnectionError 等）",
            "matchedStatuses": ["broken"],
            "flaky": False,
        },
        {
            "name": "认证/鉴权异常",
            "description": "登录失败或 Token 校验异常",
            "matchedStatuses": ["failed"],
            "messageRegex": ".*(用户名或密码错误|Token|JWT|鉴权|认证).*",
        },
        {
            "name": "参数校验缺失",
            "description": "后端未正确拦截非法输入",
            "matchedStatuses": ["failed"],
            "messageRegex": ".*(请输入|格式不正确|不能为空|不一致).*",
        },
        {
            "name": "服务连接故障",
            "description": "被测服务不可达或数据库连接失败",
            "matchedStatuses": ["broken"],
            "messageRegex": ".*(Connection|refused|timeout|502|503).*",
        },
    ]
    (allure_dir / "categories.json").write_text(
        json.dumps(categories, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _write_executor(allure_dir: Path) -> None:
    """写入运行器信息 — 报告"运行器"页签的数据来源。

    可通过环境变量覆盖：
      ALLURE_EXECUTOR_NAME   — 运行器名称（如 Jenkins / GitHub Actions）
      ALLURE_EXECUTOR_TYPE   — 运行器类型（如 jenkins / github）
      ALLURE_EXECUTOR_BUILD  — 构建名称/编号
    """
    executor = {
        "name": os.environ.get("ALLURE_EXECUTOR_NAME", "本地开发机"),
        "type": os.environ.get("ALLURE_EXECUTOR_TYPE", "pytest"),
        "buildName": os.environ.get("ALLURE_EXECUTOR_BUILD", platform.node()),
        "buildOrder": int(os.environ.get("ALLURE_EXECUTOR_BUILD_ORDER", "1")),
    }
    (allure_dir / "executor.json").write_text(
        json.dumps(executor, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ── Hooks ──


def pytest_sessionstart(session: pytest.Session) -> None:
    """测试会话启动时自动写入 Allure 元数据文件。"""
    _write_allure_metadata(session.config)


# ── Fixtures ──


@pytest.fixture(scope="session")
def base_url() -> str:
    """被测服务根地址，默认 http://localhost:8766。可通过 TEST_BASE_URL 环境变量覆盖。"""
    return BASE_URL


@pytest.fixture(scope="function")
def api_session() -> requests.Session:
    """预配置 Content-Type 的 requests.Session，每个测试函数独立实例。"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session
