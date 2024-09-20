from json import __all__
from django.db import models
from django.contrib.postgres.fields import JSONField 

class Candidate(models.Model):
    name = models.CharField(max_length=20)
    employee_id = models.IntegerField()

    def __str__(self):
        return '__all__'

class Question(models.Model):
    question_text = models.CharField(max_length=255)

    def __str__(self):
        return '__all__'

class Option(models.Model):
    question_id = models.IntegerField()
    option_text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return '__all__'

class QuizResult(models.Model):
    candidate_id = models.IntegerField()
    score = models.PositiveIntegerField()
    total_questions = models.PositiveIntegerField()
    wrong_answers = models.PositiveIntegerField()
    date_taken = models.DateTimeField(auto_now_add=True)
    employee_id = models.CharField(max_length=50,null=True)  # Add this field
    details = models.TextField()
    retest = models.IntegerField()
    
    def __str__(self):
        return '__all__'


