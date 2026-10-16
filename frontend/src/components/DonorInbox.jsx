import { useEffect, useState } from "react";
import { api } from "../api";

export default function DonorInbox() {
  const [alerts, setAlerts] = useState([]);
  const [msg, setMsg] = useState("");
  const [error, setError] = useState("");
  const [showPast, setShowPast] = useState(false);

  async function load() {
    try {
      setAlerts(await api("/alerts/mine"));
    } catch {
      /* try again on the next check */
    }
  }

  useEffect(() => {
    load();
    const timer = setInterval(load, 5000);
    return () => clearInterval(timer);
  }, []);

  async function respond(id, action) {
    setError("");
    setMsg("");
    try {
      const res = await api(`/alerts/${id}/respond`, { method: "POST", body: { action } });
      setMsg(res.message);
      load();
    } catch (err) {
      setError(err.message);
    }
  }

  const isOpen = (a) => a.my_status === "sent" && a.request_status === "searching";
  const openAlerts = alerts.filter(isOpen);
  const pastAlerts = alerts.filter((a) => !isOpen(a));

  function card(a) {
    const open = isOpen(a);
    return (
      <div className="alert-card" key={a.alert_id}>
        <div>
          {a.urgency === "urgent" && <span className="badge-urgent">URGENT </span>}
          <b>{a.blood_group}</b> blood needed at <b>{a.hospital}</b>
        </div>
        {a.distance_km !== null && <div>{a.distance_km} km from you</div>}
        {open ? (
          <div className="row">
            <button onClick={() => respond(a.alert_id, "accept")}>Accept</button>
            <button className="secondary" onClick={() => respond(a.alert_id, "decline")}>
              Decline
            </button>
          </div>
        ) : (
          <div style={{ marginTop: 8 }}>
            {a.my_status === "accepted" && "You accepted this request ✓"}
            {a.my_status === "declined" && "You declined this request"}
            {a.my_status === "sent" && "Already filled by another donor"}
          </div>
        )}
      </div>
    );
  }

  return (
    <div>
      <h3>Blood requests near you</h3>
      {msg && <div className="success">{msg}</div>}
      {error && <div className="error">{error}</div>}
      {openAlerts.length === 0 && (
        <p>No open requests right now. This page checks for new requests every 5 seconds.</p>
      )}
      {openAlerts.map(card)}
      {pastAlerts.length > 0 && (
        <>
          <button className="secondary" onClick={() => setShowPast(!showPast)}>
            {showPast ? "Hide" : "Show"} past requests ({pastAlerts.length})
          </button>
          {showPast && pastAlerts.map(card)}
        </>
      )}
    </div>
  );
}