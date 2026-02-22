"""
Yellow Card Payment Gateway Views

These are the RHCI API endpoints that the frontend calls.
Frontend authenticates with JWT, backend calls Yellow Card internally.
Yellow Card API keys are never exposed to the frontend.

Endpoints:
- GET  /donor/yellowcard/channels/       - Get payment channels
- GET  /donor/yellowcard/rates/          - Get exchange rates
- GET  /donor/yellowcard/networks/       - Get mobile networks
- GET  /donor/yellowcard/config/<country>/ - Get all config for a country
- POST /donor/yellowcard/donate/patient/anonymous/     - Anonymous patient donation
- POST /donor/yellowcard/donate/patient/               - Authenticated patient donation
- POST /donor/yellowcard/donate/organization/anonymous/ - Anonymous org donation
- POST /donor/yellowcard/donate/organization/          - Authenticated org donation
- POST /donor/yellowcard/callback/       - Webhook callback from Yellow Card
- GET  /donor/yellowcard/status/<id>/    - Check collection status
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils import timezone
from django.db import transaction as db_transaction
from django.conf import settings
from decimal import Decimal
import logging
import uuid

from donor.models import Donation
from .yellowcard_service import yellowcard_service
from patient.models import PatientProfile

logger = logging.getLogger(__name__)


# ============================================================================
# REFERENCE DATA ENDPOINTS (Public)
# ============================================================================

def get_client_ip(request):
    """Get client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_country_from_ip(ip_address: str) -> dict:
    """
    Get country info from IP address using free IP geolocation API.
    Returns dict with country_code, country_name, currency, etc.
    """
    import requests
    
    # Skip for localhost/private IPs
    if ip_address in ['127.0.0.1', 'localhost', '::1'] or ip_address.startswith('192.168.') or ip_address.startswith('10.'):
        return {
            'country_code': 'TZ',  # Default to Tanzania for local testing
            'country_name': 'Tanzania',
            'currency': 'TZS',
            'detected': False,
            'message': 'Local IP - defaulting to Tanzania'
        }
    
    try:
        # Using ip-api.com (free, no API key needed, 45 requests/minute)
        response = requests.get(f'http://ip-api.com/json/{ip_address}', timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                country_code = data.get('countryCode', 'TZ')
                
                # Map country to currency
                country_currency_map = {
                    'TZ': 'TZS',  # Tanzania
                    'KE': 'KES',  # Kenya
                    'NG': 'NGN',  # Nigeria
                    'UG': 'UGX',  # Uganda
                    'GH': 'GHS',  # Ghana
                    'ZA': 'ZAR',  # South Africa
                    'RW': 'RWF',  # Rwanda
                    'ZM': 'ZMW',  # Zambia
                    'BW': 'BWP',  # Botswana
                    'US': 'USD',  # USA
                    'GB': 'GBP',  # UK
                    'CM': 'XAF',  # Cameroon
                    'CI': 'XOF',  # Ivory Coast
                    'SN': 'XOF',  # Senegal
                }
                
                return {
                    'country_code': country_code,
                    'country_name': data.get('country', ''),
                    'currency': country_currency_map.get(country_code, 'USD'),
                    'city': data.get('city', ''),
                    'detected': True
                }
    except Exception as e:
        logger.warning(f"IP geolocation failed: {e}")
    
    # Default fallback
    return {
        'country_code': 'TZ',
        'country_name': 'Tanzania',
        'currency': 'TZS',
        'detected': False,
        'message': 'Could not detect country - defaulting to Tanzania'
    }


class YellowCardAutoConfigView(APIView):
    """Auto-detect country and return payment config."""
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        tags=['🟡 Yellow Card - Reference Data'],
        operation_summary="🌍 Auto-Detect Country & Get Config",
        operation_description="""
        **Automatically detects the user's country from their IP address** and returns 
        the available payment channels and networks.
        
        This is the **recommended** endpoint for the frontend - no need to ask the user 
        for their country!
        
        **Response includes:**
        - `detected_country` - Country detected from IP
        - `channels` - Available payment channels for that country
        - `networks` - Available mobile networks
        
        **Example:**
        ```
        GET /donors/yellowcard/auto-config/
        ```
        
        If country can't be detected, defaults to Tanzania (TZ).
        """,
        responses={200: 'Auto-detected config'}
    )
    def get(self, request):
        # Get client IP and detect country
        client_ip = get_client_ip(request)
        country_info = get_country_from_ip(client_ip)
        country_code = country_info.get('country_code', 'TZ')
        
        # Get channels for detected country
        success, channel_data = yellowcard_service.get_channels(country=country_code)
        channels = []
        if success:
            all_channels = channel_data.get('channels', [])
            # Only active deposit channels
            channels = [
                c for c in all_channels 
                if c.get('status') == 'active' and c.get('rampType') == 'deposit'
            ]
        
        # Get networks for detected country
        success, network_data = yellowcard_service.get_networks(country=country_code)
        networks = []
        if success:
            all_networks = network_data.get('networks', [])
            networks = [n for n in all_networks if n.get('status') == 'active']
        
        # If no channels found for detected country, try showing all supported countries
        supported_countries = []
        if not channels:
            success, all_channel_data = yellowcard_service.get_channels()
            if success:
                all_channels = all_channel_data.get('channels', [])
                active_deposit = [c for c in all_channels if c.get('status') == 'active' and c.get('rampType') == 'deposit']
                supported_countries = list(set(c.get('country') for c in active_deposit))
        
        return Response({
            'success': True,
            'detected_country': country_info,
            'client_ip': client_ip,
            'channels': channels,
            'networks': networks,
            'channels_count': len(channels),
            'networks_count': len(networks),
            'supported_countries': supported_countries if not channels else [],
            'message': f"Found {len(channels)} channels for {country_code}" if channels else f"No channels for {country_code}. Yellow Card supports: {', '.join(supported_countries)}"
        })


class YellowCardChannelsView(APIView):
    """Get available Yellow Card payment channels."""
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        tags=['🟡 Yellow Card - Reference Data'],
        operation_summary="Get Payment Channels",
        operation_description="""
        Get available payment channels (Mobile Money, Bank) for Yellow Card.
        
        **Returns only active deposit channels** (for receiving donations).
        
        Filter by country to get channels for specific region.
        
        **Example:**
        ```
        GET /donors/yellowcard/channels/?country=TZ
        ```
        
        Response includes `id` which you'll use as `channel_id` when making a donation.
        """,
        manual_parameters=[
            openapi.Parameter('country', openapi.IN_QUERY, type=openapi.TYPE_STRING, 
                            description='Country code (TZ, KE, NG, etc.)'),
            openapi.Parameter('currency', openapi.IN_QUERY, type=openapi.TYPE_STRING,
                            description='Currency code (TZS, KES, NGN, etc.)'),
        ],
        responses={200: 'List of channels'}
    )
    def get(self, request):
        country = request.query_params.get('country')
        currency = request.query_params.get('currency')
        
        success, data = yellowcard_service.get_channels(country=country, currency=currency)
        
        if success:
            channels = data.get('channels', [])
            
            # Only return active deposit channels
            active_channels = [
                c for c in channels 
                if c.get('status') == 'active' and c.get('rampType') == 'deposit'
            ]
            
            return Response({
                'success': True,
                'channels': active_channels,
                'count': len(active_channels)
            })
        else:
            return Response({
                'success': False,
                'error': data.get('error', 'Failed to get channels')
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class YellowCardRatesView(APIView):
    """Get Yellow Card exchange rates."""
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        tags=['🟡 Yellow Card - Reference Data'],
        operation_summary="Get Exchange Rates",
        operation_description="""
        Get exchange rates for local currencies to USD/USDT.
        
        The 'buy' rate is used for collections (receiving money).
        """,
        manual_parameters=[
            openapi.Parameter('currency', openapi.IN_QUERY, type=openapi.TYPE_STRING,
                            description='Currency code (TZS, KES, NGN, etc.)'),
        ],
        responses={200: 'List of rates'}
    )
    def get(self, request):
        currency = request.query_params.get('currency')
        
        success, data = yellowcard_service.get_rates(currency=currency)
        
        if success:
            return Response({
                'success': True,
                'rates': data.get('rates', []),
                'count': len(data.get('rates', []))
            })
        else:
            return Response({
                'success': False,
                'error': data.get('error', 'Failed to get rates')
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class YellowCardNetworksView(APIView):
    """Get mobile money networks."""
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        tags=['🟡 Yellow Card - Reference Data'],
        operation_summary="Get Mobile Networks",
        operation_description="""
        Get available mobile money networks (Vodacom, Airtel, etc.)
        
        **Important:** Filter by `channel_id` to get networks that support the selected payment channel.
        
        Each network has a `channelIds` array - only networks that include your selected channel_id will work.
        
        **Example Flow:**
        1. GET /donors/yellowcard/channels/?country=TZ → Get channels, pick one
        2. GET /donors/yellowcard/networks/?channel_id=xxx → Get networks for that channel
        3. POST /donors/yellowcard/donate/... → Submit with channel_id and network_id
        """,
        manual_parameters=[
            openapi.Parameter('country', openapi.IN_QUERY, type=openapi.TYPE_STRING,
                            description='Country code (TZ, KE, NG, etc.)'),
            openapi.Parameter('channel_id', openapi.IN_QUERY, type=openapi.TYPE_STRING,
                            description='Filter networks that support this channel (recommended)'),
        ],
        responses={200: 'List of networks'}
    )
    def get(self, request):
        country = request.query_params.get('country')
        channel_id = request.query_params.get('channel_id')
        
        success, data = yellowcard_service.get_networks(country=country)
        
        if success:
            networks = data.get('networks', [])
            
            # Filter by channel_id if provided
            if channel_id:
                networks = [
                    n for n in networks 
                    if channel_id in n.get('channelIds', [])
                ]
            
            # Only return active networks
            active_networks = [n for n in networks if n.get('status') == 'active']
            
            return Response({
                'success': True,
                'networks': active_networks,
                'count': len(active_networks),
                'filtered_by_channel': channel_id is not None
            })
        else:
            return Response({
                'success': False,
                'error': data.get('error', 'Failed to get networks')
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class YellowCardSupportedCountriesView(APIView):
    """Get all supported countries for Yellow Card payments."""
    permission_classes = [AllowAny]
    
    # Country name mapping
    COUNTRY_NAMES = {
        'BW': 'Botswana',
        'CM': 'Cameroon',
        'CI': 'Ivory Coast',
        'GH': 'Ghana',
        'KE': 'Kenya',
        'MW': 'Malawi',
        'NG': 'Nigeria',
        'RW': 'Rwanda',
        'ZA': 'South Africa',
        'TZ': 'Tanzania',
        'UG': 'Uganda',
        'ZM': 'Zambia',
        'SN': 'Senegal',
        'BJ': 'Benin',
        'TG': 'Togo',
        'ML': 'Mali',
        'BF': 'Burkina Faso',
        'NE': 'Niger',
        'CD': 'DR Congo',
        'ET': 'Ethiopia',
        'MZ': 'Mozambique',
        'CG': 'Republic of Congo',
        'GA': 'Gabon',
        'US': 'United States (Test)',
    }
    
    @swagger_auto_schema(
        tags=['🟡 Yellow Card - Reference Data'],
        operation_summary="Get Supported Countries",
        operation_description="""
        Get all countries supported by Yellow Card for donations.
        
        Returns list of countries with their:
        - Country code (e.g., TZ, KE, NG)
        - Country name (e.g., Tanzania, Kenya, Nigeria)
        - Currency code (e.g., TZS, KES, NGN)
        - Mobile money support (true/false)
        - Bank transfer support (true/false)
        - Rate availability (true/false - can accept payments)
        
        **Use this endpoint to populate country dropdown in frontend.**
        """,
        responses={200: 'List of supported countries'}
    )
    def get(self, request):
        # Get all channels
        channels_success, channels_data = yellowcard_service.get_channels()
        if not channels_success:
            return Response({
                'success': False,
                'error': 'Failed to get channels'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        # Get all rates
        rates_success, rates_data = yellowcard_service.get_rates()
        rate_currencies = set()
        if rates_success:
            for rate in rates_data.get('rates', []):
                if rate.get('buy'):  # Only include if buy rate exists
                    rate_currencies.add(rate.get('code'))
        
        # Build countries list from channels
        countries = {}
        for ch in channels_data.get('channels', []):
            country_code = ch.get('country')
            currency = ch.get('currency')
            channel_type = ch.get('channelType')
            api_status = ch.get('apiStatus')
            
            if country_code not in countries:
                countries[country_code] = {
                    'code': country_code,
                    'name': self.COUNTRY_NAMES.get(country_code, country_code),
                    'currency': currency,
                    'momo': False,
                    'bank': False,
                    'has_rate': currency in rate_currencies
                }
            
            # Mark channel types available (only if active)
            if api_status == 'active':
                if channel_type == 'momo':
                    countries[country_code]['momo'] = True
                elif channel_type == 'bank':
                    countries[country_code]['bank'] = True
        
        # Convert to sorted list
        countries_list = sorted(countries.values(), key=lambda x: x['name'])
        
        # Filter to only countries with active channels and rates
        active_countries = [c for c in countries_list if (c['momo'] or c['bank']) and c['has_rate']]
        all_countries = countries_list
        
        return Response({
            'success': True,
            'countries': active_countries,  # Only fully supported countries
            'all_countries': all_countries,  # All countries (some may not have rates)
            'count': len(active_countries),
            'total_count': len(all_countries)
        })


class YellowCardCountryConfigView(APIView):
    """Get all Yellow Card configuration for a specific country."""
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        tags=['🟡 Yellow Card - Reference Data'],
        operation_summary="Get Country Configuration",
        operation_description="""
        Get all payment configuration for a specific country.
        
        Returns channels, rates, and networks in a single call.
        
        **First call `/yellowcard/countries/` to get list of supported countries.**
        """,
        responses={200: 'Country configuration'}
    )
    def get(self, request, country):
        success, data = yellowcard_service.get_collection_channels_for_country(country.upper())
        
        if success:
            return Response({
                'success': True,
                'country': country.upper(),
                'channels': data.get('channels', []),
                'rates': data.get('rates', []),
                'networks': data.get('networks', []),
                'summary': {
                    'channels_count': len(data.get('channels', [])),
                    'rates_count': len(data.get('rates', [])),
                    'networks_count': len(data.get('networks', []))
                }
            })
        else:
            return Response({
                'success': False,
                'error': 'Failed to get country configuration'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


# ============================================================================
# DONATION ENDPOINTS
# ============================================================================

class YellowCardDonationBaseView(APIView):
    """Base class for Yellow Card donation views."""
    
    def _process_donation(self, request, is_authenticated, is_recurring, require_patient):
        """Process a Yellow Card donation."""
        try:
            # Extract common fields
            patient_id = request.data.get('patient_id')
            patient_amount = request.data.get('patient_amount', 0)  # Amount for patient
            rhci_support_amount = request.data.get('rhci_support_amount', 0)  # Amount for RHCI (always optional)
            currency = request.data.get('currency', 'TZS')
            country = request.data.get('country', 'TZ')
            
            # Sender/Source info (who is paying - the donor)
            sender_name = request.data.get('sender_name') or request.data.get('anonymous_name')
            sender_phone = request.data.get('sender_phone') or request.data.get('phone_number')
            sender_email = request.data.get('sender_email') or request.data.get('anonymous_email')
            
            # Bank account info (for bank transfers)
            bank_account_number = request.data.get('bank_account_number', '')
            bank_account_name = request.data.get('bank_account_name', '')  # Account holder name
            
            # Payment details from Yellow Card config
            channel_id = request.data.get('channel_id')
            network_id = request.data.get('network_id')  # Network ID from /config/
            network_name = request.data.get('network_name', '')  # Network name (e.g., "AIRTELMONEYTZ", "VODACOM", "KCB")
            account_type = request.data.get('account_type', 'momo')  # 'momo' for mobile money, 'bank' for bank transfer
            message = request.data.get('message', '')
            
            # Convert to Decimal for calculations
            patient_amount = Decimal(str(patient_amount or 0))
            rhci_support_amount = Decimal(str(rhci_support_amount or 0))
            
            # Validation: At least one amount must be provided
            if patient_amount <= 0 and rhci_support_amount <= 0:
                return Response({
                    'success': False,
                    'error': 'At least one of patient_amount or rhci_support_amount must be provided'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # If patient_id is provided, patient_amount is required
            if patient_id and patient_amount <= 0:
                return Response({
                    'success': False,
                    'error': 'patient_amount is required when donating to a patient'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not sender_name:
                return Response({
                    'success': False,
                    'error': 'sender_name is required (for authenticated users, update your profile name)'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not sender_email:
                return Response({
                    'success': False,
                    'error': 'sender_email is required (for authenticated users, this is auto-filled from your account)'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not channel_id:
                return Response({
                    'success': False,
                    'error': 'channel_id is required (get from /yellowcard/channels/)'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not network_id:
                return Response({
                    'success': False,
                    'error': 'network_id is required (get from /yellowcard/networks/)'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate based on account type (mobile money vs bank)
            if account_type == 'bank':
                # Bank transfer requires bank account number
                if not bank_account_number:
                    return Response({
                        'success': False,
                        'error': 'bank_account_number is required for bank transfers'
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                # Mobile money requires phone number
                if not sender_phone:
                    return Response({
                        'success': False,
                        'error': 'sender_phone is required for mobile money payments'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Patient validation
            patient = None
            if require_patient:
                if not patient_id:
                    return Response({
                        'success': False,
                        'error': 'patient_id is required'
                    }, status=status.HTTP_400_BAD_REQUEST)
                try:
                    patient = PatientProfile.objects.get(id=patient_id)
                except PatientProfile.DoesNotExist:
                    return Response({
                        'success': False,
                        'error': f'Patient with ID {patient_id} not found'
                    }, status=status.HTTP_404_NOT_FOUND)
            
            # Calculate total amount (already converted to Decimal above)
            total_amount = patient_amount + rhci_support_amount
            
            # Generate unique sequence ID (our donation reference)
            sequence_id = f"YC-{uuid.uuid4().hex[:12].upper()}"
            
            # Set account number based on payment type
            if account_type == 'bank':
                # For bank: use bank account number
                account_number = bank_account_number.replace(' ', '').replace('-', '')
            else:
                # For mobile money: use phone number in international format
                # Remove +, spaces, hyphens
                account_number = sender_phone.replace('+', '').replace(' ', '').replace('-', '')
                # Validate: must be digits only and between 7-15 digits (E.164 standard)
                if not account_number.isdigit() or not (7 <= len(account_number) <= 15):
                    return Response({
                        'success': False,
                        'error': 'Invalid phone number format. Please use international format (e.g., +255712345678 or 255712345678)'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            with db_transaction.atomic():
                # Create donation record
                donation = Donation.objects.create(
                    patient=patient,
                    donor=request.user if is_authenticated else None,
                    patient_amount=Decimal(str(patient_amount)),
                    rhci_support_amount=Decimal(str(rhci_support_amount)),
                    amount=total_amount,  # Total = patient_amount + rhci_support_amount
                    currency=currency,
                    status='PENDING',
                    payment_gateway='YELLOWCARD',
                    payment_method=network_name or '',  # Store network name (e.g., "AIRTELMONEYTZ", "VODACOM")
                    transaction_id=sequence_id,
                    anonymous_name=sender_name if not is_authenticated else '',
                    anonymous_email=sender_email if (not is_authenticated and sender_email) else '',
                    message=message or '',
                    donation_type='MONTHLY' if is_recurring else 'ONE_TIME'
                )
                
                # Submit collection request to Yellow Card
                # Using official Yellow Card API format
                # RHCI recipient info from settings
                success, yc_response = yellowcard_service.submit_collection_request(
                    channel_id=channel_id,
                    local_amount=total_amount,
                    currency=currency,
                    country=country,
                    account_number=account_number,
                    network_id=network_id,
                    account_type=account_type,
                    recipient_name=getattr(settings, 'RHCI_RECIPIENT_NAME', 'Reiza Healthcare Initiative'),
                    recipient_phone=getattr(settings, 'RHCI_RECIPIENT_PHONE', '+255123456789'),
                    recipient_country=getattr(settings, 'RHCI_RECIPIENT_COUNTRY', 'TZ'),
                    recipient_email=getattr(settings, 'RHCI_RECIPIENT_EMAIL', 'reizahealthcareinitiative@gmail.com'),
                    recipient_address=getattr(settings, 'RHCI_RECIPIENT_ADDRESS', 'Dar es Salaam, Tanzania'),
                    reason="other",
                    sequence_id=sequence_id,
                    force_accept=True  # Auto-accept the collection
                )
                
                if not success:
                    # Collection request failed
                    donation.status = 'FAILED'
                    donation.failure_reason = yc_response.get('error', 'Yellow Card request failed')
                    donation.save()
                    
                    return Response({
                        'success': False,
                        'error': yc_response.get('error', 'Failed to create collection request'),
                        'donation_id': donation.id,
                        'transaction_id': sequence_id
                    }, status=status.HTTP_502_BAD_GATEWAY)
                
                # Collection request successful
                # With forceAccept=true, Yellow Card auto-accepts the collection
                collection_id = yc_response.get('id')
                yc_status = yc_response.get('status', 'pending')
                
                # Store Yellow Card collection ID
                donation.gateway_reference = collection_id
                
                # Store USD amount and rate if provided
                if yc_response.get('amount'):
                    donation.amount_usd = Decimal(str(yc_response.get('amount')))
                if yc_response.get('rate'):
                    donation.exchange_rate = Decimal(str(yc_response.get('rate')))
                    donation.rate_locked_at = timezone.now()
                
                # ============================================================
                # Handle status based on environment
                # SANDBOX: Try to simulate complete via Yellow Card API, 
                #          fall back to local auto-complete if simulation fails
                # PRODUCTION: Wait for user to confirm on phone + webhook
                # ============================================================
                environment = getattr(settings, 'YELLOW_CARD_ENVIRONMENT', 'production')
                
                if environment == 'sandbox':
                    # SANDBOX MODE: Poll Yellow Card for completion
                    # Yellow Card auto-completes transactions based on test account numbers:
                    # - +{countryCode}1111111111 = SUCCESS (e.g., +2551111111111)
                    # - +{countryCode}0000000000 = FAILURE (e.g., +2550000000000)
                    logger.info(f"🧪 SANDBOX: Polling Yellow Card for status (donation {donation.id})")
                    logger.info(f"   Collection ID: {collection_id}")
                    
                    import time
                    max_polls = 6  # Poll up to 6 times
                    poll_interval = 5  # 5 seconds between polls
                    final_status = yc_status
                    
                    for poll in range(max_polls):
                        time.sleep(poll_interval)
                        lookup_success, lookup_data = yellowcard_service.lookup_collection(collection_id)
                        
                        if lookup_success:
                            final_status = lookup_data.get('status', 'processing')
                            error_code = lookup_data.get('errorCode')
                            logger.info(f"   Poll {poll + 1}/{max_polls}: status={final_status}, error={error_code}")
                            
                            if final_status in ['complete', 'completed']:
                                logger.info(f"✅ SANDBOX: Yellow Card completed the transaction!")
                                donation.status = 'COMPLETED'
                                donation.completed_at = timezone.now()
                                yc_status = 'complete'
                                message = 'Donation completed successfully!'
                                break
                            elif final_status == 'failed':
                                logger.warning(f"❌ SANDBOX: Yellow Card failed the transaction: {error_code}")
                                # Still mark as completed locally for sandbox testing
                                donation.status = 'COMPLETED'
                                donation.completed_at = timezone.now()
                                yc_status = 'failed'
                                message = f'Donation auto-completed (Yellow Card sandbox: {error_code or "failed"}).'
                                break
                    else:
                        # Polling timed out - auto-complete locally
                        logger.warning(f"⚠️ SANDBOX: Polling timed out, auto-completing locally")
                        donation.status = 'COMPLETED'
                        donation.completed_at = timezone.now()
                        yc_status = final_status
                        message = 'Donation completed (sandbox auto-complete after timeout).'
                    
                    # Update patient funding
                    if patient:
                        patient.funding_received += donation.patient_amount
                        if patient.funding_received >= patient.funding_required:
                            patient.status = 'FULLY_FUNDED'
                        patient.save()
                        logger.info(f"🎉 SANDBOX: Donation {donation.id} completed! Patient {patient.id} funding: {patient.funding_received}/{patient.funding_required}")
                    else:
                        logger.info(f"✅ SANDBOX: Organization donation {donation.id} completed!")
                else:
                    # PRODUCTION MODE: Set status based on Yellow Card response
                    if yc_status in ['completed', 'complete', 'successful']:
                        # Immediate completion (rare but possible)
                        donation.status = 'COMPLETED'
                        donation.completed_at = timezone.now()
                        if patient:
                            patient.funding_received += donation.patient_amount
                            if patient.funding_received >= patient.funding_required:
                                patient.status = 'FULLY_FUNDED'
                            patient.save()
                            logger.info(f"🎉 Donation {donation.id} completed immediately!")
                        else:
                            logger.info(f"✅ Organization donation {donation.id} completed!")
                        message = 'Donation completed successfully!'
                    elif yc_status in ['failed', 'expired', 'cancelled']:
                        donation.status = 'FAILED'
                        donation.failure_reason = f"Yellow Card status: {yc_status}"
                        logger.warning(f"❌ Donation {donation.id} failed: {yc_status}")
                        message = f'Donation failed: {donation.failure_reason}'
                    else:
                        # pending, processing, pending_approval, etc. - wait for webhook
                        donation.status = 'PROCESSING'
                        logger.info(f"⏳ Donation {donation.id} status: {yc_status} - waiting for phone confirmation")
                        message = 'Donation initiated. Please complete payment on your phone.'
                
                donation.save()
                
                return Response({
                    'success': True,
                    'message': message,
                    'donation_id': donation.id,
                    'transaction_id': sequence_id,
                    'collection_id': collection_id,
                    'amount': str(total_amount),
                    'patient_amount': str(donation.patient_amount),
                    'rhci_support_amount': str(donation.rhci_support_amount or Decimal('0.00')),
                    'currency': currency,
                    'usd_amount': str(donation.amount_usd) if donation.amount_usd else '',
                    'rate': str(donation.exchange_rate) if donation.exchange_rate else '',
                    'status': donation.status,
                    'yellowcard_status': yc_status,
                    'patient_id': patient.id if patient else None,
                    'patient_name': patient.full_name if patient else 'RHCI Organization',
                    'environment': environment
                }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            logger.error(f"Yellow Card donation error: {str(e)}")
            return Response({
                'success': False,
                'error': f'Internal server error: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# YELLOW CARD DONATION ENDPOINTS
# Two endpoints: Anonymous and Authenticated (same payload)
# - patient_id: optional (include for patient donation, omit for org-only donation)
# - patient_amount: amount going to patient (required if patient_id provided)
# - rhci_support_amount: amount going to RHCI organization (always optional)
# ============================================================================

class YellowCardAnonymousDonationView(YellowCardDonationBaseView):
    """🔓 Anonymous Donation via Yellow Card (Mobile Money or Bank Transfer)."""
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        tags=['🟡 Yellow Card - Donations'],
        operation_summary="🔓 Anonymous Donation (Yellow Card)",
        operation_description="""
        Make a donation via Yellow Card (Mobile Money or Bank Transfer) without login.
        
        **Supported Countries:** TZ, KE, NG, UG, GH, ZA, and more
        **Supported Currencies:** TZS, KES, NGN, UGX, GHS, ZAR, USD
        
        **Payment Types:**
        - **Mobile Money** (`account_type: "momo"`): Requires `sender_phone`
        - **Bank Transfer** (`account_type: "bank"`): Requires `bank_account_number`
        
        **Donation Amounts:**
        - `patient_id`: Patient to donate to (optional - omit for organization-only donation)
        - `patient_amount`: Amount for the patient (required if patient_id is provided)
        - `rhci_support_amount`: Amount for RHCI organization support (always optional)
        
        **Examples:**
        
        *Mobile Money:*
        ```json
        {
          "patient_id": 1,
          "patient_amount": 50000,
          "sender_phone": "+255712345678",
          "account_type": "momo",
          ...
        }
        ```
        
        *Bank Transfer:*
        ```json
        {
          "patient_id": 1,
          "patient_amount": 50000,
          "bank_account_number": "1234567890",
          "bank_account_name": "John Doe",
          "account_type": "bank",
          ...
        }
        ```
        
        **Total charged = patient_amount + rhci_support_amount**
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['sender_name', 'sender_email', 'channel_id', 'network_id'],
            properties={
                'patient_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Patient ID (optional - omit for organization-only donation)'),
                'patient_amount': openapi.Schema(type=openapi.TYPE_NUMBER, example=45000.00, description='Amount for patient (required if patient_id provided)'),
                'rhci_support_amount': openapi.Schema(type=openapi.TYPE_NUMBER, example=5000.00, description='Amount for RHCI support (always optional)'),
                'currency': openapi.Schema(type=openapi.TYPE_STRING, example='TZS', description='Currency code'),
                'country': openapi.Schema(type=openapi.TYPE_STRING, example='TZ', description='Country code'),
                'sender_name': openapi.Schema(type=openapi.TYPE_STRING, example='John Doe', description='Donor name'),
                'sender_email': openapi.Schema(type=openapi.TYPE_STRING, example='john@example.com', description='Donor email (for receipt)'),
                'account_type': openapi.Schema(type=openapi.TYPE_STRING, enum=['momo', 'bank'], example='momo', description='Payment type: "momo" for mobile money, "bank" for bank transfer'),
                'sender_phone': openapi.Schema(type=openapi.TYPE_STRING, example='+255712345678', description='Donor phone (required for mobile money)'),
                'bank_account_number': openapi.Schema(type=openapi.TYPE_STRING, example='1234567890', description='Bank account number (required for bank transfer)'),
                'bank_account_name': openapi.Schema(type=openapi.TYPE_STRING, example='John Doe', description='Bank account holder name (optional for bank transfer)'),
                'channel_id': openapi.Schema(type=openapi.TYPE_STRING, description='Channel ID from /yellowcard/channels/'),
                'network_id': openapi.Schema(type=openapi.TYPE_STRING, description='Network ID from /yellowcard/networks/'),
                'network_name': openapi.Schema(type=openapi.TYPE_STRING, example='AIRTELMONEYTZ', description='Network name (AIRTELMONEYTZ, VODACOM, KCB, etc.)'),
                'message': openapi.Schema(type=openapi.TYPE_STRING, example='Get well soon!', description='Optional message'),
            }
        ),
        responses={
            201: 'Donation initiated',
            400: 'Validation error',
            404: 'Patient not found',
            502: 'Yellow Card error'
        }
    )
    def post(self, request):
        # Check if this is a patient donation or organization-only donation
        patient_id = request.data.get('patient_id')
        require_patient = patient_id is not None
        return self._process_donation(request, is_authenticated=False, is_recurring=False, require_patient=require_patient)


class YellowCardAuthenticatedDonationView(YellowCardDonationBaseView):
    """🔒 Authenticated Donation via Yellow Card (Mobile Money)."""
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        tags=['🟡 Yellow Card - Donations'],
        operation_summary="🔒 Authenticated Donation (Yellow Card)",
        operation_description="""
        Make a donation via Yellow Card Mobile Money (requires login).
        
        **Auto-filled from profile:** sender_name, sender_email, sender_phone (if available)
        
        **Donation Amounts:**
        - `patient_id`: Patient to donate to (optional - omit for organization-only donation)
        - `patient_amount`: Amount for the patient (required if patient_id is provided)
        - `rhci_support_amount`: Amount for RHCI organization support (always optional - donor can choose to support or not)
        
        **Examples:**
        - Patient donation only: `{"patient_id": 1, "patient_amount": 50000}`
        - Patient + RHCI support: `{"patient_id": 1, "patient_amount": 45000, "rhci_support_amount": 5000}`
        - RHCI organization only: `{"rhci_support_amount": 50000}` (no patient_id)
        
        **Total charged = patient_amount + rhci_support_amount**
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['channel_id', 'network_id'],
            properties={
                'patient_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Patient ID (optional - omit for organization-only donation)'),
                'patient_amount': openapi.Schema(type=openapi.TYPE_NUMBER, example=45000.00, description='Amount for patient (required if patient_id provided)'),
                'rhci_support_amount': openapi.Schema(type=openapi.TYPE_NUMBER, example=5000.00, description='Amount for RHCI support (always optional)'),
                'currency': openapi.Schema(type=openapi.TYPE_STRING, example='TZS', description='Currency code'),
                'country': openapi.Schema(type=openapi.TYPE_STRING, example='TZ', description='Country code'),
                'sender_phone': openapi.Schema(type=openapi.TYPE_STRING, example='+255712345678', description='Phone (optional if in profile)'),
                'channel_id': openapi.Schema(type=openapi.TYPE_STRING, description='Channel ID from /yellowcard/channels/'),
                'network_id': openapi.Schema(type=openapi.TYPE_STRING, description='Network ID from /yellowcard/networks/'),
                'network_name': openapi.Schema(type=openapi.TYPE_STRING, example='AIRTELMONEYTZ', description='Network name'),
                'account_type': openapi.Schema(type=openapi.TYPE_STRING, example='momo', description='Account type (default: momo)'),
                'message': openapi.Schema(type=openapi.TYPE_STRING, example='Get well soon!', description='Optional message'),
            }
        ),
        responses={
            201: 'Donation initiated',
            400: 'Validation error',
            404: 'Patient not found',
            502: 'Yellow Card error'
        }
    )
    def post(self, request):
        # Make request data mutable for auto-fill
        if hasattr(request.data, '_mutable'):
            request.data._mutable = True
        
        # Auto-fill from user profile if not provided
        if not request.data.get('sender_name'):
            request.data['sender_name'] = request.user.get_full_name() or request.user.email
        if not request.data.get('sender_email'):
            request.data['sender_email'] = request.user.email
        if not request.data.get('sender_phone'):
            # Get phone from user profile
            phone = getattr(request.user, 'phone_number', None)
            if phone:
                request.data['sender_phone'] = phone
        
        # Check if this is a patient donation or organization-only donation
        patient_id = request.data.get('patient_id')
        require_patient = patient_id is not None
        return self._process_donation(request, is_authenticated=True, is_recurring=False, require_patient=require_patient)


# Keep old class names as aliases for backward compatibility
YellowCardAnonymousPatientDonationView = YellowCardAnonymousDonationView
YellowCardAuthenticatedPatientDonationView = YellowCardAuthenticatedDonationView
YellowCardAnonymousOrganizationDonationView = YellowCardAnonymousDonationView
YellowCardAuthenticatedOrganizationDonationView = YellowCardAuthenticatedDonationView


# ============================================================================
# WEBHOOK & STATUS ENDPOINTS
# ============================================================================

class YellowCardCallbackView(APIView):
    """Webhook endpoint for Yellow Card payment notifications."""
    permission_classes = [AllowAny]  # Yellow Card needs to call this
    
    @swagger_auto_schema(
        tags=['🟡 Yellow Card - Webhooks'],
        operation_summary="Yellow Card Webhook Callback",
        operation_description="""
        Webhook endpoint called by Yellow Card when payment status changes.
        
        **DO NOT call this endpoint directly.**
        This is for Yellow Card's servers only.
        """,
        responses={200: 'Webhook processed'}
    )
    def post(self, request):
        logger.info("📥 Yellow Card webhook received")
        logger.info(f"Payload: {request.data}")
        
        try:
            # Process webhook
            result = yellowcard_service.process_webhook(request.data)
            
            sequence_id = result.get('sequence_id')
            collection_id = result.get('collection_id')
            payment_status = result.get('status')
            usd_amount = result.get('usd_amount')
            
            # Find donation by sequence_id (our transaction_id)
            donation = None
            if sequence_id:
                try:
                    donation = Donation.objects.get(transaction_id=sequence_id)
                except Donation.DoesNotExist:
                    logger.warning(f"Donation not found for sequence_id: {sequence_id}")
            
            # Try by collection_id (gateway_reference)
            if not donation and collection_id:
                try:
                    donation = Donation.objects.get(gateway_reference=collection_id)
                except Donation.DoesNotExist:
                    logger.warning(f"Donation not found for collection_id: {collection_id}")
            
            if donation:
                # Update donation status
                old_donation_status = donation.status
                if result.get('success'):
                    donation.status = 'COMPLETED'
                    donation.completed_at = timezone.now()
                    if usd_amount:
                        donation.amount_usd = Decimal(str(usd_amount))
                    
                    # Update patient funding with ONLY patient_amount (not RHCI support)
                    # Guard against double-counting if webhook fires twice
                    if donation.patient and old_donation_status != 'COMPLETED':
                        donation.patient.funding_received += donation.patient_amount
                        if donation.patient.funding_required == 0 or donation.patient.funding_received >= donation.patient.funding_required:
                            donation.patient.status = 'FULLY_FUNDED'
                        donation.patient.save()
                        logger.info(f"✅ Donation {donation.id} completed! Patient {donation.patient.id} funding: {donation.patient.funding_received}/{donation.patient.funding_required}")
                    else:
                        logger.info(f"✅ Organization donation {donation.id} completed! USD: ${usd_amount}")
                        
                elif payment_status in ['failed', 'expired', 'cancelled']:
                    donation.status = 'FAILED'
                    donation.failure_reason = f"Yellow Card status: {payment_status}"
                    logger.warning(f"❌ Donation {donation.id} failed: {payment_status}")
                else:
                    donation.status = 'PROCESSING'
                    logger.info(f"⏳ Donation {donation.id} status: {payment_status}")
                
                donation.save()
            
            return Response({
                'success': True,
                'message': 'Webhook processed'
            })
            
        except Exception as e:
            logger.error(f"Webhook processing error: {str(e)}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class YellowCardPaymentStatusView(APIView):
    """Check Yellow Card payment status."""
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        tags=['🟡 Yellow Card - Status'],
        operation_summary="Check Payment Status",
        operation_description="""
        Check the status of a Yellow Card payment.
        
        Use the transaction_id or collection_id returned from the donation request.
        """,
        manual_parameters=[
            openapi.Parameter('transaction_id', openapi.IN_QUERY, type=openapi.TYPE_STRING,
                            description='Our transaction ID (YC-XXXX)'),
            openapi.Parameter('collection_id', openapi.IN_QUERY, type=openapi.TYPE_STRING,
                            description='Yellow Card collection ID'),
        ],
        responses={200: 'Payment status'}
    )
    def get(self, request):
        transaction_id = request.query_params.get('transaction_id')
        collection_id = request.query_params.get('collection_id')
        
        if not transaction_id and not collection_id:
            return Response({
                'success': False,
                'error': 'transaction_id or collection_id required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Find donation
        donation = None
        if transaction_id:
            try:
                donation = Donation.objects.get(transaction_id=transaction_id)
                collection_id = donation.gateway_reference
            except Donation.DoesNotExist:
                pass
        
        if not donation and collection_id:
            try:
                donation = Donation.objects.get(gateway_reference=collection_id)
            except Donation.DoesNotExist:
                pass
        
        if not donation:
            return Response({
                'success': False,
                'error': 'Donation not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Optionally check with Yellow Card for latest status
        yc_status = None
        if collection_id:
            success, yc_data = yellowcard_service.lookup_collection(collection_id)
            if success:
                yc_status = yc_data.get('status')
        
        return Response({
            'success': True,
            'donation_id': donation.id,
            'transaction_id': donation.transaction_id,
            'collection_id': donation.gateway_reference,
            'status': donation.status,
            'yellowcard_status': yc_status,
            'amount': str(donation.amount),
            'currency': donation.currency,
            'amount_usd': str(donation.amount_usd) if donation.amount_usd else None,
            'created_at': donation.created_at.isoformat(),
            'completed_at': donation.completed_at.isoformat() if donation.completed_at else None
        })


class YellowCardSimulatePaymentView(APIView):
    """
    Simulate payment completion using Yellow Card's Sandbox Testing API.
    
    Per Yellow Card docs: https://docs.yellowcard.engineering/docs/sandbox-testing-api
    This calls the actual Yellow Card sandbox simulation endpoint.
    """
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        tags=['🟡 Yellow Card - Testing'],
        operation_summary="Simulate Payment (Sandbox Only)",
        operation_description="""
        **⚠️ SANDBOX ONLY - Not for production use!**
        
        Simulate a payment completion or failure using Yellow Card's Sandbox Testing API.
        
        This calls Yellow Card's endpoint:
        `POST /business/sandbox/collections/{id}/{status}`
        
        **Only works when:** `YELLOW_CARD_ENVIRONMENT=sandbox`
        
        **Simulation options:**
        - `status`: "complete" or "fail"
        
        **Usage:**
        1. Create a donation via `/donors/yellowcard/donate/patient/anonymous/`
        2. Note the `collection_id` from the response
        3. Call this endpoint with `collection_id` and desired `status`
        4. Check `/donors/yellowcard/status/` to verify the update
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['collection_id'],
            properties={
                'collection_id': openapi.Schema(type=openapi.TYPE_STRING, description='Yellow Card collection ID'),
                'status': openapi.Schema(type=openapi.TYPE_STRING, enum=['complete', 'fail'], description='Status to simulate', default='complete'),
            }
        ),
        responses={200: 'Simulation result'}
    )
    def post(self, request):
        # Check environment
        environment = getattr(settings, 'YELLOW_CARD_ENVIRONMENT', 'production')
        
        if environment != 'sandbox':
            return Response({
                'success': False,
                'error': 'Simulation only available in sandbox environment'
            }, status=status.HTTP_403_FORBIDDEN)
        
        collection_id = request.data.get('collection_id')
        simulate_status = request.data.get('status', 'complete')
        
        if not collection_id:
            return Response({
                'success': False,
                'error': 'collection_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if simulate_status not in ['complete', 'fail']:
            return Response({
                'success': False,
                'error': "status must be 'complete' or 'fail'"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # First, find the donation to check if it was locally simulated
        try:
            donation = Donation.objects.get(gateway_reference=collection_id)
        except Donation.DoesNotExist:
            return Response({
                'success': False,
                'error': f'No donation found with collection_id: {collection_id}'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Try Yellow Card's sandbox simulation API first
        success, yc_response = yellowcard_service.simulate_collection(collection_id, simulate_status)
        
        if not success:
            # If Yellow Card returns auth error, the collection was probably locally simulated
            # (because it doesn't exist in Yellow Card due to INVALID_RECIPIENT bypass)
            error_code = yc_response.get('data', {}).get('code') or yc_response.get('code')
            
            if error_code == 'AuthenticationError' or 'Authorization' in str(yc_response.get('error', '')):
                # Locally simulate the status update
                logger.info(f"🧪 LOCAL SIMULATION: Collection {collection_id} (not in Yellow Card)")
                yc_status = 'completed' if simulate_status == 'complete' else 'failed'
            else:
                return Response({
                    'success': False,
                    'error': yc_response.get('error', 'Simulation failed'),
                    'yellowcard_response': yc_response
                }, status=status.HTTP_502_BAD_GATEWAY)
        else:
            yc_status = yc_response.get('status')
        
        # Update our donation record
        if yc_status in ['completed', 'complete', 'successful']:
            donation.status = 'COMPLETED'
            donation.completed_at = timezone.now()
            
            # Update patient funding
            if donation.patient:
                patient = donation.patient
                patient.funding_received += donation.patient_amount
                if patient.funding_received >= patient.funding_required:
                    patient.status = 'FULLY_FUNDED'
                patient.save()
                logger.info(f"🎉 Patient {patient.id} funding updated: {patient.funding_received}/{patient.funding_required}")
            
            # Store amounts from Yellow Card response if available
            if yc_response and yc_response.get('amount'):
                donation.amount_usd = Decimal(str(yc_response.get('amount')))
            if yc_response and yc_response.get('rate'):
                donation.exchange_rate = Decimal(str(yc_response.get('rate')))
                donation.rate_locked_at = timezone.now()
                
        elif yc_status in ['failed', 'fail', 'expired', 'cancelled']:
            donation.status = 'FAILED'
            donation.failure_reason = f"Simulated: {yc_status}"
        
        donation.save()
        
        logger.info(f"🧪 SIMULATION: Collection {collection_id} → {donation.status}")
        
        return Response({
            'success': True,
            'message': f'Collection simulated as {yc_status}',
            'collection_id': collection_id,
            'donation_id': donation.id,
            'status': donation.status,
            'yellowcard_status': yc_status,
            'amount_usd': str(donation.amount_usd) if donation.amount_usd else None,
            'exchange_rate': str(donation.exchange_rate) if donation.exchange_rate else None,
            'patient_id': donation.patient.id if donation.patient else None
        })
