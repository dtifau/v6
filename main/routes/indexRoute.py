from flask import Blueprint, redirect, url_for, render_template

index_route = Blueprint('index', __name__)

@index_route.route("/", methods=["GET", "POST"])
def index():
    # 
    #return render_template("testdashboard.html")
    return redirect(url_for('dbModel.login'))
    