from django.contrib.auth import get_user_model
from django.db import models


User = get_user_model()

PUB_DATE_HELP = (
    'Если установить дату и время в будущем — можно делать '
    'отложенные публикации.')
SLUG_HELP = (
    'Идентификатор страницы для URL; разрешены символы '
    'латиницы, цифры, дефис и подчёркивание.')


class PublicationModel(models.Model):
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Добавлено',
    )
    is_published = models.BooleanField(
        default=True, verbose_name='Опубликовано',
        help_text='Снимите галочку, чтобы скрыть публикацию.',
    )

    class Meta:
        abstract = True


class Category(PublicationModel):
    title = models.CharField(max_length=256, verbose_name='Заголовок', )
    description = models.TextField(verbose_name='Описание', )
    slug = models.SlugField(
        max_length=64, unique=True,
        verbose_name='Идентификатор',
        help_text=SLUG_HELP,
    )

    class Meta:
        ordering = ('title',)
        verbose_name = 'категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.title


class Location(PublicationModel):
    name = models.CharField(max_length=256, verbose_name='Название места', )

    class Meta:
        ordering = ('name',)
        verbose_name = 'местоположение'
        verbose_name_plural = 'Местоположения'

    def __str__(self):
        return self.name


class Post(PublicationModel):
    title = models.CharField(max_length=256, verbose_name='Заголовок', )
    text = models.TextField(verbose_name='Текст', )
    pub_date = models.DateTimeField(
        auto_now_add=False,
        verbose_name='Дата и время публикации',
        help_text=PUB_DATE_HELP,
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор публикации',
    )

    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name='Местоположение',
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Категория',
    )
    image = models.ImageField('Фото', upload_to='posts_images', blank=True)

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'публикация'
        verbose_name_plural = 'Публикации'
        default_related_name = 'posts'

    def __str__(self):
        return self.title


class Comment(models.Model):
    text = models.TextField(verbose_name='Комментарий')
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        verbose_name='Пост'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор'
    )

    class Meta:
        ordering = ('created_at',)
        verbose_name = 'комментарий'
        verbose_name_plural = 'Комментарии'
        default_related_name = 'comments'

    def __str__(self):
        return self.text
