from django.utils import timezone


def year(request):
    """Добавляет переменную с текущим годом.
    НЕ ИСПОЛЬЗУЕТСЯ - в шаблонах использован тэг {% now 'Y' %}
    Оставлен для совместимости с pytest от Яндекс.Практикум"""
    return {'year': timezone.now().year}
