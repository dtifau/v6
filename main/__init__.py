from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from flask_mail import Mail

# Specify the custom static URL path
custom_static_url_path = '/static'

app = Flask(__name__, static_url_path=custom_static_url_path)
app.secret_key = 'your_secret_key'  # Set a secret key for session management

# Configure the database connection for SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cesu17.db'  # Use SQLite with a database file named 'cesu.db'
db = SQLAlchemy(app)
# Configure session to use Flask-Session
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

app.config['MAIL_SERVER']="smtp.gmail.com"
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = "lucesu50@gmail.com"
app.config['MAIL_PASSWORD'] = "ktsf yqpt tnpr iaev"
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mail = Mail(app)
from wtforms import SelectField
from flask_wtf import FlaskForm


class Form(FlaskForm):
    program = SelectField('Program', choices=[])
    subprogram = SelectField('Sub-Program', choices=[])

from main.routes.indexRoute import index_route
from main.routes.dbModelRoute import dbModel_route
from main.routes.adminRoute import admin_route
from main.routes.randomForestRoute import randomForest_Route
from main.routes.fileRoute import file_route
from main.routes.coordinatorRoute import coordinator_route

app.register_blueprint(file_route)
app.register_blueprint(index_route)
app.register_blueprint(dbModel_route)
app.register_blueprint(admin_route)
app.register_blueprint(randomForest_Route)
app.register_blueprint(coordinator_route)