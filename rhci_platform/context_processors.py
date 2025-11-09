from django.apps import apps
from django.contrib.auth.models import User
from django.db import models, connection
from django.db.models import Sum, Count, Q
from decimal import Decimal

def admin_metrics(request):
    """Add metrics to admin template context."""
    if not request.path.startswith('/admin/'):
        return {}
    
    context = {}
    
    try:
        # Beneficiaries (patients)
        Patient = apps.get_model('beneficiaries', 'Patient')
        context['beneficiaries_count'] = Patient.objects.count()
        
        # Active cases
        PatientCase = apps.get_model('beneficiaries', 'PatientCase') 
        context['active_cases_count'] = PatientCase.objects.filter(status='published').count()
        
        # Completed cases
        context['completed_cases_count'] = PatientCase.objects.filter(status='completed').count()
        
        # Donors - Fix for database compatibility
        try:
            # Check if your User model has a donor field or method
            if hasattr(User, 'is_donor'):
                context['donors_count'] = User.objects.filter(is_donor=True).count()
            else:
                # Fallback approach
                context['donors_count'] = User.objects.count()  # Or another appropriate value
        except Exception:
            context['donors_count'] = 0
        
        # Payments
        Donation = apps.get_model('donations', 'Donation')
        payment_total = Donation.objects.filter(status='succeeded').aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        context['payments_amount'] = "{:,.0f}".format(payment_total)
        
        # Referrals - adjust model name if needed
        try:
            Referral = apps.get_model('referrals', 'Referral')
            context['referrals_count'] = Referral.objects.count()
        except LookupError:
            context['referrals_count'] = 0
            
    except (LookupError, ImportError, Exception) as e:
        # Models not yet available or other error
        import traceback
        print(f"Error in admin_metrics: {e}")
        traceback.print_exc()
        
    return context

def admin_dashboard_metrics(request):
    """Add dashboard metrics to all admin templates"""
    if not request.path.startswith('/admin/') or not request.user.is_authenticated or not request.user.is_staff:
        return {}
    
    context = {}
    
    # DONORS: Count all non-admin users
    try:
        admin_users = User.objects.filter(Q(is_staff=True) | Q(is_superuser=True)).count()
        total_users = User.objects.count()
        context['donor_count'] = total_users - admin_users
    except Exception:
        context['donor_count'] = 0
    
    # BENEFICIARIES: Count all patients
    try:
        from apps.beneficiaries.models import Patient
        context['beneficiaries_count'] = Patient.objects.count()
    except Exception:
        context['beneficiaries_count'] = 0
    
    # ACTIVE CASES: Count cases that are published or pending
    try:
        from apps.beneficiaries.models import PatientCase
        context['active_cases'] = PatientCase.objects.filter(
            status__in=['published', 'pending']
        ).count()
    except Exception:
        context['active_cases'] = 0
    
    # REFERRALS: Placeholder
    context['referrals_count'] = 0
    
    # PENDING DONATIONS: Count donations with Initiated status
    try:
        from apps.donations.models import Donation
        context['pending_donations'] = Donation.objects.filter(
            status='Initiated'
        ).count()
    except Exception:
        context['pending_donations'] = 0
    
    # TOTAL DONATIONS: Sum of all successful donations
    try:
        from apps.donations.models import Donation
        donation_sum = Donation.objects.filter(
            status='Succeeded'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        context['donation_total'] = f"{donation_sum:,.0f} TZS"
    except Exception:
        context['donation_total'] = "0 TZS"
    
    # Recent patients and donations - skip for context processor to keep it light
    
    return context