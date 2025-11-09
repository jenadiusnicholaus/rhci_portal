from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('patient/<int:id>/', views.patient_detail, name='patient_detail'),
    path('about/', views.about, name='about'),
    path('how-it-works/', views.howitworks, name='howitworks'),
    path('terms/', views.terms, name='terms'),
    path('privacy/', views.privacy, name='privacy'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('discover/', views.discover, name='discover'),
    path('dashboard/', views.donor_dashboard, name='donor_dashboard'),
    #path('donate/<uuid:case_id>/', views.make_donation, name='make_donation'),
]