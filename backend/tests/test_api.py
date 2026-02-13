import os
from pathlib import Path

TEST_DB_PATH = Path(__file__).parent.parent / "data" / "test_banking.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH.as_posix()}"
os.environ["SECRET_KEY"] = "test-secret-key-123456"

from fastapi.testclient import TestClient

from app.main import app


def _login(client: TestClient, email: str, password: str) -> str:
    response = client.post(
        "/api/v1/auth/token",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]["access_token"]


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_full_banking_workflow():
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()
    TEST_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with TestClient(app) as client:
        register = client.post(
            "/api/v1/users/register",
            json={
                "name": "Alice",
                "email": "alice@example.com",
                "contact": "1234567890",
                "address": "Demo Street",
                "password": "Password@123",
            },
        )
        assert register.status_code == 200, register.text
        user_id = register.json()["data"]["user_id"]

        user_token = _login(client, "alice@example.com", "Password@123")

        account_1 = client.post(
            "/api/v1/accounts/",
            headers=_auth_header(user_token),
            json={"user_id": user_id, "account_type": "savings", "initial_deposit": 5000},
        )
        assert account_1.status_code == 200, account_1.text
        account_1_id = account_1.json()["data"]["account_id"]

        account_2 = client.post(
            "/api/v1/accounts/",
            headers=_auth_header(user_token),
            json={"user_id": user_id, "account_type": "current", "initial_deposit": 1000},
        )
        assert account_2.status_code == 200, account_2.text
        account_2_id = account_2.json()["data"]["account_id"]

        transfer = client.post(
            "/api/v1/transactions/",
            headers=_auth_header(user_token),
            json={
                "from_account_id": account_1_id,
                "to_account_id": account_2_id,
                "amount": 500,
                "description": "Rent",
            },
        )
        assert transfer.status_code == 200, transfer.text
        assert transfer.json()["data"]["transaction_id"] > 0

        card_create = client.post(
            "/api/v1/debit-cards/",
            headers=_auth_header(user_token),
            json={"account_id": account_1_id},
        )
        assert card_create.status_code == 200, card_create.text
        card_id = card_create.json()["data"]["card_id"]
        otp = card_create.json()["data"]["otp"]

        card_activate = client.put(
            "/api/v1/debit-cards/activate",
            headers=_auth_header(user_token),
            json={"card_id": card_id, "otp": otp},
        )
        assert card_activate.status_code == 200, card_activate.text

        card_disable = client.put(
            f"/api/v1/debit-cards/{card_id}/status",
            headers=_auth_header(user_token),
            json={"status": "disabled"},
        )
        assert card_disable.status_code == 200, card_disable.text

        fund_list = client.get("/api/v1/mutual-funds/", headers=_auth_header(user_token))
        assert fund_list.status_code == 200, fund_list.text
        fund_id = fund_list.json()["data"]["items"][0]["id"]

        fund_buy = client.post(
            "/api/v1/mutual-funds/buy",
            headers=_auth_header(user_token),
            json={"account_id": account_1_id, "fund_id": fund_id, "amount": 1000},
        )
        assert fund_buy.status_code == 200, fund_buy.text

        holdings = client.get("/api/v1/mutual-funds/holdings", headers=_auth_header(user_token))
        assert holdings.status_code == 200, holdings.text
        assert len(holdings.json()["data"]["items"]) >= 1

        fund_sell = client.post(
            "/api/v1/mutual-funds/sell",
            headers=_auth_header(user_token),
            json={"account_id": account_1_id, "fund_id": fund_id, "units": 1},
        )
        assert fund_sell.status_code == 200, fund_sell.text

        deposit_create = client.post(
            "/api/v1/deposits/",
            headers=_auth_header(user_token),
            json={
                "account_id": account_1_id,
                "deposit_type": "fixed",
                "term_months": 12,
                "amount": 500,
                "interest_rate": 6.5,
            },
        )
        assert deposit_create.status_code == 200, deposit_create.text
        deposit_id = deposit_create.json()["data"]["deposit_id"]

        deposit_cancel = client.put(
            f"/api/v1/deposits/{deposit_id}/cancel",
            headers=_auth_header(user_token),
        )
        assert deposit_cancel.status_code == 200, deposit_cancel.text

        transactions = client.get("/api/v1/transactions/", headers=_auth_header(user_token))
        assert transactions.status_code == 200, transactions.text
        assert len(transactions.json()["data"]["items"]) >= 3


def test_admin_bootstrap_and_audit_logs():
    with TestClient(app) as client:
        admin_token = _login(client, "admin@bankexample.com", "Admin@12345")
        logs = client.get("/api/v1/audit-logs/", headers=_auth_header(admin_token))
        assert logs.status_code == 200, logs.text
        assert "items" in logs.json()["data"]
