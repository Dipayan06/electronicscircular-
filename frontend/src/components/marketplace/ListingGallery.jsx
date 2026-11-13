// ListingGallery — product photos on the listing page. The seller can add and
// remove photos here; everyone else just browses them.
import { useState } from 'react';
import { Trash2 } from 'lucide-react';
import { useToast } from '../../context/ToastContext';
import { imageUrl, uploadListingImages, deleteListingImage, MAX_PHOTOS } from '../../services/listingService';
import PhotoPicker from './PhotoPicker';
import Button from '../ui/Button';

export default function ListingGallery({ listing, isOwner, onChange }) {
  const toast = useToast();
  const images = listing.images || [];
  const [active, setActive] = useState(0);
  const [pending, setPending] = useState([]);
  const [busy, setBusy] = useState(false);
  const current = images[Math.min(active, images.length - 1)];

  async function upload() {
    setBusy(true);
    try {
      const updated = await uploadListingImages(listing.id, pending);
      setPending([]);
      setActive(updated.images.length - 1);
      toast.success('Photos uploaded');
      onChange(updated);
    } catch (e) {
      toast.error(e.message);
    } finally {
      setBusy(false);
    }
  }

  async function remove(image) {
    setBusy(true);
    try {
      const updated = await deleteListingImage(listing.id, image.id);
      setActive(0);
      toast.success('Photo removed');
      onChange(updated);
    } catch (e) {
      toast.error(e.message);
    } finally {
      setBusy(false);
    }
  }

  if (!images.length && !isOwner) return null;

  return (
    <div className="card gallery">
      {current ? (
        <div className="gallery-main">
          <img src={imageUrl(current)} alt={listing.title} />
          {isOwner && (
            <Button variant="danger" onClick={() => remove(current)} disabled={busy}>
              <Trash2 size={15} /> Remove
            </Button>
          )}
        </div>
      ) : (
        <div className="gallery-empty">No photos yet. Listings with photos get more buyer interest.</div>
      )}

      {images.length > 1 && (
        <div className="gallery-thumbs">
          {images.map((img, i) => (
            <button type="button" key={img.id} className={`gallery-thumb${img === current ? ' active' : ''}`}
                    onClick={() => setActive(i)} aria-label={`Show photo ${i + 1}`}>
              <img src={imageUrl(img)} alt="" />
            </button>
          ))}
        </div>
      )}

      {isOwner && images.length < MAX_PHOTOS && (
        <div style={{ marginTop: 14 }}>
          <PhotoPicker files={pending} onChange={setPending} max={MAX_PHOTOS - images.length} disabled={busy} />
          {pending.length > 0 && (
            <div style={{ marginTop: 10 }}>
              <Button onClick={upload} disabled={busy}>
                {busy ? 'Uploading…' : `Upload ${pending.length} photo${pending.length === 1 ? '' : 's'}`}
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
