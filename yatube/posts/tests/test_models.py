from django.contrib.auth import get_user_model
from django.db import models
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test_slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст длиной более 15 символов',
            group=cls.group
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post = PostModelTest.post
        group = PostModelTest.group
        test_cases = {group: group.title,
                      post: post.text[:15]}
        for value, expected in test_cases.items():
            with self.subTest(value=value):
                self.assertEqual(value.__str__(),
                                 expected,
                                 'Некорректная работа метода __str__'
                                 )

    def test_post_get_absolute_url(self):
        """Проверяем правильность метода формирования URL-адреса."""
        post = PostModelTest.post
        expected_url = f'/group/{post.group.slug}/'
        self.assertEqual(post.get_absolute_url(),
                         expected_url,
                         'Некорректное формирование URL при работе'
                         'метода get_absolute_url'
                         )

    def test_model_records_ordering(self):
        """Проверяем сортировку при выводе записей."""
        post_ordering = PostModelTest.post._meta.ordering
        expected_ordering = ['-pub_date']
        self.assertEqual(post_ordering,
                         expected_ordering,
                         'Установите порядок вывода записей от новых к старым')

    def test_post_fields_on_delete_modes(self):
        """Проееряем режимы работы полей таблицы БД в случае
        удаления связанных записей: групп и пользователей."""
        post = PostModelTest.post
        on_delete_modes = {'author': models.CASCADE,
                           'group': models.SET_NULL}
        for field, expected_mode in on_delete_modes.items():
            with self.subTest(field=field):
                self.assertEqual(post._meta.get_field(field).
                                 remote_field.on_delete,
                                 expected_mode,
                                 f'\nУстановите атрибут on_delete поля {field}'
                                 f'в режим {expected_mode.__name__}'
                                 )
