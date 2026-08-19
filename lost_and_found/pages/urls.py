from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("items/", views.items, name="items"),
    path("report/", views.report, name="report"),
    path("items/<int:item_id>/", views.detail, name="detail"),
    path("items/<int:item_id>/edit/", views.edit_item, name="edit_item"),
    path("items/<int:item_id>/delete/", views.delete_item, name="delete_item"),
]
