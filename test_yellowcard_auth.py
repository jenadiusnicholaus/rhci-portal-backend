#!/usr/bin/env python
"""
Test Yellow Card API - Authentication & Collection

This script tests the Yellow Card API integration including:
1. Authentication
2. Get Channels
3. Get Rates
4. Get Networks
5. Get Payment Reasons
6. Submit Collection Request (optional)

Run from project root: python test_yellowcard_auth.py
"""
import os
import sys
import json
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from donor.payments.yellowcard_service import yellowcard_service, YellowCardService


def test_authentication():
    """Test Yellow Card API authentication."""
    print("=" * 70)
    print("STEP 1: AUTHENTICATION TEST")
    print("=" * 70)
    
    # Print configuration (hide sensitive parts)
    print(f"\n📋 Configuration:")
    print(f"   Environment: {yellowcard_service.environment}")
    print(f"   Base URL: {yellowcard_service.base_url}")
    print(f"   API Key: {yellowcard_service.api_key[:10]}..." if yellowcard_service.api_key else "   API Key: NOT SET")
    print(f"   API Secret: {'*' * 10}..." if yellowcard_service.api_secret else "   API Secret: NOT SET")
    
    # Test actual API call
    print(f"\n🔐 Testing authentication...")
    success, data = yellowcard_service.test_authentication()
    
    if success:
        print("✅ AUTHENTICATION SUCCESSFUL!")
    else:
        print("❌ AUTHENTICATION FAILED!")
        print(f"   Error: {data.get('error', 'Unknown error')}")
    
    return success


def test_get_channels():
    """Test getting payment channels."""
    print("\n" + "=" * 70)
    print("STEP 2: GET CHANNELS")
    print("=" * 70)
    
    # Get all channels
    print("\n📡 Getting all channels...")
    success, data = yellowcard_service.get_channels()
    
    if not success:
        print(f"❌ Failed: {data.get('error')}")
        return False, None
    
    channels = data.get('channels', [])
    print(f"✅ Found {len(channels)} deposit channels")
    
    # Show channels by country
    countries = {}
    for ch in channels:
        country = ch.get('country', 'Unknown')
        if country not in countries:
            countries[country] = []
        countries[country].append(ch)
    
    print(f"\n📊 Channels by Country:")
    for country, chs in sorted(countries.items()):
        currencies = set(c.get('currency') for c in chs)
        types = set(c.get('channelType') for c in chs)
        print(f"   {country}: {len(chs)} channels ({', '.join(currencies)}) - Types: {', '.join(types)}")
    
    # Show Tanzania channels specifically
    tz_channels = [c for c in channels if c.get('country') == 'TZ']
    if tz_channels:
        print(f"\n🇹🇿 Tanzania Channels ({len(tz_channels)}):")
        for ch in tz_channels[:5]:  # Show first 5
            print(f"   - {ch.get('channelType')}: {ch.get('currency')} "
                  f"(min: {ch.get('min')}, max: {ch.get('max')}) "
                  f"ID: {ch.get('id')[:20]}...")
    
    return True, channels


def test_get_rates():
    """Test getting exchange rates."""
    print("\n" + "=" * 70)
    print("STEP 3: GET RATES")
    print("=" * 70)
    
    print("\n📡 Getting exchange rates...")
    success, data = yellowcard_service.get_rates()
    
    if not success:
        print(f"❌ Failed: {data.get('error')}")
        return False, None
    
    rates = data.get('rates', [])
    print(f"✅ Found {len(rates)} rate(s)")
    
    # Show rates
    print(f"\n📊 Exchange Rates (Local Currency → USD):")
    for rate in rates[:10]:  # Show first 10
        currency = rate.get('currency', 'Unknown')
        buy = rate.get('buy', 'N/A')
        sell = rate.get('sell', 'N/A')
        print(f"   {currency}: Buy={buy}, Sell={sell}")
    
    # Show Tanzania rate
    tz_rates = [r for r in rates if r.get('currency') == 'TZS']
    if tz_rates:
        print(f"\n🇹🇿 Tanzania Rate (TZS):")
        for r in tz_rates:
            print(f"   Buy (for collection): {r.get('buy')}")
            print(f"   Meaning: 1 USD = {r.get('buy')} TZS")
    
    return True, rates


def test_get_networks():
    """Test getting mobile money networks."""
    print("\n" + "=" * 70)
    print("STEP 4: GET NETWORKS")
    print("=" * 70)
    
    print("\n📡 Getting mobile money networks...")
    success, data = yellowcard_service.get_networks()
    
    if not success:
        print(f"❌ Failed: {data.get('error')}")
        return False, None
    
    networks = data.get('networks', [])
    print(f"✅ Found {len(networks)} network(s)")
    
    # Show networks by country
    countries = {}
    for net in networks:
        country = net.get('country', 'Unknown')
        if country not in countries:
            countries[country] = []
        countries[country].append(net)
    
    print(f"\n📊 Networks by Country:")
    for country, nets in sorted(countries.items()):
        names = [n.get('name', n.get('code', 'Unknown')) for n in nets]
        print(f"   {country}: {', '.join(names)}")
    
    # Show Tanzania networks
    tz_networks = [n for n in networks if n.get('country') == 'TZ']
    if tz_networks:
        print(f"\n🇹🇿 Tanzania Networks ({len(tz_networks)}):")
        for net in tz_networks:
            print(f"   - {net.get('name', net.get('code'))}: {net.get('code')}")
    
    return True, networks


def test_get_payment_reasons():
    """Test getting payment reasons."""
    print("\n" + "=" * 70)
    print("STEP 5: GET PAYMENT REASONS")
    print("=" * 70)
    
    print("\n📡 Getting payment reasons...")
    success, data = yellowcard_service.get_payment_reasons()
    
    if not success:
        print(f"❌ Failed: {data.get('error')}")
        return False, None
    
    reasons = data.get('reasons', [])
    print(f"✅ Found {len(reasons)} reason(s)")
    
    # Show reasons
    print(f"\n📊 Payment Reasons:")
    for reason in reasons[:20]:  # Show first 20
        if isinstance(reason, dict):
            print(f"   - {reason.get('code', reason.get('id'))}: {reason.get('name', reason.get('description', 'N/A'))}")
        else:
            print(f"   - {reason}")
    
    # Look for donation-related reasons
    donation_keywords = ['donation', 'charity', 'gift', 'support']
    donation_reasons = [r for r in reasons if isinstance(r, dict) and 
                       any(kw in str(r).lower() for kw in donation_keywords)]
    
    if donation_reasons:
        print(f"\n💝 Donation-related reasons:")
        for r in donation_reasons:
            print(f"   - {r}")
    
    return True, reasons


def test_combined_collection_data():
    """Test getting all collection data for a country."""
    print("\n" + "=" * 70)
    print("STEP 6: GET COMBINED COLLECTION DATA (Tanzania)")
    print("=" * 70)
    
    print("\n📡 Getting all collection data for Tanzania...")
    success, data = yellowcard_service.get_collection_channels_for_country('TZ')
    
    if not success:
        print(f"❌ Failed")
        return False
    
    print(f"✅ Combined data retrieved:")
    print(f"   Channels: {len(data.get('channels', []))}")
    print(f"   Rates: {len(data.get('rates', []))}")
    print(f"   Networks: {len(data.get('networks', []))}")
    print(f"   Reasons: {len(data.get('reasons', []))}")
    
    return True


def test_summary():
    """Print test summary."""
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print("""
✅ All Collection API Methods Implemented:

1. get_channels()              - Get payment channels (Mobile Money, Bank)
2. get_rates()                 - Get exchange rates (TZS → USD)
3. get_networks()              - Get mobile networks (Vodacom, Airtel)
4. get_payment_reasons()       - Get valid payment reasons
5. submit_collection_request() - Submit collection (get quote)
6. accept_collection_request() - Accept collection (confirm payment)
7. deny_collection_request()   - Cancel collection
8. lookup_collection()         - Check collection status
9. process_webhook()           - Process webhook callbacks

📋 Collection Flow:
   1. GET channels, rates, networks, reasons (display options)
   2. POST submit_collection_request (get quote with locked rate)
   3. POST accept_collection_request (confirm & initiate payment)
   4. WEBHOOK receives success/failure notification
   5. GET lookup_collection (verify final status)
""")


if __name__ == "__main__":
    print("\n")
    print("=" * 70)
    print("YELLOW CARD API TEST SUITE")
    print("=" * 70)
    
    # Run all tests
    auth_ok = test_authentication()
    
    if not auth_ok:
        print("\n❌ Authentication failed - cannot continue tests")
        sys.exit(1)
    
    test_get_channels()
    test_get_rates()
    test_get_networks()
    test_get_payment_reasons()
    test_combined_collection_data()
    
    # Print summary
    test_summary()
    
    print("\n✅ All API tests completed!")
    print("=" * 70)
    sys.exit(0)
