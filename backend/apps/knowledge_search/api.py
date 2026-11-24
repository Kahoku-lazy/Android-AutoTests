"""知识库模块登记写入口：CRUD 与校验，唯一写点。

校验规则与引擎库目录一致（库名正则、资料目录存在可读、启用库目录隔离）；
校验失败抛 ValueError，由 View 层转 400，绝不落库。
"""

from __future__ import annotations

import os
import re

from pathlib import Path

from .models import KnowledgeModule, KsEvalQuery, KsEvalRun, RetrievalSettings

_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def list_modules() -> list[KnowledgeModule]:
    """
    列出全部模块登记。

    Returns:
        按库名排序的模块列表。
    """
    return list(KnowledgeModule.objects.order_by("name"))


def get_module(module_id: int) -> KnowledgeModule | None:
    """
    按主键取一条模块登记。

    Args:
        module_id: 模块主键。

    Returns:
        模块；不存在时 None。
    """
    return KnowledgeModule.objects.filter(pk=module_id).first()


def create_module(
    *,
    name: str,
    description: str,
    data_dir: str,
    enabled: bool = True,
) -> KnowledgeModule:
    """
    新增一个模块登记；校验失败不落库。

    Args:
        name: 库名，须匹配 ^[a-z][a-z0-9_]*$ 且唯一。
        description: 模块说明，非空。
        data_dir: 服务器本地资料目录，须为已存在、可读的绝对路径。
        enabled: 是否启用。

    Returns:
        新建的模块。

    Raises:
        ValueError: 库名非法或重名、说明为空、目录不合法、启用库目录冲突。
    """
    fields = _validate_fields(
        name=name, description=description, data_dir=data_dir, enabled=enabled
    )
    if KnowledgeModule.objects.filter(name=fields["name"]).exists():
        raise ValueError(f"库名已存在：{fields['name']}")
    _check_isolation(fields["name"], Path(fields["data_dir"]), fields["enabled"])
    return KnowledgeModule.objects.create(**fields)


def update_module(module_id: int, **changes: object) -> KnowledgeModule:
    """
    编辑一个模块登记（含改路径与启停）；校验失败不落库。

    Args:
        module_id: 模块主键。
        **changes: 要改的字段（name / description / data_dir / enabled）。

    Returns:
        更新后的模块。

    Raises:
        ValueError: 模块不存在、出现未知字段、字段非法或启用库目录冲突。
    """
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
    """
    删除一个模块登记；只删登记，不碰资料目录与索引文件。

    Args:
        module_id: 模块主键。

    Returns:
        删除成功为真；模块不存在为假。
    """
    module = get_module(module_id)
    if module is None:
        return False
    module.delete()
    return True


def _validate_fields(*, name: str, description: str, data_dir: str, enabled: bool) -> dict:
    """
    校验并归一化模块字段。

    Args:
        name: 库名。
        description: 模块说明。
        data_dir: 资料目录。
        enabled: 是否启用。

    Returns:
        归一化后的字段字典（目录取 resolve 后的绝对路径）。

    Raises:
        ValueError: 任一字段不合法。
    """
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
    """
    拒绝启用库资料目录相同或互相包含。

    Args:
        name: 候选库名。
        data_dir: 候选资料目录（已 resolve）。
        enabled: 候选是否启用。
        exclude_id: 编辑时排除自身主键。

    Raises:
        ValueError: 与另一启用库目录冲突。
    """
    if not enabled:
        return
    others = KnowledgeModule.objects.filter(enabled=True)
    if exclude_id is not None:
        others = others.exclude(pk=exclude_id)
    for other in others:
        other_dir = Path(other.data_dir)
        if data_dir == other_dir or data_dir in other_dir.parents or other_dir in data_dir.parents:
            raise ValueError(f"启用库资料目录冲突：{name} 与 {other.name}")


# ── 检索配置：全表一行，唯一写点 ──


def get_retrieval_settings() -> RetrievalSettings | None:
    """
    取全局检索配置。

    Returns:
        唯一一行；尚未种入时为 None。
    """
    return RetrievalSettings.objects.order_by("id").first()


def save_retrieval_settings(
    *,
    embedding_model_id: int,
    top_k: int,
    score_threshold: float,
    chunk_size: int,
    chunk_overlap: int,
) -> tuple[RetrievalSettings, bool]:
    """
    保存全局检索配置。切块参数变化时 index_epoch 加一。

    Args:
        embedding_model_id: 向量模型配置主键，须存在且类型为 embedding。
        top_k: 默认返回条数，正整数。
        score_threshold: 相似度阈值，0 到 1。
        chunk_size: 切块大小，正整数。
        chunk_overlap: 切块重叠，须小于切块大小。

    Returns:
        (保存后的配置, 本次是否使索引失效)。

    Raises:
        ValueError: 引用的模型不存在或不是向量模型，或数值越界。
    """
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
    """引用的模型必须存在且类型为向量。不 import 对方的写库函数。"""
    from backend.apps.ai_assistant.models import AIModelConfig

    config = AIModelConfig.objects.filter(pk=int(model_id)).first()
    if config is None or config.model_kind != "embedding":
        raise ValueError("检索配置只能引用向量模型")


def _positive_int(value: object, name: str) -> int:
    """收成正整数；布尔值与小数拒绝。"""
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{name} 必须是正整数")
    return value


# ── 评测运行：唯一写点（运行器经此落库，不直接 ORM 写）──


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
    """
    创建一次评测运行（pending），快照在触发时冻结。

    Args:
        module_name: 模块库名。
        module_snapshot: 模块登记快照。
        model_config_id: 运营模型配置主键（仅追溯用）。
        model_snapshot: 模型连接参数快照。
        retrieval_snapshot: 触发时的检索配置快照；None 时不覆盖已有默认。
        pos_count: 正题数。
        neg_count: 负样本数。
        seed: 采样随机种子。
        cost_estimate: 预估 token 成本。

    Returns:
        新建的运行。
    """
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
    """
    按主键取一次评测运行。

    Args:
        pk: 运行主键。

    Returns:
        运行；不存在时 None。
    """
    return KsEvalRun.objects.filter(pk=pk).first()


def list_eval_runs(module_name: str = "") -> list[KsEvalRun]:
    """
    列出评测运行（可按模块过滤）。

    Args:
        module_name: 库名；空串列全部。

    Returns:
        按创建时间倒序的运行列表。
    """
    queryset = KsEvalRun.objects.order_by("-created_at")
    if module_name:
        queryset = queryset.filter(module_name=module_name)
    return list(queryset)


def running_eval_run(module_name: str) -> KsEvalRun | None:
    """
    取某模块进行中的运行（pending/running）。

    Args:
        module_name: 库名。

    Returns:
        进行中的运行；没有时 None。
    """
    return (
        KsEvalRun.objects.filter(
            module_name=module_name,
            status__in=[KsEvalRun.STATUS_PENDING, KsEvalRun.STATUS_RUNNING],
        )
        .order_by("-created_at")
        .first()
    )


def mark_eval_running(pk: int) -> None:
    """把运行置为 running。"""
    KsEvalRun.objects.filter(pk=pk).update(status=KsEvalRun.STATUS_RUNNING)


def set_eval_progress(pk: int, done: int, total: int) -> None:
    """更新运行进度（已完成 / 总题数）。"""
    KsEvalRun.objects.filter(pk=pk).update(progress_done=done, progress_total=total)


def set_eval_phase(pk: int, phase: str) -> None:
    """更新运行阶段（indexing / generating / retrieving），供前端等待文案。"""
    KsEvalRun.objects.filter(pk=pk).update(phase=phase)


def add_eval_query(pk: int, **fields: object) -> KsEvalQuery:
    """
    落库一道评测题及其检索结果。

    Args:
        pk: 运行主键。
        **fields: KsEvalQuery 字段。

    Returns:
        新建的题目。
    """
    return KsEvalQuery.objects.create(run_id=pk, **fields)


def finish_eval_run(pk: int, *, status: str, metrics: dict | None = None, error: str = "") -> None:
    """
    收口运行：done 带指标，failed 带可读原因。

    Args:
        pk: 运行主键。
        status: 终态（done / failed）。
        metrics: 指标字典；失败时可为 None。
        error: 失败原因。
    """
    KsEvalRun.objects.filter(pk=pk).update(
        status=status,
        metrics=metrics or {},
        error=error,
    )
