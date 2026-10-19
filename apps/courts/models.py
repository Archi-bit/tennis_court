from django.db import models



class ActiveCourtManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


SURFACE_CHOISES = [
    ('clay', 'грунт'),
    ('artificial_grass', 'искусственная трава'),
    ('hard', 'хард')
]

class CourtType(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, max_length=155)
    description = models.TextField(null=True, blank=True)
    surface = models.CharField(choices=SURFACE_CHOISES, max_length=20)
    is_indoor = models.BooleanField()
    image = models.ImageField(upload_to='court_type_image/', null=True, blank=True)

    class Meta:
        verbose_name = 'Тип корта'
        verbose_name_plural = 'Типы кортов'

    @property
    def courts_count(self):
        return self.courts.count

    def __str__(self):
        return self.name


class Court(models.Model):
    court_number = models.PositiveSmallIntegerField(unique=True)
    court_type = models.ForeignKey(CourtType, on_delete=models.PROTECT, related_name='courts')
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True, null=True)

    objects = models.Manager()
    active_objects = ActiveCourtManager()

    class Meta:
        verbose_name = 'Корт'
        verbose_name_plural = 'Корты'

    def __str__(self):
        return f'Корт № {self.court_number}'