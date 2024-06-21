from django.contrib import admin

# Register your models here.
from .models import Item, Category, RequiredItem, MenuItem, Order, OrderMeal, OrderReimbursement

admin.site.register(Item)
admin.site.register(MenuItem)
admin.site.register(Category)
admin.site.register(RequiredItem)
admin.site.register(OrderReimbursement)
# admin.site.register(Order)
# admin.site.register(OrderMeal)
class OrderMealInline(admin.TabularInline):
    model = OrderMeal
    extra = 0
    readonly_fields = ('menu_item', 'note', 'order', 'serving', 'additional_items')
    can_delete = False

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('user', 'order_status', 'address', 'total_amount', 'timestamp')
    readonly_fields = ('user', 'order_type', 'address', 'total_amount', 'timestamp')
    # fields = ('order_status', 'user', 'order_type', 'address', 'total_amount', 'order_date_time')
    inlines = [OrderMealInline]
    search_fields = ('user__username', 'address')
    list_filter = ('order_status', 'order_type', 'timestamp')
    ordering = ('-timestamp',)
    date_hierarchy = 'timestamp'

    def get_readonly_fields(self, request, obj=None):
        return self.readonly_fields

@admin.register(OrderMeal)
class OrderMealAdmin(admin.ModelAdmin):
    list_display = ('order', 'menu_item', 'serving', 'note')
    # readonly_fields = ('order', 'menu_item', 'serving', 'note', 'additional_items')
    search_fields = ('menu_item__item__name', 'order__user__username')
    list_filter = ('serving', 'menu_item')