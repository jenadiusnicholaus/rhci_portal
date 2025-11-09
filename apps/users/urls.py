from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'users'  # This sets the namespace to 'users'

urlpatterns = [
    path('', views.donor_signup, name='signup'),  # will serve /signup/ when included

    # Authentication
    path('login/', views.user_login, name='login'),
    path('signup/', views.donor_signup, name='signup'),
    path('logout/', views.user_logout, name='logout'),
    
    # Profile management
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    # Password reset URLs
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='users/password_reset.html',
             email_template_name='users/password_reset_email.html',
             subject_template_name='users/password_reset_subject.txt'
         ), 
         name='password_reset'),
    
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='users/password_reset_done.html'
         ), 
         name='password_reset_done'),
    
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='users/password_reset_confirm.html'
         ), 
         name='password_reset_confirm'),
    
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='users/password_reset_complete.html'
         ), 
         name='password_reset_complete'),
]