from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from django.shortcuts import redirect



class ClubInfo(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    hero_title = models.CharField(max_length=255)
    hero_image = models.ImageField(upload_to='core_images/', null=True, blank=True)
    hero_video = models.FileField(null=True, blank=True, max_length=1000)
    about_image = models.ImageField(upload_to='about_images/', null=True, blank=True)
    address = models.CharField(max_length=255)
    phone = PhoneNumberField(max_length=33, null=True, blank=True)
    email = models.EmailField(max_length=122, null=True, blank=True)
    tg_url = models.URLField(max_length=2333, blank=True)

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1, defaults={
            'name': 'name club',
            'description': 'description club',
            'hero_title': 'welcome to tennis site',
            'address': 'address',
            'phone': '+996990260319',
            'email': 'agro_apteka@gmail.com'
        })
        return obj

    def changelist_view(self, request, extra_context=None):
        if self.model.objects.exists():
            obj = self.model.objects.first()
            return redirect('admin.core_clubinfo_change')
        return super().changelist_view(request, extra_context)

    def __str__(self):
        return "Информация о клубе"

    class Meta:
        verbose_name = 'Информация о клубе'
        verbose_name_plural = 'Информация о клубе'


class ClubRule(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.order}. {self.title}'

    class Meta:
        verbose_name = 'Правило клуба'
        verbose_name_plural = 'Правила клуба'