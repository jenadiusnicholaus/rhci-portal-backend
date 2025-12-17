"""
Django management command to check CORS configuration
"""
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Check CORS configuration and display current settings'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('CORS CONFIGURATION CHECK'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        
        # Debug mode
        self.stdout.write(f"\n🔧 DEBUG Mode: {settings.DEBUG}")
        if settings.DEBUG:
            self.stdout.write(self.style.WARNING("  ⚠️  Development mode - CORS allows all origins"))
        else:
            self.stdout.write(self.style.SUCCESS("  ✅ Production mode - CORS restricted"))
        
        # Allow all origins
        self.stdout.write(f"\n🌐 CORS_ALLOW_ALL_ORIGINS: {settings.CORS_ALLOW_ALL_ORIGINS}")
        if settings.CORS_ALLOW_ALL_ORIGINS and not settings.DEBUG:
            self.stdout.write(self.style.ERROR("  ⚠️  WARNING: Allowing all origins in production is insecure!"))
        
        # Allowed origins
        self.stdout.write(f"\n📋 CORS_ALLOWED_ORIGINS:")
        if hasattr(settings, 'CORS_ALLOWED_ORIGINS') and settings.CORS_ALLOWED_ORIGINS:
            for origin in settings.CORS_ALLOWED_ORIGINS:
                self.stdout.write(f"  ✓ {origin}")
        else:
            self.stdout.write(self.style.WARNING("  ⚠️  No specific origins configured"))
        
        # Allowed hosts
        self.stdout.write(f"\n🏠 ALLOWED_HOSTS:")
        for host in settings.ALLOWED_HOSTS:
            self.stdout.write(f"  ✓ {host}")
        
        # CORS settings
        self.stdout.write(f"\n🔐 CORS Settings:")
        self.stdout.write(f"  Allow Credentials: {settings.CORS_ALLOW_CREDENTIALS}")
        self.stdout.write(f"  Preflight Max Age: {settings.CORS_PREFLIGHT_MAX_AGE}s")
        
        self.stdout.write(f"\n📝 Allowed Methods:")
        for method in settings.CORS_ALLOW_METHODS:
            self.stdout.write(f"  ✓ {method}")
        
        # Recommendations
        self.stdout.write(f"\n\n💡 Recommendations:")
        
        if settings.DEBUG:
            self.stdout.write(self.style.WARNING(
                "  • Set DEBUG=False in production .env file"
            ))
        
        if not settings.CORS_ALLOWED_ORIGINS and not settings.CORS_ALLOW_ALL_ORIGINS:
            self.stdout.write(self.style.ERROR(
                "  • Configure CORS_ALLOWED_ORIGINS in .env file"
            ))
        
        http_origins = [o for o in settings.CORS_ALLOWED_ORIGINS if o.startswith('http://') and not o.startswith('http://localhost') and not o.startswith('http://127.0.0.1')]
        if http_origins and not settings.DEBUG:
            self.stdout.write(self.style.WARNING(
                f"  • Use HTTPS in production, found HTTP origins: {', '.join(http_origins)}"
            ))
        
        if settings.CORS_ALLOW_ALL_ORIGINS and not settings.DEBUG:
            self.stdout.write(self.style.ERROR(
                "  • CRITICAL: Disable CORS_ALLOW_ALL_ORIGINS in production!"
            ))
        
        # Test command
        self.stdout.write(f"\n\n🧪 Test CORS with curl:")
        if settings.CORS_ALLOWED_ORIGINS:
            test_origin = settings.CORS_ALLOWED_ORIGINS[0]
            self.stdout.write(f'''
  curl -X OPTIONS http://your-server:8082/api/v1.0/donors/donate/azampay/patient/anonymous/ \\
    -H "Origin: {test_origin}" \\
    -H "Access-Control-Request-Method: POST" \\
    -v
            ''')
        
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 70))
        self.stdout.write(self.style.SUCCESS('Configuration check complete!'))
        self.stdout.write(self.style.SUCCESS('=' * 70 + '\n'))
