from django.http import HttpResponseServerError


def trigger_error(request):
    """Generates 500 code error."""
    return HttpResponseServerError("This is a test error.")
