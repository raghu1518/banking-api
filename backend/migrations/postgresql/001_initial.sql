BEGIN;

CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    contact VARCHAR(30) NOT NULL,
    address VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS accounts (
    id BIGSERIAL PRIMARY KEY,
    account_number VARCHAR(20) NOT NULL UNIQUE,
    user_id BIGINT NOT NULL REFERENCES users(id),
    account_type VARCHAR(30) NOT NULL CHECK (account_type IN ('savings', 'current', 'fixed_deposit')),
    bank_name VARCHAR(120) NOT NULL DEFAULT 'Demo Bank',
    ifsc_code VARCHAR(20) NOT NULL DEFAULT 'DEMO0001234',
    balance NUMERIC(14,2) NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS transactions (
    id BIGSERIAL PRIMARY KEY,
    from_account_id BIGINT REFERENCES accounts(id),
    to_account_id BIGINT REFERENCES accounts(id),
    transaction_type VARCHAR(40) NOT NULL CHECK (transaction_type IN ('transfer', 'mutual_fund_buy', 'mutual_fund_sell', 'deposit_create', 'deposit_cancel', 'adjustment')),
    amount NUMERIC(14,2) NOT NULL,
    description VARCHAR(255) NOT NULL DEFAULT '',
    external_bank_name VARCHAR(120),
    status VARCHAR(20) NOT NULL DEFAULT 'success' CHECK (status IN ('success', 'failed', 'pending')),
    reference VARCHAR(40) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS debit_cards (
    id BIGSERIAL PRIMARY KEY,
    account_id BIGINT NOT NULL REFERENCES accounts(id),
    card_number VARCHAR(20) NOT NULL UNIQUE,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'active', 'disabled')),
    otp_hash VARCHAR(255),
    activation_date TIMESTAMPTZ,
    expiry_date DATE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS mutual_funds (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    symbol VARCHAR(40) NOT NULL UNIQUE,
    nav NUMERIC(12,4) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS mutual_fund_holdings (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id),
    account_id BIGINT NOT NULL REFERENCES accounts(id),
    fund_id BIGINT NOT NULL REFERENCES mutual_funds(id),
    units NUMERIC(14,4) NOT NULL DEFAULT 0,
    average_nav NUMERIC(12,4) NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_user_account_fund_holding UNIQUE (user_id, account_id, fund_id)
);

CREATE TABLE IF NOT EXISTS mutual_fund_trades (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id),
    account_id BIGINT NOT NULL REFERENCES accounts(id),
    fund_id BIGINT NOT NULL REFERENCES mutual_funds(id),
    trade_type VARCHAR(20) NOT NULL CHECK (trade_type IN ('buy', 'sell')),
    nav NUMERIC(12,4) NOT NULL,
    units NUMERIC(14,4) NOT NULL,
    amount NUMERIC(14,2) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS deposits (
    id BIGSERIAL PRIMARY KEY,
    account_id BIGINT NOT NULL REFERENCES accounts(id),
    deposit_type VARCHAR(20) NOT NULL CHECK (deposit_type IN ('fixed', 'recurring')),
    term_months INTEGER NOT NULL,
    amount NUMERIC(14,2) NOT NULL,
    interest_rate NUMERIC(5,2) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'cancelled', 'matured')),
    start_date DATE NOT NULL,
    maturity_date DATE NOT NULL,
    penalty_amount NUMERIC(14,2) NOT NULL DEFAULT 0,
    cancelled_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    action VARCHAR(80) NOT NULL,
    entity VARCHAR(80) NOT NULL,
    entity_id BIGINT,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_accounts_user_id ON accounts(user_id);
CREATE INDEX IF NOT EXISTS idx_transactions_from_account_id ON transactions(from_account_id);
CREATE INDEX IF NOT EXISTS idx_transactions_to_account_id ON transactions(to_account_id);
CREATE INDEX IF NOT EXISTS idx_debit_cards_account_id ON debit_cards(account_id);
CREATE INDEX IF NOT EXISTS idx_holdings_user_id ON mutual_fund_holdings(user_id);
CREATE INDEX IF NOT EXISTS idx_deposits_account_id ON deposits(account_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);

COMMIT;
