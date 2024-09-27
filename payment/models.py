from django.db import models


class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('yookassa', 'YooKassa'),
        ('robokassa', 'RoboKassa'),
    ]

    customer_email = models.EmailField(max_length=120)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    status = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    kassa_id = models.CharField(max_length=200, default="")

    def __str__(self):
        return f'{self.customer_email} - {self.amount} via {self.payment_method} on {self.created_at}'
