import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, login } from "../api";

export default function Register() {
  const [form, setForm] = useState({ name: "", email: "", phone: "", password: "", role: "member" });
  const [error, setError] = useState("");
  const navigate = useNavigate();

  function update(field, value) {
    setForm({ ...form, [field]: value });
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    try {
      await api("/auth/register", { method: "POST", body: form });
      await login(form.email, form.password);
      navigate("/dashboard");
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="card">
      <h2>Create account</h2>
      <form onSubmit={handleSubmit}>
        <label>Name</label>
        <input value={form.name} onChange={(e) => update("name", e.target.value)} required />
        <label>Email</label>
        <input type="email" value={form.email} onChange={(e) => update("email", e.target.value)} required />
        <label>Phone</label>
        <input value={form.phone} onChange={(e) => update("phone", e.target.value)} required />
        <label>Password</label>
        <input type="password" value={form.password} onChange={(e) => update("password", e.target.value)} required />
        {error && <div className="error">{error}</div>}
        <button type="submit">Register</button>
      </form>
      <div className="link">
        Already have an account? <Link to="/login">Login</Link>
      </div>
    </div>
  );
}