import base64
import json
from pyexpat.errors import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from .forms import CandidateForm, CheckStatusForm, QuizForm
from .models import Division, EmployeeMaster,LoginStatus , Option, Question, Candidate, QuizResult, RegionMaster, SonataUsersKYCData, UnitMaster
from django.utils import timezone
from datetime import timedelta
from django.db import connection, connections
# from .models import *
import pandas as pd
from django.http import HttpResponse
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
            
            # # Get the login status for this employee_id
            # login_status, created = LoginStatus.objects.get_or_create(employee_id=employee_id)

            # # Check if the user is blocked
            # if login_status.status == 'blocked':
            #     # Check if the blocking duration has passed (24 hours)
            #     if timezone.now() - login_status.blocked_at > timedelta(hours=24):
            #         # Unblock the user after 24 hours
            #         login_status.status = 'active'
            #         login_status.failed_attempts = 0
            #         login_status.blocked_at = None
            #         login_status.save()
            #     else:
            #         # If still blocked, return an error message
            #         error = "Your account is blocked. Please try again after 24 hours."
            #         return render(request, 'home.html', {'form': form, 'error': error})

            # Query to match employee_id and password
            with connections['second_db'].cursor() as cursor:
                cursor.execute("""
                    SELECT SI.empId, SI.password, EM.first_name, EM.surname
                    FROM signUp AS SI
                    LEFT JOIN EmployeeMaster AS EM ON SI.empId = EM.employee_id
                    LEFT JOIN [HR].[dbo].[department] AS DP ON EM.DeptID = DP.department_id
                    WHERE SI.empId = %s AND SI.password = %s AND DP.department_id = 29;
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
                    # login_status.failed_attempts = 0
                    # login_status.status = 'active'
                    # login_status.save()
                    
                    # return redirect('start_quiz')
                    return redirect('HR_dashboard')
                # else:
                #     # Increment the failed attempts count
                #     login_status.failed_attempts += 1
                    
                #     # Check if failed attempts exceed the limit
                #     if login_status.failed_attempts >= 3:
                #         login_status.status = 'blocked'
                #         login_status.blocked_at = timezone.now()  # Record when the user is blocked
                #         error = "Your account has been blocked due to too many failed login attempts."
                #     else:
                #         error = "Invalid Employee ID or Password. Please try again."
                    
                #     # Save the login status
                #     login_status.save()
                    
            # Render home with error message
            return render(request, 'home.html', {'form': form})

    else:
        form = CandidateForm()
    return render(request, 'home.html', {'form': form})

def get_regions(request):
    divisional_id = request.GET.get('divisionalid')
    regions = list(RegionMaster.objects.using('second_db').filter(divisionalid=divisional_id).values('regionid', 'regionname'))
    print('regions-----------',regions)
    return JsonResponse({'regions': regions})

def get_units(request):
    region_id = request.GET.get('regionid')
    units = list(UnitMaster.objects.using('second_db').filter(regionid=region_id).values('unitid', 'unitname'))
    print('units-----------',units)
    return JsonResponse({'units': units})

def get_emp(request):
    unit_id = request.GET.get('unitid')
    print('unitid:', unit_id)  # Debugging

    if unit_id:
        employees = list(EmployeeMaster.objects.using('second_db').filter(UnitID=unit_id).values_list('employee_id', flat=True))
    else:
        employees = list(EmployeeMaster.objects.using('second_db').values_list('employee_id', flat=True))

    # Fetch only basic employee details (No images)
    employee_details = list(SonataUsersKYCData.objects.filter(EmpID__in=employees, IsProcessed=0,IsActive=1).values(
        'EmpID', 'DOB', 'MobileNo', 'AdhaarNo', 'PAN_Number'
    ))

    return JsonResponse({'employee_details': employee_details}, safe=False)

def get_emp_images(request):
    emp_id = request.GET.get('empid')
    print('emp_id',emp_id)
    
    if not emp_id:
        return JsonResponse({'error': 'EmpID is required'}, status=400)

    try:
        emp = SonataUsersKYCData.objects.get(EmpID=emp_id, IsProcessed=0,IsActive = 1)
        print('emp--------',emp)
        print("Fetching images for EmpID:", emp_id)
        # print("Aadhaar Front:", emp.AdhaarFrontImg is not None)
        # print("Aadhaar Back:", emp.AdhaarBackImg is not None)
        # print("PAN Image:", emp.PAN_Img is not None)
        
        images = {
            'AdhaarFrontImg': convert_binary_to_base64(emp.AdhaarFrontImg),
            'AdhaarBackImg': convert_binary_to_base64(emp.AdhaarBackImg),
            'PAN_Img': convert_binary_to_base64(emp.PAN_Img),
            'Photo': convert_binary_to_base64(emp.Photo),
        }
        
        print(f"✅ Images found for EmpID {emp_id}: {images}")  # Debugging output

    except SonataUsersKYCData.DoesNotExist:
        images = {'error': 'Employee not found'}

    return JsonResponse(images)

# 🔹 Function to Convert Binary to Base64
def convert_binary_to_base64(binary_data):
    if binary_data:
        return "data:image/png;base64," + base64.b64encode(binary_data).decode('utf-8')
    return None


# def get_emp(request):
#     unit_id = request.GET.get('unitid')
#     print('unitiddddddddddddddddddddd',unit_id)  # Debugging
    
#     if unit_id:
#         employees = list(EmployeeMaster.objects.using('second_db').filter(UnitID=unit_id).values_list('employee_id',flat=True))
#         # print('employees-----------',employees)
#         print('Employee IDs:', list(employees)) 
#     else:
#         print('No unitid provided, fetching all employees')
#         employees = list(EmployeeMaster.objects.using('second_db').values_list('employee_id', flat=True))  # Fetch all employees if no filter
        
#         # print('Employee IDs:', list(employees))
    
#     employee_details = list(SonataUsersKYCData.objects.filter(EmpID__in=employees,IsProcessed=0).values('EmpID','DOB','MobileNo','AdhaarNo','PAN_Number'))  # Convert QuerySet to List
#     # print('Filtered Employee Details:', employee_details)  # Debugging
#     return JsonResponse({'employee_details': employee_details}, safe=False)

def HR_dashboard(request):
     
    divisions = Division.objects.using('second_db').all()
    # emp = SonataUsersKYCData.objects.all()
    return render(request,'KYC.html', {'divisions': divisions})

def get_completed_employees(request):
    employees = list(SonataUsersKYCData.objects.filter(IsProcessed=1).values('EmpID', 'DOB', 'MobileNo', 'AdhaarNo', 'PAN_Number'))  
    print('completed-emp-----',employees)
    return JsonResponse({"employees": employees})

def update_is_processed(request):
    if request.method == "POST":
        emp_id = request.POST.get("emp_id")
        
        try:
            emp = SonataUsersKYCData.objects.get(EmpID=emp_id)
            emp.IsProcessed = 1  # Update column
            emp.save()
            return JsonResponse({"status": "success", "message": "Updated successfully!"})
        except SonataUsersKYCData.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Employee not found!"})
    
    return JsonResponse({"status": "error", "message": "Invalid request!"})


def reports_view(request):
    return render(request, "reports.html")  # ✅ Create this HTML file


from django.utils.timezone import make_aware
import datetime

def download_reports(request):
    try:
        # ✅ Query Parameters from URL
        report_type = request.GET.get("type")  # 'completed' or 'non_completed'
        start_date = request.GET.get("start")  # e.g., '2025-03-18'
        end_date = request.GET.get("end")      # e.g., '2025-03-19'

        # ✅ Convert Dates to Timezone Aware UTC
        start_date = make_aware(datetime.datetime.strptime(start_date, "%Y-%m-%d"))
        end_date = make_aware(datetime.datetime.strptime(end_date, "%Y-%m-%d")) + datetime.timedelta(days=1)

        # ✅ Filtering Data Based on IsProcessed
        filter_kwargs = {
            "IsProcessed": 1 if report_type == "completed" else 0,
            "RecievedDate__gte": start_date,
            "RecievedDate__lt": end_date
        }

        queryset = SonataUsersKYCData.objects.filter(**filter_kwargs).values(
            "EmpID", "MobileNo", "AdhaarNo", "PAN_Number", "IsActive", "IsProcessed"
        )

        # ✅ Convert Queryset to DataFrame
        df = pd.DataFrame(list(queryset))

        # ✅ Ensure only required columns are present
        required_columns = ["EmpID", "MobileNo", "AdhaarNo", "PAN_Number", "IsActive", "IsProcessed"]
        df = df[required_columns]  # Drop any extra columns if present

        # ✅ Timezone Issue Fix - Remove Timezone from Datetime Fields
        if "RecievedDate" in df.columns:
            df["RecievedDate"] = df["RecievedDate"].dt.tz_localize(None)

        # ✅ Response as Excel File
        response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = f'attachment; filename="{report_type}_KYC_Report.xlsx"'

        # ✅ Save to Excel
        df.to_excel(response, index=False)

        return response

    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=500)


def run_stored_procedure(request):
    with connection.cursor() as cursor:
        try:
            cursor.execute("""exec Sp_GET_KYC_DATA;""")
            print("✅ Stored Procedure executed successfully")  # Log in console
        except Exception as e:
            print(f"❌ Error executing SP: {str(e)}")  # Error logging
    return HttpResponse(status=204) 

# def Logout(request):
#     Logout(request)
#     return redirect('/')

# def download_reports(request):
#     try:
#         # ✅ Query Parameters from URL
#         report_type = request.GET.get("type")  # 'completed' ya 'non_completed'
#         start_date = request.GET.get("start")  # e.g., '2025-03-18'
#         end_date = request.GET.get("end")      # e.g., '2025-03-19'

#         # ✅ Convert Dates to Timezone Aware UTC
#         start_date = make_aware(datetime.datetime.strptime(start_date, "%Y-%m-%d"))
#         end_date = make_aware(datetime.datetime.strptime(end_date, "%Y-%m-%d")) + datetime.timedelta(days=1)

#         # ✅ Filtering Data Based on IsProcessed
#         if report_type == "completed":
#             queryset = SonataUsersKYCData.objects.filter(IsProcessed=1, RecievedDate__gte=start_date, RecievedDate__lt=end_date).values('EmpID','MobileNo','AdhaarNo','PAN_Number','IsActive','IsProcessed')
#         else:
#             queryset = SonataUsersKYCData.objects.filter(IsProcessed=0, RecievedDate__gte=start_date, RecievedDate__lt=end_date).values('EmpID','MobileNo','AdhaarNo','PAN_Number','IsActive','IsProcessed')

#         # ✅ Debugging Print (Remove Later)
#         print(f"Total Records Found: {queryset.count()}")
        
#         # ✅ Convert Queryset to DataFrame
#         df = pd.DataFrame(list(queryset.values()))
        
#         # ✅ Timezone Issue Fix - Remove Timezone from Datetime Fields
#         if not df.empty:
#             df["RecievedDate"] = df["RecievedDate"].dt.tz_localize(None)

#         # ✅ Response as Excel File
#         response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
#         response["Content-Disposition"] = f'attachment; filename="{report_type}_KYC_Report.xlsx"'

#         # ✅ Save to Excel
#         df.to_excel(response, index=False)

#         return response
    
#     except Exception as e:
#         return HttpResponse(f"Error: {str(e)}", status=500)










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

  
        try:
            quiz_result = QuizResult.objects.get(candidate_id=candidate.id,section=section)
            quiz_result.score = score
            quiz_result.total_questions = total_questions
            quiz_result.wrong_answers = wrong_answers
            quiz_result.details = details  # Store details as JSON or text
            quiz_result.retest += 1
            is_retest = True# Increment retest counter
            quiz_result.section_complete = 1 
            quiz_result.section = section
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
                retest=1,
                section = section,
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



