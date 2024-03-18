from flask import g, Blueprint, url_for, redirect, request, session, flash, render_template, jsonify, make_response, g, redirect
from main.models.dbModel import Community, Program, Subprogram, Role, Upload, Pending_project, Users, Archive, Logs, Plan, Department, Resources
from main import db
from flask import Response
import secrets
from datetime import datetime, timedelta
from sqlalchemy import func, case
from mailbox import Message
from main import Form, app, mail
from flask_mail import Mail, Message
import pytz, re
import base64
# LINE BELOW IS FOR PASS ENCRYPTION (UNCOMMENT IF NEEDED)
from werkzeug.security import generate_password_hash, check_password_hash 

# Get the timezone for the Philippines


dbModel_route = Blueprint('dbModel', __name__)
token_store = {}

# Function to validate email format
def is_valid_email(email):
    # Regular expression pattern for validating email format
    pattern = r'^[\w\.-]+@gmail\.com$'
    return re.match(pattern, email) is not None

def convert_date(date_str):
    return datetime.strptime(date_str, '%Y-%m-%d').date()

def convert_date1(datetime_str):
    return datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')

global cur
#################### ACCOUNT RECOVER REQUEST FUNCTION ##################

@dbModel_route.route("/send_recovery_mail", methods=['POST'])
def send_recovery_mail():
    if request.method == 'POST':
        email = request.form.get('email')
        # Check if the email exists in the database
        user = Users.query.filter_by(email=email).first()

        if user:
            userlog = user.username
            action = "Attempted to recover account"
            ph_tz = pytz.timezone('Asia/Manila')
            ph_time = datetime.now(ph_tz)
            timestamp1 = ph_time.strftime('%Y-%m-%d %H:%M:%S')
            timestamp = convert_date1(timestamp1)
            insert_logs = Logs(userlog = userlog, timestamp = timestamp, action = action)
            if insert_logs:
                db.session.add(insert_logs)
                db.session.commit()
            # Generate and store OTP in the database
            otp = secrets.token_hex(3)  # 6 characters in hex format
            user.otp = otp
            user.otp_timestamp = datetime.utcnow() + timedelta(minutes=5)  # Set expiration time to 5 minutes
            db.session.commit()

            # Send OTP via email
            send_mail(otp, email)

            return render_template('reset_password.html', email=email)
        else:
            return "Email not found."

    return redirect(url_for('dbModel.login'))


@dbModel_route.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == "POST":
        email = request.form.get("email")
        otp_entered = request.form.get("otp")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        # Check if the email exists in the database
        user = Users.query.filter_by(email=email).first()

        if ' ' in new_password:
            flash('Password cannot contain spaces.', 'newpassword_space')
            return render_template('reset_password.html', email=email)

        if user:
            if user.otp == otp_entered:
                expiration_time = user.otp_timestamp + timedelta(minutes=5)

                if datetime.utcnow() < expiration_time:

                    if new_password == confirm_password:
                        # Hash the new password
                        hashed_password = generate_password_hash(new_password)
                        user.password = hashed_password

                        # Clear OTP fields
                        user.otp = None
                        user.otp_timestamp = None

                        # Commit changes to the database
                        db.session.commit()

                        # Log the password reset action
                        userlog = user.username
                        action = "Successfully recovered account."
                        ph_tz = pytz.timezone('Asia/Manila')
                        ph_time = datetime.now(ph_tz)
                        timestamp1 = ph_time.strftime('%Y-%m-%d %H:%M:%S')
                        timestamp = convert_date1(timestamp1)
                        insert_logs = Logs(userlog=userlog, timestamp=timestamp, action=action)
                        db.session.add(insert_logs)
                        db.session.commit()

                        flash('Password reset successful. You can now log in with your new password.')
                        return redirect(url_for('dbModel.login'))
                    else:
                        flash('New password and confirmation do not match.', 'not_match')
                        return render_template('reset_password.html', email=email)
                else:
                    flash('OTP has expired. Please request a new one.', 'not_match')
                    return render_template('reset_password.html', email=email)
            else:
                flash('Invalid OTP.', 'not_match')
                return render_template('reset_password.html', email=email)
        else:
            flash('User not found.', 'not_match')
            return render_template('reset_password.html', email=email)
    return render_template('reset_password.html')

@dbModel_route.route("/send_mail")
def send_mail(otp, recipient_email):
    sender_name = "LU-CESU"
    mail_message = Message(
            'Account Recovery', 
            sender =   (sender_name, 'lucesu50@gmail.com'), 
            recipients = [recipient_email])
    mail_message.body = f"""
    Your One-Time Password (OTP): {otp}

    This OTP is valid for a single use and will expire shortly. 
    Do not share it with anyone for security reasons. 

    If you did not request this OTP or experience any issues, please contact our support team immediately. 

    Thank you for trusting us with your security.

    Best regards,
    LU-CESU MIS Team
    """
    mail_message.html = f"""
    <html>
        <body>
            <p>Hi {recipient_email},</p>
            <p>Your One-Time Password (OTP): <strong>{otp}</strong></p>
            <p>This OTP is valid for a single use and will expire shortly. 
            Do not share it with anyone for security reasons.</p>
            <p>If you did not request this OTP or experience any issues, please contact our support team immediately.</p>
            <p>Thank you for trusting us with your security.</p>
            <h1 style="margin-top: 1rem;"></h1>
            <p><em>Best regards, LU-CESU MIS Team</em></p>
        </body>
    </html>
    """
    mail.send(mail_message)
    return "Mail has sent"

#################### CURRENT USER ##################
def get_current_user():
    if 'user_id' in session:
        # Assuming you have a User model or some way to fetch the user by ID
        user = Users.query.get(session['user_id'])
        pending_count = Pending_project.query.filter_by(status="For Review").count()
            
        # Set a maximum value for pending_count
        max_pending_count = 9
        pending_count_display = min(pending_count, max_pending_count)

        # If pending_count is 9 or greater, display it as '9+'
        pending_count_display = '9+' if pending_count > max_pending_count else pending_count

        profile_picture_base64 = None
        if user:
            if user.profile_picture:
                # Convert the profile picture to base64 encoding
                profile_picture_base64 = base64.b64encode(user.profile_picture).decode('utf-8')

            return user.username, user.role, pending_count_display, user.firstname, user.lastname, profile_picture_base64
    return None, None, 0, None, None, None

@dbModel_route.before_request
def before_request():
    g.current_user, g.current_role, g.pending_count_display, g.current_firstname, g.current_lastname, g.profile_picture_base64 = get_current_user()

@dbModel_route.context_processor
def inject_current_user():
    current_user, current_role, pending_count, current_firstname, current_lastname, profile_picture_base64 = get_current_user()
    return dict(current_user=current_user, current_role=current_role, pending_count=pending_count, current_firstname=current_firstname, current_lastname=current_lastname, profile_picture_base64=profile_picture_base64)

#################### USERS LOGIN FUNCTION ##################

@dbModel_route.route("/login", methods=["GET", "POST"])
def login():
    if 'user_id' in session:
        if g.current_role != "Admin" and g.current_role != "BOR":
            return redirect(url_for('coordinator.coordinator_dashboard')) 
        else:
            return redirect(url_for('dbModel.dashboard'))

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = Users.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            userlog = username
            action = f'{user.firstname} {user.lastname} Logged in.'
            ph_tz = pytz.timezone('Asia/Manila')
            ph_time = datetime.now(ph_tz)
            timestamp1 = ph_time.strftime('%Y-%m-%d %H:%M:%S')
            timestamp = convert_date1(timestamp1)
            insert_logs = Logs(userlog=userlog, timestamp=timestamp, action=action)
            db.session.add(insert_logs)
            db.session.commit()

            session['user_id'] = user.id
            if user.role == 'Admin' or user.role == 'BOR':
                flash(f'Login successful!', 'success')
                return redirect(url_for('dbModel.dashboard'))
            else:
                return redirect(url_for('coordinator.coordinator_dashboard'))
        else:
            flash(f'Invalid username or password.', 'login_error')
            return redirect(url_for('dbModel.login'))
    return render_template('login.html')

@dbModel_route.route("/admin_dashboard")
def dashboard():
    if g.current_role != "Admin" and g.current_role != "BOR":
        return redirect(url_for('dbModel.login')) 

     # Check if the user is logged in
    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))
    return render_template("dashboard.html")

@dbModel_route.route("/clear_session")
def clear_session():
    session.clear()
    userlog = g.current_user
    action = 'Logged out.'
    ph_tz = pytz.timezone('Asia/Manila')
    ph_time = datetime.now(ph_tz)
    timestamp1 = ph_time.strftime('%Y-%m-%d %H:%M:%S')
    timestamp = convert_date1(timestamp1)
    insert_logs = Logs(userlog = userlog, timestamp = timestamp, action = action)
    if insert_logs:
        db.session.add(insert_logs)
        db.session.commit()
    return redirect(url_for('dbModel.login'))

@dbModel_route.route("/result")
def programCSVresult():
    if g.current_role != "Admin" and g.current_role != "BOR":
        return redirect(url_for('dbModel.login'))

    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))
    return redirect(url_for('randomForest.programOneRow'))

############################  USER ACCOUNT FUNCTION  FOR ADMIN #########################

@dbModel_route.route("/manage_account")
def manage_account():
    if g.current_role != "Admin" and g.current_role != "BOR":
        return redirect(url_for('dbModel.login'))

    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))
     # Fetch all user records from the database
    # Check if the current user's role is 'BOR'
    if g.current_role == 'BOR':
        # Retrieve all users with the role 'BOR'
        filtered_data = Users.query.all()
    else:
        # Retrieve all users where the role is not 'BOR'
        filtered_data = Users.query.filter(Users.role != 'BOR').all()

    # Prepare a dictionary to store profile pictures as base64 encoded strings
    profile_pictures_base64 = {}
    for user in filtered_data:
        # Check if the user has a profile picture
        if user.profile_picture:
            # Convert the profile picture to base64 encoding
            profile_pictures_base64[user.id] = base64.b64encode(user.profile_picture).decode('utf-8')
        else:
            # If there is no profile picture, set it to None
            profile_pictures_base64[user.id] = None

    role = Role.query.all()
    department = Department.query.all()
    program8 = Program.query.all()
    return render_template("manage_account.html",profile_pictures_base64=profile_pictures_base64, users = filtered_data, role = role, program8=program8, department=department)

@dbModel_route.route("/add_account", methods=["POST"])
def add_account():
    if g.current_role != "Admin" and g.current_role != "BOR":
        return redirect(url_for('dbModel.login'))

    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))
    
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        firstname = request.form.get("firstname")
        lastname = request.form.get("lastname")
        password = request.form.get("password")
        role = request.form.get("role")
        program = request.form.get("program")
        department_A = request.form.get("department_A")
        mobile_number = request.form.get("mobile_number")
        #profile_picture = request.files['profile_picture'].read()  # Use .get() instead of ['']

        # Hash the password
        hashed_password = generate_password_hash(password)


        # Check if the username already exists in the database
        existing_username = Users.query.filter_by(username=username).first()
        existing_program = Users.query.filter_by(program=program).first()
        existing_email = Users.query.filter_by(email=email).first()
        existing_mobile_number = Users.query.filter_by(mobile_number=mobile_number).first()

        # Check if the email format is valid and ends with '@gmail.com'
        if not is_valid_email(email):
            flash('Invalid email format. Only Gmail accounts are allowed.', 'password_space')
            return redirect(url_for('dbModel.manage_account'))

        if ' ' in password:
            flash('Password cannot contain spaces.', 'password_space')
            return redirect(url_for('dbModel.manage_account'))
        
     
        if ' ' in username:
            flash('Password cannot contain spaces.', 'username_space')
            return redirect(url_for('dbModel.manage_account'))
    

        if len(mobile_number) < 11:
                flash('Mobile number must be at least 11 digits long.', 'existing_username')
                return redirect(url_for('dbModel.manage_account'))

        if existing_program:
            flash(f"Sorry, '{program}' is already taken. Please choose another name or check existing programs.", 'existing_program')
        else:
            if existing_email:
                flash(f"Sorry, '{email}' is already taken.", 'existing_program')
            else:
                if existing_username:
                    flash('Username already exists. Please choose a different username.', 'existing_username')
                else:
                    if existing_mobile_number:
                        flash('Mobile number already exists.', 'existing_username')
                    else:
                        new_user = Users(username=username, firstname=firstname, lastname=lastname,password=hashed_password, email=email, role = role, program = program, department_A=department_A, mobile_number=mobile_number)
                        try: 
                            userlog = g.current_user
                            action = f'ADDED new user account named {new_user.firstname} {new_user.lastname}'
                            ph_tz = pytz.timezone('Asia/Manila')
                            ph_time = datetime.now(ph_tz)
                            timestamp1 = ph_time.strftime('%Y-%m-%d %H:%M:%S')
                            timestamp = convert_date1(timestamp1)
                            insert_logs = Logs(userlog = userlog, timestamp = timestamp, action = action)
                            if insert_logs:
                                db.session.add(insert_logs)
                                db.session.commit()

                            db.session.add(new_user)
                            db.session.commit()
                        except Exception as e:
                            db.session.rollback()
                        flash('User added successfully!', 'add_account')
    return redirect(url_for('dbModel.manage_account'))

@dbModel_route.route('/edit_account', methods=['POST'])
def edit_account():
    if g.current_role != "Admin" and g.current_role != "BOR":
        return redirect(url_for('dbModel.login'))

    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))
    
    if request.method == 'POST':
        user_id = request.form.get('id')
        new_username = request.form['new_username']
        new_email = request.form['new_email']
        new_firstname = request.form['new_firstname']
        new_lastname = request.form['new_lastname']
        new_password = request.form['new_password']
        new_role = request.form['new_role']
        new_department_A = request.form['new_department_A']
        new_program = request.form['new_program']
        new_mobile_number = request.form['new_mobile_number']
        

        if ' ' in new_password:
            flash('Password cannot contain spaces.', 'password_space')
            return redirect(url_for('dbModel.manage_account'))
        if ' ' in new_username:
            flash('Password cannot contain spaces.', 'username_space')
            return redirect(url_for('dbModel.manage_account'))
        
        # Hash the password
        hashed_password = generate_password_hash(new_password)
        
        # Check if the email format is valid and ends with '@gmail.com'
        if not is_valid_email(new_email):
            flash('Invalid email format. Only Gmail accounts are allowed.', 'password_space')
            return redirect(url_for('dbModel.manage_account'))

        
            
        user = Users.query.get(user_id)

        if user:
            # Check if the user is an admin
            if user.role == "Admin":
                # Check if there are any other admin users in the system
                other_admins = Users.query.filter(Users.role == "Admin", Users.id != user.id).first()
                if other_admins and user.program != new_program:
                    flash('Cannot change program for admin users.', 'existing_username')
                    return redirect(url_for('dbModel.manage_account'))
            
            # Check if the new values already exist in the table
            if user.username != new_username:
                existing_username = Users.query.filter_by(username=new_username).first()
                if existing_username:
                    flash(f'Username "{new_username}" already exists. Please choose a different username.', 'existing_username')
                    return redirect(url_for('dbModel.manage_account'))
            if user.email != new_email:
                existing_email = Users.query.filter_by(email=new_email).first()
                if existing_email:
                    flash(f'Email "{new_email}" already exists. Please choose a different email.', 'existing_username')
                    return redirect(url_for('dbModel.manage_account'))
            if user.program != new_program:
                existing_program = Users.query.filter_by(program=new_program).first()
                if existing_program:
                    flash(f'Program "{new_program}" already exists. Please choose a different program.', 'existing_username')
            
            existing_mobile_number = Users.query.filter_by(mobile_number=new_mobile_number).first()
            if len(new_mobile_number) < 11:
                flash('Mobile number must be at least 11 digits long.', 'existing_username')
                return redirect(url_for('dbModel.manage_account'))
            elif existing_mobile_number and existing_mobile_number.id != user.id:
                flash(f'Mobile Number: "{new_mobile_number}" already exists.', 'existing_username')
                return redirect(url_for('dbModel.manage_account'))

            # Rest of your code for updating the user's account...


            userlog = g.current_user
            action = f'UPDATED account named {new_firstname} {new_lastname}.'
            ph_tz = pytz.timezone('Asia/Manila')
            ph_time = datetime.now(ph_tz)
            timestamp1 = ph_time.strftime('%Y-%m-%d %H:%M:%S')
            timestamp = convert_date1(timestamp1)
            insert_logs = Logs(userlog = userlog, timestamp = timestamp, action = action)
            if insert_logs:
                db.session.add(insert_logs)
                db.session.commit()

            """
            if new_profile_picture.filename != '':
                # Read the binary data from the uploaded file
                profile_picture_data = new_profile_picture.read()

                # Update the user's profile picture field with the binary data
                user.profile_picture = profile_picture_data
            """
            user.username = new_username
            user.email = new_email
            user.firstname = new_firstname
            user.lastname = new_lastname
            user.password = hashed_password
            user.role = new_role
            user.program = new_program
            user.department_A= new_department_A
            user.mobile_number= new_mobile_number

            db.session.commit()
            flash('Account updated successfully!', 'edit_account')

        return redirect(url_for('dbModel.manage_account'))

@dbModel_route.route('/delete_account/<int:id>', methods=['GET'])
def delete_account(id):
    if g.current_role != "Admin" and g.current_role != "BOR":
        return redirect(url_for('dbModel.login'))

    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))
    
    user = Users.query.get(id)

    if user:
        if user.role in ['Admin', 'BOR']:
            flash('Cannot delete admin account!', 'existing_program')
            return redirect(url_for('dbModel.manage_account'))

        userlog = g.current_user
        action = f'DELETED account named {user.firstname} {user.lastname}.'
        ph_tz = pytz.timezone('Asia/Manila')
        ph_time = datetime.now(ph_tz)
        timestamp1 = ph_time.strftime('%Y-%m-%d %H:%M:%S')
        timestamp = convert_date1(timestamp1)
        insert_logs = Logs(userlog = userlog, timestamp = timestamp, action = action)
        if insert_logs:
                db.session.add(insert_logs)
                db.session.commit()
        try:
            db.session.delete(user)
            db.session.commit()
            flash('Account deleted successfully!', 'delete_account')
        except Exception as e:
            db.session.rollback()
    return redirect(url_for('dbModel.manage_account'))


########################### FOR DEPARTMENT ##################################

@dbModel_route.route("/add_department", methods=["POST"])
def add_department():
    if g.current_role != "Admin" and g.current_role != "BOR":
        return redirect(url_for('dbModel.login'))

    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))
    
    if request.method == "POST":
        department_A = request.form.get("department_A")
        department_F = request.form.get("department_F")
    

        # Check if the username already exists in the database
        existing_department_F = Department.query.filter_by(department_F=department_F).first()
        existing_department_A = Department.query.filter_by(department_A=department_A).first()

        if existing_department_A:
            flash(f'Department "{department_A}" already exists.', 'existing_username')
            return redirect(url_for('dbModel.manage_account'))

        if existing_department_F:
            flash(f'Department "{department_F}" already exists.', 'existing_username')
            return redirect(url_for('dbModel.manage_account'))
        
        new_department = Department(department_A=department_A, department_F=department_F)
        if new_department: 
            userlog = g.current_user
            action = f'ADDED new department named {new_department.department_A} {new_department.department_F}'
            ph_tz = pytz.timezone('Asia/Manila')
            ph_time = datetime.now(ph_tz)
            timestamp1 = ph_time.strftime('%Y-%m-%d %H:%M:%S')
            timestamp = convert_date1(timestamp1)
            insert_logs = Logs(userlog = userlog, timestamp = timestamp, action = action)
            if insert_logs:
                db.session.add(insert_logs)
                db.session.commit()

            db.session.add(new_department)
            db.session.commit()
            flash('Department added successfully!', 'add_account')
    return redirect(url_for('dbModel.manage_account'))

@dbModel_route.route('/edit_department', methods=['POST'])
def edit_department():
    if g.current_role != "Admin" and g.current_role != "BOR":
        return redirect(url_for('dbModel.login'))

    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))
    
    if request.method == 'POST':
        department_id = request.form.get('id')
        new_department_A = request.form['new_department_A']
        new_department_F = request.form['new_department_F']
       
        department = Department.query.get(department_id)
        
        if department:

             # Check if the new values are different from the existing values
            if department.department_F != new_department_F:
                # Check if the new values already exist in the table
                existing_department = Department.query.filter_by(department_F=new_department_F).first()
                if existing_department:
                    flash(f'Department "{new_department_F}" already exists!', 'existing_username')
                    return redirect(url_for('dbModel.manage_account'))

            userlog = g.current_user
            action = f'UPDATED department {new_department_F}.'
            ph_tz = pytz.timezone('Asia/Manila')
            ph_time = datetime.now(ph_tz)
            timestamp1 = ph_time.strftime('%Y-%m-%d %H:%M:%S')
            timestamp = convert_date1(timestamp1)
            insert_logs = Logs(userlog = userlog, timestamp = timestamp, action = action)
            if insert_logs:
                db.session.add(insert_logs)
                db.session.commit()

            department.department_A = new_department_A
            department.department_F = new_department_F
          
            db.session.commit()
            flash('Department updated successfully!', 'edit_account')

        return redirect(url_for('dbModel.manage_account'))

@dbModel_route.route('/delete_department/<int:id>', methods=['GET'])
def delete_department(id):
    if g.current_role != "Admin" and g.current_role != "BOR":
        return redirect(url_for('dbModel.login'))

    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))
    
    department = Department.query.get(id)

    if department:
        userlog = g.current_user
        action = f'DELETED department {department.department_F}.'
        ph_tz = pytz.timezone('Asia/Manila')
        ph_time = datetime.now(ph_tz)
        timestamp1 = ph_time.strftime('%Y-%m-%d %H:%M:%S')
        timestamp = convert_date1(timestamp1)
        insert_logs = Logs(userlog = userlog, timestamp = timestamp, action = action)
        if insert_logs:
                db.session.add(insert_logs)
                db.session.commit()
        try:
            # Delete associated users
            users_in_department = Users.query.filter_by(department_A=department.department_F).all()
            for user in users_in_department:
                user.department_A = None  # Remove association with the deleted department
                db.session.add(user)
            db.session.commit()

            db.session.delete(department)
            db.session.commit()
            flash('Account deleted successfully!', 'delete_account')
        except Exception as e:
            db.session.rollback()
    return redirect(url_for('dbModel.manage_account'))

############################  FOR COORDINATOR ROUTE  ############################
@dbModel_route.route('/coordinator/<data>')
def coordinator(data):
    if g.current_role != "Admin" and g.current_role != "BOR":
        return redirect(url_for('dbModel.login'))
    
    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))
    return render_template("coordinator.html", data=data)

############################  DISPLAYING MANAGE COMMUNITY DATA  ############################
@dbModel_route.route("/get_community_data", methods=['GET'])
def get_community_data():
    try:
        program = request.args.get("program")

        if program:
            community_data = [
                {
                    'community': record.community,
                    'program': record.program,
                    'subprogram': record.subprogram,
                    'week': record.week,
                    'totalWeek': record.totalWeek,
                    'user': record.user,
                    'department': record.department,
                    'subDepartment': record.subDepartment,
                    'start_date': record.start_date,
                    'end_date': record.end_date,
                    'status': record.status,
                    'budget': record.budget
                }
                for record in Community.query.filter_by(program=program).all()
            ]
            if community_data:
                return jsonify(community_data)
            else:
                # Handle the case when no data is found
                return jsonify({'message': 'No data found for the program.'}), 200
          
        else:
            # Handle the case when "program" is not provided
            return make_response("Program not specified", 400)


    except Exception as e:
        # Log the error for debugging
        print(str(e))
        return make_response("Internal Server Error", 500)

@dbModel_route.route("/community_data_list")
def community_data_list():
    try:
        community_data = [
            {
                    'community': record.community,
                    'program': record.program,
                    'subprogram': record.subprogram,
                    'week': record.week,
                    'totalWeek': record.totalWeek,
                    'user': record.user,
                    'department': record.department,
                    'subDepartment': record.subDepartment,
                    'status': record.status,
                    'budget': record.budget
            }
                for record in Community.query.all()
            ]
        return jsonify(community_data)
    except Exception as e:
        # Log the error for debugging
        print(str(e))
        return make_response("Internal Server Error", 500)

@dbModel_route.route("/manage_community")
def manage_community():
    if g.current_role != "Admin" and g.current_role != "BOR":
        return redirect(url_for('dbModel.login'))

    form = Form()
    placeholder_choice = ("", "-- Select Program --")
    form.program.choices = [placeholder_choice[1]] + [program.program for program in Program.query.all()]
    form.program.default = ""
    form.process()
    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))
     # Fetch all user records from the database
    all_data = Community.query.filter_by(status="Ongoing").all()
    program8 = Program.query.all()
    department = Department.query.all()
    user1 = Users.query.all()
    return render_template("community.html", community = all_data, form=form, program8=program8, user1 = user1, department=department)

############################ ASSIGNED PROGRAM FOR COORDINATOR ############################
@dbModel_route.route("/subprogram1/<get_program>")
def get_program(get_program):
    sub = Users.query.filter_by(program=get_program).all()
    subArray = [{'firstname': user.firstname, 'lastname': user.lastname} for user in sub]  
    return jsonify({'users': subArray})

@dbModel_route.route("/department1/<get_department>")
def get_department(get_department):
    sub = Users.query.filter_by(program=get_department).all()
    subArray = [{'department_A': user.department_A} for user in sub]  
    return jsonify({'users': subArray})


############################  CRUD FOR MANAGE COMMUNITY  ############################
@dbModel_route.route("/add_community", methods=["POST"])
def add_community():
    if g.current_role != "Admin" and g.current_role != "BOR":
        return redirect(url_for('dbModel.login'))

    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))
    
    if request.method == "POST":
        community = request.form.get("community")
        program = request.form.get("program")
        subprogram = request.form.get("subprogram")
        start_date1 = request.form.get("start_date")
        end_date1 = request.form.get("end_date")
        week = 0
        totalWeek = request.form.get("totalWeek")
        user = request.form.get("user")
        department_A = request.form.get("department_A")
        department = request.form.get("lead")
        subDepartment = request.form.get("support")
        volunteer = request.form.get("volunteer")
        status = "Ongoing"
        budget = request.form.get("budget")

        #Convert date
        start_date = convert_date(start_date1)
        end_date = convert_date(end_date1)

         # Access uploaded files
        cpf_file = request.files['CPF']
        cesap_file = request.files['CESAP']
        cna_file = request.files['CNA']
      

        existing_community = Community.query.filter_by(user= user, community=community, program = program, subprogram=subprogram).first()

        if existing_community is None:
            cpf_data = cpf_file.read()
            cesap_data = cesap_file.read()
            cna_data = cna_file.read()

            new_community = Community(community=community, program=program, subprogram=subprogram, start_date=start_date,
            end_date=end_date, week=week, totalWeek=totalWeek, user=user, department=department, subDepartment=subDepartment, status=status, budget = budget, cpf_filename=cpf_file.filename, cpf=cpf_data, cesap_filename=cesap_file.filename, cesap=cesap_data,
            cna_filename = cna_file.filename, cna=cna_data, department_A=department_A, volunteer=volunteer)

            userlog = g.current_user
            action = f'ADDED new {program} project to {community} .'
            ph_tz = pytz.timezone('Asia/Manila')
            ph_time = datetime.now(ph_tz)
            timestamp1 = ph_time.strftime('%Y-%m-%d %H:%M:%S')
            timestamp = convert_date1(timestamp1)
            insert_logs = Logs(userlog = userlog, timestamp = timestamp, action = action)
            if insert_logs:
                db.session.add(insert_logs)
                db.session.commit()

            db.session.add(new_community)
            db.session.commit()
            flash('New community project added!', 'add_community')

            new_subprogram = Subprogram(program=program, subprogram=subprogram)
            db.session.add(new_subprogram)
            db.session.commit()
            
        else:
            flash(f"Sorry, '{subprogram}' is already taken in {{community}}.", 'existing_community')
        return redirect(url_for('dbModel.manage_community'))
    return redirect(url_for('dbModel.manage_community'))

#EDIT COMMUNITY NOT NEEDED SO COMMENT 
'''
@dbModel_route.route('/edit_community', methods=['POST'])
def edit_community():
    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))
    
    if request.method == 'POST':
        user_id = request.form.get('id')  # Get the user ID from the form
        new_community = request.form['new_community']
        new_program = request.form['new_program']
        new_subprogram = request.form['new_subprogram']
        new_week= request.form['new_week']
        new_totalWeek = request.form['new_totalWeek']
        new_user = request.form['new_user']
        
        userlog = g.current_user
        action = f'UPDATE {community}'
        ph_tz = pytz.timezone('Asia/Manila')
        ph_time = datetime.now(ph_tz)
        timestamp1 = ph_time.strftime('%Y-%m-%d %H:%M:%S')
        timestamp = convert_date1(timestamp1)
        insert_logs = Logs(userlog = userlog, timestamp = timestamp, action = action)
        if insert_logs:
            db.session.add(insert_logs)
            db.session.commit()     
        # Query the user by ID
        user = Community.query.get(user_id)
        
        if user:
            # Update the user's information
            user.community = new_community
            user.program = new_program
            user.subprogram = new_subprogram
            user.week = new_week
            user.totalWeek = new_totalWeek
            user.user = new_user

            # Commit the changes to the database
            db.session.commit()
            flash('Account updated successfully!', 'success')
        else:
            flash('User not found. Please try again.', 'error')

        return redirect(url_for('dbModel.manage_community'))
'''

@dbModel_route.route('/delete_community/<int:id>', methods=['GET'])
def delete_community(id):
    if g.current_role != "Admin" and g.current_role != "BOR":
        return redirect(url_for('dbModel.login'))

    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))
    
    community = Community.query.get(id)
    program = request.args.get('program')
    subprogram = request.args.get('subprogram')
    community_name = request.args.get('community')

    subprogram_record = Subprogram.query.filter_by(program=program, subprogram=subprogram).first()

    if community:

        data_to_move = Community.query.filter_by(community=community_name, program = program, subprogram=subprogram).first()
            # Iterate through the data and move it to CPFARCHIVE
                
                # Create a new row in CPFARCHIVE
        new_row = Archive(
                community=data_to_move.community, 
                program=data_to_move.program, 
                subprogram=data_to_move.subprogram, 
                start_date=data_to_move.start_date,
                end_date=data_to_move.end_date, 
                week=data_to_move.week, 
                totalWeek=data_to_move.totalWeek, 
                user=data_to_move.user, 
                department=data_to_move.department, 
                subDepartment=data_to_move.subDepartment, 
                status=data_to_move.status, 
                budget = data_to_move.budget, 
                cpf_filename=data_to_move.cpf_filename, 
                cpf=data_to_move.cpf, 
                cesap_filename=data_to_move.cesap_filename, 
                cesap=data_to_move.cesap,
                cna_filename = data_to_move.cna_filename, 
                cna=data_to_move.cna,
                department_A = data_to_move.department_A, 
                volunteer=data_to_move.volunteer,
                url = "None"
        )
        db.session.add(new_row)
        db.session.commit()   

        userlog = g.current_user
        action = f'DELETED {program} project of {community_name}'
        ph_tz = pytz.timezone('Asia/Manila')
        ph_time = datetime.now(ph_tz)
        timestamp1 = ph_time.strftime('%Y-%m-%d %H:%M:%S')
        timestamp = convert_date1(timestamp1)
        insert_logs = Logs(userlog = userlog, timestamp = timestamp, action = action)
        if insert_logs:
            db.session.add(insert_logs)
            db.session.commit()  

        try:
            # Delete the user from the database
            db.session.delete(community)
            db.session.commit()

            
        except Exception as e:
            db.session.rollback()
            # You may want to log the exception for debugging purposes
    else:
        flash('User not found. Please try again.', 'error')
    
    if subprogram_record:
        try:
            # Delete the 'Upload' record from the database
            db.session.delete(subprogram_record)
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
    flash('Delete successfully!', 'delete_account')
    return redirect(url_for('dbModel.manage_community'))

############################### FOR PENDING COMMUNITY FUNCTION ###################################
@dbModel_route.route("/manage_pending")
def manage_pending():
    if g.current_role != "Admin" and g.current_role != "BOR":
        return redirect(url_for('dbModel.login'))

    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))
     # Fetch all user records from the database
    all_data = Pending_project.query.all()
    return render_template("pending.html", pending_project_data = all_data)

@dbModel_route.route('/delete_pending/<int:id>', methods=['GET'])
def delete_pending(id):
    if g.current_role != "Admin" and g.current_role != "BOR":
        return redirect(url_for('dbModel.login'))
        
    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))
    
    community = Pending_project.query.get(id)

    if community:
        userlog = g.current_user
        action = f'DELETED pending {community.program} project of {community.community}'
        ph_tz = pytz.timezone('Asia/Manila')
        ph_time = datetime.now(ph_tz)
        timestamp1 = ph_time.strftime('%Y-%m-%d %H:%M:%S')
        timestamp = convert_date1(timestamp1)
        insert_logs = Logs(userlog = userlog, timestamp = timestamp, action = action)
        if insert_logs:
            db.session.add(insert_logs)
            db.session.commit()
        try:
            # Delete the user from the database
            db.session.delete(community)
            db.session.commit()
            flash('Delete successfully!', 'delete_pending')
        except Exception as e:
            db.session.rollback()
            # You may want to log the exception for debugging purposes
    else:
        flash('User not found. Please try again.', 'error')
    return redirect(url_for('dbModel.manage_pending'))

@dbModel_route.route('/view_pending/<int:pending_id>', methods=['GET'])
def view_pending(pending_id):
    p = Pending_project.query.get(pending_id)

    return render_template("pending_details.html", community=p.community, program=p.program, subprogram = p.subprogram, totalWeek = p.totalWeek, user=p.user, start_date = p.start_date, end_date = p.end_date, department=p.department, subDepartment = p.subDepartment, cpf_filename=p.cpf_filename, cesap_filename=p.cesap_filename, cna_filename=p.cna_filename, budget=p.budget, comments=p.comments, department_A=p.department_A, volunteer=p.volunteer)

@dbModel_route.route('/view_cpf/<program>/<subprogram>/<community>/<cpf_filename>', methods=['GET'])
def view_cpf(program, subprogram, community, cpf_filename):
    upload_entry = Pending_project.query.filter_by(community = community, program = program, subprogram = subprogram, cpf_filename=cpf_filename).first()
    if upload_entry:
        # Determine the content type based on the file extension
        content_type = "application/octet-stream"
        filename = upload_entry.cpf_filename.lower()

        if filename.endswith((".jpg", ".jpeg", ".png", ".gif")):
            content_type = "image"

        # Serve the file with appropriate content type and Content-Disposition
        response = Response(upload_entry.cpf, content_type=content_type)

        if content_type.startswith("image"):
            # If it's an image, set Content-Disposition to inline for display
            response.headers["Content-Disposition"] = "inline"
        else:
            # For other types, set Content-Disposition to attachment for download
            response.headers[
                "Content-Disposition"] = f'attachment; filename="{upload_entry.cpf_filename}"'
        if filename.endswith(".pdf"):
            response = Response(upload_entry.cpf,
                                content_type="application/pdf")
        return response
    return "File not found", 404

@dbModel_route.route('/view_cna/<program>/<subprogram>/<community>/<cna_filename>', methods=['GET'])
def view_cna(program, subprogram, community, cna_filename):
    upload_entry = Pending_project.query.filter_by(community = community, program = program, subprogram = subprogram, cna_filename=cna_filename).first()
    if upload_entry:
        # Determine the content type based on the file extension
        content_type = "application/octet-stream"
        filename = upload_entry.cna_filename.lower()

        if filename.endswith((".jpg", ".jpeg", ".png", ".gif")):
            content_type = "image"

        # Serve the file with appropriate content type and Content-Disposition
        response = Response(upload_entry.cna, content_type=content_type)

        if content_type.startswith("image"):
            # If it's an image, set Content-Disposition to inline for display
            response.headers["Content-Disposition"] = "inline"
        else:
            # For other types, set Content-Disposition to attachment for download
            response.headers[
                "Content-Disposition"] = f'attachment; filename="{upload_entry.cna_filename}"'
        if filename.endswith(".pdf"):
            response = Response(upload_entry.cna,
                                content_type="application/pdf")
        return response
    return "File not found", 404

@dbModel_route.route('/view_cesap/<program>/<subprogram>/<community>/<cesap_filename>', methods=['GET'])
def view_cesap(program, subprogram, community, cesap_filename):
    upload_entry = Pending_project.query.filter_by(community = community, program = program, subprogram = subprogram, cesap_filename=cesap_filename).first()
    if upload_entry:
        # Determine the content type based on the file extension
        content_type = "application/octet-stream"
        filename = upload_entry.cesap_filename.lower()

        if filename.endswith((".jpg", ".jpeg", ".png", ".gif")):
            content_type = "image"

        # Serve the file with appropriate content type and Content-Disposition
        response = Response(upload_entry.cesap, content_type=content_type)

        if content_type.startswith("image"):
            # If it's an image, set Content-Disposition to inline for display
            response.headers["Content-Disposition"] = "inline"
        else:
            # For other types, set Content-Disposition to attachment for download
            response.headers[
                "Content-Disposition"] = f'attachment; filename="{upload_entry.cesap_filename}"'
        if filename.endswith(".pdf"):
            response = Response(upload_entry.cesap,
                                content_type="application/pdf")
        return response
    return "File not found", 404

@dbModel_route.route("/approve", methods=["POST"])
def approve():
    if g.current_role != "Admin" and g.current_role != "BOR":
        return redirect(url_for('dbModel.login'))

    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))
    
    if request.method == "POST":
        community = request.form.get("community")
        program = request.form.get("program")
        subprogram = request.form.get("subprogram")
        user = request.form.get("user")
        
        existing_community = Community.query.filter_by(user= user, community=community, program = program, subprogram=subprogram).first()

        if existing_community is None:
            data_to_move = Pending_project.query.filter_by(user= user, community=community, program = program, subprogram=subprogram).first()
            # Iterate through the data and move it to CPFARCHIVE
        
                # Create a new row in CPFARCHIVE
            new_row = Community(
                    community=data_to_move.community, 
                    program=data_to_move.program, 
                    subprogram=data_to_move.subprogram, 
                    start_date=data_to_move.start_date,
                    end_date=data_to_move.end_date, 
                    week=data_to_move.week, 
                    totalWeek=data_to_move.totalWeek, 
                    user=data_to_move.user, 
                    department=data_to_move.department, 
                    subDepartment=data_to_move.subDepartment, 
                    status="Ongoing", 
                    budget = data_to_move.budget, 
                    cpf_filename=data_to_move.cpf_filename, 
                    cpf=data_to_move.cpf, 
                    cesap_filename=data_to_move.cesap_filename, 
                    cesap=data_to_move.cesap,
                    cna_filename = data_to_move.cna_filename, 
                    cna=data_to_move.cna,
                    department_A = data_to_move.department_A, 
                    volunteer=data_to_move.volunteer
            )

            userlog = g.current_user
            action = f'APPROVE pending {program} project of {community}'
            ph_tz = pytz.timezone('Asia/Manila')
            ph_time = datetime.now(ph_tz)
            timestamp1 = ph_time.strftime('%Y-%m-%d %H:%M:%S')
            timestamp = convert_date1(timestamp1)
            insert_logs = Logs(userlog = userlog, timestamp = timestamp, action = action)
            if insert_logs:
                db.session.add(insert_logs)
                db.session.commit()
                db.session.add(new_row)
                db.session.commit()
                flash('Approved community project!', 'add_community')

            pending_delete = Pending_project.query.filter_by(community=community, program = program, subprogram=subprogram).first()
            if pending_delete:
                try:
                    # Delete the user from the database
                    db.session.delete(pending_delete)
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    # You may want to log the exception for debugging purposes
            else:
                flash('User not found. Please try again.', 'error')
        else:
            flash(f"Sorry, '{subprogram}' is already taken in {{community}}.", 'existing_community')

        #FOR SUBPROGRAM
        existing_subprogram = Subprogram.query.filter_by(program = program, subprogram=subprogram).first()
        if existing_subprogram is None:
            new_subprogram = Subprogram(program=program, subprogram=subprogram)
            db.session.add(new_subprogram)
            db.session.commit()
  
        return redirect(url_for('dbModel.manage_pending'))
       
    return redirect(url_for('dbModel.manage_pending'))

@dbModel_route.route("/decline", methods=["POST"])
def decline():
    if g.current_role != "Admin" and g.current_role != "BOR":
        return redirect(url_for('dbModel.login'))
    community = request.args.get('community')
    program = request.args.get('program')
    subprogram = request.args.get('subprogram')
    comments = request.form.get('comments')
    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))
    
    if request.method == "POST":
        p = Pending_project.query.filter_by(community=community, program = program, subprogram=subprogram).first()

        if p:
            userlog = g.current_user
            action = f'DECLINED pending {program} project of {community}'
            ph_tz = pytz.timezone('Asia/Manila')
            ph_time = datetime.now(ph_tz)
            timestamp1 = ph_time.strftime('%Y-%m-%d %H:%M:%S')
            timestamp = convert_date1(timestamp1)
            insert_logs = Logs(userlog = userlog, timestamp = timestamp, action = action)
            if insert_logs:
                db.session.add(insert_logs)
                db.session.commit()

            p.status = "Declined"
            p.comments=comments 
            db.session.commit()
        return redirect(url_for('dbModel.manage_pending'))
       
    return redirect(url_for('dbModel.manage_pending'))

############################### UPDATE WEEK BASED FROM Subprogram ###############################
@dbModel_route.route('/update_week', methods=['POST'])
def update_week():
    data = request.get_json()
    community = data['community']
    subprogram = data['subprogram']
    totalCheckboxes = data['totalCheckboxes']
    program = data['program']

    # Query the database to get records with the specified subprogram
    communities = Community.query.filter_by(community = community, program=program, subprogram=subprogram).all()

    for community in communities:
        community.week = totalCheckboxes

    userlog = g.current_user
    action = f'UPDATED week progress of {program} project in {community}'
    ph_tz = pytz.timezone('Asia/Manila')
    ph_time = datetime.now(ph_tz)
    timestamp1 = ph_time.strftime('%Y-%m-%d %H:%M:%S')
    timestamp = convert_date1(timestamp1)
    insert_logs = Logs(userlog = userlog, timestamp = timestamp, action = action)
    if insert_logs:
        db.session.add(insert_logs)
        db.session.commit()
    db.session.commit()
    return jsonify({'message': 'Week column updated for the specified subprogram.'})

############################### UPDATE STATUS BASED FROM Subprogram ###############################
@dbModel_route.route('/update_status', methods=['POST'])
def update_status():
    data = request.get_json()
    community = data['community']
    subprogram = data['subprogram']
    program = data['program']
    status = data['status']

    # Query the database to get a single record with the specified subprogram
    community_to_update = Community.query.filter_by(community=community, program=program, subprogram=subprogram).first()

    if community_to_update:
        # Update the status for the specific record
        community_to_update.status = status
        db.session.commit()
        return jsonify({'message': 'Status updated successfully.'})
    else:
        return jsonify({'message': 'Record not found.'}), 404

############################### ARCHIVE PROJECT ###############################
@dbModel_route.route('/archive_project', methods=['POST'])
def archive_project():
    if g.current_role != "Admin" and g.current_role != "BOR":
        return redirect(url_for('dbModel.login'))

    data = request.get_json()
    community = data['community']
    subprogram = data['subprogram']
    program = data['program']
    status = data['status']
    url = data.get('url', '')

    data_to_move = Community.query.filter_by(community=community, program = program, subprogram=subprogram).first()
    # Iterate through the data and move it to CPFARCHIVE
        
        # Create a new row in CPFARCHIVE
    new_row = Archive(
        community=data_to_move.community, 
        program=data_to_move.program, 
        subprogram=data_to_move.subprogram, 
        start_date=data_to_move.start_date,
        end_date=data_to_move.end_date, 
        week=data_to_move.week, 
        totalWeek=data_to_move.totalWeek, 
        user=data_to_move.user, 
        department=data_to_move.department, 
        subDepartment=data_to_move.subDepartment, 
        status="Completed", 
        budget = data_to_move.budget, 
        cpf_filename=data_to_move.cpf_filename, 
        cpf=data_to_move.cpf, 
        cesap_filename=data_to_move.cesap_filename, 
        cesap=data_to_move.cesap,
        cna_filename = data_to_move.cna_filename, 
        cna=data_to_move.cna,
        department_A = data_to_move.department_A, 
        volunteer=data_to_move.volunteer,
        url=url  # Assign the URL value
    )
    userlog = g.current_user
    action = f'ARCHIVED {program} project of {community}'
    ph_tz = pytz.timezone('Asia/Manila')
    ph_time = datetime.now(ph_tz)
    timestamp1 = ph_time.strftime('%Y-%m-%d %H:%M:%S')
    timestamp = convert_date1(timestamp1)
    insert_logs = Logs(userlog = userlog, timestamp = timestamp, action = action)
    if insert_logs:
        db.session.add(insert_logs)
        db.session.commit()

    db.session.add(new_row)
    db.session.commit()

    community_delete = Community.query.filter_by(community=community, program = program, subprogram=subprogram).first()
    if community_delete:
        try:
                # Delete the user from the database
            db.session.delete(community_delete)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
                # You may want to log the exception for debugging purposes
    else:
        flash('User not found. Please try again.', 'error')
   

    return jsonify({'message': 'Data archived.'})

############################### display kaakbay program and coordinator ###############################
def get_ongoing_count(session, program_name):
    result = db.session.query(
        Community.program,
        func.sum(case((Community.status == 'Ongoing', 1), else_=0)).label('ongoing_count')
    ).filter(Community.program == program_name).group_by(Community.program).all()
    
    if result:
        return result[0][1]
    else:
        return 0

def get_completed_count(session, program_name):
    result = db.session.query(
        Community.program,
        func.sum(case((Community.status == 'Completed', 1), else_=0)).label('completed_count')
    ).filter(Community.program == program_name).group_by(Community.program).all()
    
    if result:
        return result[0][1]
    else:
        return 0

@dbModel_route.route("/kaakbay_program")
def kaakbay_program():
    if g.current_role != "Admin" and g.current_role != "BOR":
        return redirect(url_for('dbModel.login'))
    
    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))
    
    literacy_program_data = Users.query.filter_by(program="Literacy").first()
    economic_program_data = Users.query.filter_by(program="Socio-economic").first()
    environmental_program_data = Users.query.filter_by(program="Environmental Stewardship").first()
    health_program_data = Users.query.filter_by(program="Health and Wellness").first()
    cultural_program_data = Users.query.filter_by(program="Cultural Enhancement").first()
    values_program_data = Users.query.filter_by(program="Values Formation").first()
    disaster_program_data = Users.query.filter_by(program="Disaster Management").first()
    gender_program_data = Users.query.filter_by(program="Gender and Development").first()

    literacy_firstname = literacy_program_data.username if literacy_program_data else None
    economic_firstname = economic_program_data.username if economic_program_data else None
    environmental_firstname = environmental_program_data.username if environmental_program_data else None
    health_firstname = health_program_data.username if health_program_data else None
    cultural_firstname = cultural_program_data.username if cultural_program_data else None
    values_firstname = values_program_data.username if values_program_data else None
    disaster_firstname = disaster_program_data.username if disaster_program_data else None
    gender_firstname = gender_program_data.username if gender_program_data else None


    program_names = ['Literacy', 'Socio-economic', 'Environmental Stewardship', 'Health and Wellness', 'Cultural Enhancement', 'Values Formation', 'Disaster Management', 'Gender and Development' ]
    program_ongoing_counts = {}
    program_completed_counts = {}

    for program_name in program_names:
        ongoing_count = get_ongoing_count(session, program_name)
        program_ongoing_counts[program_name] = ongoing_count
        
    for program_name in program_names:
        completed_count = get_completed_count(session, program_name)
        program_completed_counts[program_name] = completed_count
    
    return render_template("kaakbay_program.html", literacy_firstname=literacy_firstname,
                      economic_firstname=economic_firstname,
                      environmental_firstname=environmental_firstname,
                      health_firstname=health_firstname,
                      cultural_firstname=cultural_firstname,
                      values_firstname=values_firstname,
                      disaster_firstname=disaster_firstname,
                      gender_firstname=gender_firstname,
                      literacy_ongoing_count = program_ongoing_counts.get('Literacy', 0),
                      literacy_completed_count = program_completed_counts.get('Literacy', 0),
                      socio_ongoing_count = program_ongoing_counts.get('Socio-economic', 0),
                      socio_completed_count = program_completed_counts.get('Socio-economic', 0),
                      environmental_ongoing_count = program_ongoing_counts.get('Environmental Stewardship', 0),
                      environmental_completed_count = program_completed_counts.get('Environmental Stewardship', 0),
                      health_ongoing_count = program_ongoing_counts.get('Health and Wellness', 0),
                      health_completed_count = program_completed_counts.get('Health and Wellness', 0),
                      cultural_ongoing_count = program_ongoing_counts.get('Cultural Enhancement', 0),
                      cultural_completed_count = program_completed_counts.get('Cultural Enhancement', 0),
                      values_ongoing_count = program_ongoing_counts.get('Values Formation', 0),
                      values_completed_count = program_completed_counts.get('Values Formation', 0),
                      disaster_ongoing_count = program_ongoing_counts.get('Disaster Management', 0),
                      disaster_completed_count = program_completed_counts.get('Disaster Management', 0),
                      gender_ongoing_count = program_ongoing_counts.get('Gender and Development', 0),
                      gender_completed_count = program_completed_counts.get('Gender and Development', 0),
                      )

############################### CHANGED PASSWORD ###############################
@dbModel_route.route("/change_password")
def change_password():
    if g.current_role != "Admin" and g.current_role != "BOR":
        return redirect(url_for('dbModel.login'))
    
    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))
    return render_template("change_password.html")

@dbModel_route.route("/new_password", methods=["POST"])
def new_password():
    if g.current_role != "Admin" and g.current_role != "BOR":
        return redirect(url_for('dbModel.login'))

    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))

    if request.method == "POST":
        old_password = request.form['old_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        user = Users.query.filter_by(id=session['user_id']).first()

        if ' ' in new_password:
            flash('Password cannot contain spaces.', 'newpassword_space')
            return redirect(url_for('dbModel.change_password'))
        
        if user:
            # Retrieve the hashed password from the database
            hashed_password = user.password
            
            # Check if the old password matches the hashed password stored in the database
            if check_password_hash(hashed_password, old_password):
                if new_password == confirm_password:
                    # Hash the new password before storing
                    hashed_new_password = generate_password_hash(new_password)
                    user.password = hashed_new_password
                    
                    # Commit changes to the database
                    db.session.commit()
                    
                    # Log the password change action
                    userlog = g.current_user
                    action = f'CHANGED password'
                    ph_tz = pytz.timezone('Asia/Manila')
                    ph_time = datetime.now(ph_tz)
                    timestamp1 = ph_time.strftime('%Y-%m-%d %H:%M:%S')
                    timestamp = convert_date1(timestamp1)
                    insert_logs = Logs(userlog=userlog, timestamp=timestamp, action=action)
                    if insert_logs:
                        db.session.add(insert_logs)
                        db.session.commit()

                    flash('Password successfully changed.', 'new_password')
                    return redirect(url_for('dbModel.change_password'))
                else:
                    flash('New password and confirmation do not match.', 'not_match')
            else:
                flash('Incorrect old password.', 'wrong_old')
        else:
            flash('User not found.', 'user_not_found')
    
    return redirect(url_for('dbModel.change_password'))

############################### CURRENT PROJECT FILES ###############################
@dbModel_route.route("/project_files")
def project_files():
    if g.current_role != "Admin" and g.current_role != "BOR":
        return redirect(url_for('dbModel.login'))

    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))
    return render_template("project_files.html")

@dbModel_route.route("/project_file_list/<data>")
def project_file_list(data):
    if g.current_role != "Admin" and g.current_role != "BOR":
        return redirect(url_for('dbModel.login'))

    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))
    
    # Dynamically generate the years
    current_year = datetime.now().year

    project_file_list = Community.query.filter_by(program=data).all()

    return render_template("project_table.html", current_year=current_year, project_file_list=project_file_list, data=data)

@dbModel_route.route("/view_project/<int:project_id>")
def view_project(project_id):
    if g.current_role != "Admin" and g.current_role != "BOR":
        return redirect(url_for('dbModel.login'))

    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))

    p = Community.query.get(project_id)

    cpf_data_filename = p.cpf_filename
    cesap_data_filename = p.cesap_filename
    cna_data_filename = p.cna_filename

    return render_template("project_details.html", community=p.community, program=p.program, subprogram = p.subprogram, totalWeek = p.totalWeek, user=p.user, start_date = p.start_date, end_date = p.end_date, department=p.department, subDepartment = p.subDepartment, cpf_filename=cpf_data_filename, cesap_filename=cesap_data_filename, cna_filename=cna_data_filename, department_A=p.department_A, volunteer=p.volunteer)

@dbModel_route.route("/delete_project/<int:project_id>")
def delete_project(project_id):
    if g.current_role != "Admin" and g.current_role != "BOR":
        return redirect(url_for('dbModel.login'))

    data = request.args.get('data')
    community = request.args.get('community')
    program = request.args.get('program')
    subprogram = request.args.get('subprogram')

    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))
    
    p = Community.query.filter_by(id=project_id).first()
    if p:
        try:
            data_to_move = Community.query.filter_by(community=community, program = program, subprogram=subprogram).first()
            # Iterate through the data and move it to CPFARCHIVE
                
                # Create a new row in CPFARCHIVE
            new_row = Archive(
                community=data_to_move.community, 
                program=data_to_move.program, 
                subprogram=data_to_move.subprogram, 
                start_date=data_to_move.start_date,
                end_date=data_to_move.end_date, 
                week=data_to_move.week, 
                totalWeek=data_to_move.totalWeek, 
                user=data_to_move.user, 
                department=data_to_move.department, 
                subDepartment=data_to_move.subDepartment, 
                status=data_to_move.status, 
                budget = data_to_move.budget, 
                cpf_filename=data_to_move.cpf_filename, 
                cpf=data_to_move.cpf, 
                cesap_filename=data_to_move.cesap_filename, 
                cesap=data_to_move.cesap,
                cna_filename = data_to_move.cna_filename, 
                cna=data_to_move.cna,
                department_A = data_to_move.department_A, 
                volunteer=data_to_move.volunteer,
                url = "None"
                
            )
            userlog = g.current_user
            action = f'DELETED {program} project of {community}'
            ph_tz = pytz.timezone('Asia/Manila')
            ph_time = datetime.now(ph_tz)
            timestamp1 = ph_time.strftime('%Y-%m-%d %H:%M:%S')
            timestamp = convert_date1(timestamp1)
            insert_logs = Logs(userlog = userlog, timestamp = timestamp, action = action)
            if insert_logs:
                db.session.add(insert_logs)
                db.session.commit()

            db.session.add(new_row)
            db.session.commit()
            
            # Delete the user from the database
            db.session.delete(p)
            db.session.commit()

            subprogram_record = Subprogram.query.filter_by(program=program, subprogram=subprogram).first()
            if subprogram_record:
                try:
                    # Delete the 'Upload' record from the database
                    db.session.delete(subprogram_record)
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
        except Exception as e:
            db.session.rollback()
            # You may want to log the exception for debugging purposes
        
    else:
        flash('User not found. Please try again.', 'error')
    
    

    flash('Delete successfully!', 'delete_project')
    project_file_list = Community.query.filter_by(program=data).all()
    current_year = datetime.now().year
    return render_template("project_table.html",current_year=current_year, project_file_list=project_file_list, data=data)

@dbModel_route.route('/view_cpf_project/<program>/<subprogram>/<community>/<cpf_filename>', methods=['GET'])
def view_cpf_project(program, subprogram, community, cpf_filename):
    upload_entry = Community.query.filter_by(community = community, program = program, subprogram = subprogram, cpf_filename=cpf_filename).first()
    if upload_entry:
        # Determine the content type based on the file extension
        content_type = "application/octet-stream"
        filename = upload_entry.cpf_filename.lower()

        if filename.endswith((".jpg", ".jpeg", ".png", ".gif")):
            content_type = "image"

        # Serve the file with appropriate content type and Content-Disposition
        response = Response(upload_entry.cpf, content_type=content_type)

        if content_type.startswith("image"):
            # If it's an image, set Content-Disposition to inline for display
            response.headers["Content-Disposition"] = "inline"
        else:
            # For other types, set Content-Disposition to attachment for download
            response.headers[
                "Content-Disposition"] = f'attachment; filename="{upload_entry.cpf_filename}"'
        if filename.endswith(".pdf"):
            response = Response(upload_entry.cpf,
                                content_type="application/pdf")
        return response
    return "File not found", 404

@dbModel_route.route('/view_cna_project/<program>/<subprogram>/<community>/<cna_filename>', methods=['GET'])
def view_cna_project(program, subprogram, community, cna_filename):
    upload_entry = Community.query.filter_by(community = community, program = program, subprogram = subprogram, cna_filename=cna_filename).first()
    if upload_entry:
        # Determine the content type based on the file extension
        content_type = "application/octet-stream"
        filename = upload_entry.cna_filename.lower()

        if filename.endswith((".jpg", ".jpeg", ".png", ".gif")):
            content_type = "image"

        # Serve the file with appropriate content type and Content-Disposition
        response = Response(upload_entry.cna, content_type=content_type)

        if content_type.startswith("image"):
            # If it's an image, set Content-Disposition to inline for display
            response.headers["Content-Disposition"] = "inline"
        else:
            # For other types, set Content-Disposition to attachment for download
            response.headers[
                "Content-Disposition"] = f'attachment; filename="{upload_entry.cna_filename}"'
        if filename.endswith(".pdf"):
            response = Response(upload_entry.cna,
                                content_type="application/pdf")
        return response
    return "File not found", 404

@dbModel_route.route('/view_cesap_project/<program>/<subprogram>/<community>/<cesap_filename>', methods=['GET'])
def view_cesap_project(program, subprogram, community, cesap_filename):
    upload_entry = Community.query.filter_by(community = community, program = program, subprogram = subprogram, cesap_filename=cesap_filename).first()
    if upload_entry:
        # Determine the content type based on the file extension
        content_type = "application/octet-stream"
        filename = upload_entry.cesap_filename.lower()

        if filename.endswith((".jpg", ".jpeg", ".png", ".gif")):
            content_type = "image"

        # Serve the file with appropriate content type and Content-Disposition
        response = Response(upload_entry.cesap, content_type=content_type)

        if content_type.startswith("image"):
            # If it's an image, set Content-Disposition to inline for display
            response.headers["Content-Disposition"] = "inline"
        else:
            # For other types, set Content-Disposition to attachment for download
            response.headers[
                "Content-Disposition"] = f'attachment; filename="{upload_entry.cesap_filename}"'
        if filename.endswith(".pdf"):
            response = Response(upload_entry.cesap,
                                content_type="application/pdf")
        return response
    return "File not found", 404

############################### ARCHIVED FILES ###############################

@dbModel_route.route("/archived_files")
def archived_files():
    if g.current_role != "Admin" and g.current_role != "BOR":
        return redirect(url_for('dbModel.login'))
        
    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))
    return render_template("archived_files.html")

@dbModel_route.route("/archived_file_list/<data>")
def archived_file_list(data):
    if g.current_role != "Admin" and g.current_role != "BOR":
        return redirect(url_for('dbModel.login'))

    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))
    # Dynamically generate the years
    current_year = datetime.now().year
    
    archived_file_list = Archive.query.filter_by(program=data).all()
    return render_template("archived_table.html", current_year=current_year, archived_file_list=archived_file_list, data=data)

@dbModel_route.route("/view_archived/<int:project_id>")
def view_archived(project_id):
    if g.current_role != "Admin" and g.current_role != "BOR":
        return redirect(url_for('dbModel.login'))

    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))

    p = Archive.query.get(project_id)

    cpf_data_filename = p.cpf_filename
    cesap_data_filename = p.cesap_filename
    cna_data_filename = p.cna_filename

    return render_template("archived_details.html", community=p.community, program=p.program, subprogram = p.subprogram, totalWeek = p.totalWeek, user=p.user, start_date = p.start_date, end_date = p.end_date, department=p.department, subDepartment = p.subDepartment, cpf_filename=cpf_data_filename, cesap_filename=cesap_data_filename, cna_filename=cna_data_filename, department_A=p.department_A, volunteer=p.volunteer)

@dbModel_route.route("/delete_archived/<int:project_id>")
def delete_archived(project_id):
    if g.current_role != "Admin" and g.current_role != "BOR":
        return redirect(url_for('dbModel.login'))

    data = request.args.get('data')
    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))
    
    p = Archive.query.filter_by(id=project_id).first()
    if p:
        userlog = g.current_user
        action = f'DELETED archived {p.program} project of {p.community}'
        ph_tz = pytz.timezone('Asia/Manila')
        ph_time = datetime.now(ph_tz)
        timestamp1 = ph_time.strftime('%Y-%m-%d %H:%M:%S')
        timestamp = convert_date1(timestamp1)
        insert_logs = Logs(userlog = userlog, timestamp = timestamp, action = action)
        if insert_logs:
            db.session.add(insert_logs)
            db.session.commit()
        try:
            # Delete the user from the database
            db.session.delete(p)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            # You may want to log the exception for debugging purposes
    else:
        flash('User not found. Please try again.', 'error')
    
    flash('Delete successfully!', 'delete_project')
    archived_file_list = Archive.query.filter_by(program=data).all()
    current_year = datetime.now().year
    return render_template("archived_table.html",current_year=current_year, archived_file_list=archived_file_list, data=data)

@dbModel_route.route('/view_cpf_archived/<program>/<subprogram>/<community>/<cpf_filename>', methods=['GET'])
def view_cpf_archived(program, subprogram, community, cpf_filename):
    upload_entry = Archive.query.filter_by(community = community, program = program, subprogram = subprogram, cpf_filename=cpf_filename).first()
    if upload_entry:
        # Determine the content type based on the file extension
        content_type = "application/octet-stream"
        filename = upload_entry.cpf_filename.lower()

        if filename.endswith((".jpg", ".jpeg", ".png", ".gif")):
            content_type = "image"

        # Serve the file with appropriate content type and Content-Disposition
        response = Response(upload_entry.cpf, content_type=content_type)

        if content_type.startswith("image"):
            # If it's an image, set Content-Disposition to inline for display
            response.headers["Content-Disposition"] = "inline"
        else:
            # For other types, set Content-Disposition to attachment for download
            response.headers[
                "Content-Disposition"] = f'attachment; filename="{upload_entry.cpf_filename}"'
        if filename.endswith(".pdf"):
            response = Response(upload_entry.cpf,
                                content_type="application/pdf")
        return response
    return "File not found", 404

@dbModel_route.route('/view_cna_archived/<program>/<subprogram>/<community>/<cna_filename>', methods=['GET'])
def view_cna_archived(program, subprogram, community, cna_filename):
    upload_entry = Archive.query.filter_by(community = community, program = program, subprogram = subprogram, cna_filename=cna_filename).first()
    if upload_entry:
        # Determine the content type based on the file extension
        content_type = "application/octet-stream"
        filename = upload_entry.cna_filename.lower()

        if filename.endswith((".jpg", ".jpeg", ".png", ".gif")):
            content_type = "image"

        # Serve the file with appropriate content type and Content-Disposition
        response = Response(upload_entry.cna, content_type=content_type)

        if content_type.startswith("image"):
            # If it's an image, set Content-Disposition to inline for display
            response.headers["Content-Disposition"] = "inline"
        else:
            # For other types, set Content-Disposition to attachment for download
            response.headers[
                "Content-Disposition"] = f'attachment; filename="{upload_entry.cna_filename}"'
        if filename.endswith(".pdf"):
            response = Response(upload_entry.cna,
                                content_type="application/pdf")
        return response
    return "File not found", 404

@dbModel_route.route('/view_cesap_archived/<program>/<subprogram>/<community>/<cesap_filename>', methods=['GET'])
def view_cesap_archived(program, subprogram, community, cesap_filename):
    upload_entry = Archive.query.filter_by(community = community, program = program, subprogram = subprogram, cesap_filename=cesap_filename).first()
    if upload_entry:
        # Determine the content type based on the file extension
        content_type = "application/octet-stream"
        filename = upload_entry.cesap_filename.lower()

        if filename.endswith((".jpg", ".jpeg", ".png", ".gif")):
            content_type = "image"

        # Serve the file with appropriate content type and Content-Disposition
        response = Response(upload_entry.cesap, content_type=content_type)

        if content_type.startswith("image"):
            # If it's an image, set Content-Disposition to inline for display
            response.headers["Content-Disposition"] = "inline"
        else:
            # For other types, set Content-Disposition to attachment for download
            response.headers[
                "Content-Disposition"] = f'attachment; filename="{upload_entry.cesap_filename}"'
        if filename.endswith(".pdf"):
            response = Response(upload_entry.cesap,
                                content_type="application/pdf")
        return response
    return "File not found", 404

############################### USER LOGS ###############################
@dbModel_route.route("/logs_activity")
def logs_activity():
    if g.current_role != "Admin" and g.current_role != "BOR":
        return redirect(url_for('dbModel.login'))
        
    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))
    UserLogs = Logs.query.order_by(Logs.timestamp.desc()).all()

    return render_template("Logfolder.html", UserLogs = UserLogs)

############################### PLANS FILES ###############################

@dbModel_route.route("/cesu_plans")
def cesu_plans():
    if g.current_role != "Admin" and g.current_role != "BOR":
        return redirect(url_for('dbModel.login'))

    form = Form()
    placeholder_choice = ("", "-- Select Program --")
    form.program.choices = [placeholder_choice[1]] + [program.program for program in Program.query.all()]
    form.program.default = ""
    form.process()
    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))
    
    # Dynamically generate the years
    current_year = datetime.now().year
     # Fetch all user records from the database
    all_data = Plan.query.filter_by(status="Planning").all()
    program8 = Program.query.all()
    user1 = Users.query.all()
    return render_template("cesu_plans.html", current_year=current_year, community = all_data, form=form, program8=program8, user1 = user1)

@dbModel_route.route("/add_plan", methods=["POST"])
def add_plan():
    if g.current_role != "Admin" and g.current_role != "BOR":
        return redirect(url_for('dbModel.login'))

    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))
    
    if request.method == "POST":
        community = request.form.get("community")
        program = request.form.get("program")
        subprogram = request.form.get("subprogram")
        start_date1 = request.form.get("start_date")
        end_date1 = request.form.get("end_date")
        week = 0
        totalWeek = request.form.get("totalWeek")
        user = request.form.get("user")
        department = request.form.get("lead")
        subDepartment = request.form.get("support")
        status = "Planning"
        budget = request.form.get("budget")

        #Convert date
        start_date = convert_date(start_date1)
        end_date = convert_date(end_date1)

         # Access uploaded files
        cpf_file = request.files['CPF']
        cesap_file = request.files['CESAP']
        cna_file = request.files['CNA']

        department_A = request.form.get("department_A")
        volunteer = request.form.get("volunteer")
      

        existing_plan= Plan.query.filter_by(user= user, status= status, community=community, program = program, subprogram=subprogram).first()

        if existing_plan is None:
            cpf_data = cpf_file.read()
            cesap_data = cesap_file.read()
            cna_data = cna_file.read()

            new_plan = Plan(community=community, program=program, subprogram=subprogram, start_date=start_date,
            end_date=end_date, week=week, totalWeek=totalWeek, user=user, department=department, subDepartment=subDepartment, status=status, budget = budget, cpf_filename=cpf_file.filename, cpf=cpf_data, cesap_filename=cesap_file.filename, cesap=cesap_data,
            cna_filename = cna_file.filename, cna=cna_data, department_A=department_A, volunteer=volunteer)

            userlog = g.current_user
            action = f'ADDED new {program} project to {community} for planning.'
            ph_tz = pytz.timezone('Asia/Manila')
            ph_time = datetime.now(ph_tz)
            timestamp1 = ph_time.strftime('%Y-%m-%d %H:%M:%S')
            timestamp = convert_date1(timestamp1)
            insert_logs = Logs(userlog = userlog, timestamp = timestamp, action = action)
            if insert_logs:
                db.session.add(insert_logs)
                db.session.commit()

            db.session.add(new_plan)
            db.session.commit()
            flash('New community project added for planning!', 'add_community')

            new_subprogram = Subprogram(program=program, subprogram=subprogram)
            db.session.add(new_subprogram)
            db.session.commit()
            
        else:
            flash(f"Sorry, '{subprogram}' is already taken in {{community}}.", 'existing_community')
        return redirect(url_for('dbModel.cesu_plans'))
    return redirect(url_for('dbModel.cesu_plans'))

@dbModel_route.route('/delete_plan/<int:id>', methods=['GET'])
def delete_plan(id):
    if g.current_role != "Admin" and g.current_role != "BOR":
        return redirect(url_for('dbModel.login'))

    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))
    
    cesu_plan = Plan.query.get(id)
    program = request.args.get('program')
    subprogram = request.args.get('subprogram')
    community_name = request.args.get('community')

    subprogram_record = Subprogram.query.filter_by(program=program, subprogram=subprogram).first()

    if cesu_plan:
        userlog = g.current_user
        action = f'DELETED {program} project of {community_name} from CESU planner'
        ph_tz = pytz.timezone('Asia/Manila')
        ph_time = datetime.now(ph_tz)
        timestamp1 = ph_time.strftime('%Y-%m-%d %H:%M:%S')
        timestamp = convert_date1(timestamp1)
        insert_logs = Logs(userlog = userlog, timestamp = timestamp, action = action)
        if insert_logs:
            db.session.add(insert_logs)
            db.session.commit()  

        try:
            # Delete the user from the database
            db.session.delete(cesu_plan)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            # You may want to log the exception for debugging purposes
    else:
        flash('User not found. Please try again.', 'error')
    
    if subprogram_record:
        try:
            # Delete the 'Upload' record from the database
            db.session.delete(subprogram_record)
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
    flash('Delete successfully!', 'delete_account')
    return redirect(url_for('dbModel.cesu_plans'))

@dbModel_route.route("/view_plan/<int:plan_id>")
def view_plan(plan_id):
    if g.current_role != "Admin" and g.current_role != "BOR":
        return redirect(url_for('dbModel.login'))

    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))

    p = Plan.query.get(plan_id)

    cpf_data_filename = p.cpf_filename
    cesap_data_filename = p.cesap_filename
    cna_data_filename = p.cna_filename

    return render_template("plan_details.html",id=p.id, community=p.community, program=p.program, subprogram = p.subprogram, totalWeek = p.totalWeek, user=p.user, start_date = p.start_date, end_date = p.end_date, department=p.department, subDepartment = p.subDepartment, cpf_filename=cpf_data_filename, cesap_filename=cesap_data_filename, cna_filename=cna_data_filename, budget=p.budget, department_A=p.department_A, volunteer=p.volunteer)


@dbModel_route.route('/view_cpf_plan/<program>/<subprogram>/<community>/<cpf_filename>', methods=['GET'])
def view_cpf_plan(program, subprogram, community, cpf_filename):
    upload_entry = Plan.query.filter_by(community = community, program = program, subprogram = subprogram, cpf_filename=cpf_filename).first()
    if upload_entry:
        # Determine the content type based on the file extension
        content_type = "application/octet-stream"
        filename = upload_entry.cpf_filename.lower()

        if filename.endswith((".jpg", ".jpeg", ".png", ".gif")):
            content_type = "image"

        # Serve the file with appropriate content type and Content-Disposition
        response = Response(upload_entry.cpf, content_type=content_type)

        if content_type.startswith("image"):
            # If it's an image, set Content-Disposition to inline for display
            response.headers["Content-Disposition"] = "inline"
        else:
            # For other types, set Content-Disposition to attachment for download
            response.headers[
                "Content-Disposition"] = f'attachment; filename="{upload_entry.cpf_filename}"'
        if filename.endswith(".pdf"):
            response = Response(upload_entry.cpf,
                                content_type="application/pdf")
        return response
    return "File not found", 404

########################Fundraising Activity#############################
@dbModel_route.route("/fundraising_activity")
def fund():
    # Check if the user is an admin
    if g.current_role != "Admin" and g.current_role != "BOR":
        return redirect(url_for('dbModel.login'))

    # Check if the user is logged in
    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))

    # Dynamically generate the years
    current_year = datetime.now().year

    # Render the template with the current year and the next four years
    return render_template("fund.html", current_year=current_year)


@dbModel_route.route('/view_cna_plan/<program>/<subprogram>/<community>/<cna_filename>', methods=['GET'])
def view_cna_plan(program, subprogram, community, cna_filename):
    upload_entry = Plan.query.filter_by(community = community, program = program, subprogram = subprogram, cna_filename=cna_filename).first()
    if upload_entry:
        # Determine the content type based on the file extension
        content_type = "application/octet-stream"
        filename = upload_entry.cna_filename.lower()

        if filename.endswith((".jpg", ".jpeg", ".png", ".gif")):
            content_type = "image"

        # Serve the file with appropriate content type and Content-Disposition
        response = Response(upload_entry.cna, content_type=content_type)

        if content_type.startswith("image"):
            # If it's an image, set Content-Disposition to inline for display
            response.headers["Content-Disposition"] = "inline"
        else:
            # For other types, set Content-Disposition to attachment for download
            response.headers[
                "Content-Disposition"] = f'attachment; filename="{upload_entry.cna_filename}"'
        if filename.endswith(".pdf"):
            response = Response(upload_entry.cna,
                                content_type="application/pdf")
        return response
    return "File not found", 404

@dbModel_route.route('/view_cesap_plan/<program>/<subprogram>/<community>/<cesap_filename>', methods=['GET'])
def view_cesap_plan(program, subprogram, community, cesap_filename):
    upload_entry = Plan.query.filter_by(community = community, program = program, subprogram = subprogram, cesap_filename=cesap_filename).first()
    if upload_entry:
        # Determine the content type based on the file extension
        content_type = "application/octet-stream"
        filename = upload_entry.cesap_filename.lower()

        if filename.endswith((".jpg", ".jpeg", ".png", ".gif")):
            content_type = "image"

        # Serve the file with appropriate content type and Content-Disposition
        response = Response(upload_entry.cesap, content_type=content_type)

        if content_type.startswith("image"):
            # If it's an image, set Content-Disposition to inline for display
            response.headers["Content-Disposition"] = "inline"
        else:
            # For other types, set Content-Disposition to attachment for download
            response.headers[
                "Content-Disposition"] = f'attachment; filename="{upload_entry.cesap_filename}"'
        if filename.endswith(".pdf"):
            response = Response(upload_entry.cesap,
                                content_type="application/pdf")
        return response
    return "File not found", 404


@dbModel_route.route('/update_plan', methods=['POST'])
def update_plan():
    if g.current_role != "Admin" and g.current_role != "BOR":
        return redirect(url_for('dbModel.login'))

    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))
    
    if request.method == 'POST':
        plan_id = request.form.get('id')
        community = request.form.get('community')
        program = request.form['program']
        subprogram = request.form['subprogram']
        start_date1 = request.form['start_date']
        end_date1 = request.form['end_date']
        totalWeek = request.form['totalWeek']
        budget = request.form['budget']
        user = request.form['user']
        lead = request.form['lead']
        support = request.form['support']
        status = "Planning"
        department_A = request.form['department_A']
        volunteer = request.form['volunteer']
        
        
        #Convert date
        start_date = convert_date(start_date1)
        end_date = convert_date(end_date1)

        cesu_plan = Plan.query.get(plan_id)

        if cesu_plan:
            if not cesu_plan.cpf:
                cpf_file = request.files['CPF']
                cesu_plan.cpf_filename = cpf_file.filename
                cesu_plan.cpf = cpf_file.read()

            if not cesu_plan.cesap:
                cesap_file = request.files['CESAP']
                cesu_plan.cesap_filename = cesap_file.filename
                cesu_plan.cesap = cesap_file.read()

            if not cesu_plan.cna:
                cna_file = request.files['CNA']
                cesu_plan.cna_filename = cna_file.filename
                cesu_plan.cna = cna_file.read()

            cesu_plan.community = community
            cesu_plan.program = program
            cesu_plan.subprogram = subprogram
            cesu_plan.start_date = start_date
            cesu_plan.end_date = end_date
            cesu_plan.totalWeek = totalWeek
            cesu_plan.budget = budget
            cesu_plan.user = user
            cesu_plan.department = lead
            cesu_plan.subDepartment = support
            cesu_plan.status = status
            cesu_plan.department_A = department_A
            cesu_plan.volunteer = volunteer

            userlog = g.current_user
            action = f'UPDATED planned {program} projects of {community} from CESU Planner'
            ph_tz = pytz.timezone('Asia/Manila')
            ph_time = datetime.now(ph_tz)
            timestamp1 = ph_time.strftime('%Y-%m-%d %H:%M:%S')
            timestamp = convert_date1(timestamp1)
            insert_logs = Logs(userlog = userlog, timestamp = timestamp, action = action)
            if insert_logs:
                db.session.add(insert_logs)
                db.session.commit()
                
            db.session.commit()
            flash('Updated successfully!', 'edit_account')

        p = Plan.query.get(plan_id)

    return render_template("plan_details.html", id=p.id, community=p.community, program=p.program, subprogram = p.subprogram, totalWeek = p.totalWeek, user=p.user, start_date = p.start_date, end_date = p.end_date, department=p.department, subDepartment = p.subDepartment, cpf_filename=p.cpf_filename, cesap_filename=p.cesap_filename, cna_filename=p.cna_filename, budget=p.budget, department_A=p.department_A, volunteer=p.volunteer)

@dbModel_route.route('/delete_cpf_plan', methods=['POST'])
def delete_cpf_plan():
    if g.current_role != "Admin" and g.current_role != "BOR":
        return redirect(url_for('dbModel.login'))

    if request.method == 'POST':
        cpf_id = request.form.get('cpf_id')
        cesu_plan = Plan.query.filter_by(id=cpf_id).first()

        if cesu_plan:
            userlog = g.current_user
            action = f'DELETED CPF file : {cesu_plan.cpf_filename}'
            ph_tz = pytz.timezone('Asia/Manila')
            ph_time = datetime.now(ph_tz)
            timestamp1 = ph_time.strftime('%Y-%m-%d %H:%M:%S')
            timestamp = convert_date1(timestamp1)
            insert_logs = Logs(userlog = userlog, timestamp = timestamp, action = action)
            if insert_logs:
                db.session.add(insert_logs)
                db.session.commit()

            # Delete the file from the database
            cesu_plan.cpf = None
            cesu_plan.cpf_filename = None
            db.session.commit()
        
        p = Plan.query.get(cpf_id)

    return render_template("plan_details.html", id=p.id, community=p.community, program=p.program, subprogram = p.subprogram, totalWeek = p.totalWeek, user=p.user, start_date = p.start_date, end_date = p.end_date, department=p.department, subDepartment = p.subDepartment, cpf_filename=p.cpf_filename, cesap_filename=p.cesap_filename, cna_filename=p.cna_filename, budget=p.budget, department_A=p.department_A, volunteer=p.volunteer)

@dbModel_route.route('/delete_cesap_plan', methods=['POST'])
def delete_cesap_plan():
    if g.current_role != "Admin" and g.current_role != "BOR":
        return redirect(url_for('dbModel.login'))

    if request.method == 'POST':
        cesap_id = request.form.get('cesap_id')
        cesu_plan = Plan.query.filter_by(id=cesap_id).first()

        if cesu_plan:
            userlog = g.current_user
            action = f'DELETED CESAP file : {cesu_plan.cesap_filename}'
            ph_tz = pytz.timezone('Asia/Manila')
            ph_time = datetime.now(ph_tz)
            timestamp1 = ph_time.strftime('%Y-%m-%d %H:%M:%S')
            timestamp = convert_date1(timestamp1)
            insert_logs = Logs(userlog = userlog, timestamp = timestamp, action = action)
            if insert_logs:
                db.session.add(insert_logs)
                db.session.commit()

            # Delete the file from the database
            cesu_plan.cesap = None
            cesu_plan.cesap_filename = None
            db.session.commit()
        p = Plan.query.get(cesap_id)

    return render_template("plan_details.html", id=p.id, community=p.community, program=p.program, subprogram = p.subprogram, totalWeek = p.totalWeek, user=p.user, start_date = p.start_date, end_date = p.end_date, department=p.department, subDepartment = p.subDepartment, cpf_filename=p.cpf_filename, cesap_filename=p.cesap_filename, cna_filename=p.cna_filename, budget=p.budget, department_A=p.department_A, volunteer=p.volunteer)

@dbModel_route.route('/delete_cna_plan', methods=['POST'])
def delete_cna_plan():
    if g.current_role != "Admin" and g.current_role != "BOR":
        return redirect(url_for('dbModel.login'))

    if request.method == 'POST':
        cna_id = request.form.get('cna_id')
        cesu_plan = Plan.query.filter_by(id=cna_id).first()

        if cesu_plan:
            userlog = g.current_user
            action = f'DELETED CNA file : {cesu_plan.cna_filename}'
            ph_tz = pytz.timezone('Asia/Manila')
            ph_time = datetime.now(ph_tz)
            timestamp1 = ph_time.strftime('%Y-%m-%d %H:%M:%S')
            timestamp = convert_date1(timestamp1)
            insert_logs = Logs(userlog = userlog, timestamp = timestamp, action = action)
            if insert_logs:
                db.session.add(insert_logs)
                db.session.commit()

            # Delete the file from the database
            cesu_plan.cna = None
            cesu_plan.cna_filename = None
            db.session.commit()
        p = Plan.query.get(cna_id)

    return render_template("plan_details.html", id=p.id, community=p.community, program=p.program, subprogram = p.subprogram, totalWeek = p.totalWeek, user=p.user, start_date = p.start_date, end_date = p.end_date, department=p.department, subDepartment = p.subDepartment, cpf_filename=p.cpf_filename, cesap_filename=p.cesap_filename, cna_filename=p.cna_filename, budget=p.budget, department_A=p.department_A, volunteer=p.volunteer)

@dbModel_route.route("/deploy", methods=["POST"])
def deploy():
    if g.current_role != "Admin" and g.current_role != "BOR":
        return redirect(url_for('dbModel.login'))

    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))
    
    if request.method == "POST":
        community = request.form.get("community")
        program = request.form.get("program")
        subprogram = request.form.get("subprogram")
        
        existing_plan = Community.query.filter_by(community=community, program = program, subprogram=subprogram).first()

        if existing_plan is None:
            data_to_move = Plan.query.filter_by( community=community, program = program, subprogram=subprogram).first()

            new_row = Community(
                    community=data_to_move.community, 
                    program=data_to_move.program, 
                    subprogram=data_to_move.subprogram, 
                    start_date=data_to_move.start_date,
                    end_date=data_to_move.end_date, 
                    week=data_to_move.week, 
                    totalWeek=data_to_move.totalWeek, 
                    user=data_to_move.user, 
                    department=data_to_move.department, 
                    subDepartment=data_to_move.subDepartment, 
                    status="Ongoing", 
                    budget = data_to_move.budget, 
                    cpf_filename=data_to_move.cpf_filename, 
                    cpf=data_to_move.cpf, 
                    cesap_filename=data_to_move.cesap_filename, 
                    cesap=data_to_move.cesap,
                    cna_filename = data_to_move.cna_filename, 
                    cna=data_to_move.cna,
                    department_A = data_to_move.department_A, 
                    volunteer=data_to_move.volunteer
            )

            userlog = g.current_user
            action = f'Deployed {program} project of {community} from CESU Planner'
            ph_tz = pytz.timezone('Asia/Manila')
            ph_time = datetime.now(ph_tz)
            timestamp1 = ph_time.strftime('%Y-%m-%d %H:%M:%S')
            timestamp = convert_date1(timestamp1)
            insert_logs = Logs(userlog = userlog, timestamp = timestamp, action = action)
            if insert_logs:
                db.session.add(insert_logs)
                db.session.commit()
                db.session.add(new_row)
                db.session.commit()
                flash('Deploy community project!', 'add_community')

                community_plan = Plan.query.filter_by(community=community, program = program, subprogram=subprogram).first()
                if community_plan:
                    try:
                        # Delete the user from the database
                        db.session.delete(community_plan)
                        db.session.commit()
                    except Exception as e:
                        db.session.rollback()
                        # You may want to log the exception for debugging purposes
                #FOR SUBPROGRAM
                existing_subprogram = Subprogram.query.filter_by(program = program, subprogram=subprogram).first()
                if existing_subprogram is None:
                    new_subprogram = Subprogram(program=program, subprogram=subprogram)
                    db.session.add(new_subprogram)
                    db.session.commit()
        else:
            flash(f"Sorry, '{subprogram}' is already taken in {{community}}.", 'existing_community')

        return redirect(url_for('dbModel.cesu_plans'))
       
    return redirect(url_for('dbModel.cesu_plans'))


    ########################## EDIT PROFILE #######################


############################ EDIT PROFILE #############################
@dbModel_route.route("/edit_profile")
def edit_profile():
    if g.current_role != "Admin" and g.current_role != "BOR":
        return redirect(url_for('dbModel.login'))
    
    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))
    
    p = Users.query.filter_by(username = g.current_user).first()

    return render_template("edit_profile.html", id=p.id, username=p.username, firstname=p.firstname, lastname=p.lastname, email=p.email, mobile_number=p.mobile_number)


@dbModel_route.route('/update_profile', methods=['POST'])
def update_profile():
    if g.current_role != "Admin" and g.current_role != "BOR":
        return redirect(url_for('dbModel.login'))

    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))
    
    if request.method == 'POST':
        user_id = request.form.get('id')
        new_username = request.form['new_username']
        new_email = request.form['new_email']
        new_firstname = request.form['new_firstname']
        new_lastname = request.form['new_lastname']
        new_mobile_number = request.form['new_mobile_number']
         
        # Check if the email format is valid and ends with '@gmail.com'
        if not is_valid_email(new_email):
            flash('Invalid email format. Only Gmail accounts are allowed.', 'password_space')
            return redirect(url_for('dbModel.edit_profile'))

        user = Users.query.get(user_id)

        if user:
      
            # Check if the new values already exist in the table
            if user.username != new_username:
                existing_username = Users.query.filter_by(username=new_username).first()
                if existing_username:
                    flash(f'Username "{new_username}" already exists. Please choose a different username.', 'existing_username')
                    return redirect(url_for('dbModel.edit_profile'))
            if user.email != new_email:
                existing_email = Users.query.filter_by(email=new_email).first()
                if existing_email:
                    flash(f'Email "{new_email}" already exists. Please choose a different email.', 'existing_username')
                    return redirect(url_for('dbModel.edit_profile'))
            
            existing_mobile_number = Users.query.filter_by(mobile_number=new_mobile_number).first()
            if len(new_mobile_number) < 11:
                flash('Mobile number must be at least 11 digits long.', 'existing_username')
                return redirect(url_for('dbModel.edit_profile'))
            elif existing_mobile_number and existing_mobile_number.id != user.id:
                flash(f'Mobile Number: "{new_mobile_number}" already exists.', 'existing_username')
                return redirect(url_for('dbModel.edit_profile'))

            userlog = g.current_user
            action = f'UPDATED account named {new_firstname} {new_lastname}.'
            ph_tz = pytz.timezone('Asia/Manila')
            ph_time = datetime.now(ph_tz)
            timestamp1 = ph_time.strftime('%Y-%m-%d %H:%M:%S')
            timestamp = convert_date1(timestamp1)
            insert_logs = Logs(userlog = userlog, timestamp = timestamp, action = action)
            if insert_logs:
                db.session.add(insert_logs)
                db.session.commit()

            user.username = new_username
            user.email = new_email
            user.firstname = new_firstname
            user.lastname = new_lastname
            user.mobile_number= new_mobile_number

            db.session.commit()
            flash('Account updated successfully!', 'edit_account')

        return redirect(url_for('dbModel.edit_profile'))


@dbModel_route.route('/delete_picture', methods=['POST'])
def delete_picture():
    if request.method == 'POST':
        profile_id = request.form.get('edit-id')
        users_picture = Users.query.filter_by(id=profile_id).first()

        if users_picture:
            userlog = g.current_user
            action = f'{users_picture.username} DELETED Profile Picture'
            ph_tz = pytz.timezone('Asia/Manila')
            ph_time = datetime.now(ph_tz)
            timestamp1 = ph_time.strftime('%Y-%m-%d %H:%M:%S')
            timestamp = convert_date1(timestamp1)
            insert_logs = Logs(userlog = userlog, timestamp = timestamp, action = action)
            if insert_logs:
                db.session.add(insert_logs)
                db.session.commit()

            # Delete the file from the database
            users_picture.profile_picture = None
            
            db.session.commit()
        
        p = Users.query.get(profile_id)

    return redirect(url_for('dbModel.edit_profile'))

@dbModel_route.route('/update_picture', methods=['POST'])
def update_picture():
    if g.current_role != "Admin" and g.current_role != "BOR":
        return redirect(url_for('dbModel.login'))

    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))
    
    if request.method == 'POST':
        user_id = request.form.get('id')
        new_profile_picture = request.files['new_profile_picture']  # Use .get() instead of ['']
        
        user = Users.query.get(user_id)

        if user:

            userlog = g.current_user
            action = f'UPDATED account named {user.firstname} {user.lastname}.'
            ph_tz = pytz.timezone('Asia/Manila')
            ph_time = datetime.now(ph_tz)
            timestamp1 = ph_time.strftime('%Y-%m-%d %H:%M:%S')
            timestamp = convert_date1(timestamp1)
            insert_logs = Logs(userlog = userlog, timestamp = timestamp, action = action)
            if insert_logs:
                db.session.add(insert_logs)
                db.session.commit()

      
            if new_profile_picture.filename != '':
                # Read the binary data from the uploaded file
                profile_picture_data = new_profile_picture.read()

                # Update the user's profile picture field with the binary data
                user.profile_picture = profile_picture_data

            db.session.commit()
            flash('Account updated successfully!', 'edit_account')

        return redirect(url_for('dbModel.edit_profile'))


################## RESOURCES ################3333
@dbModel_route.route("/resources")
def resources():
    if g.current_role != "Admin" and g.current_role != "BOR":
        return redirect(url_for('dbModel.login'))

    form = Form()
    placeholder_choice = ("", "-- Select Program --")
    form.program.choices = [placeholder_choice[1]] + [program.program for program in Program.query.all()]
    form.program.default = ""
    form.process()
    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))
    
    # Dynamically generate the years
    current_year = datetime.now().year
     # Fetch all user records from the database
    all_data = Resources.query.all()
    program8 = Program.query.all()
    user1 = Users.query.all()
    return render_template("resources.html", current_year=current_year, community = all_data, form=form, program8=program8, user1 = user1)


@dbModel_route.route("/add_resources", methods=["POST"])
def add_resources():
    if g.current_role != "Admin" and g.current_role != "BOR":
        return redirect(url_for('dbModel.login'))

    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))
    
    if request.method == "POST":
        community = request.form.get("community")
        program = request.form.get("program")
        user = request.form.get("user")
        date1 = request.form.get("date")
        activity = request.form.get("activity")
        url = request.form.get("url")
     
        #Convert date
        date = convert_date(date1)
    
        existing_resources= Resources.query.filter_by(user= user, community=community, program = program, activity=activity).first()

        if existing_resources is None:
        
            new_resources = Resources(community=community, program=program, user=user, date=date, activity=activity, url=url)

            userlog = g.current_user
            action = f'ADDED new {program} project resources.'
            ph_tz = pytz.timezone('Asia/Manila')
            ph_time = datetime.now(ph_tz)
            timestamp1 = ph_time.strftime('%Y-%m-%d %H:%M:%S')
            timestamp = convert_date1(timestamp1)
            insert_logs = Logs(userlog = userlog, timestamp = timestamp, action = action)
            if insert_logs:
                db.session.add(insert_logs)
                db.session.commit()

            db.session.add(new_resources)
            db.session.commit()
            flash('New resources added', 'add_community')
        else:
            flash(f"Sorry, resources is already exist.", 'existing_community')
        return redirect(url_for('dbModel.resources'))
    return redirect(url_for('dbModel.resources'))

@dbModel_route.route('/delete_resources/<int:id>', methods=['GET'])
def delete_resources(id):
    if g.current_role != "Admin" and g.current_role != "BOR":
        return redirect(url_for('dbModel.login'))

    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))
    
    resources = Resources.query.get(id)
    program = request.args.get('program')
    community_name = request.args.get('community')

    if resources:
        userlog = g.current_user
        action = f'DELETED {program} project of {community_name} from CESU planner'
        ph_tz = pytz.timezone('Asia/Manila')
        ph_time = datetime.now(ph_tz)
        timestamp1 = ph_time.strftime('%Y-%m-%d %H:%M:%S')
        timestamp = convert_date1(timestamp1)
        insert_logs = Logs(userlog = userlog, timestamp = timestamp, action = action)
        if insert_logs:
            db.session.add(insert_logs)
            db.session.commit()  

        try:
            # Delete the user from the database
            db.session.delete(resources)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            # You may want to log the exception for debugging purposes
    else:
        flash('User not found. Please try again.', 'error')
    
    flash('Delete successfully!', 'delete_account')
    return redirect(url_for('dbModel.resources'))


