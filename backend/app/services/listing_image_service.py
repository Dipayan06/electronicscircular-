"""Product photo upload, retrieval and removal for marketplace listings."""
from fastapi import UploadFile
from sqlalchemy.orm import Session

from ..models import ListingImage, ResaleListing, User
from ..schemas.listing import ListingOut
from ..utils.responses import APIError

MAX_IMAGES = 5
MAX_BYTES = 2 * 1024 * 1024  # 2 MB per image


def _sniff(data: bytes) -> str | None:
    """Image type from the file's magic bytes (never trust the client's header)."""
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def _own_listing(db: Session, user: User, listing_id: int) -> ResaleListing:
    listing = db.query(ResaleListing).filter(ResaleListing.id == listing_id).first()
    if not listing:
        raise APIError("Listing not found", status_code=404)
    if listing.seller_id != user.id:
        raise APIError("Only the seller can change this listing's photos", status_code=403)
    return listing


def add_images(db: Session, user: User, listing_id: int, files: list[UploadFile]) -> ListingOut:
    listing = _own_listing(db, user, listing_id)
    if not files:
        raise APIError("Choose at least one image", status_code=400)
    if len(listing.images) + len(files) > MAX_IMAGES:
        raise APIError(f"A listing can have at most {MAX_IMAGES} photos", status_code=400)

    # Validate every file before saving any, so a bad file doesn't leave a partial upload.
    new = []
    for f in files:
        data = f.file.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise APIError(f"{f.filename or 'Image'} is larger than 2 MB", status_code=400)
        content_type = _sniff(data)
        if not content_type:
            raise APIError(f"{f.filename or 'File'} is not a JPEG, PNG or WebP image", status_code=400)
        new.append(ListingImage(content_type=content_type, data=data))

    listing.images.extend(new)
    db.commit()
    db.refresh(listing)
    return ListingOut.from_orm_listing(listing)


def get_image(db: Session, image_id: int) -> ListingImage:
    image = db.query(ListingImage).filter(ListingImage.id == image_id).first()
    if not image:
        raise APIError("Image not found", status_code=404)
    return image


def delete_image(db: Session, user: User, listing_id: int, image_id: int) -> ListingOut:
    listing = _own_listing(db, user, listing_id)
    image = next((i for i in listing.images if i.id == image_id), None)
    if not image:
        raise APIError("Image not found", status_code=404)
    listing.images.remove(image)
    db.commit()
    db.refresh(listing)
    return ListingOut.from_orm_listing(listing)
