from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Count
from django.contrib.auth.decorators import login_required

from blog.models import Post, Category, Comment, User

from .forms import CreateCommentForm, PostForm, ProfileForm


def filter_posts():
    return Post.objects.filter(
        is_published__exact=True,
        pub_date__lte=timezone.now(),
        category__is_published=True)


def get_pagination(request, objects):
    paginator = Paginator(objects, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj


def index(request):
    template = 'blog/index.html'
    post_list = (
        filter_posts()
        .annotate(comment_count=Count('comments'))
        .order_by('-pub_date')
    )
    page_obj = get_pagination(request, post_list)
    context = {
        'page_obj': page_obj
    }
    return render(request, template, context)


def category_posts(request, category_slug):
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published__exact=True
    )
    post_list = filter_posts().filter(category=category).order_by('-pub_date')
    page_obj = get_pagination(request, post_list)
    context = {
        'category': category, 'page_obj': page_obj
    }
    template = 'blog/category.html'
    return render(request, template, context)


def profile(request, username):
    template = 'blog/profile.html'
    user = get_object_or_404(
        User, username=username)
    post_list = (
        Post.objects.filter(author=user)
        .annotate(comment_count=Count('comments'))
        .order_by('-pub_date')
    )
    if request.user != user:
        post_list = post_list.filter(author=user)
    page_obj = get_pagination(request, post_list)
    context = {'profile': user, 'page_obj': page_obj}
    return render(request, template, context)


@login_required
def edit_profile(request):
    template = 'blog/user.html'
    user = get_object_or_404(
        User,
        username=request.user
    )
    form = ProfileForm(request.POST, instance=user)
    if form.is_valid():
        form.save()
        return redirect('blog:profile', request.user)
    context = {'form': form}
    return render(request, template, context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        post = get_object_or_404(filter_posts(), id=post_id)
    comments = (Comment.objects.select_related('author')
                .filter(post=post)
                .order_by('created_at'))
    form = CreateCommentForm(request.POST or None)
    context = {
        'post': post, 'form': form, 'comments': comments
    }
    template = 'blog/detail.html'
    return render(request, template, context)


@login_required
def create_post(request):
    template = 'blog/create.html'
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('blog:profile', request.user)
    context = {'form': form}
    return render(request, template, context)


@login_required
def edit_post(request, post_id):
    template = 'blog/create.html'
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('blog:post_detail', post_id)
    if request.method == 'POST':
        form = PostForm(request.POST, 
                        files=request.FILES or None,
                        instance=post)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', post_id)
    else:
        form = PostForm(instance=post)
    context = {'form': form}
    return render(request, template, context)


@login_required
def delete_post(request, post_id):
    template = 'blog/create.html'
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('blog:post_detail', post_id)
    form = PostForm(request.POST or None, instance=post)
    if request.method == 'POST':
        post.delete()
        return redirect('blog:index')
    context = {'form': form}
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CreateCommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
    return redirect('blog:post_detail', post_id)


@login_required
def edit_comment(request, post_id, comment_id):
    template = 'blog/comment.html'
    comment = get_object_or_404(Comment, id=comment_id)
    if request.user != comment.author:
        return redirect('blog:post_detail', post_id)
    form = CreateCommentForm(request.POST or None, instance=comment)
    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', post_id)
    context = {'form': form, 'comment': comment}
    return render(request, template, context)


@login_required
def delete_comment(request, post_id, comment_id):
    template = 'blog/comment.html'
    comment = get_object_or_404(Comment, id=comment_id)
    if request.user != comment.author:
        return redirect('blog:post_detail', post_id)
    if request.method == "POST":
        comment.delete()
        return redirect('blog:post_detail', post_id)
    context = {'comment': comment}
    return render(request, template, context)
