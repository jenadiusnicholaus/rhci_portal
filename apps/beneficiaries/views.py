from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from .models import MedicalRecord, PatientCase, Patient
from collections import defaultdict

class MedicalRecordListView(ListView):
    model = MedicalRecord
    template_name = 'beneficiaries/medicalrecord_list.html'
    context_object_name = 'records'

class MedicalRecordCreateView(CreateView):
    model = MedicalRecord
    fields = ['case', 'record_type', 'file_url', 'notes']
    template_name = 'beneficiaries/medicalrecord_form.html'
    success_url = reverse_lazy('medicalrecord-list')

def home(request):
    cases = PatientCase.objects.filter(status='published')
    print("DEBUG: Published cases count:", cases.count())
    return render(request, 'home.html', {'cases': cases})

@login_required
def patient_detail(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    cases = PatientCase.objects.filter(patient=patient, status='published')
    case = cases.first()  # assuming you want the first case for the patient

    # Get distinct categories and sum per category
    category_sums = {}
    distinct_categories = []
    if case:
        items = case.budget_items.all()
        for item in items:
            if item.category not in category_sums:
                distinct_categories.append(item.category)
                category_sums[item.category] = 0
            category_sums[item.category] += item.cost or 0

    category_display = {
        'hospital_fees': 'Hospital Fees',
        'medical_staff': 'Medical Staff',
        'medication': 'Medication',
        'supplies': 'Supplies',
        'transport': 'Transport',
    }
    category_icons = {
        'hospital_fees': 'fas fa-hospital',
        'medical_staff': 'fas fa-user-md',
        'medication': 'fas fa-pills',
        'supplies': 'fas fa-box',
        'transport': 'fas fa-bus',
    }

    return render(request, 'patient_detail.html', {
        'patient': patient,
        'cases': [case] if case else [],
        'donation_amounts': [10, 28, 56, 150],
        'distinct_categories': distinct_categories,
        'category_sums': category_sums,
        'category_display': category_display,
        'category_icons': category_icons,
    })

@login_required
def case_detail(request, case_id):
    return render(request, 'beneficiaries/case_detail.html', {'case_id': case_id})

@login_required
def donor_discover(request):
    """View for donors to discover new patients to support"""
    # Get patients with active cases that need funding
    patients = Patient.objects.filter(
        cases__status='published',
        cases__is_fully_funded=False
    ).distinct()
    
    # Get any filters applied
    condition_filter = request.GET.get('condition')
    location_filter = request.GET.get('location')
    
    if condition_filter:
        patients = patients.filter(condition__icontains=condition_filter)
    
    if location_filter:
        patients = patients.filter(location__icontains=location_filter)
    
    # Get all available conditions and locations for filter dropdowns
    all_conditions = Patient.objects.values_list('condition', flat=True).distinct()
    all_locations = Patient.objects.values_list('location', flat=True).distinct()
    
    context = {
        'patients': patients,
        'all_conditions': all_conditions,
        'all_locations': all_locations,
        'selected_condition': condition_filter,
        'selected_location': location_filter,
    }
    
    return render(request, 'donor/discover.html', context)

@login_required
def donor_support(request):
    """View for donor support and help resources"""
    faqs = [
        {
            'question': 'How do I know my donation is being used properly?',
            'answer': 'All donations are tracked and allocated directly to the medical cases you choose to support. You will receive regular updates on the patient\'s progress and how funds are being utilized.'
        },
        {
            'question': 'Can I get tax deductions for my donations?',
            'answer': 'Yes, RHCI is a registered non-profit organization and all donations are tax-deductible. You can download tax receipts from your donation history page.'
        },
        {
            'question': 'How do I contact a patient I\'m supporting?',
            'answer': 'To protect patient privacy, direct contact is not possible. However, you can send messages through our platform which will be delivered to the patient by our staff.'
        },
        {
            'question': 'What happens if a patient receives more funding than needed?',
            'answer': 'Any excess funds will be allocated to the patient\'s future medical needs or, with your permission, redirected to other patients in similar situations.'
        },
        {
            'question': 'How can I increase my impact?',
            'answer': 'Consider setting up recurring donations, sharing patient stories with your network, or participating in our fundraising campaigns.'
        }
    ]
    
    support_contacts = {
        'email': 'support@rhci.org',
        'phone': '+255 123 456 789',
        'hours': 'Monday-Friday: 9am-5pm EAT'
    }
    
    return render(request, 'donor/support.html', {
        'faqs': faqs,
        'support_contacts': support_contacts
    })

@login_required
def donor_reports(request):
    """View for donor impact reports and analytics"""
    # In a real app, you'd calculate these metrics from actual donation data
    impact_metrics = {
        'total_donated': '1,250,000 TZS',
        'patients_helped': 5,
        'treatments_funded': 8,
        'success_rate': '92%'
    }
    
    # Sample donation history by month for chart
    donation_history = [
        {'month': 'Jan', 'amount': 150000},
        {'month': 'Feb', 'amount': 200000},
        {'month': 'Mar', 'amount': 175000},
        {'month': 'Apr', 'amount': 300000},
        {'month': 'May', 'amount': 250000},
        {'month': 'Jun', 'amount': 175000},
    ]
    
    # Sample patient outcomes
    patient_outcomes = [
        {
            'name': 'Maria Joseph',
            'condition': 'Malaria complications',
            'outcome': 'Fully recovered',
            'donation_impact': 'Provided medication and hospital stay'
        },
        {
            'name': 'Emmanuel Kwame',
            'condition': 'Broken femur',
            'outcome': 'Successful surgery',
            'donation_impact': 'Funded surgical procedure and physical therapy'
        },
        {
            'name': 'Amina Hassan',
            'condition': 'Pneumonia',
            'outcome': 'Recovering well',
            'donation_impact': 'Provided antibiotics and oxygen therapy'
        }
    ]
    
    return render(request, 'donor/reports.html', {
        'impact_metrics': impact_metrics,
        'donation_history': donation_history,
        'patient_outcomes': patient_outcomes
    })
