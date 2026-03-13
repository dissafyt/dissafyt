from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from .forms import ClientRegistrationForm

def register(request):
    if request.method == 'POST':
        form = ClientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Account created for {user.username}!')
            return redirect('home')  # or dashboard
    else:
        form = ClientRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})
