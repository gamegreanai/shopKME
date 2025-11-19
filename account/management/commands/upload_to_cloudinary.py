from django.core.management.base import BaseCommand
from django.conf import settings
import cloudinary.uploader
import os
from pathlib import Path

class Command(BaseCommand):
    help = 'Upload existing media files to Cloudinary'

    def handle(self, *args, **options):
        if not settings.USE_CLOUDINARY:
            self.stdout.write(self.style.ERROR('❌ USE_CLOUDINARY is False. Set it to True first.'))
            return

        media_root = Path(settings.MEDIA_ROOT)
        
        if not media_root.exists():
            self.stdout.write(self.style.ERROR(f'❌ Media folder not found: {media_root}'))
            return

        uploaded_count = 0
        failed_count = 0
        
        self.stdout.write(self.style.SUCCESS(f'📂 Scanning: {media_root}'))
        self.stdout.write(self.style.SUCCESS('⏳ Uploading to Cloudinary...\n'))
        
        for root, dirs, files in os.walk(media_root):
            for file in files:
                # Skip non-image files
                if not file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg')):
                    continue
                
                file_path = Path(root) / file
                relative_path = file_path.relative_to(media_root)
                
                # Upload to Cloudinary maintaining folder structure
                public_id = str(relative_path).replace('\\', '/').rsplit('.', 1)[0]
                
                try:
                    result = cloudinary.uploader.upload(
                        str(file_path),
                        public_id=public_id,
                        overwrite=True,
                        resource_type="auto",
                        folder=""  # Empty to use public_id path directly
                    )
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ {relative_path} → {result["secure_url"]}')
                    )
                    uploaded_count += 1
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'❌ {relative_path}: {str(e)}')
                    )
                    failed_count += 1

        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS(f'✅ Uploaded: {uploaded_count} files'))
        if failed_count > 0:
            self.stdout.write(self.style.ERROR(f'❌ Failed: {failed_count} files'))
        self.stdout.write('='*70)
