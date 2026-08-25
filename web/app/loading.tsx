export default function Loading() {
  return (
    <div className="page-shell profile-shell" aria-label="Carregando">
      <div className="skeleton" style={{ width: "34%", height: 18 }} />
      <div className="skeleton" style={{ width: "70%", height: 64 }} />
      <div className="profile-grid">
        <div className="profile-section">
          <div className="skeleton" style={{ height: 18, marginBottom: 16 }} />
          <div className="skeleton" style={{ height: 130 }} />
        </div>
        <div className="profile-section">
          <div className="skeleton" style={{ height: 18, marginBottom: 16 }} />
          <div className="skeleton" style={{ height: 130 }} />
        </div>
      </div>
    </div>
  );
}
