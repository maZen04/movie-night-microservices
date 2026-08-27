from django.urls import path
from . import views

urlpatterns = [
    path('sessions', views.CreateSessionView.as_view(), name='create-session'),
    path('sessions/join', views.JoinSessionView.as_view(), name='join-session'),
    path('sessions/<int:session_id>/start', views.StartSessionView.as_view(), name='start-session'),
    path('sessions/<int:session_id>/end', views.EndSessionView.as_view(), name='end-session'),
    path('sessions/<int:session_id>', views.SessionDetailView.as_view(), name='session-members'),
]