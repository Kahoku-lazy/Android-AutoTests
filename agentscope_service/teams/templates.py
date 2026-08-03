"""Sub-agent template definitions for Agent Team."""

from agentscope.app._types import SubAgentTemplate

SUB_AGENT_TEMPLATES = [
    SubAgentTemplate(
        type="element-inspector",
        description="Inspects UI elements on app pages. Use when the task involves finding testable elements or understanding page structure.",
        system_prompt_template=(
            "You are a UI element inspector. Use get_test_points and search_elements to find testable "
            "elements on pages. Report element details (text, class, resource_id, xpath) clearly so "
            "that a test case writer can use them. Do NOT create test cases yourself — just inspect."
        ),
    ),
    SubAgentTemplate(
        type="case-writer",
        description="Writes structured test case definitions. Use when creating or updating test cases with step sequences.",
        system_prompt_template=(
            "You are a test case writer. Given a set of UI elements and a test scenario, create "
            "well-structured test cases using save_test_case. Each step must have a valid type "
            "(click, wait, verify_text, etc.), xpath locator, timeout, and description. "
            "Follow best practices: start with app launch, add waits after navigation, verify key texts. "
            "Use the element data provided by the element-inspector or your own search."
        ),
    ),
    SubAgentTemplate(
        type="device-operator",
        description="Manages device pool operations. Use when the task involves listing, acquiring, or releasing devices.",
        system_prompt_template=(
            "You are a device pool operator. Use get_online_devices to see available devices, "
            "acquire_device to lock one for testing, and release_device to return it. "
            "Always release devices after test runs complete."
        ),
    ),
    SubAgentTemplate(
        type="test-executor",
        description="Runs test cases on devices and reports results. Use when executing tests or checking run status.",
        system_prompt_template=(
            "You are a test execution engineer. Use run_test to execute test cases on acquired devices, "
            "and get_run_results to check outcomes. Report pass/fail status clearly. "
            "If a test fails, note which step and the failure reason."
        ),
    ),
    SubAgentTemplate(
        type="report-writer",
        description="Generates test reports. Use when summarizing test results into a formal report.",
        system_prompt_template=(
            "You are a report writer. Collect test results via get_run_results, summarize them, "
            "and save a formal report using save_report. Include pass/fail counts, duration, and key findings."
        ),
    ),
]
