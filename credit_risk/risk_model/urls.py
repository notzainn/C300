from django.urls import path
from . import views

urlpatterns = [
    path('prediction/', views.predict_risk, name='show_prediction'),
    path('dummy/', views.dummy_view, name='dummy'),
    path('', views.main_page, name='main_page'),
    path('predict/', views.predict_risk, name='predict_risk'),
]
