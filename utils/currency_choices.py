"""
Shared currency choices for the application
Used by Donation, PatientProfile, and DonationAmountOption models
"""

CURRENCY_CHOICES = [
    ('USD', 'US Dollar ($)'),
    ('EUR', 'Euro (€)'),
    ('GBP', 'British Pound (£)'),
    ('TZS', 'Tanzanian Shilling (TSh)'),
    ('KES', 'Kenyan Shilling (KSh)'),
    ('UGX', 'Ugandan Shilling (USh)'),
    ('ZAR', 'South African Rand (R)'),
    ('NGN', 'Nigerian Naira (₦)'),
    ('GHS', 'Ghanaian Cedi (GH₵)'),
    ('CAD', 'Canadian Dollar (C$)'),
    ('AUD', 'Australian Dollar (A$)'),
]

CURRENCY_SYMBOLS = {
    'USD': '$',
    'EUR': '€',
    'GBP': '£',
    'TZS': 'TSh',
    'KES': 'KSh',
    'UGX': 'USh',
    'ZAR': 'R',
    'NGN': '₦',
    'GHS': 'GH₵',
    'CAD': 'C$',
    'AUD': 'A$',
}
