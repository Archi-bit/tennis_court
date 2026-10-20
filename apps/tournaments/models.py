from django.db import models
from django.core.exceptions import ValidationError



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
        verbose_name = 'Турнир'
        verbose_name_plural = 'Турниры'
        ordering = ['-start_date']

    def clean(self):
        super().clean()
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError({
                'end_date': 'Дата окончания не может быть раньше даты начала турнира.'
            })

    def __str__(self):
        return self.title