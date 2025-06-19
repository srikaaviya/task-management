from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('signup/', views.signup, name='signup'),
    path('signin/', views.signin, name='signin'),
    path('signout/', views.signout, name='signout'),
    path('tasks/', views.tasks, name='tasks'),
    path('tasks/create_task', views.create_task, name='create_task'),
    path('tasks/task_details/<int:id>', views.task_details, name='task_details')
]