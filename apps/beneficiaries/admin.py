from django.contrib import admin
from .models import Patient, PatientCase, TreatmentStep, BudgetItem, MedicalRecord

class PatientCaseInline(admin.TabularInline):
    model = PatientCase
    extra = 0

class BudgetItemInline(admin.TabularInline):
    model = BudgetItem
    extra = 0

class TreatmentStepInline(admin.TabularInline):
    model = TreatmentStep
    extra = 0

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_name', 'last_name', 'dob', 'gender', 'city', 'region', 'created_at')
    search_fields = ('first_name', 'last_name', 'city', 'region')
    inlines = [PatientCaseInline]

@admin.register(PatientCase)
class PatientCaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'title', 'diagnosis', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('title', 'diagnosis')
    inlines = [TreatmentStepInline, BudgetItemInline]

@admin.register(TreatmentStep)
class TreatmentStepAdmin(admin.ModelAdmin):
    list_display = ('id', 'case', 'title', 'status', 'planned_date', 'actual_date', 'order_index')
    list_filter = ('status',)
    search_fields = ('title',)

@admin.register(BudgetItem)
class BudgetItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'category', 'patient', 'case', 'cost', 'expected_date')  # Remove 'diagnostics'

@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'case', 'record_type', 'uploaded_by', 'created_at')
    list_filter = ('record_type',)
    search_fields = ('case__title',)
