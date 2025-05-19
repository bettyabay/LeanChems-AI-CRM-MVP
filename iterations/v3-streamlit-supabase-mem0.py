import os
import streamlit as st
# Streamlit page configuration must be the first Streamlit command
st.set_page_config(
    page_title="AI Powered CRM",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)
from dotenv import load_dotenv
from openai import OpenAI
from mem0 import Memory
import supabase
from supabase.client import Client, ClientOptions
from pathlib import Path
import uuid
import sys
from tenacity import retry, stop_after_attempt, wait_exponential
import re
import openai
from PyPDF2 import PdfReader
from thefuzz import fuzz
import datetime
import pandas as pd

# --- Custom CSS for beautiful UI ---
st.markdown("""
    <style>
    .stButton>button {
        color: white;
        background: #4F8BF9;
        border-radius: 8px;
        padding: 0.5em 2em;
        font-weight: 600;
        border: none;
        margin: 0.5em 0;
    }
    .stTextInput>div>div>input, .stTextArea>div>textarea {
        border-radius: 8px;
        border: 1px solid #4F8BF9;
        background: #F7F9FB;
        padding: 0.5em;
        color: #222;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 1.5em;
    }
    .stExpanderHeader {
        font-weight: 600;
        color: #4F8BF9;
    }
    .stRadio>div>label {
        font-weight: 500;
    }
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #4F8BF9;
    }
    /* --- DARK MODE SUPPORT --- */
    @media (prefers-color-scheme: dark) {
        .stTextInput>div>div>input, .stTextArea>div>textarea {
            background: #222 !important;
            color: #fff !important;
            border: 1px solid #4F8BF9 !important;
        }
        .stButton>button {
            background: #222 !important;
            color: #fff !important;
        }
        .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
            color: #4F8BF9 !important;
        }
        .stExpanderHeader {
            color: #4F8BF9 !important;
        }
        /* Add more overrides as needed for other elements */
    }
    </style>
""", unsafe_allow_html=True)

# Load environment variables
project_root = Path(__file__).resolve().parent.parent
dotenv_path = project_root / '.env'
load_dotenv(dotenv_path, override=True)

# Initialize Supabase client
supabase_url = os.environ.get("SUPABASE_URL", "")
supabase_key = os.environ.get("SUPABASE_KEY", "")
supabase_client = supabase.create_client(supabase_url, supabase_key)

model = os.getenv('MODEL_CHOICE', 'gpt-3.5-turbo')

# Cache OpenAI client and Memory instance
@st.cache_resource
def get_openai_client():
    return OpenAI()

@st.cache_resource
def get_memory():
    config = {
        "llm": {
            "provider": "openai",
            "config": {
                "model": model
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
    return Memory.from_config(config)

# Get cached resources
openai_client = get_openai_client()
memory = get_memory()

def generate_customer_id():
    """Generate a unique customer ID"""
    # Generate a UUID for the database
    return str(uuid.uuid4())

def generate_display_id():
    """Generate a human-readable customer ID in format LC-YYYY-CUST-XXXX"""
    year = datetime.datetime.now().year
    
    # Get all customer IDs to find the highest number
    response = supabase_client.table('customers').select('display_id').execute()
    max_num = 0
    
    if response.data:
        for customer in response.data:
            display_id = customer.get('display_id', '')
            # Check if the ID matches our format (LC-YYYY-CUST-XXXX)
            if isinstance(display_id, str) and display_id.startswith(f'LC-{year}-CUST-'):
                try:
                    num = int(display_id.split('-')[-1])
                    max_num = max(max_num, num)
                except ValueError:
                    continue
    
    # Increment the highest number found
    new_num = max_num + 1
    return f"LC-{year}-CUST-{new_num:04d}"

def find_similar_customers(customer_name: str, threshold: int = 80):
    """Find similar customer names using fuzzy matching"""
    response = supabase_client.table('customers').select('customer_name,customer_id').execute()
    similar_customers = []
    
    for customer in response.data:
        # Calculate similarity score
        ratio = fuzz.ratio(customer_name.lower(), customer['customer_name'].lower())
        if ratio >= threshold:
            similar_customers.append({
                'name': customer['customer_name'],
                'id': customer['customer_id'],
                'similarity': ratio
            })
    
    return sorted(similar_customers, key=lambda x: x['similarity'], reverse=True)

def generate_customer_profile(customer_name: str, user_id: str):
    """Generate a customer profile using AI and existing conversations"""
    # Search relevant documents and memories
    relevant_docs = search_documents(customer_name, user_id)
    relevant_memories = get_cached_memories(customer_name, user_id)
    
    # Combine all context
    context = ""
    if relevant_docs:
        context += "\nRelevant conversations:\n"
        for doc in relevant_docs:
            context += f"\n{doc.get('content', '')}\n"
    
    if relevant_memories["results"]:
        context += "\nRelevant memories:\n"
        for memory in relevant_memories["results"]:
            context += f"\n{memory['memory']}\n"
    
    # Create the prompt for profile generation
    system_prompt = """You are a CRM assistant specialized in chemical trading. 
    Generate a detailed customer profile based on the company name and any available context.
    Include:
    1. Company background and industry
    2. Potential product interests (RDP, SBR, HPMC)
    3. Location and key contacts (if found)
    4. Current suppliers (if known)
    5. Sales stage classification
    6. Initial SPIN selling questions to ask
    
    Format your response in a clear, structured way."""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Generate a profile for: {customer_name}\n\nContext:{context}"}
    ]
    
    # Get response and convert to string
    response = get_openai_response(messages, model)
    profile_text = ""
    for chunk in response:
        if chunk.choices[0].delta.content:
            profile_text += chunk.choices[0].delta.content
    return profile_text

def create_new_customer(customer_name: str, user_id: str):
    """Handle the complete customer creation workflow"""
    # Ensure we have a valid state
    #  Initialize session state
    if 'customer_creation_state' not in st.session_state or st.session_state.customer_creation_state is None:
        st.session_state.customer_creation_state = {
            'step': 1,
            'customer_name': customer_name,
            'profile': None,
            'confirmed': False
        }
    # This checks if we're already creating a customer.
    # If not, it initializes the process at Step 1, with blank profile and confirmation.

    #This is just storing that dictionary in a local variable called state for easy use.
    state = st.session_state.customer_creation_state
    
    # Step 1: Check for similar customers
    #Calls the function that looks for existing customer names that are similar
    if state['step'] == 1:
        similar_customers = find_similar_customers(customer_name)
        
        if similar_customers:
            st.warning(f"Similar customer found: {similar_customers[0]['name']}")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Create New Customer Anyway"):
                    state['step'] = 2
                    st.rerun()
            with col2:
                if st.button("Cancel"):
                    st.session_state.customer_creation_state = None
                    st.rerun()
            return None
        else:
            state['step'] = 2
            st.rerun()
    
    # Step 2: Generate customer profile
    if state['step'] == 2:
        with st.spinner("Generating customer profile..."):
            profile = generate_customer_profile(customer_name, user_id)
            state['profile'] = profile
            st.write("Generated Profile:")
            st.write(profile)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Confirm and Add to CRM"):
                    state['confirmed'] = True
                    state['step'] = 3
                    st.rerun()
            with col2:
                if st.button("Cancel"):
                    st.session_state.customer_creation_state = None
                    st.rerun()
            return None
    
    # Step 3: Create database entry
    if state['step'] == 3 and state['confirmed']:
        customer_id = generate_customer_id()
        display_id = generate_display_id()
        
        data = {
            "customer_id": customer_id,
            "display_id": display_id,
            "customer_name": customer_name,
            "input_conversation": [f"Create profile for {customer_name}"],
            "output_conversation": [str(state['profile'])]
        }
        
        try:
            response = supabase_client.table('customers').insert(data).execute()
            
            if response.data:
                st.success(f"Customer {customer_name} created successfully! (ID: {display_id})")
                # Clear the creation state
                st.session_state.customer_creation_state = None
                return response.data[0]
            else:
                st.error("Failed to create customer")
                return None
        except Exception as e:
            st.error(f"Error creating customer: {str(e)}")
            return None

# Authentication functions
def sign_up(email, password, full_name):
    try:
        response = supabase_client.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "full_name": full_name
                }
            }
        })
        if response and response.user:
            st.session_state.authenticated = True
            st.session_state.user = response.user
            st.rerun()
        return response
    except Exception as e:
        st.error(f"Error signing up: {str(e)}")
        return None

def sign_in(email, password):
    try:
        response = supabase_client.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        if response and response.user:
            # Store user info directly in session state
            st.session_state.authenticated = True
            st.session_state.user = response.user
            st.rerun()
        return response
    except Exception as e:
        st.error(f"Error signing in: {str(e)}")
        return None

def sign_out():
    try:
        supabase_client.auth.sign_out()
        # Clear only authentication-related session state
        st.session_state.authenticated = False
        st.session_state.user = None
        # Set a flag to trigger rerun on next render
        st.session_state.logout_requested = True
    except Exception as e:
        st.error(f"Error signing out: {str(e)}")

# Add caching for frequently accessed data
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_cached_memories(query, user_id):
    try:
        return memory.search(query=query, user_id=user_id, limit=2)
    except Exception as e:
        st.error(f"Error retrieving memories: {str(e)}")
        return {"results": []}

# Add retry decorator for API calls
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def get_openai_response(messages, model):
    try:
        return openai_client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True
        )
    except Exception as e:
        st.error(f"Error getting AI response: {str(e)}")
        raise

def search_documents(query: str, user_id: str, limit: int = 3):
    try:
        # Get embedding for the query with retry
        @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
        def get_embedding():
            return openai_client.embeddings.create(
                input=query,
                model="text-embedding-3-small"
            )
        
        response = get_embedding()
        query_embedding = response.data[0].embedding

        # Search Supabase documents table with retry
        @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
        def search_supabase():
            return supabase_client.rpc(
                'match_documents',
                {
                    'query_embedding': query_embedding,
                    'match_count': limit,
                    'match_threshold': 0.5,
                    'filter': {}
                }
            ).execute()

        response = search_supabase()

        if response.data:
            return response.data
        return []
    except Exception as e:
        st.error(f"Document search failed: {str(e)}")
        st.error("Please check your internet connection and try again.")
        return []

# --- Customer management functions ---
def store_customer_conversation(customer_name: str, user_input: str, ai_output: str):
    response = supabase_client.table('customers').insert({
        'customer_name': customer_name,
        'input_conversation': [user_input],
        'output_conversation': [ai_output]
    }).execute()
    return response.data

def fetch_customer(customer_name: str):
    response = supabase_client.table('customers').select("*").eq('customer_name', customer_name).execute()
    if response.data:
        return response.data[0]
    return None

def update_customer_memory(customer_id: str, new_input: str, new_output: str):
    customer = supabase_client.table('customers').select("*").eq('customer_id', customer_id).single().execute()
    if customer.data:
        updated_inputs = customer.data['input_conversation'] + [new_input]
        updated_outputs = customer.data['output_conversation'] + [new_output]
        response = supabase_client.table('customers').update({
            'input_conversation': updated_inputs,
            'output_conversation': updated_outputs
        }).eq('customer_id', customer_id).execute()
        return response.data
    return None

def handle_create_customer_flow(customer_name: str, user_input: str, ai_output: str):
    customer = fetch_customer(customer_name)
    if customer:
        update_customer_memory(customer['customer_id'], user_input, ai_output)
        st.success(f"Customer {customer_name} found. Conversation memory updated.")
    else:
        store_customer_conversation(customer_name, user_input, ai_output)
        st.success(f"Customer {customer_name} not found. Created new customer.")

def get_all_customer_names():
    response = supabase_client.table('customers').select('customer_name,customer_id').execute()
    if response.data:
        return {c['customer_name']: c['customer_id'] for c in response.data}
    return {}

def chat_with_memories(message, user_id):
    try:
        # 1. Detect if a customer is mentioned in the message
        customer_dict = get_all_customer_names()
        mentioned_customer = None
        for name in customer_dict:
            if name.lower() in message.lower():
                mentioned_customer = name
                break

        # 2. Fetch customer conversations if mentioned
        customer_context = ""
        if mentioned_customer:
            customer_data = fetch_customer(mentioned_customer)
            if customer_data:
                customer_context += f"\nCustomer: {mentioned_customer}\n"
                # Add recent input/output conversations to context
                inps = customer_data.get('input_conversation', [])
                outs = customer_data.get('output_conversation', [])
                for inp, out in zip(inps, outs):
                    customer_context += f"User: {inp}\nAI: {out}\n"

        # 3. Fetch relevant memories (filter out empty/irrelevant)
        relevant_memories = get_cached_memories(message, user_id)
        memories_str = "\n".join(
            f"- {entry['memory']}" for entry in relevant_memories["results"]
            if entry['memory'] and entry['memory'].strip() and entry['memory'].strip().lower() != "not specified"
        )
        
        # 4. Search relevant documents
        relevant_docs = search_documents(message, user_id)
        docs_str = ""
        if relevant_docs:
            docs_str = "\nRelevant Conversations from Database:\n"
            for i, doc in enumerate(relevant_docs, 1):
                docs_str += f"\nConversation {i}:\n{doc.get('content', '')}\n"
        
        # 5. Build the system prompt/context
        system_prompt = f"""
You are a helpful AI assistant specialized in chemical trading and CRM.
If the user asks about a specific customer, use the customer's conversation history below.
Also use the provided memories and relevant conversations from the database.
If you don't find relevant information, say so.

Customer context:
{customer_context}

        User Memories:
        {memories_str}
        
{docs_str}
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ]
        
        with st.spinner("Thinking..."):
            response = get_openai_response(messages, model)
            full_response = ""
            response_placeholder = st.empty()
            for chunk in response:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    response_placeholder.markdown(full_response + "▌")
            response_placeholder.markdown(full_response)

            # Show what conversations were used
            if relevant_docs:
                with st.expander("Conversations used for this response"):
                    for i, doc in enumerate(relevant_docs, 1):
                        st.write(f"Conversation {i}:")
                        st.write(doc.get('content', ''))

        # Create new memories from the conversation
        messages.append({"role": "assistant", "content": full_response})
        memory.add(messages, user_id=user_id)

        # --- New: Automatically store conversation if customer is mentioned ---
        try:
            if mentioned_customer:
                update_customer_memory(customer_dict[mentioned_customer], message, full_response)
                st.info(f"Conversation added to {mentioned_customer}'s record.")
        except Exception as e:
            st.warning(f"Tried to auto-store conversation for mentioned customer, but got error: {str(e)}")

        return full_response
    except Exception as e:
        st.error(f"An error occurred during chat: {str(e)}")
        return "I apologize, but I encountered an error. Please try again."

def search_customers(query: str, limit: int = 5):
    try:
        # Search for customers by name
        response = supabase_client.table('customers').select('*').ilike('customer_name', f'%{query}%').limit(limit).execute()
        
        if response.data:
            return response.data
        return []
    except Exception as e:
        st.error(f"Error searching customers: {str(e)}")
        return []

def get_customer_conversations(customer_name: str):
    try:
        # Get customer conversations
        response = supabase_client.table('customers').select('*').eq('customer_name', customer_name).single().execute()
        
        if response.data:
            return response.data
        return None
    except Exception as e:
        st.error(f"Error getting customer conversations: {str(e)}")
        return None

# Update the sidebar section to handle the customer creation state
def render_customer_creation_ui(user_id):
    st.subheader("Create New Customer")
    new_customer_name = st.text_input("Enter Customer Name", key="new_customer_name")
    
    if new_customer_name:
        # Initialize or get the current state
        if 'customer_creation_state' not in st.session_state:
            st.session_state.customer_creation_state = {
                'step': 1,
                'customer_name': new_customer_name,
                'profile': None,
                'confirmed': False
            }
        
        # Only proceed if we have a valid state
        if st.session_state.customer_creation_state is not None:
            create_new_customer(
                st.session_state.customer_creation_state['customer_name'],
                user_id
            )
        else:
            # Reset the state with the new customer name
            st.session_state.customer_creation_state = {
                'step': 1,
                'customer_name': new_customer_name,
                'profile': None,
                'confirmed': False
            }
            create_new_customer(new_customer_name, user_id)

# Initialize session state
if not st.session_state.get("messages", None):
    st.session_state.messages = []

if not st.session_state.get("authenticated", None):
    st.session_state.authenticated = False

if not st.session_state.get("user", None):
    st.session_state.user = None

# Check for logout flag and clear it after processing
if st.session_state.get("logout_requested", False):
    st.session_state.logout_requested = False
    st.rerun()

# --- All function definitions (move these to the top, before main logic) ---
def get_customer_interactions(customer_id: str):
    """Fetch all interactions for a specific customer from the customers table"""
    try:
        response = supabase_client.table('customers').select('*').eq('customer_id', customer_id).single().execute()
        if response.data:
            # Combine input and output conversations into interactions
            interactions = []
            for i, (input_msg, output_msg) in enumerate(zip(
                response.data.get('input_conversation', []),
                response.data.get('output_conversation', [])
            )):
                interactions.append({
                    'interaction_input': input_msg,
                    'llm_output_summary': output_msg,
                    'created_at': response.data.get('created_at')  # Using the customer's creation time
                })
            return interactions
        return []
    except Exception as e:
        st.error(f"Error fetching interactions: {str(e)}")
        return []

def analyze_spin_elements(text: str):
    """Analyze text for SPIN selling elements"""
    system_prompt = """Analyze the following sales interaction and identify SPIN elements:
    - Situation: Current state or context
    - Problem: Issues or challenges mentioned
    - Implication: Consequences of the problem
    - Need-Payoff: Benefits of solving the problem
    
    Format your response as:
    SPIN Analysis:
    - Situation: [details]
    - Problem: [details]
    - Implication: [details]
    - Need-Payoff: [details]
    """
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": text}
    ]
    
    response = get_openai_response(messages, model)
    return "".join(chunk.choices[0].delta.content for chunk in response if chunk.choices[0].delta.content)

def determine_sales_stage(text: str, current_stage: str = None):
    """Determine the sales stage based on Brian Tracy's 7-stage process"""
    system_prompt = """Analyze the following sales interaction and determine the current stage in Brian Tracy's 7-stage sales process:
    1. Prospecting
    2. First Contact
    3. Needs Analysis
    4. Presenting Solution
    5. Handling Objections
    6. Closing
    7. Follow-up and Referrals
    
    Current stage (if known): {current_stage}
    
    Format your response as:
    Sales Stage Analysis:
    - Current Stage: [stage number and name]
    - Progress: [whether moving forward, backward, or maintaining]
    - Key Indicators: [specific points that indicate this stage]
    """
    
    messages = [
        {"role": "system", "content": system_prompt.format(current_stage=current_stage)},
        {"role": "user", "content": text}
    ]
    
    response = get_openai_response(messages, model)
    return "".join(chunk.choices[0].delta.content for chunk in response if chunk.choices[0].delta.content)

def suggest_next_action(text: str, spin_analysis: str, sales_stage: str):
    """Suggest next action based on interaction context"""
    system_prompt = """Based on the following information, suggest the next best action:
    Interaction: {text}
    SPIN Analysis: {spin_analysis}
    Sales Stage: {sales_stage}
    
    Format your response as:
    Suggested Next Action:
    - Primary Action: [specific action to take]
    - Supporting Tasks: [list of supporting tasks]
    - Timeline: [suggested timeline]
    """
    
    messages = [
        {"role": "system", "content": system_prompt.format(
            text=text,
            spin_analysis=spin_analysis,
            sales_stage=sales_stage
        )},
        {"role": "user", "content": "What should be the next action?"}
    ]
    
    response = get_openai_response(messages, model)
    return "".join(chunk.choices[0].delta.content for chunk in response if chunk.choices[0].delta.content)

def analyze_customer_update(update_text: str, customer_name: str):
    """Analyze customer update with AI reasoning"""
    system_prompt = """Analyze the following customer update and provide detailed reasoning and insights. Include:
    1. Key Developments: What are the main points of progress or change?
    2. SPIN Analysis: How does this update relate to the SPIN selling framework?
    3. Sales Stage: Where does this update place the customer in the sales process?
    4. Relationship Status: What is the current state of the business relationship?
    5. Strategic Implications: What does this mean for future opportunities?
    6. Next Steps: What should be the immediate and medium-term actions?

    Format your response as:
    Key Developments:
    [List main points]

    SPIN Analysis:
    - Situation: [Current context]
    - Problem: [Issues addressed]
    - Implication: [Impact of solutions]
    - Need-Payoff: [Benefits realized]

    Sales Stage Analysis:
    - Current Stage: [Stage in 7-step process]
    - Progress Indicators: [What shows advancement]
    - Next Stage Goals: [What to aim for]

    Relationship Status:
    [Current state of relationship]

    Strategic Implications:
    [What this means for future business]

    Recommended Next Steps:
    [Immediate and future actions]
    """
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Customer: {customer_name}\n\nUpdate: {update_text}"}
    ]
    
    response = get_openai_response(messages, model)
    return "".join(chunk.choices[0].delta.content for chunk in response if chunk.choices[0].delta.content)

def update_customer_interaction(customer_id: str, new_input: str, new_output: str):
    customer = supabase_client.table('customers').select("*").eq('customer_id', customer_id).single().execute()
    if customer.data:
        inps = customer.data.get('input_conversation', [])
        outs = customer.data.get('output_conversation', [])
        updated_inputs = inps + [new_input]
        updated_outputs = outs + [new_output]
        response = supabase_client.table('customers').update({
            'input_conversation': updated_inputs,
            'output_conversation': updated_outputs,
            'updated_at': datetime.datetime.now().isoformat()
        }).eq('customer_id', customer_id).execute()
        return response.data
    return None

def extract_file_content(file):
    """Extract content from different file types"""
    try:
        file_type = file.name.split('.')[-1].lower()
        
        if file_type == 'pdf':
            # Handle PDF files
            pdf_reader = PdfReader(file)
            content = ""
            for page in pdf_reader.pages:
                content += page.extract_text() + "\n"
            return content
            
        elif file_type == 'txt':
            # Handle text files
            return file.getvalue().decode("utf-8")
            
        elif file_type == 'docx':
            # Handle Word documents
            import docx
            doc = docx.Document(file)
            content = ""
            for paragraph in doc.paragraphs:
                content += paragraph.text + "\n"
            return content
            
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
            
    except Exception as e:
        raise Exception(f"Error extracting file content: {str(e)}")

def process_uploaded_file(file, customer_id: str):
    """Process uploaded file and store its content in customer conversation"""
    try:
        # Extract file content based on file type
        file_content = extract_file_content(file)
        
        # Create a summary of the file content
        summary_prompt = f"""Analyze the following document content for CRM purposes:
        {file_content}
        
        Format the analysis to include:
        1. Key points and main topics
        2. Important details and specifications
        3. Any specific requirements or needs mentioned
        4. Potential business opportunities
        5. Relevant product matches (RDP, SBR, HPMC)
        """
        
        messages = [
            {"role": "system", "content": "You are a document analysis assistant specialized in chemical trading. Analyze the content for CRM purposes, focusing on business opportunities and product matches."},
            {"role": "user", "content": summary_prompt}
        ]
        
        # Get AI summary
        summary = ""
        for chunk in get_openai_response(messages, model):
            if chunk.choices[0].delta.content:
                summary += chunk.choices[0].delta.content
        
        # Store in customer conversation
        update_customer_interaction(
            customer_id,
            f"Uploaded file: {file.name}\nContent: {file_content}",
            f"File Analysis:\n{summary}"
        )
        
        return True, "File processed and stored successfully!"
    except Exception as e:
        return False, f"Error processing file: {str(e)}"

def render_update_interaction_ui(user_id: str):
    """Render the Update Interaction window UI"""
    st.subheader("🔄 Update Customer Interaction")
    st.markdown("---")
    
    # Step 1: Customer Selection
    customers = get_all_customer_names()
    if not customers:
        st.warning("No customers found. Please create a customer first.")
        return
    
    st.subheader("👤 Select Customer")
    selected_customer = st.selectbox(
        "Select Customer",
        options=list(customers.keys()),
        format_func=lambda x: f"{x} ({customers[x]})",
        key="update_interaction_customer_select"
    )
    
    if not selected_customer:
        return
    
    st.markdown("---")
    
    # --- NEW: View All Interactions Table & Export ---
    st.subheader("📋 All Interactions Table")
    interactions = get_customer_interactions(customers[selected_customer])
    if interactions:
        df = pd.DataFrame(interactions)
        # Reorder columns for clarity
        cols = [c for c in ["created_at", "interaction_input", "llm_output_summary"] if c in df.columns]
        df = df[cols]
        df = df.rename(columns={
            "created_at": "Date",
            "interaction_input": "Input",
            "llm_output_summary": "AI Output"
        })
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Export Interactions to CSV",
            data=csv,
            file_name=f"{selected_customer}_interactions.csv",
            mime='text/csv',
            key="export_interactions_csv"
        )
    else:
        st.info("No interactions found for this customer.")
    st.markdown("---")
    
    # Step 2: File Upload Section
    st.subheader("📄 Upload Document")
    uploaded_file = st.file_uploader(
        "Upload a document (PDF, TXT, DOCX)",
        type=['pdf', 'txt', 'docx'],
        key="customer_file_upload"
    )
    
    if uploaded_file:
        if st.button("Process Document"):
            success, message = process_uploaded_file(uploaded_file, customers[selected_customer])
            if success:
                st.success(message)
            else:
                st.error(message)
    
    st.markdown("---")
    
    # Step 3: Contextual View
    st.subheader("🗂️ View Mode")
    view_mode = st.radio(
        "View Mode",
        ["Full Chat Thread", "Summarized Insight"],
        horizontal=True,
        key="update_interaction_view_mode"
    )
    
    # Fetch customer interactions
    interactions = get_customer_interactions(customers[selected_customer])
    
    if view_mode == "Full Chat Thread":
        st.subheader("💬 Interaction History")
        for interaction in interactions:
            with st.expander(f"Interaction on {interaction['created_at']}"):
                st.write("Input:", interaction['interaction_input'])
                st.write("Analysis:", interaction['llm_output_summary'])
    else:
        # Generate summary
        if interactions:
            summary_prompt = f"Summarize the following customer interactions for {selected_customer}:\n"
            for interaction in interactions[:5]:  # Last 5 interactions
                summary_prompt += f"\n{interaction['created_at']}: {interaction['interaction_input']}\n"
            
            messages = [
                {"role": "system", "content": "Summarize the customer interactions concisely, highlighting key points and progress."},
                {"role": "user", "content": summary_prompt}
            ]
            
            with st.spinner("Generating summary..."):
                summary = "".join(chunk.choices[0].delta.content for chunk in get_openai_response(messages, model) if chunk.choices[0].delta.content)
                st.write(summary)
    
    st.markdown("---")
    
    # Step 4: New Interaction Input
    st.markdown("### ✍️ New Interaction")
    st.caption("Add a new customer interaction and analyze it with AI.")
    new_interaction = st.text_area("📝 Enter new interaction details")
    
    if st.button("💡 Analyze with AI") and new_interaction:
        # Step 5: AI Analysis
        spin_analysis = analyze_spin_elements(new_interaction)
        sales_stage = determine_sales_stage(new_interaction)
        next_action = suggest_next_action(new_interaction, spin_analysis, sales_stage)
        
        st.session_state['spin_analysis'] = spin_analysis
        st.session_state['sales_stage'] = sales_stage
        st.session_state['next_action'] = next_action
        st.session_state['new_interaction'] = new_interaction
    
    # Display analysis if available
    if all(k in st.session_state for k in ['spin_analysis', 'sales_stage', 'next_action', 'new_interaction']):
        st.subheader("🤖 AI Analysis")
        col1, col2 = st.columns(2)
        with col1:
            st.write("SPIN Analysis:")
            st.write(st.session_state['spin_analysis'])
        with col2:
            st.write("Sales Stage:")
            st.write(st.session_state['sales_stage'])
        st.write("Suggested Next Action:")
        st.write(st.session_state['next_action'])
        
        if st.button("💾 Save Interaction"):
            llm_output = f"SPIN Analysis:\n{st.session_state['spin_analysis']}\n\nSales Stage:\n{st.session_state['sales_stage']}\n\nNext Action:\n{st.session_state['next_action']}"
            result = update_customer_interaction(customers[selected_customer], st.session_state['new_interaction'], llm_output)
            if result:
                st.success("Interaction saved successfully!")
                # Clear session state for next entry
                for k in ['spin_analysis', 'sales_stage', 'next_action', 'new_interaction']:
                    if k in st.session_state:
                        del st.session_state[k]
            else:
                st.error("Failed to save interaction")

def get_all_customer_data():
    """Fetch all customer data with their interactions"""
    try:
        response = supabase_client.table('customers').select('*').execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error fetching customer data: {str(e)}")
        return []

def analyze_crm_data(query: str, user_id: str):
    """Analyze CRM data based on natural language query (PRODUCTION VERSION)"""
    customers = get_all_customer_data()
    
    context = "Customer Data:\n"
    for customer in customers:
        context += f"\nCustomer: {customer['customer_name']}\n"
        context += f"Display ID: {customer.get('display_id', 'N/A')}\n"
        context += f"Created: {customer.get('created_at', 'N/A')}\n"
        context += f"Last Updated: {customer.get('updated_at', 'N/A')}\n"
        if customer.get('input_conversation'):
            context += "\nRecent Interactions:\n"
            for i, (input_msg, output_msg) in enumerate(zip(
                customer['input_conversation'][-3:],
                customer['output_conversation'][-3:]
            )):
                context += f"\nInteraction {i+1}:\n"
                context += f"Input: {input_msg}\n"
                context += f"Output: {output_msg}\n"
    
    # Filter out empty/irrelevant memories
    relevant_memories = get_cached_memories(query, user_id)
    memories_str = "\n".join(
        f"- {entry['memory']}" for entry in relevant_memories["results"]
        if entry['memory'] and entry['memory'].strip() and entry['memory'].strip().lower() != "not specified"
    )
    
    system_prompt = """You are a CRM data analyst specialized in chemical trading. Analyze the provided data and answer the user's query.
    Use the following guidelines:
    1. Be concise but comprehensive
    2. Structure your response in a clear, readable format
    3. Include relevant numbers and statistics when available
    4. Highlight important trends or patterns
    5. Suggest actionable insights when relevant
    
    Available Data:
    {context}
    
    Relevant Memories:
    {memories}
    
    Format your response as:
    Analysis:
    [Your analysis here]
    
    Key Findings:
    - [Finding 1]
    - [Finding 2]
    ...
    
    Recommendations:
    - [Recommendation 1]
    - [Recommendation 2]
    ...
    """
    
    messages = [
        {"role": "system", "content": system_prompt.format(context=context, memories=memories_str)},
        {"role": "user", "content": query}
    ]
    try:
        response = get_openai_response(messages, model)
        result = "".join(chunk.choices[0].delta.content for chunk in response if chunk.choices[0].delta.content)
        return result
    except Exception as e:
        st.error(f"OpenAI error: {e}")
        return f"OpenAI error: {e}"

def save_analysis_query(query: str, response: str, user_id: str):
    """Save the analysis query and response to the deals table"""
    try:
        data = {
            "input_log": query,
            "ai_response_log": response,
            "created_by": user_id,
            "created_at": datetime.datetime.now().isoformat()
        }
        response = supabase_client.table('deals').insert(data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        st.error(f"Error saving analysis query: {str(e)}")
        return None

def get_saved_queries(user_id: str):
    """Fetch saved analysis queries for the user"""
    try:
        response = supabase_client.table('deals').select('*').eq('created_by', user_id).order('created_at', desc=True).execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error fetching saved queries: {str(e)}")
        return []

def render_analysis_ui(user_id: str):
    """Render the Analysis & Reporting window UI"""
    st.title("📊 CRM Analysis & Reporting")
    st.write("Ask any question about your CRM data and get instant insights.")
    st.markdown("---")
    # Toggle for saved queries
    show_saved = st.checkbox("Show Saved Queries")
    if show_saved:
        saved_queries = get_saved_queries(user_id)
        if saved_queries:
            st.subheader("💾 Saved Queries")
            for query in saved_queries:
                with st.expander(f"Query from {query['created_at']}"):
                    st.write("Query:", query['input_log'])
                    st.write("Response:", query['ai_response_log'])
        else:
            st.info("No saved queries found.")
    st.markdown("---")
    # Main query interface using a form
    st.subheader("📝 New Analysis")
    st.caption("Type your question about CRM data and click the button to analyze with AI.")
    with st.form("analysis_form"):
        query = st.text_area("Enter your analysis query", height=100, key="analysis_query")
        submitted = st.form_submit_button("💡 Analyze with AI")
        if submitted and query:
            with st.spinner("Analyzing data..."):
                analysis = analyze_crm_data(query, user_id)
                st.session_state['last_analysis_query'] = query
                st.session_state['last_analysis_result'] = analysis
    # Show results if available (but remove Save Analysis button)
    if st.session_state.get('last_analysis_result'):
        st.write("Analysis Results:")
        st.write(st.session_state['last_analysis_result'])
    st.markdown("---")

# --- Chatbot UI for memory-powered chat ---
def render_chatbot_ui(user_id):
    st.header("🤖 Chat with Memory-Powered AI")
    st.write("Your conversation history and preferences are remembered across sessions.")
    st.markdown("---")
    # Memory Management
    st.subheader("🧹 Memory Management")
    if st.button("🗑️ Clear All Memories", key="tab_clear_memories"):
        memory.clear(user_id=user_id)
        st.success("All memories cleared!")
        st.session_state.messages = []
        st.rerun()
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    # Place chat input directly after messages
    user_input = st.chat_input("Type your message here...")
    if user_input:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_input})
        # Display user message
        with st.chat_message("user"):
            st.write(user_input)
        # Get AI response with streaming
        with st.chat_message("assistant"):
            ai_response = chat_with_memories(user_input, user_id)
        # Add AI response to chat history
        st.session_state.messages.append({"role": "assistant", "content": ai_response})

# --- Customer creation UI for dashboard tab ---
def render_customer_creation_ui_tab(user_id):
    st.subheader("Create New Customer")
    new_customer_name = st.text_input("Enter Customer Name", key="tab_new_customer_name")
    if new_customer_name:
        if 'customer_creation_state' not in st.session_state:
            st.session_state.customer_creation_state = {
                'step': 1,
                'customer_name': new_customer_name,
                'profile': None,
                'confirmed': False
            }
        if st.session_state.customer_creation_state is not None:
            create_new_customer(
                st.session_state.customer_creation_state['customer_name'],
                user_id
            )
        else:
            st.session_state.customer_creation_state = {
                'step': 1,
                'customer_name': new_customer_name,
                'profile': None,
                'confirmed': False
            }
            create_new_customer(new_customer_name, user_id)

# --- Customer search and update interaction for dashboard tab ---
def render_choose_existing_ui(user_id):
    st.subheader("Customer Search")
    search_query = st.text_input("Search customers", key="tab_customer_search")
    customers = search_customers(search_query) if search_query else get_all_customer_names()
    if customers:
        st.write("Found customers:")
        for customer in (customers if isinstance(customers, list) else customers.keys()):
            name = customer['customer_name'] if isinstance(customer, dict) else customer
            with st.expander(name):
                if isinstance(customer, dict):
                    st.write("Created:", customer.get('created_at', 'N/A'))
                    st.write("Last updated:", customer.get('updated_at', 'N/A'))
                    if customer.get('input_conversation'):
                        st.write("Recent conversations:")
                        for i, (input_msg, output_msg) in enumerate(zip(customer['input_conversation'][-3:], customer['output_conversation'][-3:]), 1):
                            st.write(f"Conversation {i}:")
                            st.write("Input:", input_msg)
                            st.write("Output:", output_msg)
    else:
        st.write("No customers found.")
    st.subheader("Customer Management")
    render_update_interaction_ui(user_id)

# --- Main CRM Dashboard with Tabs ---
def main_crm_dashboard(user_id):
    st.title("CRM Dashboard")
    tabs = st.tabs(["Create Customer", "Choose Existing", "Analysis & Chat", "Chatbot"])

    with tabs[0]:
        render_customer_creation_ui_tab(user_id)

    with tabs[1]:
        render_choose_existing_ui(user_id)

    with tabs[2]:
        render_analysis_ui(user_id)

    with tabs[3]:
        render_chatbot_ui(user_id)

# --- Main Streamlit logic below ---
if st.session_state.get("logout_requested", False):
    st.session_state.logout_requested = False
    st.rerun()

# Sidebar: Only login/logout/profile
with st.sidebar:
    st.sidebar.title("🧠 AI Powered CRM Chat")
    if not st.session_state.authenticated:
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        with tab1:
            st.subheader("Login")
            login_email = st.text_input("Email", key="sidebar_login_email")
            login_password = st.text_input("Password", type="password", key="sidebar_login_password")
            login_button = st.button("Login", key="sidebar_login_button")
            if login_button:
                if login_email and login_password:
                    sign_in(login_email, login_password)
                else:
                    st.warning("Please enter both email and password.")
        with tab2:
            st.subheader("Sign Up")
            signup_email = st.text_input("Email", key="sidebar_signup_email")
            signup_password = st.text_input("Password", type="password", key="sidebar_signup_password")
            signup_name = st.text_input("Full Name", key="sidebar_signup_name")
            signup_button = st.button("Sign Up", key="sidebar_signup_button")
            if signup_button:
                if signup_email and signup_password and signup_name:
                    response = sign_up(signup_email, signup_password, signup_name)
                    if response and response.user:
                        st.success("Sign up successful! Please check your email to confirm your account.")
                    else:
                        st.error("Sign up failed. Please try again.")
                else:
                    st.warning("Please fill in all fields.")
    else:
        user = st.session_state.user
        if user:
            st.success(f"Logged in as: {user.email}")
            st.button("Logout", on_click=sign_out, key="sidebar_logout_button")
            st.subheader("Your Profile")
            st.write(f"User ID: {user.id}")

# Main tabbed dashboard for authenticated users
if st.session_state.authenticated and st.session_state.user:
    user_id = st.session_state.user.id
    main_crm_dashboard(user_id)
else:
    st.title("Welcome to LeanChems Chat Assistant")
    st.write("Please login or sign up to start chatting with the memory-powered AI assistant.")
   
    # Feature highlights
    st.subheader("Features")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 🧠 Long-term Memory")
        st.write("The AI remembers your past conversations and preferences.")
    
    with col2:
        st.markdown("### 🔒 Secure Authentication")
        st.write("Your data is protected with Supabase authentication.")
    
    with col3:
        st.markdown("### 💬 Personalized Responses")
        st.write("Get responses tailored to your history and context.")

def upload_pdf_to_documents(pdf_path: str, user_id: str = "default_user"):
    # 1. Read PDF content
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    
    # 2. Get embedding for the content (using OpenAI)
    response = openai.Embedding.create(
        input=text,
        model="text-embedding-3-small"
    )
    embedding = response['data'][0]['embedding']
    
    # 3. Store in Supabase
    data = {
        "content": text,
        "embedding": embedding,
        "metadata": {
            "filename": Path(pdf_path).name,
            "user_id": user_id,
            "source": "product_pdf"
        }
    }
    supabase_client.table("documents").insert(data).execute()
    print(f"Uploaded {pdf_path} to documents table.")

# Update the main execution block to use the new sidebar
if __name__ == "__main__":
    # This section won't run in Streamlit
    pass