"""case-manager public API — backward-compatible facade.

All real implementations live in api_directories.py / api_ui.py / api_storage.py / api_api.py / api_lock.py.
This file re-exports everything so existing cross-app consumers (test_runner, dashboard, agentscope_service)
continue to work without changes.
"""

from .models import TestDefinition, CaseDirectory

# Directory API
from .api_directories import (  # noqa: E402
    get_directory_tree,
    create_directory,
    update_directory,
    delete_directory,
    batch_move_items,
)

# UI automation case API
from .api_ui import (  # noqa: E402
    ConflictError,
    _parse_datetime,
    get_enabled_definitions,
    get_definition,
    save_definition,
    batch_save_definitions,
)

# Storage case API
from .api_storage import (  # noqa: E402
    get_storage_definitions,
    get_storage_definition,
    save_storage_definition,
    batch_save_storage_definitions,
)

# API test case API
from .api_api import (  # noqa: E402
    get_api_definitions,
    get_api_definition,
    save_api_definition,
    batch_save_api_definitions,
)

# Web automation case API
from .api_web import (  # noqa: E402
    get_web_definitions,
    get_web_definition,
    save_web_definition,
    batch_save_web_definitions,
)

# Lock helpers (generalized cross-type)
from .api_lock import (  # noqa: E402
    find_case_across_types,
    get_case_for_lock,
)

__all__ = [
    # Models
    "TestDefinition",
    "CaseDirectory",
    # Directory
    "get_directory_tree",
    "create_directory",
    "update_directory",
    "delete_directory",
    "batch_move_items",
    # UI automation
    "get_enabled_definitions",
    "get_definition",
    "save_definition",
    "batch_save_definitions",
    # Storage
    "get_storage_definitions",
    "get_storage_definition",
    "save_storage_definition",
    "batch_save_storage_definitions",
    # API testing
    "get_api_definitions",
    "get_api_definition",
    "save_api_definition",
    "batch_save_api_definitions",
    # Web automation
    "get_web_definitions",
    "get_web_definition",
    "save_web_definition",
    "batch_save_web_definitions",
    # Lock
    "find_case_across_types",
    "get_case_for_lock",
    # Utility
    "ConflictError",
    "_parse_datetime",
]
