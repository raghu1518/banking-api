START TRANSACTION;

CREATE TABLE IF NOT EXISTS users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    contact VARCHAR(30) NOT NULL,
    address VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS accounts (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    account_number VARCHAR(20) NOT NULL UNIQUE,
    user_id BIGINT NOT NULL,
    account_type VARCHAR(30) NOT NULL,
    bank_name VARCHAR(120) NOT NULL DEFAULT 'Demo Bank',
    ifsc_code VARCHAR(20) NOT NULL DEFAULT 'DEMO0001234',
    balance DECIMAL(14,2) NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_accounts_user FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT chk_accounts_type CHECK (account_type IN ('savings', 'current', 'fixed_deposit'))
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS transactions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    from_account_id BIGINT NULL,
    to_account_id BIGINT NULL,
    transaction_type VARCHAR(40) NOT NULL,
    amount DECIMAL(14,2) NOT NULL,
    description VARCHAR(255) NOT NULL DEFAULT '',
    external_bank_name VARCHAR(120) NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'success',
    reference VARCHAR(40) NOT NULL UNIQUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_txn_from_account FOREIGN KEY (from_account_id) REFERENCES accounts(id),
    CONSTRAINT fk_txn_to_account FOREIGN KEY (to_account_id) REFERENCES accounts(id),
    CONSTRAINT chk_txn_type CHECK (transaction_type IN ('transfer', 'mutual_fund_buy', 'mutual_fund_sell', 'deposit_create', 'deposit_cancel', 'adjustment')),
    CONSTRAINT chk_txn_status CHECK (status IN ('success', 'failed', 'pending'))
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS debit_cards (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    account_id BIGINT NOT NULL,
    card_number VARCHAR(20) NOT NULL UNIQUE,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    otp_hash VARCHAR(255) NULL,
    activation_date DATETIME NULL,
    expiry_date DATE NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_cards_account FOREIGN KEY (account_id) REFERENCES accounts(id),
    CONSTRAINT chk_cards_status CHECK (status IN ('pending', 'active', 'disabled'))
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS mutual_funds (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    symbol VARCHAR(40) NOT NULL UNIQUE,
    nav DECIMAL(12,4) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS mutual_fund_holdings (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    account_id BIGINT NOT NULL,
    fund_id BIGINT NOT NULL,
    units DECIMAL(14,4) NOT NULL DEFAULT 0,
    average_nav DECIMAL(12,4) NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT uq_user_account_fund_holding UNIQUE (user_id, account_id, fund_id),
    CONSTRAINT fk_holdings_user FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT fk_holdings_account FOREIGN KEY (account_id) REFERENCES accounts(id),
    CONSTRAINT fk_holdings_fund FOREIGN KEY (fund_id) REFERENCES mutual_funds(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS mutual_fund_trades (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    account_id BIGINT NOT NULL,
    fund_id BIGINT NOT NULL,
    trade_type VARCHAR(20) NOT NULL,
    nav DECIMAL(12,4) NOT NULL,
    units DECIMAL(14,4) NOT NULL,
    amount DECIMAL(14,2) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_trades_user FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT fk_trades_account FOREIGN KEY (account_id) REFERENCES accounts(id),
    CONSTRAINT fk_trades_fund FOREIGN KEY (fund_id) REFERENCES mutual_funds(id),
    CONSTRAINT chk_trade_type CHECK (trade_type IN ('buy', 'sell'))
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS deposits (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    account_id BIGINT NOT NULL,
    deposit_type VARCHAR(20) NOT NULL,
    term_months INT NOT NULL,
    amount DECIMAL(14,2) NOT NULL,
    interest_rate DECIMAL(5,2) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    start_date DATE NOT NULL,
    maturity_date DATE NOT NULL,
    penalty_amount DECIMAL(14,2) NOT NULL DEFAULT 0,
    cancelled_at DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_deposits_account FOREIGN KEY (account_id) REFERENCES accounts(id),
    CONSTRAINT chk_deposit_type CHECK (deposit_type IN ('fixed', 'recurring')),
    CONSTRAINT chk_deposit_status CHECK (status IN ('active', 'cancelled', 'matured'))
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NULL,
    action VARCHAR(80) NOT NULL,
    entity VARCHAR(80) NOT NULL,
    entity_id BIGINT NULL,
    details JSON NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_audit_user FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB;

CREATE INDEX idx_accounts_user_id ON accounts(user_id);
CREATE INDEX idx_transactions_from_account_id ON transactions(from_account_id);
CREATE INDEX idx_transactions_to_account_id ON transactions(to_account_id);
CREATE INDEX idx_debit_cards_account_id ON debit_cards(account_id);
CREATE INDEX idx_holdings_user_id ON mutual_fund_holdings(user_id);
CREATE INDEX idx_deposits_account_id ON deposits(account_id);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);

COMMIT;
