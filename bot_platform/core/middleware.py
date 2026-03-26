# core/middleware.py

from django.http import JsonResponse
from communication.models import Bot


class ApiKeyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path.startswith("/api/"):
            return self.get_response(request)

        api_key = request.headers.get("X-API-KEY")
        if not api_key:
            return JsonResponse({"error": "missing api key"}, status=401)

        try:
            bot = Bot.objects.select_related("company").get(
                api_key=api_key,
                is_active=True,
            )
        except Bot.DoesNotExist:
            return JsonResponse({"error": "invalid api key"}, status=401)

        request.bot = bot
        request.company = bot.company

        return self.get_response(request)