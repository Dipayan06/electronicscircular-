// Reusable button (Phase 0 §14 component kit).
// variant: 'primary' | 'secondary' | 'ghost' | 'success' (approve) | 'danger' (reject)
export default function Button({
  variant = 'primary',
  block = false,
  type = 'button',
  children,
  ...props
}) {
  const cls = ['btn', `btn-${variant}`, block ? 'btn-block' : ''].join(' ').trim();
  return (
    <button type={type} className={cls} {...props}>
      {children}
    </button>
  );
}
