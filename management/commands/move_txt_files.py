# management/commands/move_txt_files.py
from django.core.management.base import BaseCommand
from packing_system.views import move_text_files_with_db_query

class Command(BaseCommand):
    help = 'Move text files from source to destination based on database data'
    
    def handle(self, *args, **options):
        self.stdout.write("Starting file move operation...")
        success = move_text_files_with_db_query()
        if success:
            self.stdout.write(self.style.SUCCESS("File move completed successfully"))
        else:
            self.stdout.write(self.style.ERROR("File move failed"))