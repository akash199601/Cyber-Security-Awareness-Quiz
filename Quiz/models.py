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
    UnitID = models.IntegerField(null=True, blank=True)
    employee_id = models.IntegerField(primary_key=True)
    EmpDOB = models.DateField(null=True, blank=True)
    StaffTypeID= models.IntegerField(null=True, blank=True)
    DesigID = models.IntegerField(null=True, blank=True)
    DeptID = models.IntegerField(null=True, blank=True)
    first_name = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    DOR = models.DateField(null=True, blank=True)
    DOJ = models.DateField(null=True, blank=True)

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
    
    
    
    
    
class HR_TABLE(models.Model):
    name = models.CharField(max_length=20)
    employee_id = models.IntegerField()

    def __str__(self):
        return '__all__'


class Division(models.Model):
    divisionalid = models.AutoField(primary_key=True)  
    Divisionname = models.CharField(max_length=255) 
    zoneID = models.IntegerField() 

    class Meta:
        db_table = "Division"
        managed = False 
    

class RegionMaster(models.Model):
    regionid = models.AutoField(primary_key=True) 
    regionname = models.CharField(max_length=255) 
    divisionalid = models.ForeignKey(Division, on_delete=models.CASCADE,db_column='divisionalid')  
    state = models.CharField(max_length=255)  

    class Meta:
        db_table = "regionmaster"
        managed = False
        
class UnitMaster(models.Model):
    unitid = models.AutoField(primary_key=True) 
    unitname = models.CharField(max_length=255)  
    districtid = models.IntegerField(null=True, blank=True)
    regionid = models.IntegerField(null=True, blank=True)
    stateid = models.IntegerField(null=True, blank=True)
    esiapplicable = models.BooleanField(default=False)  
    statename = models.CharField(max_length=255, null=True, blank=True)
    isopen = models.BooleanField(default=False) 
    currentaddress = models.TextField(null=True, blank=True)
    workingstatus = models.BooleanField(default=True)  
    dateofopening = models.DateField(null=True, blank=True)
    applicability = models.CharField(max_length=255, null=True, blank=True)
    registrationno = models.CharField(max_length=255, null=True, blank=True)
    renewaldate = models.DateField(null=True, blank=True)
    expirydate = models.DateField(null=True, blank=True)
    docstatus = models.CharField(max_length=255, null=True, blank=True)
    filelink = models.URLField(null=True, blank=True)  
    cmbdocumenttype = models.CharField(max_length=255, null=True, blank=True)
    portfolio_unit_id = models.IntegerField(null=True, blank=True)
    hubid = models.IntegerField(null=True, blank=True)
    category = models.CharField(max_length=255, null=True, blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    officetypeid = models.IntegerField(null=True, blank=True)
    reportingunitid = models.IntegerField(null=True, blank=True)
    misname = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'unitmaster'  
        managed = False  
    
    
class SonataUsersKYCData(models.Model):
    StageID = models.IntegerField()
    EmpID = models.BigIntegerField(unique=True)
    DOB = models.DateField(null=True,blank=True)
    Photo = models.BinaryField(null=True,blank=True)
    MobileNo = models.CharField(max_length=15)
    AdhaarNo = models.CharField(max_length=12)
    PAN_Number = models.CharField(max_length=10)
    AdhaarFrontImg = models.BinaryField(null=True, blank=True)
    AdhaarBackImg = models.BinaryField(null=True, blank=True)
    PAN_Img = models.BinaryField(null=True, blank=True)
    DL_Img = models.BinaryField(null=True, blank=True)
    Passbook_Img = models.BinaryField(null=True, blank=True)
    RecievedDate = models.DateTimeField(auto_now_add=True)
    IsActive = models.BooleanField(default=True)
    IsProcessed = models.IntegerField(default=0)
    FinalVerified_by = models.IntegerField(null=True, blank=True)
    Verified_Date = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = "Tbl_Sonata_Users_KYC_Data"
        managed = False
        

       
       
class RegionAllotment(models.Model):
    id = models.AutoField(primary_key=True)
    staffid = models.IntegerField(null=True, blank=True)
    regionid = models.SmallIntegerField(null=True, blank=True)

    class Meta:
        db_table = 'regionAllotment'    
        managed = False
 
 
class SonataUsersKYCTransactionData(models.Model):
    RefID = models.IntegerField(null=True, blank=True)
    EmpID = models.IntegerField(null=True, blank=True)
    StageID = models.IntegerField(null=True, blank=True)
    IsVerified = models.IntegerField(null=True, blank=True)
    Remark = models.CharField(max_length=255, null=True, blank=True)
    Date = models.DateField(null=True, blank=True)
    Stage = models.IntegerField(null=True, blank=True)
    Verified_by = models.IntegerField(null=True, blank=True)
    class Meta:
        db_table = "Tbl_Sonata_Users_KYC_Transaction_Data"
        managed = False
        
        
class TblSonataUsersKYCDataSignDesk(models.Model):
    EmpID = models.BigIntegerField(null=True, blank=True)
    FullName = models.CharField(max_length=255)
    AadharNo = models.CharField(max_length=12, unique=True)
    DOB = models.DateField()
    Gender = models.CharField(max_length=10)
    Country = models.CharField(max_length=100)
    District = models.CharField(max_length=100)
    State = models.CharField(max_length=100)
    PO = models.CharField(max_length=255, null=True, blank=True)
    Loc = models.CharField(max_length=255, null=True, blank=True)
    Vtc = models.CharField(max_length=255, null=True, blank=True)
    Street = models.CharField(max_length=255, null=True, blank=True)
    House = models.CharField(max_length=255, null=True, blank=True)
    Landmark = models.CharField(max_length=255, null=True, blank=True)
    ZIP = models.CharField(max_length=10)
    ProfileImage = models.BinaryField(null=True, blank=True)
    Care_Of = models.CharField(max_length=255, null=True, blank=True)
    Status = models.CharField(max_length=255, null=True, blank=True)
    reference_id = models.TextField(null=True, blank=True)
    uniqueness_id = models.TextField(null=True, blank=True)
    UpdatedDate = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "Tbl_Sonata_Users_KYC_Data_SignDesk"
        managed = False