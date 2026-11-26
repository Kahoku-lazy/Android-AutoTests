from __future__ import annotations

import json

from datetime import datetime

_POSITIVE_PROMPT = (
    "你是评测题集生成器。下面是若干资料片段（JSON 数组，每个元素含 i 与 text）。"
    "请为每个片段生成一个仅凭该片段内容就能回答的中文问题。"
    "要求：口语化、换述表达、不得照抄原文句子、不要出现「片段」「根据资料」字样。"
    '只输出 JSON 数组，格式：[{"i":0,"q":"问题"}]，不要输出其它内容。'
)

_NEGATIVE_PROMPT = (
    "某知识库的主题是：{description}。它包含的文档标题有：{sources}。"
    "请生成 {count} 个与该知识库主题完全无关的中文问题（库里不可能查到答案）。"
    '只输出 JSON 数组，格式：["问题1","问题2"]，不要输出其它内容。'
)

_STAMP = "%Y-%m-%d_%H-%M-%S.%f"


def extract_text(response) -> str:
    parts = []
    for block in response.content or []:
        if isinstance(block, dict):
            block_type = block.get("type")
            text = block.get("text")
        else:
            block_type = getattr(block, "type", "")
            text = getattr(block, "text", "")
        if block_type == "text":
            parts.append(str(text or ""))
    return "".join(parts)


def parse_json_payload(text: str):
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
    try:
        return json.loads(cleaned)
    except (TypeError, ValueError):
        return None


def _usage_event(response, *, api_key_env: str, model_name: str, round_index: int) -> dict | None:
    usage = getattr(response, "usage", None)
    if usage is None:
        return None
    return {
        "round": f"chat-{round_index}",
        "api_key_env": api_key_env,
        "model_name": model_name,
        "input_tokens": int(getattr(usage, "input_tokens", 0) or 0),
        "output_tokens": int(getattr(usage, "output_tokens", 0) or 0),
        "cache_input_tokens": int(getattr(usage, "cache_input_tokens", 0) or 0),
        "cache_creation_input_tokens": int(getattr(usage, "cache_creation_input_tokens", 0) or 0),
        "started_at": datetime.now().strftime(_STAMP)[:-3],
    }


async def _call(model, prompt: str):
    from agentscope.message import UserMsg

    return await model([UserMsg(name="evaluator", content=prompt)])


async def generate_positive_questions(
    model,
    chunks: list[dict],
    *,
    api_key_env: str,
    model_name: str,
    batch_size: int = 5,
) -> tuple[list[dict], list[dict]]:
    questions: list[dict] = []
    usages: list[dict] = []
    round_index = 0
    for start in range(0, len(chunks), batch_size):
        batch = chunks[start : start + batch_size]
        payload = [{"i": index, "text": chunk["text"][:800]} for index, chunk in enumerate(batch)]
        prompt = _POSITIVE_PROMPT + "\n" + json.dumps(payload, ensure_ascii=False)
        round_index += 1
        response = await _call(model, prompt)
        event = _usage_event(
            response, api_key_env=api_key_env, model_name=model_name, round_index=round_index
        )
        if event:
            usages.append(event)
        parsed = parse_json_payload(extract_text(response))
        if not isinstance(parsed, list):
            continue
        for item in parsed:
            if not isinstance(item, dict):
                continue
            index = item.get("i")
            question = str(item.get("q") or "").strip()
            if isinstance(index, int) and 0 <= index < len(batch) and question:
                questions.append({"question": question, "chunk": batch[index]})
    return questions, usages


async def generate_negative_questions(
    model,
    description: str,
    sources: list[str],
    count: int,
    *,
    api_key_env: str,
    model_name: str,
) -> tuple[list[str], list[dict]]:
    if count <= 0:
        return [], []
    prompt = _NEGATIVE_PROMPT.format(
        description=description,
        sources="、".join(sources[:20]) or "（无）",
        count=count,
    )
    response = await _call(model, prompt)
    usages = []
    event = _usage_event(response, api_key_env=api_key_env, model_name=model_name, round_index=1)
    if event:
        usages.append(event)
    parsed = parse_json_payload(extract_text(response))
    if not isinstance(parsed, list):
        return [], usages
    questions = [str(item).strip() for item in parsed if str(item).strip()]
    return questions[:count], usages
