"""case-manager public API — write-path facade for cross-app / View / Tool callers."""

from .api_definitions import (
    batch_delete_definitions,
    create_definition,
    delete_definition,
    get_definition,
    serialize_definition,
    update_definition,
)
from .api_directories import (
    create_directory,
    delete_directory,
    move_item,
    serialize_directory,
    update_directory,
)
from .api_files import (
    create_file,
    delete_file,
    get_file,
    get_file_sheet,
    list_file_cases,
    serialize_file,
    update_file,
)
from .api_ids import next_case_id
from .api_projects import (
    ConflictError,
    create_project,
    delete_project,
    get_project,
    get_project_tree,
    list_projects,
    serialize_project,
    update_project,
)
from .models import CaseDirectory, CaseFile, CaseProject, TestDefinition

__all__ = [
    "CaseDirectory",
    "CaseFile",
    "CaseProject",
    "ConflictError",
    "TestDefinition",
    "batch_delete_definitions",
    "create_definition",
    "create_directory",
    "create_file",
    "create_project",
    "delete_definition",
    "delete_directory",
    "delete_file",
    "delete_project",
    "get_definition",
    "get_file",
    "get_file_sheet",
    "get_project",
    "get_project_tree",
    "list_file_cases",
    "list_projects",
    "move_item",
    "next_case_id",
    "serialize_definition",
    "serialize_directory",
    "serialize_file",
    "serialize_project",
    "update_definition",
    "update_directory",
    "update_file",
    "update_project",
]
