"""
Email verification utilities for donor and patient registration
"""
import secrets
import hashlib
import logging
from datetime import timedelta
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def generate_verification_token():
    """Generate a secure random token for email verification"""
    return secrets.token_urlsafe(32)


def create_verification_token_hash(token):
    """Create a hash of the verification token for secure storage"""
    return hashlib.sha256(token.encode()).hexdigest()


def is_token_expired(sent_at, expiry_hours=24):
    """Check if verification token has expired (default 24 hours)"""
    if not sent_at:
        return True
    expiry_time = sent_at + timedelta(hours=expiry_hours)
    return timezone.now() > expiry_time


def send_verification_email(user, verification_url, user_type='donor'):
    """
    Send email verification link to user
    
    Args:
        user: CustomUser instance
        verification_url: Full URL for email verification
        user_type: 'donor' or 'patient' for customized messaging
    """
    subject = f"Verify Your RHCI {user_type.capitalize()} Account"
    
    logger.info(f"Preparing verification email for {user.email} ({user_type})")
    
    # Context for email template
    context = {
        'user_name': user.get_full_name() or user.email,
        'verification_url': verification_url,
        'user_type': user_type.capitalize(),
        'expiry_hours': 24,
    }
    
    try:
        # Render HTML email
        html_message = render_to_string('emails/email_verification.html', context)
        plain_message = strip_tags(html_message)
        
        logger.info(f"Template rendered successfully for {user.email}")
        logger.debug(f"Verification URL: {verification_url}")
        
        # Send email
        result = send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Email sent to {user.email}. Send result: {result}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending email to {user.email}: {str(e)}", exc_info=True)
        raise


def verify_email_token(user, token):
    """
    Verify the email token for a user
    
    Args:
        user: CustomUser instance
        token: Token to verify
        
    Returns:
        tuple: (success: bool, message: str)
    """
    # Check if user is already verified
    if user.is_verified:
        return False, "Email already verified"
    
    # Check if token exists
    if not user.email_verification_token:
        return False, "No verification token found"
    
    # Check if token is expired
    if is_token_expired(user.email_verification_sent_at):
        return False, "Verification link has expired. Please request a new one."
    
    # Create hash of provided token and compare
    token_hash = create_verification_token_hash(token)
    
    if token_hash != user.email_verification_token:
        return False, "Invalid verification token"
    
    # Mark user as verified
    user.is_verified = True
    user.is_active = True
    user.email_verification_token = None  # Clear token after use
    user.email_verification_sent_at = None
    user.save()
    
    return True, "Email verified successfully"


def resend_verification_email(user, verification_url, user_type='donor'):
    """
    Resend verification email (generates new token)
    
    Args:
        user: CustomUser instance
        verification_url: Base URL for verification (token will be appended)
        user_type: 'donor' or 'patient'
        
    Returns:
        tuple: (success: bool, message: str)
    """
    # Check if already verified
    if user.is_verified:
        return False, "Email already verified"
    
    # Check rate limiting (can only resend after 2 minutes)
    if user.email_verification_sent_at:
        time_since_last_send = timezone.now() - user.email_verification_sent_at
        if time_since_last_send < timedelta(minutes=2):
            remaining = 2 - (time_since_last_send.seconds // 60)
            return False, f"Please wait {remaining} minute(s) before requesting another email"
    
    # Generate new token
    token = generate_verification_token()
    token_hash = create_verification_token_hash(token)
    
    # Update user
    user.email_verification_token = token_hash
    user.email_verification_sent_at = timezone.now()
    user.save()
    
    # Send email with new token
    full_verification_url = f"{verification_url}?token={token}"
    send_verification_email(user, full_verification_url, user_type)
    
    return True, "Verification email sent successfully"
