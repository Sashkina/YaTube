# from django.contrib.auth import get_user_model
# from django.test import TestCase, Client

# from http import HTTPStatus

# User = get_user_model()


# class PostURLTests(TestCase):
#     @classmethod
#     def setUpClass(cls):
#         super().setUpClass()
#         cls.user = User.objects.create_user(username='ТестАвтор')
#         cls.group = Group.objects.create(
#             title='Тест-группа',
#             slug='test-slug',
#             description='Тестовое описание',
#         )
#         cls.post = Post.objects.create(
#             text='Тестовый текст',
#             author=cls.user,
#             group=cls.group,
#         )

#     def setUp(self):
#         self.guest_client = Client()
#         self.authorized_client = Client()
#         self.authorized_client.force_login(self.user)

#     def test_pages_for_guest(self):
#         """Страницы, доступные неавторизованному пользователю."""
#         exists_for_guest = {
#             '/': HTTPStatus.OK,
#             '/group/test-slug/': HTTPStatus.OK,
#             '/profile/ТестАвтор/': HTTPStatus.OK,
#             f'/posts/{self.post.id}/': HTTPStatus.OK,
#             '/unexisting_page/': HTTPStatus.NOT_FOUND,
#         }
#         for adress, status in exists_for_guest.items():
#             with self.subTest(adress=adress):
#                 response = self.guest_client.get(adress)
#                 self.assertEqual(
#                     response.status_code, status)

#     def test_page_create_for_authorized(self):
#         """Страница /create/ доступна
#         авторизованному пользователю."""
#         response = self.authorized_client.get('/create/')
#         self.assertEqual(response.status_code, HTTPStatus.OK)

#     def test_page_edit_for_author(self):
#         """Страница '/<post_id>/edit/' доступна автору поста"""
#         response = self.authorized_client.get('/<post_id>/edit/')
#         if self.authorized_client == self.post.author:
#             self.assertEqual(response.status_code, HTTPStatus.OK)

#     def test_urls_posts_use_correct_template(self):
#         """URL-адрес использует соответствующий шаблон."""
#         templates_url_names = {
#             '/': 'posts/index.html',
#             '/group/test-slug/': 'posts/group_list.html',
#             '/profile/ТестАвтор/': 'posts/profile.html',
#             f'/posts/{self.post.id}/': 'posts/post_detail.html',
#             '/create/': 'posts/post_create.html',
#             f'/posts/{self.post.id}/edit/': 'posts/post_create.html',
#         }
#         for url, template, in templates_url_names.items():
#             with self.subTest(template=template):
#                 response = self.authorized_client.get(url)
#                 self.assertTemplateUsed(response, template)
