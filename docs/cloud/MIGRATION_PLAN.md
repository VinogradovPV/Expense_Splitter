# CLOUD.0 — YAML To PostgreSQL Migration Plan

Дата: 2026-07-01
Статус: migration design; migration scripts не создавались.

## Цель

Описать безопасный путь миграции из текущих локальных YAML-файлов в PostgreSQL со stable IDs,
сохраняя offline YAML mode.

## Source Files

- `data/participants.yaml`
- `data/categories.yaml`
- `data/purchases.yaml`
- `data/settlement_periods.yaml`

Эти файлы являются пользовательскими локальными данными и не коммитятся.

## Migration Modes

### Dry Run

Reads YAML, builds mapping, validates counts/totals, reports warnings. Does not write PostgreSQL.

### Import

Writes tenant/users/participants/categories/purchases/periods/reports/audit data into PostgreSQL
inside transaction.

### Rollback

For MVP import rollback means database transaction rollback before commit. After commit, rollback
requires restore from database backup or deleting imported tenant if no production activity occurred.

## Stable ID Generation

Generate stable IDs for:

- tenant;
- participants;
- categories;
- purchases;
- settlement periods;
- reports/audit rows if imported.

Keep legacy values:

- YAML purchase `id` -> `legacy_purchase_id`;
- YAML settlement period `id` -> `legacy_settlement_period_id` / `period_code`;
- participant/category display names -> aliases.

## Alias Mapping

For each participant:

- create `participant_id`;
- keep current name as `display_name`;
- create `participant_aliases` row with `source='yaml_migration'`.

For rename history, if available later:

- add old display names as aliases;
- do not overwrite historical settlement snapshot labels.

## Conflict Handling

Conflicts:

- two participants normalize to same name;
- purchase references unknown payer;
- purchase participant name is unknown;
- category string is missing from category list;
- settlement period references missing purchase id;
- settlement settlement references unknown participant.

Rules:

- dry-run must report conflicts;
- import must not silently guess;
- user/admin must provide mapping file or manual fix;
- unresolved critical conflicts block import.

## Migration Warnings

Warnings should include:

- `unknown_category_created`;
- `missing_purchase_for_period`;
- `ambiguous_participant_name`;
- `unknown_participant_reference`;
- `undated_purchase`;
- `period_snapshot_incomplete`;
- `legacy_id_duplicate`.

Warnings become:

- dry-run report output;
- optional `audit_log` metadata;
- migration summary document.

## Import Steps

1. Validate YAML parse and schema compatibility.
2. Create import backup of YAML files or require existing backup.
3. Create tenant.
4. Import participants and aliases.
5. Import categories.
6. Import purchases.
7. Import purchase participants.
8. Import settlement periods.
9. Import settlement period purchase snapshots.
10. Validate totals/counts.
11. Write `migration.imported` audit event.
12. Commit transaction.

## Validation Totals And Counts

Dry-run/import must compare:

- participant count;
- category count;
- purchase count;
- settlement period count;
- total purchase amount;
- total amount by period;
- purchase IDs linked to periods;
- settled/open counts.

Any mismatch is a blocker unless explicitly classified as warning.

## Snapshot Rules

Historical settlement period migration must preserve:

- original period ID as legacy code;
- date range;
- closed/reopened status;
- total amount;
- snapshot settlements;
- display labels at migration time if snapshot lacks labels.

Do not recalculate historical settlements during migration unless no snapshot exists, and then mark
metadata warning.

## Backup Strategy

Before import:

- copy YAML files to ignored backup directory;
- record checksum in migration summary;
- create database backup or use empty target database.

After import:

- keep YAML offline mode intact;
- do not delete local YAML;
- do not change desktop defaults automatically.

## Rollback Strategy

Dry-run: no rollback needed.

Import before commit: transaction rollback.

Import after commit:

- if tenant is isolated and unused, delete imported tenant in controlled admin flow;
- otherwise restore database backup;
- rotate credentials only if logs/secrets were exposed.

## Output

Migration tool should produce:

- summary JSON;
- human-readable Markdown;
- warnings list;
- ID mapping file for audit/admin review.

## Out Of Scope For CLOUD.0

- migration script code;
- actual PostgreSQL connection;
- modifying user YAML;
- importing real local data.
