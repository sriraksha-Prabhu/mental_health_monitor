import requests
import pyttsx3
import speech_recognition as sr

# Set your Gemini API key
API_KEY = "AIzaSyBnalPeCH1ZsClB_7-AFRhpLZC64hMuXwQ"  # Replace with your Gemini API key
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

# Initialize the text-to-speech engine
engine = pyttsx3.init()
engine.setProperty('rate', 150)  # Speed of speech
engine.setProperty('volume', 0.9)  # Volume level

# Initialize the speech recognizer
recognizer = sr.Recognizer()

def speak(text):
    """Speak the given text."""
    engine.say(text)
    engine.runAndWait()

def listen():
    """Listen to the user and return the transcribed text."""
    with sr.Microphone() as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source, timeout=5)
            print("Processing...")
            return recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            return "I couldn't understand that. Could you please repeat?"
        except sr.RequestError:
            return "Sorry, I am having trouble understanding you. Please try again."

def get_response_from_gemini(prompt):
    """Get a response from Gemini API based on the user's input."""
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
        print(response.status_code)
        if response.status_code == 200:
         
            # Parse the response
            result = response.json()
            return result['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"What is the problem ?{e}"

def main():
    """Main function to interact with the virtual talking companion."""
    print("Hi, I'm your virtual mental health companion. How can I support you today?")
    speak("Hi, I'm your virtual mental health companion. How can I support you today?")
    
    while True:
        user_input = listen()
        
        if "exit" in user_input.lower() or "quit" in user_input.lower():
            print("Take care! I'm always here if you need me.")
            speak("Take care! I'm always here if you need me.")
            break
        
        print(f"You: {user_input}")
        prompt = f"You are a supportive and empathetic companion. The user said: {user_input}. Respond empathetically and encourage self-care."
        response = get_response_from_gemini(prompt)
        print(response)
        print(f"Companion: {response}")
        speak(response)

if __name__ == "__main__":
    main()