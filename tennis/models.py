from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.shortcuts import redirect
from django.utils.text import slugify
from phonenumber_field.modelfields import PhoneNumberField


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

    def __str__(self):
        return "Информация о клубе"

    class Meta:
        db_table = 'core_clubinfo'
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
        db_table = 'core_clubrule'
        verbose_name = 'Правило клуба'
        verbose_name_plural = 'Правила клуба'
        ordering = ['order', 'id']


class ActiveCourtManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


SURFACE_CHOICES = [
    ('clay', 'грунт'),
    ('artificial_grass', 'искусственная трава'),
    ('hard', 'Хард')
]

class CourtType(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, max_length=155, blank=True, allow_unicode=True)
    description = models.TextField(null=True, blank=True)
    surface = models.CharField(choices=SURFACE_CHOICES, max_length=20)
    is_indoor = models.BooleanField()
    image = models.ImageField(upload_to='court_type_image/', null=True, blank=True)

    class Meta:
        db_table = 'courts_courttype'
        verbose_name = 'Тип корта'
        verbose_name_plural = 'Типы кортов'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Court(models.Model):
    court_number = models.PositiveSmallIntegerField(unique=True)
    court_type = models.ForeignKey(CourtType, on_delete=models.PROTECT, related_name='court_type')
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True, null=True)

    objects = models.Manager()
    active_objects = ActiveCourtManager()

    class Meta:
        db_table = 'courts_court'
        verbose_name = 'Корт'
        verbose_name_plural = 'Корты'

    def __str__(self):
        return f'Корт № {self.court_number}'


class ActiveCoachManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class Coach(models.Model):
    full_name = models.CharField(max_length=150)
    photo = models.ImageField(upload_to='coach_images/', null=True, blank=True)
    short_bio = models.TextField()
    experience = models.PositiveSmallIntegerField()
    specialization = models.CharField(max_length=150)
    is_active = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField()

    objects = models.Manager()
    active_objects = ActiveCoachManager()

    class Meta:
        db_table = 'coaches_coach'
        verbose_name = 'Тренер'
        verbose_name_plural = 'Тренеры'
        ordering = ['order']

    def __str__(self):
        return f'Тренер: {self.full_name}'


SERVICE_CATEGORY_CHOICE = [
    ('court rental', 'Аренда корта'),
    ("children's tennis", 'Детский теннис'),
    ('team training camps', 'Сборы команд'),
    ('schedule', 'Расписание')
]

class Service(models.Model):
    title = models.CharField(max_length=150)
    slug = models.SlugField(unique=True, max_length=177)
    description = models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to='service_images/', null=True, blank=True)
    category = models.CharField(choices=SERVICE_CATEGORY_CHOICE, max_length=20)
    is_active = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField()

    class Meta:
        db_table = 'services_service'
        verbose_name = 'Сервис'
        verbose_name_plural = 'Сервисы'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class PriceCategory(models.Model):
    title = models.CharField(max_length=150)
    slug = models.SlugField(unique=True, max_length=177)
    order = models.PositiveSmallIntegerField()

    class Meta:
        db_table = 'services_pricecategory'
        verbose_name = 'Цена за сервис'
        verbose_name_plural = 'Цены за сервисы'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class ActivePriceItemManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class PriceItem(models.Model):
    category = models.ForeignKey(PriceCategory, on_delete=models.CASCADE, related_name='price')
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, blank=True, null=True, related_name='service')
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(Decimal(0.00))])
    duration_minutes = models.PositiveIntegerField(blank=True, null=True)
    discount_percent = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    is_active = models.BooleanField(default=True)

    objects = models.Manager()
    active_objects = ActivePriceItemManager()

    class Meta:
        db_table = 'services_priceitem'
        verbose_name = "Ценовая позиция"
        verbose_name_plural = "Ценовые позиции"
        ordering = ['category', 'title']

    def __str__(self):
        return self.title


class PublishedNewsManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_published=True)


class News(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=333, unique=True)
    short_description = models.CharField(max_length=300)
    content = models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to='news_images/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=True)

    objects = models.Manager()
    published_objects = PublishedNewsManager()

    class Meta:
        db_table = 'news_news'
        verbose_name = 'Новость'
        verbose_name_plural = 'Новости'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


GALLERY_CATEGORY_CHOICE = [
    ('club', 'Клуб'),
    ('courts', 'Корты'),
    ('training', 'Тренировки'),
    ('tournaments', 'Турниры'),
    ('other', 'Другие')
]

class GalleryImage(models.Model):
    title = models.CharField(max_length=150)
    image = models.ImageField(upload_to='gallery_images/', null=True, blank=True)
    category = models.CharField(choices=GALLERY_CATEGORY_CHOICE, max_length=15, default='club')
    courts = models.ForeignKey(Court, on_delete=models.SET_NULL, blank=True, null=True, related_name='courts')
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = 'news_galleryimage'
        verbose_name = 'Фотография галереи'
        verbose_name_plural = 'Фотографии галереи'
        ordering = ['order']

    def __str__(self):
        return self.title


class PublishedTournamentManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_published=True)


TOURNAMENT_CHOICES = [
    ('upcoming', 'Предстоящий'),
    ('ongoing', 'Текущий'),
    ('finished', 'Завершённый')
]

class Tournament(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=233)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='tournament_images/', null=True, blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(choices=TOURNAMENT_CHOICES, default='upcoming', max_length=15)
    is_published = models.BooleanField(default=True)

    objects = models.Manager()
    published_objects = PublishedTournamentManager()

    class Meta:
        db_table = 'tournaments_tournament'
        verbose_name = 'Турнир'
        verbose_name_plural = 'Турниры'
        ordering = ['-start_date']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError({
                'end_date': 'Дата окончания не может быть раньше даты начала турнира.'
            })

    def __str__(self):
        return self.title
