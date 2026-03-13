from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def dashboard(request):
    client = request.client
    return render(request, 'cms/dashboard.html', {'client': client})
