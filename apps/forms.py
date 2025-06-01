import re
from calendar import month

from django.forms.fields import CharField, DateField
from django.forms.forms import Form
from django.forms.models import ModelForm
from django.forms.widgets import DateInput

from apps.models import Debt, Contact


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
