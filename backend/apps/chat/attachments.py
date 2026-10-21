"""Checking files sent in chat before they are saved.

- Size: at most settings.CHAT_MAX_FILE_MB.
- Program/script files that could run on a member's computer are refused.
- Photos (JPEG, PNG, GIF, WebP) must really be pictures (opened with
  Pillow). JPEG/PNG/WebP are saved again without their metadata, which
  removes hidden details such as the GPS location where they were taken.
- Videos (MP4, MOV, WebM, Ogg) must start like a real video file.
- Anything else is kept as a plain file and only ever offered as a download.
The kind decides how ChatFileView serves it (shown in the page or downloaded).
"""

import io
import re
from dataclasses import dataclass
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from PIL import Image, ImageOps, UnidentifiedImageError
from rest_framework.exceptions import ValidationError

from .models import Kind

# Files Windows (or a browser) would run when opened.
BLOCKED_EXTENSIONS = {
    '.exe', '.msi', '.msp', '.bat', '.cmd', '.com', '.scr', '.pif', '.cpl', '.dll', '.sys',
    '.vbs', '.vbe', '.js', '.jse', '.wsf', '.wsh', '.ps1', '.psm1', '.hta', '.lnk', '.reg',
    '.jar', '.application', '.appref-ms', '.gadget', '.inf', '.msc', '.html', '.htm', '.xhtml',
    '.svg', '.svgz',
}

IMAGE_FORMATS = {'JPEG': 'image/jpeg', 'PNG': 'image/png', 'GIF': 'image/gif', 'WEBP': 'image/webp'}
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
# Extension -> served type. MOV is usually H.264 inside, which browsers play as MP4.
VIDEO_TYPES = {'.mp4': 'video/mp4', '.m4v': 'video/mp4', '.mov': 'video/mp4', '.webm': 'video/webm', '.ogv': 'video/ogg'}


@dataclass
class Attachment:
    content: object  # what gets saved: the upload itself, or a cleaned copy
    name: str
    size: int
    kind: str
    content_type: str
    width: int = None
    height: int = None


def max_bytes():
    return settings.CHAT_MAX_FILE_MB * 1024 * 1024


def clean_name(name):
    """The file name to show: no folders, no control characters, not too long."""
    name = Path(str(name).replace('\\', '/')).name
    name = re.sub(r'[\x00-\x1f\x7f"]', '', name).strip() or 'file'
    if len(name) > 200:
        suffix = Path(name).suffix[:20]
        name = name[:200 - len(suffix)] + suffix
    return name


def read_head(upload, n=16):
    upload.seek(0)
    head = upload.read(n)
    upload.seek(0)
    return head


def looks_like_video(ext, head):
    """True if a file named *ext starts the way that kind of video does."""
    if ext in ('.mp4', '.m4v', '.mov'):
        return head[4:8] in (b'ftyp', b'moov', b'mdat', b'wide', b'free', b'skip')
    if ext == '.webm':
        return head[:4] == b'\x1a\x45\xdf\xa3'
    if ext == '.ogv':
        return head[:4] == b'OggS'
    return False


def _image(upload, name, ext):
    """An Attachment for a real picture, or None if it isn't one."""
    try:
        upload.seek(0)
        with Image.open(upload) as probe:
            probe.verify()  # catches broken / fake pictures
        upload.seek(0)
        img = Image.open(upload)
        fmt = img.format
        if fmt not in IMAGE_FORMATS:
            return None
        animated = getattr(img, 'is_animated', False)
        if fmt == 'GIF' or animated:
            # Kept as sent (re-saving would lose the animation).
            width, height = img.size
            if img.getexif().get(0x0112) in (5, 6, 7, 8):  # rotated a quarter turn
                width, height = height, width
            upload.seek(0)
            return Attachment(upload, name, upload.size, Kind.IMAGE, IMAGE_FORMATS[fmt], width, height)

        # Turn it upright, then save a copy without metadata (EXIF/GPS).
        img = ImageOps.exif_transpose(img)
        if fmt == 'JPEG' and img.mode not in ('RGB', 'L'):
            img = img.convert('RGB')
        out = io.BytesIO()
        options = {'JPEG': {'quality': 90, 'optimize': True}, 'WEBP': {'quality': 90}, 'PNG': {'optimize': True}}[fmt]
        img.save(out, fmt, **options)
        data = out.getvalue()
        return Attachment(ContentFile(data), name, len(data), Kind.IMAGE, IMAGE_FORMATS[fmt], *img.size)
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError, Image.DecompressionBombError):
        return None
    finally:
        upload.seek(0)


def check_upload(upload):
    """Validate an uploaded file and work out how to show it."""
    name = clean_name(upload.name)
    ext = Path(name).suffix.lower()
    if upload.size == 0:
        raise ValidationError({'file': 'This file is empty.'})
    if upload.size > max_bytes():
        raise ValidationError({'file': f'Files can be at most {settings.CHAT_MAX_FILE_MB} MB.'})
    if ext in BLOCKED_EXTENSIONS:
        raise ValidationError({'file': f'For everyone\'s safety, {ext} files can\'t be sent.'})

    if ext in IMAGE_EXTENSIONS:
        image = _image(upload, name, ext)
        if image is not None:
            return image
    elif ext in VIDEO_TYPES and looks_like_video(ext, read_head(upload)):
        return Attachment(upload, name, upload.size, Kind.VIDEO, VIDEO_TYPES[ext])
    return Attachment(upload, name, upload.size, Kind.FILE, 'application/octet-stream')
