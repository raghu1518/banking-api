const DEFAULT_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

export async function apiRequest(path, { method = "GET", token, body } = {}) {
  const response = await fetch(`${DEFAULT_BASE_URL}${path}`, {
    method,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  const payload = await response.json().catch(() => ({
    status: "error",
    message: "Invalid server response",
    data: {},
  }));

  if (!response.ok || payload.status === "error") {
    throw new Error(payload.message || "Request failed");
  }

  return payload;
}

export const apiBaseUrl = DEFAULT_BASE_URL;
