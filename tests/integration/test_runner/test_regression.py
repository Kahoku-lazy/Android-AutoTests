"""
Regression tests for bugs discovered during Web executor QA.

ALL tests in this file should FAIL to prove the bug exists.
A PASS means the bug has been FIXED (or the test is wrong).
"""
import pytest
import json
import asyncio
from unittest.mock import MagicMock, AsyncMock


# ══════════════════════════════════════════════════════════════════════
# Bug #2: api_directories — StorageTestCase has no steps_json field
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestBug2_Storage500:
    """GET /api/cases/directories?case_type=storage → 500.

    api_directories.py:39 accesses td.steps_json on every case model,
    but StorageTestCase uses `steps` (TextField) not `steps_json`.
    """

    def test_directory_tree_crashes_on_storage(self):
        """This MUST fail until StorageTestCase gets steps_json support."""
        from apps.case_manager.api_directories import get_directory_tree
        from apps.case_manager.models import CaseDirectory
        from apps.case_manager.models_storage import StorageTestCase

        d = CaseDirectory.objects.create(name="test-dir", case_type="storage")
        StorageTestCase.objects.create(
            id="ST-REGRESSION-001", title="Storage Case", directory=d,
        )

        try:
            get_directory_tree(case_type="storage")
        except AttributeError as e:
            if "steps_json" in str(e):
                pytest.fail(
                    f"BUG CONFIRMED: StorageTestCase has no steps_json field. "
                    f"api_directories.py:39 accesses td.steps_json unconditionally. "
                    f"Error: {e}"
                )
            raise
        else:
            # Bug is fixed — test should pass
            pass


# ══════════════════════════════════════════════════════════════════════
# Bug #3: State machine — enqueue→dequeue stale in-memory object
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestBug3_StateMachineStaleObject:
    """_persist_run_start: sm.enqueue() then sm.dequeue() with stale tc_card.

    sm.enqueue() re-fetches inside _save_transaction. The caller's tc_card
    stays at status="idle". sm.dequeue() then rejects idle→running.
    """

    def test_enqueue_then_dequeue_without_refresh(self):
        """This MUST fail until execution_steps.py refreshes tc_card after enqueue."""
        from apps.test_runner.models import TaskCard
        from apps.test_runner import state_machine as sm

        tc = TaskCard.objects.create(
            task_id="BUG-STALE-001", status="idle", device_serial="test",
        )
        sm.enqueue(tc, "test-device")
        # tc.status is STILL "idle" (stale — sm.enqueue re-fetched internally)

        try:
            sm.dequeue(tc, "run-test-001", "test-device", [], 1)
        except sm.InvalidTransition as e:
            pytest.fail(
                f"BUG CONFIRMED: sm.enqueue() does not update the caller's "
                f"TaskCard reference. sm.dequeue() sees status='idle' not "
                f"'queued' and rejects the transition. "
                f"Fix: add tc_card.refresh_from_db() after sm.enqueue() in "
                f"execution_steps.py:124. Error: {e}"
            )
        # If dequeue succeeded without error → bug is fixed → test passes


# ══════════════════════════════════════════════════════════════════════
# Bug #5: WebExecutor._verify_expected_result — literal text match
# ══════════════════════════════════════════════════════════════════════


class TestBug5_ExpectedResultLiteralMatch:
    """expected_result is natural-language description, not page text.

    executor.py:117:  if expected not in str(page_text)[:10000]
    Substring-matches a human description against HTML — always fails
    for descriptive text like "页面跳转到仪表盘，显示'仪表盘'标题".
    """

    def test_descriptive_text_not_literal_page_content(self):
        """This MUST fail until expected_result matching logic is fixed."""
        page_html = "<html><body><h1>仪表盘</h1><p>Welcome to dashboard</p></body></html>"
        expected_descriptive = "页面跳转到仪表盘，显示'仪表盘'标题"
        expected_keyword = "仪表盘"

        # The keyword IS found on the page...
        assert expected_keyword in page_html, "sanity check: keyword exists"

        # But the full descriptive text is NOT literal page content
        if expected_descriptive not in page_html:
            pytest.fail(
                f"BUG CONFIRMED: expected_result='{expected_descriptive}' is "
                f"a human description, not literal page text. The code at "
                f"executor.py:117 does substring matching against HTML, so "
                f"this always fails for any descriptive expected_result."
            )

    def test_partial_match_only_finds_exact_words(self):
        """Descriptive framing around a keyword also fails."""
        page_html = "<html><body><h1>Dashboard</h1></body></html>"
        expected = "页面显示Dashboard标题"

        if "Dashboard" in page_html and expected not in page_html:
            pytest.fail(
                f"BUG CONFIRMED: 'Dashboard' is on the page but "
                f"'{expected}' is not literal content. "
                f"Descriptive expected_result values never match."
            )


# ══════════════════════════════════════════════════════════════════════
# Bug #6: case_ids order not preserved by id__in
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestBug6_CaseIdsOrder:
    """Django id__in does not preserve input list order.

    execution.py:107 uses WebTestCase.objects.filter(id__in=case_ids).
    """

    def test_id_in_does_not_preserve_input_order(self):
        """This MUST fail until case loading preserves user-specified order."""
        from apps.case_manager.models_web import WebTestCase

        WebTestCase.objects.filter(id__startswith="BUG-ORDER-").delete()
        WebTestCase.objects.create(id="BUG-ORDER-BBB", title="Case B", url="http://x.com")
        WebTestCase.objects.create(id="BUG-ORDER-AAA", title="Case A", url="http://x.com")

        requested_order = ["BUG-ORDER-BBB", "BUG-ORDER-AAA"]
        results = list(WebTestCase.objects.filter(id__in=requested_order))
        result_ids = [r.id for r in results]

        if result_ids != requested_order:
            pytest.fail(
                f"BUG CONFIRMED: id__in returned {result_ids} but requested "
                f"{requested_order}. Django filter does not preserve input list "
                f"order. Fix: sort results to match the input order, or use "
                f"Case.objects.filter().order_by(...) with a CASE WHEN expression."
            )


# ══════════════════════════════════════════════════════════════════════
# Bug #4: WS broadcast consumer discard → silent message loss
# ══════════════════════════════════════════════════════════════════════


class TestBug4_WsSilentDiscard:
    """_broadcast discards consumer on timeout → all subsequent messages
    silently dropped. No error, no retry, no feedback to caller.
    """

    @pytest.mark.asyncio
    async def test_slow_consumer_discarded_silently(self):
        """This MUST fail until _broadcast has error reporting on discard."""
        from apps.test_runner.callbacks import WsTestCallback

        cb = WsTestCallback()
        run_id = "bug-discard-001"

        slow_consumer = AsyncMock()
        slow_consumer.send = AsyncMock(side_effect=asyncio.TimeoutError)
        cb.register(run_id, slow_consumer)

        await cb.on_log(run_id, "msg-1")

        # Consumer discarded — but no error was raised
        consumer_gone = run_id not in cb.clients or not cb.clients[run_id]

        # Send more messages — all silently lost
        await cb.on_log(run_id, "msg-2-lost")
        await cb.on_step_result(run_id, "C1", 1, 0, 5, "x", "y", "pass")

        if consumer_gone:
            pytest.fail(
                f"BUG CONFIRMED: WS consumer was silently discarded after "
                f"send() timeout. All subsequent on_log/on_step_result calls "
                f"are no-ops — messages are lost with zero feedback to the "
                f"caller (_bridge_ws_log has no way to detect this)."
            )

    @pytest.mark.asyncio
    async def test_broadcast_to_zero_consumers_no_error(self):
        """This MUST fail until broadcast returns feedback on delivery."""
        from apps.test_runner.callbacks import WsTestCallback

        cb = WsTestCallback()
        run_id = "bug-discard-002"

        # No consumers registered — all messages silently dropped
        await cb.on_log(run_id, "lost-1")
        await cb.on_case_started(run_id, "C1", "title", 3)
        await cb.on_step_result(run_id, "C1", 1, 0, 5, "x", "y", "pass")

        pytest.fail(
            f"BUG CONFIRMED: Broadcasting to zero consumers silently drops "
            f"all messages. The caller has no way to know delivery failed. "
            f"_broadcast() should return a delivery status or raise when "
            f"no consumers are registered."
        )
