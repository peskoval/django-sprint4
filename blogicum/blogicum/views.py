from django.http import HttpResponseServerError


def trigger_error(request):
    """Generate a 500 code error."""
    return HttpResponseServerError("This is a test error.")
