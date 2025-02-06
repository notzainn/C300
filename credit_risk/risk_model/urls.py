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
    path('companies/', views.companies_api, name='companies_api'),
    path('save_prediction/', views.save_prediction, name='save_prediction'),
    path("export/pdf/", views.export_to_pdf, name="export_to_pdf"),
    path('api/predictions/', views.predictions_api, name='predictions_api'),
    path('api/predictions/<int:id>/', views.predictions_api, name='predictions_api'),
    path('new_form/', views.new_form_view, name='new_form_page'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('delete_user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('user_login/', views.user_login, name='user_login'),
    path('user_logout/', views.user_logout, name='user_logout'),
    path('credit_rating_form/', views.main_page, name='credit_rating_form'),
    path('manage_users/', views.manage, name='manage_users'),
    path('add_user/', views.add_user, name='add_user'),
    path('delete_user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('mypredictions/', views.mypredictions_view, name='mypredictions'),
    path('mypredictions/update/', views.update_prediction, name='update_prediction'),
    path('mypredictions/delete/', views.delete_prediction, name='delete_prediction'),
    path('edit_user/<int:user_id>/', views.edit_user, name='edit_user'),
    path('generate_pdf/<int:prediction_id>/', views.generate_pdf, name='generate_pdf'),
]