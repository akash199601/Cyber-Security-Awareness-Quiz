
from django import forms


class CandidateForm(forms.Form):
    employee_id = forms.CharField(label="Employee ID", max_length=50, required=True,  widget=forms.TextInput(attrs={'class': 'form-control'}))
    name = forms.CharField(label="Name", max_length=100, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    

# class QuizForm(forms.Form):
#     def __init__(self, *args, **kwargs):
#         questions = kwargs.pop('questions', None)
#         super().__init__(*args, **kwargs)
        
#         if questions:
#             for question in questions:
#                 self.fields[f'question_{question.id}'] = forms.ChoiceField(
#                     label=question.question_text,
#                     choices=[(option.id, option.option_text) for option in question.options.all()],
#                     widget=forms.RadioSelect
#                 )

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