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
            font-size: 40px;
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
                font-size: 28px;
                padding: 15px 5px;
            }
        }
        </style>

        <div class="main-header">🌱 School Mental Health & Psychosocial Support</div>
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
   with open("self_help_techniques.json", "r") as f:
      techniques = json.load(f)

      def format_items(data, key):
         items = data.get(key, [])
         if isinstance(items, list):
             return "<br>".join([f"• {item}" for item in items])
         elif isinstance(items, str) and items.strip():
             return f"• {items}"
         else:
             return ""

      if not is_mobile:
         for technique, data in techniques.items():
             with st.expander(f"{technique}", expanded=True):
                 st.markdown(f"### :blue[{technique}]")
                 col1, col2 = st.columns([2, 2])

                 with col1:
                     st.image(data["image"], use_column_width=True)

                 with col2:
                     # st.markdown(f"### :blue[{technique}]")
                     # st.write(data["description"].get("definition", ""))

                     st.markdown(f"""
                         <div style="background-color: #f3f8fb; padding: 15px; border-radius: 10px; 
                                     box-shadow: 0 2px 8px rgba(0,0,0,0.05); margin-top: 10px; 
                                     font-family: 'Segoe UI', sans-serif;">
                         


                         <details style="margin-bottom: 10px;">
                             <summary style="font-weight: bold; font-size: 20px; color:#1b4f72; cursor: pointer;">
                                 🔍 What is {technique} ?
                             </summary>
                             <p style="margin-left: 15px; color: #444; font-size: 18px">
                                 {data['description'].get('definition', '')}
                             </p>
                         </details>
                         

                         <details style="margin-bottom: 10px;">
                             <summary style="font-weight: bold; font-size: 20px; color:#1b4f72; cursor: pointer;">
                                 🔍 Why is {technique} effective?
                             </summary>
                             <p style="margin-left: 15px; color: #444;font-size: 18px">
                                 {data['description'].get('evidence', '')}
                             </p>
                         </details>

                         <details style="margin-bottom: 10px;">
                             <summary style="font-weight: bold; font-size: 20px; color:#1b4f72; cursor: pointer;">
                                 📝 How to practice {technique} step by step?
                             </summary>
                             <p style="margin-left: 15px; color: #444;font-size: 18px">
                                 {format_items(data['description'], 'steps')}
                             </p>
                         </details>

                         </div>
                     """, unsafe_allow_html=True)

                 with col1:
                     # st.markdown(f"### :blue[{technique}]")
                     # # st.write(data["description"].get("definition", ""))

                     st.markdown(f"""
                         <div style="background-color: #f3f8fb; padding: 15px; border-radius: 10px; 
                                     box-shadow: 0 2px 8px rgba(0,0,0,0.05); margin-top: 10px; 
                                     font-family: 'Segoe UI', sans-serif;">
                         

                         

                         <details style="margin-bottom: 10px;">
                             <summary style="font-weight: bold; font-size: 20px; color:#1b4f72; cursor: pointer;">
                                 📚 Example of using {technique} in school life
                             </summary>
                             <p style="margin-left: 15px; color: #444;font-size: 18px">
                                 {data['description'].get('example', '')}
                             </p>
                         </details>

                         </div>
                     """, unsafe_allow_html=True)

      

if __name__ == "__main__":
   main()