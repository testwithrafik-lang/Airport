from django.urls import path

from .views import ProjectAssistantAskView

urlpatterns = [
    path("ask/", ProjectAssistantAskView.as_view(), name="assistant_ask"),
]

