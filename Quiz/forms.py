
from django import forms


class CandidateForm(forms.Form):
    employee_id = forms.CharField(label="Employee ID", max_length=6, required=True,  widget=forms.NumberInput(attrs={'class': 'form-control','id':'emp_id','oninput': "if(this.value.length > 6) this.value = this.value.slice(0, 6)"}))
    password = forms.CharField(label="Enter Your Password", max_length=20,required=True, widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}, render_value=False))

    def clean_employee_id(self):
        employee_id = self.cleaned_data['employee_id']
        if len(employee_id) > 6:
            raise forms.ValidationError("Employee ID cannot be more than 6 digits.")
        return employee_id
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
