from __future__ import annotations

import os
import re

from pathlib import Path

from .models import KnowledgeModule, KsEvalQuery, KsEvalRun, RetrievalSettings

_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def list_modules() -> list[KnowledgeModule]:
    return list(KnowledgeModule.objects.order_by("name"))


def get_module(module_id: int) -> KnowledgeModule | None:
    return KnowledgeModule.objects.filter(pk=module_id).first()


def create_module(
    *,
    name: str,
    description: str,
    data_dir: str,
    enabled: bool = True,
) -> KnowledgeModule:
    fields = _validate_fields(
        name=name, description=description, data_dir=data_dir, enabled=enabled
    )
    if KnowledgeModule.objects.filter(name=fields["name"]).exists():
        raise ValueError(f"库名已存在：{fields['name']}")
    _check_isolation(fields["name"], Path(fields["data_dir"]), fields["enabled"])
    return KnowledgeModule.objects.create(**fields)


def update_module(module_id: int, **changes: object) -> KnowledgeModule:
    module = get_module(module_id)
    if module is None:
        raise ValueError(f"模块不存在：{module_id}")
    unknown = set(changes) - {"name", "description", "data_dir", "enabled"}
    if unknown:
        raise ValueError(f"未知字段：{', '.join(sorted(unknown))}")
    merged = {
        "name": module.name,
        "description": module.description,
        "data_dir": module.data_dir,
        "enabled": module.enabled,
    }
    merged.update(changes)
    fields = _validate_fields(**merged)
    if KnowledgeModule.objects.filter(name=fields["name"]).exclude(pk=module_id).exists():
        raise ValueError(f"库名已存在：{fields['name']}")
    _check_isolation(
        fields["name"], Path(fields["data_dir"]), fields["enabled"], exclude_id=module_id
    )
    for field, value in fields.items():
        setattr(module, field, value)
    module.save()
    return module


def delete_module(module_id: int) -> bool:
    module = get_module(module_id)
    if module is None:
        return False
    module.delete()
    return True


def _validate_fields(*, name: str, description: str, data_dir: str, enabled: bool) -> dict:
    name = str(name or "").strip()
    if not _NAME_RE.fullmatch(name):
        raise ValueError(f"库名不合法：{name!r}（须以小写字母开头，只含小写字母/数字/下划线）")
    description = str(description or "").strip()
    if not description:
        raise ValueError("模块说明不能为空")
    if len(description) > 200:
        raise ValueError("模块说明不能超过 200 字")
    raw_dir = str(data_dir or "").strip()
    if not raw_dir:
        raise ValueError("资料目录不能为空")
    path = Path(raw_dir)
    if not path.is_absolute():
        raise ValueError(f"资料目录必须是绝对路径：{raw_dir}")
    if not path.exists() or not path.is_dir():
        raise ValueError(f"资料目录不存在或不是目录：{raw_dir}")
    if not os.access(path, os.R_OK):
        raise ValueError(f"资料目录不可读：{raw_dir}")
    if not isinstance(enabled, bool):
        raise ValueError("enabled 必须是布尔值")
    return {
        "name": name,
        "description": description,
        "data_dir": str(path.resolve()),
        "enabled": enabled,
    }


def _check_isolation(
    name: str,
    data_dir: Path,
    enabled: bool,
    *,
    exclude_id: int | None = None,
) -> None:
    if not enabled:
        return
    others = KnowledgeModule.objects.filter(enabled=True)
    if exclude_id is not None:
        others = others.exclude(pk=exclude_id)
    for other in others:
        other_dir = Path(other.data_dir)
        if data_dir == other_dir or data_dir in other_dir.parents or other_dir in data_dir.parents:
            raise ValueError(f"启用库资料目录冲突：{name} 与 {other.name}")


def get_retrieval_settings() -> RetrievalSettings | None:
    return RetrievalSettings.objects.order_by("id").first()


def save_retrieval_settings(
    *,
    embedding_model_id: int,
    top_k: int,
    score_threshold: float,
    chunk_size: int,
    chunk_overlap: int,
) -> tuple[RetrievalSettings, bool]:
    _require_embedding_model(embedding_model_id)
    top_k = _positive_int(top_k, "top_k")
    chunk_size = _positive_int(chunk_size, "chunk_size")
    chunk_overlap = _positive_int(chunk_overlap, "chunk_overlap")
    if not 0 <= float(score_threshold) <= 1:
        raise ValueError("相似度阈值必须在 0 到 1 之间")
    if chunk_overlap >= chunk_size:
        raise ValueError("切块重叠必须小于切块大小")
    current = get_retrieval_settings()
    chunk_changed = current is None or (
        current.chunk_size != chunk_size or current.chunk_overlap != chunk_overlap
    )
    if current is None:
        current = RetrievalSettings(index_epoch=0)
    current.embedding_model_id = int(embedding_model_id)
    current.top_k = top_k
    current.score_threshold = float(score_threshold)
    current.chunk_size = chunk_size
    current.chunk_overlap = chunk_overlap
    if chunk_changed and current.pk is not None:
        current.index_epoch += 1
    current.save()
    return current, chunk_changed and current.index_epoch > 0


def _require_embedding_model(model_id: int) -> None:
    from backend.apps.ai_assistant.models import AIModelConfig

    config = AIModelConfig.objects.filter(pk=int(model_id)).first()
    if config is None or config.model_kind != "embedding":
        raise ValueError("检索配置只能引用向量模型")


def _positive_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{name} 必须是正整数")
    return value


def create_eval_run(
    *,
    module_name: str,
    module_snapshot: dict,
    model_config_id: int | None,
    model_snapshot: dict,
    retrieval_snapshot: dict | None = None,
    pos_count: int,
    neg_count: int,
    seed: int,
    cost_estimate: dict,
) -> KsEvalRun:
    return KsEvalRun.objects.create(
        module_name=module_name,
        module_snapshot=module_snapshot,
        model_config_id=model_config_id,
        model_snapshot={**model_snapshot, "retrieval": retrieval_snapshot or {}},
        pos_count=pos_count,
        neg_count=neg_count,
        seed=seed,
        cost_estimate=cost_estimate,
        progress_total=pos_count + neg_count,
    )


def get_eval_run(pk: int) -> KsEvalRun | None:
    return KsEvalRun.objects.filter(pk=pk).first()


def list_eval_runs(module_name: str = "") -> list[KsEvalRun]:
    queryset = KsEvalRun.objects.order_by("-created_at")
    if module_name:
        queryset = queryset.filter(module_name=module_name)
    return list(queryset)


def running_eval_run(module_name: str) -> KsEvalRun | None:
    return (
        KsEvalRun.objects.filter(
            module_name=module_name,
            status__in=[KsEvalRun.STATUS_PENDING, KsEvalRun.STATUS_RUNNING],
        )
        .order_by("-created_at")
        .first()
    )


def mark_eval_running(pk: int) -> None:
    KsEvalRun.objects.filter(pk=pk).update(status=KsEvalRun.STATUS_RUNNING)


def set_eval_progress(pk: int, done: int, total: int) -> None:
    KsEvalRun.objects.filter(pk=pk).update(progress_done=done, progress_total=total)


def set_eval_phase(pk: int, phase: str) -> None:
    KsEvalRun.objects.filter(pk=pk).update(phase=phase)


def add_eval_query(pk: int, **fields: object) -> KsEvalQuery:
    return KsEvalQuery.objects.create(run_id=pk, **fields)


def finish_eval_run(pk: int, *, status: str, metrics: dict | None = None, error: str = "") -> None:
    KsEvalRun.objects.filter(pk=pk).update(
        status=status,
        metrics=metrics or {},
        error=error,
    )
