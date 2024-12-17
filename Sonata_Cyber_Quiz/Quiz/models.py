from json import __all__
from django.db import models


class Candidate(models.Model):
    name = models.CharField(max_length=20)
    employee_id = models.IntegerField()

    def __str__(self):
        return '__all__'

class Question(models.Model):
    question_text = models.CharField(max_length=255)
    section = models.CharField(max_length=50, default='General')
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
    section = models.CharField(max_length=255,null=True)
    section_complete = models.IntegerField(default=0,null=False)
    def __str__(self):
        return '__all__'
    class Meta:
        unique_together = ('candidate_id', 'section') 

class EmployeeMaster(models.Model):
    employee_id = models.IntegerField(primary_key=True)
    first_name = models.CharField(max_length=50)
    surname = models.CharField(max_length=50)

    class Meta:
        db_table = 'EmployeeMaster'  # This should match the actual table name in the master database
        managed = False  # Since Django should not manage the migrations of this table
        
class signUP(models.Model):
    password = models.CharField(max_length=50)
    empId = models.IntegerField()
    class Meta:
        db_table = 'signUP'  # This should match the actual table name in the master database
        managed = False  # Since Django should not manage the migrations of this table
        

class LoginStatus(models.Model):
    employee_id = models.IntegerField(unique=True)
    failed_attempts = models.IntegerField(default=0)
    status = models.CharField(max_length=50, default='active')
    blocked_at = models.DateTimeField(null=True)

    class Meta:
        db_table = 'loginstatus'
    
    def __str__(self):
        return '__all__'
    