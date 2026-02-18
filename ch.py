import ollama

def chatbot():
    print("Local Ollama Chatbot (type 'quit' to exit)\n")

    while True:
        user_input = input("You: ")

        if user_input.lower() == "quit":
            print("Goodbye ")
            break

        response = ollama.chat(
            model="llama3.2",   
            messages=[
                {"role": "user", "content": user_input}
            ]
        )

        print("BOT:", response['message']['content'])

if __name__ == "__main__":
    chatbot()
