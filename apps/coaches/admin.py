from django.contrib import admin
from .models import * 



@admin.register(Coach)
class CoachAdmin(admin.ModelAdmin):
    list_display = ('order', 'full_name', 'specialization', 'experience', 'is_active')
    list_editable = ('order', 'is_active')
    list_filter = ('is_active', 'specialization')
    search_fields = ('full_name', 'specialization', 'short_bio')