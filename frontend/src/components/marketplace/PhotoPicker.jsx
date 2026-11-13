// PhotoPicker — choose product photos with previews, before they are uploaded.
// Controlled: `files` is a File[]; `onChange` receives the new array. `max` is how
// many more photos may be added (5 minus any already on the listing).
import { useEffect, useMemo, useRef, useState } from 'react';
import { ImagePlus, X } from 'lucide-react';
import { MAX_PHOTOS, MAX_PHOTO_BYTES, PHOTO_TYPES } from '../../services/listingService';

export default function PhotoPicker({ files, onChange, max = MAX_PHOTOS, disabled = false }) {
  const input = useRef(null);
  const [error, setError] = useState('');
  const previews = useMemo(() => files.map((f) => URL.createObjectURL(f)), [files]);
  useEffect(() => () => previews.forEach((u) => URL.revokeObjectURL(u)), [previews]);

  function pick(e) {
    const chosen = Array.from(e.target.files || []);
    e.target.value = ''; // allow picking the same file again after removing it
    const bad = chosen.find((f) => !PHOTO_TYPES.includes(f.type));
    const big = chosen.find((f) => f.size > MAX_PHOTO_BYTES);
    if (bad) { setError(`${bad.name} is not a JPEG, PNG or WebP image.`); return; }
    if (big) { setError(`${big.name} is larger than 2 MB.`); return; }
    const next = [...files, ...chosen];
    if (next.length > max) { setError(`You can add up to ${max} photo${max === 1 ? '' : 's'}.`); return; }
    setError('');
    onChange(next);
  }

  return (
    <div>
      <div className="photo-grid">
        {previews.map((src, i) => (
          <div className="photo-tile" key={src}>
            <img src={src} alt={`Selected photo ${i + 1}`} />
            <button type="button" className="photo-remove" aria-label={`Remove photo ${i + 1}`}
                    onClick={() => onChange(files.filter((_, j) => j !== i))} disabled={disabled}>
              <X size={14} />
            </button>
          </div>
        ))}
        {files.length < max && (
          <button type="button" className="photo-add" onClick={() => input.current?.click()} disabled={disabled}>
            <ImagePlus size={22} />
            <span>Add photo</span>
          </button>
        )}
      </div>
      <input ref={input} type="file" accept={PHOTO_TYPES.join(',')} multiple hidden onChange={pick} />
      <div className="photo-hint">JPEG, PNG or WebP · up to 2 MB each · max {MAX_PHOTOS} per listing</div>
      {error && <div className="photo-error" role="alert">{error}</div>}
    </div>
  );
}
