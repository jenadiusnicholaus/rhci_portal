from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    DONOR_TYPE_CHOICES = [
        ('Individual', 'Individual'),
        ('Company CSR', 'Company CSR'),
        ('NGO', 'NGO'),
    ]
    
    PAYMENT_PREFERENCE_CHOICES = [
        ('One-time', 'One-time Donation'),
        ('Periodic', 'Periodic Support'),
        ('Not sure', 'Not Sure Yet'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    is_donor = models.BooleanField(default=False)
    donor_type = models.CharField(max_length=20, choices=DONOR_TYPE_CHOICES, null=True, blank=True)
    
    organization_name = models.CharField(max_length=255, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    payment_preference = models.CharField(max_length=20, choices=PAYMENT_PREFERENCE_CHOICES, null=True, blank=True)
    
    def __str__(self):
        return f"Profile for {self.user.email}"
