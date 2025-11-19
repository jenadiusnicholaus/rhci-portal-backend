from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Fix inconsistent migration history'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Check current state
            cursor.execute("""
                SELECT app, name 
                FROM django_migrations 
                WHERE app IN ('admin', 'auth_app', 'auth', 'contenttypes')
                ORDER BY id
            """)
            
            self.stdout.write("Current migration state:")
            for row in cursor.fetchall():
                self.stdout.write(f"  {row[0]}: {row[1]}")
            
            # Delete admin migrations to reapply them in correct order
            self.stdout.write("\nRemoving admin migrations...")
            cursor.execute("DELETE FROM django_migrations WHERE app = 'admin'")
            
            self.stdout.write(self.style.SUCCESS("\nMigration history fixed!"))
            self.stdout.write("Now run: python manage.py migrate admin --fake")
            self.stdout.write("Then run: python manage.py migrate")
