from flask import Blueprint, render_template, redirect, url_for, flash, session, request, g, send_file, Response
from collections import Counter
import pandas as pd
import joblib, base64, re
from main.models.dbModel import Users, Subprogram, Pending_project
from main import db

randomForest_Route = Blueprint('randomForest', __name__)

model_path_cesu = 'trained_modelCESU7.pkl'
sub_model_path = 'subprogram7.pkl'

#comments

model = joblib.load(model_path_cesu)
model2 = joblib.load(sub_model_path)


@randomForest_Route.errorhandler(Exception)
def handle_error(e):
    if g.current_role == "Coordinator":
        return render_template("cerror.html"), 500  # Customize the error page and status code
    else:
        return render_template("error.html"), 500  # Customize the error page and status code
  
def get_current_user():
    if 'user_id' in session:
        # Assuming you have a User model or some way to fetch the user by ID
        user = Users.query.get(session['user_id'])
        pending_count = Pending_project.query.filter_by(status="For Review").count()
            
        # Set a maximum value for pending_count
        max_pending_count = 9
        pending_count_display = min(pending_count, max_pending_count)
        pending_count_display = '9+' if pending_count > max_pending_count else pending_count


        declined_count = Pending_project.query.filter_by(status="Declined", program=user.program).count() 
        max_declined_count = 9
        declined_count_display = min(declined_count, max_declined_count)
        declined_count_display = '9+' if declined_count > max_declined_count else declined_count
        
        profile_picture_base64 = None
        if user:
            if user.profile_picture:
                # Convert the profile picture to base64 encoding
                profile_picture_base64 = base64.b64encode(user.profile_picture).decode('utf-8')
            return user.username, user.role, pending_count_display, declined_count_display, user.firstname, user.lastname, profile_picture_base64
    return None, None, 0, 0, None, None, None

@randomForest_Route.before_request
def before_request():
    g.current_user, g.current_role, g.pending_count_display, g.declined_count_display, g.current_firstname, g.current_lastname, g.profile_picture_base64 = get_current_user()

@randomForest_Route.context_processor
def inject_current_user():
    return dict(current_user=g.current_user, current_role=g.current_role, pending_count = g.pending_count_display, declined_count=g.declined_count_display, current_firstname=g.current_firstname, current_lastname=g.current_lastname, profile_picture_base64 = g.profile_picture_base64 )

@randomForest_Route.route("/program", methods=["GET", "POST"])
def program():
    if g.current_role != "Admin" and g.current_role != "BOR":
        return redirect(url_for('dbModel.login'))
        
    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))

    return render_template("program.html")

@randomForest_Route.route("/cProgram", methods=["GET", "POST"])
def cProgram():
    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))

    return render_template("cProgram.html")

#######################################################################

@randomForest_Route.route("/programWithCSV", methods=["GET", "POST"])
def programWithCSV():
    if g.current_role != "Admin" and g.current_role != "BOR":
        return redirect(url_for('dbModel.login'))
    
    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))

    if request.method == "POST":
        csv_file = request.files["csv_file"]
      
        if csv_file:
            df = pd.read_csv(csv_file)
            df = df.iloc[:, 3:]
            columns_with_strings = df.select_dtypes(include=['object']).columns

            sub_programs_dict = {
                "Literacy": db.session.query(Subprogram).filter(Subprogram.program == "Literacy").all(),
                "Socio-economic": db.session.query(Subprogram).filter(Subprogram.program == "Socio-economic").all(),
                "Environmental Stewardship": db.session.query(Subprogram).filter(Subprogram.program == "Environmental Stewardship").all(),
                "Health and Wellness": db.session.query(Subprogram).filter(Subprogram.program == "Health and Wellness").all(),
                "Cultural Enhancement": db.session.query(Subprogram).filter(Subprogram.program == "Cultural Enhancement").all(),
                "Values Formation": db.session.query(Subprogram).filter(Subprogram.program == "Values Formation").all(),
                "Disaster Management": db.session.query(Subprogram).filter(Subprogram.program == "Disaster Management").all(),
                "Gender and Development": db.session.query(Subprogram).filter(Subprogram.program == "Gender and Development").all()
            }

            if not columns_with_strings.empty:
                encoding_dict_kasarian = {'Lalake': 0, 'Babae': 1}
                encoding_dict_edad = {'17-below': 0, '18-24': 1, '25-34': 2, '35-44': 3, '45-54': 4, '55-64': 5, '65-Above': 6}
                encoding_dict_antas = {'Hindi nakapagtapos ng Elementarya':0, 'Elementarya':1, 'Hindi nakapagtapos ng Sekundarya':2, 'Sekundarya':3, 'Kolehiyo':4, 'Hindi nakapagtapos ng Kolehiyo':5, 'Masters Degree':6, 'Doctorate Degree':7, 'Hindi nakapag-aral':8}
                encoding_dict_uri = {'May Trabaho': 1, 'Walang Trabaho': 0}

                endcoding_dict_Pangedukasyon = {'Oo':1, 'Hindi': 0}
                endcoding_dict_Pangkultura = {'Oo':1, 'Hindi': 0}
                endcoding_dict_Pangkabuhayan = {'Oo':1, 'Hindi': 0}
                endcoding_dict_Values = {'Oo':1, 'Hindi': 0}
                endcoding_dict_Pagtatanim = {'Oo':1, 'Hindi': 0}
                endcoding_dict_Pagkain = {'Oo':1, 'Hindi': 0}
                endcoding_dict_Pangkalusugan = {'Oo':1, 'Hindi': 0}
                endcoding_dict_Pagrerecycle = {'Oo':1, 'Hindi': 0}
                endcoding_dict_Dental = {'Oo':1, 'Hindi': 0}
                endcoding_dict_Teknolohiya = {'Oo':1, 'Hindi': 0}

                df['Kasarian'] = df['Kasarian'].map(encoding_dict_kasarian)
                df['Edad'] = df['Edad'].map(encoding_dict_edad)
                df['Antas na tinapos'] = df['Antas na tinapos'].map(encoding_dict_antas)
                df['Uri ng trabaho'] = df['Uri ng trabaho'].map(encoding_dict_uri)
                df['Serbisyong Pangedukasyon'] = df['Serbisyong Pangedukasyon'].map(endcoding_dict_Pangedukasyon)
                df['Pagsasanay Pangkabuhayan (Livelihood)'] = df['Pagsasanay Pangkabuhayan (Livelihood)'].map(endcoding_dict_Pangkabuhayan)
                df['Pagtatanim'] = df['Pagtatanim'].map(endcoding_dict_Pagtatanim)
                df['Serbisyong Pangkalusugan'] = df['Serbisyong Pangkalusugan'].map(endcoding_dict_Pangkalusugan)
                df['Serbisyong Dental'] = df['Serbisyong Dental'].map(endcoding_dict_Dental)
                df['Kaalamang Pangkultura'] = df['Kaalamang Pangkultura'].map(endcoding_dict_Pangkultura)
                df['Values Formation at Moral Recovery'] = df['Values Formation at Moral Recovery'].map(endcoding_dict_Values)
                df['Ayudang Pagkain (Food Assistance)'] = df['Ayudang Pagkain (Food Assistance)'].map(endcoding_dict_Pagkain)
                df['Pagrerecycle'] = df['Pagrerecycle'].map(endcoding_dict_Pagrerecycle)
                df['Pagsasanay Ukol sa Teknolohiya'] = df['Pagsasanay Ukol sa Teknolohiya'].map(endcoding_dict_Teknolohiya)
                

            if "Program" in df.columns:
                target_variable = "Program"
                X = df.drop(target_variable, axis=1)
                predictions = model.predict(X)
                df["Program"] = predictions

            else:
                predictions = model.predict(df)
                df["Program"] = predictions

            #FOR SUBPROGRAM PREDICTION

            encoding_dict_program = {'Literacy': 0, 'Socio-economic': 1, 'Environmental Stewardship': 2, 'Health and Wellness': 3, 'Cultural Enhancement': 4, 'Values Formation': 5, 'Disaster Management': 6, 'Gender and Development': 7}  # Define your categories and values
            df['Program'] = df['Program'].map(encoding_dict_program)

            if "Sub Program" in df.columns:
                target_variable = "Sub Program"
                X = df.drop(target_variable, axis=1)
                predictions2 = model2.predict(X)
                df["Sub Program"] = predictions2
            else:
                predictions2 = model2.predict(df)
                df["Sub Program"] = predictions2

            result_csv_filename = "result.csv"  # Specify the filename you want
            df.to_csv(result_csv_filename, index=False)

            df = pd.read_csv(result_csv_filename)
            columns_with_strings = df.select_dtypes(include=['object']).columns
            prediction_counts2 = Counter(predictions2)
            top_3_predictions2 = prediction_counts2.most_common(3)

            top_programs_with_subprograms2 = []
            for prediction2, count in top_3_predictions2:
                top_programs_with_subprograms2.append({
                    "program": prediction2,
                    "quantity": count
                   
            })
            #END of subprogram prediction


            prediction_counts = Counter(predictions)

            # Find the top 3 most frequent predictions
            top_3_predictions = prediction_counts.most_common(3)

             # Pass the top programs and their sub-programs to the template
            top_programs_with_subprograms = []
            for prediction, count in top_3_predictions:
                top_programs_with_subprograms.append({
                    "program": prediction,
                    "quantity": count,
                    "sub_programs": [sub_program.subprogram for sub_program in sub_programs_dict.get(prediction, [])]
            })
                
            kasarian_counts = df['Kasarian'].value_counts().to_dict()  
            edad_counts = df['Edad'].value_counts().to_dict()  
            antas_counts = df['Antas na tinapos'].value_counts().to_dict()  
            uri_counts = df['Uri ng trabaho'].value_counts().to_dict()  

            Pangedukasyon_counts = df['Serbisyong Pangedukasyon'].value_counts().to_dict()  
            Pangkabuhayan_counts = df['Pagsasanay Pangkabuhayan (Livelihood)'].value_counts().to_dict()  
            Pagtatanim_counts = df['Pagtatanim'].value_counts().to_dict()  
            Pangkalusugan_counts = df['Serbisyong Pangkalusugan'].value_counts().to_dict()  
            Dental_counts = df['Serbisyong Dental'].value_counts().to_dict()
            Pangkultura_counts = df['Kaalamang Pangkultura'].value_counts().to_dict()  
            Values_counts = df['Values Formation at Moral Recovery'].value_counts().to_dict()  
            Pagkain_counts = df['Ayudang Pagkain (Food Assistance)'].value_counts().to_dict()  
            Pagrerecycle_counts = df['Pagrerecycle'].value_counts().to_dict()  
            Teknolohiya_counts = df['Pagsasanay Ukol sa Teknolohiya'].value_counts().to_dict()  

            category_counts = {
                "Pangedukasyon": Pangedukasyon_counts.get(1, 0),
                "Pangkabuhayan": Pangkabuhayan_counts.get(1, 0),
                "Pagtatanim": Pagtatanim_counts.get(1, 0),
                "Pangkalusugan": Pangkalusugan_counts.get(1, 0),
                "Dental": Dental_counts.get(1, 0),
                "Pangkultura": Pangkultura_counts.get(1, 0),
                "Values": Values_counts.get(1, 0),
                "Pagkain": Pagkain_counts.get(1, 0),
                "Pagrerecycle": Pagrerecycle_counts.get(1, 0),
                "Teknolohiya": Teknolohiya_counts.get(1, 0)
            }

            # Find the category with the highest count
            max_category = max(category_counts, key=category_counts.get)
            highest_count = category_counts[max_category]

            if max_category == "Pangedukasyon" or max_category == "Teknolohiya":
                program_ces = "Literacy"
            elif max_category == "Pangkabuhayan":
                program_ces = "Socio-economic"
            elif max_category == "Pagtatanim" or max_category == "Pagrerecycle":
                program_ces = "Environmental Stewardship"
            elif max_category == "Pangkalusugan" or max_category == "Dental":
                program_ces = "Health and Wellness"
            elif max_category == "Pangkultura":
                program_ces = "Cultural Enhancement"
            elif max_category == "Values":
                program_ces = "Values Formation"
            elif max_category == "Pagkain":
                program_ces = "Disaster Management"   
            else:
                program_ces = "Gender Development" 

            return render_template("resultCSV.html",
            top1=top_programs_with_subprograms[0] if top_programs_with_subprograms else {},
            top2=top_programs_with_subprograms[1] if len(top_programs_with_subprograms) > 1 else {},
            top3=top_programs_with_subprograms[2] if len(top_programs_with_subprograms) > 2 else {},
            top1_2=top_programs_with_subprograms2[0] if top_programs_with_subprograms2 else {},
            top2_2=top_programs_with_subprograms2[1] if len(top_programs_with_subprograms2) > 1 else {},
            top3_2=top_programs_with_subprograms2[2] if len(top_programs_with_subprograms2) > 2 else {},
            kasarian_counts=kasarian_counts,
            edad_counts=edad_counts,
            antas_counts=antas_counts,
            uri_counts=uri_counts,
            Pangedukasyon_counts=Pangedukasyon_counts,
            Pangkabuhayan_counts=Pangkabuhayan_counts,
            Pagtatanim_counts=Pagtatanim_counts,
            Pangkalusugan_counts=Pangkalusugan_counts,
            Dental_counts=Dental_counts,
            Pangkultura_counts=Pangkultura_counts,
            Values_counts=Values_counts,
            Pagkain_counts=Pagkain_counts,
            Pagrerecycle_counts=Pagrerecycle_counts,
            Teknolohiya_counts=Teknolohiya_counts,
            max_category=max_category,
            highest_count=highest_count,
            program_ces=program_ces)

        
    return render_template("program.html")

#for coordinator side

@randomForest_Route.route("/cProgramWithCSV", methods=["GET", "POST"])
def cProgramWithCSV():
    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))

    if request.method == "POST":
        csv_file = request.files["csv_file"]
        if csv_file:
            df = pd.read_csv(csv_file)
            df = df.iloc[:, 3:]
            columns_with_strings = df.select_dtypes(include=['object']).columns

            sub_programs_dict = {
                "Literacy": db.session.query(Subprogram).filter(Subprogram.program == "Literacy").all(),
                "Socio-economic": db.session.query(Subprogram).filter(Subprogram.program == "Socio-economic").all(),
                "Environmental Stewardship": db.session.query(Subprogram).filter(Subprogram.program == "Environmental Stewardship").all(),
                "Health and Wellness": db.session.query(Subprogram).filter(Subprogram.program == "Health and Wellness").all(),
                "Cultural Enhancement": db.session.query(Subprogram).filter(Subprogram.program == "Cultural Enhancement").all(),
                "Values Formation": db.session.query(Subprogram).filter(Subprogram.program == "Values Formation").all(),
                "Disaster Management": db.session.query(Subprogram).filter(Subprogram.program == "Disaster Management").all(),
                "Gender and Development": db.session.query(Subprogram).filter(Subprogram.program == "Gender and Development").all()
            }
            db.session.close()

            if not columns_with_strings.empty:
                encoding_dict_kasarian = {'Lalake': 0, 'Babae': 1}
                encoding_dict_edad = {'17-below': 0, '18-24': 1, '25-34': 2, '35-44': 3, '45-54': 4, '55-64': 5, '65-Above': 6}
                encoding_dict_antas = {'Hindi nakapagtapos ng Elementarya':0, 'Elementarya':1, 'Hindi nakapagtapos ng Sekundarya':2, 'Sekundarya':3, 'Kolehiyo':4, 'Hindi nakapagtapos ng Kolehiyo':5, 'Masters Degree':6, 'Doctorate Degree':7, 'Hindi nakapag-aral':8}
                encoding_dict_uri = {'May Trabaho': 1, 'Walang Trabaho': 0}

                endcoding_dict_Pangedukasyon = {'Oo':1, 'Hindi': 0}
                endcoding_dict_Pangkultura = {'Oo':1, 'Hindi': 0}
                endcoding_dict_Pangkabuhayan = {'Oo':1, 'Hindi': 0}
                endcoding_dict_Values = {'Oo':1, 'Hindi': 0}
                endcoding_dict_Pagtatanim = {'Oo':1, 'Hindi': 0}
                endcoding_dict_Pagkain = {'Oo':1, 'Hindi': 0}
                endcoding_dict_Pangkalusugan = {'Oo':1, 'Hindi': 0}
                endcoding_dict_Pagrerecycle = {'Oo':1, 'Hindi': 0}
                endcoding_dict_Dental = {'Oo':1, 'Hindi': 0}
                endcoding_dict_Teknolohiya = {'Oo':1, 'Hindi': 0}

                df['Kasarian'] = df['Kasarian'].map(encoding_dict_kasarian)
                df['Edad'] = df['Edad'].map(encoding_dict_edad)
                df['Antas na tinapos'] = df['Antas na tinapos'].map(encoding_dict_antas)
                df['Uri ng trabaho'] = df['Uri ng trabaho'].map(encoding_dict_uri)
                df['Serbisyong Pangedukasyon'] = df['Serbisyong Pangedukasyon'].map(endcoding_dict_Pangedukasyon)
                df['Pagsasanay Pangkabuhayan (Livelihood)'] = df['Pagsasanay Pangkabuhayan (Livelihood)'].map(endcoding_dict_Pangkabuhayan)
                df['Pagtatanim'] = df['Pagtatanim'].map(endcoding_dict_Pagtatanim)
                df['Serbisyong Pangkalusugan'] = df['Serbisyong Pangkalusugan'].map(endcoding_dict_Pangkalusugan)
                df['Serbisyong Dental'] = df['Serbisyong Dental'].map(endcoding_dict_Dental)
                df['Kaalamang Pangkultura'] = df['Kaalamang Pangkultura'].map(endcoding_dict_Pangkultura)
                df['Values Formation at Moral Recovery'] = df['Values Formation at Moral Recovery'].map(endcoding_dict_Values)
                df['Ayudang Pagkain (Food Assistance)'] = df['Ayudang Pagkain (Food Assistance)'].map(endcoding_dict_Pagkain)
                df['Pagrerecycle'] = df['Pagrerecycle'].map(endcoding_dict_Pagrerecycle)
                df['Pagsasanay Ukol sa Teknolohiya'] = df['Pagsasanay Ukol sa Teknolohiya'].map(endcoding_dict_Teknolohiya)
                

            if "Program" in df.columns:
                target_variable = "Program"
                X = df.drop(target_variable, axis=1)
                predictions = model.predict(X)
                df["Program"] = predictions

            else:
                predictions = model.predict(df)
                df["Program"] = predictions

            #FOR SUBPROGRAM PREDICTION

            encoding_dict_program = {'Literacy': 0, 'Socio-economic': 1, 'Environmental Stewardship': 2, 'Health and Wellness': 3, 'Cultural Enhancement': 4, 'Values Formation': 5, 'Disaster Management': 6, 'Gender and Development': 7}  # Define your categories and values
            df['Program'] = df['Program'].map(encoding_dict_program)

            if "Sub Program" in df.columns:
                target_variable = "Sub Program"
                X = df.drop(target_variable, axis=1)
                predictions2 = model2.predict(X)
                df["Sub Program"] = predictions2
            else:
                predictions2 = model2.predict(df)
                df["Sub Program"] = predictions2

            result_csv_filename = "result.csv"  # Specify the filename you want
            df.to_csv(result_csv_filename, index=False)

            df = pd.read_csv(result_csv_filename)
            columns_with_strings = df.select_dtypes(include=['object']).columns
            prediction_counts2 = Counter(predictions2)
            top_3_predictions2 = prediction_counts2.most_common(3)

            top_programs_with_subprograms2 = []
            for prediction2, count in top_3_predictions2:
                top_programs_with_subprograms2.append({
                    "program": prediction2,
                    "quantity": count
                   
            })
            #END of subprogram prediction


            prediction_counts = Counter(predictions)

            # Find the top 3 most frequent predictions
            top_3_predictions = prediction_counts.most_common(3)

             # Pass the top programs and their sub-programs to the template
            top_programs_with_subprograms = []
            for prediction, count in top_3_predictions:
                top_programs_with_subprograms.append({
                    "program": prediction,
                    "quantity": count,
                    "sub_programs": [sub_program.subprogram for sub_program in sub_programs_dict.get(prediction, [])]
            })
                
            kasarian_counts = df['Kasarian'].value_counts().to_dict()  
            edad_counts = df['Edad'].value_counts().to_dict()  
            antas_counts = df['Antas na tinapos'].value_counts().to_dict()  
            uri_counts = df['Uri ng trabaho'].value_counts().to_dict()  

            Pangedukasyon_counts = df['Serbisyong Pangedukasyon'].value_counts().to_dict()  
            Pangkabuhayan_counts = df['Pagsasanay Pangkabuhayan (Livelihood)'].value_counts().to_dict()  
            Pagtatanim_counts = df['Pagtatanim'].value_counts().to_dict()  
            Pangkalusugan_counts = df['Serbisyong Pangkalusugan'].value_counts().to_dict()  
            Dental_counts = df['Serbisyong Dental'].value_counts().to_dict()
            Pangkultura_counts = df['Kaalamang Pangkultura'].value_counts().to_dict()  
            Values_counts = df['Values Formation at Moral Recovery'].value_counts().to_dict()  
            Pagkain_counts = df['Ayudang Pagkain (Food Assistance)'].value_counts().to_dict()  
            Pagrerecycle_counts = df['Pagrerecycle'].value_counts().to_dict()  
            Teknolohiya_counts = df['Pagsasanay Ukol sa Teknolohiya'].value_counts().to_dict()  

            category_counts = {
                "Pangedukasyon": Pangedukasyon_counts.get(1, 0),
                "Pangkabuhayan": Pangkabuhayan_counts.get(1, 0),
                "Pagtatanim": Pagtatanim_counts.get(1, 0),
                "Pangkalusugan": Pangkalusugan_counts.get(1, 0),
                "Dental": Dental_counts.get(1, 0),
                "Pangkultura": Pangkultura_counts.get(1, 0),
                "Values": Values_counts.get(1, 0),
                "Pagkain": Pagkain_counts.get(1, 0),
                "Pagrerecycle": Pagrerecycle_counts.get(1, 0),
                "Teknolohiya": Teknolohiya_counts.get(1, 0)
            }

            # Find the category with the highest count
            max_category = max(category_counts, key=category_counts.get)
            highest_count = category_counts[max_category]

            if max_category == "Pangedukasyon" or max_category == "Teknolohiya":
                program_ces = "Literacy"
            elif max_category == "Pangkabuhayan":
                program_ces = "Socio-economic"
            elif max_category == "Pagtatanim" or max_category == "Pagrerecycle":
                program_ces = "Environmental Stewardship"
            elif max_category == "Pangkalusugan" or max_category == "Dental":
                program_ces = "Health and Wellness"
            elif max_category == "Pangkultura":
                program_ces = "Cultural Enhancement"
            elif max_category == "Values":
                program_ces = "Values Formation"
            elif max_category == "Pagkain":
                program_ces = "Disaster Management"   
            else:
                program_ces = "Gender Development"  

            return render_template("cResultCSV.html",
            top1=top_programs_with_subprograms[0] if top_programs_with_subprograms else {},
            top2=top_programs_with_subprograms[1] if len(top_programs_with_subprograms) > 1 else {},
            top3=top_programs_with_subprograms[2] if len(top_programs_with_subprograms) > 2 else {},
            top1_2=top_programs_with_subprograms2[0] if top_programs_with_subprograms2 else {},
            top2_2=top_programs_with_subprograms2[1] if len(top_programs_with_subprograms2) > 1 else {},
            top3_2=top_programs_with_subprograms2[2] if len(top_programs_with_subprograms2) > 2 else {},
            kasarian_counts=kasarian_counts,
            edad_counts=edad_counts,
            antas_counts=antas_counts,
            uri_counts=uri_counts,
            Pangedukasyon_counts=Pangedukasyon_counts,
            Pangkabuhayan_counts=Pangkabuhayan_counts,
            Pagtatanim_counts=Pagtatanim_counts,
            Pangkalusugan_counts=Pangkalusugan_counts,
            Dental_counts=Dental_counts,
            Pangkultura_counts=Pangkultura_counts,
            Values_counts=Values_counts,
            Pagkain_counts=Pagkain_counts,
            Pagrerecycle_counts=Pagrerecycle_counts,
            Teknolohiya_counts=Teknolohiya_counts,
            max_category=max_category,
            highest_count=highest_count,
            program_ces=program_ces)
        
    return render_template("cProgram.html")

