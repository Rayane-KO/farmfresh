from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem

class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'order_date', 'status', 'total')
    list_filter = ('status',)
    search_fields = ('user__username',)
    inlines = [OrderItemInline]


class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'item', 'quantity', 'total')
    list_filter = ('order__status',)
    search_fields = ('order__user__username',)



# Register your models here.
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem, OrderItemAdmin)