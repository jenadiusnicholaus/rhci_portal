from django.urls import path
from . import views

urlpatterns = [
    path('patients/<int:patient_id>/', views.patient_detail, name='patient_detail'),
    path('cases/<int:case_id>/', views.case_detail, name='case_detail'),
]