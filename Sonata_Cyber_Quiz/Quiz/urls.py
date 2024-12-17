from django.urls import path
from . import views
from django.conf.urls import handler404, handler500

handler404 = 'Quiz.views.custom_404'
handler500 = 'Quiz.views.custom_500'

urlpatterns = [
    path('', views.home, name='home'),
    # path('candidate/', views.candidate_details, name='candidate_details'),
    path('quiz_section/', views.quiz_section, name='quiz_section'),  # Section selection page
    path('start-quiz/<str:section>/', views.start_quiz, name='start_quiz'),
    path('submit-quiz/<str:section>/', views.submit_quiz, name='submit_quiz'),
    # path('quiz_results/', views.quiz_results, name='quiz_results'),
]

