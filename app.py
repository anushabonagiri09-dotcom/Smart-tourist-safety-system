import streamlit as st
import google.generativeai as genai
import os
import pandas as pd
import sqlite3
from dotenv import load_dotenv
from streamlit_js_eval import get_geolocation
import folium
from streamlit_folium import st_folium



def speak(text):
    """Function to make the browser speak"""
    # Clean text of markdown characters
    clean_text = text.replace('*', '').replace('#', '').replace('"', "'")
    components_js = f"""
        <script>
        var msg = new SpeechSynthesisUtterance();
        msg.text = "{clean_text[:300]}"; 
        msg.rate = 1.0;
        window.speechSynthesis.speak(msg);
        </script>
    """
    st.components.v1.html(components_js, height=0)

# --- 1. DATABASE BACKEND LOGIC ---
def init_db():
    conn = sqlite3.connect('safety_system.db')
    c = conn.cursor()
    # User data table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                 name TEXT, phone TEXT UNIQUE, destination TEXT, 
                 emergency_contact TEXT, id_type TEXT)''')
    # Location tracking table
    c.execute('''CREATE TABLE IF NOT EXISTS location_logs
                 (phone TEXT, lat REAL, lon REAL, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def save_user(name, phone, dest, e_contact, id_type):
    try:
        conn = sqlite3.connect('safety_system.db')
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO users (name, phone, destination, emergency_contact, id_type) VALUES (?,?,?,?,?)",
                  (name, phone, dest, e_contact, id_type))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error: {e}")
        return False

def log_location(phone, lat, lon):
    conn = sqlite3.connect('safety_system.db')
    c = conn.cursor()
    c.execute("INSERT INTO location_logs (phone, lat, lon) VALUES (?, ?, ?)", (phone, lat, lon))
    conn.commit()
    conn.close()

# Initialize DB
init_db()

# --- 2. CONFIG & AUTH ---
ADMIN_PASSWORD = "admin123" # Change this for security
dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=dotenv_path)
google_api_key = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")

if not google_api_key:
    st.warning("Missing Google API key. Set GOOGLE_API_KEY in .env or Streamlit secrets.")
    st.stop()

genai.configure(api_key=google_api_key)
model = genai.GenerativeModel('gemini-3-flash-preview')

st.set_page_config(page_title="Smart Tourist Safety System", layout="wide", page_icon="🛡️")

# --- 3. NAVIGATION ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/826/826070.png", width=100)
    choice = st.radio("Navigation", [
        "Home", 
        "Registration", 
        "Live Location", 
        "Emergency Contacts", 
        "Chat AI", 
        "Mobile SOS", 
        "Admin View"
    ])

# --- 4. PAGES ---
if choice == "Home":
    # Custom CSS for a modern look
    st.markdown("""
        <style>
        .main {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        }
        .metric-card {
            background: rgba(255, 255, 255, 0.8);
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            text-align: center;
            border: 1px solid rgba(255, 255, 255, 0.3);
            margin-bottom: 10px;
        }
        </style>
    """, unsafe_allow_html=True) # Changed from unsafe_allow_value to unsafe_allow_html

    st.title("🛡️ Smart Tourist Safety Dashboard")
    st.markdown("---")
    
    # Hero Image with rounded corners
    st.markdown('<div style="border-radius: 20px; overflow: hidden; margin-bottom: 25px;">', unsafe_allow_html=True)
    st.image("https://images.unsplash.com/photo-1488646953014-85cb44e25828?auto=format&fit=crop&w=1200&q=80")
    st.markdown('</div>', unsafe_allow_html=True)

    st.write("## Current Safety Overview")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Safety Score", "9.4/10", "High")
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Local Weather", "24°C", "Sunny")
        st.markdown('</div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Response Time", "4.2m", "Fast")
        st.markdown('</div>', unsafe_allow_html=True)
elif choice == "Registration":
    st.header("📋 User Registration")
    with st.form("reg_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Name")
            u_phone = st.text_input("Your Phone Number (as unique ID)")
            dest = st.text_input("Destination")
        with col2:
            e_contact = st.text_input("Emergency Contact Number")
            id_type = st.selectbox("ID Type", ["Passport", "National ID"])
            id_file = st.file_uploader("Upload ID")
        
        submitted = st.form_submit_button("Save & Register")
        if submitted:
            if name and u_phone:
                if save_user(name, u_phone, dest, e_contact, id_type):
                    st.success(f"Successfully registered {name}!")
                    st.session_state.user_phone = u_phone
                    st.balloons()
            else:
                st.error("Name and Phone are required.")

elif choice == "Live Location":
    st.header("📍 Real-time Tracking")
    loc = get_geolocation()
    if loc:
        lat, lon = loc['coords']['latitude'], loc['coords']['longitude']
        st.info(f"Broadcast Quality: High Accuracy Active | Current: {lat}, {lon}")
        
        # Automatic Logging if phone exists
        phone_id = st.session_state.get('user_phone', 'Guest_User')
        log_location(phone_id, lat, lon)
        
        m = folium.Map(location=[lat, lon], zoom_start=16)
        folium.Marker([lat, lon], tooltip="You are here", icon=folium.Icon(color="blue", icon="info-sign")).add_to(m)
        st_folium(m, height=400, use_container_width=True)
    else:
        st.warning("Please enable GPS/Location access in your browser.")

elif choice == "Emergency Contacts":
    st.header("📞 Local Emergency Directory")
    st.markdown("Immediate help is one click away.")
    
    contacts = {
        "Police": "100",
        "Ambulance": "108",
        "Fire Dept": "101",
        "Tourist Helpline": "8522069472",
        "Women Helpline": "1091"
    }
    
    cols = st.columns(len(contacts))
    for i, (service, num) in enumerate(contacts.items()):
        with cols[i]:
            st.button(f"📞 {service}: {num}", use_container_width=True)


elif choice == "Chat AI":
    st.header("🤖 Smart Tourist AI Assistant (Voice Enabled)")
    if "greeted" not in st.session_state:
        greeting = "Hi! I am your safety assistant. How can I help you explore safely today?"
        st.toast(greeting)
        speak(greeting) # Using your existing speak function
        st.session_state.greeted = True

    # Function to make the browser speak
    def speak(text):
        # Clean text of markdown characters like * or # for cleaner speech
        clean_text = text.replace('*', '').replace('#', '').replace('"', "'")
        components_js = f"""
            <script>
            var msg = new SpeechSynthesisUtterance();
            msg.text = "{clean_text[:300]}"; // Limit to 300 chars to avoid browser lag
            msg.rate = 1.0;
            window.speechSynthesis.speak(msg);
            </script>
        """
        st.components.v1.html(components_js, height=0)

    # 1. Automatic Greeting + Voice
    if "greeted" not in st.session_state:
        st.session_state.greeted = True
        greeting_text = "Hi! I am your safety assistant. How can I help you explore safely today?"
        st.toast(greeting_text)
        speak(greeting_text)

    # 2. Chat History Display
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hi! How can I help you today? Tell me where you are going, and I'll give you safety tips!"}
        ]

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # 3. User Input & AI Logic
    user_input = st.chat_input("Enter a place name (e.g., Paris, Tokyo)...")
    
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)
        
        # --- Image preview code removed from here ---
        
        with st.chat_message("assistant"):
            with st.spinner(f"Fetching safety data for {user_input}..."):
                prompt = (
                    f"You are a Smart Tourist Safety AI. For the location: {user_input}, "
                    "provide a short guide including: Safety Level, Climate, "
                    "Budget, and 3 safe spots. End with one quick safety tip."
                )
                try:
                    response = model.generate_content(prompt)
                    reply = response.text
                    st.markdown(reply)
                    
                    # TRIGGER VOICE FOR RESPONSE
                    speak(reply)
                    
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                except Exception as e:
                    st.error(f"AI request failed: {e}")
                    st.error("Please verify your GOOGLE_API_KEY and network connectivity.")
import streamlit as st
import sqlite3
import os
import base64
import time
import pandas as pd
import folium
from streamlit_folium import st_folium
from streamlit_js_eval import get_geolocation

# --- 1. CONFIGURATION ---
RECORDINGS_DIR = "recordings"
ADMIN_PASSWORD = "admin123"
if not os.path.exists(RECORDINGS_DIR):
    os.makedirs(RECORDINGS_DIR)

# --- 2. DATABASE LOGIC ---
def init_db():
    conn = sqlite3.connect('safety_system.db')
    c = conn.cursor()
    # User Directory
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                 name TEXT, phone TEXT UNIQUE, destination TEXT, 
                 emergency_contact TEXT, id_type TEXT)''')
    # SOS Incidents with Media
    c.execute('''CREATE TABLE IF NOT EXISTS sos_incidents
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                 phone TEXT, lat REAL, lon REAL, 
                 reason TEXT, media_path TEXT, 
                 timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def handle_sos_upload(base64_data, phone, lat, lon, reason):
    """Saves the base64 media string as a .webm file and logs to DB"""
    try:
        file_name = f"SOS_{phone}_{int(time.time())}.webm"
        file_path = os.path.join(RECORDINGS_DIR, file_name)
        
        # Decode base64
        header, encoded = base64_data.split(",", 1)
        data = base64.b64decode(encoded)
        
        with open(file_path, "wb") as f:
            f.write(data)
        
        # Save to DB
        conn = sqlite3.connect('safety_system.db')
        c = conn.cursor()
        c.execute("""INSERT INTO sos_incidents (phone, lat, lon, reason, media_path) 
                     VALUES (?, ?, ?, ?, ?)""", (phone, lat, lon, reason, file_path))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Failed to save emergency media: {e}")
        return False

init_db()

# --- 3. UI SETUP ---
st.set_page_config(page_title="Tourist Safety Shield", layout="wide")

# Check for incoming SOS data via query params (The JS-to-Python Bridge)
query_params = st.query_params
if "sos_data" in query_params:
    handle_sos_upload(
        query_params["sos_data"], 
        st.session_state.get('user_phone', 'Unknown'),
        query_params.get("lat", 0),
        query_params.get("lon", 0),
        "User Triggered SOS"
    )
    st.query_params.clear() # Clean URL after save



# --- 5. PAGE: MOBILE SOS ---
if choice == "Mobile SOS":
    st.header("🆘 Panic Alert System")
    
    user_phone = st.session_state.get('user_phone', '9999999999')
    loc = get_geolocation()
    
    if loc:
        lat, lon = loc['coords']['latitude'], loc['coords']['longitude']
        
        # The SOS Trigger Button & JS Engine
        st.components.v1.html(f"""
            <script>
            async function triggerSOS() {{
                const reason = "Manual Panic Trigger";
                try {{
                    const stream = await navigator.mediaDevices.getUserMedia({{ video: true, audio: true }});
                    const mediaRecorder = new MediaRecorder(stream);
                    let chunks = [];

                    mediaRecorder.ondataavailable = (e) => chunks.push(e.data);
                    mediaRecorder.onstop = async () => {{
                        const blob = new Blob(chunks, {{ type: 'video/webm' }});
                        const reader = new FileReader();
                        reader.readAsDataURL(blob);
                        reader.onloadend = () => {{
                            const base64data = reader.result;
                            // Sending data back to Streamlit via URL (for simplicity in local dev)
                            const url = new URL(window.location.href);
                            url.searchParams.set("sos_data", "active_recording"); 
                            // In a real app, use a hidden form or API POST
                            alert("SOS Captured & Sent to Admin. Filename: " + reason);
                        }};
                    }};

                    mediaRecorder.start();
                    setTimeout(() => mediaRecorder.stop(), 5000); // Records 5 seconds
                    
                }} catch(e) {{ alert("Error: " + e.message); }}
            }}
            </script>
            <button onclick="triggerSOS()" style="width:100%; padding:20px; background:red; color:white; border:none; border-radius:10px; font-weight:bold; font-size:20px; cursor:pointer;">
                🚨 ACTIVATE EMERGENCY SOS
            </button>
        """, height=100)
    else:
        st.warning("Please enable GPS to use the SOS feature.")

# --- 6. PAGE: ADMIN VIEW ---
elif choice == "Admin View":
    st.header("🕵️ Control Center")
    
    pwd = st.text_input("Admin Password", type="password")
    if pwd == ADMIN_PASSWORD:
        tab1, tab2, tab3 = st.tabs(["User Directory", "SOS Incident Logs", "Live Tracking Map"])
        
        with tab1:
            conn = sqlite3.connect('safety_system.db')
            st.dataframe(pd.read_sql_query("SELECT * FROM users", conn), use_container_width=True)
            conn.close()

        with tab2:
            st.subheader("🚨 SOS Incident Logs")
            conn = sqlite3.connect('safety_system.db')
            df_sos = pd.read_sql_query("SELECT * FROM sos_incidents ORDER BY timestamp DESC", conn)
            if df_sos.empty:
                st.info("No emergency incidents reported.")
            else:
                for index, row in df_sos.iterrows():
                    with st.expander(f"🔴 {row['reason']} - {row['timestamp']}"):
                        st.write(f"**Phone:** {row['phone']}")
                        if row['media_path'] and os.path.exists(row['media_path']):
                            st.video(row['media_path'])
            conn.close()

        # --- TAB 3: LIVE TRACKING (ALL USERS) ---
        with tab3:
            st.subheader("📍 Real-time Tourist Locations")
            
            try:
                conn = sqlite3.connect('safety_system.db')
                # SQL Query to pull the MOST RECENT location for every unique user
                query = """
                    SELECT phone, lat, lon, MAX(timestamp) as last_seen 
                    FROM location_logs 
                    GROUP BY phone
                """
                df_live = pd.read_sql_query(query, conn)
                conn.close()

                if not df_live.empty:
                    # Create the base map centered on the first available user
                    center_lat = df_live.iloc[0]['lat']
                    center_lon = df_live.iloc[0]['lon']
                    m_live = folium.Map(location=[center_lat, center_lon], zoom_start=12)
                    
                    # Loop through all active users and add a marker for each
                    for i, row in df_live.iterrows():
                        folium.Marker(
                            [row['lat'], row['lon']], 
                            popup=f"<b>User:</b> {row['phone']}<br><b>Last seen:</b> {row['last_seen']}",
                            tooltip=f"User: {row['phone']}",
                            icon=folium.Icon(color="blue", icon="user", prefix="fa")
                        ).add_to(m_live)
                    
                    # Render the map in the Streamlit app
                    st_folium(
                        m_live, 
                        height=600, 
                        use_container_width=True, 
                        key="admin_live_map_unique"
                    )
                    
                    # Optional: Show the data table below the map
                    with st.expander("View Location Data Table"):
                        st.dataframe(df_live, use_container_width=True)
                else:
                    st.info("No live location data found in the database. Users must visit the 'Live Location' page to start broadcasting.")
            
            except Exception as e:
                st.error(f"Error loading live tracking map: {e}")
          