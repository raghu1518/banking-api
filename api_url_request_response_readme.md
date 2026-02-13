# API URL / Request / Response Reference

This document lists **all currently available API endpoints** in this project, with:
- URL
- HTTP method
- Auth requirement
- Request body/query format
- Sample success response

## Base URLs
- App health: `http://127.0.0.1:8000/`
- API base: `http://127.0.0.1:8000/api/v1`

## Auth Header
For protected endpoints:
```http
Authorization: Bearer <access_token>
```

## Standard Response Envelope
All API responses use:
```json
{
  "status": "success/error",
  "message": "Description of result",
  "data": {}
}
```

## Common Enums
- `account_type`: `savings | current | fixed_deposit`
- `transaction_type`: `transfer | mutual_fund_buy | mutual_fund_sell | deposit_create | deposit_cancel | adjustment`
- `transaction_status`: `success | failed | pending`
- `card_status`: `pending | active | disabled`
- `deposit_type`: `fixed | recurring`
- `deposit_status`: `active | cancelled | matured`

---

## 1) Health

### GET `/`
- Auth: Public
- Request: none
- Success response:
```json
{
  "status": "success",
  "message": "Banking API is running",
  "data": {
    "version": "1.0.0"
  }
}
```

---

## 2) Authentication

### POST `/api/v1/auth/token`
- Auth: Public
- Request body:
```json
{
  "email": "admin@bankexample.com",
  "password": "Admin@12345"
}
```
- Success response:
```json
{
  "status": "success",
  "message": "Authentication successful",
  "data": {
    "access_token": "<jwt>",
    "token_type": "bearer",
    "user_id": 1
  }
}
```

### GET `/api/v1/auth/me`
- Auth: Bearer token
- Request: none
- Success response:
```json
{
  "status": "success",
  "message": "Current user retrieved",
  "data": {
    "user": {
      "id": 1,
      "name": "System Admin",
      "email": "admin@bankexample.com",
      "contact": "9999999999",
      "address": "HQ",
      "is_active": true,
      "is_admin": true,
      "created_at": "2026-02-13T23:00:00Z"
    }
  }
}
```

---

## 3) Users

### POST `/api/v1/users/register`
- Auth: Public
- Request body:
```json
{
  "name": "Alice",
  "email": "alice@example.com",
  "contact": "1234567890",
  "address": "Demo Street",
  "password": "Password@123",
  "is_admin": false
}
```
- Success response:
```json
{
  "status": "success",
  "message": "User registered",
  "data": {
    "user_id": 2
  }
}
```

### POST `/api/v1/users/`
- Auth: Admin only
- Request body:
```json
{
  "name": "Bob",
  "email": "bob@example.com",
  "contact": "8888888888",
  "address": "Main Road",
  "password": "Password@123",
  "is_admin": true
}
```
- Success response:
```json
{
  "status": "success",
  "message": "User created",
  "data": {
    "user_id": 3
  }
}
```

### GET `/api/v1/users/`
- Auth: Admin only
- Request: none
- Success response:
```json
{
  "status": "success",
  "message": "Users fetched",
  "data": {
    "items": [
      {
        "id": 3,
        "name": "Bob",
        "email": "bob@example.com",
        "contact": "8888888888",
        "address": "Main Road",
        "is_active": true,
        "is_admin": true,
        "created_at": "2026-02-13T23:00:00Z"
      }
    ]
  }
}
```

### GET `/api/v1/users/{user_id}`
- Auth: Admin or same user
- Path params:
  - `user_id` (int)
- Success response:
```json
{
  "status": "success",
  "message": "User fetched",
  "data": {
    "user": {
      "id": 2,
      "name": "Alice",
      "email": "alice@example.com",
      "contact": "1234567890",
      "address": "Demo Street",
      "is_active": true,
      "is_admin": false,
      "created_at": "2026-02-13T23:00:00Z"
    }
  }
}
```

### PUT `/api/v1/users/{user_id}`
- Auth: Admin or same user (`is_active` can be changed by admin only)
- Path params:
  - `user_id` (int)
- Request body (all optional):
```json
{
  "name": "Alice Updated",
  "contact": "7777777777",
  "address": "New Address",
  "password": "NewPassword@123",
  "is_active": true
}
```
- Success response:
```json
{
  "status": "success",
  "message": "User updated",
  "data": {
    "user_id": 2
  }
}
```

### DELETE `/api/v1/users/{user_id}`
- Auth: Admin only
- Path params:
  - `user_id` (int)
- Behavior: soft delete (`is_deleted=true`, `is_active=false`)
- Success response:
```json
{
  "status": "success",
  "message": "User deleted",
  "data": {
    "user_id": 2
  }
}
```

---

## 4) Accounts

### POST `/api/v1/accounts/`
- Auth: Bearer token (admin can create for any user; normal user for self only)
- Request body:
```json
{
  "user_id": 2,
  "account_type": "savings",
  "initial_deposit": 5000
}
```
- Success response:
```json
{
  "status": "success",
  "message": "Account created",
  "data": {
    "account_id": 101
  }
}
```

### GET `/api/v1/accounts/`
- Auth: Bearer token
- Query params:
  - `include_deleted` (bool, optional, default `false`)
- Success response:
```json
{
  "status": "success",
  "message": "Accounts fetched",
  "data": {
    "items": [
      {
        "id": 101,
        "account_number": "123456789012",
        "user_id": 2,
        "account_type": "savings",
        "bank_name": "Demo Bank",
        "ifsc_code": "DEMO0001234",
        "balance": "5000.00",
        "is_active": true,
        "is_deleted": false,
        "created_at": "2026-02-13T23:00:00Z"
      }
    ]
  }
}
```

### GET `/api/v1/accounts/{account_id}`
- Auth: Bearer token (admin or account owner)
- Path params:
  - `account_id` (int)
- Success response:
```json
{
  "status": "success",
  "message": "Account fetched",
  "data": {
    "account": {
      "id": 101,
      "account_number": "123456789012",
      "user_id": 2,
      "account_type": "savings",
      "bank_name": "Demo Bank",
      "ifsc_code": "DEMO0001234",
      "balance": "5000.00",
      "is_active": true,
      "is_deleted": false,
      "created_at": "2026-02-13T23:00:00Z"
    }
  }
}
```

### PUT `/api/v1/accounts/{account_id}`
- Auth: Bearer token (admin or account owner)
- Path params:
  - `account_id` (int)
- Request body (all optional):
```json
{
  "account_type": "current",
  "is_active": true
}
```
- Success response:
```json
{
  "status": "success",
  "message": "Account updated",
  "data": {
    "account_id": 101
  }
}
```

### DELETE `/api/v1/accounts/{account_id}`
- Auth: Bearer token (admin or account owner)
- Path params:
  - `account_id` (int)
- Behavior: soft delete (`is_deleted=true`, `is_active=false`)
- Success response:
```json
{
  "status": "success",
  "message": "Account deleted",
  "data": {
    "account_id": 101
  }
}
```

### GET `/api/v1/accounts/{account_id}/balance`
- Auth: Bearer token (admin or account owner)
- Path params:
  - `account_id` (int)
- Success response:
```json
{
  "status": "success",
  "message": "Account balance fetched",
  "data": {
    "balance": {
      "account_id": 101,
      "balance": "5000.00"
    }
  }
}
```

---

## 5) Transactions

### POST `/api/v1/transactions/`
- Auth: Bearer token
- Notes:
  - For same-bank transfer, pass `to_account_id`.
  - For inter-bank transfer, set `to_account_id: null` and provide `external_bank_name`.
- Request body:
```json
{
  "from_account_id": 101,
  "to_account_id": 102,
  "external_bank_name": null,
  "amount": 1000,
  "description": "Rent transfer"
}
```
- Success response:
```json
{
  "status": "success",
  "message": "Transaction successful",
  "data": {
    "transaction_id": 501
  }
}
```

### GET `/api/v1/transactions/`
- Auth: Bearer token
- Query params (all optional):
  - `date_from` (datetime, ISO-8601)
  - `date_to` (datetime, ISO-8601)
  - `transaction_type` (`transfer|mutual_fund_buy|mutual_fund_sell|deposit_create|deposit_cancel|adjustment`)
  - `min_amount` (decimal)
  - `max_amount` (decimal)
- Success response:
```json
{
  "status": "success",
  "message": "Transactions fetched",
  "data": {
    "items": [
      {
        "id": 501,
        "from_account_id": 101,
        "to_account_id": 102,
        "transaction_type": "transfer",
        "amount": "1000.00",
        "description": "Rent transfer",
        "external_bank_name": null,
        "status": "success",
        "reference": "TXN123456789012",
        "created_at": "2026-02-13T23:00:00Z"
      }
    ]
  }
}
```

### GET `/api/v1/transactions/{transaction_id}`
- Auth: Bearer token (admin or account owner)
- Path params:
  - `transaction_id` (int)
- Success response:
```json
{
  "status": "success",
  "message": "Transaction fetched",
  "data": {
    "transaction": {
      "id": 501,
      "from_account_id": 101,
      "to_account_id": 102,
      "transaction_type": "transfer",
      "amount": "1000.00",
      "description": "Rent transfer",
      "external_bank_name": null,
      "status": "success",
      "reference": "TXN123456789012",
      "created_at": "2026-02-13T23:00:00Z"
    }
  }
}
```

### PUT `/api/v1/transactions/{transaction_id}`
- Auth: Admin only
- Path params:
  - `transaction_id` (int)
- Request body (all optional):
```json
{
  "description": "Updated description",
  "status": "pending"
}
```
- Success response:
```json
{
  "status": "success",
  "message": "Transaction updated",
  "data": {
    "transaction_id": 501
  }
}
```

### DELETE `/api/v1/transactions/{transaction_id}`
- Auth: Admin only
- Path params:
  - `transaction_id` (int)
- Success response:
```json
{
  "status": "success",
  "message": "Transaction deleted",
  "data": {
    "transaction_id": 501
  }
}
```

---

## 6) Debit Cards

### POST `/api/v1/debit-cards/`
- Auth: Bearer token (admin or account owner)
- Request body:
```json
{
  "account_id": 101
}
```
- Success response:
```json
{
  "status": "success",
  "message": "Debit card created. Use OTP to activate.",
  "data": {
    "card_id": 201,
    "otp": "123456"
  }
}
```

### GET `/api/v1/debit-cards/`
- Auth: Bearer token
- Success response:
```json
{
  "status": "success",
  "message": "Debit cards fetched",
  "data": {
    "items": [
      {
        "id": 201,
        "account_id": 101,
        "card_number": "521234123456789",
        "status": "pending",
        "activation_date": null,
        "expiry_date": "2031-02-13"
      }
    ]
  }
}
```

### GET `/api/v1/debit-cards/{card_id}`
- Auth: Bearer token (admin or account owner)
- Path params:
  - `card_id` (int)
- Success response:
```json
{
  "status": "success",
  "message": "Card fetched",
  "data": {
    "card": {
      "id": 201,
      "account_id": 101,
      "card_number": "521234123456789",
      "status": "pending",
      "activation_date": null,
      "expiry_date": "2031-02-13"
    }
  }
}
```

### PUT `/api/v1/debit-cards/{card_id}/status`
- Auth: Bearer token (admin or account owner)
- Allowed statuses here: `active` or `disabled`
- Path params:
  - `card_id` (int)
- Request body:
```json
{
  "status": "disabled"
}
```
- Success response:
```json
{
  "status": "success",
  "message": "Card status updated",
  "data": {
    "card_id": 201
  }
}
```

### PUT `/api/v1/debit-cards/activate`
- Auth: Bearer token (admin or account owner)
- Request body:
```json
{
  "card_id": 201,
  "otp": "123456"
}
```
- Success response:
```json
{
  "status": "success",
  "message": "Card activated",
  "data": {
    "card_id": 201
  }
}
```

### DELETE `/api/v1/debit-cards/{card_id}`
- Auth: Bearer token (admin or account owner)
- Path params:
  - `card_id` (int)
- Behavior: card is disabled
- Success response:
```json
{
  "status": "success",
  "message": "Card disabled",
  "data": {
    "card_id": 201
  }
}
```

---

## 7) Mutual Funds

### POST `/api/v1/mutual-funds/`
- Auth: Admin only
- Request body:
```json
{
  "name": "Bluechip Equity Fund",
  "symbol": "BEF",
  "nav": 42.5
}
```
- Success response:
```json
{
  "status": "success",
  "message": "Mutual fund created",
  "data": {
    "fund_id": 301
  }
}
```

### GET `/api/v1/mutual-funds/`
- Auth: Bearer token
- Success response:
```json
{
  "status": "success",
  "message": "Mutual funds fetched",
  "data": {
    "items": [
      {
        "id": 301,
        "name": "Bluechip Equity Fund",
        "symbol": "BEF",
        "nav": "42.5000",
        "is_active": true
      }
    ]
  }
}
```

### GET `/api/v1/mutual-funds/{fund_id}`
- Auth: Bearer token
- Path params:
  - `fund_id` (int)
- Success response:
```json
{
  "status": "success",
  "message": "Mutual fund fetched",
  "data": {
    "fund": {
      "id": 301,
      "name": "Bluechip Equity Fund",
      "symbol": "BEF",
      "nav": "42.5000",
      "is_active": true
    }
  }
}
```

### PUT `/api/v1/mutual-funds/{fund_id}`
- Auth: Admin only
- Path params:
  - `fund_id` (int)
- Request body:
```json
{
  "nav": 45.125
}
```
- Success response:
```json
{
  "status": "success",
  "message": "Mutual fund updated",
  "data": {
    "fund_id": 301
  }
}
```

### DELETE `/api/v1/mutual-funds/{fund_id}`
- Auth: Admin only
- Path params:
  - `fund_id` (int)
- Behavior: deactivates fund
- Success response:
```json
{
  "status": "success",
  "message": "Mutual fund deactivated",
  "data": {
    "fund_id": 301
  }
}
```

### POST `/api/v1/mutual-funds/buy`
- Auth: Bearer token (admin or account owner)
- Request body:
```json
{
  "account_id": 101,
  "fund_id": 301,
  "amount": 1000
}
```
- Success response:
```json
{
  "status": "success",
  "message": "Mutual fund purchased",
  "data": {
    "trade_id": 401
  }
}
```

### POST `/api/v1/mutual-funds/sell`
- Auth: Bearer token (admin or account owner)
- Request body:
```json
{
  "account_id": 101,
  "fund_id": 301,
  "units": 1.25
}
```
- Success response:
```json
{
  "status": "success",
  "message": "Mutual fund sold",
  "data": {
    "trade_id": 402
  }
}
```

### GET `/api/v1/mutual-funds/holdings`
- Auth: Bearer token (admin sees all; user sees own)
- Success response:
```json
{
  "status": "success",
  "message": "Mutual fund holdings fetched",
  "data": {
    "items": [
      {
        "id": 1,
        "user_id": 2,
        "account_id": 101,
        "fund_id": 301,
        "units": "23.5294",
        "average_nav": "42.5000"
      }
    ]
  }
}
```

### GET `/api/v1/mutual-funds/trades`
- Auth: Bearer token (admin sees all; user sees own)
- Success response:
```json
{
  "status": "success",
  "message": "Mutual fund trades fetched",
  "data": {
    "items": [
      {
        "id": 401,
        "user_id": 2,
        "account_id": 101,
        "fund_id": 301,
        "trade_type": "buy",
        "nav": "42.5000",
        "units": "23.5294",
        "amount": "1000.00",
        "created_at": "2026-02-13T23:00:00Z"
      }
    ]
  }
}
```

---

## 8) Deposits

### POST `/api/v1/deposits/`
- Auth: Bearer token (admin or account owner)
- Request body:
```json
{
  "account_id": 101,
  "deposit_type": "fixed",
  "term_months": 12,
  "amount": 5000,
  "interest_rate": 6.5
}
```
- Success response:
```json
{
  "status": "success",
  "message": "Deposit created",
  "data": {
    "deposit_id": 601
  }
}
```

### GET `/api/v1/deposits/`
- Auth: Bearer token
- Query params:
  - `status_filter` (`active|cancelled|matured`, optional)
- Success response:
```json
{
  "status": "success",
  "message": "Deposits fetched",
  "data": {
    "items": [
      {
        "id": 601,
        "account_id": 101,
        "deposit_type": "fixed",
        "term_months": 12,
        "amount": "5000.00",
        "interest_rate": "6.50",
        "status": "active",
        "start_date": "2026-02-13",
        "maturity_date": "2027-02-13",
        "penalty_amount": "0.00",
        "cancelled_at": null
      }
    ]
  }
}
```

### GET `/api/v1/deposits/{deposit_id}`
- Auth: Bearer token (admin or account owner)
- Path params:
  - `deposit_id` (int)
- Success response:
```json
{
  "status": "success",
  "message": "Deposit fetched",
  "data": {
    "deposit": {
      "id": 601,
      "account_id": 101,
      "deposit_type": "fixed",
      "term_months": 12,
      "amount": "5000.00",
      "interest_rate": "6.50",
      "status": "active",
      "start_date": "2026-02-13",
      "maturity_date": "2027-02-13",
      "penalty_amount": "0.00",
      "cancelled_at": null
    }
  }
}
```

### PUT `/api/v1/deposits/{deposit_id}/cancel`
- Auth: Bearer token (admin or account owner)
- Path params:
  - `deposit_id` (int)
- Request body: none
- Success response:
```json
{
  "status": "success",
  "message": "Deposit cancelled",
  "data": {
    "deposit_id": 601,
    "penalty": "50.00"
  }
}
```

### DELETE `/api/v1/deposits/{deposit_id}`
- Auth: Bearer token (admin or account owner)
- Path params:
  - `deposit_id` (int)
- Note: active deposits must be cancelled first
- Success response:
```json
{
  "status": "success",
  "message": "Deposit removed",
  "data": {
    "deposit_id": 601
  }
}
```

---

## 9) Audit Logs

### GET `/api/v1/audit-logs/`
- Auth: Admin only
- Request: none
- Success response:
```json
{
  "status": "success",
  "message": "Audit logs fetched",
  "data": {
    "items": [
      {
        "id": 1,
        "user_id": 1,
        "action": "create",
        "entity": "account",
        "entity_id": 101,
        "details": {
          "user_id": 2,
          "account_type": "savings"
        },
        "created_at": "2026-02-13T23:00:00Z"
      }
    ]
  }
}
```

---

## Common Error Response Examples

### Validation error (422)
```json
{
  "status": "error",
  "message": "Validation failed",
  "data": {
    "errors": [
      {
        "type": "string_type",
        "loc": ["body", "email"],
        "msg": "Input should be a valid string",
        "input": null
      }
    ]
  }
}
```

### Auth/permission/business error (4xx)
```json
{
  "status": "error",
  "message": "Insufficient permissions",
  "data": {}
}
```

### Unexpected server error (500)
```json
{
  "status": "error",
  "message": "Internal server error",
  "data": {}
}
```

