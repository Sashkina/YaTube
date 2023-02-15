import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django import forms

from ..models import Post, Group, Follow
from ..forms import PostForm

User = get_user_model()

NUM_PAGINATOR_POSTS_1 = 10
NUM_PAGINATOR_POSTS_2 = 1
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)
UPLOADED = SimpleUploadedFile(
    name='small.gif',
    content=SMALL_GIF,
    content_type='image/gif'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='ТестАвтор')
        cls.group = Group.objects.create(
            title='Тест-группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.group2 = Group.objects.create(
            title='Тест-группа 2',
            slug='test-slug-2',
            description='Тестовое описание 2',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст для 2 группы',
            author=cls.user,
            group=cls.group2,
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
            image=UPLOADED
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}):
                'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': 'ТестАвтор'}):
                'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}):
                'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/post_create.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}):
                'posts/post_create.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_group_list_profile_show_correct_context(self):
        """Шаблоны index, group_list, profile
        сформированы с правильным контекстом."""
        response_context = {
            'index': reverse('posts:index'),
            'group_list': (
                reverse('posts:group_list', kwargs={'slug': 'test-slug'})
            ),
            'profile': (
                reverse('posts:profile', kwargs={'username': 'ТестАвтор'})
            ),
        }
        for reverse_name in response_context.values():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                if self.assertIn('page_obj', response.context):
                    first_object = (response).context['page_obj'][0]
                    post_text_0 = first_object.text
                    post_author_0 = first_object.author.username
                    post_group_0 = first_object.group.title
                    post_image_0 = first_object.image
                    self.assertEqual(post_text_0, 'Тестовый текст')
                    self.assertEqual(post_author_0, 'ТестАвтор')
                    self.assertEqual(post_group_0, 'Тест-группа')
                    self.assertEqual(post_image_0, 'posts/small.gif')

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = (
            self.authorized_client.get(
                reverse('posts:post_detail', kwargs={'post_id': self.post.id})
            )
        )
        self.assertEqual(
            response.context.get('post').text, 'Тестовый текст'
        )
        self.assertEqual(
            response.context.get('post').author.username, 'ТестАвтор'
        )
        self.assertEqual(
            response.context.get('post').group.title, 'Тест-группа'
        )
        self.assertEqual(
            response.context.get('post').image, 'posts/small.gif'
        )

    def test_create_page_show_correct_context(self):
        """Шаблон create сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_create'))
        self.assertIsInstance(response.context['form'], PostForm)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get(
                    'form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_edit_page_show_correct_context(self):
        """Шаблон edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}))
        self.assertIsInstance(response.context['form'], PostForm)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get(
                    'form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_in_group(self):
        """Объект post на страницах
        index, group_list, profile при указании группы."""
        response_index = self.authorized_client.get(
            reverse('posts:index')
        )
        response_group_list = (self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}))
        )
        response_profile = (self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'ТестАвтор'}))
        )
        self.assertIn(
            self.post, response_index.context['page_obj']
        )
        self.assertIn(
            self.post, response_group_list.context['page_obj']
        )
        self.assertIn(
            self.post, response_profile.context['page_obj']
        )

    def test_post_not_in_group(self):
        """Объект post не попал на страницу group_list,
        для которой не предназначен."""
        response = (self.authorized_client.get(
            reverse('posts:group_list', kwargs={
                'slug': 'test-slug-2'}))
        )
        self.assertNotIn(self.post, response.context['page_obj'])


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='ТестАвтор')
        cls.group = Group.objects.create(
            title='Тест-группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        for i in range(11):
            cls.post = Post.objects.create(
                text=f'Тестовый текст{i}',
                author=cls.user,
                group=cls.group,
            )

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_records(self):
        """Paginator выдает 10 постов на первой странице."""
        response_index = self.client.get(
            reverse('posts:index')
        )
        response_group_list = self.client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug'})
        )
        response_profile = self.client.get(
            reverse('posts:profile', kwargs={
                'username': 'ТестАвтор'})
        )
        first_paginator_test = {
            response_index: NUM_PAGINATOR_POSTS_1,
            response_group_list: NUM_PAGINATOR_POSTS_1,
            response_profile: NUM_PAGINATOR_POSTS_1,
        }
        for response, num_posts in first_paginator_test.items():
            with self.subTest(response=response):
                self.assertEqual(
                    len(response.context['page_obj']), num_posts)

    def test_second_page_contains_three_records(self):
        """Paginator выдает 1 пост на второй странице."""
        response_index = self.client.get(
            reverse('posts:index') + '?page=2')
        response_group_list = self.client.get(
            reverse('posts:group_list', kwargs={
                'slug': 'test-slug'}) + '?page=2'
        )
        response_profile = self.client.get(
            reverse('posts:profile', kwargs={
                'username': 'ТестАвтор'}) + '?page=2'
        )
        first_paginator_test = {
            response_index: NUM_PAGINATOR_POSTS_2,
            response_group_list: NUM_PAGINATOR_POSTS_2,
            response_profile: NUM_PAGINATOR_POSTS_2,
        }
        for response, num_posts in first_paginator_test.items():
            with self.subTest(response=response):
                self.assertEqual(
                    len(response.context['page_obj']), num_posts
                )


class CacheViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='ТестАвтор')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
        )

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_cache_index_page(self):
        """Страница index попадает в кэш."""
        response1 = self.authorized_client.get(reverse('posts:index'))
        self.post.delete()
        response2 = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response1.content, response2.content)
        cache.clear()
        response3 = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(response1.content, response3.content)


class FollowingViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = User.objects.create_user(username='ТестАвтор1')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user1,
        )
        cls.user2 = User.objects.create_user(username='ТестАвтор2')
        cls.user3 = User.objects.create_user(username='ТестАвтор3')

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user2)

    def test_user_follow_unfollow_another_user(self):
        """Авторизованный пользователь может подписываться
        на других пользователей и удалять их из подписок."""
        response1 = (self.authorized_client.get(
            reverse('posts:profile_follow', kwargs={
                'username': 'ТестАвтор1'}))
        )
        self.assertTrue(
            Follow.objects.filter(
                user=self.user2,
                author=self.user1,
            ).exists()
        )
        response2 = (self.authorized_client.get(
            reverse('posts:profile_unfollow', kwargs={
                'username': 'ТестАвтор1'}))
        )
        self.assertFalse(
            Follow.objects.filter(
                user=self.user2,
                author=self.user1,
            ).exists()
        )

    def test_user_follow_index_page(self):
        """Новая запись пользователя появляется в ленте тех,
        кто на него подписан и не появляется в ленте тех,
        кто не подписан."""
        response = (self.authorized_client.get(
            reverse('posts:profile_follow', kwargs={
                'username': 'ТестАвтор1'}))
        )
        response1 = self.authorized_client.get(
            reverse('posts:follow_index'))
        self.assertIn(
            self.post, response1.context['page_obj']
        )
        self.authorized_client.logout()
        self.authorized_client.force_login(self.user3)
        response2 = self.authorized_client.get(
            reverse('posts:follow_index'))
        self.assertNotIn(
            self.post, response2.context['page_obj']
        )
