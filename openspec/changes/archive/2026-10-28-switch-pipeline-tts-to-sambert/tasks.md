## 1. TTS 閫傞厤

- [x] 1.1 `pipeline_tts.py` 鏂板 `SambertTts`锛圵ebSocket run-task銆丳CM 鎷兼帴銆佸け璐ユ姏 RuntimeError锛夛紱楠岃瘉锛氱湡瀹炰腑鏂囧悎鎴愩€?- [x] 1.2 `config.py` 澧炲姞 `pipeline_tts_provider`銆侀粯璁?`sambert` / `sambert-zhichu-v1` / 鐭ュ帹锛屽苟淇濈暀 qwen 榛樿鍊硷紱楠岃瘉锛氶厤缃崟娴嬨€?- [x] 1.3 `pipeline.py` 鎸?provider 閫?TTS锛宺eady 鏄剧ず鏂版ā鍨嬩笌闊宠壊锛涢獙璇侊細Pipeline 绔埌绔€?
## 2. 閰嶇疆涓庢枃妗?
- [x] 2.1 `.env.example` 榛樿 Sambert锛屼繚鐣?Qwen-TTS 绀轰緥锛涢獙璇侊細鍙橀噺鍚嶄笌 config 涓€鑷淬€?- [x] 2.2 鏇存柊寮曟搸/鍓嶇 AGENTS 鐨?TTS 璇存槑銆?
## 3. 楠岃瘉

- [x] 3.1 `sambert-zhichu-v1` 鐪熷疄鍚堟垚杩斿洖 PCM16 24k銆?- [x] 3.2 鐪熷疄 WAV 璧?Pipeline锛氱敤鎴疯浆鍐?+ DeepSeek 鍥炵瓟 + Sambert 闊抽锛沗ready.model` 鍚?sambert銆?- [x] 3.3 ruff / pytest / `manage.py check` / 鍓嶇 build銆?- [x] 3.4 `openspec validate switch-pipeline-tts-to-sambert --strict` 骞跺綊妗ｃ€?
