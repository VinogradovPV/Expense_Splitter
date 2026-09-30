# TG-PREP.4 — Service / Repository Boundary

Дата: 2026-07-01
Ветка: `cloud/telegram-prep`
Статус: planning boundary; код сервисов и репозиториев пока не создавался.

## Цель

Подготовить постепенное выделение service/repository слоя перед Telegram/FastAPI/Yandex Cloud
контуром, не переписывая приложение целиком и не ломая текущие Desktop GUI/CLI сценарии.

Главная идея: расчеты, закрытие периодов и генерация отчетных dataset должны работать с доменными
объектами, а не знать, пришли ли эти объекты из YAML, PostgreSQL, тестового fake repository или
будущего API.

## Target Structure

Будущая структура:

```text
src/expense_splitter/services/
  __init__.py
  purchases_service.py
  participants_service.py
  categories_service.py
  settlement_service.py
  report_service.py

src/expense_splitter/repositories/
  __init__.py
  protocols.py
  yaml_repository.py
  postgres_repository.py   # future
```

На первом шаге это должен быть тонкий слой поверх существующих функций, а не большая замена всех
модулей. Текущие `storage.py`, `directories.py`, `settlement_periods.py`, `analytics.py`,
`current_report.py` и `settlement_period_report.py` остаются источником проверенной логики.

## Boundary Principles

1. Desktop GUI и CLI продолжают работать через YAML-backed repository.
2. Telegram/FastAPI позже используют PostgreSQL-backed repository.
3. Расчеты не знают о YAML, PostgreSQL, Object Storage, Tkinter или Typer.
4. Report generation принимает dataset и output adapter/job workspace, а не пишет без контроля в
   глобальный `reports/`.
5. Backward compatibility текущего GUI/CLI не ломается: существующие команды, аргументы и папки
   остаются рабочими.
6. Сначала выделяется use-case orchestration, затем storage adapters, и только после этого
   Telegram/API.

## Repository Protocols

Минимальные protocols должны жить в `src/expense_splitter/repositories/protocols.py`.

```python
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Protocol

from expense_splitter.models import CategoryEntry, Participant, Purchase, SettlementPeriod


@dataclass(frozen=True)
class PurchasePatch:
    purchase_name: str | None = None
    date: date | None = None
    amount: Decimal | None = None
    payer: str | None = None
    participants: list[str] | None = None
    category: str | None = None
    comment: str | None = None
    settled: bool | None = None
    settlement_period_id: str | None = None


class PurchaseRepository(Protocol):
    def list_purchases(self, tenant_id: str) -> list[Purchase]: ...
    def get_purchase(self, tenant_id: str, purchase_id: str) -> Purchase | None: ...
    def add_purchase(self, tenant_id: str, purchase: Purchase) -> Purchase: ...
    def update_purchase(
        self,
        tenant_id: str,
        purchase_id: str,
        patch: PurchasePatch,
    ) -> Purchase: ...
    def replace_purchases(self, tenant_id: str, purchases: list[Purchase]) -> None: ...


class ParticipantRepository(Protocol):
    def list_participants(self, tenant_id: str) -> list[Participant]: ...
    def save_participants(self, tenant_id: str, participants: list[Participant]) -> None: ...


class CategoryRepository(Protocol):
    def list_categories(self, tenant_id: str) -> list[CategoryEntry]: ...
    def save_categories(self, tenant_id: str, categories: list[CategoryEntry]) -> None: ...


class SettlementPeriodRepository(Protocol):
    def list_periods(self, tenant_id: str) -> list[SettlementPeriod]: ...
    def get_period(self, tenant_id: str, period_id: str) -> SettlementPeriod | None: ...
    def save_period(self, tenant_id: str, period: SettlementPeriod) -> SettlementPeriod: ...
    def replace_periods(self, tenant_id: str, periods: list[SettlementPeriod]) -> None: ...
```

Почему есть `replace_*`: текущие YAML flows часто загружают список, мутируют его и сохраняют весь
файл. Это сохраняет compatibility для первого шага. Для PostgreSQL эти методы можно реализовать как
transactional batch операции или позже сузить через более точные commands.

## Unit Of Work

Close/reopen settlement period меняет purchases и periods одновременно. В YAML это сейчас два
сохранения после доменной мутации. Для server mode нужен transaction boundary.

Минимальный future protocol:

```python
class ExpenseUnitOfWork(Protocol):
    purchases: PurchaseRepository
    participants: ParticipantRepository
    categories: CategoryRepository
    settlement_periods: SettlementPeriodRepository

    def __enter__(self) -> "ExpenseUnitOfWork": ...
    def __exit__(self, exc_type, exc, tb) -> None: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
```

Для `YamlExpenseRepository` rollback может быть best-effort или no-op на первом этапе, потому что
текущий offline режим уже полагается на backup и atomic replace per file. Для PostgreSQL commit и
rollback должны быть настоящей транзакцией.

## YAML Repository

Файл: `src/expense_splitter/repositories/yaml_repository.py`.

Назначение:

- сохранить Desktop/CLI offline mode;
- обернуть текущий `storage.py`;
- скрыть `data_dir / "purchases.yaml"` от services;
- сохранить текущий backup behavior;
- использовать один `tenant_id` по умолчанию для local mode.

Предлагаемый local tenant:

```python
LOCAL_TENANT_ID = "local"
```

YAML repository может принимать `data_dir: Path` в constructor:

```python
class YamlExpenseRepository:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
```

На первом шаге `tenant_id` можно валидировать как `local` или игнорировать, но protocol уже должен
его принимать, чтобы будущий PostgreSQL adapter не менял service signatures.

## PostgreSQL Repository

Файл: `src/expense_splitter/repositories/postgres_repository.py`.

Статус: future placeholder, не реализовывать до data model этапа.

Будущие требования:

- stable tenant/user IDs;
- transaction support;
- optimistic locking или row-level locking для close/reopen;
- audit fields (`created_by`, `updated_by`, timestamps);
- миграция из YAML;
- запрет прямой привязки бизнес-логики к Telegram chat/user IDs.

Важно: PostgreSQL repository не должен имитировать YAML-файлы. Он должен реализовывать тот же
domain protocol на нормальной relational model.

## Services

Services должны принимать repositories или unit of work и возвращать доменные объекты/result DTO.
Они не должны импортировать Typer, Rich, Tkinter или messagebox.

### `purchases_service.py`

Ответственность:

- list/filter/sort purchases;
- add purchase;
- edit purchase;
- delete purchase;
- запреты на небезопасное редактирование settled purchases;
- нормализация participants/group expansion через participant/group repository;
- сохранение backward-compatible validation messages.

Начальный API:

```python
class PurchaseService:
    def __init__(self, purchases: PurchaseRepository, participants: ParticipantRepository) -> None:
        ...

    def list_purchases(self, tenant_id: str, scope: str = "all") -> list[Purchase]: ...
    def add_purchase(self, tenant_id: str, command: AddPurchaseCommand) -> Purchase: ...
    def update_purchase(
        self,
        tenant_id: str,
        purchase_id: str,
        patch: PurchasePatch,
    ) -> Purchase: ...
    def delete_purchase(self, tenant_id: str, purchase_id: str, confirm: str) -> Purchase: ...
```

### `participants_service.py`

Ответственность:

- list active/archived participants;
- add/rename/archive/delete participant;
- update dependent purchases/groups/settlement snapshots where current behavior already does this;
- prevent deleting participants used by purchases or periods unless explicit policy allows it.

Начальный API:

```python
class ParticipantService:
    def list_participants(self, tenant_id: str, include_archived: bool = False) -> list[Participant]: ...
    def add_participant(self, tenant_id: str, name: str) -> Participant: ...
    def rename_participant(self, tenant_id: str, old_name: str, new_name: str) -> Participant: ...
    def archive_participant(self, tenant_id: str, name: str) -> Participant: ...
```

### `categories_service.py`

Ответственность:

- list active/archived categories;
- add/rename/archive/delete category;
- preserve current behavior for category rename in purchases;
- keep category display names separate from future stable IDs.

Начальный API:

```python
class CategoryService:
    def list_categories(self, tenant_id: str, include_archived: bool = False) -> list[CategoryEntry]: ...
    def add_category(self, tenant_id: str, name: str) -> CategoryEntry: ...
    def rename_category(self, tenant_id: str, old_name: str, new_name: str) -> CategoryEntry: ...
    def archive_category(self, tenant_id: str, name: str) -> CategoryEntry: ...
```

### `settlement_service.py`

Ответственность:

- balances and settlements for open/all/period scope;
- settlement period preview;
- close settlement period;
- reopen settlement period;
- rename/update period metadata;
- delete empty technical periods;
- enforce transaction boundary for close/reopen.

Начальный API:

```python
class SettlementService:
    def preview_period(
        self,
        tenant_id: str,
        date_from: date,
        date_to: date,
    ) -> SettlementPeriodPreview: ...

    def close_period(
        self,
        tenant_id: str,
        command: ClosePeriodCommand,
    ) -> SettlementPeriod: ...

    def reopen_period(self, tenant_id: str, period_id: str) -> SettlementPeriod: ...
```

Расчеты внутри сервиса должны использовать `calculate_balances`, `calculate_settlements` и
`settlement_periods.py`, но не должны знать, откуда repository взял purchases/periods.

### `report_service.py`

Ответственность:

- build analytics/current/settlement-period datasets;
- выбрать output adapter;
- запустить report writers в controlled workspace;
- вернуть список artifacts, warnings и metadata.

Начальный API:

```python
@dataclass(frozen=True)
class ReportArtifact:
    kind: str
    name: str
    path: str | None = None
    storage_key: str | None = None
    content_type: str | None = None


@dataclass(frozen=True)
class ReportBuildResult:
    report_id: str
    artifacts: list[ReportArtifact]
    warnings: list[dict[str, object]]
    metadata: dict[str, object]


class ReportService:
    def build_current_report(
        self,
        tenant_id: str,
        scope: str,
        output_format: str,
        output: "ReportOutputAdapter",
    ) -> ReportBuildResult: ...
```

Report service не должен жестко писать в глобальный `reports/`. Desktop adapter может передать
`reports/current_state`, а cloud adapter — temp workspace + Object Storage upload.

## Report Output Adapter

Минимальная идея:

```python
class ReportOutputAdapter(Protocol):
    def create_workspace(self, tenant_id: str, report_kind: str) -> Path: ...
    def publish(self, workspace: Path) -> list[ReportArtifact]: ...
```

Adapters:

- `LocalReportOutputAdapter`: возвращает текущие папки `reports/...`, ничего не upload-ит.
- `TempReportOutputAdapter`: создает временную папку для tests/backend jobs.
- `ObjectStorageReportOutputAdapter`: future, upload в Yandex Object Storage или аналог.

На первом шаге можно оставить writers как есть и оборачивать их workspace через adapter. Позже
writers можно разделить на pure table generation и artifact publishing.

## Migration Plan

### Step 1 — Protocols only

Добавить `repositories/protocols.py` и DTO patches/commands без изменения behavior.

Проверки:

- full tests;
- imports do not pull Typer/Tkinter into protocols;
- no changes to CLI/GUI output.

### Step 2 — YAML repository adapter

Добавить `YamlExpenseRepository`, который использует текущий `storage.py`.

Compatibility:

- CLI/GUI могут все еще работать старым путем;
- новые tests проверяют, что repository возвращает те же objects as storage.

### Step 3 — Services thin wrappers

Вынести один use case за раз:

1. list/add purchases;
2. balances/settlements;
3. settlement-period preview/close/reopen;
4. reports.

Каждый шаг должен сохранять public CLI/GUI behavior.

### Step 4 — CLI/GUI as adapters

CLI и GUI начинают вызывать services. Typer/Rich/Tkinter остаются только на внешнем слое.

### Step 5 — PostgreSQL design

Только после stable ID/data model документа:

- добавить `postgres_repository.py`;
- добавить migrations;
- добавить transaction tests;
- не подключать Telegram напрямую к YAML.

## Backward Compatibility Rules

- Не менять имена существующих CLI commands без отдельного release decision.
- Не менять default `data/` и `reports/` для desktop mode.
- Не менять YAML schema без migration/backward compatibility tests.
- Не менять settlement close/reopen semantics.
- Не пересчитывать historical settlement snapshots, если snapshot already exists.
- GUI должен продолжать открывать локальные HTML/XLSX/PDF для local reports.
- Tests для старых CLI/GUI flows должны оставаться зелеными на каждом маленьком шаге.

## Anti-Patterns To Avoid

- Не писать Telegram bot поверх `storage.py` напрямую.
- Не импортировать `typer`, `tkinter`, `messagebox`, `Console` или `Table` в services.
- Не заставлять расчетные функции принимать `data_dir`.
- Не смешивать Object Storage upload с расчетом balances/settlements.
- Не переписывать GUI одновременно с repository extraction.
- Не делать PostgreSQL schema до stable ID решения.

## Open Decisions For TG-PREP.5+

- Stable ID model: `tenant_id`, `user_id`, `participant_id`, `purchase_id`, `category_id`.
- Как мигрировать current display-name references.
- Как хранить historical settlement snapshots: names only, IDs plus display labels, or both.
- Fair rounding policy for server mode.
- Report artifact delivery contract for Telegram: PDF only, ZIP bundle, HTML link, XLSX attachment.
- Transaction and locking policy for close/reopen period.

## Decision

`cloud/telegram-prep` должен двигаться через небольшой compatibility-preserving extraction:
сначала protocols и YAML adapter, затем тонкие services, затем CLI/GUI переходят на services, и
только после этого проект готов к Telegram/FastAPI/PostgreSQL implementation.
