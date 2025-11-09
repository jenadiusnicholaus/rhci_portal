from django.contrib.admin.views.decorators import staff_member_required
from django.template.response import TemplateResponse
from django.contrib.auth.models import User
from django.db.models import Sum, Count, Q
from django.utils import timezone
from apps.beneficiaries.models import Patient, PatientCase
from apps.users.models import Profile
from apps.donations.models import Donation
from decimal import Decimal

@staff_member_required
def custom_admin_index(request, extra_context=None):
    """Custom admin index view with dashboard metrics"""
    
    # DONORS: Count all non-admin users
    donor_count = User.objects.filter(is_staff=False, is_superuser=False).count()
    
    # BENEFICIARIES: Count all patients
    beneficiaries_count = Patient.objects.count()
    
    # ACTIVE CASES: Count cases that are published or pending
    active_cases = PatientCase.objects.filter(
        status__in=['published', 'pending']
    ).count()
    
    # REFERRALS: Placeholder (replace with actual logic if available)
    referrals_count = 0
    
    # PENDING DONATIONS: Count donations with Initiated status
    pending_donations = Donation.objects.filter(
        status='Initiated'
    ).count()
    
    # TOTAL DONATIONS: Sum of all successful donations
    donation_sum = Donation.objects.filter(
        status='Succeeded'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    # Format the donation total (matching the template variable name)
    donation_total = f"{donation_sum:,.0f} {Donation.objects.first().currency if Donation.objects.exists() else 'TZS'}"
    
    # Recent patients for activity section
    recent_patients = Patient.objects.order_by('-created_at')[:5]
    
    # Recent donations for activity section
    recent_donations = Donation.objects.order_by('-created_at')[:5]

    # Create context with metrics
    context = {
        'donor_count': donor_count,
        'beneficiaries_count': beneficiaries_count,
        'active_cases': active_cases,
        'referrals_count': referrals_count,
        'pending_donations': pending_donations,
        'donation_total': donation_total,  # Match this name with the template
        'recent_patients': recent_patients,
        'recent_donations': recent_donations,
        # Add Django's default admin context
        'title': 'Dashboard',
        'app_list': [], # Empty list to prevent duplicate app list
    }
    
    # Add any extra context
    if extra_context:
        context.update(extra_context)
    
    return TemplateResponse(request, 'admin/index.html', context)