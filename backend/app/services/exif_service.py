import io
import math
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, Tuple
from PIL import Image, ExifTags

# Allowed image MIME types and maximum file size (5 MB)
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


class ImageValidationError(Exception):
    """Raised when an uploaded evidence image fails format, size, or integrity checks."""
    pass


@dataclass
class ExifGpsResult:
    """Safe, sanitized extraction of GPS coordinates from image EXIF metadata."""
    has_gps: bool
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    distance_to_complaint_meters: Optional[float] = None
    is_within_tolerance: bool = False


def validate_image_file(file_bytes: bytes, declared_content_type: str) -> str:
    """
    Validates magic bytes, file size, and image readability.
    Returns the verified MIME type.
    """
    if len(file_bytes) == 0:
        raise ImageValidationError("Uploaded image file is empty.")

    if len(file_bytes) > MAX_IMAGE_SIZE_BYTES:
        raise ImageValidationError(
            f"Image exceeds the maximum allowed size of {MAX_IMAGE_SIZE_BYTES // (1024 * 1024)} MB."
        )

    # Magic byte inspection
    detected_type: Optional[str] = None
    if file_bytes.startswith(b"\xff\xd8\xff"):
        detected_type = "image/jpeg"
    elif file_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        detected_type = "image/png"
    elif file_bytes.startswith(b"RIFF") and len(file_bytes) >= 12 and file_bytes[8:12] == b"WEBP":
        detected_type = "image/webp"

    if not detected_type or detected_type not in ALLOWED_MIME_TYPES:
        raise ImageValidationError(
            "Unsupported image format. Only JPEG, PNG, and WebP files are accepted."
        )

    # Verify Pillow can open and parse image structure
    try:
        with Image.open(io.BytesIO(file_bytes)) as img:
            img.verify()
    except Exception as exc:
        raise ImageValidationError("Corrupted or unreadable image file.") from exc

    return detected_type


def _convert_dms_to_decimal(dms: Tuple, ref: str) -> Optional[Decimal]:
    """Converts (degrees, minutes, seconds) tuple and cardinal reference into decimal degrees."""
    try:
        degrees = float(dms[0])
        minutes = float(dms[1])
        seconds = float(dms[2])
        decimal_val = degrees + (minutes / 60.0) + (seconds / 3600.0)
        if ref in ("S", "W"):
            decimal_val = -decimal_val
        return Decimal(str(round(decimal_val, 6)))
    except Exception:
        return None


def extract_exif_gps(
    file_bytes: bytes,
    complaint_latitude: Optional[Decimal] = None,
    complaint_longitude: Optional[Decimal] = None,
    tolerance_meters: float = 1000.0,
) -> ExifGpsResult:
    """
    Safely extracts GPS coordinates from image EXIF metadata if present.
    Calculates geographic discrepancy with declared complaint location.
    Strips and ignores all other metadata to protect citizen privacy.
    """
    try:
        with Image.open(io.BytesIO(file_bytes)) as img:
            exif = img.getexif()
            if not exif:
                return ExifGpsResult(has_gps=False)

            # Extract GPS IFD
            try:
                gps_ifd = exif.get_ifd(ExifTags.IFD.GPSInfo)
            except Exception:
                return ExifGpsResult(has_gps=False)

            if not gps_ifd:
                return ExifGpsResult(has_gps=False)

            # GPS Tag 2: Latitude, Tag 1: LatitudeRef ('N'/'S')
            # GPS Tag 4: Longitude, Tag 3: LongitudeRef ('E'/'W')
            lat_dms = gps_ifd.get(2)
            lat_ref = gps_ifd.get(1, "N")
            lon_dms = gps_ifd.get(4)
            lon_ref = gps_ifd.get(3, "E")

            if not lat_dms or not lon_dms:
                return ExifGpsResult(has_gps=False)

            latitude = _convert_dms_to_decimal(lat_dms, lat_ref)
            longitude = _convert_dms_to_decimal(lon_dms, lon_ref)

            if latitude is None or longitude is None:
                return ExifGpsResult(has_gps=False)

            # Validate coordinate ranges
            if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
                return ExifGpsResult(has_gps=False)

            result = ExifGpsResult(has_gps=True, latitude=latitude, longitude=longitude)

            # If complaint location is provided, calculate Haversine distance
            if complaint_latitude is not None and complaint_longitude is not None:
                dist = haversine_distance(
                    float(latitude), float(longitude),
                    float(complaint_latitude), float(complaint_longitude),
                )
                result.distance_to_complaint_meters = dist
                result.is_within_tolerance = dist <= tolerance_meters

            return result

    except Exception:
        # Never crash on malformed or non-standard EXIF data
        return ExifGpsResult(has_gps=False)


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two geographic points in meters."""
    r = 6371000.0  # Earth's radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c
