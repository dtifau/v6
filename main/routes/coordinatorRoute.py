from flask import Blueprint, url_for, redirect, request, session, flash, render_template, jsonify, make_response, g, redirect
from main.models.dbModel import Users, Community, Program, Subprogram, Role, Upload, Pending_project, Logs, Resources
from main import db
from main import Form
from flask import Response
from datetime import datetime
from sqlalchemy import func, case
import pytz, re
import base64
from werkzeug.security import generate_password_hash, check_password_hash 


coordinator_route = Blueprint('coordinator', __name__)


# Function to validate email format
def is_valid_email(email):
    # Regular expression pattern for validating email format
    pattern = r'^[\w\.-]+@gmail\.com$'
    return re.match(pattern, email) is not None

def convert_date1(datetime_str):
    return datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')

@coordinator_route.route("/coordinator_dashboard")
def coordinator_dashboard():
     # Check if the user is logged in
    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))
    return render_template("cDashboard.html")

def get_current_user():
    if 'user_id' in session:
        # Assuming you have a User model or some way to fetch the user by ID
        user = Users.query.get(session['user_id'])
        declined_count = Pending_project.query.filter_by(status="Declined", program=user.program).count()
            
        # Set a maximum value for pending_count
        max_declined_count = 9
        declined_count_display = min(declined_count, max_declined_count)

        # If pending_count is 9 or greater, display it as '9+'
        declined_count_display = '9+' if declined_count > max_declined_count else declined_count

        profile_picture_base64 = None
        if user:
            if user.profile_picture:
                # Convert the profile picture to base64 encoding
                profile_picture_base64 = base64.b64encode(user.profile_picture).decode('utf-8')
            return user.username, user.role, user.program, declined_count_display, user.firstname, user.lastname, user.department_A, profile_picture_base64
    return None, None, None, 0, None, None, None, None
    
@coordinator_route.before_request
def before_request():
    g.current_user, g.current_role, g.current_program, g.declined_count_display, g.current_firstname, g.current_lastname, g.current_department_A, g.profile_picture_base64 = get_current_user()

@coordinator_route.context_processor
def inject_current_user():
    current_program_coordinator = g.current_program
    return dict(current_user=g.current_user, current_role=g.current_role, current_program=g.current_program, declined_count = g.declined_count_display, current_firstname=g.current_firstname, current_lastname=g.current_lastname, current_department_A=g.current_department_A, profile_picture_base64 = g.profile_picture_base64)

@coordinator_route.route("/cClear_session")
def cClear_session():
    session.clear()
    userlog = g.current_user
    action = f'Logged out.'
    ph_tz = pytz.timezone('Asia/Manila')
    ph_time = datetime.now(ph_tz)
    timestamp1 = ph_time.strftime('%Y-%m-%d %H:%M:%S')
    timestamp = convert_date1(timestamp1)
    insert_logs = Logs(userlog = userlog, timestamp = timestamp, action = action)
    if insert_logs:
        db.session.add(insert_logs)
        db.session.commit()
    return redirect(url_for('dbModel.login'))

@coordinator_route.route('/cCoordinator')
def cCoordinator():
    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))
    return render_template("cCoordinator.html")


##################  FOR COMMUNITY CRUD  #######################
@coordinator_route.route("/cGet_community_data", methods=['GET'])
def cGet_community_data():
    try:
        # Retrieve the "program" parameter from the query string
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
                for record in Community.query.filter_by(program=g.current_program).all()
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

@coordinator_route.route("/cCommunity_data_list")
def cCommunity_data_list():
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
                for record in Community.query.filter_by(program=g.current_program).all()
            ]
        return jsonify(community_data)
    except Exception as e:
        # Log the error for debugging
        print(str(e))
        return make_response("Internal Server Error", 500)

@coordinator_route.route("/cManage_community")
def cManage_community():
    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))
     # Fetch all user records from the database
    all_data = Community.query.filter_by(program=g.current_program).all()
    return render_template("cCommunity.html", community = all_data)

# Function to convert date strings to Python date objects
def convert_date(date_str):
    return datetime.strptime(date_str, '%Y-%m-%d').date() 

@coordinator_route.route("/cAdd_community", methods=["POST"])
def cAdd_community():
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
        status = "For Review"
        budget = request.form.get("budget")
        department_A = request.form.get("department_A")
        volunteer = request.form.get("volunteer")


        #Convert date
        start_date = convert_date(start_date1)
        end_date = convert_date(end_date1)

         # Access uploaded files
        cpf_file = request.files['CPF']
        cesap_file = request.files['CESAP']
        cna_file = request.files['CNA']
      

        existing_community = Pending_project.query.filter_by(community=community, program = program, subprogram=subprogram).first()

        if existing_community is None:
            cpf_data = cpf_file.read()
            cesap_data = cesap_file.read()
            cna_data = cna_file.read()

            new_community = Pending_project(community=community, program=program, subprogram=subprogram, start_date=start_date,
            end_date=end_date, week=week, totalWeek=totalWeek, user=user, department=department, subDepartment=subDepartment, status=status, budget = budget, cpf_filename=cpf_file.filename, cpf=cpf_data, cesap_filename=cesap_file.filename, cesap=cesap_data,
            cna_filename = cna_file.filename, cna=cna_data, department_A=department_A, volunteer=volunteer)
            db.session.add(new_community)
            db.session.commit()
            userlog = g.current_user

            action = f'ADDED pending {program} project of {community}'
            ph_tz = pytz.timezone('Asia/Manila')
            ph_time = datetime.now(ph_tz)
            timestamp1 = ph_time.strftime('%Y-%m-%d %H:%M:%S')
            timestamp = convert_date1(timestamp1)
            insert_logs = Logs(userlog = userlog, timestamp = timestamp, action = action)
            if insert_logs:
                db.session.add(insert_logs)
                db.session.commit()
            flash('Pending project added!', 'add_community')
        else:
            return redirect(url_for('coordinator.cManage_community'))
        
        return redirect(url_for('coordinator.cManage_community'))
       
    return redirect(url_for('coordinator.cManage_community'))


############# UPDATE WEEK BASED FROM Subprogram ##############

@coordinator_route.route('/cUpdate_week', methods=['POST'])
def cUpdate_week():
    data = request.get_json()
    community = data['community']
    subprogram = data['subprogram']
    totalCheckboxes = data['totalCheckboxes']
    program = data['program']

    # Query the database to get records with the specified subprogram
    communities = Community.query.filter_by(community=community,program=program, subprogram=subprogram).all()

    for community in communities:
        # Update the "week" column to match the totalCheckboxes
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

############# UPDATE Status BASED FROM Subprogram ##############
@coordinator_route.route('/cUpdate_status', methods=['POST'])
def cUpdate_status():
    data = request.get_json()
    community = data['community']
    subprogram = data['subprogram']
    program = data['program']
    status = data['status']

    # Query the database to get records with the specified subprogram
    communities = Community.query.filter_by(program=program, subprogram=subprogram).all()

    for community in communities:
        community.status = status
    db.session.commit()
    return jsonify({'message': 'Week column updated for the specified subprogram.'})


#display kaakbay program and coordinator
def cGet_ongoing_count(session, program_name):
    result = db.session.query(
        Community.program,
        func.sum(case((Community.status == 'Ongoing', 1), else_=0)).label('ongoing_count')
    ).filter(Community.program == program_name).group_by(Community.program).all()
    
    if result:
        return result[0][1]
    else:
        return 0

def cGet_completed_count(session, program_name):
    result = db.session.query(
        Community.program,
        func.sum(case((Community.status == 'Completed', 1), else_=0)).label('completed_count')
    ).filter(Community.program == program_name).group_by(Community.program).all()
    
    if result:
        return result[0][1]
    else:
        return 0

############# changepassword ##############
@coordinator_route.route("/cChange_password")
def cChange_password():
    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))
   
    return render_template("cChange_password.html")

############# changepassword ##############

@coordinator_route.route("/cNew_password", methods=["POST"])
def cNew_password():
    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))

    if request.method == "POST":
        old_password = request.form['old_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        user = Users.query.filter_by(id=session['user_id']).first()
        
        if not user:
            flash('User not found.', 'user_not_found')
            return redirect(url_for('dbModel.login'))

        # Check if the old password matches the hashed password stored in the database
        if check_password_hash(user.password, old_password):
            if new_password == confirm_password:
                # Hash the new password before storing
                hashed_new_password = generate_password_hash(new_password)
                user.password = hashed_new_password
                db.session.commit()
                flash('Password successfully changed.', 'new_password')

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
                return redirect(url_for('coordinator.cChange_password'))
            else:
                flash('New password and confirmation do not match.', 'not_match')
        else:
            flash('Incorrect old password.', 'wrong_old')

    return redirect(url_for('coordinator.cChange_password'))


############################### COORDINATOR CURRENT PROJECT FILES ###############################

@coordinator_route.route("/cProject_file_list")
def cProject_file_list():
    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))
    project_file_list = Community.query.filter_by(program=g.current_program).all()

    # Dynamically generate the years
    current_year = datetime.now().year
    
    return render_template("cProject_table.html", current_year=current_year, project_file_list=project_file_list, data=g.current_program)

@coordinator_route.route("/cView_project/<int:project_id>")
def cView_project(project_id):
    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))

    p = Community.query.get(project_id)

    cpf_data_filename = p.cpf_filename
    cesap_data_filename = p.cesap_filename
    cna_data_filename = p.cna_filename

    return render_template("cProject_details.html", community=p.community, program=p.program, subprogram = p.subprogram, totalWeek = p.totalWeek, user=p.user, start_date = p.start_date, end_date = p.end_date, department=p.department, subDepartment = p.subDepartment, cpf_filename=cpf_data_filename, cesap_filename=cesap_data_filename, cna_filename=cna_data_filename, department_A=p.department_A, volunteer=p.volunteer)

@coordinator_route.route('/cView_cpf_project/<program>/<subprogram>/<community>/<cpf_filename>', methods=['GET'])
def cView_cpf_project(program, subprogram, community, cpf_filename):
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

@coordinator_route.route('/cView_cna_project/<program>/<subprogram>/<community>/<cna_filename>', methods=['GET'])
def cView_cna_project(program, subprogram, community, cna_filename):
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

@coordinator_route.route('/cView_cesap_project/<program>/<subprogram>/<community>/<cesap_filename>', methods=['GET'])
def cView_cesap_project(program, subprogram, community, cesap_filename):
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



############################### COORDINATOR PENDING PROJECT FILES ###############################
@coordinator_route.route("/cManage_pending")
def cManage_pending():
    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))
     # Fetch all user records from the database
    all_data = Pending_project.query.filter_by(program=g.current_program).all()
    return render_template("cPending.html", pending_project_data = all_data)

@coordinator_route.route('/cDelete_pending/<int:id>', methods=['GET'])
def cDelete_pending(id):
    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))
    
    community = Pending_project.query.get(id)
    if community:
        try:
            # Delete the user from the database
            db.session.delete(community)
            db.session.commit()

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
            flash('Delete successfully!', 'delete_pending')
        except Exception as e:
            db.session.rollback()
            # You may want to log the exception for debugging purposes
    else:
        flash('User not found. Please try again.', 'error')
    return redirect(url_for('coordinator.cManage_pending'))

@coordinator_route.route('/cView_pending/<int:pending_id>', methods=['GET'])
def cView_pending(pending_id):
    p = Pending_project.query.get(pending_id)

    return render_template("cPending_details.html", id=p.id, community=p.community, program=p.program, subprogram = p.subprogram, totalWeek = p.totalWeek, user=p.user, start_date = p.start_date, end_date = p.end_date, department=p.department, subDepartment = p.subDepartment, cpf_filename=p.cpf_filename, cesap_filename=p.cesap_filename, cna_filename=p.cna_filename, budget=p.budget, comments=p.comments, department_A=p.department_A, volunteer=p.volunteer)

@coordinator_route.route('/cView_cpf/<program>/<subprogram>/<community>/<cpf_filename>', methods=['GET'])
def cView_cpf(program, subprogram, community, cpf_filename):
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

@coordinator_route.route('/cView_cna/<program>/<subprogram>/<community>/<cna_filename>', methods=['GET'])
def cView_cna(program, subprogram, community, cna_filename):
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

@coordinator_route.route('/cView_cesap/<program>/<subprogram>/<community>/<cesap_filename>', methods=['GET'])
def cView_cesap(program, subprogram, community, cesap_filename):
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

@coordinator_route.route('/CPF_delete', methods=['POST'])
def CPF_delete():
    if request.method == 'POST':
        cpf_id = request.form.get('cpf_id')
        pending_project = Pending_project.query.filter_by(id=cpf_id).first()

        if pending_project:
            

            userlog = g.current_user
            action = f'DELETED CPF file : {pending_project.cpf_filename}'
            ph_tz = pytz.timezone('Asia/Manila')
            ph_time = datetime.now(ph_tz)
            timestamp1 = ph_time.strftime('%Y-%m-%d %H:%M:%S')
            timestamp = convert_date1(timestamp1)
            insert_logs = Logs(userlog = userlog, timestamp = timestamp, action = action)
            if insert_logs:
                db.session.add(insert_logs)
                db.session.commit()

            # Delete the file from the database
            pending_project.cpf = None
            pending_project.cpf_filename = None
            db.session.commit()
        
        p = Pending_project.query.get(cpf_id)

    return render_template("cPending_details.html", id=p.id, community=p.community, program=p.program, subprogram = p.subprogram, totalWeek = p.totalWeek, user=p.user, start_date = p.start_date, end_date = p.end_date, department=p.department, subDepartment = p.subDepartment, cpf_filename=p.cpf_filename, cesap_filename=p.cesap_filename, cna_filename=p.cna_filename, budget=p.budget, comments=p.comments, department_A=p.department_A, volunteer=p.volunteer)

@coordinator_route.route('/CESAP_delete', methods=['POST'])
def CESAP_delete():
    if request.method == 'POST':
        cesap_id = request.form.get('cesap_id')
        pending_project = Pending_project.query.filter_by(id=cesap_id).first()

        if pending_project:


            userlog = g.current_user
            action = f'DELETED CESAP file : {pending_project.cesap_filename}'
            ph_tz = pytz.timezone('Asia/Manila')
            ph_time = datetime.now(ph_tz)
            timestamp1 = ph_time.strftime('%Y-%m-%d %H:%M:%S')
            timestamp = convert_date1(timestamp1)
            insert_logs = Logs(userlog = userlog, timestamp = timestamp, action = action)
            if insert_logs:
                db.session.add(insert_logs)
                db.session.commit()

            # Delete the file from the database
            pending_project.cesap = None
            pending_project.cesap_filename = None
            db.session.commit()
        p = Pending_project.query.get(cesap_id)

    return render_template("cPending_details.html", id=p.id, community=p.community, program=p.program, subprogram = p.subprogram, totalWeek = p.totalWeek, user=p.user, start_date = p.start_date, end_date = p.end_date, department=p.department, subDepartment = p.subDepartment, cpf_filename=p.cpf_filename, cesap_filename=p.cesap_filename, cna_filename=p.cna_filename, budget=p.budget, comments=p.comments, department_A=p.department_A, volunteer=p.volunteer)

@coordinator_route.route('/CNA_delete', methods=['POST'])
def CNA_delete():
    if request.method == 'POST':
        cna_id = request.form.get('cna_id')
        pending_project = Pending_project.query.filter_by(id=cna_id).first()

        if pending_project:

            
            userlog = g.current_user
            action = f'DELETED CNA file : {pending_project.cna_filename}'
            ph_tz = pytz.timezone('Asia/Manila')
            ph_time = datetime.now(ph_tz)
            timestamp1 = ph_time.strftime('%Y-%m-%d %H:%M:%S')
            timestamp = convert_date1(timestamp1)
            insert_logs = Logs(userlog = userlog, timestamp = timestamp, action = action)
            if insert_logs:
                db.session.add(insert_logs)
                db.session.commit()

            # Delete the file from the database
            pending_project.cna = None
            pending_project.cna_filename = None
            db.session.commit()
        p = Pending_project.query.get(cna_id)

    return render_template("cPending_details.html", id=p.id, community=p.community, program=p.program, subprogram = p.subprogram, totalWeek = p.totalWeek, user=p.user, start_date = p.start_date, end_date = p.end_date, department=p.department, subDepartment = p.subDepartment, cpf_filename=p.cpf_filename, cesap_filename=p.cesap_filename, cna_filename=p.cna_filename, budget=p.budget, comments=p.comments, department_A=p.department_A, volunteer=p.volunteer)

@coordinator_route.route('/update_pending', methods=['POST'])
def update_pending():
    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))
    
    if request.method == 'POST':
        pending_id = request.form.get('id')
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
        status = "For Review"
        department_A = request.form['department_A']
        volunteer = request.form['volunteer']
        
        
        #Convert date
        start_date = convert_date(start_date1)
        end_date = convert_date(end_date1)

        pending = Pending_project.query.get(pending_id)

        if pending:
            if not pending.cpf:
                cpf_file = request.files['CPF']
                pending.cpf_filename = cpf_file.filename
                pending.cpf = cpf_file.read()

            if not pending.cesap:
                cesap_file = request.files['CESAP']
                pending.cesap_filename = cesap_file.filename
                pending.cesap = cesap_file.read()

            if not pending.cna:
                cna_file = request.files['CNA']
                pending.cna_filename = cna_file.filename
                pending.cna = cna_file.read()

            pending.community = community
            pending.program = program
            pending.subprogram = subprogram
            pending.start_date = start_date
            pending.end_date = end_date
            pending.totalWeek = totalWeek
            pending.budget = budget
            pending.user = user
            pending.department = lead
            pending.subDepartment = support
            pending.status = status
            pending.department_A = department_A
            pending.volunteer = volunteer

            userlog = g.current_user
            action = f'UPDATED pending {program} projects of {community}'
            ph_tz = pytz.timezone('Asia/Manila')
            ph_time = datetime.now(ph_tz)
            timestamp1 = ph_time.strftime('%Y-%m-%d %H:%M:%S')
            timestamp = convert_date1(timestamp1)
            insert_logs = Logs(userlog = userlog, timestamp = timestamp, action = action)
            if insert_logs:
                db.session.add(insert_logs)
                db.session.commit()
                
            db.session.commit()
            flash('Pending updated successfully!', 'edit_account')

        p = Pending_project.query.get(pending_id)

    return render_template("cPending_details.html", id=p.id, community=p.community, program=p.program, subprogram = p.subprogram, totalWeek = p.totalWeek, user=p.user, start_date = p.start_date, end_date = p.end_date, department=p.department, subDepartment = p.subDepartment, cpf_filename=p.cpf_filename, cesap_filename=p.cesap_filename, cna_filename=p.cna_filename, budget=p.budget, comments=p.comments, department_A=p.department_A, volunteer=p.volunteer)


############################### COORDINATOR COMMENTS ###############################
@coordinator_route.route('/get_comments')
def get_comments():
    try:
        community_data = [
            {
                'community': record.community,
                'program': record.program,
                'subprogram': record.subprogram,
                'comments': record.comments
            }
            for record in Pending_project.query.filter_by(program=g.current_program).all()
        ]
        return jsonify(community_data)
    except Exception as e:
        # Log the error for debugging
        print(str(e))
        return make_response("Internal Server Error", 500)
    

############################ EDIT PROFILE #############################
@coordinator_route.route("/cEdit_profile")
def cEdit_profile():
  
    
    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))
    
    p = Users.query.filter_by(username = g.current_user).first()

    return render_template("cEdit_profile.html", id=p.id, username=p.username, firstname=p.firstname, lastname=p.lastname, email=p.email, mobile_number=p.mobile_number)


@coordinator_route.route('/cUpdate_profile', methods=['POST'])
def cUpdate_profile():
   

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
            flash('Invalid email format. Only Gmail accounts are allowed.', 'delete_pending')
            return redirect(url_for('coordinator.cEdit_profile'))

        user = Users.query.get(user_id)

        if user:
      
            # Check if the new values already exist in the table
            if user.username != new_username:
                existing_username = Users.query.filter_by(username=new_username).first()
                if existing_username:
                    flash(f'Username "{new_username}" already exists. Please choose a different username.', 'delete_pending')
                    return redirect(url_for('coordinator.cEdit_profile'))
            if user.email != new_email:
                existing_email = Users.query.filter_by(email=new_email).first()
                if existing_email:
                    flash(f'Email "{new_email}" already exists. Please choose a different email.', 'delete_pending')
                    return redirect(url_for('coordinator.cEdit_profile'))
            
            existing_mobile_number = Users.query.filter_by(mobile_number=new_mobile_number).first()
            if len(new_mobile_number) < 11:
                flash('Mobile number must be at least 11 digits long.', 'delete_pending')
                return redirect(url_for('coordinator.cEdit_profile'))
            elif existing_mobile_number and existing_mobile_number.id != user.id:
                flash(f'Mobile Number: "{new_mobile_number}" already exists.', 'delete_pending')
                return redirect(url_for('coordinator.cEdit_profile'))

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
            flash('Account updated successfully!', 'new_password')

        return redirect(url_for('coordinator.cEdit_profile'))



@coordinator_route.route('/cDelete_picture', methods=['POST'])
def cDelete_picture():
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

    return redirect(url_for('coordinator.cEdit_profile'))

@coordinator_route.route('/cUpdate_picture', methods=['POST'])
def cUpdate_picture():

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

        return redirect(url_for('coordinator.cEdit_profile'))


################## RESOURCES ################3333
@coordinator_route.route("/cResources")
def cResources():
    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))
    
    # Dynamically generate the years
    current_year = datetime.now().year
     # Fetch all user records from the database
    all_data = Resources.query.filter_by(program=g.current_program).all()
    program8 = Program.query.all()
    user1 = Users.query.all()
    return render_template("cResources.html", current_year=current_year, community = all_data)


@coordinator_route.route("/cAdd_resources", methods=["POST"])
def cAdd_resources():

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
        return redirect(url_for('coordinator.cResources'))
    return redirect(url_for('coordinator.cResources'))

@coordinator_route.route('/cDelete_resources/<int:id>', methods=['GET'])
def cDelete_resources(id):

    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))
    
    resources = Resources.query.get(id)
    program = request.args.get('program')
    community_name = request.args.get('community')

    if resources:
        userlog = g.current_user
        action = f'DELETED resources'
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
    return redirect(url_for('coordinator.cResources'))
