import time
import socket
import logging
from django.core.management.base import BaseCommand

logger = logging.getLogger('port_checker')

class Command(BaseCommand):
    help = 'Continuously checks if a port is listening and logs the result'

    def add_arguments(self, parser):
        parser.add_argument('--host', type=str, default='127.0.0.1', help='Host to check')
        parser.add_argument('--port', type=int, default=8000, help='Port to check')
        parser.add_argument('--interval', type=int, default=10, help='Check interval in seconds')

    def handle(self, *args, **options):
        host = options['host']
        port = options['port']
        interval = options['interval']

        self.stdout.write(f"Starting continuous port check on {host}:{port}...")

        while True:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            
            result = sock.connect_ex((host, port))
            if result == 0:
                logger.info(f"SUCCESS: Port {port} is LISTENING on {host}.")
            else:
                logger.warning(f"FAILURE: Port {port} is CLOSED on {host}.")
                
            sock.close()
            time.sleep(interval)
