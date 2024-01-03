from flask import Flask, render_template, request, redirect, session, url_for
from pymongo import MongoClient
from werkzeug.security import check_password_hash, generate_password_hash
from bson import ObjectId
from dotenv import load_dotenv
import random
import string
from flask import flash



load_dotenv()

app = Flask(__name__)
import os

app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'default_secret_key')

client = MongoClient(os.environ.get("MONGODB_URI"))
db = client.get_database("users")
admins_collection = db.get_collection("user_permissions")

def generate_random_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form.get('adminId')
        passkey = request.form.get('passkey')

        # Check if user exists in the user_permissions collection
        user_data = admins_collection.find_one({'_id': user_id, 'passkey': passkey})

        if user_data:
            # If user exists, set session and redirect to admin_dashboard
            session['user_id'] = user_id
            return redirect(url_for('admin'))
        else:
            # If user doesn't exist or password is incorrect, show an error message
            error_message = "Invalid user ID or passkey."
            return render_template('login.html', error_message=error_message)

    return render_template('login.html')

@app.route('/admin')
def admin():
    if 'user_id' in session:
        # User is logged in, show the admin dashboard
        current_user_id = session['user_id']

        # Retrieve competitions where the current user is an admin
        competitions = db.competition_management.find({'admins': current_user_id})

        return render_template('admin_dashboard.html', user_id=current_user_id, competitions=competitions)

    else:
        # User is not logged in, redirect to the login page
        return redirect(url_for('login'))

@app.route('/create_competition')
def create_competition():
    admins_data = admins_collection.find({}, {'_id': 1, 'passkey': 0})

    # Get the current session user_id
    current_user_id = session.get('user_id')

    # Filter out the current admin from the dropdown options
    admins_options = [
        {'_id': str(admin['_id']), 'admin_id': admin['_id']}
        for admin in admins_data
        if str(admin['_id']) != current_user_id
    ]

    return render_template('createcomp.html', admins_options=admins_options)

@app.route('/create_competition', methods=['POST'])
def handle_competition_form():
    # Extract form data
    competition_name = request.form.get('competitionName')
    competition_subtitle = request.form.get('subtitle')
    num_rounds = int(request.form.get('numRounds'))
    num_categories = int(request.form.get('numCategories'))
    selected_admins = request.form.getlist('addAdmins[]')

    # Generate a random 8-character alphanumeric code for _id
    competition_id = generate_random_code()

    # Include the current session user_id (admin_ood) in the selected admins
    current_user_id = session.get('user_id')
    selected_admins.append(current_user_id)

    # Prepare the competition document
    competition_doc = {
        '_id': competition_id,
        'competition_name': competition_name,
        'competition_subtitle': competition_subtitle,
        'num_rounds': num_rounds,
        'num_categories': num_categories,
        'admins': selected_admins
    }

    db.competition_management.insert_one(competition_doc)

    flash(f'Competition "{competition_name}" successfully generated', 'success')

    return redirect(url_for('admin'))



def get_competition_details(comp_id):
    pass

def process_configuration_form(form_data, comp_id):
    pass


if __name__ == '__main__':
    app.run(debug=True, port=5002)
