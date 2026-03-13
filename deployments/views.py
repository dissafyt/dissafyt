from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

@login_required
def deploy(request):
    if request.method == 'POST':
        # Simulate deployment
        messages.success(request, 'Website deployed successfully!')
        return redirect('cms_dashboard')
    return render(request, 'deployments/deploy.html', {'client': request.client})
