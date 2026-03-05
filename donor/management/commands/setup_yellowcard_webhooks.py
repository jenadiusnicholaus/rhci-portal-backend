from django.core.management.base import BaseCommand
from django.conf import settings
from django.urls import reverse
import requests
import json
import logging
import hmac
import hashlib
import base64
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Set up Yellow Card webhooks for collection events'

    def add_arguments(self, parser):
        parser.add_argument(
            '--action',
            choices=['create', 'list', 'delete', 'update'],
            default='list',
            help='Action to perform'
        )
        parser.add_argument(
            '--webhook-id',
            help='Webhook ID for delete/update actions'
        )
        parser.add_argument(
            '--url',
            help='Webhook URL (for create/update)'
        )
        parser.add_argument(
            '--state',
            help='Webhook state/event (e.g., COLLECTION.COMPLETE)'
        )
        parser.add_argument(
            '--active',
            type=bool,
            default=True,
            help='Whether webhook should be active'
        )

    def handle(self, *args, **options):
        action = options['action']
        
        if action == 'create':
            self.create_webhook(options)
        elif action == 'list':
            self.list_webhooks()
        elif action == 'delete':
            self.delete_webhook(options['webhook_id'])
        elif action == 'update':
            self.update_webhook(options)

    def get_auth_headers(self, path, method, body=None):
        """Generate Yellow Card API authentication headers"""
        api_key = getattr(settings, 'YELLOW_CARD_API_KEY', None)
        secret_key = getattr(settings, 'YELLOW_CARD_API_SECRET', None)
        
        if not api_key or not secret_key:
            self.stdout.write(self.style.ERROR('YELLOW_CARD_API_KEY and YELLOW_CARD_API_SECRET must be configured'))
            return None

        # Create timestamp
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Create HMAC signature
        hmac_obj = hmac.new(
            secret_key.encode('utf-8'),
            b'',  # Start with empty string
            hashlib.sha256
        )
        
        # Update with timestamp, path, method
        hmac_obj.update(timestamp.encode('utf-8'))
        hmac_obj.update(path.encode('utf-8'))
        hmac_obj.update(method.upper().encode('utf-8'))
        
        # Add body hash if present
        if body:
            body_hash = hashlib.sha256(json.dumps(body).encode('utf-8')).digest()
            body_hash_b64 = base64.b64encode(body_hash).decode('utf-8')
            hmac_obj.update(body_hash_b64.encode('utf-8'))
        
        signature = base64.b64encode(hmac_obj.digest()).decode('utf-8')
        
        return {
            'X-YC-Timestamp': timestamp,
            'Authorization': f'YcHmacV1 {api_key}:{signature}',
            'Content-Type': 'application/json'
        }

    def create_webhook(self, options):
        """Create a new webhook"""
        url = options.get('url') or self.get_default_webhook_url()
        state = options.get('state')
        active = options['active']
        
        # Build request body
        body = {
            'url': url,
            'active': active
        }
        
        if state:
            body['state'] = state
        
        # Make API request
        path = '/business/webhooks'
        headers = self.get_auth_headers(path, 'POST', body)
        
        if not headers:
            return
        
        try:
            api_base = self.get_api_base()
            response = requests.post(f'{api_base}{path}', json=body, headers=headers)
            
            if response.status_code in [200, 201]:
                webhook = response.json()
                self.stdout.write(self.style.SUCCESS(f'✅ Webhook created: {webhook["id"]}'))
                self.stdout.write(f'   URL: {webhook["url"]}')
                self.stdout.write(f'   State: {webhook.get("state", "ALL EVENTS")}')
                self.stdout.write(f'   Active: {webhook["active"]}')
                self.stdout.write(f'   Created: {webhook.get("createdAt", "N/A")}')
            else:
                self.stdout.write(self.style.ERROR(f'❌ Failed to create webhook: {response.status_code}'))
                self.stdout.write(f'   Response: {response.text}')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))

    def list_webhooks(self):
        """List all existing webhooks"""
        path = '/business/webhooks'
        headers = self.get_auth_headers(path, 'GET')
        
        if not headers:
            return
        
        try:
            api_base = self.get_api_base()
            response = requests.get(f'{api_base}{path}', headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                self.stdout.write(f'Raw response: {data}')  # Debug output
                
                # Handle different response formats
                webhooks = data
                if isinstance(data, dict):
                    if 'data' in data:
                        webhooks = data['data']
                    elif 'webhooks' in data:
                        webhooks = data['webhooks']
                
                if not webhooks:
                    self.stdout.write('No webhooks found')
                    return
                
                if not isinstance(webhooks, list):
                    self.stdout.write(f'Unexpected response format: {type(webhooks)}')
                    return
                
                self.stdout.write(f'Found {len(webhooks)} webhook(s):')
                for webhook in webhooks:
                    if not isinstance(webhook, dict):
                        self.stdout.write(f'  Invalid webhook format: {webhook}')
                        continue
                        
                    status = '🟢' if webhook.get('active') else '🔴'
                    self.stdout.write(f'\n{status} {webhook.get("id", "N/A")}')
                    self.stdout.write(f'   URL: {webhook.get("url", "N/A")}')
                    self.stdout.write(f'   State: {webhook.get("state", "ALL EVENTS")}')
                    self.stdout.write(f'   Created: {webhook.get("createdAt", "N/A")}')
            else:
                self.stdout.write(self.style.ERROR(f'❌ Failed to list webhooks: {response.status_code}'))
                self.stdout.write(f'   Response: {response.text}')
                
                # Check for IP whitelist error
                if response.status_code == 401:
                    try:
                        error_data = response.json()
                        if error_data.get('code') == 'IPMismatchError':
                            self.stdout.write(self.style.WARNING('\n📋 IP WHITELIST REQUIRED'))
                            self.stdout.write('   Production API requires IP whitelisting.')
                            self.stdout.write('   Please contact Yellow Card support to whitelist your server IP.')
                            self.stdout.write('   Or create the webhook via the Yellow Card dashboard.')
                    except:
                        pass
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))
            import traceback
            traceback.print_exc()

    def delete_webhook(self, webhook_id):
        """Delete a webhook"""
        path = f'/business/webhooks/{webhook_id}'
        headers = self.get_auth_headers(path, 'DELETE')
        
        if not headers:
            return
        
        try:
            api_base = self.get_api_base()
            response = requests.delete(f'{api_base}{path}', headers=headers)
            
            if response.status_code in [200, 204]:
                self.stdout.write(self.style.SUCCESS(f'✅ Webhook {webhook_id} deleted'))
            else:
                self.stdout.write(self.style.ERROR(f'❌ Failed to delete webhook: {response.status_code}'))
                self.stdout.write(f'   Response: {response.text}')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))

    def update_webhook(self, options):
        """Update a webhook"""
        webhook_id = options['webhook_id']
        if not webhook_id:
            self.stdout.write(self.style.ERROR('Webhook ID required for update'))
            return
        
        # Build request body
        body = {'id': webhook_id}
        
        if options.get('active') is not None:
            body['active'] = options['active']
        
        if options.get('url'):
            body['url'] = options['url']
        
        if options.get('state'):
            body['state'] = options['state']
        
        # Make API request
        path = '/business/webhooks'
        headers = self.get_auth_headers(path, 'PUT', body)
        
        if not headers:
            return
        
        try:
            api_base = self.get_api_base()
            response = requests.put(f'{api_base}{path}', json=body, headers=headers)
            
            if response.status_code == 200:
                webhook = response.json()
                self.stdout.write(self.style.SUCCESS(f'✅ Webhook updated: {webhook["id"]}'))
                self.stdout.write(f'   URL: {webhook["url"]}')
                self.stdout.write(f'   State: {webhook.get("state", "ALL EVENTS")}')
                self.stdout.write(f'   Active: {webhook["active"]}')
            else:
                self.stdout.write(self.style.ERROR(f'❌ Failed to update webhook: {response.status_code}'))
                self.stdout.write(f'   Response: {response.text}')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))

    def get_default_webhook_url(self):
        """Get the default webhook URL for this instance"""
        from django.contrib.sites.models import Site
        try:
            site = Site.objects.get_current()
            return f"https://{site.domain}/webhooks/yellowcard/collection/"
        except:
            return "https://api.rhci.co.tz/webhooks/yellowcard/collection/"

    def get_api_base(self):
        """Get Yellow Card API base URL"""
        return getattr(settings, 'YELLOW_CARD_BASE_URL', 'https://api.yellowcard.io')
