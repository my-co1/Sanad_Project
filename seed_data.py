import os
import django
from django.utils import timezone
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from donations.models import UserProfile, Category, Tag, Project, ProjectImage, Donation, Rating, Comment

print("بدء حقن البيانات التجريبية...")

# 1. إنشاء مستخدمين
users_data = [
    {"username": "ahmed_ali", "email": "ahmed@example.com", "first": "أحمد", "last": "علي", "phone": "01012345678"},
    {"username": "sara_nour", "email": "sara@example.com", "first": "سارة", "last": "نور", "phone": "01198765432"},
    {"username": "omar_khaled", "email": "omar@example.com", "first": "عمر", "last": "خالد", "phone": "01234567890"},
]

created_users = []
for u in users_data:
    user, created = User.objects.get_or_create(
        username=u["username"],
        email=u["email"],
        defaults={"first_name": u["first"], "last_name": u["last"], "is_active": True}
    )
    if created:
        user.set_password("Password123!")
        user.save()
        UserProfile.objects.create(
            user=user,
            phone=u["phone"],
            country="مصر",
            is_email_verified=True
        )
    created_users.append(user)

# 2. إنشاء التصنيفات
categories_list = ["صحة ورعاية طبية", "تعليم وبحوث", "تكنولوجيا وبرمجيات", "إغاثة وإطعام", "بيئة وتنمية مستدامة"]
created_cats = []
for cat_name in categories_list:
    cat, _ = Category.objects.get_or_create(name=cat_name, defaults={"description": f"مشاريع خاصة بمجال {cat_name}"})
    created_cats.append(cat)

# 3. إنشاء الوسوم Tags
tags_list = ["مصر", "علاج", "أيتام", "ذكاء_اصطناعي", "مدارس", "إطعام", "شباب", "طاقة_شمسية"]
created_tags = {}
for t in tags_list:
    tag, _ = Tag.objects.get_or_create(name=t)
    created_tags[t] = tag

# 4. إنشاء مشاريع
now = timezone.now()
projects_data = [
    {
        "title": "تجهيز وحدة غسيل كلوي في مستشفى قروي",
        "details": "حملة لشراء وتوفير 5 أجهزة غسيل كلوي متطورة لخدمة أهالي القرى الأكثر احتياجاً بالمجان.",
        "category": created_cats[0],
        "target": 350000.0,
        "user": created_users[0],
        "is_featured": True,
        "tags": [created_tags["مصر"], created_tags["علاج"]]
    },
    {
        "title": "معمل حاسب آلي وبرمجة لطلاب المدارس الحكومية",
        "details": "تزويد مدرستين حكوميتين بأجهزة كمبيوتر وشبكة إنترنت لتدريب الطلاب على البرمجة والذكاء الاصطناعي.",
        "category": created_cats[1],
        "target": 180000.0,
        "user": created_users[1],
        "is_featured": True,
        "tags": [created_tags["مدارس"], created_tags["ذكاء_اصطناعي"], created_tags["شباب"]]
    },
    {
        "title": "قافلة إطعام وتوزيع كراتين غذائية في الشتاء",
        "details": "توزيع 2000 كرتونة مواد غذائية أساسية ووجبات ساخنة على الأسر المستحقة والأيتام.",
        "category": created_cats[3],
        "target": 120000.0,
        "user": created_users[2],
        "is_featured": False,
        "tags": [created_tags["إطعام"], created_tags["أيتام"], created_tags["مصر"]]
    },
    {
        "title": "محطة طاقة شمسية لتشغيل آبار مياه الشرب",
        "details": "مشروع لتوفير مياه نظيفة ومستدامة من خلال توليد الكهرباء الشمسية لتشغيل طلمبات الآبار الجوفية.",
        "category": created_cats[4],
        "target": 250000.0,
        "user": created_users[0],
        "is_featured": True,
        "tags": [created_tags["طاقة_شمسية"], created_tags["مصر"]]
    },
    {
        "title": "منصة تعليمية مفتوحة المصدر لتدريب الشباب",
        "details": "بناء منصة تفاعلية مجانية بالكامل لتقديم كورسات تطوير البرمجيات والذكاء الاصطناعي للطلبة.",
        "category": created_cats[2],
        "target": 95000.0,
        "user": created_users[1],
        "is_featured": False,
        "tags": [created_tags["ذكاء_اصطناعي"], created_tags["شباب"]]
    },
]

for p_info in projects_data:
    proj, created = Project.objects.get_or_create(
        title=p_info["title"],
        defaults={
            "user": p_info["user"],
            "details": p_info["details"],
            "category": p_info["category"],
            "total_target": p_info["target"],
            "start_time": now - timedelta(days=5),
            "end_time": now + timedelta(days=45),
            "is_featured": p_info["is_featured"],
        }
    )
    if created:
        proj.tags.set(p_info["tags"])
        
        # تبرعات تجريبية
        Donation.objects.create(user=created_users[2], project=proj, amount=1500.0)
        Donation.objects.create(user=created_users[1], project=proj, amount=3000.0)

        # تقييمات تجريبية
        Rating.objects.create(user=created_users[1], project=proj, value=5)
        Rating.objects.create(user=created_users[2], project=proj, value=4)

        # تعليق ورد
        c1 = Comment.objects.create(user=created_users[1], project=proj, content="مشروع عظيم جداً، بالتوفيق!")
        Comment.objects.create(user=proj.user, project=proj, parent=c1, content="شكراً جزيلاً لدعمكم المستمر.")

print("تمت إضافة البيانات بنجاح تام!")