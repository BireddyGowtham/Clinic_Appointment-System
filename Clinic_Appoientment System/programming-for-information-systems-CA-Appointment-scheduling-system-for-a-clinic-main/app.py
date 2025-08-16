from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
import os
from datetime import datetime, timedelta
import random

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a random secret key

class Clinic:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_tables()
        self.initialize_data()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Create users table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
        ''')
        
        # Create patients table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT,
            email TEXT,
            phone TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        # Create departments table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
        ''')
        
        # Create doctors table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS doctors (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            department_id INTEGER NOT NULL,
            FOREIGN KEY (department_id) REFERENCES departments (id)
        )
        ''')
        
        # Create appointments table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            doctor_id TEXT NOT NULL,
            service TEXT NOT NULL,
            datetime TEXT NOT NULL,
            status TEXT DEFAULT 'scheduled',
            FOREIGN KEY (patient_id) REFERENCES patients (id),
            FOREIGN KEY (doctor_id) REFERENCES doctors (id)
        )
        ''')
        
        self.conn.commit()
    
    def initialize_data(self):
        cursor = self.conn.cursor()
        
        # Check if departments already exist
        cursor.execute("SELECT COUNT(*) FROM departments")
        if cursor.fetchone()[0] > 0:
            return  # Data already initialized
        
        # Initialize departments
        departments = [
            "General Medicine",
            "Cardiology",
            "Dermatology",
            "Orthopedics",
            "Pediatrics",
            "Neurology",
            "Ophthalmology",
            "Dentistry",
            "Gynecology",
            "Psychiatry"
        ]
        
        dept_ids = {}
        for dept in departments:
            cursor.execute("INSERT INTO departments (name) VALUES (?)", (dept,))
            dept_ids[dept] = cursor.lastrowid
        
        # Initialize doctors
        doctors = [
            # General Medicine
            ("GM001", "Dr. John Smith", dept_ids["General Medicine"]),
            ("GM002", "Dr. Sarah Johnson", dept_ids["General Medicine"]),
            ("GM003", "Dr. Michael Brown", dept_ids["General Medicine"]),
            
            # Cardiology
            ("CA001", "Dr. Emily Davis", dept_ids["Cardiology"]),
            ("CA002", "Dr. Robert Wilson", dept_ids["Cardiology"]),
            ("CA003", "Dr. Jennifer Lee", dept_ids["Cardiology"]),
            
            # Dermatology
            ("DE001", "Dr. David Miller", dept_ids["Dermatology"]),
            ("DE002", "Dr. Lisa Anderson", dept_ids["Dermatology"]),
            ("DE003", "Dr. James Taylor", dept_ids["Dermatology"]),
            
            # Orthopedics
            ("OR001", "Dr. Patricia Martinez", dept_ids["Orthopedics"]),
            ("OR002", "Dr. Thomas Garcia", dept_ids["Orthopedics"]),
            ("OR003", "Dr. Nancy Rodriguez", dept_ids["Orthopedics"]),
            
            # Pediatrics
            ("PE001", "Dr. Richard Lewis", dept_ids["Pediatrics"]),
            ("PE002", "Dr. Karen Walker", dept_ids["Pediatrics"]),
            ("PE003", "Dr. Steven Hall", dept_ids["Pediatrics"]),
            
            # Neurology
            ("NE001", "Dr. Susan Allen", dept_ids["Neurology"]),
            ("NE002", "Dr. Paul Young", dept_ids["Neurology"]),
            ("NE003", "Dr. Betty King", dept_ids["Neurology"]),
            
            # Ophthalmology
            ("OP001", "Dr. Mark Wright", dept_ids["Ophthalmology"]),
            ("OP002", "Dr. Linda Scott", dept_ids["Ophthalmology"]),
            ("OP003", "Dr. George Adams", dept_ids["Ophthalmology"]),
            
            # Dentistry
            ("DE001", "Dr. Helen Baker", dept_ids["Dentistry"]),
            ("DE002", "Dr. Daniel Nelson", dept_ids["Dentistry"]),
            ("DE003", "Dr. Olivia Carter", dept_ids["Dentistry"]),
            
            # Gynecology
            ("GY001", "Dr. Charles Mitchell", dept_ids["Gynecology"]),
            ("GY002", "Dr. Donna Perez", dept_ids["Gynecology"]),
            ("GY003", "Dr. Edward Roberts", dept_ids["Gynecology"]),
            
            # Psychiatry
            ("PS001", "Dr. Sandra Turner", dept_ids["Psychiatry"]),
            ("PS002", "Dr. Joseph Phillips", dept_ids["Psychiatry"]),
            ("PS003", "Dr. Carol Campbell", dept_ids["Psychiatry"])
        ]
        
        for doctor_id, name, department_id in doctors:
            try:
                cursor.execute(
                    "INSERT INTO doctors (id, name, department_id) VALUES (?, ?, ?)",
                    (doctor_id, name, department_id)
                )
            except sqlite3.IntegrityError:
                # Skip if doctor already exists
                pass
        
        self.conn.commit()
    
    def register_user(self, username, password):
        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            self.conn.commit()
            return True, "Registration successful!"
        except sqlite3.IntegrityError:
            return False, "Username already exists. Please choose another one."
        except Exception as e:
            return False, f"Error during registration: {str(e)}"
    
    def login_user(self, username, password):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()
        if user:
            return True, user[0]
        else:
            return False, "Invalid username or password."
    
    def get_profile(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT name, email, phone FROM patients WHERE user_id=?", (user_id,))
        result = cursor.fetchone()
        
        if result:
            name, email, phone = result
            return {
                'name': name,
                'email': email,
                'phone': phone
            }
        else:
            # Create an empty profile if it doesn't exist
            cursor.execute(
                "INSERT INTO patients (user_id, name, email, phone) VALUES (?, ?, NULL, NULL)",
                (user_id, "Unnamed")  # Set a default name
            )
            self.conn.commit()
            return {
                'name': 'Unnamed',  # Return the default name
                'email': '',
                'phone': ''
            }
    
    def update_profile(self, user_id, name, email, phone):
        try:
            cursor = self.conn.cursor()
            
            # Check if profile exists
            cursor.execute("SELECT id FROM patients WHERE user_id=?", (user_id,))
            patient = cursor.fetchone()
            
            if patient:
                # Update existing profile
                cursor.execute(
                    "UPDATE patients SET name=?, email=?, phone=? WHERE user_id=?",
                    (name, email, phone, user_id)
                )
            else:
                # Create new profile
                cursor.execute(
                    "INSERT INTO patients (user_id, name, email, phone) VALUES (?, ?, ?, ?)",
                    (user_id, name, email, phone)
                )
            
            self.conn.commit()
            return True, "Profile updated successfully!"
        except Exception as e:
            return False, f"Error updating profile: {str(e)}"
    
    def get_departments(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name FROM departments ORDER BY name")
        return cursor.fetchall()
    
    def get_doctors_by_department(self, department_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name FROM doctors WHERE department_id=? ORDER BY name", (department_id,))
        return cursor.fetchall()
    
    def schedule_appointment(self, user_id, doctor_id, service, datetime_str):
        try:
            # Get the patient_id from the patients table
            cursor = self.conn.cursor()
            cursor.execute("SELECT id FROM patients WHERE user_id=?", (user_id,))
            patient = cursor.fetchone()
            
            if not patient:
                return False, "Patient profile not found. Please update your profile first."
            
            patient_id = patient[0]
            
            # Check if the time slot is already booked
            cursor.execute(
                "SELECT COUNT(*) FROM appointments WHERE doctor_id=? AND datetime=? AND status != 'cancelled'",
                (doctor_id, datetime_str)
            )
            count = cursor.fetchone()[0]
            if count > 0:
                return False, "This time slot is already booked. Please select another time."
            
            # Insert the appointment
            cursor.execute(
                "INSERT INTO appointments (patient_id, doctor_id, service, datetime) VALUES (?, ?, ?, ?)",
                (patient_id, doctor_id, service, datetime_str)
            )
            self.conn.commit()
            
            # Get doctor name for confirmation message
            cursor.execute("SELECT name FROM doctors WHERE id=?", (doctor_id,))
            doctor_name = cursor.fetchone()[0]
            
            return True, f"Appointment scheduled successfully with {doctor_name} for {service} on {datetime_str}!"
        except Exception as e:
            return False, f"Error scheduling appointment: {str(e)}"
    
    def get_user_appointments(self, user_id):
        # Return dummy data for now to avoid the error
        return [
            {
                'id': 1,
                'start_datetime': '2023-06-01 10:00',
                'end_datetime': '2023-06-01 10:30',
                'status': 'scheduled',
                'doctor': 'Dr. John Smith',
                'type': 'General Checkup'
            },
            {
                'id': 2,
                'start_datetime': '2023-05-15 14:00',
                'end_datetime': '2023-05-15 14:30',
                'status': 'completed',
                'doctor': 'Dr. Sarah Johnson',
                'type': 'Vaccination'
            },
            {
                'id': 3,
                'start_datetime': '2023-05-01 11:00',
                'end_datetime': '2023-05-01 11:30',
                'status': 'cancelled',
                'doctor': 'Dr. Michael Brown',
                'type': 'Blood Test'
            }
        ]
    
    def cancel_appointment(self, appointment_id, user_id):
        # Dummy implementation
        return True, "Appointment cancelled successfully."

# Create the clinic instance
clinic = Clinic('clinic.db')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        success, message = clinic.register_user(username, password)
        
        if success:
            return redirect(url_for('login'))
        else:
            return render_template('register.html', error=message)
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        success, result = clinic.login_user(username, password)
        
        if success:
            session['user_id'] = result
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error=result)
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get user's appointments
    appointments = clinic.get_user_appointments(session['user_id'])
    
    return render_template('dashboard.html', appointments=appointments)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        
        success, message = clinic.update_profile(session['user_id'], name, email, phone)
        
        if success:
            return redirect(url_for('profile', success=message))
        else:
            return render_template('profile.html', error=message)
    
    # Get user profile data
    profile_data = clinic.get_profile(session['user_id'])
    
    # Check for success message in query parameters
    success = request.args.get('success')
    
    return render_template('profile.html', profile_data=profile_data, success=success)

@app.route('/schedule', methods=['GET', 'POST'])
def schedule():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        doctor_id = request.form.get('doctor')
        service = request.form.get('service')
        date = request.form.get('date')
        time = request.form.get('time')
        
        # Combine date and time
        datetime_str = f"{date} {time}"
        
        success, message = clinic.schedule_appointment(session['user_id'], doctor_id, service, datetime_str)
        
        return render_template('result.html', success=success, message=message)
    
    # Get departments for the template
    departments = clinic.get_departments()
    
    return render_template('schedule.html', departments=departments)

@app.route('/get_doctors/<int:department_id>')
def get_doctors(department_id):
    doctors = clinic.get_doctors_by_department(department_id)
    return jsonify({'doctors': [{'id': id, 'name': name} for id, name in doctors]})

@app.route('/cancel_appointment/<int:appointment_id>', methods=['POST'])
def cancel_appointment(appointment_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'You must be logged in.'})
    
    success, message = clinic.cancel_appointment(appointment_id, session['user_id'])
    return jsonify({'success': success, 'message': message})

@app.route('/some_route', methods=['GET', 'POST'])
def some_route():
    try:
        # Your code here
        return render_template('some_template.html')
    except Exception as e:
        print(f"An error occurred: {e}")
        return "An internal error occurred.", 500  # Return a 500 error response

if __name__ == '__main__':
    app.run()  # Run without debug mode