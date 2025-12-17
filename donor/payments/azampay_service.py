"""
Azam Pay Payment Gateway Integration
Handles payment processing for donations using Azam Pay API
Based on official AzamPay API documentation
"""
import requests
import json
import logging
from decimal import Decimal
from typing import Dict, Optional, Tuple
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class AzamPayError(Exception):
    """Custom exception for AzamPay errors"""
    def __init__(self, message: str, error_code: str = None, response_data: Dict = None):
        self.message = message
        self.error_code = error_code
        self.response_data = response_data or {}
        super().__init__(self.message)


class AzamPayService:
    """Enhanced Azam Pay service with comprehensive payment processing"""
    
    def __init__(self):
        self.auth_url = settings.AZAM_PAY_AUTH
        self.checkout_url = settings.AZAM_PAY_CHECKOUT_URL
        self.app_name = settings.AZAM_PAY_APP_NAME
        self.client_id = settings.AZAM_PAY_CLIENT_ID
        self.client_secret = settings.AZAM_PAY_CLIENT_SECRET
        self.environment = settings.AZAM_PAY_ENVIRONMENT
        
        # Timeout configuration based on environment
        # Sandbox: None (no timeout) - responses are slower
        # Production: (connection_timeout, read_timeout) tuple
        timeout_connect = settings.AZAM_PAY_TIMEOUT_CONNECT
        timeout_read = settings.AZAM_PAY_TIMEOUT_READ
        
        if timeout_connect is None or timeout_read is None:
            self.timeout = None  # No timeout for sandbox
        else:
            self.timeout = (timeout_connect, timeout_read)
        
        logger.info(f"AzamPay Service initialized - Environment: {self.environment}, Timeout: {self.timeout}")
        
        # Provider mappings (exact values from AzamPay API docs)
        self.mobile_providers = {
            'mpesa': 'Mpesa',
            'airtel': 'Airtel',
            'tigo': 'Tigo',
            'halopesa': 'Halopesa',
            'azampesa': 'Azampesa'
        }
        
        self.bank_providers = {
            'crdb': 'CRDB',
            'nmb': 'NMB'
        }
    
    def _normalize_phone_number(self, phone_number: str) -> str:
        """Normalize phone number to AzamPay format (255XXXXXXXXX)"""
        # Remove all non-digits
        cleaned = ''.join(filter(str.isdigit, phone_number))
        
        # Handle different formats
        if cleaned.startswith('255'):
            return cleaned
        elif cleaned.startswith('0'):
            return '255' + cleaned[1:]
        elif len(cleaned) == 9:  # Tanzanian number without country code
            return '255' + cleaned
        else:
            return cleaned
    
    def _get_access_token(self) -> str:
        """
        Get or refresh Azam Pay access token with caching
        Returns cached token if valid, otherwise requests new one
        """
        # Try cache first (30 minute cache)
        cached_token = cache.get('azampay_token')
        if cached_token:
            logger.debug("Using cached AzamPay token")
            return cached_token
        
        # Request new token
        try:
            url = f"{self.auth_url}/AppRegistration/GenerateToken"
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            payload = {
                'appName': self.app_name,
                'clientId': self.client_id,
                'clientSecret': self.client_secret
            }
            
            logger.info(f"Requesting new AzamPay token from {url}")
            response = requests.post(
                url, 
                json=payload, 
                headers=headers, 
                timeout=self.timeout  # None for sandbox, (connect, read) for production
            )
            
            response_data = response.json()
            
            if response.status_code == 200 and response_data.get("success"):
                token_data = response_data.get("data", {})
                access_token = token_data.get("accessToken")
                
                if not access_token:
                    raise AzamPayError("No access token in response", response_data=response_data)
                
                # Cache for 30 minutes (tokens expire in 24h but we refresh more frequently)
                cache.set('azampay_token', access_token.strip(), 1800)
                
                logger.info("Successfully obtained new AzamPay token")
                return access_token.strip()
            else:
                error_msg = response_data.get("message", "Authentication failed")
                logger.error(f"AzamPay auth failed: {response_data}")
                raise AzamPayError(error_msg, response_data=response_data)
                
        except requests.exceptions.Timeout:
            logger.error("AzamPay authentication request timed out")
            cache.delete('azampay_token')  # Invalidate on timeout
            raise AzamPayError("Authentication request timed out. Please try again.")
        except requests.RequestException as e:
            logger.error(f"Failed to get AzamPay access token: {str(e)}")
            if "401" in str(e) or "403" in str(e):
                cache.delete('azampay_token')
            raise AzamPayError(f"Authentication failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error getting access token: {str(e)}")
            raise AzamPayError(f"Authentication error: {str(e)}")
    
    def initiate_checkout(
        self,
        amount: Decimal,
        currency: str,
        external_id: str,
        provider: str,
        account_number: str,
        additional_properties: Optional[Dict] = None
    ) -> Tuple[bool, Dict]:
        """
        Initiate mobile money checkout with Azam Pay
        
        Args:
            amount: Payment amount
            currency: Currency code (e.g., 'TZS')
            external_id: Unique transaction reference (donation ID)
            provider: Mobile money provider (e.g., 'Airtel', 'Tigo', 'Mpesa', 'Halopesa', 'Azampesa')
            account_number: Customer phone number
            additional_properties: Optional metadata
        
        Returns:
            Tuple of (success: bool, response_data: dict)
        """
        try:
            # Validate and normalize provider
            provider_key = provider.lower().replace(' ', '')
            if provider_key not in self.mobile_providers:
                raise AzamPayError(
                    f"Unsupported mobile provider: {provider}. "
                    f"Supported: {list(self.mobile_providers.keys())}"
                )
            
            azam_provider = self.mobile_providers[provider_key]
            
            # Normalize phone number
            normalized_phone = self._normalize_phone_number(account_number)
            
            # Validate amount
            if amount <= 0:
                raise AzamPayError("Amount must be greater than 0")
            
            token = self._get_access_token()
            
            url = f"{self.checkout_url}/azampay/mno/checkout"
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            payload = {
                'accountNumber': normalized_phone,
                'amount': str(int(amount)),  # AzamPay expects integer string
                'currency': currency,
                'externalId': external_id,
                'provider': azam_provider
            }
            
            if additional_properties:
                payload['additionalProperties'] = additional_properties
            
            logger.info(f"Initiating AzamPay checkout: {external_id} - {amount} {currency} via {azam_provider}")
            logger.info(f"Phone: {normalized_phone}")
            logger.debug(f"Request Payload: {payload}")
            
            response = requests.post(
                url, 
                json=payload, 
                headers=headers, 
                timeout=self.timeout  # None for sandbox, (connect, read) for production
            )
            
            # Log response for debugging
            logger.info(f"📥 AzamPay Response Status: {response.status_code}")
            logger.info(f"📥 AzamPay Response Body: {response.text[:1000]}")  # Log more content
            
            # Handle empty or non-JSON responses
            if not response.text.strip():
                logger.error("Empty response from AzamPay checkout")
                raise AzamPayError("Empty response from payment service")
            
            try:
                data = response.json()
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON from AzamPay: {e}")
                logger.error(f"Response content: {response.text}")
                raise AzamPayError("Invalid response from payment service")
            
            # Check if request was successful
            if response.status_code == 200 and data.get('success', False):
                logger.info(f"✅ Successfully initiated checkout: {external_id}")
                logger.info(f"✅ Transaction ID: {data.get('transactionId', 'N/A')}")
                logger.info(f"✅ Message: {data.get('message', 'No message')}")
                return True, data
            else:
                # Handle validation errors
                error_msg = data.get('message', 'Unknown error')
                errors = data.get('errors', {})
                
                if errors:
                    error_details = []
                    for field, field_errors in errors.items():
                        if field_errors:
                            error_details.append(f"{field}: {', '.join(field_errors)}")
                    if error_details:
                        error_msg += f": {'; '.join(error_details)}"
                
                logger.error(f"❌ AzamPay checkout failed: {error_msg}")
                logger.error(f"❌ Full error data: {data}")
                return False, {'error': error_msg, 'data': data}
                
        except AzamPayError:
            raise
        except requests.exceptions.Timeout:
            logger.error("AzamPay checkout request timed out")
            return False, {'error': 'Payment request timed out. Please try again.'}
        except requests.RequestException as e:
            logger.error(f"AzamPay checkout request failed: {str(e)}")
            return False, {'error': f'Payment request failed: {str(e)}'}
        except Exception as e:
            logger.error(f"Unexpected error in checkout: {str(e)}")
            return False, {'error': f'Unexpected error: {str(e)}'}
    
    def initiate_bank_checkout(
        self,
        amount: Decimal,
        currency: str,
        external_id: str,
        provider: str,
        merchant_account_number: str,
        merchant_mobile_number: str,
        otp: str,
        additional_properties: Optional[Dict] = None
    ) -> Tuple[bool, Dict]:
        """
        Initiate bank checkout with Azam Pay (CRDB, NMB)
        
        Args:
            amount: Payment amount
            currency: Currency code (TZS)
            external_id: Unique transaction reference
            provider: Bank provider name (must be in bank_providers)
            merchant_account_number: Merchant account number
            merchant_mobile_number: Merchant mobile number (normalized to 255XXXXXXXXX)
            otp: One-time password from bank
            additional_properties: Optional metadata
        
        Returns:
            Tuple of (success: bool, response_data: dict)
        """
        try:
            # Validate bank provider
            provider_lower = provider.lower()
            if provider_lower not in self.bank_providers:
                raise AzamPayError(
                    f"Invalid bank provider: {provider}. Must be one of: {', '.join(self.bank_providers.keys())}",
                    error_code='INVALID_BANK_PROVIDER'
                )
            
            # Use correct provider name from mapping
            provider_name = self.bank_providers[provider_lower]
            
            # Normalize phone number
            normalized_phone = self._normalize_phone_number(merchant_mobile_number)
            
            token = self._get_access_token()
            
            url = f"{self.checkout_url}/azampay/bank/checkout"
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            payload = {
                'amount': str(amount),
                'currencyCode': currency,
                'merchantAccountNumber': merchant_account_number,
                'merchantMobileNumber': normalized_phone,
                'merchantName': self.app_name,
                'otp': otp,
                'provider': provider_name,
                'referenceId': external_id
            }
            
            if additional_properties:
                payload['additionalProperties'] = additional_properties
            
            logger.info(f"Initiating AzamPay bank checkout: {external_id} with {provider_name}")
            logger.debug(f"Bank Request Payload: {payload}")
            
            response = requests.post(
                url, 
                json=payload, 
                headers=headers, 
                timeout=self.timeout  # None for sandbox, (connect, read) for production
            )
            
            logger.info(f"📥 Bank Response Status: {response.status_code}")
            logger.info(f"📥 Bank Response Body: {response.text[:1000]}")
            
            if not response.text.strip():
                logger.error("❌ Empty response from bank checkout")
                return False, {'error': 'Empty response from payment gateway'}
            
            try:
                data = response.json()
            except json.JSONDecodeError:
                logger.error(f"❌ Invalid JSON in bank checkout response: {response.text}")
                return False, {'error': 'Invalid response from payment gateway'}
            
            if response.status_code == 200 and data.get('success', False):
                logger.info(f"✅ Bank checkout successful: {external_id}")
                logger.info(f"✅ Transaction ID: {data.get('transactionId', 'N/A')}")
                return True, data
            else:
                error_msg = data.get('message', 'Bank checkout failed')
                
                # Format validation errors if present
                if 'errors' in data and isinstance(data['errors'], dict):
                    error_details = []
                    for field, errors in data['errors'].items():
                        if isinstance(errors, list):
                            field_errors = [str(err) for err in errors]
                        else:
                            field_errors = [str(errors)]
                        if field_errors:
                            error_details.append(f"{field}: {', '.join(field_errors)}")
                    if error_details:
                        error_msg += f": {'; '.join(error_details)}"
                
                logger.error(f"❌ AzamPay bank checkout failed: {error_msg}")
                logger.error(f"❌ Full error data: {data}")
                return False, {'error': error_msg, 'data': data}
                
        except AzamPayError:
            raise
        except requests.exceptions.Timeout:
            logger.error("❌ AzamPay bank checkout request timed out")
            return False, {'error': 'Bank payment request timed out. Please try again.'}
        except requests.RequestException as e:
            logger.error(f"❌ AzamPay bank checkout failed: {str(e)}")
            return False, {'error': f'Bank payment request failed: {str(e)}'}
        except Exception as e:
            logger.error(f"Unexpected error in bank checkout: {str(e)}")
            return False, {'error': f'Unexpected error: {str(e)}'}
    
    def check_transaction_status(self, reference_id: str) -> Tuple[bool, Dict]:
        """
        Check transaction status from Azam Pay
        
        Args:
            reference_id: Transaction reference ID (externalId or transactionId)
        
        Returns:
            Tuple of (success: bool, response_data: dict)
        """
        try:
            token = self._get_access_token()
            
            url = f"{self.checkout_url}/azampay/mno/checkout/status"
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            payload = {
                'transactionId': reference_id
            }
            
            logger.info(f"Checking AzamPay transaction status: {reference_id}")
            response = requests.post(
                url, 
                json=payload, 
                headers=headers, 
                timeout=self.timeout  # None for sandbox, (connect, read) for production
            )
            
            if not response.text.strip():
                logger.error("Empty response from status check")
                return False, {'error': 'Empty response from status service'}
            
            try:
                data = response.json()
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON in status response: {response.text}")
                return False, {'error': 'Invalid response from status service'}
            
            if response.status_code == 200:
                logger.info(f"Status check successful: {data.get('status', 'unknown')}")
                return True, data
            else:
                logger.error(f"Status check failed: {data}")
                return False, {'error': data.get('message', 'Status check failed'), 'data': data}
            
        except requests.exceptions.Timeout:
            logger.error("Status check request timed out")
            return False, {'error': 'Status check timed out'}
        except requests.RequestException as e:
            logger.error(f"Failed to check transaction status: {str(e)}")
            return False, {'error': f'Status check failed: {str(e)}'}
        except Exception as e:
            logger.error(f"Unexpected error checking status: {str(e)}")
            return False, {'error': f'Unexpected error: {str(e)}'}
    
    def process_callback(self, callback_data: Dict) -> Dict:
        """
        Process payment callback/webhook from Azam Pay
        
        Official AzamPay Callback Format (from API docs):
        {
            "amount": "115000",
            "clientId": "your_client_id",
            "externalreference": "RHCI-DN-29-20251208065834",
            "message": "Transaction successful",
            "mnoreference": "MPE123456789",
            "msisdn": "255789123456",
            "operator": "Mpesa",
            "password": "webhook_password",
            "reference": "AZM987654321",
            "transactionstatus": "success",  // or "failure"
            "transid": "TXN123",
            "user": "user_id",
            "utilityref": "utility_reference",
            "additionalProperties": {}
        }
        
        Args:
            callback_data: Callback payload from Azam Pay
        
        Returns:
            Processed callback information
        """
        try:
            # Extract information using ACTUAL AzamPay field names
            result = {
                # Transaction IDs
                'transaction_id': (callback_data.get('reference') or          # AzamPay txn ID
                                  callback_data.get('transid') or
                                  callback_data.get('transactionId')),
                
                # External reference (OUR reference ID)
                'external_id': (callback_data.get('externalreference') or      # Official field name
                               callback_data.get('externalId') or
                               callback_data.get('utilityref')),
                
                # Amount and status
                'amount': callback_data.get('amount'),
                'status': (callback_data.get('transactionstatus') or          # Official field name
                          callback_data.get('status')),
                
                # Additional details
                'message': callback_data.get('message'),
                'provider': callback_data.get('operator') or callback_data.get('provider'),
                'mno_reference': callback_data.get('mnoreference'),            # M-Pesa/Airtel reference
                'msisdn': callback_data.get('msisdn'),                          # Customer phone number
                'client_id': callback_data.get('clientId'),
                'utility_ref': callback_data.get('utilityref'),
                'password': callback_data.get('password'),                      # Webhook auth password
                'raw_data': callback_data
            }
            
            logger.info(f"Processed Azam Pay callback: {result['external_id']} - {result['status']}")
            logger.debug(f"Full callback data: {callback_data}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing callback: {str(e)}")
            logger.error(f"Callback data received: {callback_data}")
            raise


# Global service instance
azampay_service = AzamPayService()
