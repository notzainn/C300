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
    # path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('companies/', views.companies_api, name='companies_api'),
    # path('admin_login/', views.admin_login, name='admin_login'),  # Admin login
    path('save_prediction/', views.save_prediction, name='save_prediction'),
    path("export/pdf/", views.export_to_pdf, name="export_to_pdf"),
    path('api/predictions/', views.predictions_api, name='predictions_api'),  # API for predictions
    path('api/predictions/<int:id>/', views.predictions_api, name='predictions_api'),
    path('new_form/', views.new_form_view, name='new_form_page'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('manage_users/', views.manage_users, name='manage_users'),
    path('toggle_admin/<int:user_id>/', views.toggle_admin, name='toggle_admin'),
    path('delete_user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('user_login/', views.user_login, name='user_login'),  # Add this line
    path('user_logout/', views.user_logout, name='user_logout'),
    path('credit_rating_form/', views.main_page, name='credit_rating_form'),
]