from django.contrib import admin
from .models import * 



@admin.register(Coach)
class CoachAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'order', 'specialization', 'experience', 'is_active')
    list_filter = ('is_active', 'specialization')
    list_editable = ('order', 'is_active')
    search_fields = ('full_name', 'specialization', 'short_bio')