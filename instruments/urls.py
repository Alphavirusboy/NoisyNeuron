from django.urls import path
from . import views

app_name = 'instruments'

urlpatterns = [
    path('', views.instrument_list, name='list'),
    path('piano/', views.piano_lessons, name='piano'),
    path('guitar/', views.guitar_lessons, name='guitar'),
    path('drums/', views.drums_lessons, name='drums'),
    path('violin/', views.violin_lessons, name='violin'),
    path('bass/', views.bass_lessons, name='bass'),
    path('saxophone/', views.saxophone_lessons, name='saxophone'),
    path('<str:instrument>/lesson/<int:lesson_id>/', views.lesson_detail, name='lesson_detail'),
    path('<str:instrument>/practice/', views.practice_session, name='practice'),
    path('<str:instrument>/progress/', views.progress_tracking, name='progress'),
]