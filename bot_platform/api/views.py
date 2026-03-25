
from rest_framework.decorators import api_view
from rest_framework.response import Response






from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(["POST"])
def get_context(request):
    print(request.data)

    user = request.data.get("user")
    chat = request.data.get("chat")
    
    
    if not user or not chat:
        return Response({"error": "user and chat required"}, status=400)

    return Response({"user_id": 1, "role": 1})