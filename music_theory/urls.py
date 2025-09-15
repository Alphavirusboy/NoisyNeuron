from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'instruments', views.InstrumentViewSet)
router.register(r'chords', views.ChordViewSet)
router.register(r'songs', views.SongViewSet)
router.register(r'practice', views.PracticeViewSet, basename='practice')
router.register(r'learning-paths', views.LearningPathViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('chord-recommendations/', views.ChordRecommendationView.as_view(), name='chord-recommendations'),
    path('key-detection/', views.KeyDetectionView.as_view(), name='key-detection'),
    path('progress/', views.ProgressTrackingView.as_view(), name='progress-tracking'),
]
