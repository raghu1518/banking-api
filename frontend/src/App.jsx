
import { useEffect, useMemo, useState } from "react";

import { apiBaseUrl, apiRequest } from "./api";

const TABS = [
  { id: "users", label: "Users" },
  { id: "accounts", label: "Accounts" },
  { id: "transactions", label: "Transactions" },
  { id: "debit_cards", label: "Debit Cards" },
  { id: "mutual_funds", label: "Mutual Funds" },
  { id: "deposits", label: "Deposits" },
  { id: "audit", label: "Audit Logs" },
];

function SectionCard({ title, children, actions }) {
  return (
    <section className="section-card">
      <header className="section-header">
        <h3>{title}</h3>
        <div className="section-actions">{actions}</div>
      </header>
      <div className="section-body">{children}</div>
    </section>
  );
}

function DataTable({ columns, rows }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column.key}>{column.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="empty-row">
                No records found.
              </td>
            </tr>
          ) : (
            rows.map((row, idx) => (
              <tr key={row.id ?? idx}>
                {columns.map((column) => (
                  <td key={`${column.key}-${idx}`}>{formatCell(row[column.key])}</td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

function formatCell(value) {
  if (value === null || value === undefined) return "-";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function Notice({ notice, onClose }) {
  if (!notice) return null;
  return (
    <div className={`notice ${notice.type}`}>
      <span>{notice.text}</span>
      <button type="button" onClick={onClose}>
        x
      </button>
    </div>
  );
}

function AuthView({ onAuth, notify }) {
  const [login, setLogin] = useState({ email: "admin@bankexample.com", password: "Admin@12345" });
  const [register, setRegister] = useState({
    name: "",
    email: "",
    contact: "",
    address: "",
    password: "",
  });

  const submitLogin = async (event) => {
    event.preventDefault();
    try {
      const tokenResponse = await apiRequest("/auth/token", { method: "POST", body: login });
      onAuth(tokenResponse.data.access_token);
      notify("success", "Logged in");
    } catch (error) {
      notify("error", error.message);
    }
  };

  const submitRegister = async (event) => {
    event.preventDefault();
    try {
      await apiRequest("/users/register", { method: "POST", body: register });
      notify("success", "User registered. You can now log in.");
      setRegister({ name: "", email: "", contact: "", address: "", password: "" });
    } catch (error) {
      notify("error", error.message);
    }
  };

  return (
    <div className="auth-shell">
      <div className="auth-intro">
        <p className="eyebrow">Banking Control Desk</p>
        <h1>Production-ready API + UI banking suite</h1>
        <p>
          API base: <code>{apiBaseUrl}</code>
        </p>
      </div>
      <div className="auth-grid">
        <SectionCard title="Sign In">
          <form onSubmit={submitLogin} className="form-grid">
            <label>
              Email
              <input value={login.email} onChange={(e) => setLogin((prev) => ({ ...prev, email: e.target.value }))} required />
            </label>
            <label>
              Password
              <input
                type="password"
                value={login.password}
                onChange={(e) => setLogin((prev) => ({ ...prev, password: e.target.value }))}
                required
              />
            </label>
            <button type="submit">Login</button>
          </form>
        </SectionCard>

        <SectionCard title="Register New User">
          <form onSubmit={submitRegister} className="form-grid">
            <label>
              Name
              <input value={register.name} onChange={(e) => setRegister((prev) => ({ ...prev, name: e.target.value }))} required />
            </label>
            <label>
              Email
              <input value={register.email} onChange={(e) => setRegister((prev) => ({ ...prev, email: e.target.value }))} required />
            </label>
            <label>
              Contact
              <input value={register.contact} onChange={(e) => setRegister((prev) => ({ ...prev, contact: e.target.value }))} required />
            </label>
            <label>
              Address
              <input value={register.address} onChange={(e) => setRegister((prev) => ({ ...prev, address: e.target.value }))} required />
            </label>
            <label>
              Password
              <input
                type="password"
                value={register.password}
                onChange={(e) => setRegister((prev) => ({ ...prev, password: e.target.value }))}
                required
              />
            </label>
            <button type="submit">Register</button>
          </form>
        </SectionCard>
      </div>
    </div>
  );
}
function UsersPanel({ token, currentUser, notify }) {
  const [rows, setRows] = useState([]);
  const [createForm, setCreateForm] = useState({
    name: "",
    email: "",
    contact: "",
    address: "",
    password: "Password@123",
    is_admin: false,
  });
  const [updateForm, setUpdateForm] = useState({ user_id: "", name: "", contact: "", address: "", password: "", is_active: "true" });
  const [deleteId, setDeleteId] = useState("");

  const load = async () => {
    try {
      if (currentUser.is_admin) {
        const response = await apiRequest("/users/", { token });
        setRows(response.data.items || []);
      } else {
        const response = await apiRequest(`/users/${currentUser.id}`, { token });
        setRows([response.data.user]);
      }
    } catch (error) {
      notify("error", error.message);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const createUser = async (event) => {
    event.preventDefault();
    const endpoint = currentUser.is_admin ? "/users/" : "/users/register";
    const body = currentUser.is_admin ? createForm : { ...createForm, is_admin: false };
    try {
      const response = await apiRequest(endpoint, { method: "POST", token: currentUser.is_admin ? token : undefined, body });
      notify("success", `User saved with ID ${response.data.user_id}`);
      await load();
    } catch (error) {
      notify("error", error.message);
    }
  };

  const updateUser = async (event) => {
    event.preventDefault();
    if (!updateForm.user_id) return;
    const body = {};
    if (updateForm.name) body.name = updateForm.name;
    if (updateForm.contact) body.contact = updateForm.contact;
    if (updateForm.address) body.address = updateForm.address;
    if (updateForm.password) body.password = updateForm.password;
    if (currentUser.is_admin) body.is_active = updateForm.is_active === "true";

    try {
      await apiRequest(`/users/${updateForm.user_id}`, { method: "PUT", token, body });
      notify("success", "User updated");
      await load();
    } catch (error) {
      notify("error", error.message);
    }
  };

  const deleteUser = async (event) => {
    event.preventDefault();
    if (!deleteId) return;
    try {
      await apiRequest(`/users/${deleteId}`, { method: "DELETE", token });
      notify("success", "User soft deleted");
      setDeleteId("");
      await load();
    } catch (error) {
      notify("error", error.message);
    }
  };

  return (
    <div className="panel-grid">
      <SectionCard title="Users" actions={<button onClick={load}>Refresh</button>}>
        <DataTable
          columns={[
            { key: "id", label: "ID" },
            { key: "name", label: "Name" },
            { key: "email", label: "Email" },
            { key: "contact", label: "Contact" },
            { key: "is_admin", label: "Admin" },
            { key: "is_active", label: "Active" },
          ]}
          rows={rows}
        />
      </SectionCard>

      <SectionCard title="Create User">
        <form className="form-grid" onSubmit={createUser}>
          <label>
            Name
            <input value={createForm.name} onChange={(e) => setCreateForm((prev) => ({ ...prev, name: e.target.value }))} required />
          </label>
          <label>
            Email
            <input value={createForm.email} onChange={(e) => setCreateForm((prev) => ({ ...prev, email: e.target.value }))} required />
          </label>
          <label>
            Contact
            <input value={createForm.contact} onChange={(e) => setCreateForm((prev) => ({ ...prev, contact: e.target.value }))} required />
          </label>
          <label>
            Address
            <input value={createForm.address} onChange={(e) => setCreateForm((prev) => ({ ...prev, address: e.target.value }))} required />
          </label>
          <label>
            Password
            <input
              type="password"
              value={createForm.password}
              onChange={(e) => setCreateForm((prev) => ({ ...prev, password: e.target.value }))}
              required
            />
          </label>
          {currentUser.is_admin ? (
            <label>
              Admin
              <select
                value={createForm.is_admin ? "true" : "false"}
                onChange={(e) => setCreateForm((prev) => ({ ...prev, is_admin: e.target.value === "true" }))}
              >
                <option value="false">No</option>
                <option value="true">Yes</option>
              </select>
            </label>
          ) : null}
          <button type="submit">Save User</button>
        </form>
      </SectionCard>

      <SectionCard title="Update User">
        <form className="form-grid" onSubmit={updateUser}>
          <label>
            User ID
            <input value={updateForm.user_id} onChange={(e) => setUpdateForm((prev) => ({ ...prev, user_id: e.target.value }))} required />
          </label>
          <label>
            New Name
            <input value={updateForm.name} onChange={(e) => setUpdateForm((prev) => ({ ...prev, name: e.target.value }))} />
          </label>
          <label>
            New Contact
            <input value={updateForm.contact} onChange={(e) => setUpdateForm((prev) => ({ ...prev, contact: e.target.value }))} />
          </label>
          <label>
            New Address
            <input value={updateForm.address} onChange={(e) => setUpdateForm((prev) => ({ ...prev, address: e.target.value }))} />
          </label>
          <label>
            New Password
            <input
              type="password"
              value={updateForm.password}
              onChange={(e) => setUpdateForm((prev) => ({ ...prev, password: e.target.value }))}
            />
          </label>
          {currentUser.is_admin ? (
            <label>
              Active
              <select value={updateForm.is_active} onChange={(e) => setUpdateForm((prev) => ({ ...prev, is_active: e.target.value }))}>
                <option value="true">True</option>
                <option value="false">False</option>
              </select>
            </label>
          ) : null}
          <button type="submit">Update User</button>
        </form>
      </SectionCard>

      {currentUser.is_admin ? (
        <SectionCard title="Delete User (Soft Delete)">
          <form className="inline-form" onSubmit={deleteUser}>
            <input placeholder="User ID" value={deleteId} onChange={(e) => setDeleteId(e.target.value)} required />
            <button type="submit">Delete</button>
          </form>
        </SectionCard>
      ) : null}
    </div>
  );
}
function AccountsPanel({ token, currentUser, notify }) {
  const [rows, setRows] = useState([]);
  const [createForm, setCreateForm] = useState({ user_id: String(currentUser.id), account_type: "savings", initial_deposit: 0 });
  const [updateForm, setUpdateForm] = useState({ account_id: "", account_type: "savings", is_active: "true" });
  const [deleteId, setDeleteId] = useState("");
  const [balanceId, setBalanceId] = useState("");
  const [balance, setBalance] = useState("");

  const load = async () => {
    try {
      const response = await apiRequest("/accounts/", { token });
      setRows(response.data.items || []);
    } catch (error) {
      notify("error", error.message);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const createAccount = async (event) => {
    event.preventDefault();
    try {
      const response = await apiRequest("/accounts/", {
        method: "POST",
        token,
        body: {
          user_id: Number(createForm.user_id),
          account_type: createForm.account_type,
          initial_deposit: Number(createForm.initial_deposit),
        },
      });
      notify("success", `Account created: ${response.data.account_id}`);
      await load();
    } catch (error) {
      notify("error", error.message);
    }
  };

  const updateAccount = async (event) => {
    event.preventDefault();
    try {
      await apiRequest(`/accounts/${updateForm.account_id}`, {
        method: "PUT",
        token,
        body: { account_type: updateForm.account_type, is_active: updateForm.is_active === "true" },
      });
      notify("success", "Account updated");
      await load();
    } catch (error) {
      notify("error", error.message);
    }
  };

  const deleteAccount = async (event) => {
    event.preventDefault();
    try {
      await apiRequest(`/accounts/${deleteId}`, { method: "DELETE", token });
      notify("success", "Account soft deleted");
      setDeleteId("");
      await load();
    } catch (error) {
      notify("error", error.message);
    }
  };

  const checkBalance = async (event) => {
    event.preventDefault();
    try {
      const response = await apiRequest(`/accounts/${balanceId}/balance`, { token });
      setBalance(response.data.balance.balance);
      notify("success", "Balance fetched");
    } catch (error) {
      notify("error", error.message);
    }
  };

  return (
    <div className="panel-grid">
      <SectionCard title="Accounts" actions={<button onClick={load}>Refresh</button>}>
        <DataTable
          columns={[
            { key: "id", label: "ID" },
            { key: "account_number", label: "Account Number" },
            { key: "user_id", label: "User ID" },
            { key: "account_type", label: "Type" },
            { key: "balance", label: "Balance" },
            { key: "is_active", label: "Active" },
            { key: "is_deleted", label: "Deleted" },
          ]}
          rows={rows}
        />
      </SectionCard>

      <SectionCard title="Create Account">
        <form className="form-grid" onSubmit={createAccount}>
          <label>
            User ID
            <input value={createForm.user_id} onChange={(e) => setCreateForm((prev) => ({ ...prev, user_id: e.target.value }))} required />
          </label>
          <label>
            Type
            <select value={createForm.account_type} onChange={(e) => setCreateForm((prev) => ({ ...prev, account_type: e.target.value }))}>
              <option value="savings">Savings</option>
              <option value="current">Current</option>
              <option value="fixed_deposit">Fixed Deposit</option>
            </select>
          </label>
          <label>
            Initial Deposit
            <input
              type="number"
              step="0.01"
              value={createForm.initial_deposit}
              onChange={(e) => setCreateForm((prev) => ({ ...prev, initial_deposit: e.target.value }))}
              required
            />
          </label>
          <button type="submit">Create</button>
        </form>
      </SectionCard>

      <SectionCard title="Update Account">
        <form className="form-grid" onSubmit={updateAccount}>
          <label>
            Account ID
            <input value={updateForm.account_id} onChange={(e) => setUpdateForm((prev) => ({ ...prev, account_id: e.target.value }))} required />
          </label>
          <label>
            Type
            <select value={updateForm.account_type} onChange={(e) => setUpdateForm((prev) => ({ ...prev, account_type: e.target.value }))}>
              <option value="savings">Savings</option>
              <option value="current">Current</option>
              <option value="fixed_deposit">Fixed Deposit</option>
            </select>
          </label>
          <label>
            Active
            <select value={updateForm.is_active} onChange={(e) => setUpdateForm((prev) => ({ ...prev, is_active: e.target.value }))}>
              <option value="true">True</option>
              <option value="false">False</option>
            </select>
          </label>
          <button type="submit">Update</button>
        </form>
      </SectionCard>

      <SectionCard title="Delete Account (Soft Delete)">
        <form className="inline-form" onSubmit={deleteAccount}>
          <input value={deleteId} onChange={(e) => setDeleteId(e.target.value)} placeholder="Account ID" required />
          <button type="submit">Delete</button>
        </form>
      </SectionCard>

      <SectionCard title="Balance Enquiry">
        <form className="inline-form" onSubmit={checkBalance}>
          <input value={balanceId} onChange={(e) => setBalanceId(e.target.value)} placeholder="Account ID" required />
          <button type="submit">Check</button>
          <span className="pill">Balance: {balance || "-"}</span>
        </form>
      </SectionCard>
    </div>
  );
}
function TransactionsPanel({ token, currentUser, notify }) {
  const [rows, setRows] = useState([]);
  const [transfer, setTransfer] = useState({ from_account_id: "", to_account_id: "", amount: "", description: "", external_bank_name: "" });
  const [filters, setFilters] = useState({ date_from: "", date_to: "", transaction_type: "", min_amount: "", max_amount: "" });
  const [updateForm, setUpdateForm] = useState({ transaction_id: "", description: "", status: "success" });
  const [deleteId, setDeleteId] = useState("");

  const buildQuery = () => {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value) params.set(key, value);
    });
    const query = params.toString();
    return query ? `?${query}` : "";
  };

  const load = async () => {
    try {
      const response = await apiRequest(`/transactions/${buildQuery()}`, { token });
      setRows(response.data.items || []);
    } catch (error) {
      notify("error", error.message);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const submitTransfer = async (event) => {
    event.preventDefault();
    const body = {
      from_account_id: Number(transfer.from_account_id),
      to_account_id: transfer.to_account_id ? Number(transfer.to_account_id) : null,
      external_bank_name: transfer.external_bank_name || null,
      amount: Number(transfer.amount),
      description: transfer.description,
    };

    try {
      const response = await apiRequest("/transactions/", { method: "POST", token, body });
      notify("success", `Transfer complete: ${response.data.transaction_id}`);
      await load();
    } catch (error) {
      notify("error", error.message);
    }
  };

  const updateTransaction = async (event) => {
    event.preventDefault();
    try {
      await apiRequest(`/transactions/${updateForm.transaction_id}`, {
        method: "PUT",
        token,
        body: { description: updateForm.description, status: updateForm.status },
      });
      notify("success", "Transaction updated");
      await load();
    } catch (error) {
      notify("error", error.message);
    }
  };

  const deleteTransaction = async (event) => {
    event.preventDefault();
    try {
      await apiRequest(`/transactions/${deleteId}`, { method: "DELETE", token });
      notify("success", "Transaction deleted");
      setDeleteId("");
      await load();
    } catch (error) {
      notify("error", error.message);
    }
  };

  return (
    <div className="panel-grid">
      <SectionCard title="Transfer Funds">
        <form className="form-grid" onSubmit={submitTransfer}>
          <label>
            From Account
            <input value={transfer.from_account_id} onChange={(e) => setTransfer((prev) => ({ ...prev, from_account_id: e.target.value }))} required />
          </label>
          <label>
            To Account (optional)
            <input value={transfer.to_account_id} onChange={(e) => setTransfer((prev) => ({ ...prev, to_account_id: e.target.value }))} />
          </label>
          <label>
            External Bank (if inter-bank)
            <input value={transfer.external_bank_name} onChange={(e) => setTransfer((prev) => ({ ...prev, external_bank_name: e.target.value }))} />
          </label>
          <label>
            Amount
            <input type="number" step="0.01" value={transfer.amount} onChange={(e) => setTransfer((prev) => ({ ...prev, amount: e.target.value }))} required />
          </label>
          <label>
            Description
            <input value={transfer.description} onChange={(e) => setTransfer((prev) => ({ ...prev, description: e.target.value }))} />
          </label>
          <button type="submit">Transfer</button>
        </form>
      </SectionCard>

      <SectionCard title="Transaction History Filters" actions={<button onClick={load}>Apply</button>}>
        <div className="form-grid filter-grid">
          <label>
            From Date
            <input type="datetime-local" value={filters.date_from} onChange={(e) => setFilters((prev) => ({ ...prev, date_from: e.target.value }))} />
          </label>
          <label>
            To Date
            <input type="datetime-local" value={filters.date_to} onChange={(e) => setFilters((prev) => ({ ...prev, date_to: e.target.value }))} />
          </label>
          <label>
            Type
            <select value={filters.transaction_type} onChange={(e) => setFilters((prev) => ({ ...prev, transaction_type: e.target.value }))}>
              <option value="">Any</option>
              <option value="transfer">Transfer</option>
              <option value="mutual_fund_buy">Mutual Fund Buy</option>
              <option value="mutual_fund_sell">Mutual Fund Sell</option>
              <option value="deposit_create">Deposit Create</option>
              <option value="deposit_cancel">Deposit Cancel</option>
            </select>
          </label>
          <label>
            Min Amount
            <input type="number" step="0.01" value={filters.min_amount} onChange={(e) => setFilters((prev) => ({ ...prev, min_amount: e.target.value }))} />
          </label>
          <label>
            Max Amount
            <input type="number" step="0.01" value={filters.max_amount} onChange={(e) => setFilters((prev) => ({ ...prev, max_amount: e.target.value }))} />
          </label>
        </div>
      </SectionCard>

      <SectionCard title="Transactions" actions={<button onClick={load}>Refresh</button>}>
        <DataTable
          columns={[
            { key: "id", label: "ID" },
            { key: "from_account_id", label: "From" },
            { key: "to_account_id", label: "To" },
            { key: "transaction_type", label: "Type" },
            { key: "amount", label: "Amount" },
            { key: "status", label: "Status" },
            { key: "reference", label: "Reference" },
            { key: "created_at", label: "Time" },
          ]}
          rows={rows}
        />
      </SectionCard>

      {currentUser.is_admin ? (
        <SectionCard title="Admin: Update/Delete Transactions">
          <form className="inline-form" onSubmit={updateTransaction}>
            <input
              placeholder="Transaction ID"
              value={updateForm.transaction_id}
              onChange={(e) => setUpdateForm((prev) => ({ ...prev, transaction_id: e.target.value }))}
              required
            />
            <input
              placeholder="Description"
              value={updateForm.description}
              onChange={(e) => setUpdateForm((prev) => ({ ...prev, description: e.target.value }))}
            />
            <select value={updateForm.status} onChange={(e) => setUpdateForm((prev) => ({ ...prev, status: e.target.value }))}>
              <option value="success">Success</option>
              <option value="failed">Failed</option>
              <option value="pending">Pending</option>
            </select>
            <button type="submit">Update</button>
          </form>
          <form className="inline-form" onSubmit={deleteTransaction}>
            <input placeholder="Transaction ID" value={deleteId} onChange={(e) => setDeleteId(e.target.value)} required />
            <button type="submit">Delete</button>
          </form>
        </SectionCard>
      ) : null}
    </div>
  );
}

function DebitCardsPanel({ token, notify }) {
  const [rows, setRows] = useState([]);
  const [createAccountId, setCreateAccountId] = useState("");
  const [activateForm, setActivateForm] = useState({ card_id: "", otp: "" });
  const [statusForm, setStatusForm] = useState({ card_id: "", status: "active" });
  const [deleteId, setDeleteId] = useState("");

  const load = async () => {
    try {
      const response = await apiRequest("/debit-cards/", { token });
      setRows(response.data.items || []);
    } catch (error) {
      notify("error", error.message);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const createCard = async (event) => {
    event.preventDefault();
    try {
      const response = await apiRequest("/debit-cards/", { method: "POST", token, body: { account_id: Number(createAccountId) } });
      notify("success", `Card ${response.data.card_id} created. OTP: ${response.data.otp}`);
      await load();
    } catch (error) {
      notify("error", error.message);
    }
  };

  const activate = async (event) => {
    event.preventDefault();
    try {
      await apiRequest("/debit-cards/activate", { method: "PUT", token, body: { card_id: Number(activateForm.card_id), otp: activateForm.otp } });
      notify("success", "Card activated");
      await load();
    } catch (error) {
      notify("error", error.message);
    }
  };

  const updateStatus = async (event) => {
    event.preventDefault();
    try {
      await apiRequest(`/debit-cards/${statusForm.card_id}/status`, {
        method: "PUT",
        token,
        body: { status: statusForm.status },
      });
      notify("success", "Card status updated");
      await load();
    } catch (error) {
      notify("error", error.message);
    }
  };

  const deleteCard = async (event) => {
    event.preventDefault();
    try {
      await apiRequest(`/debit-cards/${deleteId}`, { method: "DELETE", token });
      notify("success", "Card disabled");
      setDeleteId("");
      await load();
    } catch (error) {
      notify("error", error.message);
    }
  };

  return (
    <div className="panel-grid">
      <SectionCard title="Debit Cards" actions={<button onClick={load}>Refresh</button>}>
        <DataTable
          columns={[
            { key: "id", label: "ID" },
            { key: "account_id", label: "Account" },
            { key: "card_number", label: "Card Number" },
            { key: "status", label: "Status" },
            { key: "activation_date", label: "Activated" },
            { key: "expiry_date", label: "Expiry" },
          ]}
          rows={rows}
        />
      </SectionCard>

      <SectionCard title="Create Card">
        <form className="inline-form" onSubmit={createCard}>
          <input placeholder="Account ID" value={createAccountId} onChange={(e) => setCreateAccountId(e.target.value)} required />
          <button type="submit">Create</button>
        </form>
      </SectionCard>

      <SectionCard title="Activate Card (OTP)">
        <form className="inline-form" onSubmit={activate}>
          <input placeholder="Card ID" value={activateForm.card_id} onChange={(e) => setActivateForm((prev) => ({ ...prev, card_id: e.target.value }))} required />
          <input placeholder="OTP" value={activateForm.otp} onChange={(e) => setActivateForm((prev) => ({ ...prev, otp: e.target.value }))} required />
          <button type="submit">Activate</button>
        </form>
      </SectionCard>

      <SectionCard title="Enable/Disable Card">
        <form className="inline-form" onSubmit={updateStatus}>
          <input placeholder="Card ID" value={statusForm.card_id} onChange={(e) => setStatusForm((prev) => ({ ...prev, card_id: e.target.value }))} required />
          <select value={statusForm.status} onChange={(e) => setStatusForm((prev) => ({ ...prev, status: e.target.value }))}>
            <option value="active">Active</option>
            <option value="disabled">Disabled</option>
          </select>
          <button type="submit">Update</button>
        </form>
      </SectionCard>

      <SectionCard title="Delete (Disable) Card">
        <form className="inline-form" onSubmit={deleteCard}>
          <input placeholder="Card ID" value={deleteId} onChange={(e) => setDeleteId(e.target.value)} required />
          <button type="submit">Disable</button>
        </form>
      </SectionCard>
    </div>
  );
}
function MutualFundsPanel({ token, currentUser, notify }) {
  const [funds, setFunds] = useState([]);
  const [holdings, setHoldings] = useState([]);
  const [trades, setTrades] = useState([]);
  const [createForm, setCreateForm] = useState({ name: "", symbol: "", nav: "" });
  const [updateForm, setUpdateForm] = useState({ fund_id: "", nav: "" });
  const [deleteId, setDeleteId] = useState("");
  const [buyForm, setBuyForm] = useState({ account_id: "", fund_id: "", amount: "" });
  const [sellForm, setSellForm] = useState({ account_id: "", fund_id: "", units: "" });

  const load = async () => {
    try {
      const [fundResp, holdingResp, tradeResp] = await Promise.all([
        apiRequest("/mutual-funds/", { token }),
        apiRequest("/mutual-funds/holdings", { token }),
        apiRequest("/mutual-funds/trades", { token }),
      ]);
      setFunds(fundResp.data.items || []);
      setHoldings(holdingResp.data.items || []);
      setTrades(tradeResp.data.items || []);
    } catch (error) {
      notify("error", error.message);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const createFund = async (event) => {
    event.preventDefault();
    try {
      const response = await apiRequest("/mutual-funds/", { method: "POST", token, body: { ...createForm, nav: Number(createForm.nav) } });
      notify("success", `Fund created: ${response.data.fund_id}`);
      await load();
    } catch (error) {
      notify("error", error.message);
    }
  };

  const updateFund = async (event) => {
    event.preventDefault();
    try {
      await apiRequest(`/mutual-funds/${updateForm.fund_id}`, {
        method: "PUT",
        token,
        body: { nav: Number(updateForm.nav) },
      });
      notify("success", "Fund NAV updated");
      await load();
    } catch (error) {
      notify("error", error.message);
    }
  };

  const deleteFund = async (event) => {
    event.preventDefault();
    try {
      await apiRequest(`/mutual-funds/${deleteId}`, { method: "DELETE", token });
      notify("success", "Fund deactivated");
      setDeleteId("");
      await load();
    } catch (error) {
      notify("error", error.message);
    }
  };

  const buy = async (event) => {
    event.preventDefault();
    try {
      const response = await apiRequest("/mutual-funds/buy", {
        method: "POST",
        token,
        body: { account_id: Number(buyForm.account_id), fund_id: Number(buyForm.fund_id), amount: Number(buyForm.amount) },
      });
      notify("success", `Buy trade: ${response.data.trade_id}`);
      await load();
    } catch (error) {
      notify("error", error.message);
    }
  };

  const sell = async (event) => {
    event.preventDefault();
    try {
      const response = await apiRequest("/mutual-funds/sell", {
        method: "POST",
        token,
        body: { account_id: Number(sellForm.account_id), fund_id: Number(sellForm.fund_id), units: Number(sellForm.units) },
      });
      notify("success", `Sell trade: ${response.data.trade_id}`);
      await load();
    } catch (error) {
      notify("error", error.message);
    }
  };

  return (
    <div className="panel-grid">
      <SectionCard title="Fund Catalog" actions={<button onClick={load}>Refresh</button>}>
        <DataTable
          columns={[
            { key: "id", label: "ID" },
            { key: "name", label: "Name" },
            { key: "symbol", label: "Symbol" },
            { key: "nav", label: "NAV" },
            { key: "is_active", label: "Active" },
          ]}
          rows={funds}
        />
      </SectionCard>

      {currentUser.is_admin ? (
        <SectionCard title="Admin: Create / Update / Delete Funds">
          <form className="inline-form" onSubmit={createFund}>
            <input placeholder="Name" value={createForm.name} onChange={(e) => setCreateForm((prev) => ({ ...prev, name: e.target.value }))} required />
            <input placeholder="Symbol" value={createForm.symbol} onChange={(e) => setCreateForm((prev) => ({ ...prev, symbol: e.target.value }))} required />
            <input placeholder="NAV" type="number" step="0.0001" value={createForm.nav} onChange={(e) => setCreateForm((prev) => ({ ...prev, nav: e.target.value }))} required />
            <button type="submit">Create</button>
          </form>
          <form className="inline-form" onSubmit={updateFund}>
            <input placeholder="Fund ID" value={updateForm.fund_id} onChange={(e) => setUpdateForm((prev) => ({ ...prev, fund_id: e.target.value }))} required />
            <input placeholder="New NAV" type="number" step="0.0001" value={updateForm.nav} onChange={(e) => setUpdateForm((prev) => ({ ...prev, nav: e.target.value }))} required />
            <button type="submit">Update NAV</button>
          </form>
          <form className="inline-form" onSubmit={deleteFund}>
            <input placeholder="Fund ID" value={deleteId} onChange={(e) => setDeleteId(e.target.value)} required />
            <button type="submit">Deactivate</button>
          </form>
        </SectionCard>
      ) : null}

      <SectionCard title="Buy Fund">
        <form className="inline-form" onSubmit={buy}>
          <input placeholder="Account ID" value={buyForm.account_id} onChange={(e) => setBuyForm((prev) => ({ ...prev, account_id: e.target.value }))} required />
          <input placeholder="Fund ID" value={buyForm.fund_id} onChange={(e) => setBuyForm((prev) => ({ ...prev, fund_id: e.target.value }))} required />
          <input placeholder="Amount" type="number" step="0.01" value={buyForm.amount} onChange={(e) => setBuyForm((prev) => ({ ...prev, amount: e.target.value }))} required />
          <button type="submit">Buy</button>
        </form>
      </SectionCard>

      <SectionCard title="Sell Fund">
        <form className="inline-form" onSubmit={sell}>
          <input placeholder="Account ID" value={sellForm.account_id} onChange={(e) => setSellForm((prev) => ({ ...prev, account_id: e.target.value }))} required />
          <input placeholder="Fund ID" value={sellForm.fund_id} onChange={(e) => setSellForm((prev) => ({ ...prev, fund_id: e.target.value }))} required />
          <input placeholder="Units" type="number" step="0.0001" value={sellForm.units} onChange={(e) => setSellForm((prev) => ({ ...prev, units: e.target.value }))} required />
          <button type="submit">Sell</button>
        </form>
      </SectionCard>

      <SectionCard title="Holdings">
        <DataTable
          columns={[
            { key: "id", label: "ID" },
            { key: "user_id", label: "User" },
            { key: "account_id", label: "Account" },
            { key: "fund_id", label: "Fund" },
            { key: "units", label: "Units" },
            { key: "average_nav", label: "Avg NAV" },
          ]}
          rows={holdings}
        />
      </SectionCard>

      <SectionCard title="Trades">
        <DataTable
          columns={[
            { key: "id", label: "ID" },
            { key: "account_id", label: "Account" },
            { key: "fund_id", label: "Fund" },
            { key: "trade_type", label: "Type" },
            { key: "units", label: "Units" },
            { key: "amount", label: "Amount" },
            { key: "created_at", label: "Time" },
          ]}
          rows={trades}
        />
      </SectionCard>
    </div>
  );
}
function DepositsPanel({ token, notify }) {
  const [rows, setRows] = useState([]);
  const [createForm, setCreateForm] = useState({ account_id: "", deposit_type: "fixed", term_months: 12, amount: "", interest_rate: 6.5 });
  const [cancelId, setCancelId] = useState("");
  const [deleteId, setDeleteId] = useState("");

  const load = async () => {
    try {
      const response = await apiRequest("/deposits/", { token });
      setRows(response.data.items || []);
    } catch (error) {
      notify("error", error.message);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const createDeposit = async (event) => {
    event.preventDefault();
    try {
      const response = await apiRequest("/deposits/", {
        method: "POST",
        token,
        body: {
          account_id: Number(createForm.account_id),
          deposit_type: createForm.deposit_type,
          term_months: Number(createForm.term_months),
          amount: Number(createForm.amount),
          interest_rate: Number(createForm.interest_rate),
        },
      });
      notify("success", `Deposit created: ${response.data.deposit_id}`);
      await load();
    } catch (error) {
      notify("error", error.message);
    }
  };

  const cancelDeposit = async (event) => {
    event.preventDefault();
    try {
      const response = await apiRequest(`/deposits/${cancelId}/cancel`, { method: "PUT", token });
      notify("success", `Deposit cancelled, penalty ${response.data.penalty}`);
      setCancelId("");
      await load();
    } catch (error) {
      notify("error", error.message);
    }
  };

  const deleteDeposit = async (event) => {
    event.preventDefault();
    try {
      await apiRequest(`/deposits/${deleteId}`, { method: "DELETE", token });
      notify("success", "Deposit removed");
      setDeleteId("");
      await load();
    } catch (error) {
      notify("error", error.message);
    }
  };

  return (
    <div className="panel-grid">
      <SectionCard title="Deposits" actions={<button onClick={load}>Refresh</button>}>
        <DataTable
          columns={[
            { key: "id", label: "ID" },
            { key: "account_id", label: "Account" },
            { key: "deposit_type", label: "Type" },
            { key: "term_months", label: "Term (Months)" },
            { key: "amount", label: "Amount" },
            { key: "interest_rate", label: "Rate" },
            { key: "status", label: "Status" },
            { key: "penalty_amount", label: "Penalty" },
          ]}
          rows={rows}
        />
      </SectionCard>

      <SectionCard title="Create Deposit">
        <form className="inline-form" onSubmit={createDeposit}>
          <input placeholder="Account ID" value={createForm.account_id} onChange={(e) => setCreateForm((prev) => ({ ...prev, account_id: e.target.value }))} required />
          <select value={createForm.deposit_type} onChange={(e) => setCreateForm((prev) => ({ ...prev, deposit_type: e.target.value }))}>
            <option value="fixed">Fixed</option>
            <option value="recurring">Recurring</option>
          </select>
          <input placeholder="Term" type="number" value={createForm.term_months} onChange={(e) => setCreateForm((prev) => ({ ...prev, term_months: e.target.value }))} required />
          <input placeholder="Amount" type="number" step="0.01" value={createForm.amount} onChange={(e) => setCreateForm((prev) => ({ ...prev, amount: e.target.value }))} required />
          <input
            placeholder="Interest %"
            type="number"
            step="0.01"
            value={createForm.interest_rate}
            onChange={(e) => setCreateForm((prev) => ({ ...prev, interest_rate: e.target.value }))}
            required
          />
          <button type="submit">Create</button>
        </form>
      </SectionCard>

      <SectionCard title="Cancel Deposit">
        <form className="inline-form" onSubmit={cancelDeposit}>
          <input placeholder="Deposit ID" value={cancelId} onChange={(e) => setCancelId(e.target.value)} required />
          <button type="submit">Cancel</button>
        </form>
      </SectionCard>

      <SectionCard title="Delete Deposit">
        <form className="inline-form" onSubmit={deleteDeposit}>
          <input placeholder="Deposit ID" value={deleteId} onChange={(e) => setDeleteId(e.target.value)} required />
          <button type="submit">Delete</button>
        </form>
      </SectionCard>
    </div>
  );
}

function AuditPanel({ token, currentUser, notify }) {
  const [rows, setRows] = useState([]);

  const load = async () => {
    try {
      const response = await apiRequest("/audit-logs/", { token });
      setRows(response.data.items || []);
    } catch (error) {
      notify("error", error.message);
    }
  };

  useEffect(() => {
    if (currentUser.is_admin) load();
  }, []);

  if (!currentUser.is_admin) {
    return <p className="blocked">Audit logs are available only for admins.</p>;
  }

  return (
    <div className="panel-grid">
      <SectionCard title="Audit Logs" actions={<button onClick={load}>Refresh</button>}>
        <DataTable
          columns={[
            { key: "id", label: "ID" },
            { key: "user_id", label: "User ID" },
            { key: "action", label: "Action" },
            { key: "entity", label: "Entity" },
            { key: "entity_id", label: "Entity ID" },
            { key: "details", label: "Details" },
            { key: "created_at", label: "Time" },
          ]}
          rows={rows}
        />
      </SectionCard>
    </div>
  );
}

export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem("banking_token") || "");
  const [currentUser, setCurrentUser] = useState(null);
  const [activeTab, setActiveTab] = useState("accounts");
  const [notice, setNotice] = useState(null);

  const notify = (type, text) => {
    setNotice({ type, text });
    setTimeout(() => setNotice(null), 5000);
  };

  const logout = () => {
    setToken("");
    setCurrentUser(null);
    localStorage.removeItem("banking_token");
    notify("success", "Logged out");
  };

  useEffect(() => {
    const bootstrap = async () => {
      if (!token) return;
      try {
        localStorage.setItem("banking_token", token);
        const response = await apiRequest("/auth/me", { token });
        setCurrentUser(response.data.user);
      } catch (error) {
        localStorage.removeItem("banking_token");
        setToken("");
        setCurrentUser(null);
        notify("error", `Authentication failed: ${error.message}`);
      }
    };
    bootstrap();
  }, [token]);

  const panel = useMemo(() => {
    if (!currentUser) return null;
    if (activeTab === "users") return <UsersPanel token={token} currentUser={currentUser} notify={notify} />;
    if (activeTab === "accounts") return <AccountsPanel token={token} currentUser={currentUser} notify={notify} />;
    if (activeTab === "transactions") return <TransactionsPanel token={token} currentUser={currentUser} notify={notify} />;
    if (activeTab === "debit_cards") return <DebitCardsPanel token={token} notify={notify} />;
    if (activeTab === "mutual_funds") return <MutualFundsPanel token={token} currentUser={currentUser} notify={notify} />;
    if (activeTab === "deposits") return <DepositsPanel token={token} notify={notify} />;
    return <AuditPanel token={token} currentUser={currentUser} notify={notify} />;
  }, [activeTab, token, currentUser]);

  if (!token || !currentUser) {
    return (
      <>
        <Notice notice={notice} onClose={() => setNotice(null)} />
        <AuthView onAuth={setToken} notify={notify} />
      </>
    );
  }

  return (
    <div className="app-shell">
      <Notice notice={notice} onClose={() => setNotice(null)} />
      <header className="topbar">
        <div>
          <p className="eyebrow">Banking Control Desk</p>
          <h1>Operational Console</h1>
        </div>
        <div className="user-box">
          <span>
            {currentUser.name} ({currentUser.is_admin ? "admin" : "user"})
          </span>
          <button onClick={logout}>Logout</button>
        </div>
      </header>

      <div className="workspace">
        <aside className="sidebar">
          {TABS.map((tab) => (
            <button key={tab.id} className={activeTab === tab.id ? "tab active" : "tab"} onClick={() => setActiveTab(tab.id)}>
              {tab.label}
            </button>
          ))}
        </aside>
        <main className="content">{panel}</main>
      </div>
    </div>
  );
}
