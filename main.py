from flask import Flask, render_template, request, redirect, url_for,session
from werkzeug.utils import secure_filename
import hashlib
import MySQLdb
import re

app = Flask(__name__)

# Configuration for file upload
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['ALLOWED_EXTENSIONS'] = {'jpg', 'jpeg', 'png'}

# Function to check if the file extension is allowed
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Database configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'your_username'
app.config['MYSQL_PASSWORD'] = 'your_password'
app.config['MYSQL_DB'] = 'user-system'

@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get form data
        email = request.form['email']
        password = request.form['password']

        # Connect to MySQL database
        db = MySQLdb.connect(host=app.config['MYSQL_HOST'], user=app.config['MYSQL_USER'],
                             password=app.config['MYSQL_PASSWORD'], db=app.config['MYSQL_DB'])

        # Create cursor
        cursor = db.cursor()

        # Check if the user exists in the database
        cursor.execute("SELECT * FROM user WHERE email = %s", (email,))
        user = cursor.fetchone()

        if user:
            # Verify password
            encrypted_password = hashlib.sha256(password.encode()).hexdigest()
            if encrypted_password == user[4]:  # Index 4 corresponds to the password column in the database
                # Successful login
                # Set session variables
                session['loggedin'] = True
                session['userid'] = user[0]  # Index 0 corresponds to the userid column in the database
                session['name'] = user[1]  # Index 1 corresponds to the first_name column in the database
                session['email'] = user[3]  # Index 3 corresponds to the email column in the database
                message = 'Logged in successfully!'
                return render_template('user.html', message=message)
        
        # Invalid credentials
        message = 'Invalid email/password. Please try again.'

        
        return render_template('login.html', message=message)

    return render_template('login.html')


# Route for the registration page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get form data
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        mobile_number = request.form['mobile_number']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        profile_photo = request.files['profile_photo']

        # Validate form data
        if not first_name or not last_name or not mobile_number or not email or not password or not confirm_password:
            error = 'Please fill in all the required fields.'
            return render_template('register.html', error=error)

        if password != confirm_password:
            error = 'Passwords do not match.'
            return render_template('register.html', error=error)
        
        email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(email_regex, email):
            error ='Invalid email address'
            return render_template('register.html',error = error)
        
        mobile_regex = r'^\d{10}$'
        if not re.match(mobile_regex, mobile_number):
            error = 'Invalid mobile number'
            return render_template('register.html', error = error)


        # Save profile photo
        if profile_photo and allowed_file(profile_photo.filename):
            filename = secure_filename(profile_photo.filename)
            profile_photo.save(app.config['UPLOAD_FOLDER'] + filename)
        else:
            error = 'Invalid profile photo. Please upload an image with JPG, JPEG, or PNG format.'
            return render_template('register.html', error=error)

        # Encrypt password
        encrypted_password = hashlib.sha256(password.encode()).hexdigest()

        # Connect to MySQL database
        db = MySQLdb.connect(host=app.config['MYSQL_HOST'], user=app.config['MYSQL_USER'],
                             password=app.config['MYSQL_PASSWORD'], db=app.config['MYSQL_DB'])

        # Create cursor
        cursor = db.cursor()

        # Insert user data into the database
        sql = "INSERT INTO user (first_name, last_name, mobile_number, email, password, profile_photo) " \
              "VALUES (%s, %s, %s, %s, %s, %s)"
        values = (first_name, last_name, mobile_number, email, encrypted_password, filename)
        cursor.execute(sql, values)

        # Commit the transaction
        db.commit()

        # Close cursor and database connection
        cursor.close()
        db.close()

        # Redirect to a success page or login page
        return redirect(url_for('login'))

    return render_template('register.html')




if __name__ == '__main__':
    app.run(debug=True)
