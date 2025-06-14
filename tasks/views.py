from django.shortcuts import render
from django.contrib.auth.forms import UserCreationForm

def home(request):
    return render(request, 'index.html')
    
def signup(request):
    return render(request, 'signup.html', {
        'form': UserCreationForm
    })
