import json
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from decimal import Decimal
from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.db.models import Sum, Avg, Count
from django.utils import timezone
from datetime import timedelta, datetime
from .models import Donation, PaymentCallback
from apps.beneficiaries.models import PatientCase
# Add to existing imports at the top
from django.contrib import messages
from django.urls import reverse_lazy


logger = logging.getLogger(__name__)

def get_azampay_token():
    """Get access token from AzamPay with proper error handling"""
    
    # Try getting cached token first
    cached_token = cache.get('azampay_token')
    if cached_token:
        return cached_token

    try:
        url = f"{settings.AZAMPAY_AUTH_BASE}/AppRegistration/GenerateToken"
        
        payload = {
            "appName": settings.AZAMPAY_APP_NAME,
            "clientId": settings.AZAMPAY_CLIENT_ID,
            "clientSecret": settings.AZAMPAY_CLIENT_SECRET
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        logger.info(f"Requesting AzamPay token for app: {settings.AZAMPAY_APP_NAME}")
        
        response = requests.post(
            url, 
            json=payload,
            headers=headers, 
            timeout=30,
            verify=True
        )
        
        # Log response for debugging
        logger.info(f"AzamPay response status: {response.status_code}")
        logger.info(f"AzamPay response headers: {response.headers}")
        
        try:
            response_data = response.json()
            logger.info(f"AzamPay response data: {json.dumps(response_data)}")
        except json.JSONDecodeError:
            logger.error(f"Non-JSON response: {response.text}")
            raise ValueError("Invalid JSON response from AzamPay")

        # Check for token in response data structure
        if not response_data.get('data', {}).get('accessToken'):
            logger.error(f"No token in response: {response_data}")
            raise ValueError("No token in AzamPay response")

        token = response_data['data']['accessToken']
        
        # Cache the token until 5 minutes before expiry
        expire_str = response_data['data'].get('expire')
        if expire_str:
            try:
                expire = datetime.fromisoformat(expire_str.replace('Z', '+00:00'))
                cache_duration = (expire - timezone.now()).total_seconds() - 300  # 5 minutes buffer
                if cache_duration > 0:
                    cache.set('azampay_token', token, int(cache_duration))
            except Exception as e:
                logger.warning(f"Could not parse token expiry: {e}")
                # Fall back to default cache duration
                cache.set('azampay_token', token, settings.AZAMPAY_TOKEN_CACHE_DURATION)
        else:
            # Use default cache duration if no expiry provided
            cache.set('azampay_token', token, settings.AZAMPAY_TOKEN_CACHE_DURATION)
        
        return token

    except requests.exceptions.RequestException as e:
        logger.error(f"Network error getting AzamPay token: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error getting AzamPay token: {str(e)}")
        raise

class PaymentMethod:
    # Mobile Money Providers
    MPESA = 'mpesa'
    TIGOPESA = 'tigopesa'
    AIRTELMONEY = 'airtelmoney'
    
    # Banks
    CRDB = 'crdb'
    NMB = 'nmb'
    
    # Cards
    VISA = 'visa'
    MASTERCARD = 'mastercard'
    
    CHOICES = [
        (MPESA, 'M-Pesa'),
        (TIGOPESA, 'Tigo Pesa'),
        (AIRTELMONEY, 'Airtel Money'),
        (CRDB, 'CRDB Bank'),
        (NMB, 'NMB Bank'),
        (VISA, 'Visa Card'),
        (MASTERCARD, 'Mastercard'),
    ]
    
    MOBILE_MONEY = [MPESA, TIGOPESA, AIRTELMONEY]
    BANKS = [CRDB, NMB]
    CARDS = [VISA, MASTERCARD]

def make_donation(request, case_id):
    """Enhanced donation view with support for multiple payment methods and RHCI support"""
    case = get_object_or_404(PatientCase, id=case_id)
    
    # Calculate remaining amount needed
    remaining_amount = case.target_amount - case.amount_raised
    
    # Define preset amounts
    preset_amounts = [
        min(amount, remaining_amount) 
        for amount in [10, 50, 100, 500] 
        if amount <= remaining_amount
    ]
    
    # Add remaining amount if not in presets
    if remaining_amount not in preset_amounts:
        preset_amounts.append(remaining_amount)
    
    # Define payment methods with future options
    payment_methods = {
        'current': [
            {
                'id': 'mobile',
                'name': 'Mobile Money',
                'description': 'Pay using M-Pesa, Airtel Money, or Tigo Pesa',
                'icon': 'mobile-alt',
                'providers': [
                    {'id': 'mpesa', 'name': 'M-Pesa'},
                    {'id': 'tigopesa', 'name': 'Tigo Pesa'},
                    {'id': 'airtelmoney', 'name': 'Airtel Money'}
                ]
            },
            {
                'id': 'bank',
                'name': 'Bank Transfer',
                'description': 'Pay using CRDB or NMB Bank',
                'icon': 'university',
                'providers': [
                    {'id': 'crdb', 'name': 'CRDB Bank'},
                    {'id': 'nmb', 'name': 'NMB Bank'}
                ]
            }
        ],
        'coming_soon': [
            {
                'id': 'paypal',
                'name': 'PayPal',
                'description': 'Coming soon - International payments',
                'icon': 'paypal'
            },
            {
                'id': 'bitcoin',
                'name': 'Bitcoin',
                'description': 'Coming soon - Cryptocurrency payments',
                'icon': 'bitcoin'
            }
        ]
    }

    context = {
        'case': case,
        'preset_amounts': preset_amounts,
        'remaining_amount': remaining_amount,
        'payment_methods': payment_methods,
        'currencies': [
            {'code': 'TZS', 'name': 'Tanzanian Shilling', 'symbol': 'TSh'},
            {'code': 'USD', 'name': 'US Dollar', 'symbol': '$'}
        ],
        'rhci_support_percentage': 10,  # 10% support option
        'user_data': {
            'is_authenticated': request.user.is_authenticated,
            'name': f"{request.user.first_name} {request.user.last_name}".strip() if request.user.is_authenticated else '',
            'email': request.user.email if request.user.is_authenticated else '',
            'default_currency': getattr(request.user.profile, 'default_currency', 'TZS') if request.user.is_authenticated else 'TZS',
            'default_payment_method': getattr(request.user.profile, 'default_payment_method', None) if request.user.is_authenticated else None,
        },
        'success_url': request.build_absolute_uri(reverse('donations:success')),
        'cancel_url': request.build_absolute_uri(
            reverse('donations:dashboard') if request.user.is_authenticated 
            else reverse('core:home')
        ),
    }
    
    if request.method == 'POST':
        try:
            # Extract form data
            amount = Decimal(request.POST.get('amount', 0))
            support_amount = Decimal(request.POST.get('support_amount', 0))
            payment_method = request.POST.get('payment_method')
            provider = request.POST.get('provider')
            currency = request.POST.get('currency')
            is_anonymous = request.POST.get('anonymous') == 'on'
            
            # Create donation
            donation = Donation.objects.create(
                case=case,
                donor=None if is_anonymous else request.user,
                amount=amount,
                support_amount=support_amount,
                total_amount=amount + support_amount,
                currency=currency,
                payment_method=payment_method,
                provider=provider,
                is_anonymous=is_anonymous,
                donor_name=request.POST.get('donor_name') if is_anonymous else None,
                donor_email=request.POST.get('donor_email') if is_anonymous else None,
                status='pending'
            )
            
            # Redirect to payment processing
            return redirect('donations:process_payment', donation_id=donation.id)
            
        except Exception as e:
            logger.error(f"Error creating donation: {str(e)}")
            messages.error(request, 'Error processing donation. Please try again.')
            return render(request, 'donations/donate.html', context)
    
    return render(request, 'donations/donate.html', context)

def get_http_session():
    """Create requests session with retry strategy"""
    session = requests.Session()
    retry_strategy = Retry(
        total=3,  # number of retries
        backoff_factor=0.5,  # wait 0.5, 1, 2... seconds between retries
        status_forcelist=[500, 502, 503, 504],  # retry on these status codes
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

@require_http_methods(["GET"])
def get_payment_providers(request):
    """Fetch payment providers from AzamPay with improved error handling"""
    try:
        category = request.GET.get('category')
        if not category:
            return JsonResponse({'success': False, 'error': 'Category required'})

        # Try cache first
        cache_key = f'payment_providers_{category}'
        providers = cache.get(cache_key)
        if providers:
            return JsonResponse({'success': True, 'providers': providers})

        # Get fresh token
        token = get_azampay_token()
        
        # Create session with retry strategy
        session = get_http_session()
        
        url = f"{settings.AZAMPAY_CHECKOUT_BASE}/api/v1/Partner/GetPaymentPartners"
        headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Connection': 'keep-alive'
        }

        logger.info(f"Fetching payment providers for category: {category}")
        logger.debug(f"Request URL: {url}")
        logger.debug(f"Request headers: {headers}")

        response = session.get(
            url, 
            headers=headers, 
            timeout=30,
            verify=True
        )
        
        # Log response details
        logger.info(f"AzamPay providers response status: {response.status_code}")
        logger.debug(f"Response headers: {response.headers}")
        
        try:
            response_data = response.json()
            logger.debug(f"Response data: {json.dumps(response_data)}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response: {response.text[:500]}")
            raise ValueError(f"Invalid JSON response from AzamPay: {str(e)}")

        # Handle empty response
        if not response_data:
            logger.warning("Empty response from AzamPay")
            return JsonResponse({
                'success': False,
                'error': 'No providers available'
            }, status=404)

        # Filter partners
        filtered = []
        for partner in response_data:
            partner_type = str(partner.get('provider', '')).lower()
            if ((category == 'mno' and any(x in partner_type for x in ['mobile', 'mno', 'airtel', 'tigo', 'vodacom'])) or
                (category == 'bank' and any(x in partner_type for x in ['bank', 'crdb', 'nmb']))):
                filtered.append({
                    'id': partner.get('paymentPartnerId'),
                    'name': partner.get('partnerName'),
                    'logo': partner.get('logoUrl') or f'/static/img/{category}.png',  # Fallback image
                    'provider': partner.get('provider'),
                    'vendor_id': partner.get('paymentVendorId'),
                    'currency': partner.get('currency', 'TZS')
                })

        # Cache results
        if filtered:
            cache.set(cache_key, filtered, 3600)

        return JsonResponse({
            'success': True, 
            'providers': filtered
        })

    except requests.exceptions.RequestException as e:
        logger.error(f"Network error fetching payment providers: {str(e)}")
        # Return cached results if available during network error
        cached = cache.get(cache_key)
        if cached:
            return JsonResponse({
                'success': True,
                'providers': cached,
                'from_cache': True
            })
        return JsonResponse({
            'success': False,
            'error': 'Network error. Please try again.'
        }, status=503)
    except Exception as e:
        logger.error(f"Error fetching payment providers: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Could not fetch providers.'
        }, status=500)
    finally:
        if 'session' in locals():
            session.close()

@require_http_methods(["POST"])
def initiate_payment(request):
    """Initiate payment with AzamPay"""
    try:
        data = json.loads(request.body)
        case_id = data.get('case_id')
        amount = Decimal(data.get('amount', 0))
        currency = data.get('currency', 'TZS')
        payment_channel = data.get('payment_channel')
        provider = data.get('provider')
        is_anonymous = data.get('is_anonymous', False)
        support_amount = Decimal(data.get('support_amount', 0))
        
        # Validate required fields
        if not all([case_id, amount, payment_channel, provider]):
            return JsonResponse({
                'success': False,
                'error': 'Missing required fields'
            }, status=400)

        # Get case
        case = get_object_or_404(PatientCase, id=case_id)
        
        # Create donation record
        donation = Donation.objects.create(
            case=case,
            donor=request.user,
            amount=amount + support_amount,
            currency=currency,
            is_anonymous=is_anonymous,
            payment_channel=payment_channel,
            payment_provider=provider,
            account_number=data.get('account_number'),
            otp=data.get('otp'),
            payment_vendor_id=data.get('vendor_id'),
            payment_partner_id=data.get('partner_id'),
            vendor_name=data.get('vendor_name'),
            status='pending'
        )

        # Get AzamPay token
        token = get_azampay_token()
        
        # Prepare checkout URL and payload
        if payment_channel == 'mno':
            url = f"{settings.AZAMPAY_CHECKOUT_BASE}/azampay/mno/checkout"
        else:
            url = f"{settings.AZAMPAY_CHECKOUT_BASE}/azampay/bank/checkout"
            
        payload = donation.get_azampay_payload()
        
        # Call AzamPay checkout API
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        response.raise_for_status()
        result = response.json()

        # Update donation with response
        donation.payment_data = payload
        donation.azampay_transaction_id = result.get('transactionId')
        donation.save()

        return JsonResponse({
            'success': True,
            'message': result.get('message'),
            'transaction_id': result.get('transactionId'),
            'external_id': donation.external_id
        })

    except Exception as e:
        logger.error(f"Error initiating payment: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def payment_callback(request):
    """Handle AzamPay payment callback"""
    try:
        data = json.loads(request.body)
        utility_ref = data.get('utilityref')  # This is our external_id
        
        # Find the donation
        donation = get_object_or_404(Donation, external_id=utility_ref)
        
        # Create callback record
        callback = PaymentCallback.objects.create(
            donation=donation,
            msisdn=data.get('msisdn'),
            amount=data.get('amount'),
            message=data.get('message'),
            utility_ref=utility_ref,
            operator=data.get('operator'),
            reference=data.get('reference'),
            transaction_status=data.get('transactionstatus'),
            submerchant_acc=data.get('submerchantAcc'),
            fsp_reference_id=data.get('fspReferenceId'),
            raw_payload=data
        )

        # Callback model's save method will update donation status
        
        return JsonResponse({'success': True})

    except Exception as e:
        logger.error(f"Error processing payment callback: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def payment_status(request):
    """Check payment status"""
    try:
        external_id = request.GET.get('ref')
        if not external_id:
            return JsonResponse({'success': False, 'error': 'Reference required'})

        donation = get_object_or_404(Donation, external_id=external_id)
        
        return JsonResponse({
            'success': True,
            'status': donation.status,
            'message': donation.error_message or ''
        })

    except Exception as e:
        logger.error(f"Error checking payment status: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def payment_success(request):
    """Display payment success page"""
    try:
        external_id = request.GET.get('ref')
        if not external_id:
            return redirect('donations:dashboard')

        donation = get_object_or_404(Donation, external_id=external_id)
        
        context = {
            'donation': donation,
            'case': donation.case,
            'transaction_id': donation.azampay_transaction_id,
            'amount': donation.amount,
            'currency': donation.currency,
            'payment_method': donation.payment_channel,
            'provider': donation.payment_provider,
            'date': donation.completed_at or donation.created_at,
            'share_url': request.build_absolute_uri(
                reverse('case_detail', args=[donation.case.id])
            )
        }
        
        return render(request, 'donations/success.html', context)

    except Exception as e:
        logger.error(f"Error displaying success page: {str(e)}")
        return redirect('donations:dashboard')

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'donations/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        context.update({
            'total_donated': Donation.objects.filter(
                donor=user,
                status='completed'
            ).aggregate(total=models.Sum('amount'))['total'] or 0,
            
            'patients_count': PatientCase.objects.filter(
                donations__donor=user,
                donations__status='completed'
            ).distinct().count(),
            
            'donations_count': Donation.objects.filter(
                donor=user,
                status='completed'
            ).count(),
            
            'recent_patients': PatientCase.objects.filter(
                donations__donor=user
            ).distinct().order_by('-created_at')[:3],
            
            'recent_donations': Donation.objects.filter(
                donor=user
            ).order_by('-created_at')[:3]
        })
        
        return context

def calculate_impact_score(user):
    """Calculate donor impact score"""
    donations = Donation.objects.filter(donor=user, status='completed')
    total_amount = donations.aggregate(total=models.Sum('amount'))['total'] or 0
    donation_count = donations.count()
    
    # Simple scoring algorithm - can be made more complex
    return int((total_amount / 100) + (donation_count * 10))

class PatientListView(LoginRequiredMixin, ListView):
    template_name = 'donations/patients.html'
    context_object_name = 'patients'
    paginate_by = 10

    def get_queryset(self):
        # Get patients user has donated to
        return PatientCase.objects.filter(
            donations__donor=self.request.user,
            donations__status='completed'
        ).distinct().select_related('patient').annotate(
            total_donated=Sum('donations__amount'),
            donations_count=Count('donations')
        ).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_patients'] = self.get_queryset().count()
        return context

class ReportsView(LoginRequiredMixin, TemplateView):
    template_name = 'donations/reports.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        today = timezone.now()
        thirty_days_ago = today - timedelta(days=30)

        # Monthly statistics
        monthly_donations = Donation.objects.filter(
            donor=user,
            status='completed',
            created_at__gte=thirty_days_ago
        )

        context.update({
            'monthly_total': monthly_donations.aggregate(
                total=Sum('amount')
            )['total'] or 0,
            'monthly_count': monthly_donations.count(),
            'donation_history': self.get_donation_history(user),
            'category_distribution': self.get_category_distribution(user),
            'payment_methods': self.get_payment_methods_stats(user)
        })
        return context

    def get_donation_history(self, user):
        # Get last 12 months of donations
        return Donation.objects.filter(
            donor=user,
            status='completed'
        ).annotate(
            month=models.functions.TruncMonth('created_at')
        ).values('month').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('month')

    def get_category_distribution(self, user):
        return PatientCase.objects.filter(
            donations__donor=user,
            donations__status='completed'
        ).values('diagnosis_category').annotate(
            total=Sum('donations__amount'),
            count=Count('id')
        )

    def get_payment_methods_stats(self, user):
        return Donation.objects.filter(
            donor=user,
            status='completed'
        ).values('payment_channel').annotate(
            total=Sum('amount'),
            count=Count('id')
        )

class TreatmentPlansView(LoginRequiredMixin, ListView):
    template_name = 'donations/treatment_plans.html'
    context_object_name = 'treatment_plans'
    paginate_by = 10

    def get_queryset(self):
        return PatientCase.objects.filter(
            donations__donor=self.request.user,
            donations__status='completed'
        ).distinct().select_related('patient').prefetch_related(
            'treatments'
        ).annotate(
            completion_percentage=models.ExpressionWrapper(
                models.F('amount_raised') * 100.0 / models.F('total_amount'),
                output_field=models.FloatField()
            )
        ).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_plans'] = self.get_queryset().count()
        context['completed_plans'] = self.get_queryset().filter(
            completion_percentage=100
        ).count()
        return context

class SettingsView(LoginRequiredMixin, TemplateView):
    template_name = 'donations/settings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        context.update({
            'notification_settings': {
                'email_notifications': user.profile.email_notifications,
                'sms_notifications': user.profile.sms_notifications,
                'donation_updates': user.profile.donation_updates,
                'patient_updates': user.profile.patient_updates
            },
            'payment_preferences': {
                'default_currency': user.profile.default_currency,
                'default_payment_method': user.profile.default_payment_method
            },
            'privacy_settings': {
                'show_donation_amount': user.profile.show_donation_amount,
                'show_in_leaderboard': user.profile.show_in_leaderboard,
                'allow_patient_contact': user.profile.allow_patient_contact
            },
            'recent_logins': user.loginlog_set.all()[:5] if hasattr(user, 'loginlog_set') else None
        })
        return context

class DonationListView(LoginRequiredMixin, ListView):
    template_name = 'donations/donations.html'
    context_object_name = 'donations'
    paginate_by = 10

    def get_queryset(self):
        return Donation.objects.filter(
            donor=self.request.user
        ).select_related('case__patient').order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Add donation statistics
        donations = self.get_queryset()
        context.update({
            'total_amount': donations.filter(status='completed').aggregate(
                total=Sum('amount')
            )['total'] or 0,
            'average_amount': donations.filter(status='completed').aggregate(
                avg=models.Avg('amount')
            )['avg'] or 0,
            'donation_count': donations.filter(status='completed').count(),
            'monthly_stats': self.get_monthly_stats()
        })
        return context
    
    def get_monthly_stats(self):
        today = timezone.now()
        last_month = today - timedelta(days=30)
        
        return Donation.objects.filter(
            donor=self.request.user,
            created_at__gte=last_month,
            status='completed'
        ).annotate(
            date=models.functions.TruncDay('created_at')
        ).values('date').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('date')
    #adding patient discovery view
class DiscoveryView(LoginRequiredMixin, ListView):
    template_name = 'donations/discovery.html'
    context_object_name = 'patients'
    paginate_by = 10

    def get_queryset(self):
        # Get patients user has not donated to
        donated_case_ids = Donation.objects.filter(
            donor=self.request.user,
            status='completed'
        ).values_list('case_id', flat=True)
        
        return PatientCase.objects.exclude(
            id__in=donated_case_ids
        ).select_related('patient').annotate(
            total_donated=Sum('donations__amount'),
            donations_count=Count('donations')
        ).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_patients'] = self.get_queryset().count()
        return context

class PaymentsView(LoginRequiredMixin, ListView):
    template_name = 'donations/payments.html'
    context_object_name = 'payments'
    paginate_by = 10

    def get_queryset(self):
        status = self.request.GET.get('status')
        search = self.request.GET.get('search')
        
        queryset = Donation.objects.filter(
            donor=self.request.user
        ).select_related(
            'case__patient'
        ).order_by('-created_at')
        
        if status:
            queryset = queryset.filter(status=status)
            
        if search:
            queryset = queryset.filter(
                models.Q(case__patient__first_name__icontains=search) |
                models.Q(case__patient__last_name__icontains=search) |
                models.Q(external_id__icontains=search) |
                models.Q(azampay_transaction_id__icontains=search)
            )
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Payment statistics
        completed_payments = self.get_queryset().filter(status='completed')
        context.update({
            'total_amount': completed_payments.aggregate(
                total=Sum('amount')
            )['total'] or 0,
            'payment_count': completed_payments.count(),
            'payment_methods': self.get_payment_methods_breakdown(),
            'recent_activity': self.get_recent_activity(),
            'filter_status': self.request.GET.get('status', ''),
            'search_query': self.request.GET.get('search', '')
        })
        return context
    
    def get_payment_methods_breakdown(self):
        return Donation.objects.filter(
            donor=self.request.user,
            status='completed'
        ).values('payment_channel', 'payment_provider').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')
    
    def get_recent_activity(self):
        return Donation.objects.filter(
            donor=self.request.user
        ).select_related('case__patient').order_by(
            '-updated_at'
        )[:5]
    #adding notifications view
class NotificationsView(LoginRequiredMixin, TemplateView):
    template_name = 'donations/notifications.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Fetch notifications - safely handle users without a notifications relation or anonymous users
        notifications_manager = getattr(user, 'notifications', None)
        if notifications_manager is not None:
            notifications = notifications_manager.all().order_by('-created_at')[:20]
            # use the manager to count unread notifications efficiently
            try:
                unread_count = notifications_manager.filter(read=False).count()
            except Exception:
                # fallback if filter/count not supported for some custom managers
                unread_count = sum(1 for n in notifications if not getattr(n, 'read', False))
        else:
            notifications = []
            unread_count = 0

        context.update({
            'notifications': notifications,
            'unread_count': unread_count
        })
        return context


# Add this class after other views
class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'donations/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        context.update({
            'user': user,
            'profile': user.profile,
            'donation_stats': {
                'total_donated': Donation.objects.filter(
                    donor=user,
                    status='completed'
                ).aggregate(total=Sum('amount'))['total'] or 0,
                'donation_count': Donation.objects.filter(
                    donor=user,
                    status='completed'
                ).count(),
                'patients_helped': PatientCase.objects.filter(
                    donations__donor=user,
                    donations__status='completed'
                ).distinct().count(),
                'impact_score': calculate_impact_score(user)
            },
            'recent_donations': Donation.objects.filter(
                donor=user
            ).select_related('case__patient').order_by('-created_at')[:5],
            'favorite_payment_methods': self.get_favorite_payment_methods(user)
        })
        return context
    
    def get_favorite_payment_methods(self, user):
        return Donation.objects.filter(
            donor=user,
            status='completed'
        ).values('payment_channel', 'payment_provider').annotate(
            count=Count('id')
        ).order_by('-count')[:3]

    def post(self, request, *args, **kwargs):
        try:
            user = request.user
            profile = user.profile

            # Update user info
            user.first_name = request.POST.get('first_name', user.first_name)
            user.last_name = request.POST.get('last_name', user.last_name)
            user.email = request.POST.get('email', user.email)
            user.save()

            # Update profile info
            profile.phone = request.POST.get('phone', profile.phone)
            profile.address = request.POST.get('address', profile.address)
            profile.bio = request.POST.get('bio', profile.bio)
            profile.default_currency = request.POST.get('currency', profile.default_currency)
            profile.default_payment_method = request.POST.get('payment_method', profile.default_payment_method)
            
            # Handle profile picture upload
            if 'profile_picture' in request.FILES:
                profile.profile_picture = request.FILES['profile_picture']
            
            profile.save()

            messages.success(request, 'Profile updated successfully!')
            return redirect('donations:profile')

        except Exception as e:
            logger.error(f"Error updating profile: {str(e)}")
            messages.error(request, 'Error updating profile. Please try again.')
            return self.get(request, *args, **kwargs)