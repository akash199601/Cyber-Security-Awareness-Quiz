import json
from pyexpat.errors import messages
from django.shortcuts import get_object_or_404, render, redirect
from .forms import CandidateForm, CheckStatusForm, QuizForm
from .models import EmployeeMaster,LoginStatus , Option, Question, Candidate, QuizResult
from django.utils import timezone
from datetime import timedelta
from django.db import connections


from django.shortcuts import render

def custom_404(request, exception):
    return render(request, '404.html', status=404)

def custom_500(request):
    return render(request, '500.html', status=500)


def home(request):
    if request.method == 'POST':
        form = CandidateForm(request.POST)
        if form.is_valid():
            employee_id = form.cleaned_data['employee_id']
            password = form.cleaned_data['password']
            
            # Get the login status for this employee_id
            login_status, created = LoginStatus.objects.get_or_create(employee_id=employee_id)

            # Check if the user is blocked
            if login_status.status == 'blocked':
                # Check if the blocking duration has passed (24 hours)
                if timezone.now() - login_status.blocked_at > timedelta(hours=24):
                    # Unblock the user after 24 hours
                    login_status.status = 'active'
                    login_status.failed_attempts = 0
                    login_status.blocked_at = None
                    login_status.save()
                else:
                    # If still blocked, return an error message
                    error = "Your account is blocked. Please try again after 24 hours."
                    return render(request, 'home.html', {'form': form, 'error': error})

            # Query to match employee_id and password
            with connections['employee_master'].cursor() as cursor:
                cursor.execute("""
                    SELECT SI.empId, SI.password, EM.first_name, EM.surname
                    FROM signUp AS SI
                    LEFT JOIN EmployeeMaster AS EM ON SI.empId = EM.employee_id
                    WHERE SI.empId = %s AND SI.password = %s
                """, [employee_id, password])

                result = cursor.fetchone()
                
                # If result is found
                if result:
                    empId = result[0]
                    first_name = result[2]
                    surname = result[3]
                    full_name = first_name +''+ surname
                    print("fullname", full_name)
                    candidate, created = Candidate.objects.get_or_create(
                        name=full_name,
                        employee_id=empId
                    )
                    request.session['candidate_id'] = candidate.id
                    
                    # Reset failed attempts on successful login
                    login_status.failed_attempts = 0
                    login_status.status = 'active'
                    login_status.save()
                    
                    # return redirect('start_quiz')
                    return redirect('quiz_section')
                else:
                    # Increment the failed attempts count
                    login_status.failed_attempts += 1
                    
                    # Check if failed attempts exceed the limit
                    if login_status.failed_attempts >= 3:
                        login_status.status = 'blocked'
                        login_status.blocked_at = timezone.now()  # Record when the user is blocked
                        error = "Your account has been blocked due to too many failed login attempts."
                    else:
                        error = "Invalid Employee ID or Password. Please try again."
                    
                    # Save the login status
                    login_status.save()
                    
            # Render home with error message
            return render(request, 'home.html', {'form': form, 'error': error})

    else:
        form = CandidateForm()
    return render(request, 'home.html', {'form': form})

# def start_quiz(request):
#     if 'candidate_id' not in request.session:
#         return redirect('home')

#     questions = Question.objects.all()
#     return render(request, 'quiz.html', {'questions': questions})

def quiz_section(request):
    if 'candidate_id' not in request.session:
        return redirect('home')

    candidate_id = request.session.get('candidate_id')
  
    # Define available sections with descriptions and video URLs
    sections = {
        'Internet Safety': {
            'description': 'Learn about keeping your information secure online.',
            'video_url': 'https://www.youtube.com/embed/kQVp2VxlRm4'
        },
        'Email Privacy': {
            'description': 'Understand how to protect your email and personal data.',
            'video_url': 'https://www.youtube.com/embed/mtB3EBk1Hpg'
        },
        'General': {
            'description': 'Test your knowledge on general cyber safety practices.',
            'video_url': 'https://www.youtube.com/embed/s7ZjOS_XKmI'
          
        }
    }

    # Create lists to track completed and not completed sections
    completed_sections = []
    not_completed_sections = []

    for section, details in sections.items():
        result = QuizResult.objects.filter(candidate_id=candidate_id, section=section).order_by('-id').first()
        section_data = {
            'name': section,
            'description': details['description'],
            'video_url': details['video_url']
        }
        if result and result.section_complete == 1:
            completed_sections.append({
                **section_data,
                'score': result.score,
                'score_percentage': (result.score / result.total_questions) * 100 if result.total_questions > 0 else 0
            })
        else:
            not_completed_sections.append(section_data)

    return render(request, 'quiz_sections.html', {
        'completed_sections': completed_sections,
        'not_completed_sections': not_completed_sections,
        
    })


# def start_quiz(request):
#     if 'candidate_id' not in request.session:
#         return redirect('home')

#      # Retrieve candidate_id from the session
#     candidate_id = request.session.get('candidate_id')
    
#     # Check if there's a previous quiz result for this candidate
#     try:
#         quiz_result = QuizResult.objects.get(candidate_id=candidate_id)
#         retest_count = quiz_result.retest
#         is_retest = True  # The candidate has taken the quiz before
#     except QuizResult.DoesNotExist:
#         retest_count = 0  # First attempt
#         is_retest = False  # This is the first attempt
#     # Retrieve all questions
#     questions = Question.objects.all()

#     # Retrieve all options related to these questions
#     options = Option.objects.filter(question_id__in=[q.id for q in questions])

#     # Prepare a list of tuples (question, options) for easy iteration in template
#     questions_with_options = [(q, [opt for opt in options if opt.question_id == q.id]) for q in questions]

#     # Pass questions and their options to the template
#     return render(request, 'quiz.html', {'questions_with_options': questions_with_options,'retest_count': retest_count, 'is_retest': is_retest })

def start_quiz(request, section=None):
    if 'candidate_id' not in request.session:
        return redirect('home')

     # Retrieve candidate_id from the session
    candidate_id = request.session.get('candidate_id')
     # Check if there's a previous quiz result for this candidate
    quiz_results = QuizResult.objects.filter(candidate_id=candidate_id)
    # Check if there's a previous quiz result for this candidate
    if quiz_results.exists():
        # Assume the most recent quiz result is the one to use
        quiz_result = quiz_results.latest('date_taken')  # Assuming 'date_taken' field exists to track quiz result date
        retest_count = quiz_result.retest
        is_retest = True  # The candidate has taken the quiz before
    else:
        retest_count = 0  # First attempt
        is_retest = False  # This is the first attempt
    # Retrieve all questions
    # questions = Question.objects.all()
    
    # Fetch questions from the selected section
    questions = Question.objects.filter(section=section)        
    # Retrieve all options related to these questions
    options = Option.objects.filter(question_id__in=[q.id for q in questions])

    # Prepare a list of tuples (question, options) for easy iteration in template
    questions_with_options = [(q, [opt for opt in options if opt.question_id == q.id]) for q in questions]

    # Pass questions and their options to the template
    return render(request, 'quiz.html', {'questions_with_options': questions_with_options,'retest_count': retest_count, 'is_retest': is_retest, 'section': section })


def submit_quiz(request,section):
    if request.method == 'POST':
        
        candidate_id = request.session.get('candidate_id')
        if not candidate_id:
            return redirect('home')

        try:
            candidate = Candidate.objects.get(id=candidate_id)
        except Candidate.DoesNotExist:
            return redirect('home')
            
        questions = Question.objects.filter(section=section)
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
            quiz_result = QuizResult.objects.get(candidate_id=candidate.id,section=section)
            quiz_result.score = score
            quiz_result.total_questions = total_questions
            quiz_result.wrong_answers = wrong_answers
            quiz_result.details = details  # Store details as JSON or text
            quiz_result.retest += 1
            is_retest = True# Increment retest counter
            quiz_result.section_complete = 1 
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
                section_complete = 1,
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
            'is_retest' : is_retest,
            'section' : section,
            
        })

    return redirect('home')



