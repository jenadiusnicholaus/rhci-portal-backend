from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Mark all existing migrations as applied without running them'

    def handle(self, *args, **options):
        apps_to_fake = [
            ('contenttypes', '0001_initial'),
            ('contenttypes', '0002_remove_content_type_name'),
            ('auth', '0001_initial'),
            ('auth', '0002_alter_permission_name_max_length'),
            ('auth', '0003_alter_user_email_max_length'),
            ('auth', '0004_alter_user_username_opts'),
            ('auth', '0005_alter_user_last_login_null'),
            ('auth', '0006_require_contenttypes_0002'),
            ('auth', '0007_alter_validators_add_error_messages'),
            ('auth', '0008_alter_user_username_max_length'),
            ('auth', '0009_alter_user_last_name_max_length'),
            ('auth', '0010_alter_group_name_max_length'),
            ('auth', '0011_update_proxy_permissions'),
            ('auth', '0012_alter_user_first_name_max_length'),
            ('admin', '0001_initial'),
            ('admin', '0002_logentry_remove_auto_add'),
            ('admin', '0003_logentry_add_action_flag_choices'),
            ('sessions', '0001_initial'),
        ]
        
        with connection.cursor() as cursor:
            for app, migration in apps_to_fake:
                # Check if migration exists
                cursor.execute(
                    "SELECT id FROM django_migrations WHERE app = %s AND name = %s",
                    [app, migration]
                )
                
                if not cursor.fetchone():
                    # Insert the migration record
                    cursor.execute(
                        "INSERT INTO django_migrations (app, name, applied) VALUES (%s, %s, NOW())",
                        [app, migration]
                    )
                    self.stdout.write(f"Faked: {app}.{migration}")
                else:
                    self.stdout.write(f"Already applied: {app}.{migration}")
        
        self.stdout.write(self.style.SUCCESS("\nAll built-in migrations marked as applied!"))
        self.stdout.write("Now you can run: python manage.py migrate")
