"""evaluator URL routing."""

from django.urls import path

from .views import (
    bank_detail,
    create_bank,
    delete_bank,
    delete_run,
    kb_search,
    kb_self_test,
    list_banks,
    list_frameworks,
    list_runs,
    run_detail,
    seed_default_bank,
    start_eval_run,
    submit_human_score,
    update_bank,
)

app_name = "evaluator"

urlpatterns = [
    # Question banks
    path("banks", list_banks, name="banks_list"),
    path("banks/create", create_bank, name="bank_create"),
    path("banks/seed", seed_default_bank, name="bank_seed"),
    path("banks/<int:bank_id>", bank_detail, name="bank_detail"),
    path("banks/<int:bank_id>/update", update_bank, name="bank_update"),
    path("banks/<int:bank_id>/delete", delete_bank, name="bank_delete"),
    # Eval runs
    path("runs", list_runs, name="runs_list"),
    path("runs/start", start_eval_run, name="run_start"),
    path("runs/<int:run_id>", run_detail, name="run_detail"),
    path("runs/<int:run_id>/delete", delete_run, name="run_delete"),
    # Human scoring
    path("results/<int:result_id>/score", submit_human_score, name="result_score"),
    # Frameworks
    path("frameworks", list_frameworks, name="frameworks_list"),
    # KB search & self-test
    path("kb-search", kb_search, name="kb_search"),
    path("kb-self-test", kb_self_test, name="kb_self_test"),
]
