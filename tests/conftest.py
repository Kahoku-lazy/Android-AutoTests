"""tests/ 三层测试框架的全局公共 fixture。

层次划分（各自独立执行）：
  - tests/api/      接口测试（黑盒 HTTP，live server）
  - tests/graybox/  灰盒测试（unit 单元 + integration 集成）
  - tests/e2e/      黑盒测试（端到端，真实浏览器）
  - tests/arch/     架构契约测试（保留）

共享 fixture 只放跨层通用的最小项；各层专属 fixture 放各自 conftest.py。
"""

import os

import pytest

BASE_URL = os.environ.get("TEST_BASE_URL", "http://localhost:8766")


@pytest.fixture(scope="session")
def base_url() -> str:
    """被测后端根地址，默认 http://localhost:8766，可用 TEST_BASE_URL 覆盖。"""
    return BASE_URL
