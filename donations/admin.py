from django.contrib import admin
from .models import (
    UserProfile,
    Category,
    Tag,
    Project,
    ProjectImage,
    Donation,
    Rating,
    Comment,
    ProjectReport,
    CommentReport,
)

class ProjectImageInline(admin.TabularInline):
    model = ProjectImage
    extra = 3

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'user',
        'category',
        'total_target',
        'start_time',
        'end_time',
        'is_featured',
        'is_cancelled',
    )
    list_filter = ('category', 'is_featured', 'is_cancelled', 'created_at')
    search_fields = ('title', 'details', 'user__username')
    inlines = [ProjectImageInline]

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'country', 'is_email_verified')
    search_fields = ('user__username', 'user__email', 'phone')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ('user', 'project', 'amount', 'donated_at')
    list_filter = ('donated_at',)

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'project', 'value')
    list_filter = ('value',)

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'project', 'parent', 'created_at')
    search_fields = ('content', 'user__username')

@admin.register(ProjectReport)
class ProjectReportAdmin(admin.ModelAdmin):
    list_display = ('user', 'project', 'created_at')
    search_fields = ('reason', 'user__username')

@admin.register(CommentReport)
class CommentReportAdmin(admin.ModelAdmin):
    list_display = ('user', 'comment', 'created_at')
    search_fields = ('reason', 'user__username')