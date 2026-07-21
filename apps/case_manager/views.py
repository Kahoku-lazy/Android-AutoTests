"""case-manager HTTP views — facade re-exporting from sub-modules."""

# Shared helper (no circular deps)
from .views_helpers import resolve_username as _resolve_username  # noqa: F401 — compat alias

# Directory endpoints
from .views_directories import (  # noqa: E402, F401
    directory_list,
    directory_create,
    directory_detail,
    directory_batch_move,
    directory_permission,
)

# UI automation endpoints
from .views_ui import (  # noqa: E402, F401
    definitions_handler,
    definition_detail,
    definitions_batch,
    export_yaml,
    list_exports,
    download_export,
)

# Lock & visibility endpoints
from .views_lock import (  # noqa: E402, F401
    acquire_edit_lock,
    release_edit_lock,
    case_lock,
    case_unlock,
    set_visibility,
)
