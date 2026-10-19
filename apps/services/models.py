from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal



CATEGORY_CHOICE = [
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
    category = models.CharField(choices=CATEGORY_CHOICE, max_length=20)
    is_active = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField()

    class Meta:
        verbose_name = 'Сервис'
        verbose_name_plural = 'Сервисы'

    def __str__(self):
        return self.title


class PriceCategory(models.Model):
    title = models.CharField(max_length=150)
    slug = models.SlugField(unique=True, max_length=177)
    order = models.PositiveSmallIntegerField()

    class Meta:
        verbose_name = 'Цена за сервис'
        verbose_name_plural = 'Цены за сервисы'

    def __str__(self):
        return self.title


class ActivePriceItemManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class PriceItem(models.Model):
    category = models.ForeignKey(PriceCategory, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, blank=True, null=True)
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(Decimal(0.00))])
    duration_minutes = models.PositiveIntegerField(blank=True, null=True)
    discount_present = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    is_active = models.BooleanField(default=True)

    objects = models.Manager()
    active_objects = ActivePriceItemManager()

    class Meta:
        verbose_name = "Ценовая позиция"
        verbose_name_plural = "Ценовые позиции"
        ordering = ['category', 'title']

    def __str__(self):
        return self.title