from django.contrib import admin

from apps.models import Payment, Debt, Category, Contact
from django.contrib.auth.models import Group
from django.contrib import admin

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'amount', 'debt', 'created_at')
    search_fields = ('debt__id',)
    list_filter = ('created_at',)

@admin.register(Debt)
class DebtAdmin(admin.ModelAdmin):
    list_display = 'id', 'amount', 'given_date'
    list_filter = 'id','given_date'

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = 'id', 'name'
    list_filter = 'id',

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = 'id', 'fullname', 'phone_number'
    list_filter = 'id', 'fullname'

admin.site.unregister(Group)
# admin.site.unregister(User)