from django.contrib import admin

from .models import (
    ClubInfo, ClubRule, CourtType, Court, Coach, Service, PriceCategory,
    PriceItem, News, GalleryImage, Tournament,
)


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
    list_display = ('title', 'order', 'is_active')
    list_filter = ('is_active', )
    list_editable = ('order', 'is_active')
    search_fields = ('title', 'content')


@admin.register(CourtType)
class CourtTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'surface', 'is_indoor', 'get_court_type_count')
    list_filter = ('surface', 'is_indoor')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description')

    @admin.display(description='Количество кортов')
    def get_court_type_count(self, obj):
        return obj.court_type.count()


@admin.register(Court)
class CourtAdmin(admin.ModelAdmin):
    list_display = ('court_number', 'court_type', 'is_active')
    list_filter = ('court_type', 'is_active')
    list_editable = ('is_active',)


@admin.register(Coach)
class CoachAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'order', 'specialization', 'experience', 'is_active')
    list_filter = ('is_active', 'specialization')
    list_editable = ('order', 'is_active')
    search_fields = ('full_name', 'specialization', 'short_bio')


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'is_active', 'order')
    list_filter = ('is_active', 'category', 'order')
    list_editable = ('order', 'is_active')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}


@admin.register(PriceCategory)
class PriceCategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'order')
    list_filter = ('order', )
    search_fields = ('title', )


@admin.register(PriceItem)
class PriceItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'service', 'price', 'discount_percent', 'is_active')
    list_filter = ('is_active', 'category', 'service')
    search_fields = ('title', 'description')
    list_editable = ('price', 'is_active')


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'is_published')
    list_filter = ('is_published', 'created_at')
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ('is_published',)


@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'courts', 'order', 'image')
    list_filter = ('category', 'courts')
    search_fields = ('title', )
    list_editable = ('order', 'category')


@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_date', 'end_date', 'status', 'is_published')
    list_filter = ('status', 'is_published', 'start_date')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title', )}
    list_editable = ('status', 'is_published')
