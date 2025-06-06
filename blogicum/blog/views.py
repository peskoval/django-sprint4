from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .forms import CommentForm, PostForm
from .models import Category, Comment, Post


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
    paginate_by = 10
    template_name = 'blog/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        for post_object in context['object_list']:
            post_object.comment_count = post_object.comments.count()
        return context


class CategoryPosts(ListView):
    model = Post
    template_name = 'blog/category.html'
    paginate_by = 10

    def get_queryset(self):
        category = get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True,
        )
        return posts_filter(Post.objects).filter(category=category)


class UserProfileView(DetailView):
    User = get_user_model()
    model = User
    context_object_name = 'profile'
    template_name = 'blog/profile.html'
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def get_object(self, queryset=None):
        username = self.kwargs.get(self.slug_url_kwarg)
        return get_object_or_404(self.User, **{self.slug_field: username})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['get_full_name'] = self.object.get_full_name()
        authors_posts = Post.objects.filter(author=self.get_object())
        paginator = Paginator(
            # Post.objects.filter(author=self.get_object()),
            authors_posts,
            10,
        )
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context['page_obj'] = page_obj
        for post in authors_posts:
            context['post.comment_count'] = post.comments.count()
        # context['comment_count'] = Post.objects.filter(author=self.get_object()).comments.count()
        return context


class EditProfileView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = get_user_model()
    fields = ('username', 'first_name', 'last_name', 'email',)
    slug_field = 'username'
    slug_url_kwarg = 'username'
    template_name = 'blog/user.html'

    def get_object(self, queryset=None):
        return get_object_or_404(get_user_model(), **{self.slug_field: self.request.user.username})

    def test_func(self):
        profile = self.get_object()
        return self.request.user.username == profile.username

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )


class CreatePost(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["author"] = self.request.user.id
        return context

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        username = self.request.user
        return reverse_lazy('blog:profile', kwargs={'username': self.request.user})


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    def get_object(self, queryset=None):
        post_id = self.kwargs.get(self.pk_url_kwarg)
        post_object = get_object_or_404(Post, id=post_id)
        if self.request.user == post_object.author:
            return post_object
        if post_object == get_object_or_404(posts_filter(Post.objects), id=post_id):
            return post_object
        raise Http404("404")


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.get_object()
        context['form'] = CommentForm()
        context['comments'] = post.comments.all()
        return context


class EditPostView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    pk_url_kwarg = 'post_id'
    fields = ['title', 'text', 'location', 'category', 'pub_date', 'image', 'is_published']
    template_name = 'blog/create.html'

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author

    def handle_no_permission(self):
        post = self.get_object()
        return redirect(
            reverse('blog:post_detail', kwargs={'post_id': post.id}),
        )

    def get_success_url(self):
        post_id = self.object.id
        return reverse_lazy('blog:post_detail', kwargs={'post_id': post_id})


class DeletePostView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author

    def handle_no_permission(self):
        post = self.get_object()
        return redirect(
            reverse('blog:post_detail', kwargs={'post_id': post.id}),
        )

    def get_success_url(self):
        username = self.request.user
        return reverse_lazy('blog:profile', kwargs={'username': username})


class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def form_valid(self, form):
        post_id = self.kwargs.get('post_id')
        post = get_object_or_404(Post, id=post_id)
        form.instance.author = self.request.user
        form.instance.post = post
        if post.is_published and post.category.is_published:
            return super().form_valid(form)
        else:
            form.add_error(
                None,
                "Невозможно оставить комментарий к неопубликованному посту.",
            )
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.object.post.id},
        )


class EditCommentView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Comment
    pk_url_kwarg = 'comment_id'
    fields = ('comment',)
    template_name = 'blog/comment.html'

    def get_object(self, queryset=None):
        comment_id = self.kwargs.get(self.pk_url_kwarg)
        return get_object_or_404(Comment, id=comment_id)

    def form_valid(self, form):
        post_id = self.kwargs.get('post_id')
        post = get_object_or_404(Post, id=post_id)
        form.instance.author = self.request.user
        form.instance.post = post
        if post.is_published and post.category.is_published:
            return super().form_valid(form)
        else:
            form.add_error(
                None,
                "Невозможно оставить комментарий к неопубликованному посту.",
            )
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comment = self.get_object()
        context['post'] = comment.post
        context['author_username'] = comment.post.author.username
        return context

    def test_func(self):
        comment = self.get_object()
        return self.request.user == comment.author

    def handle_no_permission(self):
        post = self.get_object()
        return redirect(
            reverse('blog:post_detail', kwargs={'post_id': post.id}),
        )

    def get_success_url(self):
        comment = self.get_object()
        return reverse_lazy(
            'blog:post_detail',
            kwargs={'post_id': comment.post.id},
        )


class DeleteCommentView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comment = self.get_object()
        context['post'] = comment.post
        context['author_username'] = comment.post.author.username
        return context

    def test_func(self):
        comment = self.get_object()
        return self.request.user == comment.author

    def handle_no_permission(self):
        comment = self.get_object()
        return redirect(
            reverse('blog:post_detail', kwargs={'post_id': comment.post.id}),
        )

    def get_success_url(self):
        comment = self.get_object()
        return reverse_lazy(
            'blog:post_detail',
            kwargs={'post_id': comment.post.id, },
        )
