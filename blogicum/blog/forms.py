from django import forms
from django.contrib.auth import get_user_model

from .models import Comment, Post, User


class UserForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        fields = (
            'title',
            'text',
            'location',
            'category',
            'pub_date',
            'image',
            'is_published',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['pub_date'].widget = forms.DateTimeInput(attrs={
            'type': 'datetime-local',
        })


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ('text',)
