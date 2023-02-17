from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page

from .models import User, Post, Group, Follow
from .forms import PostForm, CommentForm
from .funcs import get_page_object


@cache_page(20, key_prefix='index_page')
def index(request):
    post_list = Post.objects.select_related('author', 'group').all()
    page_obj = get_page_object(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    page_obj = get_page_object(request, post_list)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    num_posts = post_list.count()
    page_obj = get_page_object(request, post_list)
    context = {
        'author': author,
        'page_obj': page_obj,
        'num_posts': num_posts,
    }
    if request.user.is_anonymous:
        return render(request, 'posts/profile.html', context)
    following = (
        Follow.objects.filter(
            user=request.user,
            author=author,
        ).exists()
    )
    context['following'] = following
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    num_posts = post.author.posts.count()
    form = CommentForm(request.POST or None)
    comment = post.comments.all()
    context = {
        'post': post,
        'num_posts': num_posts,
        'form': form,
        'comments': comment,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if form.is_valid():
        new_post = form.save(commit=False)
        new_post.author = request.user
        new_post.save()
        return redirect('posts:profile', request.user)
    form = PostForm()
    return render(request, 'posts/post_create.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post,
    )
    context = {
        'post': post,
        'form': form,
        'is_edit': True,
    }
    if post.author != request.user:
        return redirect('posts:post_detail', post.id)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('posts:post_detail', post.id)
        return render(request, 'posts/post_create.html', context)
    return render(request, 'posts/post_create.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    page_obj = get_page_object(request, post_list)
    context = {'page_obj': page_obj}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    user = get_object_or_404(User, username=request.user.username)
    if user != author:
        Follow.objects.get_or_create(
            user=user,
            author=author,
        )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    follow_obj = get_object_or_404(Follow, user=user, author=author)
    follow_obj.delete()
    return redirect('posts:profile', username=username)
