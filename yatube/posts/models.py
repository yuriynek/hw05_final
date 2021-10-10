from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse

User = get_user_model()


class Post(models.Model):
    text = models.TextField(verbose_name='Текст поста')
    pub_date = models.DateTimeField(auto_now_add=True,
                                    verbose_name='Дата публикации')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор'
    )
    group = models.ForeignKey(
        'Group',
        on_delete=models.SET_NULL,
        related_name='posts',
        blank=True,
        null=True,
        verbose_name='Сообщество'
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        ordering = ['-pub_date', ]
        verbose_name = 'запись'
        verbose_name_plural = 'Записи'

    def __str__(self):
        return self.text[:15]

    def get_absolute_url(self):
        """Метод для формирования динамического URL-адреса"""
        return reverse('posts:group_list', kwargs={'slug': self.group.slug})


class Group(models.Model):
    title = models.CharField(max_length=200, verbose_name='Наименование')
    slug = models.SlugField(unique=True, verbose_name='URL-адрес')
    description = models.TextField(verbose_name='Описание')

    class Meta:
        verbose_name = 'сообщество'
        verbose_name_plural = 'Сообщества'
        ordering = ['pk', ]

    def __str__(self):
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Комментарий'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор'
    )
    text = models.TextField('Текст комментария')
    created = models.DateTimeField(
        'Дата и время комментария',
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ['-created', ]

    def __str__(self):
        return self.text[:15]


class Follow(models.Model):

    user = models.ForeignKey(
        User,
        related_name='follower',
        verbose_name='Подписчик',
        on_delete=models.CASCADE
    )
    author = models.ForeignKey(
        User,
        related_name='following',
        verbose_name='Подписка',
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'подписка'
        verbose_name_plural = 'Подписки'
        ordering = ['pk', ]
