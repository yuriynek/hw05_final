from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostsURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author_username = 'test_user'
        cls.user = User.objects.create_user(username=cls.author_username)
        cls.user1 = User.objects.create_user(username='not_author')
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test_slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст поста автора,'
                 'доступного для редактирвоания test_user',
            group=cls.group
        )
        cls.post_not_editable = Post.objects.create(
            author=cls.user1,
            text='Тестовый текст поста автора,'
                 'недоступного для редактирвоания test_user',
            group=cls.group
        )
        post_id = cls.post.pk
        slug = cls.group.slug
        username = cls.user.username
        # Задаем начальные данные для тестов
        cls.test_urls = {'index': {'template': 'posts/index.html',
                                   'url': '/',
                                   'access': 'all',
                                   'response': HTTPStatus.OK},
                         'group_list': {'template': 'posts/group_list.html',
                                        'url': f'/group/{slug}/',
                                        'access': 'all',
                                        'response': HTTPStatus.OK},
                         'profile': {'template': 'posts/profile.html',
                                     'url': f'/profile/{username}/',
                                     'access': 'all',
                                     'response': HTTPStatus.OK},
                         'post_detail': {'template': 'posts/post_detail.html',
                                         'url': f'/posts/{post_id}/',
                                         'access': 'all',
                                         'response': HTTPStatus.OK},
                         'not_exist': {'template': None,
                                       'url': '/unexisting_page/',
                                       'access': 'all',
                                       'response': HTTPStatus.NOT_FOUND},
                         'post_create': {'template': 'posts/create_post.html',
                                         'url': '/create/',
                                         'access': 'login_required',
                                         'response': HTTPStatus.OK},
                         'post_edit': {'template': 'posts/create_post.html',
                                       'url': lambda post=cls.post:
                                       f'/posts/{post.pk}/edit/',
                                       'access': 'author',
                                       'response': HTTPStatus.OK},
                         }

    def setUp(self):
        self.guest_user = Client()
        self.auth_user = Client()
        self.auth_user.force_login(PostsURLTests.user)
        cache.clear()

    def test_url_uses_correct_template(self):
        """Проверка использования правильных шаблонов страниц
        в зависимости от URL-адреса"""
        test_urls = PostsURLTests.test_urls
        for url_name, url_params in test_urls.items():
            if url_params['template']:
                with self.subTest(url_name=url_name):
                    url = url_params['url']
                    if url_name == 'post_edit':
                        url = url_params['url']()
                    response = self.auth_user.get(url)
                    self.assertTemplateUsed(response, url_params['template'])

    def test_post_urls_exists_at_desired_location(self):
        """Проверка доступности и наличия тестируемых URL,
        с учетом уровней доступа пользователей"""

        # Подготовка данных для тестов
        test_urls = PostsURLTests.test_urls
        users = {'guest': self.guest_user,
                 'authorized': self.auth_user}
        post = PostsURLTests.post
        post_not_editable = PostsURLTests.post_not_editable
        posts = {'author': post,
                 'not_author': post_not_editable}
        for url_name, url_params in test_urls.items():
            with self.subTest(url_name=url_name):
                # Если уровень доступа - все пользователи:
                if url_params['access'] == 'all':
                    response = self.guest_user.get(
                        url_params['url']).status_code
                    self.assertEqual(response, url_params['response'])
                # Если уровень доступа - авторизованные пользователи:
                if url_params['access'] == 'login_required':
                    for user_status, user in users.items():
                        with self.subTest(user=user_status):
                            response = user.get(url_params['url'])
                            self.__login_access_url(user,
                                                    response,
                                                    url_params['response']
                                                    )
                # Если уровень доступа - автор поста:
                if url_params['access'] == 'author':
                    # Проверяем редирект для неавторизованного пользователя:
                    with self.subTest(users=users['guest']):
                        response = self.guest_user.get(url_params['url'](post))
                        self.assertRedirects(response,
                                             f'/auth/login/?next=/posts/'
                                             f'{post.pk}/edit/')
                    #  Проверяем доступность редактирования поста:
                    for post_status, post in posts.items():
                        with self.subTest(users=users['authorized'],
                                          post_status=post_status):
                            response = self.auth_user.get(
                                url_params['url'](post))
                            self.__author_access_url(response,
                                                     url_params['response'],
                                                     post
                                                     )

    def __user_is_authorized(self, user, response):
        """Проверяем, авторизован ли тестовый пользователь,
        если нет - проверяем корректность редиректа"""
        if user == self.auth_user:
            return True
        self.assertRedirects(response, '/auth/login/?next=/create/')
        return False

    def __login_access_url(self, user, response, expected_response):
        """Проверяем, авторизован пользователь или нет,
        если да - проверяем код ответа на корректность"""
        if self.__user_is_authorized(user, response):
            self.assertEqual(response.status_code, expected_response)

    def __author_access_url(self, response, expected_response, post):
        """Проверяем, является ли тестируемый авторизованный пользователь
        автором поста.
        Если нет - проверяем редирект;
        Если да - проверяем корректность кода ответа."""
        if post.author.username == PostsURLTests.author_username:
            self.assertEqual(response.status_code, expected_response)
        else:
            self.assertRedirects(response, f'/posts/{post.pk}/')
