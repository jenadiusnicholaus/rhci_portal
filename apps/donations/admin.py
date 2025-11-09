from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Donation, Receipt, PaymentCallback

@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = [
        'external_id', 
        'donor_name_display',
        'patient_link',
        'amount', 
        'payment_channel',
        'status',
        'created_at'
    ]
    
    list_filter = [
        'status',
        'payment_channel',
        'created_at',
        'currency'
    ]
    
    search_fields = [
        'external_id',
        'donor__email',
        'donor__first_name',
        'donor__last_name',
        'case__patient__first_name',
        'case__patient__last_name',
        'azampay_transaction_id'
    ]
    
    readonly_fields = [
        'external_id',
        'created_at',
        'updated_at',
        'azampay_transaction_id'
    ]
    
    fieldsets = [
        ('Donation Info', {
            'fields': (
                'external_id',
                'donor',
                'case',
                ('amount', 'currency'),
                'status'
            )
        }),
        ('Payment Details', {
            'fields': (
                'payment_channel',
                'payment_provider',
                'azampay_transaction_id'
            )
        }),
        ('Timing', {
            'fields': (
                'created_at',
                'updated_at'
            )
        })
    ]
    
    def donor_name_display(self, obj):
        if obj.donor:
            return f"{obj.donor.first_name} {obj.donor.last_name}"
        return "Anonymous"
    donor_name_display.short_description = "Donor"
    
    def patient_link(self, obj):
        if obj.case and obj.case.patient:
            url = reverse('admin:beneficiaries_patient_change', args=[obj.case.patient.id])
            return format_html('<a href="{}">{} {}</a>', 
                             url, 
                             obj.case.patient.first_name,
                             obj.case.patient.last_name)
        return "-"
    patient_link.short_description = "Patient"
    
    def has_add_permission(self, request):
        # Donations should only be created through the donation flow
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of donations for audit purposes
        return False
    
    class Media:
        css = {
            'all': ('css/admin/donation.css',)
        }
        js = ('js/admin/donation.js',)

@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ['receipt_number', 'donation_link', 'amount', 'currency', 'generated_at']
    search_fields = ['receipt_number', 'donation__external_id']
    readonly_fields = ['receipt_number', 'generated_at', 'donation', 'amount', 'currency']
    
    def donation_link(self, obj):
        if obj.donation:
            url = reverse('admin:donations_donation_change', args=[obj.donation.id])
            return format_html('<a href="{}">{}</a>', url, obj.donation.external_id)
        return "-"
    donation_link.short_description = "Donation"

@admin.register(PaymentCallback)
class PaymentCallbackAdmin(admin.ModelAdmin):
    list_display = [
        'donation',
        'transaction_status',
        'amount',
        'operator',
        'received_at'
    ]
    list_filter = ['transaction_status', 'operator', 'received_at']
    search_fields = [
        'donation__external_id',
        'msisdn',
        'utility_ref',
        'reference',
        'fsp_reference_id'
    ]
    readonly_fields = [
        'donation',
        'msisdn',
        'amount',
        'message',
        'utility_ref',
        'operator',
        'reference',
        'transaction_status',
        'submerchant_acc',
        'fsp_reference_id',
        'raw_payload',
        'received_at'
    ]