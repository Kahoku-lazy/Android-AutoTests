## MODIFIED Requirements

### Requirement: System locator projects

The system SHALL provide exactly one locator project with code `android`. Users MUST NOT create, rename, or delete this project. The project list API SHALL seed the missing project on read.

#### Scenario: List locked projects

- **WHEN** a logged-in user requests `GET /api/elements/projects/`
- **THEN** the response envelope is `{status: true, data}` containing exactly one project with code `android`

#### Scenario: Mutating projects is rejected

- **WHEN** a client calls `POST`, `PATCH`, or `DELETE` on `/api/elements/projects/` or a project detail
- **THEN** the server responds with HTTP 405 and a Chinese message

### Requirement: Project workspace tree

The project SHALL expose an unlimited-depth directory tree. Tree nodes SHALL be directories or files. File `kind` SHALL be `page`. Dragging a directory into its own descendant MUST return HTTP 409.

#### Scenario: Create directory and file under project

- **WHEN** the user creates a directory then creates a `page` file under it
- **THEN** `GET /api/elements/projects/android/tree/` includes both nodes under the correct parent

#### Scenario: Illegal directory move

- **WHEN** the user moves a directory under one of its descendants
- **THEN** the move fails with HTTP 409 and Chinese message

### Requirement: Leaf identity preserved on migration

Data migration SHALL place existing Android pages into the corresponding system project directories derived from former folders, preserving leaf primary keys whenever possible.

#### Scenario: Existing page id still fetchable

- **WHEN** migration completes for an existing Android page id N
- **THEN** `GET /api/elements/pages/N` (or equivalent leaf read) still returns that page and its elements

## REMOVED Requirements

### Requirement: Legacy group write path retired

**Reason**: 该需求约束的对象（`WebGroup` / `ApiGroup` 及其写端点）随 Web/API 域整体下线而删除，不再存在需要「写端点返回 HTTP 410」保护的过渡态。

**Migration**: 元素定位的结构编辑一律走 `/api/elements/directories/` 与 `/api/elements/move/`；原 web-groups / api-groups 写路径及其 410 语义不再是需要保持的契约。
