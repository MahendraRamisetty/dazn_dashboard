from django.urls import path, re_path
from . import views

# urlpatterns = [
#     path('', views.home, name='home'),  # Home page for file upload
#     re_path(r'^dashboardData/(?P<file_path>.+)/$', views.dashboard, name='dashboard'),  # Dashboard view
# ]

urlpatterns = [
    path('', views.home, name='home'),  # Home page
    path('dashboard/<path:file_path>/', views.dashboard, name='dashboard'),  # ✅ FIXED: Consistent URL pattern
]
