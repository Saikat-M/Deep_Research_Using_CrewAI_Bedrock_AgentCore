import os
import streamlit as st
import requests
# from datetime import datetime
import time
import json
from src.deep_research.crew import DeepResearch

# ----------------------------------------
# REQUIRED: Disable CrewAI telemetry
# ----------------------------------------
os.environ["CREWAI_TELEMETRY_DISABLED"] = "true"

st.set_page_config(page_title="AI Deep Research Agent", page_icon="📚", layout="wide")

# ----------------------------------------
# CSS Styling
# ----------------------------------------
st.markdown("""
<style>
.main-header {
    background: linear-gradient(90deg, #6A11CB, #2575FC);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 3rem;
    font-weight: bold;
    text-align: center;
}
.subtitle {
    color: #666;
    text-align: center;
    font-size: 1.2rem;
    margin-bottom: 2rem;
}
.research-container {
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    padding: 2rem;
    border-radius: 15px;
    margin: 1rem 0;
    box-shadow: 0 8px 25px rgba(0,0,0,0.1);
            
    width: 95%;          /* 👈 wider container */
    max-width: 1400px;   /* 👈 cap width for readability */
}
</style>
""", unsafe_allow_html=True)

# ----------------------------------------
# Header
# ----------------------------------------
st.markdown('<h1 class="main-header">📚 Deep Research Agent Using CrewAI and AgentCore</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="subtitle">Conduct structured, multi-step deep research and generate high-quality reports</p>',
    unsafe_allow_html=True
)

# ----------------------------------------
# Initialize Session State
# ----------------------------------------
if "report_content" not in st.session_state:
    st.session_state.report_content = None
if "report_topic" not in st.session_state:
    st.session_state.report_topic = None

# ----------------------------------------
# Input Form
# ----------------------------------------
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    with st.form("research_form"):
        topic = st.text_input(
            "Enter a research topic",
            placeholder="e.g., Impact of Generative AI on Healthcare",
            help="Enter any topic for deep research"
        )
        submitted = st.form_submit_button(
            "🚀 Run Deep Research",
            type="primary",
            use_container_width=True
        )

API_URL = "https://ncez2dc06j.execute-api.us-east-1.amazonaws.com/dev/deep_research"

# ----------------------------------------
# Run Research (ONLY when submitted)
# ----------------------------------------
if submitted and topic:
    with st.spinner("🔬 Conducting deep research... This may take a few minutes."):
        try:
            response = requests.post(API_URL, json={"prompt": topic})

            if response.status_code == 202:
                data = response.json()
                session_id = data.get("session_id")
                
                if not session_id:
                    st.error("❌ No session ID received from API")
                else:
                    st.info(f"🔄 Research started. Session ID: {session_id}")
                    
                    # Create placeholders for status updates
                    status_placeholder = st.empty()
                    progress_placeholder = st.empty()
                    
                    # Poll until done
                    result = None
                    max_attempts = 60  # 5 minutes with 5-second intervals
                    
                    for attempt in range(max_attempts):
                        try:
                            # Check status
                            poll_response = requests.get(API_URL, params={"session_id": session_id}, timeout=10)
                            
                            if poll_response.status_code == 200:
                                poll_data = poll_response.json()
                                status = poll_data.get("status")
                                message = poll_data.get("message", "Processing...")
                                
                                # Update status display
                                with status_placeholder.container():
                                    if status == "PENDING":
                                        st.info(f"⏳ {message}")
                                    elif status == "PROCESSING":
                                        st.info(f"🔄 {message}")
                                    elif status == "DONE":
                                        st.success(f"✅ {message}")
                                    elif status == "ERROR":
                                        st.error(f"❌ {message}")
                                
                                # Update progress
                                progress = min((attempt + 1) / max_attempts * 100, 95)
                                progress_placeholder.progress(int(progress))
                                
                                if status == "DONE":
                                    result = poll_data.get("result")
                                    break
                                elif status == "ERROR":
                                    st.error(f"❌ Research failed: {message}")
                                    break
                                    
                            else:
                                st.warning(f"Status check failed: {poll_response.status_code}")
                            
                            # Wait before next poll
                            time.sleep(5)
                            
                        except requests.exceptions.Timeout:
                            st.warning(f"Status check timeout (attempt {attempt + 1})")
                            time.sleep(5)
                        except Exception as e:
                            st.warning(f"Status check error: {str(e)}")
                            time.sleep(5)
                    
                    # Clear status displays
                    status_placeholder.empty()
                    progress_placeholder.empty()
                    
                    if result:
                        st.balloons()
                        st.success("🎉 Research complete!")

                        # Extract string content if result is a dict
                        if isinstance(result, dict):
                            result = result.get("result", str(result))
                        
                        # Store in session state
                        st.session_state.report_content = result
                        st.session_state.report_topic = topic
                    else:
                        st.error("❌ Research timed out or failed.")
            else:
                st.error(f"❌ API Error: {response.status_code} - {response.text}")

        except requests.exceptions.Timeout:
            st.error("❌ Request timeout. Please try again.")
        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")

elif submitted:
    st.warning("⚠️ Please enter a research topic to begin!")

# ----------------------------------------
# Persistent Report Display (KEY FIX)
# ----------------------------------------
if st.session_state.report_content:
    st.markdown('<div class="research-container">', unsafe_allow_html=True)
    st.markdown(f"## 📄 Research Report: {st.session_state.report_topic}")
    st.markdown(st.session_state.report_content)
    st.markdown('</div>', unsafe_allow_html=True)

    st.download_button(
        label="💾 Download Research Report",
        data=st.session_state.report_content,
        file_name=f"{st.session_state.report_topic.replace(' ', '_')}_research_report.md",
        mime="text/markdown"
    )

# ----------------------------------------
# Sidebar
# ----------------------------------------
with st.sidebar:
    st.markdown("### 🧠 How The App Works")

    features = [
        ("📑 Research Planning", "Breaks the topic into structured research steps"),
        ("🌐 Evidence Gathering", "Collects data from multiple sources"),
        ("✅ Verification", "Checks credibility and reduces hallucinations"),
        ("✍️ Report Writing", "Produces a clear, well-structured final report")
    ]

    for title, desc in features:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 1rem; border-radius: 10px; margin: 0.5rem 0;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <p style="color: white; margin: 0; font-weight: bold;">{title}</p>
            <p style="color: rgba(255,255,255,0.9); margin: 0; font-size: 0.9rem;">{desc}</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")