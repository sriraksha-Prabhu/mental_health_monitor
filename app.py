from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import pyttsx3
import requests
import threading
import os
import random
import re  

app = Flask(__name__)

# Configure SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # SQLite database for simplicity
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Secret key for session management
app.secret_key = os.urandom(24)

# Initialize the login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# User model (removed email field)
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

# Create the database tables
with app.app_context():
    db.create_all()


# Load user function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Initialize the text-to-speech engine
engine = pyttsx3.init()
engine.setProperty('rate', 150)
engine.setProperty('volume', 0.9)

# Gemini API Setup
API_KEY = "AIzaSyBnalPeCH1ZsClB_7-AFRhpLZC64hMuXwQ"
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

# In-memory list to store reviews temporarily
reviews = []

# Home route (Login page)
@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

# Register route (For creating new users)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Check if the 'confirm_password' field exists
        if not confirm_password:
            return "Confirm password field is missing", 400

        # Check if passwords match
        if password != confirm_password:
            error = 'Passwords do not match'
            return render_template('register.html', error=error)
        
        # Check if the username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            error = 'Username already taken. Please choose another one.'
            return render_template('register.html', error=error)

        # Hash the password and save to the database
        hashed_password = generate_password_hash(password)  # Default method 'pbkdf2_sha256'
        new_user = User(username=username, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        # After successful registration, redirect to login
        success_message = "Registration successful! Please log in."
        return render_template('login.html', success_message=success_message)

    return render_template('register.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if user exists and password matches
        user = User.query.filter_by(username=username).first() 
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            return 'Invalid username or password'

    return render_template('login.html')

# Dashboard route (Requires login)
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', username=current_user.username)

# Chat route
@app.route('/chat')
@login_required
def chat():
    return render_template('chat.html')

# Virtual Companion route
@app.route('/virtual_companion')
def virtual_companion():
    return render_template('virtual_companion.html')

# About page route
@app.route('/about')
def about():
    return render_template('about.html')

# Contact page route
@app.route('/contact')
def contact():
    return render_template('contact.html')

# Speech route
@app.route('/speech')
@login_required
def speech():
    return render_template('speech.html')

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Main entry point (Frontend route to serve the main page)
@app.route('/index')
def index():
    return render_template('index.html')

# Backend route to handle user input (both text and speech) and return response
@app.route('/talk', methods=['POST'])
def talk():
    user_input = request.form['user_input']
    prompt = f"You are a supportive and empathetic companion. The user said: {user_input}. Respond empathetically and encourage self-care."
    response = get_response_from_gemini(prompt)

    return jsonify({'response': response})

def get_response_from_gemini(prompt):
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }

    try:
        response = requests.post(
            f"{API_URL}?key={API_KEY}",
            headers=headers,
            json=payload
        )
        if response.status_code == 200:
            result = response.json()
            return result['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"An error occurred: {e}"

# Route to handle text-to-speech
@app.route('/speak', methods=['GET'])
def speak():
    text = request.args.get('text', '')
    if text:
        # Create a separate thread for speaking to avoid blocking the Flask app
        def speak_text():
            engine.say(text)
            engine.runAndWait()

        threading.Thread(target=speak_text).start()
        return '', 200  # Return empty response after speaking

    return '', 400  # Return error if no text was provided

@app.route('/speech_process', methods=['POST'])
def speech_process():
    try:
        user_input = request.form['user_input']
        print(f"User Input: {user_input}")  # Debugging line to check input

        # Generate a response based on user input
        response = generate_response(user_input)
        print(f"Generated Response: {response}")  # Debugging line to check response

        # Return the response as a JSON object
        return jsonify({'response': response})

    except Exception as e:
        print(f"Error: {e}")  # Print any errors that occur
        return jsonify({'response': 'Sorry, something went wrong on the server.'}), 500

def generate_response(user_input):
    # Simple response generator (replace this with more sophisticated logic or AI)
    responses = [
        "Hello! How can I help you today?",
        "I'm here to assist you. What do you need?",
        "I don't understand that. Can you say it again?",
        "How are you doing today?"
    ]
    return random.choice(responses)

@app.route('/stop_speech', methods=['GET'])
def stop_speech():
    try:
        engine.stop()  # Stop the speech
        return '', 200  # Return success response
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Review routes
@app.route('/reviews')
def reviews_page():
    return render_template('index.html', reviews=reviews)

@app.route('/submit_review', methods=['POST'])
def submit_review():
    reviewer_name = request.form['reviewer_name']
    review_text = request.form['review_text']
    
    # Add the review to the in-memory list
    reviews.append({'name': reviewer_name, 'review': review_text})
    
    return render_template('index.html', reviews=reviews)

# Start Flask app
if __name__ == '__main__':
    app.run(debug=True)
