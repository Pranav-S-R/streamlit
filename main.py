import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
import threading
import asyncio
import speech_recognition as sr
import pyttsx3
import webbrowser
import os
import requests
import winsound
import openai
from rasa.core.agent import Agent
from rasa.shared.nlu.training_data.message import Message
import queue

# Setting OpenAI API key
openai.api_key = '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'

# Initializing speech recognition
recognizer = sr.Recognizer()

# Initializing text-to-speech
tts = pyttsx3.init()

# Initializing NLP engine
interpreter = Agent.load("models\\20240110-090011-radiant-color.tar.gz")

class VoiceAssistant:
    def __init__(self):
        self.stop_event = threading.Event()
        self.command_queue = queue.Queue()
        self.async_queue = queue.Queue()
        self.loop = None

    def start_voice_assistant(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.listen_for_commands())

    def listen_for_commands(self):
        wit_api_key = 'C2GLKMJ4CG3F6O26WPQ2522VVC7DCGTU'

        while not self.stop_event.is_set():
            try:
                with sr.Microphone() as source:
                    print("Listening...")
                    winsound.Beep(500, 500)
                    audio = recognizer.listen(source)
                    command = recognizer.recognize_wit(audio, key=wit_api_key)
                    print(f"User said: {command}")

                    if "assistant" in command.lower():
                        asyncio.run(self.process_command(command))
                        self.command_queue.put(("User", command))
                    else:
                        system_response = self.generate_openai_response(command)
                        print(system_response)
                        self.speak(system_response)
                        # Put the system response in the queue
                        self.command_queue.put(("System", system_response))

            except sr.UnknownValueError:
                print("Could not understand audio")
                self.speak("Could not understand audio, please repeat again")

            except sr.RequestError as e:
                print(f"Could not request results; {e}")
                self.speak(f"Could not request results; {e}")

    async def process_command(self, command):
        system_response = ""  # Initialize the variable

        # Creating a message object using the interpreter
        message = Message(data={"text": command})
        
        # Using the interpreter to parse the message
        result = await interpreter.parse_message(message.data["text"])
        intent = result.get("intent", {}).get("name")
        confidence = result.get("intent", {}).get("confidence", 0.0)
        entities = result.get("entities", [])

        # Setting a confidence threshold for better results
        confidence_threshold = 0.5

        if confidence >= confidence_threshold:
            # Processing the command based on the recognized intent
            if intent == "search":
                search_query = next((e['value'] for e in entities if e['entity'] == 'search_query'), None)
                if search_query:
                    self.perform_web_search(search_query)
                else:
                    system_response = "Please specify what you want to search for."
            elif intent == "open":
                app_name = next((e['value'] for e in entities if e['entity'] == 'app_name'), None)
                if app_name:
                    self.open_application(app_name)
                else:
                    system_response = "Please specify the application to open."
            elif intent == "weather":
                location = next((e['value'] for e in entities if e['entity'] == 'location'), None)
                if location:
                    self.fetch_weather(location)
                else:
                    system_response = "Please specify the city for weather information."
            else:
                system_response = self.generate_openai_response(command)
        else:
            system_response = "Sorry, I don't understand that command."

        # Printing and Speaking the system response
        print(system_response)
        self.speak(system_response)

    # Using OpenAI API to generate a response
    def generate_openai_response(self, prompt):
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
        )

        return response['choices'][0]['message']['content'].strip()

    # Using OpenWeatherMap API to generate a response
    def fetch_weather(self, city):
        api_key = '0b1fc621e052037ff715369716e080f1'
        base_url = 'http://api.openweathermap.org/data/2.5/weather'
        params = {'q': city, 'appid': api_key}

        response = requests.get(base_url, params=params)
        data = response.json()

        if data['cod'] == 200:
            temperature = data['main']['temp']
            description = data['weather'][0]['description']
            print(f"Weather in {city}: {description}, Temperature: {temperature/10}°C")
            self.speak(f"Weather in {city}: {description}, Temperature: {temperature/10}°C")
        else:
            print("Could not fetch weather information.")
            self.speak("Could not fetch weather information.")

    # Using Os Module to generate a response
    def open_application(self, app_name):
        app_paths = {
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "chrome": "chrome.exe",
            "File Explorer": "exlporer.exe",
            "Email" : "outlook.exe"
        }

        if app_name in app_paths:
            app_path = app_paths[app_name]
            os.system(f'start {app_path}')
            print(f"Opening {app_name}...")
            self.speak(f"Opening {app_name}...")
        else:
            print("Application not found.")
            self.speak("Application not found.")

    # Using Webbrowser Module to generate a response
    def perform_web_search(self, search_query):
        search_url = f"https://www.google.com/search?q={search_query}"
        webbrowser.open(search_url)
        print(f"Performing a web search for: {search_query}")
        self.speak(f"Performing a web search for: {search_query}")

    # Using pyttsx3 to change the text to audio
    def speak(self, text):
        tts.say(text)
        tts.runAndWait()

class VoiceAssistantGUI:
    def __init__(self, root, voice_assistant):
        self.root = root
        self.root.title("V.A.P.A.S")

        self.voice_assistant = voice_assistant
        self.create_widgets()

        # Periodically check the command queue for new items
        self.root.after(1000, self.check_queue)

    def create_widgets(self):
        # Create a text widget for displaying user commands and system responses
        self.text_widget = scrolledtext.ScrolledText(self.root, width=40, height=10, wrap=tk.WORD)
        self.text_widget.grid(column=0, row=0, columnspan=3, pady=10, padx=10, sticky='nsew')

        # Create an entry widget for manual command input
        self.command_entry = ttk.Entry(self.root, width=30)
        self.command_entry.grid(column=0, row=1, pady=10, padx=10, sticky='nsew')

        # Create a button to execute the manual command
        self.execute_button = ttk.Button(self.root, text="Execute Command", command=self.execute_command)
        self.execute_button.grid(column=1, row=1, pady=10, padx=10, sticky='nsew')

        # Create a button to start the voice assistant
        self.start_button = ttk.Button(self.root, text="Start", command=self.start_voice_assistant)
        self.start_button.grid(column=2, row=1, pady=10, padx=10, sticky='nsew')

        # Create a button to stop the voice assistant
        self.stop_button = ttk.Button(self.root, text="Stop", command=self.stop_voice_assistant)
        self.stop_button.grid(column=2, row=2, pady=10, padx=10, sticky='nsew')

        # Configure row and column weights for resizing
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=1)
        self.root.columnconfigure(2, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

    def check_queue(self):
        while not voice_assistant.command_queue.empty():
            role, text = voice_assistant.command_queue.get()
            tag = "user_command" if role == "User" else "system_response"
            self.display_text(f"{role}: {text}", tag=tag)
        # Continue checking the queue periodically
        self.root.after(1000, self.check_queue)

    def execute_command(self):
        command = self.command_entry.get().strip()
        if command:
            self.display_text(f"User: {command}", tag="user_command")
            asyncio.run(self.voice_assistant.process_command(command))

    def start_voice_assistant(self):
        # Start voice assistant in a separate thread
        voice_assistant_thread = threading.Thread(target=self.voice_assistant.listen_for_commands)
        voice_assistant_thread.start()
        self.display_text("Voice Assistant started.")

    def stop_voice_assistant(self):
        self.voice_assistant.stop_event.set()
        self.display_text("Voice Assistant stopped.")

    def quit(self):
        self.voice_assistant.stop_event.set()
        self.root.destroy()

    def display_text(self, text, tag=None):
        # Display text in the text widget with the specified tag
        self.text_widget.insert(tk.END, f"{text}\n", tag)
        self.text_widget.see(tk.END)

if __name__ == "__main__":
    # Create an instance of VoiceAssistant
    voice_assistant = VoiceAssistant()

    # Create GUI
    root = tk.Tk()
    app = VoiceAssistantGUI(root, voice_assistant)

    # Configure text widget tag styles
    app.text_widget.tag_configure("user_command", foreground="blue")
    app.text_widget.tag_configure("system_response", foreground="green")

    # Start voice assistant in a separate thread
    voice_assistant_thread = threading.Thread(target=voice_assistant.start_voice_assistant)
    voice_assistant_thread.start()
    
    root.mainloop()