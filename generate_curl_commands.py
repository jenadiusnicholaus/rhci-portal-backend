#!/usr/bin/env python3
"""
Generate curl commands for Yellow Card API testing
Run: python generate_curl_commands.py
"""
import hmac
import hashlib
import base64
from datetime import datetime, timezone

# Configuration
API_KEY = "0392fa1c63d962a064b483013db4a52b"
API_SECRET = "41da10bae44592dd28da5577acf7507557a6834e656f372d6c2a9945234bc72b"
BASE_URL = "https://sandbox.api.yellowcard.io"


def get_timestamp():
    """Get ISO8601 timestamp."""
    now = datetime.now(timezone.utc)
    return now.strftime('%Y-%m-%dT%H:%M:%S.') + f'{now.microsecond // 1000:03d}Z'


def hash_body(body: str) -> str:
    """Base64 SHA256 hash of body."""
    if not body:
        return ""
    sha256_hash = hashlib.sha256(body.encode('utf-8')).digest()
    return base64.b64encode(sha256_hash).decode('utf-8')


def generate_signature(timestamp: str, path: str, method: str, body: str = "") -> str:
    """Generate HMAC-SHA256 signature."""
    message = timestamp + path + method
    if method in ['POST', 'PUT'] and body:
        message += hash_body(body)
    
    signature = hmac.new(
        API_SECRET.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).digest()
    
    return base64.b64encode(signature).decode('utf-8')


def generate_curl(method: str, path: str, body: str = None, description: str = ""):
    """Generate a curl command."""
    timestamp = get_timestamp()
    body_str = body if body else ""
    signature = generate_signature(timestamp, path, method, body_str)
    
    print(f"\n{'='*70}")
    print(f"# {description}")
    print(f"# {method} {path}")
    print(f"{'='*70}")
    
    curl_cmd = f'''curl -X {method} "{BASE_URL}{path}" \\
  -H "Content-Type: application/json" \\
  -H "Accept: application/json" \\
  -H "X-YC-Timestamp: {timestamp}" \\
  -H "Authorization: YcHmacV1 {API_KEY}:{signature}"'''
    
    if body:
        # Escape for shell
        body_escaped = body.replace("'", "'\\''")
        curl_cmd += f" \\\n  -d '{body_escaped}'"
    
    print(curl_cmd)
    print()


# =============================================================================
# GENERATE CURL COMMANDS
# =============================================================================

print("\n" + "="*70)
print("YELLOW CARD API - CURL COMMANDS")
print("="*70)
print("""
NOTE: These commands have pre-generated signatures that are valid
for a short time. Run this script again to get fresh signatures.

Base URL: https://sandbox.api.yellowcard.io
""")

# 1. Get Channels
generate_curl("GET", "/business/channels", description="1. GET CHANNELS - Get available payment methods")

# 2. Get Rates  
generate_curl("GET", "/business/rates", description="2. GET RATES - Get exchange rates")

# 3. Get Networks
generate_curl("GET", "/business/networks", description="3. GET NETWORKS - Get mobile money networks")

# 4. Get Reasons (may not work)
generate_curl("GET", "/business/reasons", description="4. GET REASONS - Get payment reasons (may return 401)")

# 5. Submit Collection Request
collection_body = '''{
  "channelId": "656d4e72-7849-4fd6-bXXX-XXXXXXXXXXXX",
  "amount": "50000",
  "currency": "TZS",
  "country": "TZ",
  "reason": "donation",
  "network": "VODACOM",
  "sequenceId": "test-donation-001",
  "sender": {
    "name": "John Doe",
    "phone": "+255712345678",
    "country": "TZ"
  }
}'''

print("\n" + "="*70)
print("# 5. SUBMIT COLLECTION REQUEST (POST)")
print("# NOTE: Replace channelId with a valid one from GET /business/channels")
print("="*70)
generate_curl("POST", "/business/collections", collection_body, 
              "5. SUBMIT COLLECTION - Create a collection request")

# 6. Accept Collection
print("\n" + "="*70)
print("# 6. ACCEPT COLLECTION (Replace {collection_id} with actual ID)")
print("="*70)
generate_curl("POST", "/business/collections/{collection_id}/accept", "{}",
              "6. ACCEPT COLLECTION - Confirm the collection")

# 7. Lookup Collection
print("\n" + "="*70)
print("# 7. LOOKUP COLLECTION (Replace {collection_id} with actual ID)")
print("="*70)
generate_curl("GET", "/business/collections/{collection_id}",
              description="7. LOOKUP COLLECTION - Get collection status")


print("\n" + "="*70)
print("QUICK COPY-PASTE COMMANDS (Tanzania)")
print("="*70)

# Generate fresh commands for Tanzania-specific testing
timestamp = get_timestamp()
sig_channels = generate_signature(timestamp, "/business/channels", "GET")

print(f'''
# Test Authentication (GET Channels)
curl -X GET "{BASE_URL}/business/channels" \\
  -H "X-YC-Timestamp: {timestamp}" \\
  -H "Authorization: YcHmacV1 {API_KEY}:{sig_channels}"
''')

timestamp = get_timestamp()
sig_rates = generate_signature(timestamp, "/business/rates", "GET")

print(f'''
# Get Exchange Rates
curl -X GET "{BASE_URL}/business/rates" \\
  -H "X-YC-Timestamp: {timestamp}" \\
  -H "Authorization: YcHmacV1 {API_KEY}:{sig_rates}"
''')

timestamp = get_timestamp()
sig_networks = generate_signature(timestamp, "/business/networks", "GET")

print(f'''
# Get Networks
curl -X GET "{BASE_URL}/business/networks" \\
  -H "X-YC-Timestamp: {timestamp}" \\
  -H "Authorization: YcHmacV1 {API_KEY}:{sig_networks}"
''')

print("\n" + "="*70)
print("✅ Commands generated! Copy and paste into terminal.")
print("="*70 + "\n")
