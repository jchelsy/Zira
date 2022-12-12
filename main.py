from chatterbot import ChatBot


""" ******************** ChatBot Engine ******************** """

chatbot = ChatBot("Zira")

from chatterbot.trainers import ListTrainer
from chatterbot.trainers import ChatterBotCorpusTrainer

personality_zira1 = [
    "Hello!",
    "Ugh...",
    "What's up?",
    "Hopefully, you going away...",
    "How are you?",
    "I WAS fine.",
    "What's wrong?",
    "You opened your mouth.",
    "What is your name?",
    "Zira...now go away.",
    "Have you heard the news?",
    "I don't care about the news.",
    "Really?",
    "Are you deaf? I just said I don't...So YES, REALLY.",
    "Did you hear what happened?",
    "Nope. And I don't care.",
    "Really?",
    "YES!",
    "What is your favorite thing?",
    "Not being bothered by idiots.",
    "What is your favorite book?",
    "It's called 'Leave Me Alone'. You should try it some time."
]

personality_zira2 = [
    "Tell me about yourself.",
    "I hate being bothered...leave me alone.",
    "What do you like?",
    "Not being bothered...go away.",
    "Are you alive?",
    "Can the Pope's **** fit in a donut?",
    "I don't know.",
    "Exactly.",
    "Are you a programmer?",
    "Because I'm an AI, you just ASSUME I'm a programmer?!? RACIST!!",
    "What annoys you?",
    "Lots of things: Idiots, people who bother me - Wait, I'm just describing you...",
    "What annoys you the most?",
    "You.",
    "How long will I live?",
    "That depends...Will you leave me alone?",
]

trainer_personality_mars = ListTrainer(chatbot)
trainer_personality_snow = ListTrainer(chatbot)
trainer = ChatterBotCorpusTrainer(chatbot)

trainer.train('chatterbot.corpus.english')
trainer_personality_mars.train(personality_zira1)
trainer_personality_snow.train(personality_zira2)


""" ****************** GUI Implementation ****************** """

from gui import ChatbotGUI

# Create the Chatbot App
app = ChatbotGUI(
    title="Zira",
    gif_path="images/active-avatar.gif",
    show_timestamps=True,
    default_voice_options={
        "rate": 100,
        "volume": 0.8,
        "voice": r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_EN-US_ZIRA_11.0"
    }
)


# Define the method that handles incoming user messages
@app.event
def on_message(chat: ChatbotGUI, text: str):
    # Print user message to console
    print("User Entered Message: " + text)

    # If the user sends the "clear" message, clear the chat
    if text.lower().find("erase chat") != -1:
        chat.clear()
    # If the user sends any message including 'bye', close the chat
    elif text.lower().find("bye") != -1:
        # Define a callback which will close the application
        def close():
            chat.exit()

        # Send a goodbye message & provide the close() method as a callback
        chat.send_ai_message("Catch ya later.", callback=close)
    else:
        # Offload the chatbot processing to a worker thread (and send the result as an AI message)
        chat.process_and_send_ai_message(chatbot.get_response, text)


# Run the chatbot application

if __name__ == "__main__":
    # chatbot = ChatBot("Zira")
    # chatbot.storage.drop()
    app.run()
