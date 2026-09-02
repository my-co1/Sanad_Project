from django.urls import path
from . import views

urlpatterns = [
    # الرئيسية والتصنيفات والبحث
    path('', views.home_view, name='home'),
    path('about/', views.about_view, name='about'),
    path('contact/', views.contact_view, name='contact'),
    path('category/<int:category_id>/', views.category_projects, name='category_projects'),
    path('search/', views.search_view, name='search'),

    # التوثيق والحسابات
    path('register/', views.register_view, name='register'),
    path('activate/<str:uidb64>/<str:token>/', views.activate_account, name='activate'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.profile_view, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),

    # إدارة المشاريع والتفاعل
    path('project/create/', views.create_project, name='create_project'),
    path('project/<int:project_id>/', views.project_detail, name='project_detail'),
    path('project/<int:project_id>/donate/', views.donate_view, name='donate'),
    path('project/<int:project_id>/rate/', views.rate_project, name='rate_project'),
    path('project/<int:project_id>/comment/', views.add_comment, name='add_comment'),
    path('project/<int:project_id>/report/', views.report_project, name='report_project'),
    path('comment/<int:comment_id>/report/', views.report_comment, name='report_comment'),
    path('project/<int:project_id>/cancel/', views.cancel_project, name='cancel_project'),

    # المساعد الذكي
    path('api/chatbot/', views.chatbot_api, name='chatbot_api'),
    path('ai-chat/', views.chatbot_api, name='ai_chat'),
]