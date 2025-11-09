from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout
from django.urls import reverse
from apps.beneficiaries.models import PatientCase

# Defensive imports to support different model names / missing apps
try:
    from apps.beneficiaries.models import PatientCase as CaseModel
except Exception:
    try:
        from apps.beneficiaries.models import Case as CaseModel
    except Exception:
        CaseModel = None

try:
    from apps.beneficiaries.models import Patient as PatientModel
except Exception:
    PatientModel = None

def home(request):
    """Home view showing featured patient cases"""
    cases = PatientCase.objects.select_related('patient').filter(
        status='published'  # Assuming 'published' is a valid status
    ).order_by('-created_at')[:8]
    
    context = {
        'cases': cases,
        'featured_categories': [
            'Neural Tube Defects',
            'Gastrointestinal Anomalies',
            'Cardiac Defects',
            'Urogenital Anomalies',
            'Orthopedic Defects',
            'Other Issues'
        ]
    }
    return render(request, 'core/home.html', context)

def patient_detail(request, id):  # Changed to match URL parameter name
    """
    Patient detail view - resolve patient and related cases defensively.
    """
    case = get_object_or_404(PatientCase, id=id)

    # Calculate budget category sums
    category_sums = {}
    for item in case.budget_items.all():
        if item.category in category_sums:
            category_sums[item.category] += item.amount
        else:
            category_sums[item.category] = item.amount

    context = {
        'patient': case.patient,  # Add patient object
        'case': case,  # Single case
        'cases': [case],  # List of cases for legacy template support
        'treatment_steps': case.treatment_steps.all().order_by('planned_date'),
        'budget_items': case.budget_items.all(),
        'category_sums': category_sums,
        'distinct_categories': case.budget_items.values_list('category', flat=True).distinct(),
        'medical_records': case.medical_records.all() if request.user.is_authenticated else None,
    }
    return render(request, 'core/patient_detail.html', context)

def about(request):
    return render(request, 'core/about.html')

def howitworks(request):
    return render(request, 'core/howitworks.html')

def terms(request):
    return render(request, 'core/terms.html')

def privacy(request):
    return render(request, 'core/privacy.html')

def login_view(request):
    """Simple wrapper if you need a local login view (can be replaced by auth views)"""
    return render(request, 'users/login.html')

def signup_view(request):
    return render(request, 'users/signup.html')

def logout_view(request):
    auth_logout(request)
    return redirect('core:home')
def discover(request):
    """
    Defensive discover view: avoids unsupported lookups and shows recent cases.
    """
    cases = []
    if CaseModel is not None:
        qs = CaseModel.objects.all()
        field_names = [f.name for f in CaseModel._meta.get_fields() if hasattr(f, 'name')]

        # Prefer a published/visible filter when available
        if 'status' in field_names:
            try:
                qs = qs.filter(status='published')
            except Exception:
                qs = qs
        elif 'is_published' in field_names:
            qs = qs.filter(is_published=True)
        elif 'published' in field_names:
            qs = qs.filter(published=True)

        # Don't attempt lookups on related objects (avoids ManyToOneRel lookups)
        # Limit and order for display
        try:
            cases = qs.order_by('-id')[:50]
        except Exception:
            cases = list(qs[:50])

    return render(request, 'core/discover.html', {'cases': cases})
def donor_dashboard(request):
    """Simple donor dashboard view"""
    return render(request, 'donations/dashboard.html', {})

def make_donation(request, case_id):
    """
    Handle donation initiation for a specific case.
    Supports both authenticated and anonymous users.
    """
    case = get_object_or_404(PatientCase, id=case_id)
    
    # Get preset amounts based on remaining amount needed
    remaining = case.total_amount - case.amount_raised
    preset_amounts = [
        min(amount, remaining) 
        for amount in [10, 50, 100, 500] 
        if amount <= remaining
    ]

    # Add user context if authenticated
    user_context = {}
    if request.user.is_authenticated:
        user_context = {
            'default_currency': getattr(request.user.profile, 'default_currency', 'TZS'),
            'default_payment_method': getattr(request.user.profile, 'default_payment_method', 'mno'),
            'email': request.user.email,
            'phone': getattr(request.user.profile, 'phone', ''),
        }

    context = {
        'case': case,
        'preset_amounts': preset_amounts,
        'payment_methods': [
            {
                'id': 'mno',
                'name': 'Mobile Money',
                'description': 'Pay using M-Pesa, Airtel Money, or Tigo Pesa',
                'icon': 'mobile-alt'
            },
            {
                'id': 'bank',
                'name': 'Bank Transfer',
                'description': 'Pay using CRDB or NMB Bank',
                'icon': 'university'
            },
            {
                'id': 'card',
                'name': 'Card Payment',
                'description': 'Coming soon - Pay with Visa or Mastercard',
                'icon': 'credit-card',
                'disabled': True
            },
            {
                'id': 'crypto',
                'name': 'Bitcoin',
                'description': 'Coming soon - Pay with cryptocurrency',
                'icon': 'bitcoin',
                'disabled': True
            }
        ],
        'currencies': [
            {'code': 'TZS', 'name': 'Tanzanian Shilling'},
            {'code': 'USD', 'name': 'US Dollar'}
        ],
        'remaining_amount': remaining,
        'success_url': request.build_absolute_uri(
            reverse('donations:success')
        ),
        'cancel_url': request.build_absolute_uri(
            reverse('donations:dashboard') if request.user.is_authenticated 
            else reverse('core:home')
        ),
        'is_authenticated': request.user.is_authenticated,
        'login_url': f"{reverse('login')}?next={request.path}",
        **user_context
    }
    
    return render(request, 'donations/donate.html', context)