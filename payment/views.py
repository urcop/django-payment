import json

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from yookassa.domain.notification import WebhookNotificationEventType as event_type, WebhookNotification

from core import settings
from .forms import PaymentForm
from .models import Payment
from .services.process_payment import process_payment_yookassa
from .utils.robokassa.help_scripts import generate_payment_link


def payment_view(request):
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            payment_method = form.cleaned_data['payment_method']
            amount = form.cleaned_data['amount']
            payment_model = Payment.objects.create(
                    payment_method=payment_method,
                    customer_email=email,
                    amount=amount,
                    status="pending"
                )
            payment_model.save()

            if payment_method == 'yookassa':
                return_url = request.build_absolute_uri(
                    'http://localhost:8000/payment/result/' + str(payment_model.id))
                description = f"Оплата от пользователя {email}"
                redirect_url, _ = process_payment_yookassa(amount, description, return_url, payment_model)

                if redirect_url:
                    return redirect(redirect_url)

            elif payment_method == "robokassa":

                return redirect(redirect_url)


    else:
        form = PaymentForm()

    return render(request, 'payment.html', {'form': form})


def payment_result(request, payment_id):
    payment = Payment.objects.get(id=payment_id)
    return render(request, 'payment_result.html', {'payment': payment})


@csrf_exempt
def yookassa_webhook(request):
    try:
        event_json = json.loads(request.body)
        notification_object = WebhookNotification(event_json)

        if notification_object.event in [event_type.PAYMENT_SUCCEEDED,
                                         event_type.PAYMENT_CANCELED,
                                         event_type.PAYMENT_WAITING_FOR_CAPTURE]:

            payment_id = notification_object.object.id
            payment_status = notification_object.object.status

            try:
                payment = Payment.objects.get(kassa_id=payment_id)
                payment.status = payment_status
                payment.save()
            except Exception as e:
                return HttpResponse(f"Payment with ID {payment_id} not found", status=404)

            return JsonResponse({"message": "Payment status updated successfully"}, status=200)

        else:
            return JsonResponse({"message": "Unknown event"}, status=400)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)