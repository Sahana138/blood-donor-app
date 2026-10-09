import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, logout } from "../api";

export default function Dashboard() {
  const [me, setMe] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    api("/auth/me")
      .then(setMe)
      .catch(() => {
        logout();
        navigate("/login");
      });
  }, [navigate]);

  function handleLogout() {
    logout();
    navigate("/login");
  }

  if (!me) return <div className="card">Loading...</div>;

  return (
    <div className="card">
      <h2>Welcome, {me.name}</h2>
      <p>Role: <b>{me.role}</b></p>
      <button onClick={handleLogout}>Logout</button>
    </div>
  );
}