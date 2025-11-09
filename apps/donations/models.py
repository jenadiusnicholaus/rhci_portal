from decimal import Decimal
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
import uuid

User = get_user_model()

class Donation(models.Model):
    PAYMENT_STATUS = [
        ('initiated', 'Initiated'),
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded')
    ]

    PAYMENT_CHANNELS = [
        ('mno', 'Mobile Money'),
        ('bank', 'Bank Transfer'),
        ('card', 'Card Payment')
    ]

    PROVIDER_CHOICES = [
        # Mobile Money
        ('Airtel', 'Airtel Money'),
        ('Tigo', 'Tigo Pesa'),
        ('Halopesa', 'Halopesa'),
        ('Azampesa', 'Azampesa'),
        ('Mpesa', 'M-Pesa'),
        # Banks
        ('CRDB', 'CRDB Bank'),
        ('NMB', 'NMB Bank'),
    ]

    # Core donation fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey('beneficiaries.PatientCase', on_delete=models.PROTECT, related_name='donations')
    donor = models.ForeignKey(User, on_delete=models.PROTECT, related_name='donations')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='TZS')
    is_anonymous = models.BooleanField(default=False)
    message = models.TextField(blank=True, null=True)

    # Payment details
    payment_channel = models.CharField(max_length=20, choices=PAYMENT_CHANNELS, default='mno')
    payment_provider = models.CharField(max_length=50, choices=PROVIDER_CHOICES, default='Mpesa')
    account_number = models.CharField(max_length=100, null=True, blank=True)
    otp = models.CharField(max_length=50, null=True, blank=True)
    merchant_name = models.CharField(max_length=100, null=True, blank=True)
    
    # AzamPay integration fields
    external_id = models.CharField(max_length=128, unique=True, blank=True)
    azampay_transaction_id = models.CharField(max_length=128, null=True, blank=True)
    payment_vendor_id = models.UUIDField(null=True, blank=True)
    payment_partner_id = models.UUIDField(null=True, blank=True)
    vendor_name = models.CharField(max_length=100, null=True, blank=True)
    fsp_reference_id = models.CharField(max_length=128, null=True, blank=True)
    payment_data = models.JSONField(default=dict, blank=True)
    callback_data = models.JSONField(default=dict, blank=True)
    
    # Status tracking
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='initiated')
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['external_id']),
            models.Index(fields=['azampay_transaction_id']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Donation {self.id} - {self.amount} {self.currency} via {self.payment_provider}"

    def save(self, *args, **kwargs):
        if not self.external_id:
            self.external_id = f"don_{uuid.uuid4().hex[:20]}"
        
        if self.status == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()
            self.case.increment_amount_raised(self.amount)
            
        super().save(*args, **kwargs)

        if self.status == 'completed':
            Receipt.objects.get_or_create(
                donation=self,
                defaults={
                    'receipt_number': f"RCP{self.created_at.strftime('%Y%m%d')}{str(self.id)[:8]}",
                    'amount': self.amount,
                    'currency': self.currency
                }
            )

    def get_azampay_payload(self):
        """Generate AzamPay API payload based on payment channel"""
        additional_properties = {
            'patient_name': self.case.patient.get_full_name(),
            'donor_name': self.donor.get_full_name() if not self.is_anonymous else 'Anonymous'
        }

        if self.payment_channel == 'mno':
            return {
                'accountNumber': self.account_number,
                'additionalProperties': additional_properties,
                'amount': float(self.amount),
                'currency': self.currency,
                'externalId': self.external_id,
                'provider': self.payment_provider
            }
        elif self.payment_channel == 'bank':
            return {
                'additionalProperties': additional_properties,
                'amount': float(self.amount),
                'currencyCode': self.currency,
                'merchantAccountNumber': settings.AZAMPAY_MERCHANT_ACCOUNT,
                'merchantMobileNumber': settings.AZAMPAY_MERCHANT_PHONE,
                'merchantName': settings.AZAMPAY_MERCHANT_NAME,
                'otp': self.otp,
                'provider': self.payment_provider,
                'referenceId': self.external_id
            }
        return {}

class Receipt(models.Model):
    donation = models.OneToOneField(Donation, on_delete=models.PROTECT, related_name='receipt')
    receipt_number = models.CharField(max_length=50, unique=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3)
    generated_at = models.DateTimeField(auto_now_add=True)  # Fixed: removed default
    pdf_file = models.FileField(upload_to='receipts/', null=True, blank=True)

    class Meta:
        ordering = ['-generated_at']

    def __str__(self):
        return f"Receipt {self.receipt_number} for {self.donation}"

class PaymentCallback(models.Model):
    donation = models.ForeignKey(Donation, on_delete=models.PROTECT, related_name='callbacks')
    msisdn = models.CharField(max_length=100, null=True)
    amount = models.CharField(max_length=20)
    message = models.TextField()
    utility_ref = models.CharField(max_length=128)
    operator = models.CharField(max_length=50)
    reference = models.CharField(max_length=128)
    transaction_status = models.CharField(max_length=20)
    submerchant_acc = models.CharField(max_length=100, null=True)
    fsp_reference_id = models.CharField(max_length=128, null=True)
    raw_payload = models.JSONField()
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-received_at']
        indexes = [
            models.Index(fields=['utility_ref']),
            models.Index(fields=['reference']),
            models.Index(fields=['fsp_reference_id']),
        ]

    def __str__(self):
        return f"Callback for {self.donation} - {self.transaction_status}"

    def save(self, *args, **kwargs):
        if self.donation and self.transaction_status:
            if self.transaction_status.lower() == 'success':
                self.donation.status = 'completed'
            elif self.transaction_status.lower() == 'failed':
                self.donation.status = 'failed'
            self.donation.save()
        super().save(*args, **kwargs)