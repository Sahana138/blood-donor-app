import { useEffect, useState } from "react";
import { api } from "../api";

const GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"];

export default function DonorProfile() {
  const [form, setForm] = useState({
    blood_group: "B+",
    area: "Mysuru",
    latitude: "12.2958",
    longitude: "76.6394",
    last_donated: "",
    available: true,
  });
  const [msg, setMsg] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    api("/donors/me")
      .then((d) => setForm({ ...d, last_donated: d.last_donated || "" }))
      .catch(() => {}); // no profile yet
  }, []);

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
    setMsg("");
    setError("");
    try {
      await api("/donors/me", {
        method: "PUT",
        body: {
          blood_group: form.blood_group,
          area: form.area,
          latitude: parseFloat(form.latitude),
          longitude: parseFloat(form.longitude),
          last_donated: form.last_donated || null,
          available: form.available,
        },
      });
      setMsg("Profile saved. You can now receive blood requests.");
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <h3>My donor profile</h3>
      <label>Blood group</label>
      <select value={form.blood_group} onChange={(e) => update("blood_group", e.target.value)}>
        {GROUPS.map((g) => (
          <option key={g}>{g}</option>
        ))}
      </select>
      <label>Area</label>
      <input value={form.area} onChange={(e) => update("area", e.target.value)} required />
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
      <label>Last donated (leave empty if never)</label>
      <input type="date" value={form.last_donated} onChange={(e) => update("last_donated", e.target.value)} />
      <label>
        <input
          type="checkbox"
          checked={form.available}
          onChange={(e) => update("available", e.target.checked)}
        />
        I am available to donate
      </label>
      {msg && <div className="success">{msg}</div>}
      {error && <div className="error">{error}</div>}
      <button type="submit">Save profile</button>
    </form>
  );
}