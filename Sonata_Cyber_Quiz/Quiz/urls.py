from django.urls import path
from . import views
from django.conf.urls import handler404, handler500

handler404 = 'Quiz.views.custom_404'
handler500 = 'Quiz.views.custom_500'

urlpatterns = [
    path('', views.home, name='home'),
    path('HR_dashboard/', views.HR_dashboard, name='HR_dashboard'),
    path("reports/", views.reports_view, name="reports"),
    path("download-reports/", views.download_reports, name="download_reports"),
    path("download-excel-reports/", views.download_excel_reports, name="download_excel_reports"),
    path('get-emp-images/', views.get_emp_images, name='get_emp_images'),
    path('run-sp/', views.run_stored_procedure, name='run_stored_procedure'),
    path("verify-document/", views.verify_document, name="verify_document"),
    path('logout/', views.user_logout, name='logout'),
    path('final-submission/', views.final_submission, name='final_submission'),
    
    
    
    
    # path('candidate/', views.candidate_details, name='candidate_details'),
    path('quiz_section/', views.quiz_section, name='quiz_section'),  # Section selection page
    path('start-quiz/<str:section>/', views.start_quiz, name='start_quiz'),
    path('submit-quiz/<str:section>/', views.submit_quiz, name='submit_quiz'),
    # path('quiz_results/', views.quiz_results, name='quiz_results'),
]

