import os
from django.conf import settings
import uuid

def save_uploaded_file(file, pk_code):
    """Save uploaded file directly inside MEDIA_ROOT with unique filename."""
    ext = file.name.split('.')[-1]
    filename = f"{pk_code}_{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(settings.MEDIA_ROOT, filename)
    
    # Write file directly; no os.makedirs() needed because MEDIA_ROOT already exists
    with open(filepath, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)
    
    return filename

def delete_uploaded_file(filename):
    """Delete uploaded file directly from MEDIA_ROOT."""
    filepath = os.path.join(settings.MEDIA_ROOT, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        return True
    return False

def get_file_url(filename):
    """Return URL for a file stored in MEDIA_ROOT."""
    return f"{settings.MEDIA_URL}{filename}" if filename else None
