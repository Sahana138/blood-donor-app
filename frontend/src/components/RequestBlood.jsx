import { useEffect, useState } from "react";
import { api } from "../api";
import MapView from "./MapView";

const GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"];

export default function RequestBlood() {
  const [form, setForm] = useState({
    blood_group: "B+",
    hospital: "",
    latitude: "12.3051",
    longitude: "76.6551",
    urgency: "normal",
  });
  const [requestId, setRequestId] = useState(null);
  const [status, setStatus] = useState(null);
  const [error, setError] = useState("");

  // After a request is created, check its status every 5 seconds
  useEffect(() => {
    if (!requestId) return;
    let timer;
    async function check() {
      try {
        const s = await api(`/requests/${requestId}`);
        setStatus(s);
        if (s.status === "accepted") clearInterval(timer);
      } catch {
        /* ignore and try again */
      }
    }
    check();
    timer = setInterval(check, 5000);
    return () => clearInterval(timer);
  }, [requestId]);

  function update(field, value) {
    setForm({ ...form, [field]: value });
  }

  function fillLocation() {
    navigator.geolocation.getCurrentPosition(
      (pos) =>
        setForm((f) => ({
          ...f,
          latitude: pos.coords.latitude.toFixed(5),
          longitude: pos.coords.longitude.toFixed(5),
        })),
      () => setError("Could not get your location. Please type it.")
    );
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    try {
      const res = await api("/requests", {
        method: "POST",
        body: {
          ...form,
          latitude: parseFloat(form.latitude),
          longitude: parseFloat(form.longitude),
        },
      });
      setStatus(null);
      setRequestId(res.request.id);
    } catch (err) {
      setError(err.message);
    }
  }

  function reset() {
    setRequestId(null);
    setStatus(null);
  }

  if (requestId) {
    return (
      <div>
        <h3>Request #{requestId}</h3>
        {!status && <p>Sending alerts...</p>}
        {status && (
          <>
            <div className="box">
              <div>Blood group: <b>{status.blood_group}</b></div>
              <div>Hospital: {status.hospital}</div>
              <div>Donors alerted: <b>{status.donors_alerted}</b></div>
              <div>Status: <b>{status.status}</b></div>
              <MapView status={status} />
            </div>
            {status.status === "searching" && (
              <p>Waiting for a donor to accept. More donors are alerted automatically if nobody responds.</p>
            )}
            {status.accepted_donor && (
              <div className="success">
                <b>{status.accepted_donor.name}</b> accepted ({status.accepted_donor.blood_group},{" "}
                {status.accepted_donor.area}).
                <br />
                Phone: <b>{status.accepted_donor.phone}</b>
              </div>
            )}
          </>
        )}
        <button className="secondary" onClick={reset}>New request</button>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit}>
      <h3>Request blood</h3>
      <label>Blood group needed</label>
      <select value={form.blood_group} onChange={(e) => update("blood_group", e.target.value)}>
        {GROUPS.map((g) => (
          <option key={g}>{g}</option>
        ))}
      </select>
      <label>Hospital</label>
      <input value={form.hospital} onChange={(e) => update("hospital", e.target.value)} required />
      <div className="row">
        <div>
          <label>Latitude</label>
          <input value={form.latitude} onChange={(e) => update("latitude", e.target.value)} required />
        </div>
        <div>
          <label>Longitude</label>
          <input value={form.longitude} onChange={(e) => update("longitude", e.target.value)} required />
        </div>
      </div>
      <button type="button" className="secondary" onClick={fillLocation}>
        Use my current location
      </button>
      <label>Urgency</label>
      <select value={form.urgency} onChange={(e) => update("urgency", e.target.value)}>
        <option value="normal">Normal</option>
        <option value="urgent">Urgent</option>
      </select>
      {error && <div className="error">{error}</div>}
      <button type="submit">Send request</button>
    </form>
  );
}