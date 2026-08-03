"""Initialize the knowledge base by loading all project documents.

Usage:
    python manage.py init_knowledge_base          # incremental (adds new docs)
    python manage.py init_knowledge_base --reset  # clear + full reindex
"""

from django.core.management.base import BaseCommand

from apps.ai_assistant.agent_scope.rag_service import (
    add_documents,
    clear_collection,
    load_all_documents,
)


class Command(BaseCommand):
    help = "Initialize the ChromaDB knowledge base from dev_docs/"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Clear existing collection before indexing",
        )

    def handle(self, **options):
        if options["reset"]:
            clear_collection()
            self.stdout.write("Knowledge base cleared.")

        docs = load_all_documents(force=True)
        count = add_documents(docs)
        self.stdout.write(
            self.style.SUCCESS(f"Knowledge base initialized: {count} documents indexed.")
        )
