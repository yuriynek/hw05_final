from django.utils import timezone


def year(request):
    """Добавляет переменную с текущим годом.
    НЕ ИСПОЛЬЗУЕТСЯ - в шаблонах использован тэг {% now 'Y' %} """
    return {'year': timezone.now().year}
