"""Initialize the knowledge base by loading all project documents."""
import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django; django.setup()

from agentscope_service.rag.loader import load_all_documents
from agentscope_service.rag.document_store import add_documents, clear_collection

if __name__ == '__main__':
    if '--reset' in sys.argv:
        clear_collection()
        print('Knowledge base cleared.')

    docs = load_all_documents()
    count = add_documents(docs)
    print(f'Knowledge base initialized: {count} documents indexed.')
