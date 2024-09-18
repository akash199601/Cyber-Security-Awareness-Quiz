from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    # path('candidate/', views.candidate_details, name='candidate_details'),
    path('start-quiz/', views.start_quiz, name='start_quiz'),
    path('submit-quiz/', views.submit_quiz, name='submit_quiz'),
    # path('quiz_results/', views.quiz_results, name='quiz_results'),
]

