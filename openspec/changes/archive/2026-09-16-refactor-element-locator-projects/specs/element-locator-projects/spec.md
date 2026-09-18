## ADDED Requirements

### Requirement: System locator projects

The system SHALL provide exactly three locator projects with codes `android`, `web`, and `api`. Users MUST NOT create, rename, or delete these projects. The project list API SHALL seed missing projects on read.

#### Scenario: List locked projects

- **WHEN** a logged-in user requests `GET /api/elements/projects/`
- **THEN** the response envelope is `{status: true, data}` containing three projects with fixed names Android / Web / API

#### Scenario: Mutating projects is rejected

- **WHEN** a client calls `POST`, `PATCH`, or `DELETE` on `/api/elements/projects/` or a project detail
- **THEN** the server responds with HTTP 405 and a Chinese message

### Requirement: Project workspace tree

Each project SHALL expose an unlimited-depth directory tree. Tree nodes SHALL be directories or files. File `kind` SHALL be `page` for android, `web_element` for web, and `api_endpoint` for api. Dragging a directory into its own descendant MUST return HTTP 409.

#### Scenario: Create directory and file under project

- **WHEN** the user creates a directory then creates a file of the project's leaf type under it
- **THEN** `GET /api/elements/projects/{code}/tree/` includes both nodes under the correct parent

#### Scenario: Illegal directory move

- **WHEN** the user moves a directory under one of its descendants
- **THEN** the move fails with HTTP 409 and Chinese message

### Requirement: Legacy group write path retired

After migration, creating or updating locator structure via `WebGroup` / `ApiGroup` / `Page.is_folder` write endpoints MUST NOT succeed for workspace edits. Those write endpoints SHALL return HTTP 410. Read-only consumers MAY still receive a projected directory tree for web groups where needed.

#### Scenario: Create web group returns gone

- **WHEN** a client posts to create a web group
- **THEN** the server responds HTTP 410 with a Chinese message directing the client to use directories

### Requirement: Leaf identity preserved on migration

Data migration SHALL place existing Android pages, Web elements, and API endpoints into the corresponding system project directories derived from former folders/groups, preserving leaf primary keys whenever possible.

#### Scenario: Existing page id still fetchable

- **WHEN** migration completes for an existing Android page id N
- **THEN** `GET /api/elements/pages/N` (or equivalent leaf read) still returns that page and its elements
