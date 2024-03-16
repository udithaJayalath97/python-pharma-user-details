import os
import io
from bson import ObjectId
from flask import Flask, render_template, request, redirect, send_file, session
from gridfs import GridFS, GridFSBucket
from pymongo import MongoClient
import bcrypt
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = 'hvbcqgewcy3yegwcygcwec32r3'


client = MongoClient(os.environ.get("MONGODB_URI"))
app.db = client.LoonsLab

fs = GridFS(app.db)

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/user_register")
def user_register():
    return render_template("user-register.html")

@app.route("/user_login")
def userlogin():
    return render_template("login.html")

@app.route("/user_dashboard/<string:user_id>")
def userdashboard(user_id):
    users = app.db.users.find_one({"_id": ObjectId(user_id)})
    if users:
        user_data = {
            "first_name": users["first_name"],
            "last_name": users["last_name"],
            "mobile_number": users["mobile_number"],
            "email": users["email"],
            "profile_picture_id": users["profile_picture_id"]
        }
        return render_template("dashboard.html", user=user_data)
    else:
        # Handle case when user is not found
        return "User not found"
    
@app.route("/photo/<string:photo_id>")
def get_photo(photo_id):
    fs = GridFSBucket(app.db)
    photo_data = fs.open_download_stream(ObjectId(photo_id)).read()
    if photo_data:
        return send_file(io.BytesIO(photo_data), mimetype='image/jpeg')
    else:
        return "Photo not found"

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        mobile_number = request.form.get('mobile_number')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Handle profile picture
        profile_picture = request.files['picture']
        if profile_picture:
            # Read the file data
            file_data = profile_picture.read()
            # Save the file data into MongoDB using GridFS
            file_id = fs.put(file_data, filename=profile_picture.filename)

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        user_data = {
            'first_name': first_name,
            'last_name': last_name,
            'mobile_number': mobile_number,
            'email': email,
            'password': hashed_password
        }
        # If profile_picture is available, add it to user_data
        if profile_picture:
            user_data['profile_picture_id'] = file_id

        # Save data to MongoDB    
        app.db.users.insert_one(user_data)

        return redirect('/login')

    return render_template('user-register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error_message = None
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user_data = app.db.users.find_one({'email': email})
        if user_data and bcrypt.checkpw(password.encode('utf-8'), user_data['password']):
            session['user_id'] = str(user_data['_id'])  # Store user's _id as a string
            return redirect('/dashboard')
        else:
            error_message = "Invalid email or password. Please try again."

    return render_template('login.html', error=error_message)


@app.route('/dashboard')
def dashboard():
    if 'user_id' in session:
        user_id = session['user_id']
        user_data = app.db.users.find_one({'_id': ObjectId(user_id)})
        if user_data:
            return render_template('dashboard.html', user=user_data)
    
    return redirect('/login')



if __name__ == '__main__':
    app.run(debug=True)
