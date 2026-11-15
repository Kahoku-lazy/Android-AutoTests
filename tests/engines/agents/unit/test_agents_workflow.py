"""
调试代码，功能不完善 ~ 禁止修改此文件代码。
调试指令：python -m tests.engines.agents.test_agents_workflow
"""

from engines.agents.workflow.ui_auto_workflow import run_workflow


class TestAgentsWorkflow:
    def test_ui_auto_workflow(self):

        #  (yml_path: str, run_input: str, case_title: str | None
        data = {
            "yml_path": "tests/engines/agents/test_agents_workflow.yml",
            "run_input": "1234567890",
            "case_title": "test_ui_auto_workflow",
        }

        run_workflow(data["yml_path"], data["run_input"], data["case_title"])


if __name__ == "__main__":
    data = {
        "yml_path": "tests/engines/agents/1.yaml",
        "run_input": "192.168.35.57:39569",
    }
    result = run_workflow(data["yml_path"], data["run_input"])
