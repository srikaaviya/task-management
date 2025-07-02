from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.db.models import ProtectedError, Count, Q
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
import logging
from .models import Task
from .forms import TaskForm

logger = logging.getLogger(__name__)

def home(request):
    return render(request, 'index.html')

def dashboard(request):
    if request.user.is_authenticated:

        stats = Task.objects.filter(user=request.user).aggregate(
            total=Count('id'),
            pending=Count('id', filter=Q(status='pending')),
            in_progress=Count('id', filter=Q(status='in_progress')),
            completed=Count('id', filter=Q(status='completed'))
        )
        
        # solo las tareas recientes necesarias
        recent_tasks = Task.objects.filter(user=request.user).order_by('-created_at')[:5]
        
        return render(request, 'dashboard.html', {
            'total_tasks': stats['total'],
            'pending_tasks': stats['pending'],
            'in_progress_tasks': stats['in_progress'],
            'completed_tasks': stats['completed'],
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
    # Obtener todos los parámetros de la URL
    title = request.GET.get('title', '')
    status = request.GET.get('status', 'default')
    priority = request.GET.get('priority', 'default')
    order_by = request.GET.get('order_by', '-created_at')
    
    # Validar ordenamiento
    valid_orders = ['-created_at', 'created_at', 'priority', '-priority', 'title']
    if order_by not in valid_orders:
        order_by = '-created_at'
    
    # Comenzar con todas las tareas del usuario
    tasks_list = Task.objects.filter(user=request.user)
    
    # Aplicar filtros solo si tienen valores válidos
    if title:
        tasks_list = tasks_list.filter(title__icontains=title)
        
    if status != 'default' and status:
        tasks_list = tasks_list.filter(status=status)
        
    if priority != 'default' and priority:
        tasks_list = tasks_list.filter(priority=priority)
    
    # Aplicar ordenamiento
    tasks_list = tasks_list.order_by(order_by)
    
    # Paginación (6 tareas por página)
    paginator = Paginator(tasks_list, 6)
    page_number = request.GET.get('page')
    tasks = paginator.get_page(page_number)
    
    form = TaskForm()
    return render(request, 'tasks.html', {
        'tasks': tasks,
        'form': form,
        'current_order': order_by,
        'title': title,
        'status': status,
        'priority': priority,
    })
    
@login_required
def create_task(request):
    if request.method == "POST":
        form = TaskForm(data=request.POST)
        if form.is_valid():
            if not form.cleaned_data.get('title') or not form.cleaned_data['title'].strip():
                messages.error(request, 'Title is required and cannot be empty')
                tasks = Task.objects.filter(user=request.user)
                return render(request, 'tasks.html', {
                    'form': form,
                })
            try:
                new_task = form.save(commit=False)
                new_task.user = request.user
                new_task.save()
                messages.success(request, f'Task "{new_task.title}" created successfully!')
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
        try:
            task = Task.objects.get(pk=id, user=request.user)
        except Task.DoesNotExist:
            messages.error(request, 'Task not found or you do not have permission to access it')
            return redirect('tasks')
        form = TaskForm(instance=task)
        return render(request, 'task_details.html', {
            'form': form,
            'task': task
        })
        
@login_required
def update_task(request, id):
    if request.method == 'POST':
        try:
            task = Task.objects.get(pk=id, user=request.user)
        except Task.DoesNotExist:
            messages.error(request, 'Task not found or you do not have permission to access it')
            return redirect('tasks')
        form = TaskForm(request.POST, instance=task)
        
        if not form.is_valid():
            return render(request, 'task_details.html', {
                'task': task,
                'form': form,
            })
            
        if not form.cleaned_data.get('title') or not form.cleaned_data['title'].strip():
            messages.error(request, 'Title is required and cannot be empty')
            return render(request, 'task_details.html', {
                'task': task,
                'form': form,
            })
        try:
            form.save()
            messages.success(request, f'Task updated successfully!')
            return redirect('tasks')
        except IntegrityError:
            messages.error(request, 'An error has ocurred updating the task. Verify the info')
            return redirect('tasks')
        except ValidationError as e:
            messages.error(request, f'Invalid data: {e}')
            return redirect('tasks')
        except Exception as e:
            messages.error(request, 'Unexpected error updating the task')
            logger.error(f'Error in update_task: {str(e)}')
            return redirect('tasks')
    else:
        try:
            task = Task.objects.get(pk=id, user=request.user)
        except Task.DoesNotExist:
            messages.error(request, 'Task not found or you do not have permission to access it')
            return redirect('tasks')
        form = TaskForm(instance=task)
        return render(request, 'task_details.html', {
            'form': form,
            'task': task
        })
        
@login_required
def delete_task(request, id):
    try:
        task = Task.objects.get(pk=id, user=request.user)
    except Task.DoesNotExist:
        messages.error(request, 'Task not found or you do not have permission to access it')
        return redirect('tasks')
    
    if request.method == 'POST':
        try:
            task_title = task.title
            task.delete()
            messages.success(request, f'Task "{task_title}" deleted successfully!')
            return redirect('tasks')
        except IntegrityError:
            messages.error(request, 'An error has occurred deleting the task. Verify the info')  
            return redirect('task_details', id=id)
        except ProtectedError:
            messages.error(request, 'Error deleting task')
            return redirect('task_details', id=id)
        except Exception as e:
            messages.error(request, 'Unexpected error deleting the task')
            logger.error(f'Error in delete_task: {str(e)}')
            return redirect('task_details', id=id)
    else:
        return redirect('task_details', id=id)
        
@login_required
def toggle_task_status(request, id):
    task = get_object_or_404(Task, pk=id, user=request.user)
    if task.status == 'completed':
        task.status = 'pending'
    else:
        task.status = 'completed'
    task.save()
    return redirect('tasks')

                        
            


