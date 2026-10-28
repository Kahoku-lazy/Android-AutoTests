## 1. RAG 寮曟搸

- [x] 1.1 鏂板 `engines/agents/rag/config.py`锛氭暟鎹洰褰曘€佺储寮曠洰褰曘€佸祵鍏ユā鍨嬨€乼op_k/闃堝€笺€?- [x] 1.2 鏂板 `engines/agents/rag/store.py`锛歚SQLiteVectorStore` 瀹炵幇 `VectorStoreBase`銆?- [x] 1.3 鏂板 `engines/agents/rag/indexer.py`锛歍extParser + ApproxTokenChunker + KnowledgeBase锛屾寜鏂囦欢澧為噺閲嶅缓銆?- [x] 1.4 鏂板 `engines/agents/rag/service.py`锛歚RagService.search/build_context`锛屽け璐ラ檷绾с€?- [x] 1.5 鏂板 `engines/agents/rag/AGENTS.md` 涓?`__init__.py`銆?
## 2. 鎺ュ叆 Pipeline

- [x] 2.1 `DeepSeekAnswerer` 鎺ユ敹 `RagService`锛屾瘡杞敞鍏ユ绱笂涓嬫枃銆?- [x] 2.2 `PipelineVoiceSession` 鍒涘缓 RAG 鏈嶅姟骞剁‘淇濈储寮曪紱澶辫触涓嶉樆濉炪€?- [x] 2.3 `.env.example` 澧炲姞 RAG 閰嶇疆銆?
## 3. 楠岃瘉

- [x] 3.1 鐢?`D:\Govee\data\rag_data` 寤虹储寮曪紝鏌ヨ鈥滈暱鎸夊紑鍏虫寜閿?绉掆€濆懡涓寜閿枃妗ｃ€?- [x] 3.2 DeepSeek 甯?RAG 鍥炵瓟鍖呭惈璧勬枡鍐呭锛涙棤鍛戒腑闂姝ｅ父鍥炵瓟銆?- [x] 3.3 Pipeline 鐪熷疄 WAV 浠嶈窇閫氾紝RAG 澶辫触鏃跺彲闄嶇骇銆?- [x] 3.4 ruff / pytest / `manage.py check` / 鍓嶇 typecheck銆?- [x] 3.5 `openspec validate add-rag-voice-llm --strict` 骞跺綊妗ｃ€?
