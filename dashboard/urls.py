from django.urls import path
from . import views
urlpatterns = [

    path('', views.home, name='home'),
      path('dashboard/<str:file_path>/', views.dashboard, name='dashboard'),
      path('send-pdf/', views.send_pdf_report, name='send_pdf_report'),
]
