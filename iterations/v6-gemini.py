import os
import streamlit as st
from streamlit_lottie import st_lottie
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
import json
import requests
import urllib.parse
from serpapi import GoogleSearch  # Keep SerpAPI for combined results
from bs4 import BeautifulSoup
import numpy as np

# --- Custom CSS for beautiful UI ---
st.markdown("""
<style>
/* Global Styles */
body {
    background-color: #f5f7fa; /* Light background */
    font-family: 'Segoe UI', sans-serif;
}

/* Adjust main content area padding for spacious layout */
.main .block-container {
    padding-top: 40px;
    padding-right: 60px;
    padding-left: 60px;
    padding-bottom: 40px;
}

/* Sidebar styling */
.css-1d391kg, .css-1v0mbdj { /* Adjust these class names if needed based on Streamlit version */
    background-color: #ffffff;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08); /* Slightly stronger shadow */
    margin-bottom: 20px;
}

/* Input fields */
input {
    border: 1px solid #e0e0e0; /* Lighter border */
    border-radius: 10px;
    padding: 12px;
    font-size: 16px;
    width: 100%;
    margin-bottom: 15px; /* Increased space */
    background-color: #f9f9f9; /* Slightly different input background */
}

/* Hide 'Press Enter to apply' text */
.stTextInput > div > div > input + div {
    display: none;
}

/* Buttons */
button[kind="primary"] {
    background-color: #1e73c4; /* A shade of blue */
    color: white;
    border: none;
    border-radius: 10px;
    padding: 12px 20px;
    font-weight: bold;
    margin-top: 15px; /* Increased space */
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    transition: background-color 0.3s ease;
}

button[kind="primary"]:hover {
    background-color: #155b9e; /* Darker shade on hover */
}

/* Header styles */
h1, h2, h3, h4 {
    color: #333; /* Darker text for headers */
    font-weight: 700;
    margin-bottom: 15px;
    padding-top: 5px; /* Add some padding above headers */
}

/* Features layout (Cards) */
.feature-box {
    background-color: #ffffff;
    padding: 25px; /* Increased padding inside cards */
    border-radius: 16px; /* Rounded corners */
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1); /* More prominent shadow */
    margin-top: 15px; /* Increased margin */
    margin-bottom: 15px; /* Increased margin */
    text-align: left;
    height: 100%;
    transition: transform 0.3s ease, box-shadow 0.3s ease; /* Smooth hover effect */
}

.feature-box:hover {
    transform: translateY(-5px); /* Lift effect on hover */
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15); /* Enhanced shadow on hover */
}

.stMarkdown > div > p {
    margin-bottom: 1rem; /* Standard space below paragraphs */
    color: #555; /* Slightly lighter text for paragraph */
}

/* Adjust spacing around columns */
.st-emotion-l8z9g2 > div { /* This targets the div inside the columns, adjust class name if needed */
    margin-bottom: 30px; /* Space between rows of columns */
    padding: 0 10px; /* Add horizontal padding between columns */
}

/* Center the main content block */
.css-18e3gdp.e8zbici2 {
    max-width: 1200px; /* Set a max width for content */
    margin: auto; /* Center the block */
}

/* Class for bold text */
.bold-text {
    font-weight: bold;
}

/* Dark mode adjustments */
@media (prefers-color-scheme: dark) {
    body {
        background-color: #1e1e1e; /* Darker background */
    }
    .stApp {
        background-color: #1e1e1e;
    }
    .main .block-container {
        padding-top: 40px;
        padding-right: 60px;
        padding-left: 60px;
        padding-bottom: 40px;
    }
    .css-1d391kg, .css-1v0mbdj {
        background-color: #2c2c2c;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
    }
    input {
        border: 1px solid #444;
        background-color: #333;
        color: #f0f0f0;
    }
    button[kind="primary"] {
        background-color: #1a4d7d; /* Dark mode blue */
    }
    button[kind="primary"]:hover {
        background-color: #12395a; /* Darker shade on hover */
    }
    h1, h2, h3, h4 {
        color: #f0f0f0;
    }
    .feature-box {
        background-color: #2c2c2c;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
    }
    .feature-box:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.45);
    }
     .stMarkdown > div > p {
        color: #cccccc;
    }
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

# --- Gemini integration (minimal, no new requirements) ---
LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'gemini').lower()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', None)
GEMINI_CHAT_MODEL = os.getenv('GEMINI_CHAT_MODEL', 'gemini-2.5-flash')
GEMINI_EMBED_MODEL = os.getenv('GEMINI_EMBED_MODEL', 'text-embedding-004')
GEMINI_CHAT_URL = f'https://generativelanguage.googleapis.com/v1/models/{GEMINI_CHAT_MODEL}:generateContent'
GEMINI_EMBED_URL = f'https://generativelanguage.googleapis.com/v1/models/{GEMINI_EMBED_MODEL}:embedContent'

def gemini_chat(messages):
    """Call Gemini chat API with OpenAI-style messages."""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not set in environment.")
    # Gemini expects a different message format
    # We'll concatenate all messages into a single prompt
    prompt = "\n".join([m['content'] for m in messages])
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    headers = {"Content-Type": "application/json"}
    params = {"key": GEMINI_API_KEY}
    response = requests.post(GEMINI_CHAT_URL, params=params, headers=headers, data=json.dumps(payload))
    response.raise_for_status()
    candidates = response.json().get('candidates', [])
    if candidates:
        return candidates[0]['content']['parts'][0]['text']
    return "[No response from Gemini]"

def gemini_embed(text):
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not set in environment.")
    try:
        payload = {
            "content": {
                "parts": [
                    {"text": text}
                ]
            }
        }
        headers = {"Content-Type": "application/json"}
        params = {"key": GEMINI_API_KEY}
        response = requests.post(
            GEMINI_EMBED_URL, 
            params=params, 
            headers=headers, 
            data=json.dumps(payload),
            timeout=30
        )
        if response.status_code != 200:
            st.error(f"Gemini API Error: {response.status_code} - {response.text}")
            response.raise_for_status()
        response_data = response.json()
        print("DEBUG: Gemini embed API raw response:", response_data)  # <--- Debug print
        if 'embedding' in response_data:
            embedding = response_data['embedding'].get('values', None)
        elif 'data' in response_data:
            embedding = response_data['data'][0].get('embedding', None)
        else:
            st.error(f"Unexpected response format: {response_data}")
            raise ValueError("No embedding found in response")
        if not embedding:
            raise ValueError("No embedding returned from Gemini API")
        return embedding
    except requests.exceptions.ConnectionError as e:
        st.error(f"Connection error to Gemini API: {str(e)}")
        st.warning("Please check your internet connection and Gemini API key.")
        raise
    except requests.exceptions.Timeout as e:
        st.error(f"Timeout error to Gemini API: {str(e)}")
        st.warning("The request to Gemini API timed out. Please try again.")
        raise
    except requests.exceptions.RequestException as e:
        st.error(f"Request error to Gemini API: {str(e)}")
        st.warning("There was an error communicating with Gemini API.")
        raise
    except Exception as e:
        st.error(f"Unexpected error in gemini_embed: {str(e)}")
        raise

# Cache OpenAI client and Memory instance
@st.cache_resource
def get_openai_client():
    return OpenAI()

@st.cache_resource
def get_memory():
    config = {
        "llm": {
            "provider": LLM_PROVIDER,
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

def search_web_for_company(company_name: str):
    """Search the web for company information using both Google PSE, SerpAPI, and force-include Wikipedia and official site."""
    try:
        combined_results = []
        # 1. Google PSE Search
        pse_api_key = os.getenv("GOOGLE_PSE_API_KEY")
        pse_cx = os.getenv("GOOGLE_PSE_CX")
        if pse_api_key and pse_cx:
            query = f"{company_name} company information business profile"
            encoded_query = urllib.parse.quote(query)
            url = f"https://www.googleapis.com/customsearch/v1?key={pse_api_key}&cx={pse_cx}&q={encoded_query}&num=5"
            response = requests.get(url)
            if response.status_code == 200:
                results = response.json()
                if "items" in results:
                    for item in results["items"]:
                        result = {
                            'title': item.get('title', ''),
                            'snippet': item.get('snippet', ''),
                            'link': item.get('link', ''),
                            'source': 'Google PSE'
                        }
                        if 'pagemap' in item and 'metatags' in item['pagemap']:
                            metatags = item['pagemap']['metatags'][0]
                            if 'og:description' in metatags:
                                result['description'] = metatags['og:description']
                        combined_results.append(result)
        # 2. SerpAPI Search
        serpapi_key = os.getenv("SERPAPI_API_KEY")
        if serpapi_key:
            params = {
                "engine": "google",
                "q": f"{company_name} company information business profile",
                "api_key": serpapi_key,
                "num": 5
            }
            search = GoogleSearch(params)
            results = search.get_dict()
            if "organic_results" in results:
                for result in results["organic_results"]:
                    combined_results.append({
                        'title': result.get('title', ''),
                        'snippet': result.get('snippet', ''),
                        'link': result.get('link', ''),
                        'source': 'SerpAPI'
                    })
        # 3. Force-include Wikipedia page
        wiki_url = f"https://en.wikipedia.org/wiki/{company_name.replace(' ', '_')}"
        wiki_resp = requests.get(wiki_url)
        if wiki_resp.status_code == 200:
            soup = BeautifulSoup(wiki_resp.text, 'html.parser')
            p = soup.find('p')
            snippet = p.text.strip() if p else ''
            combined_results.append({
                'title': f"Wikipedia: {company_name}",
                'snippet': snippet,
                'link': wiki_url,
                'source': 'Wikipedia'
            })
        # 4. Force-include official site if pattern matches
        for domain in [f"https://{company_name.replace(' ', '').lower()}.com", f"https://{company_name.replace(' ', '').capitalize()}.com"]:
            try:
                resp = requests.get(domain, timeout=3)
                if resp.status_code == 200:
                    combined_results.append({
                        'title': f"Official Site: {company_name}",
                        'snippet': f"Official website for {company_name}.",
                        'link': domain,
                        'source': 'Official Site'
                    })
                    break
            except Exception:
                continue
        # Remove duplicates based on URL
        unique_results = []
        seen_urls = set()
        for result in combined_results:
            if result['link'] not in seen_urls:
                seen_urls.add(result['link'])
                unique_results.append(result)
        # Format results
        web_context = ""
        for result in unique_results:
            web_context += f"\nTitle: {result['title']}\n"
            web_context += f"Snippet: {result['snippet']}\n"
            web_context += f"Link: {result['link']}\n"
            web_context += f"Source: {result['source']}\n"
            if 'description' in result:
                web_context += f"Description: {result['description']}\n"
            web_context += "---\n"
        return web_context
    except Exception as e:
        st.warning(f"Web search failed: {str(e)}")
        return ""

def search_linkedin_profiles_ethiopia(company_name: str):
    """Search for LinkedIn profiles in Ethiopia using both Google PSE and SerpAPI"""
    try:
        all_profiles = []
        
        # Broader search query as a fallback
        search_queries = [
            f'site:linkedin.com/in/ "{company_name}" Ethiopia (CEO OR "Managing Director" OR "General Manager")',
            f'site:linkedin.com/in/ "{company_name}" Ethiopia (Operations OR "Plant Manager" OR Production)',
            f'site:linkedin.com/in/ "{company_name}" Ethiopia (Procurement OR "Supply Chain" OR Purchasing)',
            f'site:linkedin.com/in/ "{company_name}" Ethiopia (Technical OR R&D OR Quality)',
            f'site:linkedin.com/in/ "{company_name}" Ethiopia (Sales OR "Business Development")',
            f'site:linkedin.com/in/ "{company_name}" Ethiopia' # General search
        ]
        
        # Check for API keys and show warnings
        pse_api_key = os.getenv("GOOGLE_PSE_API_KEY")
        pse_cx = os.getenv("GOOGLE_PSE_CX")
        serpapi_key = os.getenv("SERPAPI_API_KEY")

        if not pse_api_key or not pse_cx:
            st.warning("Google Custom Search API keys (GOOGLE_PSE_API_KEY, GOOGLE_PSE_CX) are not set. LinkedIn search may be incomplete.")
        
        if not serpapi_key:
            st.warning("SerpAPI key (SERPAPI_API_KEY) is not set. LinkedIn search may be incomplete.")

        # 1. Google PSE Search
        if pse_api_key and pse_cx:
            for query in search_queries:
                encoded_query = urllib.parse.quote(query)
                url = f"https://www.googleapis.com/customsearch/v1?key={pse_api_key}&cx={pse_cx}&q={encoded_query}&num=5&gl=et&hl=en"
                
                response = requests.get(url)
                if response.status_code == 200:
                    results = response.json()
                    if "items" in results:
                        for item in results["items"]:
                            title = item.get('title', '')
                            snippet = item.get('snippet', '')
                            link = item.get('link', '')
                            
                            name = title.split('|')[0].strip()
                            position = snippet.split('·')[0].strip() if '·' in snippet else 'Not specified'
                            
                            all_profiles.append({
                                'name': name,
                                'position': position,
                                'link': link,
                                'snippet': snippet,
                                'source': 'Google PSE'
                            })
        
        # 2. SerpAPI Search
        if serpapi_key:
            for query in search_queries:
                params = {
                    "engine": "google",
                    "q": query,
                    "api_key": serpapi_key,
                    "num": 5,
                    "gl": "et",
                    "hl": "en",
                    "filter": 0
                }
                
                search = GoogleSearch(params)
                results = search.get_dict()
                
                if "organic_results" in results:
                    for result in results["organic_results"]:
                        title = result.get('title', '')
                        snippet = result.get('snippet', '')
                        link = result.get('link', '')
                        
                        name = title.split('|')[0].strip()
                        position = snippet.split('·')[0].strip() if '·' in snippet else 'Not specified'
                        
                        all_profiles.append({
                            'name': name,
                            'position': position,
                            'link': link,
                            'snippet': snippet,
                            'source': 'SerpAPI'
                        })
        
        # Remove duplicates based on LinkedIn URL and format results
        unique_profiles = []
        seen_links = set()
        for profile in all_profiles:
            if profile['link'] and profile['link'] not in seen_links:
                seen_links.add(profile['link'])
                unique_profiles.append(profile)
        
        linkedin_context = "\nLinkedIn Profiles in Ethiopia:\n"
        if unique_profiles:
            for profile in unique_profiles[:10]:  # Limit to top 10 profiles
                linkedin_context += f"\n- Name: {profile['name']}\n"
                linkedin_context += f"  Position: {profile['position']}\n"
                linkedin_context += f"  Profile: {profile['link']}\n"
                linkedin_context += f"  Source: {profile['source']}\n"
                if profile['snippet']:
                    context = profile['snippet'].split('·')[-1].strip()
                    if context:
                        linkedin_context += f"  Context: {context}\n"
                linkedin_context += "---\n"
        else:
            linkedin_context += "\nNo relevant LinkedIn profiles found. This could be due to missing API keys, search limitations, or no public profiles for this company.\n"
            
        return linkedin_context
    except Exception as e:
        return f"\nLinkedIn Profiles in Ethiopia:\nSearch Error: {str(e)}\n"

def generate_customer_profile(customer_name: str, user_id: str):
    """Generate a customer profile using AI, existing conversations, and web search"""
    # Search relevant documents and memories
    relevant_docs = search_documents(customer_name, user_id)
    relevant_memories = get_cached_memories(customer_name, user_id)
    
    # Search web for company information
    web_context = search_web_for_company(customer_name)
    
    # Search for LinkedIn profiles in Ethiopia
    linkedin_context = search_linkedin_profiles_ethiopia(customer_name)
    
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
    
    if web_context:
        context += "\nWeb Search Results:\n"
        context += web_context
    
    if linkedin_context:
        context += "\nLinkedIn Information:\n"
        context += linkedin_context
    
    # Create the enhanced prompt for profile generation
    system_prompt = """You are an Industry-Intel Research Assistant and B2B Chemical-Supply Strategist for LeanChem. Your mission is to perform a deep-dive analysis of {Target Company} and all of its construction-relevant subsidiaries operating in Ethiopia, to:

Identify all business units manufacturing products for the construction sector: cement, dry-mix mortar, concrete admixtures, and paint/coatings.

Evaluate how LeanChem's chemical portfolio aligns with each unit's product and operational profile.

Recommend precise engagement strategies tailored by subsector and supply pain points.

Provide verified decision-maker contacts for B2B outreach.

If the company is a conglomerate, list all major business units and subsidiaries relevant to construction, chemicals, and manufacturing, even if not all are found in the immediate context.

🧾 Primary Deliverables
Company Overview & Recent News

≤500-character summary of {Target Company}'s core business, size, and activity in Ethiopia.

Highlight recent expansions, investments, or new product lines in cement, dry-mix, admixtures, or coatings, using GPT-4o/web-search insights or official sources.

Include citations [1], [2], … from reliable sources.

Construction-Sector Manufacturing Overview

A structured table listing all business units in Ethiopia manufacturing construction-related materials.

Table Columns:

Business Unit

Construction Products

Location (City, Country)

Scale Metric (e.g., capacity, project size)

Source

Strategic-Fit Matrix

For each subsidiary, assess alignment to LeanChem's offerings across 4 subsectors:

Cement

Dry-Mix

Admixtures

Paint & Coatings

Score each axis using:

0 = No Fit

1 = Low Fit

2 = Moderate Fit

3 = High Fit

Base scores on:

Volume opportunity vs LeanChem capacity

LeanChem's ability to solve supply or technical pain points (e.g., forex, lead time, performance)

Competitive pressure and likelihood of switching

Strategic Insights & Action Plan

Max 200-word narrative outlining 3–5 high-leverage opportunities and pain-point matches.

Segment by subsector (Cement, Dry-Mix, Admixtures, Paints) and recommend clear engagement actions such as:

Outreach channel (email, event, enabler)

Sample trial with product match

Proposal for supply contract, JIT, or SEZ warehousing

Technical advisory to improve performance or reduce cost

Key Contacts for Engagement

List up to 10 decision-makers or influencers in operations, procurement, or technical roles.

Columns:

Name

Position

LinkedIn Profile (full clickable URL)

Source

Extract only real individuals verified via LinkedIn or company websites.

🧩 Research Inputs
LeanChem Offerings

Dry-Mix/Plaster: RDP, HPMC, Starch Ether, Fiber, Zinc Stearate, Plasticizer, Defoamer, SBR, Acrylic Waterproofing, White Cement, Iron Oxide, Titanium Dioxide

Concrete Admixtures: PCE, SNF, Lignosulphonate, Sodium Gluconate, Penetrol-type waterproofing

Paint/Coatings: Styrene-Acrylic Binders, Pure Acrylics, VAE, HEC, White Cement, Iron Oxide, Titanium Dioxide

Cement Grinding: Cement grinding aids

🔍 Research Tools & Constraints
Source from:

{Target Company} official website and group/subsidiary pages

Annual reports and press releases

LinkedIn (for verified role-based contacts)

News outlets, trade journals, government registries

Use structured search queries like:

"{Target Company} cement plant Ethiopia"

"{Target Company} paint coatings manufacturer Ethiopia"

"{Target Company} dry mix mortar factory site"

"{Target Company} procurement manager LinkedIn"

Use numbered citations [1], [2], etc.

Provide honest results—if a construction vertical is not present, list as "N/A" or "0" in the fit matrix.
..."""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Generate a profile for: {customer_name}\n\nContext:{context}"}
    ]
    
    # Get response and convert to string
    response = get_llm_response(messages, model)
    profile_text = ""
    for chunk in response:
        if chunk.choices[0].delta.content:
            profile_text += chunk.choices[0].delta.content
    return profile_text

def ensure_vector(embedding):
    # If it's a string, try to parse as JSON
    if isinstance(embedding, str):
        try:
            embedding = json.loads(embedding)
        except Exception:
            raise ValueError("Embedding string could not be parsed as JSON array.")
    # If it's a list of numbers (possibly as strings), convert all to float
    if isinstance(embedding, list):
        # If it's a list of lists (shouldn't happen for a single embedding), flatten
        if len(embedding) > 0 and isinstance(embedding[0], list):
            embedding = embedding[0]
        return [float(x) for x in embedding]
    # If it's a single float or int, raise error
    if isinstance(embedding, (float, int)):
        raise ValueError("Embedding is a single number, expected a list of floats.")
    raise ValueError(f"Unexpected embedding type: {type(embedding)}")

def create_new_customer(customer_name: str, user_id: str):
    """Handle the complete customer creation workflow"""
    # Ensure we have a valid state
    if 'customer_creation_state' not in st.session_state or st.session_state.customer_creation_state is None:
        st.session_state.customer_creation_state = {
            'step': 1,
            'customer_name': customer_name,
            'profile': None,
            'confirmed': False
        }

    state = st.session_state.customer_creation_state
    
    # Step 1: Check for similar customers
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
        profile_input = f"Create profile for {customer_name}"
        profile_output = str(state['profile'])
        # --- Generate embedding for the profile input ---
        embedding = gemini_embed(profile_input)
        embedding = ensure_vector(embedding)
        interaction_embeddings = [embedding]  # Always a list of lists
        # Remove debug print
        # print("DEBUG: embedding to be saved:", embedding, type(embedding))
        interaction_json = {
            "input": profile_input,
            "output": profile_output,
            "timestamp": datetime.datetime.now().isoformat(),
            "user_id": user_id
        }
        data = {
            "customer_id": customer_id,
            "display_id": display_id,
            "customer_name": customer_name,
            "input_conversation": [profile_input],
            "output_conversation": [profile_output],
            "interaction_metadata": [interaction_json],  # list of dicts (JSON)
            "interaction_embeddings": interaction_embeddings  # list of lists of floats (vector per interaction)
        }
        try:
            response = supabase_client.table('customers').insert(data).execute()
            if response.data:
                # Clear the creation state first
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
def get_llm_response(messages, model):
    try:
        if LLM_PROVIDER == 'openai':
            return openai_client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True
            )
        elif LLM_PROVIDER == 'gemini':
            # Gemini does not support streaming, so yield a single chunk
            class DummyChunk:
                def __init__(self, text):
                    self.choices = [type('Delta', (), {'delta': type('DeltaContent', (), {'content': text})()})()]
            text = gemini_chat(messages)
            yield DummyChunk(text)
        else:
            raise ValueError(f"Unknown LLM_PROVIDER: {LLM_PROVIDER}")
    except Exception as e:
        st.error(f"Error getting AI response: {str(e)}")
        raise

def search_documents(query: str, user_id: str, limit: int = 3):
    try:
        @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
        def get_embedding():
            return gemini_embed(query)
        query_embedding = get_embedding()
        @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
        def search_supabase():
            try:
                response = supabase_client.rpc(
                    'match_conversation',
                    {
                        'query_embedding': query_embedding,
                        'match_count': limit,
                        'match_threshold': 0.5,
                        'filter': {}
                    }
                ).execute()
                return response
            except Exception as rpc_error:
                st.error(f"Supabase RPC error details: {str(rpc_error)}")
                if hasattr(rpc_error, 'message'):
                    st.error(f"RPC Error message: {rpc_error.message}")
                if hasattr(rpc_error, 'details'):
                    st.error(f"RPC Error details: {rpc_error.details}")
                raise
        response = search_supabase()
        if response.data:
            return response.data
        else:
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

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def get_all_customer_names():
    response = supabase_client.table('customers').select('customer_name,customer_id').execute()
    if response.data:
        return {c['customer_name']: c['customer_id'] for c in response.data}
    return {}

# Add a function to load Lottie animation JSON from a URL.
def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

def detect_latest_interaction_query(message):
    pattern = re.compile(r'(latest|last) interaction with ([\w\s]+)', re.IGNORECASE)
    match = pattern.search(message)
    if match:
        customer_name = match.group(2).strip()
        return customer_name
    return None

def get_latest_interaction_by_name(customer_name: str):
    customer = supabase_client.table('customers').select('interaction_metadata').eq('customer_name', customer_name).single().execute()
    if customer.data and customer.data.get('interaction_metadata'):
        interactions = customer.data['interaction_metadata']
        if interactions:
            return interactions[-1]  # Last (latest) interaction
    return None

def detect_summarize_query(message):
    pattern = re.compile(r'summarize (my )?interaction(s)? with ([\w\s]+)', re.IGNORECASE)
    match = pattern.search(message)
    if match:
        customer_name = match.group(3).strip()
        return customer_name
    return None

def summarize_interactions_with_customer(customer_name, user_id, n=5):
    customer = supabase_client.table('customers').select('interaction_metadata').eq('customer_name', customer_name).single().execute()
    if customer.data and customer.data.get('interaction_metadata'):
        interactions = customer.data['interaction_metadata'][-n:]  # Last n interactions
        if not interactions:
            return f"No interactions found for {customer_name}."
        context = ""
        for i, interaction in enumerate(interactions, 1):
            context += f"Interaction {i}:\nInput: {interaction['input']}\nOutput: {interaction['output']}\n"
        system_prompt = f"Summarize the following interactions with {customer_name}:"
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": context}
        ]
        response = get_llm_response(messages, model)
        return ''.join(chunk.choices[0].delta.content for chunk in response if chunk.choices[0].delta.content)
    return f"No interactions found for {customer_name}."

def chat_with_memories(message, user_id):
    # Meta-query detection for latest interaction
    customer_name_meta = detect_latest_interaction_query(message)
    if customer_name_meta:
        latest = get_latest_interaction_by_name(customer_name_meta)
        if not latest:
            return f"No interactions found for {customer_name_meta}."
        formatted = (
            f"Latest interaction with {customer_name_meta}:\n"
            f"Input: {latest['input']}\n"
            f"Output: {latest['output']}\n"
            f"Timestamp: {latest['timestamp']}\n"
        )
        return formatted
    # Meta-query detection for summarize
    customer_name_summarize = detect_summarize_query(message)
    if customer_name_summarize:
        return summarize_interactions_with_customer(customer_name_summarize, user_id)
    try:
        # 1. Detect if a customer is mentioned in the message
        customer_dict = get_all_customer_names()
        mentioned_customer = None
        for name in customer_dict:
            if name.lower() in message.lower():
                mentioned_customer = name
                break

        # 2. Fetch customer conversations if mentioned (RAG retrieval)
        customer_context = ""
        if mentioned_customer:
            customer_id = customer_dict[mentioned_customer]
            relevant_interactions = retrieve_relevant_interactions(customer_id, message, top_k=3)
            if relevant_interactions:
                customer_context += f"\nCustomer: {mentioned_customer}\n"
                for interaction in relevant_interactions:
                    customer_context += f"User: {interaction['input']}\nAI: {interaction['output']}\n(Similarity: {interaction['similarity']:.2f})\n"

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
If the user asks about a specific customer, use the customer's most relevant past interactions below (retrieved by semantic similarity).
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
            response = get_llm_response(messages, model)
            full_response = ""
            response_placeholder = st.empty()
            for chunk in response:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    response_placeholder.markdown(full_response + "▌")
            response_placeholder.markdown(full_response)
            # Show what conversations were used
            if mentioned_customer and relevant_interactions:
                with st.expander("Relevant Past Interactions Used for this Response"):
                    for i, interaction in enumerate(relevant_interactions, 1):
                        st.write(f"Interaction {i} (Similarity: {interaction['similarity']:.2f}):")
                        st.write(f"User: {interaction['input']}")
                        st.write(f"AI: {interaction['output']}")
        # Create new memories from the conversation
        messages.append({"role": "assistant", "content": full_response})
        memory.add(messages, user_id=user_id)
        # --- New: Automatically store conversation if customer is mentioned ---
        try:
            if mentioned_customer:
                update_customer_interaction(customer_dict[mentioned_customer], message, full_response, user_id)
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
def render_customer_creation_ui_tab(user_id):
    st.subheader("Create New Customer")

    # Initialize the input field state if it doesn't exist
    if 'tab_new_customer_name' not in st.session_state:
        st.session_state.tab_new_customer_name = ""

    # Text input for customer name
    new_customer_name = st.text_input("Enter Customer Name", key="tab_new_customer_name")

    # Add the Enter button always below the input field
    if st.button("Enter", key="create_customer_enter_button", type="primary"):
        if not new_customer_name:
            st.warning("Please enter a customer name.")
        else:
            # Initialize the creation state
            st.session_state.customer_creation_state = {
                'step': 1,
                'customer_name': new_customer_name,
                'profile': None,
                'confirmed': False
            }
            st.rerun()

    # --- Customer creation flow logic based on state ---
    if st.session_state.get('customer_creation_state') is not None:
        # Call create_new_customer to handle the current step (1, 2, or 3)
        created_customer_data = create_new_customer(
            st.session_state.customer_creation_state['customer_name'],
            user_id
        )

        # After create_new_customer finishes its steps, check if creation was successful (step 3 completed)
        if created_customer_data:
            # Customer creation finished successfully in create_new_customer (step 3)
            # Clear the creation state
            st.session_state.customer_creation_state = None
            # Show success message
            st.success(f"Customer {created_customer_data.get('customer_name', 'created')} created successfully! (ID: {created_customer_data.get('display_id', 'N/A')})")
            st.info("To update your interaction with this customer, please go to 'Choose Existing' section, select the customer, and upload your insights, conversations and data.")

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

def analyze_spin_elements(new_interaction: str, past_context: str):
    """Analyze text for SPIN selling elements, using past interactions for context."""
    system_prompt = f"""Analyze the "New Interaction" below to identify SPIN elements (Situation, Problem, Implication, Need-Payoff). Use the "Past Interactions" as context.

If the new interaction is empty or doesn't contain enough information, state that clearly.

**Past Interactions:**
{past_context}

**New Interaction to Analyze:**
{new_interaction}

Format your response as:
SPIN Analysis:
- Situation: [details]
- Problem: [details]
- Implication: [details]
- Need-Payoff: [details]
"""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Please provide the SPIN analysis."}
    ]
    
    response = get_llm_response(messages, model)
    return "".join(chunk.choices[0].delta.content for chunk in response if chunk.choices[0].delta.content)

def determine_sales_stage(new_interaction: str, past_context: str, current_stage: str = None):
    """Determine the sales stage based on Brian Tracy's 7-stage process, using past interactions for context."""
    system_prompt = f"""Analyze the "New Interaction" below to determine the current stage in Brian Tracy's 7-stage sales process. Use the "Past Interactions" as context.

If the new interaction is empty or doesn't contain enough information, state that clearly.

**Past Interactions:**
{past_context}

**New Interaction to Analyze:**
{new_interaction}

Current stage (if known): {current_stage}

The 7 stages are:
1. Prospecting, 2. First Contact, 3. Needs Analysis, 4. Presenting Solution, 5. Handling Objections, 6. Closing, 7. Follow-up and Referrals.

Format your response as:
Sales Stage Analysis:
- Current Stage: [stage number and name]
- Progress: [whether moving forward, backward, or maintaining]
- Key Indicators: [specific points from the new interaction that indicate this stage]
"""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Please provide the sales stage analysis."}
    ]
    
    response = get_llm_response(messages, model)
    return "".join(chunk.choices[0].delta.content for chunk in response if chunk.choices[0].delta.content)

def suggest_next_action(new_interaction: str, past_context: str, spin_analysis: str, sales_stage: str):
    """Suggest next action based on interaction context."""
    system_prompt = f"""Based on the following information, suggest the next best action. Use the "Past Interactions" as context for your suggestion.

**Past Interactions:**
{past_context}

**New Interaction:**
{new_interaction}

**SPIN Analysis of New Interaction:**
{spin_analysis}

**Sales Stage Analysis of New Interaction:**
{sales_stage}

Format your response as:
Suggested Next Action:
- Primary Action: [specific action to take]
- Supporting Tasks: [list of supporting tasks]
- Timeline: [suggested timeline]
"""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "What should be the next action?"}
    ]
    
    response = get_llm_response(messages, model)
    return "".join(chunk.choices[0].delta.content for chunk in response if chunk.choices[0].delta.content)

def analyze_customer_update(update_text: str, customer_id: str, customer_name: str):
    """Analyze customer update with AI reasoning (Brian Tracy 7-stage journey style), using all past interactions and the new interaction."""
    # Fetch all past interactions for this customer
    interactions = get_customer_interactions(customer_id)
    # Format the interaction history for the prompt
    history_str = ""
    for i, interaction in enumerate(interactions, 1):
        history_str += f"Interaction {i}:\nInput: {interaction['interaction_input']}\nOutput: {interaction['llm_output_summary']}\n"
    # Compose the user prompt
    user_prompt = f"Customer: {customer_name}\n\nHistorical Interactions:\n{history_str}\nNEW_INTERACTION:\n{update_text}\n"
    system_prompt = '''You are "LeanChem AI CRM Analyst", an expert B2B sales assistant trained in Brian Tracy's methods.
Follow the 7-stage journey:
1 Prospecting\t2 Rapport\t3 Needs Analysis\t4 Present\t5 Objections\t6 Close\t7 Follow-up
For every customer you will:
* Retrieve the full record from the key "customerdatabase".
* Summarise existing information stage-by-stage (max 70 words per stage).
* If NEW_INTERACTION is present, append it to interactions[], overwriting conflicting facts; then re-evaluate all stage scores (1–10).
* Map every enabler with {impact, willingness}.
* Assign sequential Deal-IDs when stage 6 is triggered.
* Return PLAIN TEXT with two blocks: \n  A) 7-Stage Summary\tB) Insights & Action Plan (Brian Tracy style, ≤200 words)
'''
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    response = get_llm_response(messages, model)
    return "".join(chunk.choices[0].delta.content for chunk in response if chunk.choices[0].delta.content)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def update_customer_interaction(customer_id: str, new_input: str, new_output: str, user_id: str):
    """Update customer interaction, storing a structured JSON object in the metadata."""
    # 1. Generate embedding for the new input
    embedding = gemini_embed(new_input)
    print("DEBUG: embedding from gemini_embed:", embedding, type(embedding))
    import json
    import numpy as np
    # --- Robust ensure_vector function ---
    def ensure_vector(x):
        # If it's already a list of floats, return as is
        if isinstance(x, list):
            # If it's a list of lists (shouldn't happen), flatten
            if len(x) > 0 and isinstance(x[0], list):
                return x[0]
            return x
        # If it's a string, try to parse as JSON list, or wrap as list
        if isinstance(x, str):
            try:
                val = json.loads(x)
                if isinstance(val, list):
                    return val
                else:
                    return [float(val)]
            except Exception:
                return [float(x)]
        # If it's a float or int, wrap as list
        if isinstance(x, float) or isinstance(x, int):
            return [float(x)]
        # If it's a numpy array
        if isinstance(x, np.ndarray):
            return x.tolist()
        # Fallback: wrap as list
        return [float(x)]

    embedding = ensure_vector(embedding)
    # 2. Create the new interaction object (as JSON)
    new_interaction_json = {
        "input": new_input,
        "output": new_output,
        "timestamp": datetime.datetime.now().isoformat(),
        "user_id": user_id
    }

    # 3. Fetch existing data
    customer = supabase_client.table('customers').select("*").eq('customer_id', customer_id).single().execute()
    inps = customer.data.get('input_conversation') or []
    outs = customer.data.get('output_conversation') or []
    embs = customer.data.get('interaction_embeddings') or []
    metas = customer.data.get('interaction_metadata') or []  # This is now a list of JSON objects

    # Defensive: ensure all are lists
    if not isinstance(inps, list):
        inps = list(inps) if inps else []
    if not isinstance(outs, list):
        outs = list(outs) if outs else []
    if not isinstance(embs, list):
        embs = list(embs) if embs else []
    if not isinstance(metas, list):
        metas = list(metas) if metas else []

    # 4. Append new data
    updated_inputs = inps + [new_input]
    updated_outputs = outs + [new_output]
    updated_embs = embs + [embedding]  # list of lists of floats
    updated_metas = metas + [new_interaction_json]  # list of dicts (JSON)

    # --- Ensure every embedding is a list of floats ---
    updated_embs = [ensure_vector(e) for e in updated_embs]
    # --- Ensure every metadata is a dict ---
    updated_metas = [m if isinstance(m, dict) else json.loads(m) for m in updated_metas]

    # Debug: Print types and sample data before update
    print("DEBUG: Types and lengths before update:")
    print("updated_inputs:", type(updated_inputs), len(updated_inputs))
    print("updated_outputs:", type(updated_outputs), len(updated_outputs))
    print("updated_embs:", type(updated_embs), len(updated_embs))
    print("updated_metas:", type(updated_metas), len(updated_metas))
    print("Sample embedding (last):", updated_embs[-1], type(updated_embs[-1]))

    # 5. Save
    try:
        response = supabase_client.table('customers').update({
            'input_conversation': updated_inputs,
            'output_conversation': updated_outputs,
            'interaction_embeddings': updated_embs,  # list of lists of floats
            'interaction_metadata': updated_metas,    # list of dicts (JSON)
            'updated_at': datetime.datetime.now().isoformat()
        }).eq('customer_id', customer_id).execute()
        return response.data
    except Exception as e:
        print("Supabase update error:", e)
        st.error(f"Supabase update error: {e}")
        raise

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def retrieve_relevant_interactions(customer_id: str, query: str, top_k: int = 3):
    """Retrieve the most relevant past interactions using vector similarity, returning full JSON objects."""
    query_embedding = gemini_embed(query)
    print("DEBUG: query_embedding from gemini_embed:", query_embedding, type(query_embedding))
    import json
    import numpy as np
    if isinstance(query_embedding, str):
        try:
            query_embedding = json.loads(query_embedding)
        except Exception:
            query_embedding = [float(query_embedding)]
    elif isinstance(query_embedding, float) or isinstance(query_embedding, int):
        query_embedding = [query_embedding]
    elif isinstance(query_embedding, np.ndarray):
        query_embedding = query_embedding.tolist()
    # Now query_embedding should be a list of floats
    customer = supabase_client.table('customers').select("interaction_embeddings, interaction_metadata").eq('customer_id', customer_id).single().execute()
    
    if not customer.data:
        return []

    embs = customer.data.get('interaction_embeddings', [])
    metas = customer.data.get('interaction_metadata', [])

    if not embs or not metas:
        return []

    # Handle case where embeddings list is shorter than metadata list, or vice-versa
    min_len = min(len(embs), len(metas))
    embs_np = np.array(embs[:min_len])
    metas = metas[:min_len]

    if embs_np.shape[0] == 0:
        return []

    query_np = np.array(query_embedding)
    similarities = embs_np @ query_np / (np.linalg.norm(embs_np, axis=1) * np.linalg.norm(query_np) + 1e-8)
    top_indices = np.argsort(similarities)[-top_k:][::-1]

    # Return the full JSON object from metadata, adding similarity score
    results = []
    for i in top_indices:
        interaction_json = metas[i]
        interaction_json['similarity'] = float(similarities[i])
        results.append(interaction_json)
        
    return results

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
    """Process uploaded file, extract content, and generate summary."""
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
        for chunk in get_llm_response(messages, model):
            if chunk.choices[0].delta.content:
                summary += chunk.choices[0].delta.content

        # Instead of storing directly, return the content and summary
        # update_customer_interaction(
        #     customer_id,
        #     f"Uploaded file: {file.name}\nContent: {file_content}",
        #     f"File Analysis:\n{summary}"
        # )

        # Return both the file content and the generated summary
        return True, "Document analyzed successfully! Review analysis below and save.", file_content, summary
    except Exception as e:
        return False, f"Error processing file: {str(e)}", None, None

def render_update_interaction_ui(user_id: str):
    """Render the Update Interaction window UI."""

    # State 1: Customer Selection
    if 'selected_customer_for_update' not in st.session_state or st.session_state['selected_customer_for_update'] is None:
        st.subheader("Select Customer to Update")

        customers_dict = get_all_customer_names()
        if not customers_dict:
            st.warning("No customers found. Please create a customer first.")
            return

        sorted_customer_names = sorted(customers_dict.keys())

        col_dropdown, col_button = st.columns([0.7, 0.3])

        with col_dropdown:
            selected_customer_name = st.selectbox(
                "Select Customer",
                options=sorted_customer_names,
                key="update_interaction_customer_select"
            )

        with col_button:
            st.markdown("<br>", unsafe_allow_html=True) # Add a small space above the button
            select_button = st.button("Select", key="select_customer_button", type="primary")

        # Store the selected customer ID if the button is clicked and trigger rerun
        if select_button and selected_customer_name:
            selected_customer_id = customers_dict.get(selected_customer_name)
            if selected_customer_id:
                st.session_state['selected_customer_for_update'] = {
                    'name': selected_customer_name,
                    'id': selected_customer_id
                }
                st.rerun() # Rerun to show the interaction details

    # State 2, 3, 4: Interaction Details and Adding New Data
    else:
        selected_customer = st.session_state['selected_customer_for_update']
        customer_name = selected_customer['name']
        customer_id = selected_customer['id']

        st.subheader(f"Interactions with {customer_name}")

        # Display interaction history (Collapsible Cards)
        interactions = get_customer_interactions(customer_id)
        if interactions:
            for idx, interaction in enumerate(reversed(interactions)):
                with st.expander(f"{interaction['created_at']} | Interaction #{len(interactions)-idx}"):
                    st.markdown(f"**Input:** {interaction['interaction_input']}")
                    st.markdown(f"**AI Output:** {interaction['llm_output_summary']}")
            if st.button("Select Another Customer"):
                st.session_state['selected_customer_for_update'] = None
                if 'current_interaction_analysis' in st.session_state:
                    st.session_state['current_interaction_analysis'] = None
                if 'current_file_analysis' in st.session_state:
                    st.session_state['current_file_analysis'] = None
                st.rerun()
        else:
            st.info("No interactions found for this customer yet.")
            if st.button("Select Another Customer"):
                st.session_state['selected_customer_for_update'] = None
                if 'current_interaction_analysis' in st.session_state:
                    st.session_state['current_interaction_analysis'] = None
                if 'current_file_analysis' in st.session_state:
                    st.session_state['current_file_analysis'] = None
                st.rerun()

        st.markdown("\n---\n")

        # --- Section for adding New Interactions and Uploads ---
        st.subheader("Add New Interaction or Upload Document")

        # State 3: Display file analysis and Save/Cancel buttons if available in session state
        if 'current_file_analysis' in st.session_state and st.session_state['current_file_analysis'] is not None:
            file_analysis_data = st.session_state['current_file_analysis']
            st.subheader("📄 File Analysis Ready to Save")
            st.write(f"**File:** {file_analysis_data['file_name']}")
            st.markdown("**Extracted Content (Input):**")
            st.expander("View full content").markdown(f"```\n{file_analysis_data['file_content']}\n```")
            st.markdown("**AI Summary (Output):**")
            # Tabs for AI summary (if you want to split by sections, you can parse summary here)
            st.write(file_analysis_data['summary'])
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Save File Interaction", key="save_file_interaction_button"):
                    llm_output = f"File Analysis:\n{file_analysis_data['summary']}"
                    interaction_input = f"Uploaded file: {file_analysis_data['file_name']}. Content summary: {file_analysis_data['file_content'][:200]}..."
                    result = update_customer_interaction(customer_id, interaction_input, llm_output, user_id)
                    if result:
                        st.success(f"File analysis for {file_analysis_data['file_name']} saved successfully!")
                        st.session_state['current_file_analysis'] = None
                        st.rerun()
                    else:
                        st.error("Failed to save file analysis")
            with col2:
                if st.button("❌ Cancel", key="cancel_file_interaction_button"):
                    st.session_state['current_file_analysis'] = None
                    st.rerun()
            st.markdown("\n---\n")

        # State 4: Display analysis and Save/Cancel buttons for text interaction if available in session state
        elif 'current_interaction_analysis' in st.session_state and st.session_state['current_interaction_analysis'] is not None:
            analysis_data = st.session_state['current_interaction_analysis']
            st.subheader("🤖 AI Analysis")
            # Tabs for AI output
            tabs = st.tabs(["SPIN Analysis", "Sales Stage", "Next Action"])
            with tabs[0]:
                st.write(analysis_data['spin_analysis'])
            with tabs[1]:
                st.write(analysis_data['sales_stage'])
            with tabs[2]:
                st.write(analysis_data['next_action'])
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Save Interaction", key="save_interaction_button"):
                    llm_output = f"SPIN Analysis:\n{analysis_data['spin_analysis']}\n\nSales Stage:\n{analysis_data['sales_stage']}\n\nNext Action:\n{analysis_data['next_action']}"
                    result = update_customer_interaction(customer_id, analysis_data['new_interaction'], llm_output, user_id)
                    if result:
                        st.success("Interaction saved successfully!")
                        st.session_state['current_interaction_analysis'] = None
                        st.rerun()
                    else:
                        st.error("Failed to save interaction")
            with col2:
                if st.button("❌ Cancel", key="cancel_interaction_button"):
                    st.session_state['current_interaction_analysis'] = None
                    st.rerun()
            st.markdown("\n---\n")

        # State 5: Default state for adding new interactions/uploads
        else:
            st.subheader("✍️ New Interaction")
            st.caption("Add a new customer interaction and analyze it with AI, or ask any question about this customer.")
            new_interaction = st.text_area("📝 Enter new interaction details or any question", key="new_interaction_textarea")
            if st.button("💡 Analyze with AI", key="analyze_interaction_button") and new_interaction:
                # Meta-query detection for summarize (always use selected customer)
                if "summarize" in new_interaction.lower():
                    summary = summarize_interactions_with_customer(customer_name, user_id)
                    st.session_state['current_interaction_analysis'] = {
                        'new_interaction': new_interaction,
                        'spin_analysis': summary,
                        'sales_stage': summary,
                        'next_action': summary
                    }
                    st.rerun()
                with st.spinner("Analyzing interaction or answering your question..."):
                    # 1. Retrieve relevant past interactions for context (always use selected customer)
                    relevant_interactions = retrieve_relevant_interactions(customer_id, new_interaction, top_k=3)
                    past_context = "No relevant past interactions found."
                    if relevant_interactions:
                        past_context = "Relevant Past Interactions (for context):\n"
                        for interaction in relevant_interactions:
                            past_context += f"- User: {interaction['input']}\\n- AI: {interaction['output']}\\n"
                    # --- Improved meta-query detection ---
                    is_question = new_interaction.strip().endswith('?')
                    is_summarize = "summarize" in new_interaction.lower()
                    is_latest = "latest interaction" in new_interaction.lower() or "last interaction" in new_interaction.lower()

                    if is_question or is_summarize or is_latest:
                        # Use open-ended RAG answer for questions and meta-queries
                        open_answer = answer_any_query_with_rag(new_interaction, customer_id, user_id, top_k=3)
                        st.session_state['current_interaction_analysis'] = {
                            'new_interaction': new_interaction,
                            'spin_analysis': open_answer,
                            'sales_stage': open_answer,
                            'next_action': open_answer
                        }
                    else:
                        # Always run classic sales analysis for normal sales interactions
                        spin_analysis = analyze_spin_elements(new_interaction, past_context)
                        sales_stage = determine_sales_stage(new_interaction, past_context)
                        next_action = suggest_next_action(new_interaction, past_context, spin_analysis, sales_stage)
                        st.session_state['current_interaction_analysis'] = {
                            'new_interaction': new_interaction,
                            'spin_analysis': spin_analysis,
                            'sales_stage': sales_stage,
                            'next_action': next_action
                        }
                st.rerun()
            st.markdown("\n---\n")
            st.subheader("Upload Document")
            uploaded_file = st.file_uploader(
                "Upload a document (PDF, TXT, DOCX)",
                type=['pdf', 'txt', 'docx'],
                key="customer_file_upload"
            )
            if uploaded_file:
                if st.button("Process Document", key="process_uploaded_file_button"):
                    success, message, file_content, summary = process_uploaded_file(uploaded_file, customer_id)
                    if success:
                        st.success(message)
                        st.session_state['current_file_analysis'] = {
                            'file_name': uploaded_file.name,
                            'file_content': file_content,
                            'summary': summary
                        }
                        st.rerun()
                    else:
                        st.error(message)

def get_all_customer_data():
    """Fetch all customer data with their interactions"""
    try:
        response = supabase_client.table('customers').select('*').execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error fetching customer data: {str(e)}")
        return []

def analyze_crm_data(query: str, user_id: str):
    """Analyze CRM data based on natural language query (RAG-ENHANCED VERSION)"""
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

    # --- RAG: Retrieve relevant documents and conversations ---
    relevant_docs = search_documents(query, user_id, limit=5)
    docs_str = ""
    if relevant_docs:
        docs_str = "\nRelevant Documents and Conversations:\n"
        for i, doc in enumerate(relevant_docs, 1):
            docs_str += f"\nDocument {i}:\n{doc.get('content', '')}\n"

    system_prompt = """You are a CRM data analyst specialized in chemical trading. Analyze the provided data and answer the user's query.\nUse the following guidelines:\n1. Be concise but comprehensive\n2. Structure your response in a clear, readable format\n3. Include relevant numbers and statistics when available\n4. Highlight important trends or patterns\n5. Suggest actionable insights when relevant\n\nAvailable Data:\n{context}\n\nRelevant Memories:\n{memories}\n\n{docs}\n\nFormat your response as:\nAnalysis:\n[Your analysis here]\n\nKey Findings:\n- [Finding 1]\n- [Finding 2]\n...\n\nRecommendations:\n- [Recommendation 1]\n- [Recommendation 2]\n...\n"""

    messages = [
        {"role": "system", "content": system_prompt.format(context=context, memories=memories_str, docs=docs_str)},
        {"role": "user", "content": query}
    ]
    try:
        response = get_llm_response(messages, model)
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
    show_saved = st.checkbox("Show Saved Queries", key="show_saved_analysis_queries")

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

    # --- New Analysis Section ---
    st.subheader("📝 New Analysis")
    st.write("Type your question about CRM data and click the button to analyze with AI.")

    analysis_query = st.text_area("Enter your analysis query", key="new_analysis_query_input")

    if st.button("💡 Analyze with AI", key="analyze_crm_button") and analysis_query:
        with st.spinner("Analyzing CRM data..."):
            analysis_response = analyze_crm_data(analysis_query, user_id)
            # Store analysis response and query in session state for display and saving
            st.session_state['current_crm_analysis'] = {
                'query': analysis_query,
                'response': analysis_response
            }
            st.rerun() # Rerun to display analysis and save button

    # Display current analysis response and Save button if available in session state
    if 'current_crm_analysis' in st.session_state and st.session_state['current_crm_analysis'] is not None:
        analysis_data = st.session_state['current_crm_analysis']
        st.subheader("🤖 AI Analysis Result")
        st.write("**Query:**", analysis_data['query'])
        st.write("**Response:**")
        st.write(analysis_data['response'])

        if st.button("💾 Save Analysis", key="save_current_analysis_button"):
            saved_query_data = save_analysis_query(analysis_data['query'], analysis_data['response'], user_id)
            if saved_query_data:
                st.success("Analysis saved successfully!")
                # Clear the current analysis from session state after saving
                st.session_state['current_crm_analysis'] = None
                st.rerun() # Rerun to refresh the saved queries list (if shown)
            else:
                st.error("Failed to save analysis")

    # Clear the input area after analysis is triggered or saved (optional, can be adjusted)
    # if 'new_analysis_query_input' in st.session_state:
    #     del st.session_state['new_analysis_query_input']

def check_documents_table():
    """Check if there are any documents in the documents table"""
    try:
        response = supabase_client.table('documents').select('count').execute()
        return len(response.data) if response.data else 0
    except Exception as e:
        st.error(f"Error checking documents table: {str(e)}")
        return 0

def test_api_connectivity():
    """Test API connectivity and return status"""
    results = {}
    
    # Test Gemini API
    if GEMINI_API_KEY:
        try:
            # Simple test request
            test_payload = {"text": "test"}
            headers = {"Content-Type": "application/json"}
            params = {"key": GEMINI_API_KEY}
            
            response = requests.post(
                GEMINI_EMBED_URL,
                params=params,
                headers=headers,
                data=json.dumps(test_payload),
                timeout=10
            )
            
            if response.status_code == 200:
                results['gemini'] = "✅ Working"
            else:
                results['gemini'] = f"❌ Error {response.status_code}: {response.text[:100]}"
        except Exception as e:
            results['gemini'] = f"❌ Connection failed: {str(e)}"
    else:
        results['gemini'] = "❌ No API key"
    
    # Test OpenAI API
    openai_key = os.getenv('OPENAI_API_KEY')
    if openai_key:
        try:
            response = openai_client.embeddings.create(
                input="test",
                model="text-embedding-3-small"
            )
            results['openai'] = "✅ Working"
        except Exception as e:
            results['openai'] = f"❌ Error: {str(e)}"
    else:
        results['openai'] = "❌ No API key"
    
    # Test Supabase
    try:
        response = supabase_client.table('customers').select('count').limit(1).execute()
        results['supabase'] = "✅ Working"
    except Exception as e:
        results['supabase'] = f"❌ Error: {str(e)}"
    
    return results

# --- RAG Test UI ---
def render_rag_test_ui(user_id):
    import streamlit as st
    st.title("🔍 RAG Test: Conversation Retrieval")
    st.markdown("---")
    # Check if conversations exist in the database
    try:
        response = supabase_client.table('conversation').select('count').execute()
        conv_count = len(response.data) if response.data else 0
    except Exception as e:
        st.error(f"Error checking conversation table: {str(e)}")
        conv_count = 0
    if conv_count == 0:
        st.warning("⚠️ No conversations found in the database. Please upload some test conversations first.")
        st.subheader("📝 Upload Test Conversation")
        test_content = st.text_area(
            "Enter test conversation content",
            value="Customer inquiry about RDP (Redispersible Polymer Powder) for dry-mix mortar applications. Need technical specifications and pricing for construction projects in Ethiopia.",
            key="test_conversation_content"
        )
        if st.button("📤 Upload Test Conversation", key="upload_test_conversation_button"):
            if test_content:
                with st.spinner("Uploading test conversation..."):
                    result = upload_test_conversation(test_content, user_id)
                    if result:
                        st.rerun()
            else:
                st.warning("Please enter some content for the test conversation.")
        return
    st.subheader("🔍 Test Conversation Retrieval")
    query = st.text_input("Enter a query to test conversation retrieval", key="rag_test_query")
    limit = st.number_input("Number of results to fetch", min_value=1, max_value=10, value=3, step=1, key="rag_test_limit")
    if st.button("🔍 Run RAG Test", key="run_rag_test_button") and query:
        with st.spinner("Fetching relevant conversations from Supabase..."):
            conversations = search_documents(query, user_id, limit=limit)
        if conversations:
            # Combine all retrieved conversation contents
            context = "\n\n".join(conv.get('content', '') for conv in conversations)
            # Build a prompt for Gemini
            prompt = (
                f"Context:\n{context}\n\n"
                f"User Query: {query}\n\n"
                "Based on the above context, provide a concise, insightful answer to the user's query. "
                "If the context is insufficient, say so."
            )
            # Call Gemini for analysis
            analyzed_answer = gemini_chat([
                {"role": "system", "content": "You are an expert CRM assistant."},
                {"role": "user", "content": prompt}
            ])
            st.subheader("🤖 Gemini's Analyzed Answer")
            st.write(analyzed_answer)
            # Optionally, still show the raw retrieved conversations for transparency
            with st.expander("Show Retrieved Conversations"):
                for i, conv in enumerate(conversations, 1):
                    st.markdown(f"**Conversation {i}:**")
                    st.code(conv.get('content', '')[:2000], language='text')
                    if conv.get('similarity'):
                        st.info(f"Similarity Score: {conv.get('similarity', 'N/A'):.4f}")
                    st.markdown("---")
        else:
            st.warning("No relevant conversations found for this query.")
    st.caption("This tool helps you debug and verify your RAG pipeline by directly inspecting what the retriever returns from your uploaded conversations.")

# --- Customer search and update interaction for dashboard tab ---
def render_choose_existing_ui(user_id):
    # Removed Customer Search Section
    # st.subheader("Customer Search")
    # search_query = st.text_input("Search customers", key="tab_customer_search")
    # customers = search_customers(search_query) if search_query else get_all_customer_names()
    # if customers:
    #     st.write("Found customers:")
    #     for customer in (customers if isinstance(customers, list) else customers.keys()):
    #         name = customer['customer_name'] if isinstance(customer, dict) else customer
    #         with st.expander(name):
    #             if isinstance(customer, dict):
    #                 st.write("Created:", customer.get('created_at', 'N/A'))
    #                 st.write("Last updated:", customer.get('updated_at', 'N/A'))
    #                 if customer.get('input_conversation'):
    #                     st.write("Recent conversations:")
    #                     for i, (input_msg, output_msg) in enumerate(zip(customer['input_conversation'][-3:], customer['output_conversation'][-3:]), 1):
    #                         st.write(f"Conversation {i}:")
    #                         st.write("Input:", input_msg)
    #                         st.write("Output:", output_msg)
    # else:
    #     st.write("No customers found.")

    st.subheader("Customer Management")

    # Removed All Interactions Table Section
    # st.subheader("📋 All Interactions Table")
    # interactions = get_customer_interactions(customers[selected_customer])
    # if interactions:
    #     df = pd.DataFrame(interactions)
    #     # Reorder columns for clarity
    #     cols = [c for c in ["created_at", "interaction_input", "llm_output_summary"] if c in df.columns]
    #     df = df[cols]
    #     df = df.rename(columns={
    #         "created_at": "Date",
    #         "interaction_input": "Input",
    #         "ai_output_summary": "AI Output"
    #     })
    #     st.dataframe(df, use_container_width=True)
    #     csv = df.to_csv(index=False).encode('utf-8')
    #     st.download_button(
    #         label="Export Interactions to CSV",
    #         data=csv,
    #         file_name=f"{selected_customer}_interactions.csv",
    #         mime='text/csv',
    #         key="export_interactions_csv"
    #     )
    # else:
    #     st.info("No interactions found for this customer.")
    # st.markdown("---")

    # Removed View Mode Section
    # st.subheader("🗂️ View Mode")
    # view_mode = st.radio(
    #     "View Mode",
    #     ["Full Chat Thread", "Summarized Insight"],
    #     horizontal=True,
    #     key="update_interaction_view_mode"
    # )

    # The customer selection is now handled inside render_update_interaction_ui
    # Fetch customer interactions - This is now done inside render_update_interaction_ui
    # interactions = get_customer_interactions(customers[selected_customer])

    # if view_mode == "Full Chat Thread":
    #     st.subheader("💬 Interaction History")
    #     for interaction in interactions:
    #         with st.expander(f"Interaction on {interaction['created_at']}"):
    #             st.write("Input:", interaction['interaction_input'])
    #             st.write("Analysis:", interaction['llm_output_summary'])
    # else:
        # Generate summary - This is now done inside render_update_interaction_ui
    #    ...
    # st.markdown("---")

    render_update_interaction_ui(user_id)

# --- Main CRM Dashboard with Tabs ---
def main_crm_dashboard(user_id, default_tab=None):
    st.title("CRM Dashboard")
    
    # Determine the default tab index based on the default_tab string
    tab_titles = ["Create Customer", "Choose Existing", "Analysis & Chat", "RAG Test"]
    default_tab_index = 0 # Default to Create Customer
    if default_tab == 'manage':
        default_tab_index = 1
    elif default_tab == 'analysis':
        default_tab_index = 2
    elif default_tab == 'rag':
        default_tab_index = 3

    tabs = st.tabs(tab_titles)

    with tabs[default_tab_index]:
        if default_tab == 'create' or default_tab is None:
            render_customer_creation_ui_tab(user_id)
        elif default_tab == 'manage':
            st.write("Rendering Manage Existing Customers section...") # Debugging line
            render_choose_existing_ui(user_id)
        elif default_tab == 'analysis':
            st.write("Rendering Report, Analysis & Notification section...") # Debugging line
            render_analysis_ui(user_id)
        elif default_tab == 'rag':
            st.write("Rendering RAG Test section...")
            render_rag_test_ui(user_id)

# --- Main Streamlit logic below ---
if st.session_state.get("logout_requested", False):
    st.session_state.logout_requested = False
    st.rerun()

# Initialize crm_view state if it doesn't exist
if 'crm_view' not in st.session_state:
    st.session_state.crm_view = None

# Sidebar: Only login/logout/profile
with st.sidebar:
    st.sidebar.title(" AI Powered CRM Chat ")
    # Add the logo here with error handling
    try:
        st.image("leanchems logo.png", width=150)
    except:
        st.markdown("### 🧠 AI Powered CRM")
    if not st.session_state.authenticated:
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        with tab1:
            st.subheader("Login")
            login_email = st.text_input("Email", key="sidebar_login_email")
            login_password = st.text_input("Password", type="password", key="sidebar_login_password")
            login_button = st.button("Login", key="sidebar_login_button", type="primary")
            if login_button:
                if login_email and login_password:
                    sign_in(login_email, login_password)
                else:
                    st.warning("Please enter both email and password.")
        with tab2:
            st.subheader("Sign Up")
            signup_name = st.text_input("Full Name", key="sidebar_signup_name")
            signup_email = st.text_input("Email", key="sidebar_signup_email")
            signup_password = st.text_input("Password", type="password", key="sidebar_signup_password")
            signup_button = st.button("Sign Up", key="sidebar_signup_button", type="primary")
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
            # Get the user's full name from metadata, default to 'User' if not found
            full_name = user.user_metadata.get('full_name', 'User')
            # Display welcome message, centered and bold
            st.markdown(f"<div style='text-align: center;'><strong>Welcome, {full_name}!</strong></div>", unsafe_allow_html=True)
            st.button("Logout", on_click=sign_out, key="sidebar_logout_button", type="primary")

# Main tabbed dashboard for authenticated users
if st.session_state.authenticated and st.session_state.user:
    user_id = st.session_state.user.id
    
    if st.session_state.crm_view is None:
        st.title("CRM Dashboard")
        st.write("Select an action to get started.")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("Create New Customer", key="btn_create_customer", use_container_width=True, type="primary"):
                st.session_state.crm_view = 'create'
                st.rerun()

        with col2:
            if st.button("Manage Existing Customers", key="btn_manage_customer", use_container_width=True, type="primary"):
                st.session_state.crm_view = 'manage'
                st.rerun()

        with col3:
            if st.button("Report, Analysis & Notification", key="btn_analyze_crm", use_container_width=True, type="primary"):
                st.session_state.crm_view = 'analysis'
                st.rerun()

        with col4:
            if st.button("RAG Test", key="btn_rag_test", use_container_width=True, type="primary"):
                st.session_state.crm_view = 'rag'
                st.rerun()

    else:
        # Render the content of the selected view without tabs
        st.title("CRM Dashboard") # Keep the main title
        user_id = st.session_state.user.id # Ensure user_id is available

        # Add a button to go back to the initial selection view
        st.markdown("---") # Add a separator
       
        if st.button("Back to Main Menu", key="btn_back_to_menu"):
            st.session_state.crm_view = None
            st.rerun()

        # Now render the section-specific content
        if st.session_state.crm_view == 'create':
            render_customer_creation_ui_tab(user_id)
        elif st.session_state.crm_view == 'manage':
            
            render_choose_existing_ui(user_id)
        elif st.session_state.crm_view == 'analysis':
           
            render_analysis_ui(user_id)
        elif st.session_state.crm_view == 'rag':
            render_rag_test_ui(user_id)

else:
    # Apply custom styling
    st.title("Welcome to LeanChems AI CRM Chat")
    st.write("Login or sign up to unlock powerful AI features for managing customer interactions, gaining insights, and driving growth.")
   
    # Feature highlights
    st.subheader("Features")
    col1, col2, col3 = st.columns(3)

    # Define Lottie animation URLs
    lottie_profiling = load_lottieurl("https://lottie.host/732c38ca-e084-4a94-a8c7-c2c1324b9700/WzO5X7h1a4.json") # Example URL, replace with actual
    lottie_relationships = load_lottieurl("https://lottie.host/embed/59a97f54-3a5c-494d-9d0f-b5504f6b308e/H6m7G94hUj.json") # Example URL, replace with actual
    lottie_reporting = load_lottieurl("https://lottie.host/8616b5b7-31f9-44c2-a110-76692c499332/oXqA8f8z07.json") # Example URL, replace with actual

    with col1:
        st.markdown('<div class="feature-box">', unsafe_allow_html=True)
        if lottie_profiling:
            st_lottie(lottie_profiling, height=150, key="profiling_animation")
        st.markdown("#### ✨ Ideal Customer Profiling")
        st.write("Leverage AI to build detailed profiles and understand your most valuable customers.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="feature-box">', unsafe_allow_html=True)
        if lottie_relationships:
            st_lottie(lottie_relationships, height=150, key="relationships_animation")
        st.markdown("#### 🤝 Develop & Manage Relationships")
        st.write("Track interactions, gain conversation insights, and nurture customer relationships effectively.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col3:
        st.markdown('<div class="feature-box">', unsafe_allow_html=True)
        if lottie_reporting:
            st_lottie(lottie_reporting, height=150, key="reporting_animation")
        st.markdown("#### 📈 Advanced Reporting & Alerts")
        st.write("Get data-driven insights and receive timely alerts to stay ahead of opportunities.")
        st.markdown('</div>', unsafe_allow_html=True)

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

def upload_test_conversation(content: str, user_id: str = "default_user"):
    """Upload a test conversation to the conversation table for RAG testing"""
    try:
        # Generate embedding for the content
        embedding = gemini_embed(content)
        
        # Store in Supabase conversation table
        data = {
            "content": content,
            "embedding": embedding,
            "metadata": {
                "user_id": user_id,
                "source": "test_upload",
                "type": "conversation"
            }
        }
        
        response = supabase_client.table("conversation").insert(data).execute()
        
        if response.data:
            st.success(f"Successfully uploaded test conversation with ID: {response.data[0]['id']}")
            return response.data[0]
        else:
            st.error("Failed to upload test conversation")
            return None
            
    except Exception as e:
        st.error(f"Error uploading test conversation: {str(e)}")
        return None

def answer_any_query_with_rag(user_query, customer_id, user_id, top_k=3):
    relevant_interactions = retrieve_relevant_interactions(customer_id, user_query, top_k=top_k)
    context = ""
    if relevant_interactions:
        context = "Relevant Past Interactions:\n"
        for interaction in relevant_interactions:
            context += f"- User: {interaction['input']}\n- AI: {interaction['output']}\n"
    else:
        context = "No relevant past interactions found."
    system_prompt = f"""You are a helpful CRM assistant. Use the relevant past interactions below to answer the user's question.\n\n{context}"""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_query}
    ]
    response = get_llm_response(messages, model)
    return "".join(chunk.choices[0].delta.content for chunk in response if chunk.choices[0].delta.content)

# Update the main execution block to use the new sidebar
if __name__ == "__main__":
    # This section won't run in Streamlit
    pass