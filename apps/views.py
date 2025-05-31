
from django.db.models import Q, Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, ListView, FormView, DeleteView

from apps.forms import DebtModelForm, ContactModelForm, DebtFilterForm, PaymentFilterForm
from apps.models import Debt, Contact, Category, Payment
import csv
from django.http import HttpResponse


class DebtFormCreateView(CreateView):
    queryset = Debt.objects.all()
    form_class = DebtModelForm
    template_name = 'apps/debt_form.html'
    success_url = reverse_lazy('debt-list')

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['contacts'] = Contact.objects.all()
        data['categories'] = Category.objects.all()
        return data


class ContactFormCreateView(CreateView):
    queryset = Debt.objects.all()
    form_class = ContactModelForm
    template_name = 'apps/contact-form.html'
    success_url = reverse_lazy('debt-list')


class DebtListView(ListView, FormView):
    queryset = Debt.objects.all()
    context_object_name = 'debts'
    form_class = DebtFilterForm
    template_name = 'apps/debt-list.html'
    success_url = reverse_lazy('debt-list')

    def form_valid(self, form):
        search = form.cleaned_data.get('search')
        status = form.cleaned_data.get('status')
        category_id = form.cleaned_data.get('category')

        data = {}
        query = Debt.objects.all()
        if search:
            query = query.filter(Q(contact__fullname__icontains=search) | Q(contact__phone_number__icontains=search))
        if status and status != 'all':
            query = query.filter(status=status)
        if category_id and category_id != '-1':
            query = query.filter(category_id=category_id)

        data['debts'] = query
        data['status_list'] = Debt.StatusType.values
        data['categories'] = Category.objects.all()

        return render(self.request, 'apps/debt-list.html', context=data)

    def get_context_data(self, *args, **kwargs):
        data = super().get_context_data(*args, **kwargs)
        data['status_list'] = Debt.StatusType.values
        data['categories'] = Category.objects.all()

        return data

class DebtDeleteView(DeleteView):
    queryset = Debt.objects.all()
    template_name = 'apps/debt-list.html'
    success_url = reverse_lazy('debt-list')
    pk_url_kwarg = 'pk'

class PaymentListView(ListView, FormView):
    queryset = Payment.objects.all()
    context_object_name = 'payments'
    template_name = 'apps/payment.html'
    form_class = PaymentFilterForm
    success_url = reverse_lazy('payment-history')

    def get_context_data(self, *args, **kwargs):
        data = super().get_context_data(*args, **kwargs)
        data['debts'] = Debt.objects.all()
        data['count'] = Payment.objects.count()
        data['total'] = Payment.objects.aggregate(total=Sum('amount'))['total'] or 0
        now = timezone.now()
        start_of_month = now.replace(day=1,hour=0,minute=0,second=0,microsecond=0)
        monthly_total = Payment.objects.filter(created_at__gte=start_of_month).aggregate(total=Sum('amount'))['total'] or 0
        data['month'] = monthly_total

        return data

    def form_valid(self, form):
        month = form.cleaned_data.get('month')
        search = form.cleaned_data.get('search')

        query = Payment.objects.all()
        if search:
            months = Payment.objects.annotate(months=TruncMonth('created_at'))
            query = query.filter(months_icontains =month)

    def form_invalid(self, form):
        pass


class PaymentDeleteView(DeleteView):
    queryset = Payment.objects.all()
    template_name = 'apps/payment.html'
    success_url = reverse_lazy('payment-history')
    pk_url_kwarg = 'pk'

def export_payments_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="payments.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'Amount', 'Created At', 'Name', 'Phone'])

    payments = Payment.objects.all()

    for payment in payments:
        contact = payment.debt.contact
        writer.writerow([
            payment.id,
            payment.amount,
            payment.created_at.strftime('%Y-%m-%d %H:%M'),
            contact.fullname,
            contact.phone_number,
        ])

    return response








