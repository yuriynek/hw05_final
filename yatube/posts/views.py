from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post

User = get_user_model()


def index(request):
    template = 'posts/index.html'
    posts = Post.objects.all()
    paginator = Paginator(posts, settings.RECORDS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(
        request,
        template,
        context={
            'page_obj': page_obj
        }
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    template = 'posts/group_list.html'
    posts = group.posts.all()
    paginator = Paginator(posts, settings.RECORDS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, template, context={'group': group,
                                              'page_obj': page_obj})


def profile(request, username):
    user = get_object_or_404(User, username=username)
    template = 'posts/profile.html'
    if request.user.is_authenticated:
        following = user.pk in request.user.follower.values_list('author',
                                                                 flat=True)
    else:
        following = False
    posts = user.posts.all()
    paginator = Paginator(posts, settings.RECORDS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'author': user,
               'page_obj': page_obj,
               'following': following}
    return render(request, template, context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    template = 'posts/post_detail.html'
    reader_is_author = request.user == post.author
    form = CommentForm(request.POST or None)
    context = {'post': post,
               'comments': post.comments.all(),
               'form': form,
               'reader_is_author': reader_is_author}
    return render(request, template, context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'
    form = PostForm(request.POST or None,
                    files=request.FILES or None)
    user = request.user
    if form.is_valid():
        new_post = form.save(commit=False)
        new_post.author = user
        new_post.save()
        redirect_url = reverse('posts:profile',
                               kwargs={'username': user.username})
        return redirect(redirect_url)
    context = {'form': form, 'is_edit': False}
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    template = 'posts/create_post.html'
    post = get_object_or_404(Post, pk=post_id)
    user = request.user
    redirect_url = reverse('posts:post_detail',
                           kwargs={'post_id': post_id})
    if user != post.author:
        return redirect(redirect_url)

    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    if form.is_valid():
        form.save()
        return redirect(redirect_url)
    context = {'form': form, 'is_edit': True, 'post': post}
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    posts = Post.objects.filter(
        author_id__in=request.user.follower.values_list(
            'author',
            flat=True
        )
    )
    paginator = Paginator(posts, settings.RECORDS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(
        request,
        'posts/follow.html',
        context={
            'page_obj': page_obj
        }
    )


@login_required
def profile_follow(request, username):
    """Подписаться на автора"""
    followed_user = get_object_or_404(User, username=username)
    following_user = request.user
    if following_user != followed_user:
        if not Follow.objects.filter(
            user=following_user,
            author=followed_user
        ).exists():
            Follow.objects.create(
                user=following_user,
                author=followed_user
            )
    return redirect(reverse('posts:follow_index'))


@login_required
def profile_unfollow(request, username):
    """Дизлайк, отписка"""
    followed_user = get_object_or_404(User, username=username)
    following_user = request.user
    Follow.objects.filter(
        user=following_user,
        author=followed_user
    ).delete()
    return redirect(reverse('posts:follow_index'))
