from django.db import models



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
        verbose_name = 'Тренер'
        verbose_name_plural = 'Тренеры'
        ordering = ['order']

    def __str__(self):
        return f'Тренер: {self.full_name}'