import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, logout } from "../api";
import DonorProfile from "../components/DonorProfile";
import DonorInbox from "../components/DonorInbox";
import RequestBlood from "../components/RequestBlood";

export default function Dashboard() {
  const [me, setMe] = useState(null);
  const [tab, setTab] = useState("request");
  const navigate = useNavigate();

  useEffect(() => {
    api("/auth/me")
      .then((m) => {
        setMe(m);
        // accounts created before this change keep opening on their old side
        setTab(m.role === "donor" ? "donate" : "request");
      })
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
      <div className="tabs">
        <button
          className={tab === "request" ? "tab active" : "tab"}
          onClick={() => setTab("request")}
        >
          I need blood
        </button>
        <button
          className={tab === "donate" ? "tab active" : "tab"}
          onClick={() => setTab("donate")}
        >
          I can donate
        </button>
      </div>

      {/* Both stay mounted so a running request and donor alerts keep updating */}
      <div style={{ display: tab === "request" ? "block" : "none" }}>
        <RequestBlood />
      </div>
      <div style={{ display: tab === "donate" ? "block" : "none" }}>
        <DonorInbox />
        <DonorProfile />
      </div>

      <button className="secondary" onClick={handleLogout}>Logout</button>
    </div>
  );
}