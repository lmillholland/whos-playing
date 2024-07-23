from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path('findArtists/', views.find_artists),
]