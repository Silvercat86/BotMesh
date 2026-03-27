from rest_framework.decorators import api_view
from rest_framework.response import Response

from candidates.services.sync_from_source import sync_from_people_service


@api_view(["POST"])
def sync_employees_view(request):

    result = sync_from_people_service(request.company)

    return Response(result)