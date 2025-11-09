import uuid
from decimal import Decimal
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Patient(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    dob = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    city = models.CharField(max_length=100)
    region = models.CharField(max_length=100)
    guardian_name = models.CharField(max_length=100, blank=True, null=True)
    guardian_contact = models.CharField(max_length=50, blank=True, null=True)
    photo = models.ImageField(upload_to='patients/photos/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class PatientCase(models.Model):
    # No need to explicitly define id field - Django will create an AutoField
    patient = models.ForeignKey('Patient', on_delete=models.PROTECT)
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('published', 'Published'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('archived', 'Archived'),
    ]
    title = models.CharField(max_length=200)
    story = models.TextField()
    diagnosis = models.CharField(max_length=200)
    hospital_name = models.CharField(max_length=200)
    doctor_name = models.CharField(max_length=200)
    target_amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10, default='TZS')
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    case_image = models.ImageField(upload_to='cases/images/', blank=True, null=True)
    photo = models.ImageField(upload_to='cases/photos/', null=True, blank=True)
    published_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    amount_raised = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.patient}'s case - {self.diagnosis}"

    @property
    def percent_raised(self):
        if self.target_amount > 0:
            return int((self.amount_raised / self.target_amount) * 100)
        return 0

    @property
    def progress_offset(self):
        # 389.56 is the circumference for r=62
        if hasattr(self, 'percent_raised'):
            return 389.56 - (self.percent_raised or 0) * 3.8956
        return 389.56

    def increment_amount_raised(self, amount):
        amt = Decimal(str(amount))
        self.amount_raised = (self.amount_raised or Decimal('0')) + amt
        self.save(update_fields=['amount_raised'])

class TreatmentStep(models.Model):
    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('delayed', 'Delayed'),
    ]
    case = models.ForeignKey(PatientCase, on_delete=models.CASCADE, related_name='treatment_steps')
    title = models.CharField(max_length=200)
    description = models.TextField()
    planned_date = models.DateField()
    actual_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    order_index = models.PositiveIntegerField()

    class Meta:
        ordering = ['order_index']

    def __str__(self):
        return self.title

class BudgetItem(models.Model):
    CATEGORY_CHOICES = [
        ('hospital_fees', 'Hospital Fees'),
        ('medical_staff', 'Medical Staff'),
        ('medication', 'Medication'),
        ('supplies', 'Supplies'),
        ('transport', 'Transport'),
    ]
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='budget_items', null=True, blank=True)
    case = models.ForeignKey(PatientCase, on_delete=models.CASCADE, related_name='budget_items', null=True, blank=True)
    cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    expected_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.get_category_display()} ({self.case})"

class MedicalRecord(models.Model):
    RECORD_TYPE_CHOICES = [
        ('doctor_letter', 'Doctor Letter'),
        ('lab_result', 'Lab Result'),
        ('id', 'ID'),
    ]
    case = models.ForeignKey(PatientCase, on_delete=models.CASCADE, related_name='medical_records')
    record_type = models.CharField(max_length=20, choices=RECORD_TYPE_CHOICES)
    file = models.FileField(upload_to='medical_records/')
    notes = models.TextField(blank=True, null=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.record_type} - {self.case.title}"

# Example usage in your view
# budget_items = BudgetItem.objects.filter(case=selected_case, patient=selected_patient)
