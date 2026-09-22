// Loading indicator (Phase 0 §14, Phase 2 §2.7). Shown while data is fetched.
export default function LoadingState({ label = 'Loading…' }) {
  return (
    <div className="loading">
      <span className="spinner" aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}
