from clients.models import Client

class ClientMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        domain = request.get_host()
        try:
            request.client = Client.objects.get(domain=domain)
        except Client.DoesNotExist:
            request.client = None
        response = self.get_response(request)
        return response