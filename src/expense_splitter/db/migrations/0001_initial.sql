-- Expense Splitter PostgreSQL schema foundation.
-- Stable ID strategy: UUID generated in PostgreSQL via pgcrypto gen_random_uuid().
-- YAML offline mode is intentionally not affected by this migration.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS tenants (
    tenant_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name text NOT NULL,
    status text NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'archived')),
    default_currency text NOT NULL DEFAULT 'RUB',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS users (
    user_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    display_name text NOT NULL,
    status text NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'disabled')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS telegram_accounts (
    telegram_account_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    telegram_user_id bigint NOT NULL UNIQUE,
    user_id uuid NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    username text,
    first_name text,
    last_name text,
    language_code text,
    created_at timestamptz NOT NULL DEFAULT now(),
    last_seen_at timestamptz
);

CREATE TABLE IF NOT EXISTS participants (
    participant_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    linked_user_id uuid REFERENCES users(user_id) ON DELETE SET NULL,
    display_name text NOT NULL,
    normalized_display_name text NOT NULL,
    status text NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'archived')),
    legacy_name text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, normalized_display_name)
);

CREATE TABLE IF NOT EXISTS participant_aliases (
    participant_alias_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    participant_id uuid NOT NULL REFERENCES participants(participant_id) ON DELETE CASCADE,
    alias text NOT NULL,
    normalized_alias text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, normalized_alias)
);

CREATE TABLE IF NOT EXISTS categories (
    category_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    display_name text NOT NULL,
    normalized_display_name text NOT NULL,
    status text NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'archived')),
    legacy_name text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, normalized_display_name)
);

CREATE TABLE IF NOT EXISTS settlement_periods (
    settlement_period_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    period_code text,
    name text NOT NULL,
    status text NOT NULL CHECK (status IN ('closed', 'reopened')),
    date_from date NOT NULL,
    date_to date NOT NULL,
    closed_at timestamptz NOT NULL,
    reopened_at timestamptz,
    total_amount numeric(14, 2) NOT NULL CHECK (total_amount >= 0),
    currency text NOT NULL DEFAULT 'RUB',
    settlements_snapshot jsonb NOT NULL DEFAULT '[]'::jsonb,
    balances_snapshot jsonb NOT NULL DEFAULT '[]'::jsonb,
    created_by_user_id uuid REFERENCES users(user_id) ON DELETE SET NULL,
    notes text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CHECK (date_from <= date_to),
    UNIQUE (tenant_id, period_code)
);

CREATE TABLE IF NOT EXISTS purchases (
    purchase_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    purchase_date date,
    purchase_name text NOT NULL,
    amount numeric(14, 2) NOT NULL CHECK (amount > 0),
    currency text NOT NULL DEFAULT 'RUB',
    payer_participant_id uuid NOT NULL REFERENCES participants(participant_id) ON DELETE RESTRICT,
    payer_display_name_snapshot text NOT NULL,
    category_id uuid REFERENCES categories(category_id) ON DELETE SET NULL,
    category_display_name_snapshot text,
    comment text,
    status text NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'settled', 'void')),
    settlement_period_id uuid REFERENCES settlement_periods(settlement_period_id) ON DELETE SET NULL,
    legacy_id text,
    created_by_user_id uuid REFERENCES users(user_id) ON DELETE SET NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, legacy_id)
);

CREATE TABLE IF NOT EXISTS purchase_participants (
    purchase_participant_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    purchase_id uuid NOT NULL REFERENCES purchases(purchase_id) ON DELETE CASCADE,
    participant_id uuid NOT NULL REFERENCES participants(participant_id) ON DELETE RESTRICT,
    participant_display_name_snapshot text NOT NULL,
    share_amount numeric(14, 2),
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, purchase_id, participant_id)
);

CREATE TABLE IF NOT EXISTS settlement_period_purchases (
    settlement_period_purchase_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    settlement_period_id uuid NOT NULL REFERENCES settlement_periods(settlement_period_id)
        ON DELETE CASCADE,
    purchase_id uuid REFERENCES purchases(purchase_id) ON DELETE SET NULL,
    purchase_name_snapshot text NOT NULL,
    amount_snapshot numeric(14, 2) NOT NULL CHECK (amount_snapshot >= 0),
    payer_display_name_snapshot text NOT NULL,
    category_display_name_snapshot text,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, settlement_period_id, purchase_id)
);

CREATE TABLE IF NOT EXISTS reports (
    report_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    report_type text NOT NULL CHECK (
        report_type IN ('current', 'analytics', 'settlement_period')
    ),
    report_scope text,
    settlement_period_id uuid REFERENCES settlement_periods(settlement_period_id)
        ON DELETE SET NULL,
    period_kind text,
    period_id text,
    formats jsonb NOT NULL DEFAULT '[]'::jsonb,
    storage_backend text NOT NULL,
    storage_key_prefix text,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    warnings jsonb NOT NULL DEFAULT '[]'::jsonb,
    created_by_user_id uuid REFERENCES users(user_id) ON DELETE SET NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    expires_at timestamptz
);

CREATE TABLE IF NOT EXISTS audit_log (
    audit_log_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    actor_user_id uuid REFERENCES users(user_id) ON DELETE SET NULL,
    action text NOT NULL,
    entity_type text NOT NULL,
    entity_id uuid,
    before_data jsonb,
    after_data jsonb,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS bot_sessions (
    bot_session_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    telegram_account_id uuid NOT NULL REFERENCES telegram_accounts(telegram_account_id)
        ON DELETE CASCADE,
    state text NOT NULL,
    payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    last_report_id uuid REFERENCES reports(report_id) ON DELETE SET NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    expires_at timestamptz
);

CREATE INDEX IF NOT EXISTS idx_participants_tenant_status
    ON participants (tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_categories_tenant_status
    ON categories (tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_purchases_tenant_status_date
    ON purchases (tenant_id, status, purchase_date);
CREATE INDEX IF NOT EXISTS idx_purchase_participants_tenant_participant
    ON purchase_participants (tenant_id, participant_id);
CREATE INDEX IF NOT EXISTS idx_settlement_periods_tenant_status_dates
    ON settlement_periods (tenant_id, status, date_from, date_to);
CREATE INDEX IF NOT EXISTS idx_reports_tenant_created
    ON reports (tenant_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_tenant_created
    ON audit_log (tenant_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_bot_sessions_tenant_expires
    ON bot_sessions (tenant_id, expires_at);
