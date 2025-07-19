import csv
from itertools import chain
from operator import attrgetter

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Sum, ExpressionWrapper, F, DecimalField, Count, Value
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, ListView, FormView, DeleteView, TemplateView, DetailView

from apps.forms import DebtModelForm, ContactModelForm, DebtFilterForm, PaymentFilterForm, PaymentModelForm
from apps.models import Debt, Contact, Category, Payment
from root.settings import MAX_DIGITS, DECIMAL_PLACE


class HomeDataView(LoginRequiredMixin,ListView):
    login_url = reverse_lazy('register')
    queryset = Debt.objects.all()
    context_object_name = 'home'
    template_name = 'apps/home.html'

    def get_queryset(self):
        queryset = super().get_queryset().filter(user=self.request.user)
        return queryset

    def get_context_data(self, *args, **kwargs):
        data = super().get_context_data(*args, **kwargs)
        data['total_debts'] = Debt.objects.aggregate(total=Sum('amount'))['total'] or 0
        data['total_paid'] = Payment.objects.aggregate(total=Sum('amount'))['total'] or 0
        data['counts'] = Debt.objects.aggregate(count=Count('id'))['count'] or 0
        data['total_left'] = data['total_debts'] - data['total_paid']
        debts = Debt.objects.select_related('contact').all()
        payments = Payment.objects.select_related('debt__contact').all()

        for d in debts:
            d.item_type = 'debt'
        for p in payments:
            p.item_type = 'payment'

        combined = sorted(
            chain(debts, payments),
            key=attrgetter('created_at'),
            reverse=True
        )

        data['activities'] = combined
        return data

class DebtFormCreateView(CreateView):
    queryset = Debt.objects.all()
    form_class = DebtModelForm
    template_name = 'apps/debt_form.html'
    success_url = reverse_lazy('debt-list')

    def form_valid(self, form):
        return super().form_valid(form)
    def form_invalid(self, form):
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['contacts'] = Contact.objects.all()
        data['categories'] = Category.objects.all()
        return data


class DebtPaymentListView(LoginRequiredMixin, ListView):
    template_name = 'debt-detail.html'
    context_object_name = 'payments'

    def get_queryset(self):
        return Payment.objects.filter(debt_id=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        debt_id = self.kwargs.get("pk")
        debt = Debt.objects.select_related('contact', 'category').get(pk=debt_id)
        context['debt'] = debt
        return context
class ContactFormCreateView(CreateView):
    queryset = Debt.objects.all()
    form_class = ContactModelForm
    template_name = 'apps/contact-form.html'
    success_url = reverse_lazy('debt-list')

class DebtListView(ListView, FormView):
    queryset = Debt.objects.all()
    form_class = DebtFilterForm
    success_url = reverse_lazy('debt-list')
    template_name = 'apps/debt-list.html'
    context_object_name = "debts"

    def form_valid(self, form):
        search = form.cleaned_data.get("search")
        status = form.cleaned_data.get("status")
        category_id = form.cleaned_data.get("category")

        # Faqat paid_amount hisoblanadi
        query = Debt.objects.annotate(
            paid_amount=Coalesce(Sum('payments__amount'), Value(0), output_field=DecimalField())
        )

        if search:
            query = query.filter(
                Q(contact__fullname__icontains=search) |
                Q(contact__phone_number__icontains=search)
            )
        if status and status != 'all':
            query = query.filter(status=status)
        if category_id and category_id != '-1':
            query = query.filter(category_id=category_id)

        data = {
            'debts': query,
            'status_list': Debt.StatusType.values,
            'categories': Category.objects.all(),
            'form': form,
        }
        return render(self.request, self.template_name, context=data)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        query = Debt.objects.annotate(
            paid_amount=Coalesce(Sum('payments__amount'), Value(0), output_field=DecimalField())
        )

        data['debts'] = query
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

    def get_initial(self):
        initial = super().get_initial()
        debt_id = self.kwargs.get('pk')
        initial['debt'] = debt_id
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        debt_id = self.kwargs.get("pk")
        context['debt'] = get_object_or_404(Debt, pk=debt_id)
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        payment = self.object
        debt = payment.debt
        if debt.left_amount == 0:
            debt.status = Debt.StatusType.PAID.value
            debt.save()
        return response


