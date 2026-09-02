from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.db.models import Avg, Count, Q
from django.utils import timezone
from django.conf import settings
from datetime import datetime

from .models import (
    UserProfile, Category, Tag, Project, ProjectImage,
    Donation, Rating, Comment, ProjectReport, CommentReport
)
from .tokens import account_activation_token
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from google import genai
from google.genai import types

# ==================== AUTHENTICATION VIEWS ====================

def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        phone = request.POST.get('phone', '').strip()
        profile_picture = request.FILES.get('profile_picture')

        # التحقق من البيانات
        if password != confirm_password:
            messages.error(request, "كلمتا المرور غير متطابقتين.")
            return render(request, 'donations/register.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, "هذا البريد الإلكتروني مسجل بالفعل.")
            return render(request, 'donations/register.html')

        if UserProfile.objects.filter(phone=phone).exists():
            messages.error(request, "رقم الهاتف هذا مسجل بالفعل.")
            return render(request, 'donations/register.html')

        try:
            # إنشاء المستخدم (غير مفعّل حتى يضغط على الرابط)
            username = email.split('@')[0] + "_" + str(int(datetime.now().timestamp()))
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                is_active=False
            )

            profile = UserProfile.objects.create(
                user=user,
                phone=phone,
                profile_picture=profile_picture if profile_picture else 'profiles/default.png'
            )

            # إعداد رابط التفعيل
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = account_activation_token.make_token(user)
            activation_link = request.build_absolute_uri(f"/activate/{uid}/{token}/")

            print("\n" + "=" * 60)
            print(">>> ACCOUNT ACTIVATION LINK (VALID FOR 24 HOURS):")
            print(f">>> {activation_link}")
            print("=" * 60 + "\n")

            subject = "Activate Your Sanad Account"
            message = (
                f"Hello {first_name},\n\n"
                f"Please click the link below to verify your email and activate your account:\n"
                f"{activation_link}\n\n"
                f"Note: This link will expire in 24 hours.\n\n"
                f"Regards,\nSanad Team"
            )

            # الإرسال عبر إيميل الـ Settings الحقيقي
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False
            )

            messages.success(request, "تم إنشاء الحساب بنجاح! تم إرسال رابط التفعيل إلى بريدك الإلكتروني.")
            return redirect('login')
        except Exception as e:
            messages.error(request, f"حدث خطأ أثناء التسجيل: {str(e)}")
            return render(request, 'donations/register.html')

    return render(request, 'donations/register.html')


def activate_account(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and account_activation_token.check_token(user, token):
        user.is_active = True
        user.profile.is_email_verified = True
        user.save()
        user.profile.save()
        messages.success(request, "تم تفعيل حسابك بنجاح! يمكنك الآن تسجيل الدخول.")
        return redirect('login')
    else:
        messages.error(request, "رابط التفعيل غير صالح أو انتهت صلاحيته (24 ساعة).")
        return redirect('register')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password')

        try:
            user_obj = User.objects.get(email=email)
            if not user_obj.is_active or not getattr(user_obj, 'profile', None) or not user_obj.profile.is_email_verified:
                messages.error(request, "هذا الحساب لم يتم تفعيله بعد. يرجى مراجعة بريدك الإلكتروني.")
                return render(request, 'donations/login.html')

            user = authenticate(request, username=user_obj.username, password=password)
            if user is not None:
                auth_login(request, user)
                return redirect('home')
            else:
                messages.error(request, "كلمة المرور غير صحيحة.")
        except User.DoesNotExist:
            messages.error(request, "البريد الإلكتروني غير مسجل.")

    return render(request, 'donations/login.html')


@login_required
def logout_view(request):
    auth_logout(request)
    return redirect('home')


# ==================== USER PROFILE VIEWS ====================

@login_required
def profile_view(request):
    user = request.user
    profile, created = UserProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'delete_account':
            password = request.POST.get('password')
            if user.check_password(password):
                user.delete()
                messages.success(request, "تم حذف حسابك نهائياً.")
                return redirect('home')
            else:
                messages.error(request, "كلمة المرور غير صحيحة، لم يتم حذف الحساب.")
                return redirect('profile')

        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.save()

        profile.phone = request.POST.get('phone', profile.phone)
        profile.country = request.POST.get('country', profile.country)
        profile.facebook_profile = request.POST.get('facebook_profile', profile.facebook_profile)
        
        birthdate = request.POST.get('birthdate')
        if birthdate:
            profile.birthdate = birthdate

        if 'profile_picture' in request.FILES:
            profile.profile_picture = request.FILES['profile_picture']

        profile.save()
        messages.success(request, "تم تحديث بياناتك بنجاح.")
        return redirect('profile')

    user_projects = user.projects.all().order_by('-created_at')
    user_donations = user.donations.select_related('project').order_by('-donated_at')

    context = {
        'profile': profile,
        'projects': user_projects,
        'donations': user_donations,
    }
    return render(request, 'donations/dashboard.html', context)


# ==================== HOMEPAGE & DISCOVERY ====================

def home_view(request):
    now = timezone.now()

    running_projects = Project.objects.filter(
        is_cancelled=False,
        start_time__lte=now,
        end_time__gte=now
    ).annotate(avg_rating=Avg('ratings__value')).order_by('-avg_rating')[:5]

    latest_projects = Project.objects.filter(is_cancelled=False).order_by('-created_at')[:5]
    featured_projects = Project.objects.filter(is_featured=True, is_cancelled=False).order_by('-created_at')[:5]
    categories = Category.objects.all()

    context = {
        'running_projects': running_projects,
        'latest_projects': latest_projects,
        'featured_projects': featured_projects,
        'categories': categories,
    }
    return render(request, 'donations/home.html', context)


def category_projects(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    projects = category.projects.filter(is_cancelled=False).order_by('-created_at')
    return render(request, 'donations/search_results.html', {'projects': projects, 'query': category.name})


def search_view(request):
    query = request.GET.get('q', '').strip()
    projects = Project.objects.filter(is_cancelled=False)

    if query:
        projects = projects.filter(
            Q(title__icontains=query) | Q(tags__name__icontains=query)
        ).distinct()

    return render(request, 'donations/search_results.html', {'projects': projects, 'query': query})


# ==================== PROJECT MANAGEMENT ====================

@login_required
def create_project(request):
    categories = Category.objects.all()

    if request.method == 'POST':
        title = request.POST.get('title')
        details = request.POST.get('details')
        category_id = request.POST.get('category')
        total_target = request.POST.get('total_target')
        start_time_str = request.POST.get('start_time')
        end_time_str = request.POST.get('end_time')
        tags_input = request.POST.get('tags', '')
        images = request.FILES.getlist('images')

        if start_time_str and end_time_str:
            if start_time_str >= end_time_str:
                messages.error(request, "تاريخ ووقت النهاية يجب أن يكون بعد تاريخ ووقت البداية.")
                return render(request, 'donations/create_project.html', {'categories': categories})

        category = get_object_or_404(Category, id=category_id)

        project = Project.objects.create(
            user=request.user,
            title=title,
            details=details,
            category=category,
            total_target=total_target,
            start_time=start_time_str,
            end_time=end_time_str,
        )

        tag_names = [t.strip().lstrip('#') for t in tags_input.split(',') if t.strip()]
        for name in tag_names:
            tag, _ = Tag.objects.get_or_create(name=name.lower())
            project.tags.add(tag)

        for img in images:
            ProjectImage.objects.create(project=project, image=img)

        messages.success(request, "تم إنشاء المشروع بنجاح!")
        return redirect('project_detail', project_id=project.id)

    return render(request, 'donations/create_project.html', {'categories': categories})


def project_detail(request, project_id):
    project = get_object_or_404(Project, id=project_id)

    project_tags = project.tags.all()
    similar_projects = Project.objects.filter(
        tags__in=project_tags,
        is_cancelled=False
    ).exclude(id=project.id).annotate(
        same_tags=Count('tags')
    ).order_by('-same_tags', '-created_at')[:4]

    comments = project.comments.filter(parent=None).order_by('-created_at')

    user_rating = None
    if request.user.is_authenticated:
        rating_obj = Rating.objects.filter(project=project, user=request.user).first()
        if rating_obj:
            user_rating = rating_obj.value

    context = {
        'project': project,
        'similar_projects': similar_projects,
        'comments': comments,
        'user_rating': user_rating,
    }
    return render(request, 'donations/project_detail.html', context)


@login_required
def donate_view(request, project_id):
    project = get_object_or_404(Project, id=project_id)

    if project.is_cancelled:
        messages.error(request, "هذا المشروع تم إلغاؤه.")
        return redirect('project_detail', project_id=project.id)

    if request.method == 'POST':
        try:
            amount = float(request.POST.get('amount', 0))
            if amount <= 0:
                messages.error(request, "يرجى إدخال مبلغ صحيح أكبر من 0.")
            else:
                Donation.objects.create(user=request.user, project=project, amount=amount)
                messages.success(request, f"شكراً لك! تم التبرع بمبلغ {amount} ج.م بنجاح.")
        except ValueError:
            messages.error(request, "يرجى كتابة رقم صحيح للمبلغ.")

    return redirect('project_detail', project_id=project.id)


@login_required
def rate_project(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if request.method == 'POST':
        value = int(request.POST.get('rating', 5))
        if 1 <= value <= 5:
            Rating.objects.update_or_create(
                user=request.user, project=project,
                defaults={'value': value}
            )
            messages.success(request, "تم تسجيل تقييمك بنجاح.")
    return redirect('project_detail', project_id=project.id)


@login_required
def add_comment(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        parent_id = request.POST.get('parent_id')
        parent_comment = None

        if parent_id:
            parent_comment = Comment.objects.filter(id=parent_id, project=project).first()

        if content:
            Comment.objects.create(
                user=request.user,
                project=project,
                content=content,
                parent=parent_comment
            )
            messages.success(request, "تم نشر تعليقك.")
    return redirect('project_detail', project_id=project.id)


@login_required
def report_project(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if request.method == 'POST':
        reason = request.POST.get('reason', '').strip()
        if reason:
            ProjectReport.objects.create(user=request.user, project=project, reason=reason)
            messages.success(request, "تم إرسال بلاغك وسيتم مراجعته بواسطة الإدارة.")
    return redirect('project_detail', project_id=project.id)


@login_required
def report_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if request.method == 'POST':
        reason = request.POST.get('reason', '').strip()
        if reason:
            CommentReport.objects.create(user=request.user, comment=comment, reason=reason)
            messages.success(request, "تم إرسال البلاغ عن التعليق بنجاح.")
    return redirect('project_detail', project_id=comment.project.id)


@login_required
def cancel_project(request, project_id):
    project = get_object_or_404(Project, id=project_id, user=request.user)

    if project.can_be_cancelled:
        project.is_cancelled = True
        project.save()
        messages.success(request, "تم إلغاء المشروع بنجاح.")
    else:
        messages.error(request, "لا يمكنك إلغاء المشروع لأن التبرعات تجاوزت 25% من الهدف المالي.")

    return redirect('project_detail', project_id=project.id)


def about_view(request):
    return render(request, 'donations/about.html')


def contact_view(request):
    return render(request, 'donations/contact.html')

@csrf_exempt
def chatbot_api(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
        user_message = data.get('message', '').strip()

        if not user_message:
            return JsonResponse({'reply': 'من فضلك اكتب سؤالك أو استفسارك.'})

        # التأكد من وجود مفتاح الـ API
        api_key = getattr(settings, 'GEMINI_API_KEY', '').strip()
        if not api_key:
            return JsonResponse({'reply': 'تنبيه: لم يتم ضبط GEMINI_API_KEY داخل settings.py.'})

        # جمع المشاريع النشطة
        active_projects = Project.objects.filter(is_cancelled=False)[:5]
        projects_summary = "\n".join([
            f"- {p.title} (الهدف: {p.total_target} ج.م، تم جمع: {p.current_donations} ج.م، التصنيف: {p.category.name})"
            for p in active_projects
        ])

        system_prompt = f"""
أنت المساعد الذكي الرسمي لمنصة "سند" (Sanad) لدعم وتمويل المشاريع المجتمعية والتنموية في مصر.
مهامك:
1. الإجابة باحترافية وباللغة العربية المبسطة.
2. توضيح شروط المنصة:
   - التبرع متاح للجميع بحد أدنى 5 جنيهات.
   - يمكن لصاحب المشروع إلغاء حملته فقط إذا كانت التبرعات المجمعة أقل من 25% من الهدف المالي.
   - التسجيل يتطلب تأكيد البريد الإلكتروني عبر رابط صالح لمدة 24 ساعة.
3. المساعدة في التوصية بالمشاريع المتاحة حالياً على المنصة إذا طلب المستخدم:
{projects_summary}

كن ودوداً، مختصراً، وداعماً دائماً لعمل الخير.
"""

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.7,
            )
        )

        bot_reply = response.text if response.text else "عذراً، لم أستطع معالجة الإجابة حالياً."
        return JsonResponse({'reply': bot_reply})

    except Exception as e:
        print(f"\n[CHATBOT EXCEPTION]: {str(e)}\n")
        return JsonResponse({'reply': f"خطأ تقني: {str(e)}"}, status=200)