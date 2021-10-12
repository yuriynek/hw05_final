import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            group=cls.group,
            author=cls.user
        )
        cls.comment = Comment.objects.create(
            text='Текст тестового комментария',
            author=cls.user,
            post=cls.post,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.auth_user = Client()
        self.guest_user = Client()
        self.auth_user.force_login(user=PostFormTest.user)
        cache.clear()

    def test_create_post(self):
        """Валидная форма создает новый пост"""
        posts_count = Post.objects.count()
        group = PostFormTest.group
        image = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
                 b'\x01\x00\x80\x00\x00\x00\x00\x00'
                 b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
                 b'\x00\x00\x00\x2C\x00\x00\x00\x00'
                 b'\x02\x00\x01\x00\x00\x02\x02\x0C'
                 b'\x0A\x00\x3B')
        uploaded = SimpleUploadedFile(
            name='test_image.png',
            content=image,
            content_type='image/png'
        )

        form_data = {'text': 'Тестовый текст нового поста',
                     'group': group.pk,
                     'image': uploaded
                     }
        response = self.auth_user.post(reverse('posts:post_create'),
                                       data=form_data,
                                       follow=True)
        self.assertRedirects(response,
                             reverse('posts:profile',
                                     kwargs={'username':
                                             PostFormTest.user.username}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        # Проверка соответствия полей нового поста данным, введенным в форме
        post = Post.objects.latest('pub_date')
        new_post_expected_data = {'text': form_data['text'],
                                  'group': group,
                                  'author': PostFormTest.user,
                                  'image': 'posts/test_image.png'}
        for field, expected in new_post_expected_data.items():
            with self.subTest(field=field):
                self.assertEqual(post.__getattribute__(field),
                                 expected or None)

    def test_edit_post(self):
        """Проверка: редактирование поста"""
        post = PostFormTest.post
        posts_count = Post.objects.count()
        form_data = {'text': 'Тестовый текст измененного поста',
                     'group': ''}
        response = self.auth_user.post(reverse('posts:post_edit',
                                       kwargs={'post_id': post.pk}),
                                       data=form_data,
                                       follow=True)
        post = Post.objects.get(pk=post.pk)
        self.assertRedirects(response, reverse('posts:post_detail',
                                               kwargs={'post_id':
                                                       post.pk}))
        self.assertEqual(Post.objects.count(), posts_count)
        for field, expected in form_data.items():
            with self.subTest(field=field):
                self.assertEqual(post.__getattribute__(field),
                                 expected or None)

    def test_create_post_by_unauthorized_user(self):
        """Проверка: неавторизованный пользователь не может
        создать новый пост"""
        posts_count = Post.objects.count()
        form_data = {'text': 'Текст от неавторизованного пользователя',
                     'group': PostFormTest.group.pk}
        response = self.guest_user.post(reverse('posts:post_create'),
                                        data=form_data,
                                        follow=True)
        self.assertRedirects(response,
                             '?next='.join([reverse('users:login'),
                                            reverse('posts:post_create')]))
        self.assertEqual(Post.objects.count(), posts_count)

    def test_add_comment_by_unauthorized_user(self):
        """Проверка: неавторизованный пользователь не может
        оставлять комментарии"""
        comments_count = Comment.objects.count()
        post = PostFormTest.post
        form_data = {'text': 'Текст нового комментария'}
        response = self.guest_user.post(reverse('posts:add_comment',
                                                kwargs={'post_id': post.pk}),
                                        data=form_data,
                                        follow=True)
        self.assertRedirects(
            response,
            '?next='.join([reverse('users:login'),
                           reverse('posts:add_comment',
                                   kwargs={'post_id': post.pk})]))
        self.assertEqual(Comment.objects.count(), comments_count)

    def test_add_comment_by_authorized_user(self):
        """Проверка: добавление комментария авторизованным пользователем"""
        comments_count = Comment.objects.count()
        post = PostFormTest.post
        form_data = {'text': 'Текст нового комментария'}
        response = self.auth_user.post(reverse('posts:add_comment',
                                               kwargs={'post_id': post.pk}),
                                       data=form_data,
                                       follow=True)
        # Проверка редиректа
        self.assertRedirects(response,
                             reverse('posts:post_detail',
                                     kwargs={'post_id': post.pk}))
        # Проверка добавления комментария в базу данных
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(Comment.objects.filter(
            text=form_data['text'],
            author=PostFormTest.user,
        ).exists(),
            msg='Комментарий не добавлен в базу данных!')
        # Проверка передачи информации в контекст странциы
        comment_fields = ('text', 'author', 'created')
        last_comment_on_page = response.context['comments'].latest('created')
        last_comment_expected = Comment.objects.latest('created')
        for field in comment_fields:
            with self.subTest(field=field):
                self.assertEqual(last_comment_on_page
                                 .__getattribute__(field),
                                 last_comment_expected.__getattribute__(field))
