import csv

from django.db.models import Q, Sum, ExpressionWrapper, F, DecimalField, Count
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, ListView, FormView, DeleteView

from apps.forms import DebtModelForm, ContactModelForm, DebtFilterForm, PaymentFilterForm, PaymentModelForm
from apps.models import Debt, Contact, Category, Payment
from root.settings import MAX_DIGITS, DECIMAL_PLACE


class HomeDataView(ListView):
    queryset = Debt.objects.all()
    context_object_name = 'home'
    template_name = 'apps/home.html'

    def get_context_data(self, *args, **kwargs):
        data = super().get_context_data(*args, **kwargs)
        data['total_debts'] = Debt.objects.aggregate(total=Sum('amount'))['total'] or 0
        data['total_paid'] = Payment.objects.aggregate(total=Sum('amount'))['total'] or 0
        data['counts'] = Debt.objects.aggregate(count=Count('id'))['count'] or 0
        data['total_left'] = data['total_debts'] - data['total_paid']
        return data


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

    def get_queryset(self):
        return Debt.objects.prefetch_related('payments').annotate(
            total_amount = Sum('payments__amount'),
            left_amount=ExpressionWrapper(F('amount')- F('total_amount'),
                                      output_field=DecimalField(max_digits=MAX_DIGITS,decimal_places=DECIMAL_PLACE))
        )

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
        data['payment'] = Payment.objects.all()

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


class PaymentListView(ListView):
    queryset = Payment.objects.all()
    context_object_name = 'payments'
    template_name = 'apps/payment.html'
    form_class = PaymentFilterForm
    success_url = reverse_lazy('payment-history')

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['debts'] = Debt.objects.all()
        data['count'] = Payment.objects.count()
        data['total'] = Payment.objects.aggregate(total=Sum('amount'))['total'] or 0
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_total = Payment.objects.filter(created_at__gte=start_of_month).aggregate(total=Sum('amount'))[
                            'total'] or 0
        data['month'] = monthly_total
        return data

    def get_queryset(self):
        return Payment.objects.select_related('debt').annotate(
            left_amount=ExpressionWrapper(
                F('debt__amount') - F('amount'),
                output_field=DecimalField(max_digits=MAX_DIGITS,decimal_places=DECIMAL_PLACE)
            )
        )


    def post(self, request):
        month = request.POST.get('month')
        search = request.POST.get('search')
        context = {}

        query = Payment.objects.all()
        if month:
            query = query.filter(created_at__month=month)
        if search:
            query = query.filter(
                Q(debt__contact__fullname__icontains=search) | Q(debt__contact__phone_number__icontains=search))

        context['payments'] = query

        return render(request, template_name='apps/payment.html', context=context)


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


class PaymentFormView(CreateView):
    queryset = Payment.objects.all()
    form_class = PaymentModelForm
    template_name = 'apps/payment-form.html'
    success_url = reverse_lazy('debt-list')
    context_object_name = 'debt'

    def get_context_data(self, **kwargs):
        debt_id = self.kwargs.get("pk")
        context = super().get_context_data(**kwargs)
        context['debt'] = Debt.objects.filter(pk=debt_id).annotate(
            left_amount=F("amount") - Sum("payments__amount", default=0)).values("pk", 'left_amount').first()
        return context

    def form_valid(self, form):
        debt_id = form.data.get("debt")
        debt = Debt.objects.filter(pk=debt_id).first()
        if debt.left_amount == 0:
            debt.status = Debt.StatusType.PAID.value
            debt.save()
        return super().form_valid(form)