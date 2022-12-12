import wx
from wx.adv import Animation, AnimationCtrl
from typing import Callable
from threading import RLock
from concurrent.futures import ThreadPoolExecutor
import time
import pyttsx3

import re

# Define event ID (for sending a command to the GUI from a thread)
ID_COMMAND = wx.NewId()


# Define result event
def evt_command(win, func):
    win.Connect(-1, -1, ID_COMMAND, func)


# Result Event Class
class CommandEvent(wx.PyEvent):
    def __init__(self, task: str, data: str):
        wx.PyEvent.__init__(self)
        self.SetEventType(ID_COMMAND)

        self.task = task  # The task to perform
        self.data = data  # The data needed for the task


# Main wx Frame object
class Main(wx.Frame):
    def __init__(self, parent, title: str, gui: 'ChatbotGUI', gif_path: str, show_timestamp: bool = False):
        wx.Frame.__init__(self, parent, -1, title=title)

        self.gui = gui  # Reference to the chatbot GUI
        self.show_timestamp = show_timestamp  # Keeps track of the 'show_timestamp'

        # For logging message history of user & AI
        self.user_message_history = []
        self.ai_message_history = []

        """ ==============
             GUI Elements
            ==============
        """

        # Grid for splitting the screen into two parts (I/O elements & Avatar GIF)
        self.grid = wx.BoxSizer(wx.HORIZONTAL)

        self.io_panel = wx.Panel(self)  # Left-side Panel (for all I/O elements)
        self.io_sizer = wx.BoxSizer(wx.VERTICAL)  # Sizer for the left-side panel

        self.gif_panel = wx.Panel(self)  # Right-side Panel (for the GIF & user input)
        self.gif_sizer = wx.BoxSizer(wx.VERTICAL)  # Sizer for the right-side Panel

        ####################

        # GIF Animation & Controller
        self.chatbot_gif = Animation(gif_path)  # ChatBot animated GIF asset
        self.chatbot_control = AnimationCtrl(self.gif_panel, -1, self.chatbot_gif)  # Animation controller for the GIF
        # User input Box & Submit Button
        self.input_box = wx.TextCtrl(self.gif_panel, style=wx.TE_PROCESS_ENTER | wx.TE_MULTILINE, size=wx.Size(800, 92))
        self.chat_button = wx.Button(self.gif_panel, label="Send your message to Zira")

        # Chat history Label/Textbox
        self.chat_label = wx.StaticText(self.io_panel, label="Chat History:")
        self.chat_box = wx.TextCtrl(self.io_panel, size=wx.Size(400, 660),
                                    style=wx.TE_READONLY | wx.TE_MULTILINE | wx.TE_RICH2)

        # AI Status Label/Textbox
        self.ai_status_label = wx.StaticText(self.io_panel, label="AI Status:")
        self.status_box = wx.TextCtrl(self.io_panel, style=wx.TE_READONLY)

        ####################

        # Add elements to the I/O sizer
        self.io_sizer.Add(self.chat_label, 0, wx.EXPAND | wx.LEFT | wx.TOP, 5)
        self.io_sizer.Add(self.chat_box, 0, wx.EXPAND | wx.ALL, 5)
        self.io_sizer.Add(self.ai_status_label, 0, wx.EXPAND | wx.LEFT | wx.TOP, 5)
        self.io_sizer.Add(self.status_box, 0, wx.EXPAND | wx.ALL, 5)

        # Add elements to the GIF sizer
        self.gif_sizer.Add(self.chatbot_control, wx.EXPAND, wx.ALL, 5)
        self.gif_sizer.Add(self.input_box, 0, wx.EXPAND | wx.ALL, 5)
        self.gif_sizer.Add(self.chat_button, 0, wx.EXPAND | wx.ALL, 5)

        # Add elements to the main grid sizer
        self.grid.Add(self.io_panel, 0, wx.EXPAND | wx.ALL)
        self.grid.Add(self.gif_panel, 0, wx.EXPAND | wx.ALL)

        # Size & fit the sizers
        self.io_panel.SetSizerAndFit(self.io_sizer)
        self.gif_panel.SetSizerAndFit(self.gif_sizer)
        self.SetSizerAndFit(self.grid)

        """ ===========================
             Bind Buttons to functions
            ===========================
        """
        self.Bind(wx.EVT_TEXT_ENTER, self.on_send_press)
        self.Bind(wx.EVT_BUTTON, self.on_send_press, self.chat_button)

        # Bind the event handler (for commands)
        evt_command(self, self.on_command)

    # Method to handle command events
    def on_command(self, event: CommandEvent):
        # Process send command
        if event.task == "send":
            self.send_ai_message(event.data)  # Send AI message to chat

        # Process GIF commands
        if event.task == "gif":
            # Start GIF:
            if event.data == "start":
                self.status_box.SetValue("Speaking...")  # Set AI status
                self.start_animation()  # Start GIF
            # Stop GIF:
            else:
                self.status_box.SetValue("Waiting...")  # Set AI status
                self.stop_animation()  # Stop GIF

        # Process thinking commands
        if event.task == "thinking":
            # Set AI status to 'thinking'
            if event.data == "start":
                self.status_box.SetValue("Thinking...")
            # Set AI status to 'waiting'
            else:
                self.stop_animation("Waiting...")

    def start_animation(self, event=None):
        self.chatbot_control.Play()

    def stop_animation(self, event=None):
        self.chatbot_control.Stop()

    # Method to update user & AI message histories
    def update_message_history(self):
        chat = ""
        # zira_color = wx.TextAttr(wx.RED)
        # user_color = wx.TextAttr(wx.BLUE)

        # zira_occurs = [x.start() for x in re.finditer('<Zira>', chat)]
        # user_occurs = [x.start() for x in re.finditer('<You>', chat)]
        # zira_occurs = self.find_str_pos('<Zira>', chat)
        # user_occurs = self.find_str_pos('<You>', chat)

        for i in reversed(range(len(self.ai_message_history))):
            chat += str(self.user_message_history[i]) + "\n"
            chat += str(self.ai_message_history[i]) + "\n"

        # Update chat
        self.chat_box.SetValue(chat)

        # print(chat)
        # print(zira_occurs, "\n", user_occurs)
        #
        # for i in zira_occurs:
        #     self.chat_box.SetStyle(i, i + len("<Zira>"), zira_color)
        #
        # for i in user_occurs:
        #     self.chat_box.SetStyle(i, i + len("<You>"), user_color)

    # Method for AI to send a message
    def send_ai_message(self, text: str):
        # Add AI message to message history
        self.ai_message_history.insert(0, self.get_timestamp() + " <Zira> " + str(text))

        # Update message history (chat window)
        self.update_message_history()

    # Method to clear user & AI chat history
    def clear_chat(self):
        self.user_message_history = []
        self.ai_message_history = []
        self.update_message_history()

    # Method to close the program
    def exit_bot(self):
        self.Close()

    # Method to handle "send" button press
    def on_send_press(self, event):
        # Read text box
        text = self.input_box.GetValue()
        if text == "":
            return

        # Clear the input box
        self.input_box.SetValue("")

        # Add user message to message history
        self.user_message_history.insert(0, self.get_timestamp() + " <You> " + text)

        # Update message history (chat window)
        self.update_message_history()

        # Call the message handler function (for the ChatBot GUI)
        self.gui.call_on_message(text)

    # Method to return current timestamp
    def get_timestamp(self) -> str:
        if self.show_timestamp:
            return "[" + time.strftime("%H:%M:%S", time.localtime()) + "] "
        else:
            return ""

    # def find_str_pos(self, sub, a_str):
    #     result = []
    #     k = 0
    #     while k < len(a_str):
    #         k = a_str.find(sub, k)
    #         if k == -1:
    #             return result
    #         else:
    #             result.append(k)
    #             k += 1
    #     return result


# Main application class (controls the GUI & interactions with the GUI)
class ChatbotGUI:
    def __init__(self, title: str, gif_path: str, show_timestamps: bool = True, default_voice_options: dict = None):
        self.app = wx.App()  # App object

        self.frame = Main(None, title, self, gif_path, show_timestamps)  # Main Frame

        self.__thinking = RLock()  # Mutex to prevent out-of-order responses
        self.__talking = RLock()  # Mutex to prevent AI talking over itself
        self.__pool = ThreadPoolExecutor(max_workers=8)  # Thread pool for executing speech & processing threads

        # Set default_voice_options to the default (if not defaults are provided)
        if default_voice_options is None:
            self.default_voice_options = {
                "rate": 100,
                "volume": 0.8,
                "voice": r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_EN-US_ZIRA_11.0"
            }
        else:
            self.default_voice_options = {
                "rate": default_voice_options.get("rate", 100),
                "volume": default_voice_options.get("rate", 0.8),
                "voice": default_voice_options.get(
                    "id",
                    r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_EN-US_ZIRA_11.0"
                )
            }

    # Clear chat history
    def clear(self):
        self.frame.clear_chat()

    # Exit application
    def exit(self):
        self.frame.exit_bot()

    # Start GIF
    def start_gif(self):
        self.frame.start_animation(None)

    # Stop GIF
    def stop_gif(self):
        self.frame.stop_animation(None)

    # Send chatbot message processing to a thread
    def process_and_send_ai_message(self, ai_response_generator: Callable[[str], str], text: str,
                                    callback: Callable[[], None] = None, voice_options: dict = None):
        # Submit the processes to the thread pool
        self.__pool.submit(self.__process_and_send, ai_response_generator, text, callback, voice_options)

    # Thread function used to process the
    def __process_and_send(self, ai_response_generator: Callable[[str], str], text: str,
                           callback: Callable[[], None] = None, voice_options: dict = None):
        # Block other processing threads until this one is finished:
        with self.__thinking:
            wx.PostEvent(self.frame, CommandEvent("thinking", "start"))  # Put up 'thinking' indicator

            response = ai_response_generator(text)  # Generate AI response

            wx.PostEvent(self.frame, CommandEvent("thinking", "stop"))  # Remove 'thinking' indicator

            # Send AI message
            self.send_ai_message(response, callback, voice_options)

    # Submit AI message
    def send_ai_message(self, text: str, callback: Callable[[], None] = None, voice_options: dict = None):
        # Submit method to the thread pool
        self.__pool.submit(self.__send_ai_message, text, callback, voice_options)

    # Thread method used to submit AI message
    def __send_ai_message(self, text: str, callback: Callable[[], None] = None, voice_options: dict = None):
        # If no speech options are provided (other than set defaults)
        if voice_options is None:
            voice_options = self.default_voice_options

        # Acquire permission to perform text-to-speech
        with self.__talking:
            # Code based on https://www.geeksforgeeks.org/text-to-speech-changing-voice-in-python/

            # Send message in chat via command event
            wx.PostEvent(self.frame, CommandEvent("send", text))

            # Initialize tts engine
            converter = pyttsx3.init()

            # Set properties (given provided options)
            converter.setProperty('rate', voice_options.get("rate", self.default_voice_options.get("rate")))
            converter.setProperty('volume', voice_options.get("volume", self.default_voice_options.get("volume")))
            converter.setProperty('voice', voice_options.get("voice", self.default_voice_options.get("voice")))

            # Start GIF (by sending command event)
            wx.PostEvent(self.frame, CommandEvent("gif", "start"))

            # Say the text
            converter.say(text)
            converter.runAndWait()

            # Stop the GIF (by sending the command event)
            wx.PostEvent(self.frame, CommandEvent("gif", "stop"))

        # Run the callback (if provided)
        if callback is not None:
            callback()

    # Handle the passing of incoming user message to the on_message handler
    def call_on_message(self, text: str):
        if getattr(self, "on_message", None) is None:
            print("Please define the 'on_message' function!")
            return

        # Call the on_message handler
        getattr(self, "on_message")(self, text)

    # Easily define the on_message handler method
    def event(self, coroutine):
        # Handle general on_connect/on_disconnect handlers
        if coroutine.__name__ == "on_message":
            # Replace the existing coroutine with the provided one
            setattr(self, coroutine.__name__, coroutine)
            return True
        return False

    # Run the chatbot GUI
    def run(self) -> None:
        self.frame.Show()
        self.app.MainLoop()
