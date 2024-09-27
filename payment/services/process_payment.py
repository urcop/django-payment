from yookassa import Payment as YooPayment, Configuration, Webhook

from core import settings
from payment.models import Payment

Configuration.account_id = settings.YOOKASSA_SHOP_ID
Configuration.secret_key = settings.YOOKASSA_SECRET_KEY


def process_payment_yookassa(amount: int, description: str, return_url: str, payment_model: Payment):
    try:
        payment = YooPayment.create({
            "amount": {
                "value": str(amount),
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": return_url
            },
            "capture": True,
            "description": description,
        })
        Payment.objects.filter(id=payment_model.id).update(kassa_id=payment.id)

        return payment.confirmation['confirmation_url'], 'pending'
    except Exception as e:
        print(f"Ошибка создания платежа: {e}")
        return None, 'error'
