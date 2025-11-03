from django.urls import path
from . import views
from .views import W2Intelligence, Movies

urlpatterns = [
    path('ping', views.ping, name="ping"),
    path('w2', W2Intelligence.as_view(), name="w2_process"),
    path('w2/<str:job_id>/', W2Intelligence.as_view(), name="w2_response"),
    path('movies', Movies.as_view(), name="movies")
]
