from main import db, app
from flask_migrate import Migrate
from flask import render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from sqlalchemy import func
import secrets

"""
flask db migrate -m "volunteer change to int"
flask db upgrade


flask db downgrade


"""

migrate = Migrate(app, db)

class Resources(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    community = db.Column(db.String(255), nullable=True) 
    program = db.Column(db.String(255), nullable=True)
    user = db.Column(db.String(255), nullable=True)
    date = db.Column(db.Date, nullable=True)
    activity  = db.Column(db.String(255), nullable=True)
    url = db.Column(db.String(255), nullable=True) 
  
class Community(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    community = db.Column(db.String(255), nullable=False) 
    program = db.Column(db.String(255), nullable=False)
    subprogram = db.Column(db.String(255), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    week = db.Column(db.Integer, nullable=True)
    totalWeek = db.Column(db.Integer, nullable=False)
    user = db.Column(db.String(255), nullable=False)
    department  = db.Column(db.String(255), nullable=False) #LEAD
    subDepartment = db.Column(db.String(255), nullable=False) #SUPPORT
    status = db.Column(db.String(255), nullable=False)
    budget = db.Column(db.Integer, nullable=False)
    cna = db.Column(db.LargeBinary, nullable=True)
    cpf = db.Column(db.LargeBinary, nullable=True)
    cesap = db.Column(db.LargeBinary, nullable=True)
    cna_filename = db.Column(db.String(255), nullable=True)
    cpf_filename = db.Column(db.String(255), nullable=True)
    cesap_filename = db.Column(db.String(255), nullable=True)
    department_A = db.Column(db.String(255), nullable=True)
    volunteer = db.Column(db.Integer, nullable=True)
 
class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    otp = db.Column(db.String(6), nullable=True)
    otp_timestamp = db.Column(db.DateTime, nullable=True)
    program = db.Column(db.String(255), unique=True, nullable=False)
    department_A = db.Column(db.String(255), nullable=True)
    role = db.Column(db.String(50), nullable=False)
    firstname = db.Column(db.String(100), nullable=True)
    lastname = db.Column(db.String(100), nullable=True)
    mobile_number = db.Column(db.String(100), nullable=True)
    profile_picture = db.Column(db.LargeBinary, nullable=True)

class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    department_A = db.Column(db.String(255), nullable=True)
    department_F = db.Column(db.String(255), nullable=True)

class Program(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    program = db.Column(db.String(255), unique=True, nullable=False)

class Subprogram(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    program = db.Column(db.String(255), nullable=False)
    subprogram = db.Column(db.String(255), nullable=False)

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(255), nullable=False)

# ----------------------- Upload Files ------------------------------------
class Upload(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(50))
    data = db.Column(db.LargeBinary)

# For pending projects

class Pending_project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    community = db.Column(db.String(255), nullable=False) 
    program = db.Column(db.String(255), nullable=False)
    subprogram = db.Column(db.String(255), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    week = db.Column(db.Integer, nullable=True)
    totalWeek = db.Column(db.Integer, nullable=False)
    user = db.Column(db.String(255), nullable=False)
    department  = db.Column(db.String(255), nullable=False) #LEAD
    subDepartment = db.Column(db.String(255), nullable=False) #SUPPORT
    status = db.Column(db.String(255), nullable=False)
    budget = db.Column(db.Integer, nullable=False)
    cna = db.Column(db.LargeBinary, nullable=True)
    cpf = db.Column(db.LargeBinary, nullable=True)
    cesap = db.Column(db.LargeBinary, nullable=True)
    cna_filename = db.Column(db.String(255), nullable=True)
    cpf_filename = db.Column(db.String(255), nullable=True)
    cesap_filename = db.Column(db.String(255), nullable=True)
    comments = db.Column(db.String(255), nullable=True)
    department_A = db.Column(db.String(255), nullable=True)
    volunteer = db.Column(db.Integer, nullable=True)

class Plan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    community = db.Column(db.String(255), nullable=False) 
    program = db.Column(db.String(255), nullable=False)
    subprogram = db.Column(db.String(255), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    week = db.Column(db.Integer, nullable=True)
    totalWeek = db.Column(db.Integer, nullable=False)
    user = db.Column(db.String(255), nullable=False)
    department  = db.Column(db.String(255), nullable=False) #LEAD
    subDepartment = db.Column(db.String(255), nullable=False) #SUPPORT
    status = db.Column(db.String(255), nullable=False)
    budget = db.Column(db.Integer, nullable=False)
    cna = db.Column(db.LargeBinary, nullable=True)
    cpf = db.Column(db.LargeBinary, nullable=True)
    cesap = db.Column(db.LargeBinary, nullable=True)
    cna_filename = db.Column(db.String(255), nullable=True)
    cpf_filename = db.Column(db.String(255), nullable=True)
    cesap_filename = db.Column(db.String(255), nullable=True)
    comments = db.Column(db.String(255), nullable=True)
    department_A = db.Column(db.String(255), nullable=True)
    volunteer = db.Column(db.Integer, nullable=True)

class Archive(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    community = db.Column(db.String(255), nullable=False) 
    program = db.Column(db.String(255), nullable=False)
    subprogram = db.Column(db.String(255), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)   
    week = db.Column(db.Integer, nullable=True)
    totalWeek = db.Column(db.Integer, nullable=False)
    user = db.Column(db.String(255), nullable=False)
    department  = db.Column(db.String(255), nullable=False) #LEAD
    subDepartment = db.Column(db.String(255), nullable=False) #SUPPORT
    status = db.Column(db.String(255), nullable=False)
    budget = db.Column(db.Integer, nullable=False)
    cna = db.Column(db.LargeBinary, nullable=True)
    cpf = db.Column(db.LargeBinary, nullable=True)
    cesap = db.Column(db.LargeBinary, nullable=True)
    cna_filename = db.Column(db.String(255), nullable=True)
    cpf_filename = db.Column(db.String(255), nullable=True)
    cesap_filename = db.Column(db.String(255), nullable=True)
    department_A = db.Column(db.String(255), nullable=True)
    volunteer = db.Column(db.Integer, nullable=True)
    url = db.Column(db.String(255), nullable=True)

# --------------------- LOGS ------------------------#
class Logs(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    userlog = db.Column(db.String(255), nullable=False)
    action = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now, nullable=False)

# --------------------- TODO: MULTI-IMAGES UPLOAD ----------------------

# Create the database tables
with app.app_context():
    db.create_all()

###################### QUERIES #########################

def multiple_insert():
    # Create a list of Program instances
    program_insert = [
        Program(program='Literacy'),
        Program(program='Socio-economic'),
        Program(program='Environmental Stewardship'),
        Program(program='Health and Wellness'),
        Program(program='Cultural Enhancement'),
        Program(program='Values Formation'),
        Program(program='Disaster Management'),
        Program(program='Gender and Development'),
    ]

    # Create a list of Role instances
    role_insert = [
        Role(role='Coordinator')
    ]

    # Add the program records to the session and commit
    for program in program_insert:
        db.session.add(program)

    # Add the role records to the session and commit
    for role in role_insert:
        db.session.add(role)

    db.session.commit()
    
def insert_community():
    community = 'Bubukal'
    program = 'Literacy'
    subprogram = 'Sub-Literacy'
    start_date = datetime.strptime('2023-10-01', '%Y-%m-%d').date()
    end_date = datetime.strptime('2023-11-01', '%Y-%m-%d').date()
    week = 2
    totalWeek = 10
    user = 'Admin'
    department = 'Department'
    subDepartment = 'Sub-department'
    status = 'Ongoing'
    budget = 100
  
   
    community_insert = Community(community=community,program=program,subprogram=subprogram, start_date=start_date,
    end_date=end_date, week=week, totalWeek=totalWeek, user=user, department=department, subDepartment=subDepartment, status=status, budget=budget )
    
    if community_insert:
        # If a row with the specified program value is found, delete it
        db.session.add(community_insert)
        db.session.commit()
    
def insert_pending():
    community = 'Bubukal'
    program = 'Literacy'
    subprogram = 'Sub-Literacy'
    start_date = datetime.strptime('2023-10-01', '%Y-%m-%d').date()
    end_date = datetime.strptime('2023-11-01', '%Y-%m-%d').date()
    week = 2
    totalWeek = 10
    user = 'Admin'
    department = 'Department'
    subDepartment = 'Sub-department'
    status = 'Pending'
    budget = 100
    
    
    community_insert = Pending_project(community=community,program=program,subprogram=subprogram, start_date=start_date,
    end_date=end_date, week=week, totalWeek=totalWeek, user=user, department=department, subDepartment=subDepartment, status=status, budget=budget )
        
    if community_insert:
        # If a row with the specified program value is found, delete it
        db.session.add(community_insert)
        db.session.commit()

def insert_userx():
    username = 'admin2'
    firstname = 'Joselle2'
    lastname = 'Banocnoc2'
    email = '1ls1ucesu50@gmail.com'
    program = 'CESU'
    password = '@123ABCabc'
    role = 'Admin'
    
    user_insert = Users(username=username, firstname=firstname, lastname=lastname, program=program, email=email, password=password, role=role)
    db.session.add(user_insert)
    db.session.commit()

    username = 'admin1'
    firstname = 'Joselle1'
    lastname = 'Banocnoc1'
    email = '1ls1ucesu501@gmail.com'
    program = 'CESU '
    password = '@123ABCabc'
    role = 'Admin'
    
    user_insert = Users(username=username, firstname=firstname, lastname=lastname, program=program, email=email, password=password, role=role)
    db.session.add(user_insert)
    db.session.commit()

def delete_data():
 # Delete all records in the Subprogram table
    data = Community.query.filter_by(user="Admin").first()
 
    db.session.delete(data)
    db.session.commit()

@app.route('/db')
def initialize_database():
    #multiple_insert()
    #insert_community()
    #insert_userx()
    #insert_pending()
    #delete_data()
    return 'Program.'

@app.route('/test')
def display_community_data():
    subprogram_data = db.session.query(Subprogram).all()
    all_community_data = db.session.query(Community).all()
    Pending_project_data = Pending_project.query.all()
    User = Users.query.all()
    UserLogs = Logs.query.all()
    planner = Plan.query.all()
    department = Department.query.all()
    archive_project = db.session.query(Archive).all()
    return render_template('test.html',planner=planner, UserLogs = UserLogs, community_data=all_community_data, subprogram_data=subprogram_data, Pending_project_data = Pending_project_data, Users = User, archive_project=archive_project, department=department)
