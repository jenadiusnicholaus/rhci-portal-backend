"""
Azam Pay Payment Gateway Integration
Handles payment processing for donations using Azam Pay API
"""
import requests
import json
import logging
from decimal import Decimal
from typing import Dict, Optional, Tuple
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class AzamPayService:
    """Service class for Azam Pay payment gateway integration"""
    
    def __init__(self):
        self.auth_url = settings.AZAM_PAY_AUTH
        self.checkout_url = settings.AZAM_PAY_CHECKOUT_URL
        self.app_name = settings.AZAM_PAY_APP_NAME
        self.client_id = settings.AZAM_PAY_CLIENT_ID
        self.client_secret = settings.AZAM_PAY_CLIENT_SECRET
        self._access_token = None
        self._token_expires_at = None
    
    def _get_access_token(self) -> str:
        """
        Get or refresh Azam Pay access token
        Returns cached token if still valid, otherwise requests new one
        """
        # Return cached token if still valid
        if self._access_token and self._token_expires_at:
            if timezone.now() < self._token_expires_at:
                return self._access_token
        
        # Request new token
        try:
            url = f"{self.auth_url}/AppRegistration/GenerateToken"
            headers = {
                'Content-Type': 'application/json'
            }
            payload = {
                'appName': self.app_name,
                'clientId': self.client_id,
                'clientSecret': self.client_secret
            }
            
            logger.info(f"Requesting Azam Pay access token from {url}")
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            self._access_token = data.get('data', {}).get('accessToken')
            
            if not self._access_token:
                raise Exception("No access token in response")
            
            # Cache token for 50 minutes (expires in 1 hour)
            self._token_expires_at = timezone.now() + timedelta(minutes=50)
            
            logger.info("Successfully obtained Azam Pay access token")
            return self._access_token
            
        except requests.RequestException as e:
            logger.error(f"Failed to get Azam Pay access token: {str(e)}")
            raise Exception(f"Azam Pay authentication failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error getting access token: {str(e)}")
            raise
    
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
            provider: Mobile money provider (e.g., 'Airtel', 'Tigo', 'Halopesa', 'Azampesa')
            account_number: Customer phone number
            additional_properties: Optional metadata
        
        Returns:
            Tuple of (success: bool, response_data: dict)
        """
        try:
            token = self._get_access_token()
            
            url = f"{self.checkout_url}/azampay/mno/checkout"
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'accountNumber': account_number,
                'amount': str(amount),
                'currency': currency,
                'externalId': external_id,
                'provider': provider
            }
            
            if additional_properties:
                payload['additionalProperties'] = additional_properties
            
            logger.info(f"Initiating Azam Pay checkout: {external_id} - {amount} {currency}")
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            # Log response for debugging
            logger.info(f"Azam Pay response status: {response.status_code}")
            logger.info(f"Azam Pay response: {response.text}")
            
            response.raise_for_status()
            data = response.json()
            
            # Check if request was successful
            if data.get('success', False):
                return True, data
            else:
                error_msg = data.get('message', 'Unknown error')
                logger.error(f"Azam Pay checkout failed: {error_msg}")
                return False, {'error': error_msg, 'data': data}
                
        except requests.RequestException as e:
            logger.error(f"Azam Pay checkout request failed: {str(e)}")
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
        Initiate bank checkout with Azam Pay
        
        Args:
            amount: Payment amount
            currency: Currency code
            external_id: Unique transaction reference
            provider: Bank provider
            merchant_account_number: Merchant account number
            merchant_mobile_number: Merchant mobile number
            otp: One-time password
            additional_properties: Optional metadata
        
        Returns:
            Tuple of (success: bool, response_data: dict)
        """
        try:
            token = self._get_access_token()
            
            url = f"{self.checkout_url}/azampay/bank/checkout"
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'amount': str(amount),
                'currencyCode': currency,
                'merchantAccountNumber': merchant_account_number,
                'merchantMobileNumber': merchant_mobile_number,
                'merchantName': self.app_name,
                'otp': otp,
                'provider': provider,
                'referenceId': external_id
            }
            
            if additional_properties:
                payload['additionalProperties'] = additional_properties
            
            logger.info(f"Initiating Azam Pay bank checkout: {external_id}")
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('success', False):
                return True, data
            else:
                error_msg = data.get('message', 'Unknown error')
                logger.error(f"Azam Pay bank checkout failed: {error_msg}")
                return False, {'error': error_msg, 'data': data}
                
        except requests.RequestException as e:
            logger.error(f"Azam Pay bank checkout failed: {str(e)}")
            return False, {'error': f'Payment request failed: {str(e)}'}
        except Exception as e:
            logger.error(f"Unexpected error in bank checkout: {str(e)}")
            return False, {'error': f'Unexpected error: {str(e)}'}
    
    def check_transaction_status(self, reference_id: str) -> Tuple[bool, Dict]:
        """
        Check transaction status from Azam Pay
        
        Args:
            reference_id: Transaction reference ID (externalId)
        
        Returns:
            Tuple of (success: bool, response_data: dict)
        """
        try:
            token = self._get_access_token()
            
            url = f"{self.checkout_url}/azampay/gettransactionstatus"
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'pgReferenceId': reference_id
            }
            
            logger.info(f"Checking Azam Pay transaction status: {reference_id}")
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return True, data
            
        except requests.RequestException as e:
            logger.error(f"Failed to check transaction status: {str(e)}")
            return False, {'error': f'Status check failed: {str(e)}'}
        except Exception as e:
            logger.error(f"Unexpected error checking status: {str(e)}")
            return False, {'error': f'Unexpected error: {str(e)}'}
    
    def process_callback(self, callback_data: Dict) -> Dict:
        """
        Process payment callback/webhook from Azam Pay
        
        Args:
            callback_data: Callback payload from Azam Pay
        
        Returns:
            Processed callback information
        """
        try:
            # Extract relevant information
            result = {
                'transaction_id': callback_data.get('transactionId'),
                'external_id': callback_data.get('externalId'),
                'amount': callback_data.get('amount'),
                'status': callback_data.get('status'),
                'message': callback_data.get('message'),
                'provider': callback_data.get('provider'),
                'raw_data': callback_data
            }
            
            logger.info(f"Processed Azam Pay callback: {result['external_id']} - {result['status']}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing callback: {str(e)}")
            raise


# Global service instance
azampay_service = AzamPayService()
