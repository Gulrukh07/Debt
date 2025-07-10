from django.db.models import Model, CharField, SlugField, DecimalField, DateField, TextField, ForeignKey, CASCADE, \
    DateTimeField, SET_NULL, Value
from django.db.models.aggregates import Sum
from django.db.models.enums import TextChoices
from django.db.models.fields import URLField
from django.db.models.functions import Coalesce
from django.utils.text import slugify


class Category(Model):
    icon = URLField()
    name = CharField(max_length=255)
    slug = SlugField()

    def save(self, *args, **kwargs):
        slug = slugify(self.name)  #
        i = 1
        while self.__class__.objects.filter(slug=slug).exists():
            slug += f"-{i}"
            i += 1
        self.slug = slug
        return super().save(*args, **kwargs)

    def __repr__(self):
        return self.name


class Contact(Model):
    fullname = CharField(max_length=255)
    phone_number = CharField(max_length=20)

    def __repr__(self):
        return self.fullname


class Debt(Model):
    class StatusType(TextChoices):
        ACTIVE = 'active', 'Active'
        PAID = 'paid', 'Paid'
        EXPIRED = 'expired', 'Expired'

    amount = DecimalField(max_digits=9, decimal_places=0)
    given_date = DateField()
    due_date = DateField()
    description = TextField()
    category = ForeignKey('apps.Category', CASCADE, related_name='debts')
    user = ForeignKey('authentication.User', CASCADE, related_name='debts')
    contact = ForeignKey('apps.Contact', CASCADE, related_name='debts')
    status = CharField(max_length=25, choices=StatusType.choices, default=StatusType.ACTIVE)
    left_amount = DecimalField(max_digits=15, decimal_places=0)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.left_amount = self.amount
        super().save(*args, **kwargs)

    def update_left_amount(self):
        total_paid = self.payments.aggregate(
            total=Coalesce(Sum('amount'), Value(0), output_field=DecimalField())
        )['total']
        self.left_amount = self.amount - total_paid
        self.save()

    def __str__(self):
        return self.contact.fullname


class Payment(Model):
    amount = DecimalField(max_digits=9, decimal_places=0)
    debt = ForeignKey('apps.Debt', SET_NULL, null=True, blank=True, related_name='payments')
    created_at = DateTimeField(auto_now_add=True)
    paid_date = DateField()
    notes = TextField()

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            self.debt.update_left_amount()

    def __repr__(self):
        return self.debt.contact.fullname
