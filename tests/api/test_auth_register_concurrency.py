"""并发同名注册（TC-REG-023）— 唯一性由数据库唯一约束保证，并发下也只一个成功。

用例源：tests/api/case/register.yaml 的 TC-REG-023（带 `concurrent: 2` 标记的多请求用例，
故由本驱动执行，不进 test_login_page.py 的单请求参数化）。

期望：两个并发请求恰好一个 200、一个 409「用户名已存在」，绝不出现 500
（校验层不做唯一性判重，冲突由数据库约束翻译为领域错误）。
"""

import uuid

from concurrent.futures import ThreadPoolExecutor

import pytest
import requests

from tests.api.loader import load_cases, resolve

CASE = next(case for case in load_cases("register.yaml") if case.get("concurrent"))
WORKERS = CASE["concurrent"]
EXPECT_STATUS = CASE["expect"]["status"]
EXPECT_MESSAGE = CASE["expect"]["check"]["message"]


@pytest.mark.api
@pytest.mark.auth
def test_concurrent_register_same_username(base_url):
    username = f"test_{uuid.uuid4().hex[:8]}"
    url = f"{base_url}{CASE['path']}"
    body = resolve(CASE["body"], unique_username=username)
    headers = {"Content-Type": "application/json"}

    def register_once(_: int) -> requests.Response:
        return requests.post(url, json=body, headers=headers)

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        responses = list(pool.map(register_once, range(WORKERS)))

    statuses = sorted(resp.status_code for resp in responses)
    assert statuses == [200, EXPECT_STATUS], (
        f"{CASE['id']}（{CASE['title']}）: 期望恰好一个 200、一个 {EXPECT_STATUS}，"
        f"实际 {[(resp.status_code, resp.text[:120]) for resp in responses]}"
    )

    conflict = next(resp for resp in responses if resp.status_code == EXPECT_STATUS)
    assert conflict.json()["message"] == EXPECT_MESSAGE

    winner = next(resp for resp in responses if resp.status_code == 200)
    assert winner.json()["data"]["user"]["username"] == username
