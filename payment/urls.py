from django.urls import path
from . import views

urlpatterns = [
    path('', views.payment_view, name='payment'),
    path('result/<str:payment_id>/', views.payment_result, name='payment_result'),
    path('yookassa/webhook/', views.yookassa_webhook, name='yookassa_webhook'),
]
