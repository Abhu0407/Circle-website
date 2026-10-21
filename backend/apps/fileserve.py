"""Sending stored files (chat attachments, post videos) to the browser.

Supports Range requests, so video players can skip ahead without loading
the whole file, and adds headers that stop browsers from guessing the type
or running anything inside the file.
"""

import re

from django.http import FileResponse, Http404, HttpResponse, StreamingHttpResponse
from django.utils.http import content_disposition_header

CHUNK = 64 * 1024


def _read(file, length):
    try:
        while length > 0:
            chunk = file.read(min(CHUNK, length))
            if not chunk:
                break
            length -= len(chunk)
            yield chunk
    finally:
        file.close()


def secure(response):
    response['X-Content-Type-Options'] = 'nosniff'
    response['Content-Security-Policy'] = "default-src 'none'; img-src 'self'; media-src 'self'; sandbox"
    response['Cross-Origin-Resource-Policy'] = 'same-origin'
    response['Cache-Control'] = 'private, max-age=86400'
    return response


def serve_file(request, field_file, content_type, filename, inline=True):
    """Response for a FieldFile: whole, or the byte range asked for."""
    try:
        file = field_file.open('rb')
        size = field_file.size
    except FileNotFoundError:
        raise Http404

    match = re.fullmatch(r'bytes=(\d*)-(\d*)', request.headers.get('Range', ''))
    if match and (match[1] or match[2]):
        if match[1]:
            start = int(match[1])
            end = min(int(match[2]), size - 1) if match[2] else size - 1
        else:  # bytes=-500: the last 500 bytes
            start, end = max(size - int(match[2]), 0), size - 1
        if start > end or start >= size:
            file.close()
            response = HttpResponse(status=416)
            response['Content-Range'] = f'bytes */{size}'
            return secure(response)
        file.seek(start)
        response = StreamingHttpResponse(_read(file, end - start + 1), status=206, content_type=content_type)
        response['Content-Range'] = f'bytes {start}-{end}/{size}'
        response['Content-Length'] = str(end - start + 1)
    else:
        response = FileResponse(file, content_type=content_type)
        response['Content-Length'] = str(size)
    response['Accept-Ranges'] = 'bytes'
    response['Content-Disposition'] = content_disposition_header(not inline, filename)
    return secure(response)
