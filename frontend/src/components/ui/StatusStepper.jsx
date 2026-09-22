// StatusStepper — horizontal progress through a status flow (Phase 2 W8).
// Used by collection (REQUESTED→…→RECYCLED) and booking status.
export default function StatusStepper({ steps, current }) {
  const idx = steps.indexOf(current);
  return (
    <div className="stepper">
      {steps.map((step, i) => {
        const done = i <= idx;
        return (
          <div className="stepper-item" key={step}>
            <div className="stepper-node" style={{ background: done ? 'var(--green)' : 'var(--border)' }} />
            {i < steps.length - 1 && (
              <div className="stepper-bar" style={{ background: i < idx ? 'var(--green)' : 'var(--border)' }} />
            )}
            <div className="stepper-label" style={{ color: done ? 'var(--green-dark)' : 'var(--text-muted)', fontWeight: i === idx ? 700 : 500 }}>
              {step.replace(/_/g, ' ')}
            </div>
          </div>
        );
      })}
    </div>
  );
}
