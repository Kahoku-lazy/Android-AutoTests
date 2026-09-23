"""登录页端到端用例 — Playwright 真实浏览器（黑盒）+ 每步带标注的截图报告。

编号 E2E-### 与业务功能用例编号（BF-## / TC-BF-UI-### / TC-SESSION-###）一一对应，
映射写在每个用例的 docstring 里。

每一步都通过 steps 夹具执行：动作照旧是 Playwright 原生 API，夹具负责截图并在图上标注
「点了哪里 / 输了什么 / 滑了多远」，最后汇总成 tests/reports/e2e/index.html。

运行：python -m pytest tests/e2e -q   （前后端需已启动；无需任何密钥）
"""

import re
import time

import pytest

from playwright.sync_api import expect

from tests.e2e import selectors as S

DASHBOARD_GLOB = "**/dashboard**"
WRONG_PASSWORD = "definitely-wrong-password"


def _login_button(page):
    """登录提交按钮（el-button 渲染成原生 button）。"""
    return page.get_by_test_id(S.LOGIN_SUBMIT).locator("button").first


def _register_button(page):
    return page.get_by_test_id(S.REGISTER_SUBMIT).locator("button").first


def _input(page, testid):
    """testid 挂在原生包裹层，输入框要再取一层 input。"""
    return page.get_by_test_id(testid).locator("input").first


def _fill_login(steps, page, account, user_caption: str = "输入账号") -> None:
    steps.fill(_input(page, S.LOGIN_USERNAME), account["username"], user_caption)
    steps.fill(_input(page, S.LOGIN_PASSWORD), account["password"], "输入密码", secret=True)


def _login_via_ui(steps, page, account) -> None:
    """走界面完成一次成功登录，停在 /dashboard。"""
    steps.shot("打开 /login，登录页渲染完成")
    _fill_login(steps, page, account)
    steps.inspect(_login_button(page), "断言：账号与密码都合格后「登录」按钮点亮")
    steps.click(_login_button(page), "点击「登录」按钮")
    page.wait_for_url(DASHBOARD_GLOB, timeout=20000)
    steps.shot("登录成功，进入工作台 /dashboard")


def _logout_via_ui(steps, page) -> None:
    """走界面完成一次登出，停在 /login。"""
    steps.click(page.get_by_test_id(S.SIDEBAR_LOGOUT), "点击侧栏底部的「退出」")
    page.wait_for_url("**/login**", timeout=20000)
    page.get_by_test_id(S.LOGIN_PAGE).wait_for(timeout=15000)
    steps.shot("登出后回到 /login")


@pytest.mark.e2e
@pytest.mark.auth
def test_e2e_001_login_success_enters_dashboard(login_page, e2e_account, login_requests, steps):
    """BF-01 · TC-BF-UI-006：单击一次 → 恰好 1 次登录请求，落到 /dashboard。"""
    steps.shot("打开 /login，登录页渲染完成")
    _fill_login(steps, login_page, e2e_account)
    steps.inspect(_login_button(login_page), "断言：两个字段都合格后「登录」按钮点亮")
    steps.click(_login_button(login_page), "点击「登录」按钮")
    login_page.wait_for_url(DASHBOARD_GLOB, timeout=20000)
    steps.shot("跳转到工作台 /dashboard")
    assert len(login_requests) == 1, f"登录请求应恰好 1 次，实际 {len(login_requests)} 次"


@pytest.mark.e2e
@pytest.mark.auth
def test_e2e_002_login_failure_overlay_keeps_input_then_retry_succeeds(
    login_page, e2e_account, steps
):
    """BF-02 · TC-BF-UI-014/015：失败给原因 → 关闭后输入保留 → 改对重试成功。"""
    steps.shot("打开 /login")
    steps.fill(_input(login_page, S.LOGIN_USERNAME), e2e_account["username"], "输入账号")
    steps.fill(
        _input(login_page, S.LOGIN_PASSWORD), WRONG_PASSWORD, "输入一个错误的密码", secret=True
    )
    steps.click(_login_button(login_page), "点击「登录」按钮")

    message = login_page.get_by_test_id(S.LOGIN_ERROR_MESSAGE)
    expect(message).to_be_visible(timeout=15000)
    steps.inspect(message, "断言：覆盖层给出「用户名或密码错误」")
    expect(message).to_have_text("用户名或密码错误")

    steps.click(login_page.get_by_test_id(S.LOGIN_ERROR_DISMISS), "点击「知道了」关闭覆盖层")
    expect(message).to_be_hidden()
    steps.inspect(
        _input(login_page, S.LOGIN_USERNAME), "断言：关闭后账号输入仍保留，可直接改后重试"
    )
    expect(_input(login_page, S.LOGIN_USERNAME)).to_have_value(e2e_account["username"])
    expect(_input(login_page, S.LOGIN_PASSWORD)).to_have_value(WRONG_PASSWORD)

    steps.fill(
        _input(login_page, S.LOGIN_PASSWORD), e2e_account["password"], "改成正确的密码", secret=True
    )
    steps.click(_login_button(login_page), "再次点击「登录」重试")
    login_page.wait_for_url(DASHBOARD_GLOB, timeout=20000)
    steps.shot("重试成功，进入工作台 /dashboard")


@pytest.mark.e2e
@pytest.mark.auth
def test_e2e_003_empty_form_button_disabled_and_forced_click_sends_nothing(
    login_page, login_requests, steps
):
    """TC-BF-UI-001/002：空表单按钮为灰；强制点击灰按钮不发请求、不弹覆盖层。"""
    steps.shot("打开 /login，两个字段都是空的")
    button = _login_button(login_page)
    expect(button).to_be_disabled()
    steps.inspect(button, "断言：空表单时「登录」按钮为灰（disabled）")

    steps.click(button, "强制点击灰按钮（应被吞掉）", force=True)
    login_page.wait_for_timeout(800)
    steps.shot("强制点击之后：界面无变化、无提示、未发出请求")

    assert login_requests == [], f"灰按钮不应发出请求，实际 {login_requests}"
    expect(login_page.get_by_test_id(S.LOGIN_ERROR_MESSAGE)).to_have_count(0)


@pytest.mark.e2e
@pytest.mark.auth
def test_e2e_004_button_lights_only_when_both_fields_valid(login_page, e2e_account, steps):
    """TC-BF-UI-003/004/005：只填一项仍灰 → 填齐点亮 → 超长 151 字符回到灰并给文案。"""
    button = _login_button(login_page)
    expect(button).to_be_disabled()
    steps.inspect(button, "起点：两个字段都空，按钮为灰")

    steps.fill(_input(login_page, S.LOGIN_USERNAME), e2e_account["username"], "只填账号")
    expect(button).to_be_disabled()
    steps.inspect(button, "断言：只填一项时按钮仍为灰")

    steps.fill(
        _input(login_page, S.LOGIN_PASSWORD), e2e_account["password"], "再补上密码", secret=True
    )
    expect(button).to_be_enabled()
    steps.inspect(button, "断言：两项都合格后按钮点亮，可点击")

    steps.fill(_input(login_page, S.LOGIN_USERNAME), "u" * 151, "把账号改成 151 个字符（越界）")
    expect(button).to_be_disabled()
    steps.inspect(
        login_page.get_by_text("用户名过长，最多150个字符"),
        "断言：按钮回到灰，并在账号下方给出长度文案",
    )


@pytest.mark.e2e
@pytest.mark.auth
def test_e2e_005_rapid_clicks_produce_one_request_and_one_overlay(
    login_page, e2e_account, login_requests, held_login_requests, steps
):
    """TC-BF-UI-007：1 秒内连点 5 次 → 仍只 1 次请求、只 1 层覆盖层。

    请求被拦住不放行，把「正在提交」的窗口变成确定性的，避免本地后端太快导致偶发漏点。
    """
    steps.shot("打开 /login")
    steps.fill(_input(login_page, S.LOGIN_USERNAME), e2e_account["username"], "输入账号")
    steps.fill(_input(login_page, S.LOGIN_PASSWORD), WRONG_PASSWORD, "输入错误密码", secret=True)

    button = _login_button(login_page)
    steps.click(button, "第一次点击「登录」（请求被拦住，进入提交中窗口）")
    login_page.wait_for_timeout(200)
    assert len(held_login_requests) == 1, "登录请求应已被拦住，进入确定的提交中窗口"

    for attempt in range(2, 6):
        steps.click(button, f"提交中第 {attempt} 次连点（应被吞掉）", force=True)
        login_page.wait_for_timeout(120)

    steps.shot(f"连点 5 次之后：网络层仍只有 {len(login_requests)} 次登录请求")
    assert len(login_requests) == 1, f"连点 5 次只应发 1 次请求，实际 {len(login_requests)} 次"

    held_login_requests[0].continue_()
    message = login_page.get_by_test_id(S.LOGIN_ERROR_MESSAGE)
    expect(message).to_be_visible(timeout=15000)
    steps.inspect(message, "断言：只出现一层错误覆盖层")
    expect(message).to_have_count(1)


@pytest.mark.e2e
@pytest.mark.auth
def test_e2e_006_long_press_sends_one_request(login_page, e2e_account, login_requests, steps):
    """TC-BF-UI-008：按住「登录」1.2 秒再松开 → 只发 1 次请求。"""
    steps.shot("打开 /login")
    steps.fill(_input(login_page, S.LOGIN_USERNAME), e2e_account["username"], "输入账号")
    steps.fill(_input(login_page, S.LOGIN_PASSWORD), WRONG_PASSWORD, "输入错误密码", secret=True)

    steps.long_press(_login_button(login_page), 1200, "按住「登录」1.2 秒后松开")
    message = login_page.get_by_test_id(S.LOGIN_ERROR_MESSAGE)
    expect(message).to_be_visible(timeout=15000)
    steps.inspect(message, "断言：长按只触发一次提交，出现一层错误覆盖层")
    assert len(login_requests) == 1, f"长按只应发 1 次请求，实际 {len(login_requests)} 次"


@pytest.mark.e2e
@pytest.mark.auth
def test_e2e_007_submit_shows_loading_and_reaches_dashboard(
    login_page, e2e_account, login_requests, held_login_requests, steps
):
    """TC-BF-UI-010：提交中按钮转圈且不可再点；放行后进入工作台。"""
    steps.shot("打开 /login")
    _fill_login(steps, login_page, e2e_account)

    button = _login_button(login_page)
    steps.click(button, "点击「登录」（请求被拦住，停在提交中状态）")
    login_page.wait_for_timeout(200)
    assert len(held_login_requests) == 1, "登录请求应已被拦住，进入确定的提交中窗口"

    expect(button).to_be_disabled()
    assert "is-loading" in (button.get_attribute("class") or ""), "提交中按钮应处于 loading 态"
    steps.inspect(button, "断言：提交中按钮转圈（loading）且不可点击")

    steps.click(button, "提交中再点一次（应被吞掉）", force=True)
    login_page.wait_for_timeout(150)
    assert len(login_requests) == 1, (
        f"提交中的再点不应产生第二个请求，实际 {len(login_requests)} 次"
    )

    held_login_requests[0].continue_()
    login_page.wait_for_url(DASHBOARD_GLOB, timeout=20000)
    steps.shot("放行后登录成功，进入工作台 /dashboard")


@pytest.mark.e2e
@pytest.mark.auth
def test_e2e_008_enter_does_not_submit_current_behavior(
    login_page, e2e_account, login_requests, steps
):
    """TC-BF-UI-011：当前行为 —— 表单没有原生提交按钮，输入框里按回车不发请求。

    依据功能测试文档第五节待决项 1（实测 0 请求）。这是被登记的可用性缺口，不是期望行为：
    产品若决定支持回车提交，本用例应改为断言 1 次请求并落到 /dashboard。
    """
    steps.shot("打开 /login")
    _fill_login(steps, login_page, e2e_account)

    steps.press(_input(login_page, S.LOGIN_PASSWORD), "Enter", "焦点在密码框时按 Enter")
    login_page.wait_for_timeout(1000)
    steps.shot("按 Enter 之后：仍停在登录页，没有发出登录请求")

    assert login_requests == [], f"当前行为下回车不应发请求，实际 {login_requests}"
    expect(login_page.get_by_test_id(S.LOGIN_PAGE)).to_be_visible()


@pytest.mark.e2e
@pytest.mark.auth
def test_e2e_009_remember_username_round_trip(login_page, e2e_account, e2e_services, steps):
    """BF-04 · TC-BF-UI-018：勾选后登录 → 登出再开 /login 预填且开关为开；取消勾选后记录被清。"""
    frontend = e2e_services["frontend"]
    remember = login_page.get_by_test_id(S.LOGIN_REMEMBER).locator(".el-switch")

    steps.click(remember, "打开「记住账号」开关")
    expect(remember).to_have_class(re.compile("is-checked"))
    steps.inspect(remember, "断言：「记住账号」开关已打开")

    _login_via_ui(steps, login_page, e2e_account)
    assert login_page.evaluate("localStorage.getItem('saved_username')") == e2e_account["username"]
    steps.shot("断言：登录成功后 localStorage.saved_username 记录了本次账号")

    # 已登录时 /login 会被路由守卫送回 /dashboard，所以先登出，再重新打开登录页看预填效果
    _logout_via_ui(steps, login_page)
    steps.shot("准备重新打开登录页：/login")
    login_page.goto(f"{frontend}/login", wait_until="domcontentloaded")
    login_page.get_by_test_id(S.LOGIN_PAGE).wait_for(timeout=15000)
    steps.inspect(_input(login_page, S.LOGIN_USERNAME), "断言：重开登录页时账号已自动预填")
    expect(_input(login_page, S.LOGIN_USERNAME)).to_have_value(e2e_account["username"])
    expect(login_page.get_by_test_id(S.LOGIN_REMEMBER).locator(".el-switch")).to_have_class(
        re.compile("is-checked")
    )

    steps.click(
        login_page.get_by_test_id(S.LOGIN_REMEMBER).locator(".el-switch"),
        "取消勾选「记住账号」",
    )
    _login_via_ui(steps, login_page, e2e_account)
    assert login_page.evaluate("localStorage.getItem('saved_username')") is None
    steps.shot("断言：取消勾选后再登录，本地记录已被清除")

    _logout_via_ui(steps, login_page)
    login_page.goto(f"{frontend}/login", wait_until="domcontentloaded")
    login_page.get_by_test_id(S.LOGIN_PAGE).wait_for(timeout=15000)
    steps.inspect(_input(login_page, S.LOGIN_USERNAME), "断言：账号框为空，不再预填")
    expect(_input(login_page, S.LOGIN_USERNAME)).to_have_value("")


@pytest.mark.e2e
@pytest.mark.auth
def test_e2e_010_mode_switch_syncs_cta_title_and_resets_form(login_page, steps):
    """BF-05：CTA 与便签标题同步切换；切到注册会清空注册表单字段。"""
    title = login_page.get_by_test_id(S.MEETING_TITLE)
    expect(title).to_have_text("登录")
    expect(login_page.get_by_test_id(S.LOGIN_MODE_LOGIN)).to_have_attribute("aria-pressed", "true")
    steps.inspect(title, "起点：便签标题为「登录」，登录 CTA 处于选中态")

    steps.click(login_page.get_by_test_id(S.LOGIN_TO_REGISTER), "点击卡片底部的「去注册 →」")
    expect(title).to_have_text("注册")
    expect(login_page.get_by_test_id(S.LOGIN_MODE_REGISTER)).to_have_attribute(
        "aria-pressed", "true"
    )
    expect(login_page.get_by_test_id(S.REGISTER_USERNAME)).to_be_visible()
    steps.shot("切到注册态：便签标题与表单同步切换")

    steps.fill(
        _input(login_page, S.REGISTER_USERNAME), "a_temporary_input", "在注册账号框随便填一个值"
    )
    steps.click(login_page.get_by_test_id(S.LOGIN_MODE_LOGIN), "点击「登录」CTA 切回登录")
    expect(login_page.get_by_test_id(S.LOGIN_MODE_LOGIN)).to_have_attribute("aria-pressed", "true")
    steps.click(login_page.get_by_test_id(S.LOGIN_MODE_REGISTER), "再点「注册 →」CTA 切回注册")
    expect(_input(login_page, S.REGISTER_USERNAME)).to_have_value("")
    steps.inspect(_input(login_page, S.REGISTER_USERNAME), "断言：切回注册后该字段已被清空")


@pytest.mark.e2e
@pytest.mark.auth
def test_e2e_011_register_enters_dashboard_without_second_login(login_page, steps):
    """BF-06：注册成功即完成登录，直接进入工作台（不用再登一次）。"""
    unique = "e2e" + str(int(time.time() * 1000))[-12:]

    steps.shot("打开 /login")
    steps.click(login_page.get_by_test_id(S.LOGIN_MODE_REGISTER), "点击「注册 →」CTA 进入注册态")
    steps.fill(_input(login_page, S.REGISTER_USERNAME), unique, f"输入新账号 {unique}")
    steps.fill(_input(login_page, S.REGISTER_EMAIL), f"{unique}@test.local", "输入邮箱")
    steps.fill(_input(login_page, S.REGISTER_PASSWORD), "Test123456", "输入密码", secret=True)
    steps.fill(_input(login_page, S.REGISTER_PASSWORD2), "Test123456", "再次输入密码", secret=True)
    steps.inspect(_register_button(login_page), "断言：四个字段都合格后「完成注册」按钮点亮")

    steps.click(_register_button(login_page), "点击「完成注册」")
    login_page.wait_for_url(DASHBOARD_GLOB, timeout=20000)
    steps.shot("注册成功即登录，直接进入工作台 /dashboard")
    expect(login_page.get_by_test_id(S.SIDEBAR_ACTIVE_ACCOUNT)).to_have_text(unique)
    steps.inspect(
        login_page.get_by_test_id(S.SIDEBAR_ACTIVE_ACCOUNT), "断言：侧栏当前账号就是新注册账号"
    )


@pytest.mark.e2e
@pytest.mark.auth
def test_e2e_012_logout_returns_to_login(login_page, e2e_account, steps):
    """BF-07 · TC-SESSION-007：侧栏登出 → 回登录页，本地会话凭证整份清空。"""
    _login_via_ui(steps, login_page, e2e_account)

    _logout_via_ui(steps, login_page)

    session = login_page.evaluate(
        "['access_token', 'refresh_token', 'username'].map((k) => [k, localStorage.getItem(k)])"
    )
    leftover = {name: value for name, value in session if value is not None}
    assert leftover == {}, f"登出后本地仍残留会话键：{leftover}"
    assert login_page.evaluate("localStorage.getItem('auth_accounts')") is None, "登出后仍存在账号池键"


@pytest.mark.e2e
@pytest.mark.auth
def test_e2e_013_anonymous_visiting_dashboard_is_sent_to_login(page, e2e_services, steps):
    """TC-SESSION-001：未登录访问 /dashboard → 跳 /login。"""
    steps.shot("起点：一个全新的、未登录的浏览器上下文")
    page.goto(f"{e2e_services['frontend']}/dashboard", wait_until="domcontentloaded")
    page.wait_for_url("**/login", timeout=15000)
    steps.shot("未登录访问 /dashboard：被路由守卫送回 /login")
    expect(page.get_by_test_id(S.LOGIN_PAGE)).to_be_visible()


@pytest.mark.e2e
@pytest.mark.auth
def test_e2e_014_logged_in_visiting_login_is_sent_to_dashboard(
    login_page, e2e_account, e2e_services, steps
):
    """TC-SESSION-002：已登录访问 /login → 跳 /dashboard。"""
    _login_via_ui(steps, login_page, e2e_account)
    login_page.goto(f"{e2e_services['frontend']}/login", wait_until="domcontentloaded")
    login_page.wait_for_url(DASHBOARD_GLOB, timeout=15000)
    steps.shot("已登录时访问 /login：被守卫送回 /dashboard")


@pytest.mark.e2e
@pytest.mark.auth
def test_e2e_015_narrow_viewport_keeps_login_reachable(page, e2e_services, e2e_account, steps):
    """TC-BF-UI-022：480×844 下无横向溢出，登录卡与按钮可达可点。"""
    page.set_viewport_size({"width": 480, "height": 844})
    steps.shot("先把视口设成 480×844（窄屏）")

    page.goto(f"{e2e_services['frontend']}/login", wait_until="domcontentloaded")
    page.get_by_test_id(S.LOGIN_PAGE).wait_for(timeout=15000)
    steps.shot("窄屏下的登录页首屏")

    overflow = page.evaluate(
        "() => document.documentElement.scrollWidth - document.documentElement.clientWidth"
    )
    assert overflow <= 1, f"窄屏出现横向溢出 {overflow}px"

    _fill_login(steps, page, e2e_account)
    steps.scroll(0, 240, "向下滑动 240px 找到登录卡底部的按钮")
    button = _login_button(page)
    expect(button).to_be_enabled()
    button.scroll_into_view_if_needed()
    expect(button).to_be_in_viewport()
    steps.inspect(button, "断言：窄屏下按钮仍可达可点，且无横向滚动")
