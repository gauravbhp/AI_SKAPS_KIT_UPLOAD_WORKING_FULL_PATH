from waitress import serve
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "packing_list_system.settings")

from packing_list_system.wsgi import application

serve(
    application,
    host="127.0.0.1",
    port=8001,
    threads=20
)