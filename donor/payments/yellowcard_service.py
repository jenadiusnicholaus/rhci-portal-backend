"""
Yellow Card Payment Gateway Integration
Handles payment collection for donations using Yellow Card API

Yellow Card API Documentation: https://docs.yellowcard.engineering/
"""
import requests
import json
import hmac
import hashlib
import base64
import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Optional, Tuple
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class YellowCardError(Exception):
    """Custom exception for Yellow Card errors"""
    def __init__(self, message: str, error_code: str = None, response_data: Dict = None):
        self.message = message
        self.error_code = error_code
        self.response_data = response_data or {}
        super().__init__(self.message)


class YellowCardService:
    """
    Yellow Card API service for Collection (On-Ramp) payments.
    
    This service handles receiving donations where:
    - Donor pays in local currency (TZS, KES, NGN, etc.)
    - Yellow Card converts to USDT and stores in dashboard
    - RHCI can settle/withdraw from Yellow Card dashboard
    
    Authentication:
    - X-YC-Timestamp: ISO8601 timestamp
    - Authorization: YcHmacV1 {api_key}:{signature}
    - Signature = HMAC-SHA256(secret, timestamp + path + method + body_hash)
    """
    
    def __init__(self):
        """Initialize Yellow Card service with credentials from settings."""
        # Load configuration from settings
        self.environment = getattr(settings, 'YELLOW_CARD_ENVIRONMENT', 'sandbox')
        
        # Set base URL based on environment
        # Note: URLs should NOT include /business - paths already have it
        if self.environment == 'production':
            pass  # Base URL and credentials set below based on environment
        
        # Base URL and API credentials (automatically selected based on environment in settings.py)
        self.base_url = getattr(settings, 'YELLOW_CARD_BASE_URL', 'https://sandbox.api.yellowcard.io')
        self.api_key = getattr(settings, 'YELLOW_CARD_API_KEY', '')
        self.api_secret = getattr(settings, 'YELLOW_CARD_API_SECRET', '')
        
        # Timeout configuration
        timeout_connect = getattr(settings, 'YELLOW_CARD_TIMEOUT_CONNECT', 30)
        timeout_read = getattr(settings, 'YELLOW_CARD_TIMEOUT_READ', 60)
        self.timeout = (timeout_connect, timeout_read)
        
        # Validate credentials
        if not self.api_key or not self.api_secret:
            logger.warning("Yellow Card API credentials not configured!")
        
        logger.info(f"YellowCard Service initialized - Environment: {self.environment}")
        logger.info(f"Base URL: {self.base_url}")
    
    # =========================================================================
    # AUTHENTICATION METHODS
    # =========================================================================
    
    def _get_timestamp(self) -> str:
        """
        Get current timestamp in ISO8601 format.
        
        Example: "2022-01-11T15:48:37.424Z"
        
        Returns:
            str: ISO8601 formatted timestamp
        """
        # Get current UTC time with milliseconds
        now = datetime.now(timezone.utc)
        # Format: YYYY-MM-DDTHH:MM:SS.sssZ
        timestamp = now.strftime('%Y-%m-%dT%H:%M:%S.') + f'{now.microsecond // 1000:03d}Z'
        return timestamp
    
    def _hash_body(self, body: str) -> str:
        """
        Create base64 encoded SHA256 hash of request body.
        
        Used for POST and PUT requests.
        
        Args:
            body: JSON string of request body
            
        Returns:
            str: Base64 encoded SHA256 hash
        """
        if not body:
            return ""
        
        # SHA256 hash of body
        sha256_hash = hashlib.sha256(body.encode('utf-8')).digest()
        # Base64 encode the hash
        base64_hash = base64.b64encode(sha256_hash).decode('utf-8')
        return base64_hash
    
    def _generate_signature(self, timestamp: str, path: str, method: str, body: str = "") -> str:
        """
        Generate HMAC-SHA256 signature for Yellow Card API authentication.
        
        Message format: timestamp + path + method + body_hash (for POST/PUT)
        Example: "2022-01-11T15:48:37.424Z/business/channelsGET"
        Example with body: "2022-01-11T15:48:37.424Z/business/collectionsPOSTbase64hash=="
        
        Args:
            timestamp: ISO8601 timestamp
            path: Request path (e.g., "/business/channels")
            method: HTTP method in caps (e.g., "GET", "POST")
            body: Request body JSON string (for POST/PUT requests)
            
        Returns:
            str: Base64 encoded HMAC-SHA256 signature
        """
        # Build message to sign
        message = timestamp + path + method
        
        # Add body hash for POST and PUT requests (even if body is empty)
        if method in ['POST', 'PUT']:
            body_hash = self._hash_body(body if body else "")
            message += body_hash
        
        logger.debug(f"Signature message: {message[:100]}...")
        
        # Create HMAC-SHA256 signature
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).digest()
        
        # Base64 encode the signature
        signature_b64 = base64.b64encode(signature).decode('utf-8')
        
        return signature_b64
    
    def _get_auth_headers(self, path: str, method: str, body: str = "") -> Dict[str, str]:
        """
        Generate authentication headers for Yellow Card API request.
        
        Headers:
        - X-YC-Timestamp: ISO8601 timestamp
        - Authorization: YcHmacV1 {api_key}:{signature}
        - Content-Type: application/json
        
        Args:
            path: Request path (e.g., "/business/channels")
            method: HTTP method in caps (e.g., "GET", "POST")
            body: Request body JSON string (for POST/PUT requests)
            
        Returns:
            dict: Headers dictionary
        """
        timestamp = self._get_timestamp()
        signature = self._generate_signature(timestamp, path, method, body)
        
        headers = {
            'X-YC-Timestamp': timestamp,
            'Authorization': f'YcHmacV1 {self.api_key}:{signature}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        logger.debug(f"Auth headers generated for {method} {path}")
        logger.debug(f"Timestamp: {timestamp}")
        
        return headers
    
    # =========================================================================
    # HTTP REQUEST METHODS
    # =========================================================================
    
    def _make_request(
        self, 
        method: str, 
        path: str, 
        body: Optional[Dict] = None
    ) -> Tuple[bool, Dict]:
        """
        Make authenticated request to Yellow Card API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            path: API endpoint path (e.g., "/business/channels")
            body: Request body dictionary (for POST/PUT)
            
        Returns:
            Tuple of (success: bool, response_data: dict)
        """
        method = method.upper()
        url = f"{self.base_url}{path}"
        
        # Serialize body to JSON string
        body_str = json.dumps(body) if body else ""
        
        # Generate auth headers
        headers = self._get_auth_headers(path, method, body_str)
        
        logger.info(f"📤 Yellow Card API Request: {method} {url}")
        if body:
            # Pretty print request body for readability
            try:
                pretty_body = json.dumps(body, indent=2)
                logger.debug(f"Request body:\n{pretty_body}")
            except:
                logger.debug(f"Request body: {body_str[:500]}...")
        
        try:
            # Make request based on method
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=self.timeout)
            elif method == 'POST':
                # For POST with body, send as data; for POST without body, don't send data param
                if body_str:
                    response = requests.post(url, headers=headers, data=body_str, timeout=self.timeout)
                else:
                    response = requests.post(url, headers=headers, timeout=self.timeout)
            elif method == 'PUT':
                response = requests.put(url, headers=headers, data=body_str, timeout=self.timeout)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=self.timeout)
            else:
                raise YellowCardError(f"Unsupported HTTP method: {method}")
            
            # Log response
            logger.info(f"📥 Response Status: {response.status_code}")
            # Pretty print response body for readability
            try:
                response_data = response.json()
                pretty_response = json.dumps(response_data, indent=2)
                logger.debug(f"Response Body:\n{pretty_response}")
            except:
                logger.debug(f"Response Body: {response.text[:1000]}...")
            
            # Check content type
            content_type = response.headers.get('Content-Type', '').lower()
            if 'html' in content_type:
                logger.error(f"⚠️ Received HTML response (expected JSON)")
                logger.error(f"Response: {response.text[:500]}")
                return False, {'error': 'Received HTML response instead of JSON'}
            
            # Parse JSON response
            try:
                data = response.json()
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON: {response.text[:500]}")
                return False, {'error': 'Invalid JSON response'}
            
            # Check for success
            if response.status_code in [200, 201]:
                logger.info(f"✅ Request successful")
                return True, data
            else:
                error_msg = data.get('message', data.get('error', 'Unknown error'))
                logger.error(f"❌ Request failed: {error_msg}")
                logger.error(f"Full response: {data}")
                return False, {'error': error_msg, 'data': data, 'status_code': response.status_code}
                
        except requests.exceptions.Timeout:
            logger.error(f"❌ Request timed out: {method} {url}")
            return False, {'error': 'Request timed out'}
        except requests.exceptions.ConnectionError as e:
            logger.error(f"❌ Connection error: {str(e)}")
            return False, {'error': f'Connection error: {str(e)}'}
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Request error: {str(e)}")
            return False, {'error': f'Request failed: {str(e)}'}
        except Exception as e:
            logger.error(f"❌ Unexpected error: {str(e)}")
            return False, {'error': f'Unexpected error: {str(e)}'}
    
    # =========================================================================
    # TEST AUTHENTICATION
    # =========================================================================
    
    def test_authentication(self) -> Tuple[bool, Dict]:
        """
        Test authentication by calling Get Channels endpoint.
        
        This is useful for verifying that API credentials are correct.
        
        Returns:
            Tuple of (success: bool, response_data: dict)
        """
        logger.info("🔐 Testing Yellow Card authentication...")
        
        # Try to get channels - this should work if auth is correct
        success, data = self._make_request('GET', '/business/channels')
        
        if success:
            logger.info("✅ Authentication successful!")
            logger.info(f"Retrieved {len(data.get('channels', data))} channels")
        else:
            logger.error("❌ Authentication failed!")
            logger.error(f"Error: {data.get('error', 'Unknown error')}")
        
        return success, data
    
    # =========================================================================
    # COLLECTION API - STEP 1: GET REFERENCE DATA
    # =========================================================================
    
    def get_channels(self, country: str = None, currency: str = None) -> Tuple[bool, Dict]:
        """
        Get available payment channels (Mobile Money, Bank Transfer, etc.)
        
        API: GET /business/channels
        
        Args:
            country: Filter by country code (e.g., "TZ", "KE", "NG")
            currency: Filter by currency (e.g., "TZS", "KES", "NGN")
            
        Returns:
            Tuple of (success: bool, data: dict with 'channels' list)
            
        Response contains:
            - id: Channel ID
            - channelType: "momo", "bank", etc.
            - country: Country code
            - currency: Currency code
            - min/max: Transaction limits
            - feeLocal/feeUSD: Fees
            - rampType: "deposit" for collection
        """
        logger.info(f"📡 Getting channels (country={country}, currency={currency})...")
        
        success, data = self._make_request('GET', '/business/channels')
        
        if success:
            channels = data.get('channels', data if isinstance(data, list) else [])
            
            # Filter by country if specified
            if country:
                channels = [c for c in channels if c.get('country') == country]
            
            # Filter by currency if specified
            if currency:
                channels = [c for c in channels if c.get('currency') == currency]
            
            # Filter to only deposit channels (for collection)
            deposit_channels = [c for c in channels if c.get('rampType') == 'deposit']
            
            logger.info(f"✅ Found {len(deposit_channels)} deposit channels")
            return True, {'channels': deposit_channels, 'all_channels': channels}
        
        return success, data
    
    def get_rates(self, currency: str = None) -> Tuple[bool, Dict]:
        """
        Get exchange rates (local currency to USD/USDT).
        
        API: GET /business/rates
        
        Args:
            currency: Filter by currency (e.g., "TZS", "KES")
            
        Returns:
            Tuple of (success: bool, data: dict with 'rates' list)
            
        Response contains:
            - currency: Currency code (e.g., "TZS")
            - buy: Rate for buying USDT (collection)
            - sell: Rate for selling USDT (disbursement)
        """
        logger.info(f"📡 Getting rates (currency={currency})...")
        
        success, data = self._make_request('GET', '/business/rates')
        
        if success:
            rates = data.get('rates', data if isinstance(data, list) else [])
            
            # Filter by currency if specified
            if currency:
                rates = [r for r in rates if r.get('currency') == currency]
            
            logger.info(f"✅ Found {len(rates)} rate(s)")
            return True, {'rates': rates}
        
        return success, data
    
    def get_networks(self, country: str = None) -> Tuple[bool, Dict]:
        """
        Get mobile money networks (Vodacom, Airtel, etc.)
        
        API: GET /business/networks
        
        Args:
            country: Filter by country code (e.g., "TZ", "KE")
            
        Returns:
            Tuple of (success: bool, data: dict with 'networks' list)
            
        Response contains:
            - code: Network code (e.g., "vodacom", "airtel")
            - name: Display name
            - country: Country code
        """
        logger.info(f"📡 Getting networks (country={country})...")
        
        success, data = self._make_request('GET', '/business/networks')
        
        if success:
            networks = data.get('networks', data if isinstance(data, list) else [])
            
            # Filter by country if specified
            if country:
                networks = [n for n in networks if n.get('country') == country]
            
            logger.info(f"✅ Found {len(networks)} network(s)")
            return True, {'networks': networks}
        
        return success, data
    
    def get_payment_reasons(self) -> Tuple[bool, Dict]:
        """
        Get list of valid payment reasons (required for collections).
        
        API: GET /business/reasons
        
        Returns:
            Tuple of (success: bool, data: dict with 'reasons' list)
            
        For donations, look for reason like "donation" or "charity"
        """
        logger.info("📡 Getting payment reasons...")
        
        success, data = self._make_request('GET', '/business/reasons')
        
        if success:
            reasons = data.get('reasons', data if isinstance(data, list) else [])
            logger.info(f"✅ Found {len(reasons)} reason(s)")
            return True, {'reasons': reasons}
        
        return success, data
    
    # =========================================================================
    # COLLECTION API - SUBMIT COLLECTION REQUEST
    # =========================================================================
    
    def submit_collection_request(
        self,
        channel_id: str,
        local_amount: Decimal,
        currency: str,
        country: str,
        account_number: str,
        network_id: str,
        account_type: str,
        recipient_name: str,
        recipient_phone: str,
        recipient_country: str = "US",
        recipient_email: str = None,
        recipient_address: str = None,
        reason: str = "other",
        sequence_id: str = None,
        force_accept: bool = True,
        amount_usd: Decimal = None
    ) -> Tuple[bool, Dict]:
        """
        Submit a collection request to Yellow Card.
        
        API: POST /business/collections
        
        Based on official Yellow Card example:
        - Uses `source` object for sender's mobile money details
        - Uses `recipient` object for who receives the funds (RHCI)
        - Can use `localAmount` (local currency) or `amount` (USD)
        - `forceAccept: true` auto-confirms the collection
        
        Args:
            channel_id: Channel ID from get_channels()
            local_amount: Amount in local currency (e.g., 50000 TZS)
            currency: Currency code (e.g., "TZS", "KES")
            country: Country code (e.g., "TZ", "KE")
            account_number: Sender's phone/account number (e.g., "255712345678")
            network_id: Network ID from get_networks()
            account_type: Account type from network (e.g., "phone")
            recipient_name: Name of recipient (RHCI or donor name for records)
            recipient_phone: Recipient phone number
            recipient_country: Recipient country (default "US" for RHCI)
            recipient_email: Recipient email (optional)
            recipient_address: Recipient address (optional)
            reason: Payment reason (e.g., "other", "donation")
            sequence_id: Our unique reference (donation ID)
            force_accept: Auto-accept the collection (default True)
            amount_usd: Amount in USD (alternative to local_amount)
            
        Returns:
            Tuple of (success: bool, data: dict with collection details)
        """
        logger.info(f"📡 Submitting collection request...")
        logger.info(f"   Local Amount: {local_amount} {currency}")
        logger.info(f"   Account: {account_number}")
        logger.info(f"   Channel: {channel_id}")
        logger.info(f"   Network ID: {network_id}")
        logger.info(f"   Environment: {self.environment}")
        
        # Always call Yellow Card API (both sandbox and production)
        # Build source object (sender's mobile money details)
        # Per official Yellow Card example
        source = {
            "accountNumber": account_number,
            "accountType": account_type,
            "networkId": network_id
        }
        
        # Build recipient object (RHCI receives the funds)
        # KYC metadata required by Yellow Card for all collections
        # Format per Yellow Card docs: https://docs.yellowcard.engineering
        recipient = {
            "name": recipient_name,
            "country": recipient_country,
            "phone": recipient_phone,
            "address": recipient_address or "123 Healthcare Drive, New York, NY 10001",
            "dob": getattr(settings, 'RHCI_RECIPIENT_DOB', '01/01/1990'),
            "email": recipient_email or "donations@rhci.org",
            "idNumber": getattr(settings, 'RHCI_RECIPIENT_ID_NUMBER', '0123456789'),
            "idType": getattr(settings, 'RHCI_RECIPIENT_ID_TYPE', 'license')
        }
        
        # Build request body - following official Yellow Card example exactly
        body = {
            "recipient": recipient,
            "source": source,
            "channelId": channel_id,
            "sequenceId": sequence_id or str(uuid.uuid4()),
            "currency": currency,
            "country": country,
            "reason": reason,
            "forceAccept": force_accept
        }
        
        # Use amount (USD) or localAmount (local currency)
        # Per Yellow Card docs: use one or the other
        if amount_usd:
            body["amount"] = float(amount_usd)  # Amount in USD
        else:
            body["localAmount"] = float(local_amount)  # Amount in local currency
        
        logger.debug(f"Request body: {body}")
        
        success, data = self._make_request('POST', '/business/collections', body)
        
        if success:
            collection_id = data.get('id')
            status = data.get('status')
            local_amount_resp = data.get('localAmount') or data.get('convertedAmount')
            usd_amount = data.get('usdAmount') or data.get('amount')
            rate = data.get('rate')
            
            logger.info(f"✅ Collection request submitted!")
            logger.info(f"   Collection ID: {collection_id}")
            logger.info(f"   Status: {status}")
            logger.info(f"   Amount: {local_amount_resp} → ${usd_amount} USD")
            logger.info(f"   Rate: {rate}")
        else:
            error_code = data.get('data', {}).get('code') or data.get('errorCode') or data.get('code')
            logger.error(f"❌ Failed to submit collection request: {error_code}")
        
        return success, data
    
    # =========================================================================
    # COLLECTION API - STEP 3: ACCEPT/DENY COLLECTION
    # =========================================================================
    
    def accept_collection_request(self, collection_id: str) -> Tuple[bool, Dict]:
        """
        Accept a collection request (confirms the payment).
        
        API: POST /business/collections/{id}/accept
        
        This is STEP 2 of the two-step collection process.
        After accepting, Yellow Card will:
        1. Send USSD push to donor's phone
        2. Donor enters PIN to confirm
        3. Payment is processed
        4. Webhook is sent with result
        
        Args:
            collection_id: Collection ID from submit_collection_request()
            
        Returns:
            Tuple of (success: bool, data: dict with updated collection)
        """
        logger.info(f"📡 Accepting collection request: {collection_id}...")
        
        success, data = self._make_request(
            'POST', 
            f'/business/collections/{collection_id}/accept',
            {}  # Empty body, but still POST
        )
        
        if success:
            status = data.get('status')
            logger.info(f"✅ Collection accepted!")
            logger.info(f"   Status: {status}")
        else:
            logger.error(f"❌ Failed to accept collection")
        
        return success, data
    
    def deny_collection_request(self, collection_id: str) -> Tuple[bool, Dict]:
        """
        Deny/cancel a collection request.
        
        API: POST /business/collections/{id}/deny
        
        Use this if the user cancels before confirming.
        
        Args:
            collection_id: Collection ID from submit_collection_request()
            
        Returns:
            Tuple of (success: bool, data: dict)
        """
        logger.info(f"📡 Denying collection request: {collection_id}...")
        
        success, data = self._make_request(
            'POST',
            f'/business/collections/{collection_id}/deny',
            {}
        )
        
        if success:
            logger.info(f"✅ Collection denied/cancelled")
        else:
            logger.error(f"❌ Failed to deny collection")
        
        return success, data
    
    # =========================================================================
    # SANDBOX TESTING API - Simulate Transaction Completion
    # =========================================================================
    
    def simulate_collection(self, collection_id: str, status: str = 'complete') -> Tuple[bool, Dict]:
        """
        Simulate a collection status in sandbox mode.
        
        API: POST /business/sandbox/collections/{id}/{status}
        
        Per Yellow Card docs: https://docs.yellowcard.engineering/docs/sandbox-testing-api
        This endpoint allows you to simulate transaction completion/failure in sandbox.
        
        Args:
            collection_id: Collection ID to simulate
            status: Status to simulate - 'complete' or 'fail'
            
        Returns:
            Tuple of (success: bool, data: dict with updated collection)
            
        Note: Only works in sandbox environment!
        """
        if self.environment != 'sandbox':
            logger.error("❌ simulate_collection only works in sandbox mode!")
            return False, {'error': 'Simulation only available in sandbox environment'}
        
        if status not in ['complete', 'fail']:
            logger.error(f"❌ Invalid status: {status}. Use 'complete' or 'fail'")
            return False, {'error': "Status must be 'complete' or 'fail'"}
        
        logger.info(f"🧪 Simulating collection {collection_id} as '{status}'...")
        
        # Yellow Card sandbox simulation endpoint - no body required
        success, data = self._make_request(
            'POST',
            f'/business/sandbox/collections/{collection_id}/{status}',
            None  # No body for simulation endpoint
        )
        
        if success:
            new_status = data.get('status')
            logger.info(f"✅ Collection simulated!")
            logger.info(f"   New Status: {new_status}")
        else:
            logger.error(f"❌ Failed to simulate collection")
        
        return success, data
    
    # =========================================================================
    # COLLECTION API - STEP 4: LOOKUP & STATUS
    # =========================================================================
    
    def lookup_collection(self, collection_id: str) -> Tuple[bool, Dict]:
        """
        Look up a collection by ID.
        
        API: GET /business/collections/{id}
        
        Use this to:
        - Check payment status
        - Get final amounts after completion
        - Verify webhook data
        
        Args:
            collection_id: Collection ID
            
        Returns:
            Tuple of (success: bool, data: dict with collection details)
            
        Status values:
            - pending: Awaiting payment
            - processing: Payment in progress
            - completed: Payment successful
            - failed: Payment failed
            - expired: Quote expired
        """
        logger.info(f"📡 Looking up collection: {collection_id}...")
        
        success, data = self._make_request('GET', f'/business/collections/{collection_id}')
        
        if success:
            status = data.get('status')
            logger.info(f"✅ Collection found - Status: {status}")
        else:
            logger.error(f"❌ Collection not found")
        
        return success, data
    
    def lookup_collection_by_sequence_id(self, sequence_id: str) -> Tuple[bool, Dict]:
        """
        Look up a collection by our sequence ID (donation ID).
        
        API: GET /business/collections?sequenceId={sequence_id}
        
        Args:
            sequence_id: Our donation ID
            
        Returns:
            Tuple of (success: bool, data: dict)
        """
        logger.info(f"📡 Looking up collection by sequence ID: {sequence_id}...")
        
        # Note: This might need query params - check API docs
        success, data = self._make_request(
            'GET', 
            f'/business/collections?sequenceId={sequence_id}'
        )
        
        return success, data
    
    # =========================================================================
    # WEBHOOK PROCESSING
    # =========================================================================
    
    def verify_webhook_signature(self, payload: str, signature: str, timestamp: str) -> bool:
        """
        Verify webhook signature from Yellow Card.
        
        Args:
            payload: Raw request body as string
            signature: Signature from X-YC-Signature header
            timestamp: Timestamp from X-YC-Timestamp header
            
        Returns:
            bool: True if signature is valid
        """
        webhook_secret = getattr(settings, 'YELLOW_CARD_WEBHOOK_SECRET', '')
        
        if not webhook_secret:
            logger.warning("Webhook secret not configured - skipping verification")
            return True  # Skip verification if no secret configured
        
        # Recreate the signature
        expected_signature = hmac.new(
            webhook_secret.encode('utf-8'),
            (timestamp + payload).encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        is_valid = hmac.compare_digest(signature, expected_signature)
        
        if not is_valid:
            logger.error("❌ Webhook signature verification failed!")
        
        return is_valid
    
    def process_webhook(self, payload: Dict) -> Dict:
        """
        Process webhook payload from Yellow Card.
        
        Args:
            payload: Parsed webhook JSON payload
            
        Returns:
            dict: Processed webhook data with:
                - event: Event type
                - collection_id: Collection ID
                - status: Payment status
                - local_amount: Amount in local currency
                - usd_amount: USD equivalent
                - currency: Currency code
                - success: Whether payment succeeded
        """
        logger.info("📥 Processing Yellow Card webhook...")
        
        event = payload.get('event', payload.get('type', 'unknown'))
        data = payload.get('data', payload)
        
        collection_id = data.get('id')
        status = data.get('status', '').lower()
        local_amount = data.get('localAmount')
        usd_amount = data.get('usdAmount')
        currency = data.get('currency')
        sequence_id = data.get('sequenceId')  # Our donation ID
        
        logger.info(f"   Event: {event}")
        logger.info(f"   Collection ID: {collection_id}")
        logger.info(f"   Status: {status}")
        logger.info(f"   Amount: {local_amount} {currency} → ${usd_amount} USD")
        logger.info(f"   Sequence ID: {sequence_id}")
        
        # Determine if successful
        success = status in ['completed', 'successful', 'success']
        
        result = {
            'event': event,
            'collection_id': collection_id,
            'status': status,
            'local_amount': local_amount,
            'usd_amount': usd_amount,
            'currency': currency,
            'sequence_id': sequence_id,
            'success': success,
            'raw_data': data
        }
        
        if success:
            logger.info(f"✅ Payment successful! USD Amount: ${usd_amount}")
        else:
            logger.warning(f"⚠️ Payment status: {status}")
        
        return result
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def get_collection_channels_for_country(self, country: str) -> Tuple[bool, Dict]:
        """
        Get all available collection channels for a specific country.
        
        Combines channels, rates, and networks into a single response
        for easy frontend consumption.
        
        Args:
            country: Country code (e.g., "TZ", "KE", "NG")
            
        Returns:
            dict with channels, rates, networks for the country
        """
        logger.info(f"📡 Getting all collection data for {country}...")
        
        result = {
            'country': country,
            'channels': [],
            'rates': [],
            'networks': [],
            'reasons': []
        }
        
        # Get channels
        success, data = self.get_channels(country=country)
        if success:
            result['channels'] = data.get('channels', [])
        
        # Get currency from channels
        currencies = set(c.get('currency') for c in result['channels'])
        
        # Get rates for currencies
        success, data = self.get_rates()
        if success:
            rates = data.get('rates', [])
            result['rates'] = [r for r in rates if r.get('currency') in currencies]
        
        # Get networks for mobile money
        success, data = self.get_networks(country=country)
        if success:
            result['networks'] = data.get('networks', [])
        
        # Get payment reasons
        success, data = self.get_payment_reasons()
        if success:
            result['reasons'] = data.get('reasons', [])
        
        logger.info(f"✅ Collected data for {country}:")
        logger.info(f"   Channels: {len(result['channels'])}")
        logger.info(f"   Rates: {len(result['rates'])}")
        logger.info(f"   Networks: {len(result['networks'])}")
        logger.info(f"   Reasons: {len(result['reasons'])}")
        
        return True, result


# =========================================================================
# GLOBAL SERVICE INSTANCE
# =========================================================================

# Create a singleton instance (initialized when first imported)
# This follows the same pattern as azampay_service.py
yellowcard_service = YellowCardService()
