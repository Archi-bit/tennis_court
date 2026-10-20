from django.contrib import admin
from .models import * 



@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'is_active', 'order')
    list_filter = ('is_active', 'category', 'order')
    list_editable = ('order', 'is_active')


@admin.register(PriceCategory)
class PriceCategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'order')
    list_filter = ('order', )


@admin.register(PriceItem)
class PriceItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'service', 'price', 'discount_percent', 'is_active')
    list_filter = ('is_active', 'category', 'service')
    search_fields = ('title', 'description')
    list_editable = ('price', 'is_active')