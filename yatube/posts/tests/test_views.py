import random

from django import forms
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Follow, Group, Post

User = get_user_model()


class PostPagesTest(TestCase):

    TEST_USERNAME = 'test_user'
    TEST_PK = 1
    TEST_GROUP_SLUG = 'test_slug'
    # views и связанные с ними шаблоны
    VIEWS_TEMPLATES = {'posts:index': {'template': 'posts/index.html',
                                       'params': None
                                       },
                       'posts:group_list': {'template':
                                            'posts/group_list.html',
                                            'params':
                                            {'slug': TEST_GROUP_SLUG}
                                            },
                       'posts:profile': {'template':
                                         'posts/profile.html',
                                         'params':
                                         {'username': TEST_USERNAME}
                                         },
                       'posts:post_detail': {'template':
                                             'posts/post_detail.html',
                                             'params':
                                             {'post_id': TEST_PK}
                                             },
                       'posts:post_edit': {'template':
                                           'posts/create_post.html',
                                           'params':
                                           {'post_id': TEST_PK}
                                           },
                       'posts:post_create': {'template':
                                             'posts/create_post.html',
                                             'params':
                                             None
                                             },
                       }

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=cls.TEST_USERNAME)
        cls.group = Group.objects.create(
            pk=cls.TEST_PK,
            title='Тестовое название группы',
            slug=cls.TEST_GROUP_SLUG,
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            pk=cls.TEST_PK,
            author=cls.user,
            text='Тестовый текст поста автора,'
                 'доступного для редактирвоания test_user',
            group=cls.group
        )

    def setUp(self):
        self.auth_user = Client()
        self.auth_user.force_login(user=PostPagesTest.user)
        cache.clear()

    def test_pages_uses_correct_templates(self):
        """Проверка: URL-адрес использует корректный шаблон"""
        for view_name, page in PostPagesTest.VIEWS_TEMPLATES.items():
            with self.subTest(view_name=view_name):
                response = self.__get_response(view_name,
                                               page['params'])
                self.assertTemplateUsed(response, page['template'])

    def test_list_pages_show_correct_context(self):
        """Проверка: при вызове view-функции передается правильный context
        страницам со списком постов"""
        views = PostPagesTest.VIEWS_TEMPLATES
        post = PostPagesTest.post
        group = PostPagesTest.group
        user = PostPagesTest.user

        mutual_context = [('posts:index', post),
                          ('posts:group_list', group.posts.all()[0]),
                          ('posts:profile', user.posts.all()[0])
                          ]
        mutual_context_param = 'page_obj'
        mutual_context_fields = (
            'text', 'pub_date', 'author', 'group', 'image')
        unique_context = [('posts:group_list',
                           ('group', ('slug', 'title', 'description')),
                           group),
                          ('posts:profile',
                           ('author', ('username',)),
                           user)
                          ]
        # тестируем общий контекст
        for view_name, expected in mutual_context:
            with self.subTest(view_name=view_name,
                              mutual_context_param=mutual_context_param):
                response = self.__get_response(view_name,
                                               views[view_name]['params'])
                for field in mutual_context_fields:
                    with self.subTest(field=field):
                        self.assertEqual(response.context[mutual_context_param]
                                         [0].__getattribute__(field),
                                         expected.__getattribute__(field))
        # тестируем уникальный для каждого view контекст
        for view_name, (context_name, fields), expected in unique_context:
            with self.subTest(view_name=view_name,
                              context_name=context_name):
                response = self.__get_response(view_name,
                                               views[view_name]['params'])
                for field in fields:
                    with self.subTest(field=field):
                        self.assertEqual(response.context
                                         [context_name].__getattribute__
                                         (field),
                                         expected.__getattribute__(field))

    def test_form_pages_show_correct_context(self):
        """Проверка: при вызове view-функции передается корректный контекст
        страницам с формами"""
        views = PostPagesTest.VIEWS_TEMPLATES
        test_views = ('posts:post_create',
                      'posts:post_edit')
        form_fields = {'text': forms.fields.CharField,
                       'group': forms.fields.ChoiceField
                       }
        for view in test_views:
            with self.subTest(view=view):
                response = self.__get_response(view, views[view]['params'])
                for value, expected in form_fields.items():
                    with self.subTest(value=value):
                        form_field = response.context.get(
                            'form').fields.get(value)
                        self.assertIsInstance(form_field, expected)

    def test_post_detail_page_shows_correct_context(self):
        post = PostPagesTest.post
        views = PostPagesTest.VIEWS_TEMPLATES
        view_name = 'posts:post_detail'
        post_fields = ('text', 'pub_date', 'author', 'group', 'image')
        response = self.__get_response(view_name,
                                       views[view_name]['params'])
        for field in post_fields:
            with self.subTest(field=field):
                self.assertEqual(response.context['post']
                                 .__getattribute__(field),
                                 post.__getattribute__(field))

    def test_index_page_cache(self):
        """Проверка кэширования данных на главной странице"""
        response = self.auth_user.get(reverse('posts:index'))
        post = Post.objects.get(pk=self.TEST_PK)
        post.delete()
        new_response = self.auth_user.get(reverse('posts:index'))
        self.assertEqual(response.content,
                         new_response.content)
        cache.clear()
        new_response = self.auth_user.get(reverse('posts:index'))
        self.assertNotEqual(response.content,
                            new_response.content)

    def __get_response(self, view_name, params=None):
        return self.auth_user.get(reverse(view_name,
                                          kwargs=params or None))


class PaginatorViewsTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = User.objects.create_user(username='test_user1')
        cls.user2 = User.objects.create_user(username='test_user2')
        cls.group1 = Group.objects.create(
            title='Тестовое название группы 1',
            slug='test-slug-1',
            description='Тестовое описание 1'
        )
        cls.group2 = Group.objects.create(
            title='Тестовое название группы 1',
            slug='test-slug-2',
            description='Тестовое описание 1'
        )
        cls.posts = [
            Post.objects.create(
                author=random.choice(
                    [cls.user1,
                     cls.user2]
                ),
                text=f'Post text {i}',
                group=random.choice(
                    [cls.group1,
                     cls.group2]
                )
            )
            for i in range(13)
        ]
        cache.clear()

    def setUp(self):
        self.client = Client()
        self.client.force_login(user=self.user1)

    def test_first_page_contains_ten_records(self):
        """Проверка: количество постов на первой странице равно 10."""
        response = self.client.get(reverse('posts:index'))

        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records(self):
        """Проверка: на второй странице должно быть три поста."""
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_pages_show_correct_posts(self):
        """Проверка: на страницах группы и пользователя отображаются
        только соотетствующие им посты"""
        test_user = PaginatorViewsTest.user1
        test_group = PaginatorViewsTest.group1
        views = {'posts:profile': {'params': {'username': test_user.username},
                                   'expected': test_user.posts.all()
                                   },
                 'posts:group_list': {'params': {'slug': test_group.slug},
                                      'expected': test_group.posts.all()
                                      }
                 }
        for view, context in views.items():
            with self.subTest(view=view):
                response = self.client.get(reverse(view,
                                                   kwargs=context['params']))
                self.assertQuerysetEqual(response.context['page_obj'],
                                         [repr(post)
                                          for post in context['expected']])


class SubscriptionsTest(TestCase):
    """Тестирование подписок на авторов."""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = User.objects.create_user(username='user1')
        cls.user2 = User.objects.create_user(username='user2')
        cls.post1 = Post.objects.create(
            author=cls.user1,
            text='Тестовый текст поста автора 1',
        )
        cls.post2 = Post.objects.create(
            author=cls.user2,
            text='Тестовый текст поста автора 2',
        )

    def setUp(self):
        self.auth_user = Client()
        self.guest_user = Client()
        self.auth_user.force_login(user=self.user1)

    def test_authorized_user_follow(self):
        """Проверка подписки на автора"""
        followers_count = Follow.objects.count()
        self.auth_user.get(reverse(
            'posts:profile_follow',
            kwargs={'username': 'user2'}
        ))
        self.assertTrue(
            Follow.objects.filter(
                user=self.user1,
                author=self.user2
            ).exists()
        )
        self.assertEqual(followers_count + 1, Follow.objects.count())
        response = self.auth_user.get(reverse(
            'posts:follow_index'
        ))
        # отображение поста на странице подписчика
        expected_context = {'author': self.user2,
                            'text': self.post2.text}
        for field, expected in expected_context.items():
            with self.subTest(field=field):
                self.assertEqual(
                    response.context.get(
                        'page_obj')[0].__getattribute__(field),
                    expected
                )

    def test_authorized_user_unfollow(self):
        """Проверка отписки от автора"""
        Follow.objects.create(
            user=self.user1,
            author=self.user2
        )
        followers_count = Follow.objects.count()
        self.auth_user.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': 'user2'}
        ))
        self.assertFalse(
            Follow.objects.filter(
                user=self.user1,
                author=self.user2
            ).exists()
        )
        self.assertEqual(followers_count - 1, Follow.objects.count())

    def unauthorized_user_redirect(self):
        redirect_from = reverse(
            'posts:profile_follow',
            kwargs={'username': 'user2'}
        )
        response = self.guest_user.get(redirect_from)
        self.assertRedirects(
            response,
            '?next='.join(
                [reverse('users:login'),
                 redirect_from])
        )
