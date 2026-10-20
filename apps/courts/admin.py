from django.contrib import admin
from .models import *



@admin.register(CourtType)
class CourtTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'surface', 'is_indoor', 'get_courts_type_count')
    prepopulated_fields = {'slug': ('name',)}

    @admin.display(description='Количество кортов')
    def get_courts_type_count(self, obj):
        return obj.courts_type_count


@admin.register(Court)
class CourtAdmin(admin.ModelAdmin):
    list_display = ('court_number', 'court_type', 'is_active')
    list_filter = ('court_type', 'is_active')
    list_editable = ('is_active',)