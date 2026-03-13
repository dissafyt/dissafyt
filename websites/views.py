from django.shortcuts import render
from django.http import HttpResponse

def home(request):
    if request.client:
        return render(request, 'barber/index.html', {'client': request.client})
    else:
        return HttpResponse("No client found for this domain")
