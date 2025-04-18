import base64
import json
from pyexpat.errors import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from .forms import CandidateForm, CheckStatusForm, QuizForm
from .models import Division, EmployeeMaster,LoginStatus , Option, Question, Candidate, QuizResult, RegionMaster, SonataUsersKYCData, SonataUsersKYCTransactionData, UnitMaster
from django.utils import timezone
from datetime import date, timedelta
from django.db import connection, connections
# from .models import *
import pandas as pd
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import io
import zipfile
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from django.utils.timezone import make_aware
import datetime
from PIL import Image

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
                    request.session['employee_id'] = empId  # Store employee_id in session
                    request.session['name'] = full_name
                    
                    return redirect('HR_dashboard')                    
            # Render home with error message
            return render(request, 'home.html', {'form': form})

    else:
        form = CandidateForm()
    return render(request, 'home.html', {'form': form})

from django.contrib.auth import logout
from django.db.models import Q  # Import Q for complex queries

def user_logout(request):
    logout(request)
    request.session.flush()  # Clear the session
    return redirect('home')

# For search bar
def employee_kyc_view(request):
    search_query = request.GET.get('search', '')
    if search_query:
        employees = SonataUsersKYCData.objects.filter(Q(EmpID__icontains=search_query) | Q(MobileNo__icontains=search_query) | Q(AdhaarNo__icontains=search_query) | Q(PAN_Number__icontains=search_query) | Q(DOB_icontains = search_query)) # Search query
    else:
        employees = SonataUsersKYCData.objects.all()  # Get all employees if no search query
        return render(request, 'KYC.html', {'employee_details': employees})
    
def HR_dashboard(request):
    # Retrieve the HR's employee ID from the session
    hr_employee_id = request.session.get('employee_id')

    if not hr_employee_id:
        return redirect('home')

    hr_employee  = Candidate.objects.get(employee_id=hr_employee_id)
    
    with connections['default'].cursor() as cursor:
        cursor.execute("""
            Select u.unitname from EmployeeMaster e
            left join unitmaster u on u.unitid = e.UnitID
            where employee_id = %s
        """, [hr_employee_id])
        result = cursor.fetchall()
        employee_unitname = [row[0] for row in result]
    # Fetch all region IDs and UnitIDs for the logged-in HR in a single query
    with connections['second_db'].cursor() as cursor:
        cursor.execute("""
            SELECT ra.regionid, um.unitid
            FROM regionAllotment ra
            JOIN unitmaster um ON ra.regionid = um.regionid
            WHERE ra.staffid = %s
        """, [hr_employee_id])
        result = cursor.fetchall()
        region_ids = [row[0] for row in result]
        unit_ids = [row[1] for row in result]

    if not region_ids or not unit_ids:
        return JsonResponse({'error': 'Region IDs or Unit IDs not found for the logged-in HR'}, status=400)

    # Format unit_ids for the SQL query
    unit_ids_str = ','.join(str(unit_id) for unit_id in unit_ids)
    print('unit_ids_str:', unit_ids_str)

    # Fetch employee data for the logged-in HR's units
    pending_count_query = f"""
        SELECT count(kyc.id) pending_count
        FROM [EmployeeMaster] a
        JOIN Tbl_Sonata_Users_KYC_Data kyc ON kyc.EmpID = a.employee_id
        JOIN unitmaster u ON u.unitid = a.UnitID
        LEFT JOIN regionmaster r ON r.regionid = u.regionid
        LEFT JOIN Division d ON d.divisionalid = r.divisionalid
        LEFT JOIN Zone z ON z.id = d.zoneID
        WHERE a.UnitID IN ({unit_ids_str}) AND kyc.IsActive = 1 AND kyc.IsProcessed = 0
    """
    query = f"""
        SELECT a.employee_id, kyc.EmpID,FORMAT(kyc.DOB, 'yyyy-MM-dd') AS DOB, kyc.MobileNo, kyc.AdhaarNo,UPPER(kyc.PAN_Number) AS PAN_Number,a.first_name,a.surname,kyc.Verified_Date
        FROM [EmployeeMaster] a
        JOIN Tbl_Sonata_Users_KYC_Data kyc ON kyc.EmpID = a.employee_id
        JOIN unitmaster u ON u.unitid = a.UnitID
        LEFT JOIN regionmaster r ON r.regionid = u.regionid
        LEFT JOIN Division d ON d.divisionalid = r.divisionalid
        LEFT JOIN Zone z ON z.id = d.zoneID
        WHERE a.UnitID IN ({unit_ids_str}) AND kyc.IsActive = 1 AND kyc.IsProcessed = 0
    """

    # Fetch completed employee data for the logged-in HR's units
    completed_query = f"""
        SELECT a.employee_id,kyc.EmpID,FORMAT(kyc.DOB, 'yyyy-MM-dd') AS DOB, kyc.MobileNo, kyc.AdhaarNo,UPPER(kyc.PAN_Number) AS PAN_Number,a.first_name,
        a.surname,
        FORMAT(DATEADD(MINUTE, 330, kyc.Verified_Date), 'yyyy-MM-dd') AS Verified_Date
        FROM [EmployeeMaster] a
        JOIN Tbl_Sonata_Users_KYC_Data kyc ON kyc.EmpID = a.employee_id
        JOIN unitmaster u ON u.unitid = a.UnitID
        LEFT JOIN regionmaster r ON r.regionid = u.regionid
        LEFT JOIN Division d ON d.divisionalid = r.divisionalid
        LEFT JOIN Zone z ON z.id = d.zoneID
        WHERE a.UnitID IN ({unit_ids_str}) AND kyc.IsActive = 1 AND kyc.IsProcessed = 1
    """

    rejected_query = f"""
        WITH NumberedRemarks AS (
            SELECT 
                trn.EmpID,
                trn.Remark,
                ROW_NUMBER() OVER (PARTITION BY trn.EmpID ORDER BY trn.ID) AS rn
            FROM Tbl_Sonata_Users_KYC_Transaction_Data trn
        	WHERE trn.Remark <> '' -- Exclude empty remarks
        )
        SELECT a.employee_id,
               kyc.EmpID,
               FORMAT(kyc.DOB, 'yyyy-MM-dd') AS DOB,
               kyc.MobileNo,
               kyc.AdhaarNo,
               UPPER(kyc.PAN_Number) AS PAN_Number,
               a.first_name,
               a.surname,
                STRING_AGG(CAST(nr.rn AS VARCHAR) + '. ' + nr.Remark, ', ') AS remark,  -- Combine all remarks into a single string separated by ';'
               FORMAT(DATEADD(MINUTE, 330, kyc.Verified_Date), 'yyyy-MM-dd') AS Verified_Date
        FROM [EmployeeMaster] a
        JOIN Tbl_Sonata_Users_KYC_Data kyc ON kyc.EmpID = a.employee_id
        JOIN unitmaster u ON u.unitid = a.UnitID
        LEFT JOIN regionmaster r ON r.regionid = u.regionid
        LEFT JOIN Division d ON d.divisionalid = r.divisionalid
        LEFT JOIN Zone z ON z.id = d.zoneID
        LEFT JOIN NumberedRemarks nr ON nr.EmpID = a.employee_id
        WHERE a.UnitID IN ({unit_ids_str})
          AND kyc.IsActive = 1
          AND kyc.IsProcessed = -1
        GROUP BY a.employee_id, kyc.EmpID, kyc.DOB, kyc.MobileNo, kyc.AdhaarNo, kyc.PAN_Number, a.first_name, a.surname, kyc.Verified_Date
            
        """
    
    with connections['default'].cursor() as cursor:
        
        cursor.execute(pending_count_query)
        pending_employee_data = cursor.fetchall()
        pending_employee_count = pending_employee_data[0][0]
        print('employee_count:', pending_employee_count)
        
        cursor.execute(query)
        employee_data = cursor.fetchall()

        # Fetch completed employee data
        cursor.execute(completed_query)
        completed_employee_data = cursor.fetchall()
        
        if cursor.description:
            columns = [col[0] for col in cursor.description]  # Extract column names
            
            # pending_df = pd.DataFrame(pending_employee_data, columns=columns)  # Convert to DataFrame
            # pending_employee_count = pending_df.to_dict(orient='records')  # Convert to list of dictionaries
            # print('pending_employee_count:', pending_employee_count)
            
            df = pd.DataFrame(employee_data, columns=columns)  # Convert to DataFrame
            employee_details = df.to_dict(orient='records')  # Convert to list of dictionaries
            
            # Convert completed employee data to DataFrame and then to list of dictionaries
            completed_df = pd.DataFrame(completed_employee_data, columns=columns)
            completed_employee_details = completed_df.to_dict(orient='records')
            

        else:
            employee_details = []  # If no data is fetched, return an empty list
            completed_employee_details = []  # If no data is fetched, return an empty list
            reject_employee_details = []  # If no data is fetched, return an empty list
            
        cursor.execute(rejected_query)
        reject_employee_data = cursor.fetchall()

        if cursor.description:
            columns = [col[0] for col in cursor.description]

            reject_df = pd.DataFrame(reject_employee_data, columns=columns)
            reject_employee_details = reject_df.to_dict(orient='records')

        else:
            reject_employee_details = []  # If no data is fetched, return an empty list
            
    return render(request, 'KYC.html', {'employee_details': employee_details, 'completed_employee_details': completed_employee_details,
                                        'reject_employee_details': reject_employee_details,'hr_employee': hr_employee,'hr_employee_id': hr_employee_id,
                                        'employee_unitname': employee_unitname,'pending_employee_count': pending_employee_count})



def get_emp_images(request):
    emp_id = request.GET.get('empid')
    print('emp_id for candidate image:', emp_id)

    if not emp_id:
        return JsonResponse({'error': 'EmpID is required'}, status=400)

    query = """
        SELECT z.Zone, d.Divisionname, r.regionname, u.unitname,a.employee_id, first_name, surname, EmpDOB, kyc.MobileNo, 
        a.DOJ, PanNo, kyc.*, signdesk.FullName, signdesk.AadharNo, signdesk.DOB,signdesk.Care_Of,signdesk.District,signdesk.House,signdesk.ProfileImage
        FROM EmployeeMaster a
        JOIN Tbl_Sonata_Users_KYC_Data kyc ON kyc.EmpID = a.employee_id
        JOIN unitmaster u ON u.unitid = a.UnitID
        LEFT JOIN regionmaster r ON r.regionid = u.regionid
        LEFT JOIN Division d ON d.divisionalid = r.divisionalid
        LEFT JOIN Zone z ON z.id = d.zoneID
        LEFT JOIN Tbl_Sonata_Users_KYC_Data_SignDesk signdesk ON signdesk.EmpID = a.employee_id
        WHERE kyc.IsActive = 1 AND kyc.IsProcessed = 0 AND kyc.EmpID = %s;
    """

    with connection.cursor() as cursor:
        cursor.execute(query, [emp_id])
        row = cursor.fetchone()
        if not row:
            return JsonResponse({'error': 'Employee not found'}, status=404)

        columns = [col[0] for col in cursor.description]
        row_dict = dict(zip(columns, row))

    # Now you can safely access fields by name
    data = {
        'Zone': row_dict.get('Zone'),
        'DivisionName': row_dict.get('Divisionname'),
        'RegionName': row_dict.get('regionname'),
        'UnitName': row_dict.get('unitname'),
        'StaffID': row_dict.get('employee_id'),
        'first_name': row_dict.get('first_name'),
        'surname': row_dict.get('surname'),
        'EmpDOB': row_dict.get('EmpDOB'),
        'EmpMobileNo': row_dict.get('MobileNo'),
        'DOJ': row_dict.get('DOJ'),
        'EmpPanNo': row_dict.get('PanNo'),
        'EmpID': row_dict.get('EmpID'),
        'DOB': row_dict.get('DOB'),
        'Photo': convert_binary_to_base64(row_dict.get('Photo')),
        'MobileNo': row_dict.get('MobileNo'),
        'AdhaarNo': row_dict.get('AdhaarNo'),
        'PAN_Number': row_dict.get('PAN_Number'),
        'AdhaarFrontImg': convert_binary_to_base64(row_dict.get('AdhaarFrontImg')),
        'AdhaarBackImg': convert_binary_to_base64(row_dict.get('AdhaarBackImg')),
        'PAN_Img': convert_binary_to_base64(row_dict.get('PAN_Img')),
        'DL_Img': convert_binary_to_base64(row_dict.get('DL_Img')),
        'Passbook_Img': convert_binary_to_base64(row_dict.get('Passbook_Img')),
        'FullName_Signdesk': row_dict.get('FullName'),
        'AadharNo_Signdesk': row_dict.get('AadharNo'),
        'DOB_Signdesk': row_dict.get('DOB'),
        'Care_of': row_dict.get('Care_Of'),
        'District': row_dict.get('District'),
        'House': row_dict.get('House'),
        'ProfileImage': convert_binary_to_base64(row_dict.get('ProfileImage')),
    }

    print(f"✅ Data fetched for EmpID {emp_id}: {data}")
    return JsonResponse(data)

# 🔹 Function to Convert Binary to Base64
def convert_binary_to_base64(binary_data):
    if binary_data:
        return "data:image/png;base64," + base64.b64encode(binary_data).decode('utf-8')
    return None




@csrf_exempt
def verify_document(request):
    if request.method == "POST":
        try:
            emp_id = request.POST.get("emp_id")
            doc_type = request.POST.get("doc_type")
            action = request.POST.get("action")  # "verify" or "reject"
            remark = request.POST.get("remark", "").strip()  # 📝 Remarks lein (default empty)
            print(f"Received emp_id: {emp_id}")
          
            try:
                emp_id = int(emp_id)  
            except ValueError:
                return JsonResponse({"status": "error", "message": "Invalid Employee ID!"}, status=400)
            
            if not emp_id or not doc_type or not action:
                return JsonResponse({"status": "error", "message": "Missing required fields!"}, status=400)

            print(f"Received emp_id: {emp_id}, doc_type: {doc_type}, action: {action}, remark: {remark}")
            # Fetch the record from SonataUsersKYCData
            try:
                kyc_data = SonataUsersKYCData.objects.get(EmpID=emp_id)
                print('kyc data:', kyc_data.EmpID)
            except SonataUsersKYCData.DoesNotExist:
                print('-------1')
                return JsonResponse({"status": "error", "message": "Employee not found!"}, status=404)

            # Map doc_type to StageID
            stage_id_mapping = {
                'DOB': 2,
                'passport_photo': 3,
                'MobileNo': 4,
                'AdhaarNo': 5,
                'PAN_Number': 6,
                'aadhaar_front': 7,
                'aadhaar_back': 8,
                'PAN_Img': 9,
                'DL_Img': 10,
                'Passbook_Img': 11,
            }

            stage_id = stage_id_mapping.get(doc_type)

            if not stage_id:
                return JsonResponse({"status": "error", "message": "Invalid document type!"}, status=400)

            # Determine verification status and stage
            is_verified = 1 if action == "verify" else 0
            stage = 20 if action == "verify" else -1
            date = timezone.now()

            # Get the logged-in HR's employee ID
            hr_employee_id = request.session.get('employee_id')
            # Check if transaction already exists
            existing_transaction = SonataUsersKYCTransactionData.objects.filter(
                RefID=kyc_data.id, StageID=stage_id
            ).first()

            if existing_transaction:
                # Update existing record instead of inserting a new one
                existing_transaction.IsVerified = is_verified
                existing_transaction.Stage = stage
                existing_transaction.Date = date
                existing_transaction.Verified_by = hr_employee_id
                if action == "reject":  
                    existing_transaction.Remark = remark  # 📝 Remarks add karein
                elif action == "verify":
                    existing_transaction.Remark = ""  # Clear remarks if verified
                existing_transaction.save()
            else:
                # Insert a new row into SonataUsersKYCTransactionData
                SonataUsersKYCTransactionData.objects.update_or_create(
                    RefID=kyc_data.id,  # Primary key from SonataUsersKYCData
                    StageID=stage_id,
                    
                    EmpID=kyc_data.EmpID,
                    IsVerified= is_verified,
                    Date= date,
                    Stage= stage,
                    Remark= remark if action == "reject" else "", # 📝 Remarks set karein
                    Verified_by = hr_employee_id
                    
                )

            return JsonResponse({"status": "success", "message": "Document verification updated successfully!"})

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Invalid request method!"}, status=400)



@csrf_exempt
def final_submission(request):
    if request.method == "POST":
        emp_id = request.POST.get("emp_id")
        
        if not emp_id:
            return JsonResponse({"status": "error", "message": "Employee ID is missing!"}, status=400)

        print('final emp_id:', emp_id)  # Debugging: Log emp_id
        try:
            # Fetch the employee's KYC data
            kyc_data = SonataUsersKYCData.objects.get(EmpID=emp_id)

            # Map doc_type to StageID
            stage_id_mapping = {
                'DOB': 2,
                'passport_photo': 3,
                'MobileNo': 4,
                'AdhaarNo': 5,
                'PAN_Number': 6,
                'aadhaar_front': 7,
                'aadhaar_back': 8,
                'PAN_Img': 9,
                'DL_Img': 10,
                'Passbook_Img': 11,
            }

            # Fetch all StageIDs for the employee from SonataUsersKYCTransactionData
            completed_stages = SonataUsersKYCTransactionData.objects.filter(
                EmpID=emp_id
            ).values_list('StageID','IsVerified')

            completed_stage_dict = dict(completed_stages)
            # Find pending stages
            all_stages = set(stage_id_mapping.values())
            completed_stages = set(completed_stages)
            pending_stages = all_stages - set(completed_stage_dict.keys())

           
            if pending_stages:
                # Map pending StageIDs back to doc_type names
                pending_columns = [
                    doc_type for doc_type, stage_id in stage_id_mapping.items() if stage_id in pending_stages
                ]
                return JsonResponse({
                    "status": "error",
                    "message": f"Pending verification for: {', '.join(pending_columns)}"
                })

            # If all stages are completed, update isProcessed
            if any(is_verified == 0 for is_verified in completed_stage_dict.values()):  # If any stage is rejected
                kyc_data.IsProcessed = -1  # Mark as rejected   
            else:
                kyc_data.IsProcessed = 1
                
            date = timezone.now()
            # Get the logged-in HR's employee ID
            hr_employee_id = request.session.get('employee_id')
            kyc_data.FinalVerified_by = hr_employee_id
            kyc_data.Verified_Date = date
            kyc_data.save()

            return JsonResponse({"status": "success", "message": "Final submission successful!"})

        except SonataUsersKYCData.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Employee not found!"}, status=404)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Invalid request method!"}, status=400)


@csrf_exempt
def reports_view(request):
    if 'employee_id' not in request.session:
        return redirect('home')
    employee_id = request.session.get('employee_id')
    today = date.today()
    return render(request, "reports.html",{'employee_id': employee_id,"today_date": today})  # ✅ Create this HTML file


from django.utils.timezone import make_aware
import datetime
import pytz  # Optional if you want to specify a timezone

def download_reports(request):
    if 'employee_id' not in request.session:
        return redirect('home')

    employee_id = request.session.get('employee_id')
    print('report employee_id:', employee_id)
    try:
        # ✅ Query Parameters
        report_type = request.GET.get("type")  # 'completed' or 'non_completed'
        start_date = request.GET.get("start")  # Format: 'YYYY-MM-DD'
        end_date = request.GET.get("end")      # Format: 'YYYY-MM-DD'

        # ✅ Convert Dates to UTC Timezone
        # start_date = make_aware(datetime.datetime.strptime(start_date, "%Y-%m-%d"))
        # end_date = make_aware(datetime.datetime.strptime(end_date, "%Y-%m-%d")) + datetime.timedelta(days=1)
        # tz = pytz.UTC  # Define the timezone, e.g., UTC
        start_date = make_aware(datetime.datetime.strptime(start_date, "%Y-%m-%d"))
        end_date = make_aware(datetime.datetime.strptime(end_date, "%Y-%m-%d")) + datetime.timedelta(days=1)
        # ✅ Filtering Queryset
        filter_kwargs = {
            "IsProcessed": 1 if report_type == "completed" else 0,
            "Verified_Date__gte": start_date,
            "Verified_Date__lt": end_date,
            "StageID": 11,
            "FinalVerified_by": employee_id
        }
        print('filter_kwargs:', filter_kwargs)
        queryset = SonataUsersKYCData.objects.filter(**filter_kwargs).values(
            "EmpID", "MobileNo", "AdhaarNo", "PAN_Number", "IsActive", "IsProcessed", "Photo", "AdhaarFrontImg",
            "AdhaarBackImg", "PAN_Img", "DL_Img", "Passbook_Img"
        )
        print('reports queryset:', queryset)

        if not queryset.exists():
            return HttpResponse("No data found for the selected criteria.", status=404)

        # ✅ Convert Queryset to DataFrame
        df = pd.DataFrame(list(queryset))

        # ✅ Required Columns
        required_columns = ["EmpID", "MobileNo", "Photo", "AdhaarNo", "PAN_Number", "IsActive", "IsProcessed",
                            "AdhaarFrontImg", "AdhaarBackImg", "PAN_Img", "DL_Img", "Passbook_Img"]
        df = df[[col for col in required_columns if col in df.columns]]  # Keep only existing columns

        if df.empty:
            return HttpResponse("No valid image data found.", status=404)

        # ✅ Handle Duplicate Columns
        df = df.loc[:, ~df.columns.duplicated()]

        # ✅ Create ZIP Buffer
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:

            # ✅ Generate PDFs for Each Employee
            for _, row in df.iterrows():
                emp_id = row.get('EmpID', 'Unknown')
                pdf_buffer = io.BytesIO()
                c = canvas.Canvas(pdf_buffer, pagesize=letter)

                # ✅ Fixed Image Size
                img_width = 400
                img_height = 300

                # ✅ Top Margin
                top_margin = 150  # Page ke top se margin

                # ✅ Adjusted Image Positions
                y_positions = [600 - top_margin, 250 - top_margin]  # ✅ Shifted down by top_margin
                image_count = 0  # Track images per page

                for field in required_columns[2:]:  # Skip 'EmpID' and 'MobileNo'
                    if field in row and row[field]:  # Check if field exists and is not empty
                        try:
                            image_data = io.BytesIO(row[field])  # Convert binary data to BytesIO
                            
                            # ✅ Open Image with PIL
                            with Image.open(image_data) as img:
                                img = img.convert("RGB")  # Convert to RGB mode
                                img = img.resize((img_width, img_height))  # ✅ Resize to fixed 400x300

                                # ✅ Save Resized Image to BytesIO
                                resized_image_data = io.BytesIO()
                                img.save(resized_image_data, format="JPEG")  
                                resized_image_data.seek(0)

                            image = ImageReader(resized_image_data)  # Convert to ImageReader

                            # ✅ Draw Image on PDF
                            c.drawImage(image, 100, y_positions[image_count], width=img_width, height=img_height)
                            image_count += 1

                            if image_count == 2:  # ✅ If 2 images added, create a new page
                                c.showPage()
                                image_count = 0  # Reset count
                        except Exception as e:
                            print(f"Error processing {field} for {emp_id}: {e}")

                c.save()

                # ✅ Save the PDF in ZIP File
                pdf_buffer.seek(0)
                zip_file.writestr(f"{emp_id}_documents.pdf", pdf_buffer.read())

        # ✅ Prepare the Response with ZIP File
        response = HttpResponse(content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="employee_images.zip"'

        zip_buffer.seek(0)
        response.write(zip_buffer.getvalue())

        return response

    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=500)


def download_excel_reports(request):
    if 'employee_id' not in request.session:
        return redirect('home')

    employee_id = request.session.get('employee_id')

    try:
        # ✅ Query Parameters from URL
        report_type = request.GET.get("type")
        start_date = request.GET.get("start")
        end_date = request.GET.get("end")

        # ✅ Convert Dates to Timezone-Aware UTC
        start_date = make_aware(datetime.datetime.strptime(start_date, "%Y-%m-%d"))
        end_date = make_aware(datetime.datetime.strptime(end_date, "%Y-%m-%d")) + datetime.timedelta(days=1)
        
        with connections['second_db'].cursor() as cursor:
            cursor.execute("""
                SELECT ra.regionid, um.unitid
                FROM regionAllotment ra
                JOIN unitmaster um ON ra.regionid = um.regionid
                WHERE ra.staffid = %s
            """, [employee_id])
            result = cursor.fetchall()
            unit_ids = [row[1] for row in result]

        unit_ids_str = ','.join(['%s'] * len(unit_ids))  
        # ✅ Filtering Data
        if report_type == "completed":
            # queryset = SonataUsersKYCData.objects.filter(
            #     IsProcessed=1, Verified_Date__gte=start_date, Verified_Date__lt=end_date, FinalVerified_by=employee_id
            # ).values(*selected_columns)
            with connections['default'].cursor() as cursor:
                query = f"""
                    SELECT z.Zone, d.Divisionname, r.regionname, u.unitname, kyc.EmpID, 
                           a.first_name, a.surname, FORMAT(kyc.DOB, 'yyyy-MM-dd') AS DOB, 
                           kyc.MobileNo, kyc.AdhaarNo, UPPER(kyc.PAN_Number) AS PAN_Number, 
                           kyc.FinalVerified_by, 
                           CAST(kyc.Verified_Date AS DATE) AS Verified_Date  
                    FROM [EmployeeMaster] a
                    JOIN Tbl_Sonata_Users_KYC_Data kyc ON kyc.EmpID = a.employee_id
                    JOIN unitmaster u ON u.unitid = a.UnitID
                    LEFT JOIN regionmaster r ON r.regionid = u.regionid
                    LEFT JOIN Division d ON d.divisionalid = r.divisionalid
                    LEFT JOIN Zone z ON z.id = d.zoneID
                    WHERE a.UnitID IN ({unit_ids_str})
                    AND kyc.IsActive = 1 
                    AND kyc.IsProcessed = 1 
                    AND kyc.Verified_Date BETWEEN %s AND %s;
                """
                params = unit_ids + [start_date, end_date]  # Combine unit_ids with the other parameters

                cursor.execute(query, params)  # Execute query with parameters
                queryset = cursor.fetchall()  # Fetch results

                # Now process the query result
                columns = [col[0] for col in cursor.description]  # Get column names
                df = pd.DataFrame(queryset, columns=columns)  # Convert results to DataFrame

        elif report_type == "reject":
            with connections['default'].cursor() as cursor:
                query = f"""
                        SELECT z.Zone, d.Divisionname, r.regionname, u.unitname, kyc.EmpID, 
                               a.first_name, a.surname, FORMAT(kyc.DOB, 'yyyy-MM-dd') AS DOB, 
                               kyc.MobileNo, kyc.AdhaarNo, UPPER(kyc.PAN_Number) AS PAN_Number, 
                               kyc.FinalVerified_by, 
                               CAST(kyc.Verified_Date AS DATE) AS Verified_Date  
                        FROM [EmployeeMaster] a
                        JOIN Tbl_Sonata_Users_KYC_Data kyc ON kyc.EmpID = a.employee_id
                        JOIN unitmaster u ON u.unitid = a.UnitID
                        LEFT JOIN regionmaster r ON r.regionid = u.regionid
                        LEFT JOIN Division d ON d.divisionalid = r.divisionalid
                        LEFT JOIN Zone z ON z.id = d.zoneID
                        WHERE a.UnitID IN ({unit_ids_str})
                        AND kyc.IsActive = 1 
                        AND kyc.IsProcessed = -1 
                        AND kyc.Verified_Date BETWEEN %s AND %s;
                    """
                params = unit_ids + [start_date, end_date]  # Combine unit_ids with the other parameters

                cursor.execute(query, params)  # Execute query with parameters
                queryset = cursor.fetchall()  # Fetch results

                # Now process the query result
                columns = [col[0] for col in cursor.description]  # Get column names
                df = pd.DataFrame(queryset, columns=columns)  # Convert results to DataFrame
        else:
            with connections['default'].cursor() as cursor:
                query = f"""
                    SELECT z.Zone, d.Divisionname, r.regionname, u.unitname, kyc.EmpID, 
                           a.first_name, a.surname, FORMAT(kyc.DOB, 'yyyy-MM-dd') AS DOB, 
                           kyc.MobileNo, kyc.AdhaarNo, 
                           UPPER(kyc.PAN_Number) AS PAN_Number
                    FROM [EmployeeMaster] a
                    JOIN Tbl_Sonata_Users_KYC_Data kyc ON kyc.EmpID = a.employee_id
                    JOIN unitmaster u ON u.unitid = a.UnitID
                    LEFT JOIN regionmaster r ON r.regionid = u.regionid
                    LEFT JOIN Division d ON d.divisionalid = r.divisionalid
                    LEFT JOIN Zone z ON z.id = d.zoneID
                    WHERE a.UnitID IN ({unit_ids_str}) AND kyc.IsActive = 1 AND kyc.IsProcessed = 0;
                """
                params = unit_ids  # Combine unit_ids with the other parameters

                cursor.execute(query, params)  # Execute query with parameters
                queryset = cursor.fetchall()
                columns = [col[0] for col in cursor.description]
                df = pd.DataFrame(queryset, columns=columns)
        
        # ✅ Check if Data is Available
        if df.empty:
            return JsonResponse({'success': False, 'message': 'No data available for export.'})

        # ✅ Convert datetime columns safely
        for col in ['RecievedDate', 'Verified_Date']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
                df[col] = df[col].dt.date

        # ✅ Response as Excel File
        response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = f'attachment; filename="{report_type}_KYC_Report.xlsx"'

        df.to_excel(response, index=False, engine="openpyxl")

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


def helpdesk(request):
    return render(request, 'helpdesk.html')


def get_verification_status(request):
    emp_id = request.GET.get('emp_id')  # Get employee ID from request

    print('emp_id status:', emp_id)  # Debugging: Log emp_id
    if not emp_id:
        return JsonResponse({"status": "error", "message": "Employee ID is required"}, status=400)

    # Map StageID to Document Type
    stage_id_mapping = {
        2: "DOB",
        3: "passport_photo",
        4: "MobileNo",
        5: "AdhaarNo",
        6: "PAN_Number",
        7: "aadhaar_front",
        8: "aadhaar_back",
        9: "PAN_Img",
        10: "DL_Img",
        11: "Passbook_Img",
    }

    # Fetch all transactions for the employee
    transactions = SonataUsersKYCTransactionData.objects.filter(EmpID=emp_id)
    print('transactions:', transactions)  # Debugging: Log transactions
    # Prepare the verification status dictionary
    verification_status = {}
    for stage_id, doc_type in stage_id_mapping.items():
        transaction = transactions.filter(StageID=stage_id).first()
        if transaction:
            verification_status[doc_type] = "verified" if transaction.IsVerified == 1 else "rejected"
        else:
            verification_status[doc_type] = "pending"  # If no transaction exists, mark as pending

    return JsonResponse({"status": "success", "data": verification_status})























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



