DB_PATH = "users_db.db"
import streamlit as st
from streamlit_option_menu import option_menu
from PIL import Image
import os, base64
import json
import time
from streamlit_autorefresh import st_autorefresh
from streamlit_javascript import st_javascript

def dislay_tilte():
    st.markdown("""
        <style>
        .main-header {
            font-size: 25px;
            font-weight: 800;
            color: #003366;
            text-align: center;
            font-family: 'Segoe UI', sans-serif;
            background: linear-gradient(90deg, #e0f7fa 0%, #ffffff 100%);
            padding: 20px 10px;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
        }

        @media screen and (max-width: 768px) {
            .main-header {
                font-size: 18px;
                padding: 15px 5px;
            }
        }
        </style> <div class="main-header">🌱 Learn about the common Mental Health challenges that affect students  </div>
    """, unsafe_allow_html=True)
    
def set_full_page_background(image_path):
    try:
        if not os.path.exists(image_path):
            st.error(f"Image file '{image_path}' not found.")
            return

        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()

        st.markdown(
            f"""
            <style>
            [data-testid="stApp"] {{
                background-image: url("data:image/jpg;base64,{encoded_string}");
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
                background-attachment: fixed;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )
    except Exception as e:
        st.error(f"Error setting background: {e}")

##### DRIVER CODE ########
def main():
    device_width = st_javascript("window.innerWidth", key="scren_widith")
    if device_width is None:
        st.stop()
    is_mobile = device_width < 704
    set_full_page_background('images/dark_green_back.jpg')
    dislay_tilte()
    
    with open("mental_health_conditions_complete.json", "r") as f:
        conditions = json.load(f)

    def format_items(data, key):
        items = data.get(key, [])
        if isinstance(items, list):
            return "<br>".join([f"• {item}" for item in items])
        elif isinstance(items, str) and items.strip():
            return f"• {items}"
        else:
            return ""

    if not is_mobile:
        for condition, data in conditions.items():
            with st.expander(f"{condition}", expanded=True):
                col1, col2 = st.columns([1.5, 2])

                with col1:
                    st.image(data["image"], use_column_width=True)

                with col2:
                    st.markdown(f"### :blue[{condition}]")
                    # st.write(f"###### ***{data['intro']}***")
                    
                    st.markdown(f"""
                        <div style="background-color: #f3f8fb; padding: 15px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); margin-top: 10px; font-family: 'Segoe UI', sans-serif;">
                        
                        <details style="margin-bottom: 10px;">
                            <summary style="font-weight: bold; font-size: 20px; color:#1b4f72; cursor: pointer;">
                                'What is {condition} ?'
                            </summary>
                            <p style="margin-left: 15px; color: #444; font-size:18px;">{format_items(data, 'intro')}</p>
                        </details>




                        <details style="margin-bottom: 10px;">
                            <summary style="font-weight: bold; font-size: 20px; color:#1b4f72; cursor: pointer;">
                                📊 Prevalence of {condition} among students
                            </summary>
                            <p style="margin-left: 15px; color: #444;font-size:18px;">{format_items(data, 'prevalence')}</p>
                        </details>

                        <details style="margin-bottom: 10px;">
                            <summary style="font-weight: bold; font-size: 20px; color:#1b4f72; cursor: pointer;">
                                ⚠️ Common Causes of {condition}
                            </summary>
                            <p style="margin-left: 15px; color: #444;font-size:18px;">{format_items(data, 'causes')}</p>
                        </details>

                       
                        <details style="margin-bottom: 10px;">
                            <summary style="font-weight: bold; font-size: 20px; color:#1b4f72; cursor: pointer;">
                                🩺 Signs and Symptoms of {condition}
                            </summary>
                            <p style="margin-left: 15px; color: #444;font-size:18px;">{format_items(data, 'symptoms')}</p>
                        </details>


                        </div>
                    """, unsafe_allow_html=True)

                    st.markdown(f"""
                        <a href="{data['learn_more_link']}" target="_blank">
                            <button style='margin-top: 15px; background-color: #0072CE; color: white; padding: 8px 16px; border: none; border-radius: 6px; cursor: pointer;'>
                                Learn More →
                            </button>
                        </a>
                    """, unsafe_allow_html=True)
                with col1:
                    # st.markdown(f"### :blue[{condition}]")
                    # st.write(f"###### ***{data['intro']}***")
                    
                    st.markdown(f"""
                        <div style="background-color: #f3f8fb; padding: 15px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); margin-top: 10px; font-family: 'Segoe UI', sans-serif;">

                        <details style="margin-bottom: 10px;">
                            <summary style="font-weight: bold; font-size: 20px; color:#1b4f72; cursor: pointer;">
                                🛡️ How to Prevent {condition}
                            </summary>
                            <p style="margin-left: 15px; color: #444;font-size:18px;">{format_items(data, 'prevention')}</p>
                        </details>

                        <details style="margin-bottom: 10px;">
                            <summary style="font-weight: bold; font-size: 20px; color:#1b4f72; cursor: pointer;">
                                🧘 How to Cope with {condition}
                            </summary>
                            <p style="margin-left: 15px; color: #444;font-size:18px;">{format_items(data, 'management')}</p>
                        </details>


                        </div>
                    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
