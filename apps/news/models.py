from django.db import models
from apps.courts.models import Court
from django.utils.text import slugify



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
        verbose_name = 'Новость'
        verbose_name_plural = 'Новости'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


CATEGORY_CHOICE = [
    ('club', 'Клуб'),
    ('courts', 'Корты'),
    ('training', 'Тренировки'),
    ('tournaments', 'Турниры'),
    ('other', 'Другие')
]

class GalleryImage(models.Model):
    title = models.CharField(max_length=150)
    image = models.ImageField(upload_to='gallery_images/', null=True, blank=True)
    category = models.CharField(choices=CATEGORY_CHOICE, max_length=15, default='club')
    courts = models.ForeignKey(Court, on_delete=models.SET_NULL, blank=True, null=True, related_name='courts')
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = 'Фотография галереи'
        verbose_name_plural = 'Фотографии галереи'
        ordering = ['order']

    def __str__(self):
        return self.title