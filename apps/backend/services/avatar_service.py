"""Validate and normalize uploaded avatars before storing them on disk."""
import io
import warnings
from pathlib import Path

from fastapi import HTTPException
from PIL import Image, ImageOps, UnidentifiedImageError

MAX_AVATAR_BYTES = 5 * 1024 * 1024
MAX_AVATAR_PIXELS = 20_000_000
AVATAR_URL_PREFIX = "/media/avatars/"
AVATAR_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


def normalize_avatar(data: bytes) -> bytes:
    if not data:
        raise HTTPException(422, "Ảnh tải lên không được để trống")
    if len(data) > MAX_AVATAR_BYTES:
        raise HTTPException(413, "Ảnh đại diện không được vượt quá 5 MB")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as image:
                if image.format not in {"JPEG", "PNG", "WEBP"}:
                    raise HTTPException(415, "Chỉ hỗ trợ ảnh JPG, PNG hoặc WebP")
                if image.width * image.height > MAX_AVATAR_PIXELS:
                    raise HTTPException(422, "Ảnh quá lớn, vui lòng chọn ảnh dưới 20 megapixel")
                image.verify()
            with Image.open(io.BytesIO(data)) as image:
                oriented = ImageOps.exif_transpose(image)
                rgba = oriented.convert("RGBA")
                background = Image.new("RGB", rgba.size, "white")
                background.paste(rgba, mask=rgba.getchannel("A"))
                avatar = ImageOps.fit(background, (512, 512), Image.Resampling.LANCZOS)
                output = io.BytesIO()
                avatar.save(output, format="JPEG", quality=88)
                return output.getvalue()
    except HTTPException:
        raise
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError,
            Image.DecompressionBombWarning) as exc:
        raise HTTPException(422, "Tệp không phải ảnh hợp lệ hoặc đã bị hỏng") from exc


def remove_owned_avatar(directory: Path, avatar_url: str | None, user_id) -> None:
    """Only remove a generated avatar belonging to this user, never external URLs."""
    if not avatar_url or not avatar_url.startswith(AVATAR_URL_PREFIX):
        return
    filename = avatar_url.removeprefix(AVATAR_URL_PREFIX)
    if Path(filename).name != filename or not filename.startswith(f"{user_id}-") or not filename.endswith(".jpg"):
        return
    try:
        (directory / filename).unlink(missing_ok=True)
    except OSError:
        # A cleanup failure must not invalidate a successfully saved profile.
        pass
