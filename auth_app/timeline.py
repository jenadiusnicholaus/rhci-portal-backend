from django.db import models
from django.utils import timezone


class PatientTimeline(models.Model):
    """
    Timeline events for patient journey from submission to treatment completion
    """
    EVENT_TYPES = [
        ('PROFILE_SUBMITTED', 'Profile Submitted'),
        ('TREATMENT_SCHEDULED', 'Treatment Scheduled'),
        ('PROFILE_PUBLISHED', 'Profile Published'),
        ('AWAITING_FUNDING', 'Awaiting Funding'),
        ('FUNDING_MILESTONE', 'Funding Milestone Reached'),
        ('FULLY_FUNDED', 'Fully Funded'),
        ('TREATMENT_STARTED', 'Treatment Started'),
        ('TREATMENT_COMPLETE', 'Treatment Complete'),
        ('UPDATE_POSTED', 'Update Posted'),
        ('STATUS_CHANGED', 'Status Changed'),
    ]
    
    patient_profile = models.ForeignKey(
        'PatientProfile',
        on_delete=models.CASCADE,
        related_name='timeline_events'
    )
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES)
    title = models.CharField(max_length=200, help_text="Event title for display")
    description = models.TextField(help_text="Detailed description of the event")
    
    # Optional fields for additional context
    created_by = models.ForeignKey(
        'CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="User who triggered this event (admin, coordinator, etc.)"
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional data like funding amount, location, etc."
    )
    
    is_milestone = models.BooleanField(
        default=False,
        help_text="Mark important events as milestones"
    )
    is_visible = models.BooleanField(
        default=True,
        help_text="Control visibility of this event"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Patient Timeline Event'
        verbose_name_plural = 'Patient Timeline Events'
        indexes = [
            models.Index(fields=['patient_profile', '-created_at']),
            models.Index(fields=['event_type']),
        ]
    
    def __str__(self):
        return f"{self.patient_profile.full_name} - {self.get_event_type_display()} ({self.created_at.strftime('%B %d, %Y')})"
    
    @property
    def formatted_date(self):
        """Return formatted date like 'October 30, 2025'"""
        return self.created_at.strftime('%B %d, %Y')
    
    @property
    def is_future(self):
        """Check if this is a future/pending event"""
        return self.created_at > timezone.now()
