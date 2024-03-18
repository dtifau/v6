from flask import Blueprint, render_template, redirect, url_for, flash, session

admin_route = Blueprint('admin', __name__)

@admin_route.route("/community")
def community():
     # Check if the user is logged in
    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('dbModel.login'))
    return render_template("community.html")