from django.contrib import admin
from .models import *



@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_date', 'end_date', 'status', 'is_published')
    list_filter = ('status', 'is_published', 'start_date')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title', )}
    list_editable = ('status', 'is_published')