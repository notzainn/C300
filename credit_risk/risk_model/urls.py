from django.urls import path
from . import views

# urlpatterns = [
#     path('', views.main_page, name='main_page'), 
#     path('predict/', views.predict_risk, name='predict_risk'), 
#     path('dummy/', views.dummy_view, name='dummy'), 
# ]

urlpatterns = [
    path('', views.main_page, name='main_page'),  # Main page (form)
    path('predict/', views.predict_risk, name='predict_risk'),  # Prediction logic
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('companies/', views.companies_api, name='companies_api'),
    path('admin_login/', views.admin_login, name='admin_login'),  # Admin login
]