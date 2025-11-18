from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import PatientProfile, PatientTimeline


@receiver(post_save, sender=PatientProfile)
def create_patient_timeline_events(sender, instance, created, **kwargs):
    """
    Automatically create timeline events when patient profile changes
    """
    # When patient is first created
    if created:
        PatientTimeline.objects.create(
            patient_profile=instance,
            event_type='PROFILE_SUBMITTED',
            title='Profile Submitted',
            description=f'{instance.full_name} has submitted their profile for review.',
            is_milestone=True,
            is_visible=True,
            is_current_state=True
        )
        return
    
    # Get the previous state from database (before save)
    try:
        old_instance = PatientProfile.objects.get(pk=instance.pk)
    except PatientProfile.DoesNotExist:
        return
    
    # Check if treatment_date was just set
    if not old_instance.treatment_date and instance.treatment_date:
        PatientTimeline.objects.create(
            patient_profile=instance,
            event_type='TREATMENT_SCHEDULED',
            title='Treatment Scheduled',
            description=f'Treatment has been scheduled for {instance.treatment_date.strftime("%B %d, %Y")}.',
            event_date=instance.treatment_date,
            is_milestone=True,
            is_visible=True,
            metadata={'treatment_date': str(instance.treatment_date)}
        )
    
    # Check if status changed
    if old_instance.status != instance.status:
        event_type_map = {
            'PUBLISHED': 'PROFILE_PUBLISHED',
            'AWAITING_FUNDING': 'AWAITING_FUNDING',
            'FULLY_FUNDED': 'FULLY_FUNDED',
            'TREATMENT_COMPLETE': 'TREATMENT_COMPLETE',
        }
        
        event_type = event_type_map.get(instance.status, 'STATUS_CHANGED')
        
        title_map = {
            'PROFILE_PUBLISHED': 'Profile Published',
            'AWAITING_FUNDING': 'Now Awaiting Funding',
            'FULLY_FUNDED': 'Fully Funded!',
            'TREATMENT_COMPLETE': 'Treatment Complete',
            'STATUS_CHANGED': f'Status Changed to {instance.get_status_display()}',
        }
        
        description_map = {
            'PROFILE_PUBLISHED': f'{instance.full_name}\'s profile is now published and visible to donors.',
            'AWAITING_FUNDING': f'{instance.full_name}\'s profile is now seeking funding from donors.',
            'FULLY_FUNDED': f'{instance.full_name} has reached their funding goal!',
            'TREATMENT_COMPLETE': f'{instance.full_name} has successfully completed their treatment.',
            'STATUS_CHANGED': f'Status updated to {instance.get_status_display()}.',
        }
        
        # Unmark previous current_state events
        PatientTimeline.objects.filter(
            patient_profile=instance,
            is_current_state=True
        ).update(is_current_state=False)
        
        PatientTimeline.objects.create(
            patient_profile=instance,
            event_type=event_type,
            title=title_map.get(event_type, title_map['STATUS_CHANGED']),
            description=description_map.get(event_type, description_map['STATUS_CHANGED']),
            is_milestone=event_type in ['PROFILE_PUBLISHED', 'FULLY_FUNDED', 'TREATMENT_COMPLETE'],
            is_visible=True,
            is_current_state=True,
            metadata={'old_status': old_instance.status, 'new_status': instance.status}
        )
    
    # Check for funding milestones (25%, 50%, 75%)
    if old_instance.funding_received != instance.funding_received and instance.funding_required > 0:
        old_percentage = (old_instance.funding_received / instance.funding_required) * 100 if instance.funding_required > 0 else 0
        new_percentage = (instance.funding_received / instance.funding_required) * 100
        
        milestones = [25, 50, 75]
        for milestone in milestones:
            if old_percentage < milestone <= new_percentage:
                PatientTimeline.objects.create(
                    patient_profile=instance,
                    event_type='FUNDING_MILESTONE',
                    title=f'{milestone}% Funded!',
                    description=f'{instance.full_name} has reached {milestone}% of their funding goal.',
                    is_milestone=True,
                    is_visible=True,
                    metadata={
                        'milestone_percentage': milestone,
                        'amount_raised': str(instance.funding_received),
                        'funding_goal': str(instance.funding_required)
                    }
                )
