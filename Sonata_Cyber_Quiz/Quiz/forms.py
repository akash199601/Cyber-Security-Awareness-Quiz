
from django import forms


class CandidateForm(forms.Form):
    employee_id = forms.CharField(label="Employee ID", max_length=6, required=True,  widget=forms.TextInput(attrs={'class': 'form-control','id':'emp_id'}))
    password = forms.CharField(label="Enter Your Password", max_length=20, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))

class QuizForm(forms.Form):
    def __init__(self, *args, **kwargs):
        questions = kwargs.pop('questions', None)
        super().__init__(*args, **kwargs)
        
        if questions:
            for question in questions:
                options = question.options.all()
                choices = [(option.id, option.option_text) for option in options]
                self.fields[f'question_{question.id}'] = forms.ChoiceField(
                    choices=choices,
                    widget=forms.RadioSelect,
                    label=question.question_text
                )
                
                

class CheckStatusForm(forms.Form):
    employee_id = forms.CharField(max_length=50, label="Employee ID")
    name = forms.CharField(max_length=100, label="Name")
