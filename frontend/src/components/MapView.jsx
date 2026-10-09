import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";

export default function MapView({ status }) {
  if (!status || status.latitude == null) return null;
  const center = [status.latitude, status.longitude];

  return (
    <MapContainer
      center={center}
      zoom={13}
      style={{ height: 280, borderRadius: 8, marginTop: 12 }}
    >
      <TileLayer
        attribution="&copy; OpenStreetMap contributors"
        url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <CircleMarker
        center={center}
        radius={11}
        pathOptions={{ color: "#b3202a", fillColor: "#b3202a", fillOpacity: 0.9 }}
      >
        <Popup>Hospital: {status.hospital}</Popup>
      </CircleMarker>
      {status.nearby_donors.map((d, i) => (
        <CircleMarker
          key={i}
          center={[d.lat, d.lng]}
          radius={7}
          pathOptions={{
            color: d.status === "accepted" ? "#1e8e3e" : "#1a56db",
            fillColor: d.status === "accepted" ? "#1e8e3e" : "#1a56db",
            fillOpacity: 0.8,
          }}
        >
          <Popup>Donor ({d.status}), approximate location</Popup>
        </CircleMarker>
      ))}
    </MapContainer>
  );
}