from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
    View,
)

from .forms import CommentForm, PostForm
from .mixins import AuthorTestsMixin
from .models import Category, Comment, Post


PAGING_OBJECTS = 10

def posts_filter(posts_objects):
    return posts_objects.filter(
        pub_date__lte=timezone.now(),
        is_published=True,
        category__is_published=True,
    ).select_related(
        'author',
        'category',
        'location',
    )


class Index(ListView):
    model = Post
    queryset = posts_filter(Post.objects)
    paginate_by = PAGING_OBJECTS
    template_name = 'blog/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for post_object in context['object_list']:
            post_object.comment_count = post_object.comments.count()
        return context


class CategoryPosts(ListView):
    model = Post
    template_name = 'blog/category.html'
    paginate_by = PAGING_OBJECTS

    def get_queryset(self):
        category = get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True,
        )
        return posts_filter(Post.objects).filter(category=category)


class UserProfileView(DetailView):
    model = get_user_model()
    context_object_name = 'profile'
    template_name = 'blog/profile.html'
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        paginator = Paginator(
            Post.objects.filter(author=self.get_object()), # добавить логику чтобы
             # не видеть снятых с публикации постов другого пользователя
            PAGING_OBJECTS,
        )
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context['page_obj'] = page_obj
        for post in page_obj:
            post.comment_count = post.comments.count()
        return context


class EditProfileView(LoginRequiredMixin, UpdateView):
    model = get_user_model()
    fields = ('username', 'first_name', 'last_name', 'email',)
    template_name = 'blog/user.html'

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse(
            'blog:profile',
            args=[self.request.user.username,]
        )


class CreatePost(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:profile',
            args=[self.request.user.username, ]
        )


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    def get_object(self, queryset=None):
        post = super().get_object(queryset)
        if self.request.user == post.author:
            return post
        post = get_object_or_404(
            Post.objects.filter(is_published=True),
            id=post.id
        )
        return super().get_object(queryset)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = self.get_object().comments.all()
        return context


class EditPostView(LoginRequiredMixin, AuthorTestsMixin, UpdateView):
    model = Post
    pk_url_kwarg = 'post_id'
    form_class = PostForm
    template_name = 'blog/create.html'

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            args=[self.get_object().id, ]
        )


class DeletePostView(LoginRequiredMixin, AuthorTestsMixin, DeleteView):
    model = Post
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def get_success_url(self):
        return reverse(
            'blog:profile',
            args=[self.request.user, ]
        )


class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(Post, id=self.kwargs['post_id'])
        if (
            form.instance.post.is_published
            and form.instance.post.category.is_published
        ):
            return super().form_valid(form)
        else:
            form.add_error(
                None,
                "Невозможно оставить комментарий к неопубликованному посту.",
            )
            return self.form_invalid(form)

    def get_success_url(self):
        post_id = self.kwargs['post_id']
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': post_id}
        )


class BaseCommentView(LoginRequiredMixin, AuthorTestsMixin):
    model = Comment
    pk_url_kwarg = 'comment_id'
    template_name = 'blog/comment.html'

    def get_success_url(self):
        post_id = self.kwargs['post_id']
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': post_id}
        )


class EditCommentView(BaseCommentView, UpdateView):
    form_class = CommentForm


class DeleteCommentView(BaseCommentView, DeleteView):
    pass
