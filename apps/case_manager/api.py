"""case-manager public API — backward-compatible facade.

All real implementations live in api_directories.py / api_ui.py / api_storage.py / api_api.py / api_lock.py.
This file re-exports everything so existing cross-app consumers (test_runner, dashboard, agentscope_service)
continue to work without changes.
"""

__all__ = [
    "CaseDirectory",
    "ConflictError",
    "TestDefinition",
    "batch_move_items",
    "batch_save_api_definitions",
    "batch_save_definitions",
    "batch_save_storage_definitions",
    "batch_save_web_definitions",
    "create_directory",
    "delete_directory",
    "find_case_across_types",
    "get_api_definition",
    "get_api_definitions",
    "get_case_for_lock",
    "get_definition",
    "get_directory_tree",
    "get_enabled_definitions",
    "get_storage_definition",
    "get_storage_definitions",
    "get_web_definition",
    "get_web_definitions",
    "save_api_definition",
    "save_definition",
    "save_storage_definition",
    "save_web_definition",
    "update_directory",
]

# API test case API
from .api_api import (  # noqa: E402
    batch_save_api_definitions,
    get_api_definition,
    get_api_definitions,
    save_api_definition,
)

# Directory API
from .api_directories import (  # noqa: E402
    batch_move_items,
    create_directory,
    delete_directory,
    get_directory_tree,
    update_directory,
)

# Lock helpers (generalized cross-type)
from .api_lock import (  # noqa: E402
    find_case_across_types,
    get_case_for_lock,
)

# Storage case API
from .api_storage import (  # noqa: E402
    batch_save_storage_definitions,
    get_storage_definition,
    get_storage_definitions,
    save_storage_definition,
)

# UI automation case API
from .api_ui import (  # noqa: E402
    ConflictError,
    batch_save_definitions,
    get_definition,
    get_enabled_definitions,
    save_definition,
)

# Web automation case API
from .api_web import (  # noqa: E402
    batch_save_web_definitions,
    get_web_definition,
    get_web_definitions,
    save_web_definition,
)
from .models import CaseDirectory, TestDefinition
