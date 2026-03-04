import io
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

# Pillow is an optional dependency for image processing. In environments where
# Pillow is not available (for example when the Lambda package wasn't built
# with native binaries), provide graceful fallbacks so the service continues
# to run without image transformations.
try:
    from PIL import Image, ImageOps, ImageFilter, ImageStat
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False


def preprocess_image_bytes(image_bytes: bytes, max_side: int = 1024, jpeg_quality: int = 85) -> bytes:
    """
    Apply EXIF-aware auto-orientation and aspect-preserving resize.

    Returns processed image bytes (JPEG or PNG depending on transparency).
    On any failure, returns the original bytes.
    """
    if not PIL_AVAILABLE:
        logger.debug("Pillow not available; skipping image preprocessing")
        return image_bytes

    try:
        with io.BytesIO(image_bytes) as inp:
            img = Image.open(inp)
            # Auto-orient using EXIF data when available
            img = ImageOps.exif_transpose(img)

            # Determine if resize is needed
            width, height = img.size
            max_dim = max(width, height)
            if max_dim > max_side:
                scale = max_side / float(max_dim)
                new_size = (int(width * scale), int(height * scale))
                img = img.resize(new_size, Image.LANCZOS)

            # Choose output format: preserve alpha as PNG, otherwise use JPEG for smaller size
            has_alpha = img.mode in ("LA", "RGBA") or (hasattr(img, 'info') and img.info.get('transparency'))
            out_buf = io.BytesIO()
            if has_alpha:
                img.save(out_buf, format='PNG', optimize=True)
            else:
                # Ensure RGB for JPEG
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                img.save(out_buf, format='JPEG', quality=jpeg_quality, optimize=True)

            return out_buf.getvalue()

    except Exception as e:
        logger.warning(f"Image preprocessing failed, using original bytes: {e}")
        return image_bytes


def is_blurry(image_bytes: bytes, threshold: float = 100.0) -> bool:
    """
    Rough blur detection using edge variance.

    Returns True if the image is likely blurry. The threshold may need tuning
    per dataset; higher values are more permissive (fewer images flagged blurry).
    On any error, returns False (do not block by default).
    """
    if not PIL_AVAILABLE:
        logger.debug("Pillow not available; skipping blur detection")
        return False

    try:
        with io.BytesIO(image_bytes) as inp:
            img = Image.open(inp)
            img = ImageOps.exif_transpose(img)
            # Convert to grayscale and detect edges
            gray = img.convert('L')
            edges = gray.filter(ImageFilter.FIND_EDGES)
            stat = ImageStat.Stat(edges)
            # variance is a list; for grayscale take first channel
            var = stat.var[0] if stat.var else 0.0
            logger.debug(f"Blur detection variance: {var}")
            return float(var) < float(threshold)
    except Exception as e:
        logger.debug(f"Blur detection failed: {e}")
        return False
