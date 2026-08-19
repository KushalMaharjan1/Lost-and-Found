from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from pages import views

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("", include("pages.urls")),
]

# Serve uploaded item photos during development.
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
