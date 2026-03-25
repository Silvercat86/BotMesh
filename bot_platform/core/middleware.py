from django.conf import settings
from django.http import JsonResponse


class ApiKeyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/api/"):
            api_key = request.headers.get("X-API-KEY")

            if api_key != settings.BOT_API_KEY:
                return JsonResponse({"error": "unauthorized"}, status=401)

        return self.get_response(request)
    

