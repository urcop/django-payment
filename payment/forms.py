from django import forms


class PaymentForm(forms.Form):
    PAYMENT_METHOD_CHOICES = [
        ('yookassa', 'Юкасса'),
        ('robokassa', 'Робокасса'),
    ]

    email = forms.EmailField(label='Email', required=True)
    payment_method = forms.ChoiceField(choices=PAYMENT_METHOD_CHOICES, label='Способ оплаты')
    amount = forms.DecimalField(max_digits=10, decimal_places=2, label='Сумма оплаты')
