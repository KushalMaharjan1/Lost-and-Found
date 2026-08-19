from .views import is_admin


def admin_status(request):
    return {"admin_access": is_admin(request)}
