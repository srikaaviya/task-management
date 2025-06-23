from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Task
from .forms import TaskForm


def home(request):
    return render(request, 'index.html')

def dashboard(request):
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
            new_task = form.save(commit=False)
            new_task.user = request.user
            new_task.save()
            return redirect('tasks')
        else:
            messages.error(request, 'Please, correct errors in the form')
    else:
        form = TaskForm()
    
    return render(request, 'tasks.html', {
        'form': form,
    })
    
@login_required
def task_details(request, id):
    if request.method == "POST":
        task = get_object_or_404(Task, pk=id, user=request.user)
        form = TaskForm(request.POST, instance=task)
        form.save()
        return redirect('tasks')
    else:
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
            task.updated_at = timezone.now()
            form.save()
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
        task.delete()
        return redirect('tasks')
            


