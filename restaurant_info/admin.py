from django.contrib import admin
from .models import Restaurant, OpeningHour, RestaurantConfiguration

class OpeningHourInline(admin.TabularInline):
    model = OpeningHour
    extra = 0
    # readonly_fields = ('menu_item', 'note', 'order', 'serving', 'additional_items')
    # can_delete = False

@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    inlines = [OpeningHourInline]
    list_display = ('name', 'address', 'phone_number')

@admin.register(OpeningHour)
class OpeningHourAdmin(admin.ModelAdmin):
    list_display = ('restaurant', 'day_of_week', 'kitchen_open', 'kitchen_close', 'delivery_open', 'delivery_close')
    list_filter = ('restaurant', 'day_of_week')


@admin.register(RestaurantConfiguration)
class RestaurantConfigurationAdmin(admin.ModelAdmin):
    list_display = ('title', 'key', 'value', 'is_active')
    search_fields = ('title', 'key', 'value')
    list_filter = ('is_active',)
    ordering = ('title',)

# admin.site.register(RestaurantConfiguration, RestaurantConfigurationAdmin)