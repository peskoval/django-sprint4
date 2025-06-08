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


class EditProfileView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = get_user_model()
    fields = ('username', 'first_name', 'last_name', 'email',)
    slug_field = 'username'
    slug_url_kwarg = 'username'
    template_name = 'blog/user.html'

    def get_object(self, queryset=None):
        return get_object_or_404(
            get_user_model(),
            **{self.slug_field: self.request.user.username}
        )

    def test_func(self):
        return self.request.user.username == self.get_object().username

    def get_success_url(self):
        return reverse(
            'blog:profile',
            args=[self.request.user.username,]
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
        return reverse(
            'blog:profile',
            args=[self.request.user.username, ]
        )


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    def get_object(self, queryset=None):
        post_id = self.kwargs.get(self.pk_url_kwarg)
        post_object = get_object_or_404(Post, id=post_id)
        if self.request.user == post_object.author:
            return post_object
        if post_object == get_object_or_404(
            posts_filter(Post.objects),
            id=post_id
        ):
            return post_object
        raise Http404("404")

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

    # def get_object(self, queryset=None):
    #     post_id = self.kwargs.get(self.pk_url_kwarg)
    #     post_object = get_object_or_404(Post, id=post_id)
    #     if self.request.user == post_object.author:
    #         return post_object
    #     if post_object == get_object_or_404(
    #         posts_filter(Post.objects),
    #         id=post_id
    #     ):
    #         return post_object
    #     raise Http404("404")


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
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.object.post.id},
        )


class EditCommentView(LoginRequiredMixin, AuthorTestsMixin, UpdateView):
    model = Comment
    pk_url_kwarg = 'comment_id'
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            args=[self.get_object().post.id, ]
        )


class DeleteCommentView(LoginRequiredMixin, AuthorTestsMixin, DeleteView):
    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def test_func(self):
        return self.request.user == self.get_object().author

    def handle_no_permission(self):
        return redirect(
            reverse(
                'blog:post_detail',
                args=[self.get_object().post.id, ]
            ))

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            args=[self.get_object().post.id, ]
        )


def logout_view(request):
    logout(request)
    return redirect(reverse('blog:index'))
