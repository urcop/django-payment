import json
from urllib.parse import parse_qs

from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DetailView
from django.views.generic import FormView
from yookassa.domain.notification import WebhookNotification, WebhookNotificationEventType as event_type
from .forms import PaymentForm
from .models import Payment
from .services.process_payment import process_payment_yookassa
from .utils.robokassa.help_scripts import generate_payment_link


class PaymentView(FormView):
    template_name = 'payment.html'
    form_class = PaymentForm

    def form_valid(self, form):
        email = form.cleaned_data['email']
        payment_method = form.cleaned_data['payment_method']
        amount = form.cleaned_data['amount']

        payment = Payment.objects.create(
            payment_method=payment_method,
            customer_email=email,
            amount=amount,
            status="pending"
        )

        if payment_method == 'yookassa':
            return_url = self.request.build_absolute_uri(reverse("payment_result", args=[payment.id]))
            description = f"Оплата от пользователя {email}"
            redirect_url, _ = process_payment_yookassa(amount, description, return_url, payment)
            if redirect_url:
                return redirect(redirect_url)

        elif payment_method == 'robokassa':
            redirect_url = generate_payment_link(
                settings.ROBOKASSA_LOGIN,
                settings.ROBOKASSA_PASSWORD1,
                amount,
                payment.id,
                f"Оплата от пользователя {email}",
                settings.ROBOKASSA_TEST_MODE
            )
            return redirect(redirect_url)

        return super().form_valid(form)

    def get_success_url(self):
        return reverse('payment_result')


class PaymentResultView(DetailView):
    model = Payment
    template_name = 'payment_result.html'
    context_object_name = 'payment'

    def get_object(self):
        return Payment.objects.get(id=self.kwargs['payment_id'])


@method_decorator(csrf_exempt, name='dispatch')
class YookassaWebhookView(View):
    def post(self, request, *args, **kwargs):
        try:
            event_json = json.loads(request.body)
            notification_object = WebhookNotification(event_json)

            if notification_object.event in [event_type.PAYMENT_SUCCEEDED, event_type.PAYMENT_CANCELED,
                                             event_type.PAYMENT_WAITING_FOR_CAPTURE]:
                payment_id = notification_object.object.id
                payment_status = notification_object.object.status

                try:
                    payment = Payment.objects.get(kassa_id=payment_id)
                    payment.status = payment_status
                    payment.save()
                except Payment.DoesNotExist:
                    return HttpResponse(f"Payment with ID {payment_id} not found", status=404)

                return JsonResponse({"message": "Payment status updated successfully"}, status=200)

            return JsonResponse({"message": "Unknown event"}, status=400)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class RobokassaSuccessView(View):
    def post(self, request, *args, **kwargs):
        params = parse_qs(request.body.decode('utf-8'))
        inv_id = params.get('InvId', [None])[0]

        try:
            payment = Payment.objects.get(id=inv_id)
            payment.status = "succeeded"
            payment.save()
        except Payment.DoesNotExist:
            return HttpResponse(f"Payment with ID {inv_id} not found", status=404)

        return redirect(reverse("payment_result", args=[inv_id]))


@method_decorator(csrf_exempt, name='dispatch')
class RobokassaFailedView(View):
    def post(self, request, *args, **kwargs):
        params = parse_qs(request.body.decode('utf-8'))
        inv_id = params.get('InvId', [None])[0]

        try:
            payment = Payment.objects.get(id=inv_id)
            payment.status = "failed"
            payment.save()
        except Payment.DoesNotExist:
            return HttpResponse(f"Payment with ID {inv_id} not found", status=404)

        return redirect(reverse("payment_result", args=[inv_id]))
