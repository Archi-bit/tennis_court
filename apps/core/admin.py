from django.contrib import admin
from .models import *

@admin.register(ClubInfo)
class ClubInfoAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ClubRule)
class ClubRuleAdmin(admin.ModelAdmin):
    list_display = ('order', 'title', 'is_active')
    list_editable = ('order', 'is_active')