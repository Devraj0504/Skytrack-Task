from django.urls import path
from . import views

urlpatterns = [
    path('', views.login, name='login'),
    path('logout/', views.logout, name='logout'),

    path('dashboard/', views.dashboard_view, name='dashboard'),

    path('projects/', views.create_project, name='create_project'),
    path('projects_view/', views.projects_view, name='projects_view'),

    path('projects/<int:project_id>/tasks/', views.project_tasks_view, name='project_tasks'),

    path('project_tasks/', views.project_spreadsheet, name='project_tasks_page'),
    path('tasks/', views.tasks_list, name='tasks_list'),
    
]
