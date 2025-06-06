from django.http import HttpResponseServerError

def trigger_error(request):
    # Генерируем ошибку 500
    return HttpResponseServerError("This is a test error.")