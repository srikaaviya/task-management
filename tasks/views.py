"""
Django views for task management application.

This module contains all the view functions for handling user authentication,
task CRUD operations, and dashboard functionality. It includes comprehensive
error handling and user feedback through Django messages framework.
"""

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
    """
    Render the home page.
    
    Args:
        request: HTTP request object
        
    Returns:
        HttpResponse: Rendered index.html template
    """
    return render(request, 'index.html')

def dashboard(request):
    """
    Render the dashboard with task statistics and recent tasks.
    
    For authenticated users, displays aggregated task statistics by status
    and the 5 most recent tasks. For anonymous users, displays basic dashboard.
    
    Args:
        request: HTTP request object
        
    Returns:
        HttpResponse: Rendered dashboard.html template with context data
    """
    if request.user.is_authenticated:
        # Aggregate task statistics by status for the current user
        stats = Task.objects.filter(user=request.user).aggregate(
            total=Count('id'),
            pending=Count('id', filter=Q(status='pending')),
            in_progress=Count('id', filter=Q(status='in_progress')),
            completed=Count('id', filter=Q(status='completed'))
        )
        
        # Get the 5 most recent tasks for quick overview
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
    """
    Handle user registration.
    
    On GET: Display empty registration form
    On POST: Validate form, create user, log them in, and redirect to dashboard
    
    Args:
        request: HTTP request object
        
    Returns:
        HttpResponse: Rendered signup.html template or redirect to dashboard
    """
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
    """
    Handle user authentication.
    
    On GET: Display empty login form
    On POST: Validate credentials, log user in, and redirect to dashboard
    
    Args:
        request: HTTP request object
        
    Returns:
        HttpResponse: Rendered signin.html template or redirect to dashboard
    """
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
    """
    Log out the current user and redirect to home page.
    
    Args:
        request: HTTP request object
        
    Returns:
        HttpResponseRedirect: Redirect to home page
    """
    logout(request)
    return redirect('home')

@login_required
def tasks(request):
    """
    Display filtered and paginated list of user's tasks.
    
    Supports filtering by title, status, and priority, with sorting options.
    Results are paginated with 6 tasks per page.
    
    Query Parameters:
        title (str): Filter tasks by title (case-insensitive partial match)
        status (str): Filter by task status ('pending', 'in_progress', 'completed')
        priority (str): Filter by priority level ('low', 'medium', 'high')
        order_by (str): Sort order ('-created_at', 'created_at', 'priority', '-priority', 'title')
        page (int): Page number for pagination
    
    Args:
        request: HTTP request object
        
    Returns:
        HttpResponse: Rendered tasks.html template with filtered tasks and form
    """
    # Extract all URL parameters with default values
    title = request.GET.get('title', '')
    status = request.GET.get('status', 'default')
    priority = request.GET.get('priority', 'default')
    order_by = request.GET.get('order_by', '-created_at')
    
    # Validate sorting parameter to prevent injection
    valid_orders = ['-created_at', 'created_at', 'priority', '-priority', 'title']
    if order_by not in valid_orders:
        order_by = '-created_at'
    
    # Start with all user's tasks
    tasks_list = Task.objects.filter(user=request.user)
    
    # Apply filters only if they have valid values
    if title:
        tasks_list = tasks_list.filter(title__icontains=title)
        
    if status != 'default' and status:
        tasks_list = tasks_list.filter(status=status)
        
    if priority != 'default' and priority:
        tasks_list = tasks_list.filter(priority=priority)
    
    # Apply sorting
    tasks_list = tasks_list.order_by(order_by)
    
    # Paginate results (6 tasks per page)
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
    """
    Create a new task for the authenticated user.
    
    On GET: Display empty task creation form
    On POST: Validate form data, create task, and redirect to tasks list
    
    Validates that the title field is not empty and handles various database
    errors with appropriate user feedback.
    
    Args:
        request: HTTP request object
        
    Returns:
        HttpResponse: Rendered tasks.html template or redirect to tasks list
    """
    if request.method == "POST":
        form = TaskForm(data=request.POST)
        if form.is_valid():
            # Additional validation for empty title
            if not form.cleaned_data.get('title') or not form.cleaned_data['title'].strip():
                messages.error(request, 'Title is required and cannot be empty')
                tasks = Task.objects.filter(user=request.user)
                return render(request, 'tasks.html', {
                    'form': form,
                })
            try:
                # Create task instance without saving to database yet
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
    """
    Display detailed view of a specific task.
    
    Shows a form pre-populated with task data for editing. Only allows access
    to tasks owned by the current user.
    
    Args:
        request: HTTP request object
        id (int): Primary key of the task to display
        
    Returns:
        HttpResponse: Rendered task_details.html template or redirect to tasks list
    """
    if request.method == "GET":
        try:
            # Ensure user can only access their own tasks
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
    """
    Update an existing task.
    
    On GET: Display task details form pre-populated with current data
    On POST: Validate and save changes, then redirect to tasks list
    
    Only allows users to update their own tasks. Includes additional
    validation for empty titles and comprehensive error handling.
    
    Args:
        request: HTTP request object
        id (int): Primary key of the task to update
        
    Returns:
        HttpResponse: Rendered task_details.html template or redirect to tasks list
    """
    if request.method == 'POST':
        try:
            # Ensure user can only update their own tasks
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
            
        # Additional validation for empty title
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
    """
    Delete a task.
    
    Only processes POST requests for security. Ensures users can only
    delete their own tasks. Preserves task title for success message.
    
    Args:
        request: HTTP request object
        id (int): Primary key of the task to delete
        
    Returns:
        HttpResponseRedirect: Redirect to tasks list or task details page
    """
    try:
        # Ensure user can only delete their own tasks
        task = Task.objects.get(pk=id, user=request.user)
    except Task.DoesNotExist:
        messages.error(request, 'Task not found or you do not have permission to access it')
        return redirect('tasks')
    
    if request.method == 'POST':
        try:
            # Store title before deletion for success message
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
    """
    Toggle task status between 'completed' and 'pending'.
    
    Provides a quick way to mark tasks as done or undone without
    going through the full edit form. Returns 404 if task doesn't
    exist or user doesn't have permission.
    
    Args:
        request: HTTP request object
        id (int): Primary key of the task to toggle
        
    Returns:
        HttpResponseRedirect: Redirect to tasks list
    """
    task = get_object_or_404(Task, pk=id, user=request.user)
    # Simple toggle between completed and pending states
    if task.status == 'completed':
        task.status = 'pending'
    else:
        task.status = 'completed'
    task.save()
    return redirect('tasks')

                        
            


