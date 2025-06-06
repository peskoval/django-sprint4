from django.contrib import admin

from .models import Category, Location, Post

admin.site.empty_value_display = 'Не задано'


class PostInline(admin.TabularInline):
    model = Post
    extra = 0


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    inlines = (PostInline, )
    list_display = (
        'title',
        'slug',
        'is_published',
        'created_at',
    )
    list_editable = ('is_published', )
    search_fields = ('title', 'slug', )
    list_filter = ('title', 'slug', )
    list_display_links = ('title', )


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_published', 'created_at', )
    list_editable = ('is_published', )
    search_fields = ('name', )
    list_filter = ('name', )
    list_display_links = ('name', )
    inlines = (PostInline, )


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'author',
        'location',
        'category',
        'is_published',
        'created_at',
        'pub_date',
    )
    list_editable = ('is_published', 'pub_date', )
    search_fields = ('title', 'author', )
    list_filter = ('author', 'category', 'location', )
    list_display_links = ('title', )
