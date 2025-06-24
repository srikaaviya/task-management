from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.db.models import ProtectedError
from django.core.exceptions import ValidationError
import logging
from .models import Task
from .forms import TaskForm

logger = logging.getLogger(__name__)

def home(request):
    return render(request, 'index.html')

def dashboard(request):
    if request.user.is_authenticated:
        user_tasks = Task.objects.filter(user=request.user)
        total_tasks = user_tasks.count()
        pending_tasks = user_tasks.filter(status='pending').count()
        in_progress_tasks = user_tasks.filter(status='in_progress').count()
        completed_tasks = user_tasks.filter(status='completed').count()
        recent_tasks = user_tasks.order_by('-created_at')[:5]
        
        return render(request, 'dashboard.html', {
            'total_tasks': total_tasks,
            'pending_tasks': pending_tasks,
            'in_progress_tasks': in_progress_tasks,
            'completed_tasks': completed_tasks,
            'recent_tasks': recent_tasks,
        })
        
    return render(request, 'dashboard.html')
    
def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                login(request, user)
                messages.success(request, 'User created successfully!')
                return redirect('dashboard')
            except Exception as e:
                messages.error(request, f"An error has ocurred: {e}")
        else:
            messages.error(request, 'Please, correct errors in the form')
    else:
        form = UserCreationForm()
        
    return render(request, 'signup.html', {
        'form': form
    })

def signin(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, 'You have logged in successfully!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Username or password incorrect.')
    else:
        form = AuthenticationForm()
        
    return render(request, 'signin.html', {
        'form': form
    })
    
def signout(request):
    logout(request)
    return redirect('home')

@login_required
def tasks(request):
    tasks = Task.objects.filter(user=request.user)
    form = TaskForm()
    return render(request, 'tasks.html', {
        'tasks': tasks,
        'form': form
    })
    
@login_required
def create_task(request):
    if request.method == "POST":
        form = TaskForm(data=request.POST)
        if form.is_valid():
            try:
                new_task = form.save(commit=False)
                new_task.user = request.user
                new_task.save()
                return redirect('tasks')
            except IntegrityError:
                messages.error(request, 'An error has ocurred creating the task. Verify the info')
                return redirect('tasks')
            except ValidationError as e:
                messages.error(request, f'Invalid data: {e}')
                return redirect('tasks')
            except Exception as e:
                messages.error(request, 'Unexpected error creating the task')
                logger.error(f'Error in create_task: {str(e)}')
                return redirect('tasks')
        else:
            messages.error(request, 'Please, correct errors in the form')
            tasks = Task.objects.filter(user=request.user)
            return render(request, 'tasks.html', {
                'tasks': tasks,
                'form': form,
            })
    else:
        form = TaskForm()
        return render(request, 'tasks.html', {
            'form': form,
        })
        
    
@login_required
def task_details(request, id):
    if request.method == "GET":
        task = get_object_or_404(Task, pk=id, user=request.user)
        form = TaskForm(instance=task)
        return render(request, 'task_details.html', {
            'form': form,
            'task': task
        })
        
@login_required
def update_task(request, id):
    if request.method == 'POST':
        task = get_object_or_404(Task, pk=id, user=request.user)
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            try:
                form.save()
                return redirect('tasks')
            except IntegrityError:
                messages.error(request, 'An error has ocurred creating the task. Verify the info')
                return redirect('tasks')
            except ValidationError as e:
                messages.error(request, f'Invalid data: {e}')
                return redirect('tasks')
            except Exception as e:
                messages.error(request, 'Unexpected error creating the task')
                logger.error(f'Error in create_task: {str(e)}')
                return redirect('tasks')
    else:
        task = get_object_or_404(Task, pk=id, user=request.user)
        form = TaskForm(instance=task)
        return render(request, 'task_details.html', {
            'form': form,
            'task': task
        })
        
@login_required
def delete_task(request, id):
    task = get_object_or_404(Task, pk=id, user=request.user)
    if request.method == 'POST':
        try:
            task.delete()
            return redirect('tasks')
        except IntegrityError:
            messages.error(request, 'An error has ocurred creating the task. Verify the info')
            return redirect('tasks_details')
        except ProtectedError:
            messages.error(request, 'Error deleting task')
            return redirect('tasks_details')
        except Exception as e:
            messages.error(request, 'Unexpected error creating the task')
            logger.error(f'Error in create_task: {str(e)}')
            return redirect('tasks_details')
        
@login_required
def filter_tasks(request):
    if request.user.is_authenticated:
        title = request.GET.get('title')
        status = request.GET.get('status')
        priority = request.GET.get('priority')
        tasks = Task.objects.filter(user=request.user)
        if request.method == 'GET':
            if title:
                tasks = tasks.filter(title__icontains=title)
                
            if status != 'default' and status:
                tasks = tasks.filter(status=status)
                
            if priority != 'default' and priority:
                tasks = tasks.filter(priority=priority)
            
            return render(request, 'tasks.html', {
                'tasks': tasks,
                'status': status,
                'priority': priority,
                'title': title,
                'form': TaskForm(),
            })
                        
            


