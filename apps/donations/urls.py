from django.urls import path
from . import views

app_name = 'donations'

urlpatterns = [
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('donate/<int:case_id>/', views.make_donation, name='make_donation'),
    path('providers/', views.get_payment_providers, name='providers'),
    path('initiate/', views.initiate_payment, name='initiate'),
    path('callback/', views.payment_callback, name='callback'),
    path('status/', views.payment_status, name='status'),
    path('success/', views.payment_success, name='success'),
    path('patients/', views.PatientListView.as_view(), name='patients'),
    path('reports/', views.ReportsView.as_view(), name='reports'),
    path('treatment-plans/', views.TreatmentPlansView.as_view(), name='treatment_plans'),
    path('settings/', views.SettingsView.as_view(), name='settings'),
    path('donations/', views.DonationListView.as_view(), name='donations'),
    path('discover/', views.DiscoveryView.as_view(), name='discover'),  # Added this line
    path('payments/', views.PaymentsView.as_view(), name='payments'),
    path('notifications/', views.NotificationsView.as_view(), name='notifications'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
]