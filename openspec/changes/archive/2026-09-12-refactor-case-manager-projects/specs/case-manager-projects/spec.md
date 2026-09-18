## Purpose

为测试人员提供按项目组织的文档型用例管理：先建项目，再在无限目录树中维护统一表单的用例，不再按 Android/Web/API/业务拆模块，也不驱动自动执行。

## ADDED Requirements

### Requirement: Project list empty state
The system SHALL show the case-manager entry as a single navigation item that opens the project list. When the current user has no projects, the page MUST prompt the user to create a project and MUST NOT show a case tree or case form.

#### Scenario: First visit with no projects
- **WHEN** an authenticated user opens `/cases` and has zero projects
- **THEN** the UI shows an empty state with a create-project action and does not enter a project workspace

#### Scenario: Create first project
- **WHEN** the user submits a valid project name
- **THEN** the system creates the project and the list shows a project card that navigates to that project's workspace

### Requirement: Project cards
The system SHALL list the current user's projects as cards. Each card MUST show at least the project name and creation time. Clicking a card MUST open that project's workspace.

#### Scenario: Open workspace from card
- **WHEN** the user clicks a project card
- **THEN** the app navigates to `/cases/projects/{projectId}` for that project

#### Scenario: User isolation
- **WHEN** user A lists projects
- **THEN** projects created by other users MUST NOT appear

### Requirement: Unlimited directory tree
Inside a project workspace, the system SHALL present a directory tree of unlimited depth. The user MUST be able to create directories, create cases, multi-select cases, select all visible cases, drag directories, drag cases, delete a single node, and batch-delete selected cases.

#### Scenario: Create nested directory
- **WHEN** the user creates a directory under an existing directory
- **THEN** the tree shows the new directory as a child of that parent

#### Scenario: Case at project root
- **WHEN** the user creates a case without choosing a directory
- **THEN** the case appears at the project root of the tree

#### Scenario: Drag directory into descendant forbidden
- **WHEN** the user drops a directory onto one of its descendants
- **THEN** the server rejects the move with HTTP 409 and a Chinese message, and the tree is unchanged

#### Scenario: Drag case into directory
- **WHEN** the user drops a case onto a directory in the same project
- **THEN** the case's parent directory is updated and sort order is persisted

#### Scenario: Batch delete cases
- **WHEN** the user selects multiple cases and confirms batch delete
- **THEN** those cases are removed and unselected directories are not deleted

#### Scenario: Delete directory cascades
- **WHEN** the user confirms deleting a directory
- **THEN** that directory, its descendant directories, and nested cases are deleted

### Requirement: No preview; form only on case click
The system SHALL NOT provide a case preview pane. The unified case form MUST appear only after the user selects a case (including a newly created case that is immediately selected).

#### Scenario: Workspace with no selection
- **WHEN** the user enters a project workspace without a selected case
- **THEN** the right pane shows a prompt to click a case and does not show the form fields

#### Scenario: Open case
- **WHEN** the user clicks a case node
- **THEN** the right pane shows the unified document form for that case

### Requirement: Unified document case form
The system SHALL persist document cases with the following fields: auto-generated unique case ID (read-only); test type required single choice among APP, WEB, API, FUNC; business type required single choice among 家电, 照明, APP; created_at auto on create; title required; module optional; precondition optional; steps required text; expected_result required text; updated_at auto on each successful save. Display timestamps MUST use the format `YYYY-MM-DD-HH:mm:ss` (example `2026-09-09-12:00:24`). Steps and expected results MUST be independent text blocks (not paired step rows).

#### Scenario: Auto ID and created time
- **WHEN** a case is created
- **THEN** the form shows a platform-generated unique ID and a created timestamp; the user cannot edit those two fields

#### Scenario: Required validation
- **WHEN** the user saves with empty title, empty steps, or empty expected result
- **THEN** the client MUST NOT send the request and MUST show field errors

#### Scenario: Save updates modified time
- **WHEN** the user successfully saves an existing case
- **THEN** `updated_at` changes and is displayed in the agreed timestamp format

#### Scenario: Test and business type enums
- **WHEN** the user sets test type and business type
- **THEN** only APP/WEB/API/FUNC and 家电/照明/APP respectively are accepted; other values MUST be rejected by the API

### Requirement: Standard case APIs
The system SHALL expose project, directory, definition, move, and batch-delete endpoints under `/api/cases/` using the envelope `{status, data}` on success and `{status, message}` on failure. Writes MUST go through `case_manager` `api.py`. Responses MUST use snake_case JSON.

#### Scenario: Create project via API
- **WHEN** `POST /api/cases/projects/` is called with a valid name by an authenticated user
- **THEN** the response is `{status: true, data}` containing the project

#### Scenario: Get project tree
- **WHEN** `GET /api/cases/projects/{id}/tree/` is called by the project owner
- **THEN** the data contains nested directories and cases for that project only

#### Scenario: Unauthorized project
- **WHEN** a user requests another user's project by id
- **THEN** the API returns 404 or 403 and does not leak the tree

### Requirement: Remove four-module executable cases
The system SHALL NOT present Android UI, Web, API, or business-function as separate case-manager modules. Legacy routes `/cases/ui`, `/cases/web`, `/cases/api`, `/cases/storage` and their new/edit editors MUST redirect or be removed. Legacy four-type definition APIs MUST NOT remain as supported contracts. Existing four-type rows MUST be deleted by migration. The system SHALL NOT offer case preview, YAML export, step-type catalog, or case-editing WebSocket for this module.

#### Scenario: Old sidebar paths
- **WHEN** a user opens `/cases/ui` (or web/api/storage)
- **THEN** they are redirected to `/cases` and do not see a four-tab case manager

#### Scenario: Old definition endpoints gone
- **WHEN** a client calls a removed four-type definition path such as `/api/cases/web/definitions`
- **THEN** the server responds 404

### Requirement: Document cases are not executable
The test runner MUST NOT treat these document cases as runnable step definitions. Dashboard case counts MUST use the new document/project model rather than four executable types.

#### Scenario: Runner cannot execute document case
- **WHEN** the test runner is asked to execute a document case id
- **THEN** it MUST fail with a user-facing message that the case is documentation-only (or offer an empty selectable list)

## REMOVED Requirements

### Requirement: Four independent case-type workspaces
**Reason**: Replaced by a single project-based document workspace.  
**Migration**: Use `/cases` projects and unified definitions; do not keep per-type trees.

### Requirement: Executable steps_json editors and edit lock
**Reason**: Cases are documentation-only in this change.  
**Migration**: Structured UI/API/Web/Storage editors, edit-lock WS, and YAML export are removed; later execution work is a separate change.
