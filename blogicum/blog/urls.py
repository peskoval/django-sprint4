from django.urls import path

from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.Index.as_view(), name='index'),
    path('posts/create/', views.CreatePost.as_view(), name='create_post'),
    path('posts/<int:post_id>/', views.PostDetailView.as_view(), name='post_detail'),
    path('posts/<int:post_id>/edit/', views.EditPostView.as_view(), name='edit_post'),
    path('posts/<int:post_id>/delete/', views.DeletePostView.as_view(), name='delete_post'),
    path(
        'profile/edit/',
        views.EditProfileView.as_view(),
        name='edit_profile'
    ),
    path(
        'profile/<str:username>/',
        views.UserProfileView.as_view(),
        name='profile'
    ),
    
    path('posts/<int:post_id>/comment/', views.CommentCreateView.as_view(), name='add_comment'),
    path('posts/<post_id>/edit_comment/<comment_id>/', views.EditCommentView.as_view(), name='edit_comment'),
    path('posts/<post_id>/delete_comment/<comment_id>/', views.DeleteCommentView.as_view(), name='delete_comment'),
    path(
        'category/<slug:category_slug>/',
        views.CategoryPosts.as_view(),
        name='category_posts'
    ),
]
