## 1. 寮曟搸

- [x] 1.1 `config.py` 澧炲姞 `pipeline` 妯″紡銆乣select_mode()`銆乸ipeline LLM/TTS 閰嶇疆涓庢牎楠岋紱楠岃瘉锛氶厤缃?妯″紡閫夋嫨鍗曟祴銆?- [x] 1.2 鏂板 `pipeline_llm.py`锛欴eepSeek Flash 娴佸紡鍥炵瓟 + 澶氳疆鍘嗗彶锛涢獙璇侊細鐪熷疄 DeepSeek 璋冪敤銆?- [x] 1.3 鏂板 `pipeline_tts.py`锛歈wen-TTS HTTP 鈫?WAV 鈫?24k PCM16锛涢獙璇侊細鐪熷疄 TTS 杩斿洖鍙挱鏀?PCM銆?- [x] 1.4 鏂板 `pipeline.py`锛欰SR 浜嬩欢寰幆銆佺敤鎴疯浆鍐欍€丏eepSeek銆乀TS銆佹墦鏂€佹棩蹇楋紱楠岃瘉锛氱湡瀹?WAV 璧伴€氥€?- [x] 1.5 `LiveTranslateRealtimeModel` 鏀寔 `output_modalities=["text"]` 浣滀负 ASR锛涢獙璇侊細ASR 鍙嚭婧愯銆?
## 2. 鎺ュ叆灞?
- [x] 2.1 consumer 璇诲彇 `mode` 鏌ヨ鍙傛暟锛屾寜妯″紡閫?`RealtimeVoiceSession` / `PipelineVoiceSession`锛涢獙璇侊細omni 涓?pipeline 鍚勫缓涓€娆¤繛鎺ャ€?- [x] 2.2 鏇存柊 `.env.example` 涓庢ā鍧?AGENTS锛涢獙璇侊細鍙橀噺鍚嶄笌 config 涓€鑷淬€?
## 3. 鍓嶇

- [x] 3.1 澧炲姞璺嚎閫夋嫨鍣紙Omni 鐩磋繛 / ASR + DeepSeek + TTS锛夛紝`start(mode)` 鎷?`mode` 鏌ヨ锛涢獙璇侊細typecheck/build銆?- [x] 3.2 椤甸潰鍓爣棰?妯″紡琛岄殢璺嚎鍙樺寲锛涢獙璇侊細娴忚鍣ㄦ埅鍥俱€?- [x] 3.3 淇濈暀楹﹀厠椋庤澶囬€夋嫨鍣ㄣ€?
## 4. 楠岃瘉

- [x] 4.1 ruff / pytest / `manage.py check`銆?- [x] 4.2 鐪熷疄 WAV锛歱ipeline 璺戦€氱敤鎴疯浆鍐?+ DeepSeek 鍥炵瓟 + TTS 闊抽锛沗ready` 涓?pipeline銆?- [x] 4.3 `openspec validate add-pipeline-voice-mode --strict` 骞跺綊妗ｃ€?
