from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.db.models import Avg, Sum

# التحقق من رقم الموبايل المصري
egyptian_phone_regex = RegexValidator(
    regex=r'^01[0125][0-9]{8}$',
    message="رقم الهاتف يجب أن يكون رقماً مصرياً صحيحاً مكوناً من 11 رقماً ويبدأ بـ 010 أو 011 أو 012 أو 015."
)

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(validators=[egyptian_phone_regex], max_length=11, unique=True)
    profile_picture = models.ImageField(upload_to='profiles/', default='profiles/default.png', blank=True)
    birthdate = models.DateField(null=True, blank=True)
    facebook_profile = models.URLField(max_length=255, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, default='Egypt')
    is_email_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}'s Profile"


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return f"#{self.name}"


class Project(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    title = models.CharField(max_length=200)
    details = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='projects')
    total_target = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(100.0)])
    tags = models.ManyToManyField(Tag, related_name='projects')
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(default=timezone.now)
    is_featured = models.BooleanField(default=False)
    is_cancelled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    @property
    def current_donations(self):
        total = self.donations.aggregate(total=Sum('amount'))['total']
        return total or 0.0

    @property
    def donation_percentage(self):
        if self.total_target > 0:
            return round((float(self.current_donations) / float(self.total_target)) * 100, 2)
        return 0.0

    @property
    def can_be_cancelled(self):
        # شرط الإلغاء: التبرعات تكون أقل من 25% من الهدف
        return (float(self.current_donations) < float(self.total_target) * 0.25) and not self.is_cancelled

    @property
    def average_rating(self):
        avg = self.ratings.aggregate(avg=Avg('value'))['avg']
        return round(avg, 1) if avg else 0.0

    @property
    def is_running(self):
        now = timezone.now()
        return self.start_time <= now <= self.end_time and not self.is_cancelled


class ProjectImage(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='projects/')

    def __str__(self):
        return f"Image for {self.project.title}"


class Donation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='donations')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='donations')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(1.0)])
    donated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} donated {self.amount} EGP to {self.project.title}"


class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='ratings')
    value = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])

    class Meta:
        unique_together = ('user', 'project')

    def __str__(self):
        return f"{self.user.username} - {self.project.title} ({self.value}/5)"


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user.username} on {self.project.title}"


class ProjectReport(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='reports')
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report on {self.project.title} by {self.user.username}"


class CommentReport(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='reports')
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report on Comment #{self.comment.id} by {self.user.username}"