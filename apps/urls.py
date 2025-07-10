from django.urls import path
from django.views.generic import TemplateView

from apps.views import DebtFormCreateView, ContactFormCreateView, DebtListView, DebtDeleteView, \
    PaymentListView, PaymentDeleteView, export_payments_csv, HomeDataView, PaymentFormView

urlpatterns = [
    path("", HomeDataView.as_view(template_name='apps/home.html'), name='home'),
    path("debt-form", DebtFormCreateView.as_view(), name='debt-form'),
    path("debt-list", DebtListView.as_view(), name='debt-list'),
    path("debt-delete/<int:pk>", DebtDeleteView.as_view(), name='debt-delete'),
    path("contact-form", ContactFormCreateView.as_view(), name='contact-form'),
    path("payment-history", PaymentListView.as_view(), name='payment-history'),
    path("payment-form<int:pk>", PaymentFormView.as_view(), name='payment-form'),
    path("payment-delete/<int:pk>", PaymentDeleteView.as_view(), name='payment-delete'),
    path("payment-dexport", export_payments_csv, name='payment-export'),
]
