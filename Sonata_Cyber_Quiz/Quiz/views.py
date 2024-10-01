import json
from pyexpat.errors import messages
from django.shortcuts import get_object_or_404, render, redirect
from .forms import CandidateForm, CheckStatusForm, QuizForm
from .models import EmployeeMaster, Option, Question, Candidate, QuizResult
from django.utils import timezone
from datetime import datetime

def home(request):
    error = None
    if request.method == 'POST':
        form = CandidateForm(request.POST)
        if form.is_valid():
            candidate_name = form.cleaned_data['name']
            employee_id = form.cleaned_data['employee_id']
            # Check if the employee exists in the master database
            try:
                employee = EmployeeMaster.objects.using('employee_master').get(employee_id=employee_id)
                
                # If employee exists in the master database, check if they are already in the quiz system

                # Save candidate details
                candidate, created = Candidate.objects.get_or_create(
                name= candidate_name,
                employee_id=employee.employee_id
                )
                request.session['candidate_id'] = candidate.id
            
                return redirect('start_quiz')
            except EmployeeMaster.DoesNotExist:
                # If employee doesn't exist, show an error message
                error = 'User not found. Please enter a valid Employee ID.'
                return render(request, 'home.html', {'form': form, 'error': error})        
    else:
        form = CandidateForm()
    return render(request, 'home.html', {'form': form,'error':error})


# def start_quiz(request):
#     if 'candidate_id' not in request.session:
#         return redirect('home')

#     questions = Question.objects.all()
#     return render(request, 'quiz.html', {'questions': questions})

def start_quiz(request):
    if 'candidate_id' not in request.session:
        return redirect('home')

     # Retrieve candidate_id from the session
    candidate_id = request.session.get('candidate_id')
    
    # Check if there's a previous quiz result for this candidate
    try:
        quiz_result = QuizResult.objects.get(candidate_id=candidate_id)
        retest_count = quiz_result.retest
        is_retest = True  # The candidate has taken the quiz before
    except QuizResult.DoesNotExist:
        retest_count = 0  # First attempt
        is_retest = False  # This is the first attempt
    # Retrieve all questions
    questions = Question.objects.all()

    # Retrieve all options related to these questions
    options = Option.objects.filter(question_id__in=[q.id for q in questions])

    # Prepare a list of tuples (question, options) for easy iteration in template
    questions_with_options = [(q, [opt for opt in options if opt.question_id == q.id]) for q in questions]

    # Pass questions and their options to the template
    return render(request, 'quiz.html', {'questions_with_options': questions_with_options,'retest_count': retest_count, 'is_retest': is_retest })



def submit_quiz(request):
    if request.method == 'POST':
        
        candidate_id = request.session.get('candidate_id')
        if not candidate_id:
            return redirect('home')

        try:
            candidate = Candidate.objects.get(id=candidate_id)
        except Candidate.DoesNotExist:
            return redirect('home')
            
        questions = Question.objects.all()
        correct_answers = 0
        total_questions = 0
        details = []
        is_retest = False
        quiz_result = None  # Initialize quiz_result

        for question in questions:
            total_questions += 1
            selected_option_id = request.POST.get(f'question-{question.id}')
            selected_option = None
            correct_option = None

            if selected_option_id:
                try:
                    selected_option = Option.objects.get(id=selected_option_id, question_id=question.id)
                except Option.DoesNotExist:
                    selected_option = None

            correct_option = Option.objects.filter(question_id=question.id,is_correct=True).first()

            if selected_option and selected_option.is_correct:
                correct_answers += 1

            # Append all options and mark the selected one
            details.append({
                'question': question.question_text,
                'selected_option': selected_option.option_text if selected_option else 'None',
                'options': [
                    {
                        'option_text': option.option_text,
                        'is_selected': (option.id == int(selected_option_id)) if selected_option_id else False,
                        'is_correct': option.is_correct
                    }
                    for option in Option.objects.filter(question_id=question.id)
                ],
                'correct_answer': correct_option.option_text if correct_option else 'None'
            })

        score = correct_answers
        wrong_answers = total_questions - correct_answers
        score_percentage = (score / total_questions) * 100 if total_questions > 0 else 0

        # QuizResult.objects.create(
        #     candidate_id=candidate.id,
        #     score=score,
        #     total_questions=total_questions,
        #     wrong_answers=wrong_answers,
        #     employee_id=candidate.employee_id,
        #     details=details  # Store details as JSON or text
        # )
        
         # Check if a result already exists for this candidate
        try:
            quiz_result = QuizResult.objects.get(candidate_id=candidate.id)
            quiz_result.score = score
            quiz_result.total_questions = total_questions
            quiz_result.wrong_answers = wrong_answers
            quiz_result.details = details  # Store details as JSON or text
            quiz_result.retest += 1
            is_retest = True# Increment retest counter
            quiz_result.save()
        except QuizResult.DoesNotExist:
            # If result doesn't exist, create a new one
            QuizResult.objects.create(
                candidate_id=candidate.id,
                score=score,
                total_questions=total_questions,
                wrong_answers=wrong_answers,
                employee_id=candidate.employee_id,
                details=details,  # Store details as JSON or text
                
                retest=1
            )
            
        request.session.flush()
        # Pass all the details (including all options for each question) to the template
        return render(request, 'quiz_result.html', {
            'score': score,
            'total_questions': total_questions,
            'wrong_answers': wrong_answers,
            'candidate_name': candidate.name,
            'employee_id': candidate.employee_id,
            'score_percentage': score_percentage,
            'details': details,
            'quiz_result' : quiz_result,
            'is_retest' : is_retest 
            
        })

    return redirect('home')



