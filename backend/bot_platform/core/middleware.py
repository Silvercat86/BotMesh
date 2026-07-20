from django.http import JsonResponse
from bot_management.models import Bot, BotRunner


class ApiKeyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path.startswith("/api/"):
            return self.get_response(request)

        api_key = request.headers.get("X-API-KEY")
        if not api_key:
            return JsonResponse({"error": "forbidden"}, status=403)

        if request.path == "/api/active_bots/" or request.path.startswith("/api/runner/"):
            try:
                bot_runner = BotRunner.objects.get(
                    api_key=api_key,
                    is_active=True,
                )
            except BotRunner.DoesNotExist:
                return JsonResponse({"error": "forbidden"}, status=403)
            request.bot_runner = bot_runner
            return self.get_response(request)

        try:
            bot = Bot.objects.get(
                api_key=api_key,
                is_active=True,
            )
        except Bot.DoesNotExist:
            return JsonResponse({"error": "forbidden"}, status=403)

        request.bot = bot
        return self.get_response(request)
