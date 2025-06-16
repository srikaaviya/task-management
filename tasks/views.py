from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.contrib.auth import login, logout


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


