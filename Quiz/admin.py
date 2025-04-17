from django.contrib import admin
from .models import Candidate, Question, Option, QuizResult

admin.site.register(Candidate)
admin.site.register(Question)
admin.site.register(Option)
admin.site.register(QuizResult)
