import re
from calendar import month

from django.core.exceptions import ValidationError
from django.db.models.aggregates import Sum
from django.forms.fields import CharField, DateField
from django.forms.forms import Form
from django.forms.models import ModelForm
from django.forms.widgets import DateInput

from apps.models import Debt, Contact, Payment


class DebtModelForm(ModelForm):
    class Meta:
        model = Debt
        fields = 'amount', 'given_date', 'due_date', 'description', 'category', 'user', 'contact'

class ContactModelForm(ModelForm):
    class Meta:
        model = Contact
        fields = 'fullname', 'phone_number',
    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        re.sub(r'\D','',phone )
        return phone

class DebtFilterForm(Form):
    category = CharField(required=False)
    status = CharField(max_length=30,required=False)
    search = CharField(max_length=255 ,required=False)

class PaymentFilterForm(Form):
    search = CharField(max_length=255 ,required=False)
    month = DateField(widget=DateInput(attrs={'type':month}), required=False)

class PaymentModelForm(ModelForm):
    class Meta:
        model = Payment
        fields = 'amount', 'debt', 'paid_date', 'notes'

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        debt = self.cleaned_data.get('debt')

        if not isinstance(debt, Debt):
            debt_id = debt or self.initial.get('debt')
            debt = Debt.objects.get(pk=debt_id)

        if amount > debt.left_amount:
            raise ValidationError("To'lov miqdori qolgan qarzdan ko'p bo'lishi mumkin emas.")

        if amount < 0:
            raise ValidationError("To'lov summasi manfiy bo'lmasin!")

        return amount
