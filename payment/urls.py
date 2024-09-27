from django.urls import path
from . import views

urlpatterns = [
    path('', views.PaymentView.as_view(), name='payment'),
    path('result/<str:payment_id>/', views.PaymentResultView.as_view(), name='payment_result'),
    path('yookassa/webhook/', views.YookassaWebhookView.as_view(), name='yookassa_webhook'),
    path('robokassa/success/', views.RobokassaSuccessView.as_view(), name='robokassa_success'),
    path('robokassa/failed/', views.RobokassaFailedView.as_view(), name='robokassa_failed'),
]
