import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.config.settings")

if os.environ.get("RUN_MAIN") != "true":
    os.environ.setdefault("DJANGO_AUTORELOAD_PARENT", "1")
else:
    os.environ.pop("DJANGO_AUTORELOAD_PARENT", None)

import django

django.setup()

from daphne.cli import CommandLineInterface
from django.utils.autoreload import run_with_reloader


def main() -> None:
    CommandLineInterface().run(sys.argv[1:])


if __name__ == "__main__":
    run_with_reloader(main)
