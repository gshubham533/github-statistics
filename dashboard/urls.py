from django.urls import path
from . import views

urlpatterns = [
    path('', views.index_view, name='index'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('api-key/', views.add_api_key_view, name='add_api_key'),
    path('repository/<str:owner>/<str:repo>/', views.repository_insights_view, name='repository_insights'),
] 