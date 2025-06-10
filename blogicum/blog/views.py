from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .forms import CommentForm, PostForm, UserForm
from .mixins import AuthorTestsMixin
from .models import Category, Comment, Post


PAGING_OBJECTS = 10


def posts_query(
    posts=Post.objects,
    published=True,
    select_related=True,
    comments_count=True,
):
    if published:
        posts = posts.filter(
            pub_date__lte=timezone.now(),
            is_published=True,
            category__is_published=True,
        )
    if select_related:
        posts = posts.select_related(
            'author',
            'category',
            'location')
    if comments_count:
        posts = posts.annotate(
            comment_count=Count('comments')
        ).order_by(*posts.model._meta.ordering)
    return posts


def paging(posts, request, paginate_by=PAGING_OBJECTS):
    return Paginator(
        posts,
        paginate_by,
    ).get_page(request.GET.get('page'))


class Index(ListView):
    model = Post
    queryset = posts_query()
    paginate_by = PAGING_OBJECTS
    template_name = 'blog/index.html'


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
        return posts_query(category.posts.all())

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            **kwargs,
            category=get_object_or_404(
                Category,
                slug=self.kwargs['category_slug'],
                is_published=True,
            ))


class UserProfileView(DetailView):
    model = get_user_model()
    context_object_name = 'profile'
    template_name = 'blog/profile.html'
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            **kwargs,
            page_obj=paging(posts_query(
                self.get_object().posts.all(),
                published=(self.get_object() != self.request.user),
            ), self.request))


class EditProfileView(LoginRequiredMixin, UpdateView):
    model = get_user_model()
    form_class = UserForm
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
        return super().get_object(posts_query())

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            **kwargs,
            form=CommentForm(),
            comments=self.get_object().comments.all()
        )


class EditPostView(LoginRequiredMixin, AuthorTestsMixin, UpdateView):
    model = Post
    pk_url_kwarg = 'post_id'
    form_class = PostForm
    template_name = 'blog/create.html'

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            args=[self.kwargs[self.pk_url_kwarg]]
        )


class DeletePostView(LoginRequiredMixin, AuthorTestsMixin, DeleteView):
    model = Post
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def get_success_url(self):
        return reverse(
            'blog:index',
        )


class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(
            posts_query(),
            id=self.kwargs['post_id']
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            args=[self.kwargs['post_id']]
        )


class BaseCommentView(LoginRequiredMixin, AuthorTestsMixin):
    model = Comment
    pk_url_kwarg = 'comment_id'
    template_name = 'blog/comment.html'

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            args=[self.kwargs['post_id']]
        )


class EditCommentView(BaseCommentView, UpdateView):
    form_class = CommentForm


class DeleteCommentView(BaseCommentView, DeleteView):
    pass
