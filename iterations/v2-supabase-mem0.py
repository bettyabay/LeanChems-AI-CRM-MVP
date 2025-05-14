from dotenv import load_dotenv
from openai import OpenAI
from mem0 import Memory
import os

# Load environment variables
load_dotenv()

config = {
    "llm": {
        "provider": "openai",
        "config": {
            "model": os.getenv('MODEL_CHOICE', 'gpt-4o-mini')
        }
    },
    "vector_store": {
        "provider": "supabase",
        "config": {
            "connection_string": os.environ['DATABASE_URL'],
            "collection_name": "memories"
        }
    }    
}

openai_client = OpenAI()
memory = Memory.from_config(config)

def chat_with_memories(message: str, user_id: str = "default_user") -> str:
    # Retrieve relevant memories with reduced limit
    relevant_memories = memory.search(query=message, user_id=user_id, limit=2)
    memories_str = "\n".join(f"- {entry['memory']}" for entry in relevant_memories["results"])
    
    # Generate Assistant response
    system_prompt = f"You are a helpful AI. Answer the question based on query and memories.\nUser Memories:\n{memories_str}"
    messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": message}]
    response = openai_client.chat.completions.create(
        model=os.getenv('MODEL_CHOICE', 'gpt-3.5-turbo'),  # Using faster model by default
        messages=messages,
        temperature=0.7  # Adding temperature for faster responses
    )
    assistant_response = response.choices[0].message.content

    # Only store important conversations as memories
    if len(message) > 20:  # Only store if message is substantial
        messages.append({"role": "assistant", "content": assistant_response})
        memory.add(messages, user_id=user_id)

    return assistant_response

def main():
    print("Chat with AI (type 'exit' to quit)")
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() == 'exit':
            print("Goodbye!")
            break
        print(f"AI: {chat_with_memories(user_input)}")

if __name__ == "__main__":
    main()