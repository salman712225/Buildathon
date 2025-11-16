AI Home Design & Material Intelligence System
OpenAI × NxtWave Buildathon 2025 Project
A conversational AI platform that helps users plan their house layout and material selection using a step-by-step, expert-guided process.
The system uses multi-model failover (OpenAI → Groq → Gemini) to deliver fast, reliable responses with zero downtime.

Deployed App: https://buildathon-1-1wjj.onrender.com/

Authors 

M Mohammed Salman
Btech AIDS 4th Year 
B.S.Abdur Rahman Crescent Institute of Science and Technology

Sidrah Rashid 
BSc Data Science 3rd Year
Institute of Leadership and Entrepreneurship and Development

Features
1. Material Selection Agent
Acts as an expert consultant in architecture & materials
Asks one question at a time to understand:
Interior / Exterior / Both
Country & climate
Room/area
Design style
Mood & color palette
Budget & constraints
Sunlight & moisture
Substrate / area
Produces:
Ranked material recommendations
Climate-aware reasoning
Style + color logic
A practical sourcing & maintenance checklist

2. House Layout Planner Agent
Provides step-by-step planning for:
Plot size, direction & climate
Room and floor layout
Ventilation & sunlight strategy
Style selection
Material preferences
Budget ranges
Special requirements
Output includes 1–3 realistic layout planning options

3. Multi-Model AI Engine
Automatic failover between:
OpenAI GPT (primary)
Groq LLaMA 3.1 (ultra-fast fallback)
Gemini 2.5 (backup)
Ensures maximum uptime and fast responses.

4. Streamlit UI
Modern chat-style messaging
Light/dark mode–friendly
High-contrast user & assistant bubbles
Conversation memory with session state
Final output generation button

5. Secure Key Management
Keys are stored in a .env file:
3 × Groq keys
(Optional) OpenAI & Gemini keys
Loaded via python-dotenv.

Tech Stack
Component	Technology
UI	Streamlit
Backend	Python
Primary AI	OpenAI GPT
Secondary AI	Groq LLaMA 3.1
Fallback AI	Gemini 2.5
Key Management	.env + python-dotenv
UI Style	Custom CSS chat bubbles

Project Structure
project/
│
├── app.py                # Main Streamlit app
├── requirements.txt      # Python dependencies
├── .env                  # Secret API keys (not committed)
└── README.md             # Documentation

Installation & Setup
1. Clone the repo
git clone https://github.com/your-username/your-repo.git
cd your-repo

2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows

3. Install dependencies
pip install -r requirements.txt

4. Add your .env file
Create .env:
GROQ_KEY_1=gsk_xxxxxxxxxxxxxxxxxxxx
GROQ_KEY_2=gsk_yyyyyyyyyyyyyyyyyyyy
GROQ_KEY_3=gsk_zzzzzzzzzzzzzzzzzzzz
OPENAI_KEY=optional
GEMINI_KEY=optional

5. Run the app
streamlit run app.py

How It Works
Step 1 — Select Mode
Material Selection
House Layout Planning
Both Together

Step 2 — Conversational Flow
The assistant asks questions one by one based on selected mode.

Step 3 — Intelligent Reasoning
The system:
Stores user responses
Validates unclear answers
Infers climate from location
Uses persona-trained prompting

Step 4 — Final Output
A structured, personalized:
Material recommendation sheet or
House layout plan or
Both combined

Failover Logic
Key Failure Examples:
Rate limit exceeded
API key expired
Provider temporarily down

System Automatically Switches:
OpenAI → Groq → Gemini → Error fallback
Seamless, no user interruption.

Future Enhancements
AR-based room scanning
VR-based 3D house walkthrough
AI-generated texture previews
Marketplace integration for materials
Cost estimator agent
Multi-lingual conversational support

Contribution
Pull requests and suggestions are welcome.
Open an issue for feature requests or bugs.

License
MIT License (customizable based on your preference)

Final Notes
This project is developed for the
OpenAI × NxtWave Buildathon 2025
and showcases innovation in:
AI-driven home design
Real-time multi-model architecture

Persona-based planning & material intelligence

Conversational UX
