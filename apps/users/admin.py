from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Profile

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Donor Profile'
    
    # Update fields list (remove phone reference)
    fields = ('is_donor', 'donor_type', 'organization_name', 'country', 
              'city', 'address', 'payment_preference')

# Extend the User admin
class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_donor_type')
    
    def get_donor_type(self, obj):
        try:
            return obj.profile.donor_type
        except Profile.DoesNotExist:
            return '-'
    get_donor_type.short_description = 'Donor Type'

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'donor_type', 'organization_name', 'country')
    list_filter = ('donor_type', 'country')
    search_fields = ('user__email', 'organization_name')
