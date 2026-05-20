from django.http import HttpResponse


def ticket_home(request):
    return HttpResponse(
        "Ticket Audit Module Running ✅"
    )