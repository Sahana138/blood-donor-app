const API = "http://127.0.0.1:8000";

export function getToken() {
  return localStorage.getItem("token");
}

export function logout() {
  localStorage.clear();
}

export async function api(path, { method = "GET", body, form } = {}) {
  const headers = {};
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  let payload;
  if (form) {
    payload = new URLSearchParams(form);
    headers["Content-Type"] = "application/x-www-form-urlencoded";
  } else if (body) {
    payload = JSON.stringify(body);
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(API + path, { method, headers, body: payload });
  const data = await res.json().catch(() => null);

  if (!res.ok) {
    const detail = data?.detail;
    if (Array.isArray(detail)) throw new Error(detail.map((d) => d.msg).join(", "));
    throw new Error(detail || "Something went wrong");
  }
  return data;
}

export async function login(email, password) {
  const data = await api("/auth/login", {
    method: "POST",
    form: { username: email, password },
  });
  localStorage.setItem("token", data.access_token);
  const me = await api("/auth/me");
  localStorage.setItem("role", me.role);
  return me;
}