DB_PATH = "users_db.db"

import streamlit as st
from PIL import Image
from streamlit_option_menu import option_menu
import os, base64
from streamlit_option_menu import option_menu
import auth 
import sqlite3
import time
from streamlit_javascript import st_javascript
import uuid

def set_full_page_background(image_path):
    try:
        if not os.path.exists(image_path):
            st.error(f"Image file '{image_path}' not found.")
            return

        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()

        st.markdown(f"""
            <style>
            [data-testid="stApp"] {{
                background-image: url("data:image/jpg;base64,{encoded_string}");
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
                background-attachment: fixed;
            }}
            </style>
            """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error setting background: {e}")


@st.dialog("💬 Anonymous Feedback")
def feedback_dialog():
    st.markdown("""
        <h4 style='color:#0d47a1;font-size:20px;'>We're here to listen.</h4>
        <p style='font-size:20px;background-color:#1b4f72;'>Your thoughts help build a better mental health experience for everyone.</p>
    """, unsafe_allow_html=True)

    feedback = st.text_area("Your message:", height=200, placeholder="I feel...")

    if st.button("✅ Submit"):
        if feedback.strip():
            st.session_state["feedback_response"] = feedback
            st.success("Thank you for your feedback 💚")
            st.rerun()
        else:
            st.warning("Please enter your thoughts before submitting.")


def display_coming_soon(role="User"):
    with st.spinner("Loading resources..."):
        time.sleep(1) 
    st.markdown(f"""
        <div style='text-align: center; margin-top: 100px;'>
            <h2 style='color: #ff6f61;'>Resources for {role} Coming Soon...</h2>
            <p style='font-size: 18px;'>We're working hard to bring you the best mental health support resources tailored for {role.lower()}s.</p>
        </div>
    """, unsafe_allow_html=True)

    if st.button("⬅ Back to Home"):
        st.rerun()

def get_device_type(width):
    if width is None:
        return "desktop"
    return "mobile" if width < 704 else "desktop"

screen_width = st_javascript("window.innerWidth")
device_type = get_device_type(screen_width)
# def js_slider(images, quotes, device_type="desktop", target_page=None, role="Resources"):
#     slide_height = "100vh" if device_type == "desktop" else "50px"
#     overlay_font_size = "2.2em" if device_type == "desktop" else "1.0em"
#     button_font_size = "20px" if device_type == "desktop" else "14px"
#     rendered_height = 600 if device_type == "desktop" else 100

#     slider_id = f"slider_{uuid.uuid4().hex}"

#     # Convert images to base64
#     image_data = []
#     for img_path in images:
#         if not os.path.exists(img_path):
#             st.error(f"Image not found: {img_path}")
#             return
#         with open(img_path, "rb") as img_file:
#             b64_img = base64.b64encode(img_file.read()).decode()
#             image_data.append(f"data:image/jpeg;base64,{b64_img}")

#     # Build slides HTML
#     slides_html = ""
#     for i in range(len(images)):
#         slides_html += f"""
#         <div class="mySlide fade" style="display:none; width: 100%; position: absolute;">
#             <div class="hero" style="
#                 background-image: url('{image_data[i]}');
#                 height: {slide_height};
#                 border-radius: 5px;
#                 box-shadow: 0 4px 10px rgba(0,0,0,0.4);
#                 display: flex;
#                 flex-direction: column;
#                 justify-content: center;
#                 align-items: center;
#                 text-align: center;
#                 color: orange;
#                 font-family: 'Segoe UI', sans-serif;
#                 font-style: italic;
#                 background-size: cover;
#                 background-position: center;
#             ">
#                 <div class="overlay-text" style="
#                     font-size: {overlay_font_size};
#                     font-weight: 600;
#                     text-shadow: 2px 2px 6px black;
#                     margin-bottom: 20px;
#                 ">{quotes[i]}</div>
#                 <div class="button-group" style="
#                     display: flex;
#                     flex-direction: column;
#                     gap: 10px;
#                     align-items: center;
#                 ">
#                     <button type="button" style="
#                         background-color: red;
#                         color: white;
#                         padding: 12px 28px;
#                         border-radius: 25px;
#                         border: none;
#                         font-size: {button_font_size};
#                         font-weight: bold;
#                         box-shadow: 0 3px 8px rgba(0, 0, 0, 0.2);
#                         cursor: pointer;
#                         transition: all 0.3s ease;
#                     " 
#                     onmouseover="this.style.backgroundColor='skyblue';" 
#                     onmouseout="this.style.backgroundColor='red';"
#                     onclick="window.parent.postMessage({{func:'navigate', page:'{target_page}'}}, '*');"
#                     >
#                         Explore Mental Health Resources for {role}
#                     </button>
#                 </div>
#             </div>
#         </div>
#         """

#     html_code = f"""
#     <style>
#     .slideshow-container {{
#         position: relative;
#         max-width: 100%;
#         margin: auto;
#         border: 2px solid #ddd;
#         border-radius: 8px;
#         padding: 5px;
#         overflow: hidden;
#         height: {slide_height};
#     }}

#     .fade {{
#         opacity: 0;
#         transition: opacity 0.5s ease-in-out;
#     }}

#     .mySlide.show {{
#         opacity: 1;
#         z-index: 1;
#     }}

#     .prev, .next {{
#         cursor: pointer;
#         position: absolute;
#         top: 50%;
#         width: auto;
#         padding: 16px;
#         margin-top: -22px;
#         color: white;
#         font-weight: bold;
#         font-size: 24px;
#         border-radius: 0 3px 3px 0;
#         user-select: none;
#         background-color: rgba(0,0,0,0.4);
#         transition: background-color 0.3s ease;
#         z-index: 1000;
#     }}

#     .prev:hover, .next:hover {{
#         background-color: rgba(0,0,0,0.7);
#     }}

#     .prev {{ left: 0; border-radius: 3px 0 0 3px; }}
#     .next {{ right: 0; border-radius: 0 3px 3px 0; }}
#     </style>

#     <div class="slideshow-container" id="{slider_id}">
#         {slides_html}
#         <a class="prev">&#10094;</a>
#         <a class="next">&#10095;</a>
#     </div>

#     <script>
#     var slides = document.querySelectorAll("#{slider_id} .mySlide");
#     var prev = document.querySelector("#{slider_id} .prev");
#     var next = document.querySelector("#{slider_id} .next");
#     var slideIndex = 0;
#     var autoSlideTimeout;

#     function showSlide(n) {{
#         slideIndex = (n + slides.length) % slides.length;
#         for (var i = 0; i < slides.length; i++) {{
#             slides[i].classList.remove("show");
#         }}
#         slides[slideIndex].style.display = "block";
#         void slides[slideIndex].offsetWidth; // trigger reflow
#         slides[slideIndex].classList.add("show");

#         for (let i = 0; i < slides.length; i++) {{
#             if (i !== slideIndex) {{
#                 setTimeout((index => () => {{
#                     slides[index].style.display = "none";
#                 }})(i), 1000); // match fade duration
#             }}
#         }}
#     }}

#     function nextSlide() {{
#         showSlide(slideIndex + 1);
#         resetAutoSlide();
#     }}

#     function prevSlide() {{
#         showSlide(slideIndex - 1);
#         resetAutoSlide();
#     }}

#     function autoSlide() {{
#         showSlide(slideIndex + 1);
#         autoSlideTimeout = setTimeout(autoSlide, 5000);
#     }}

#     function resetAutoSlide() {{
#         clearTimeout(autoSlideTimeout);
#         autoSlideTimeout = setTimeout(autoSlide, 300000);
#     }}

#     prev.addEventListener("click", prevSlide);
#     next.addEventListener("click", nextSlide);

#     showSlide(slideIndex);
#     autoSlideTimeout = setTimeout(autoSlide, 5000);
#     </script>
#     """

#     st.components.v1.html(html_code, height=rendered_height)

def js_slider(images, quotes, device_type="desktop", target_page=None, role="Resources"):
    slide_height = "100vh" if device_type == "desktop" else "50px"
    overlay_font_size = "2.2em" if device_type == "desktop" else "1.0em"
    button_font_size = "20px" if device_type == "desktop" else "14px"
    rendered_height = 600 if device_type == "desktop" else 100

    slider_id = f"slider_{uuid.uuid4().hex}"

    # Convert images to base64
    image_data = []
    for img_path in images:
        if not os.path.exists(img_path):
            st.error(f"Image not found: {img_path}")
            return
        with open(img_path, "rb") as img_file:
            b64_img = base64.b64encode(img_file.read()).decode()
            image_data.append(f"data:image/jpeg;base64,{b64_img}")

    # Build slides HTML
    slides_html = ""
    for i in range(len(images)):
        slides_html += f"""
        <div class="mySlide" style="display:none; width: 100%; position: absolute;">
            <div class="hero" style="
                background-image: url('{image_data[i]}');
                height: {slide_height};
                border-radius: 5px;
                box-shadow: 0 4px 10px rgba(0,0,0,0.4);
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                text-align: center;
                color: orange;
                font-family: 'Segoe UI', sans-serif;
                font-style: italic;
                background-size: cover;
                background-position: center;
            ">
                <div class="overlay-text" style="
                    font-size: {overlay_font_size};
                    font-weight: 600;
                    text-shadow: 2px 2px 6px black;
                    margin-bottom: 20px;
                ">{quotes[i]}</div>
                <div class="button-group" style="
                    display: flex;
                    flex-direction: column;
                    gap: 10px;
                    align-items: center;
                ">
                    <button type="button" style="
                        background-color: red;
                        color: white;
                        padding: 12px 28px;
                        border-radius: 25px;
                        border: none;
                        font-size: {button_font_size};
                        font-weight: bold;
                        box-shadow: 0 3px 8px rgba(0, 0, 0, 0.2);
                        cursor: pointer;
                        transition: all 0.3s ease;
                    " 
                    onmouseover="this.style.backgroundColor='skyblue';" 
                    onmouseout="this.style.backgroundColor='red';"
                    onclick="window.parent.postMessage({{func:'navigate', page:'{target_page}'}}, '*');"
                    >
                        Explore Mental Health Resources for {role}
                    </button>
                </div>
            </div>
        </div>
        """

    html_code = f"""
    <style>
    .slideshow-container {{
        position: relative;
        max-width: 100%;
        margin: auto;
        border: 2px solid #ddd;
        border-radius: 8px;
        padding: 5px;
        overflow: hidden;
        height: {slide_height};
    }}

    /* No fade animation */
    .mySlide {{
        opacity: 1 !important;
        transition: none !important;
    }}

    .prev, .next {{
        cursor: pointer;
        position: absolute;
        top: 50%;
        width: auto;
        padding: 16px;
        margin-top: -22px;
        color: white;
        font-weight: bold;
        font-size: 24px;
        border-radius: 0 3px 3px 0;
        user-select: none;
        background-color: rgba(0,0,0,0.4);
        transition: background-color 0.3s ease;
        z-index: 1000;
    }}

    .prev:hover, .next:hover {{
        background-color: rgba(0,0,0,0.7);
    }}

    .prev {{ left: 0; border-radius: 3px 0 0 3px; }}
    .next {{ right: 0; border-radius: 0 3px 3px 0; }}
    </style>

    <div class="slideshow-container" id="{slider_id}">
        {slides_html}
        <a class="prev">&#10094;</a>
        <a class="next">&#10095;</a>
    </div>

    <script>
    var slides = document.querySelectorAll("#{slider_id} .mySlide");
    var prev = document.querySelector("#{slider_id} .prev");
    var next = document.querySelector("#{slider_id} .next");
    var slideIndex = 0;
    var autoSlideTimeout;

    function showSlide(n) {{
        slideIndex = (n + slides.length) % slides.length;
        for (var i = 0; i < slides.length; i++) {{
            slides[i].style.display = "none";
        }}
        slides[slideIndex].style.display = "block";
    }}

    function nextSlide() {{
        showSlide(slideIndex + 1);
        resetAutoSlide();
    }}

    function prevSlide() {{
        showSlide(slideIndex - 1);
        resetAutoSlide();
    }}

    function autoSlide() {{
        showSlide(slideIndex + 1);
        autoSlideTimeout = setTimeout(autoSlide, 300000); // 5 minutes
    }}

    function resetAutoSlide() {{
        clearTimeout(autoSlideTimeout);
        autoSlideTimeout = setTimeout(autoSlide, 300000); // restart 5 min timer
    }}

    prev.addEventListener("click", prevSlide);
    next.addEventListener("click", nextSlide);

    showSlide(slideIndex);
    autoSlideTimeout = setTimeout(autoSlide, 300000); // start 5 min interval
    </script>
    """

    st.components.v1.html(html_code, height=rendered_height)

def set_default_page():
    if "current_page" not in st.session_state:
        st.session_state.current_page = "home"


def display_coming_soon(role):
    st.write(f"Resources page for {role} coming soon...")



def home_page():
    device_type = "desktop"  

    margin_right = "300px" if device_type == "desktop" else "0"
    
    font_css = f"""
    <style>
    /* Default tab appearance */
    button[data-baseweb="tab"] > div[data-testid="stMarkdownContainer"] > p {{
      font-size: 16px;
      font-weight: bold;
      color: white;
      padding: 4px 10px;
      margin: 0;
      border: 2px solid brown;
      border-radius: 3%;
      background-color: orange;
      box-sizing: border-box;
      transition: all 0.3s ease-in-out;
    }}

    /* Active tab: make it green */
    button[data-baseweb="tab"][aria-selected="true"] > div[data-testid="stMarkdownContainer"] > p {{
      background-color: green !important;
      border-color: darkgreen !important;
      color: white !important;
    }}

    /* Add spacing between tabs */
    div[role="tablist"] > button {{
      margin-right: {margin_right};
    }}

    /* Content area of each tab */
    section[role="tabpanel"] {{
      padding: 16px 24px;
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      font-size: 18px;
      color: #333333;
    }}

    /* Style tables */
    section[role="tabpanel"] table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 2px;
    }}

    section[role="tabpanel"] th, section[role="tabpanel"] td {{
      border: 1px solid #ddd;
      padding: 8px;
    }}

    section[role="tabpanel"] th {{
      background-color: #00897b;
      color: red;
      text-align: left;
    }}
    </style>
    """
    
    st.markdown(font_css, unsafe_allow_html=True)
    
    section = st.tabs(["Students", "Teachers", "Parents"])

    with section[0]:
        student_images = ['images/std.jpg', 'images/std3.jpg', 'images/student1.jpg']
        student_quotes = [
            "Your mind matters as much as your grades.",
            "Strong minds ask for help. That’s real strength.",
            "Healthy minds. Safe spaces. Stronger schools."]
        js_slider(student_images, student_quotes, target_page="students", role="Students")

    with section[1]:
        teacher_images = ['images/teacher1.jpg','images/teacher.jpg',  'images/teacher4.jpg']
        teacher_quotes = [
            "Even Teachers get overwhelmed, Support your students by supporting yourself.",
            "A healthy mind creates a healthy classroom.",
            "Strong teachers build stronger communities."]
        js_slider(teacher_images, teacher_quotes, target_page="teachers", role="Teachers")

    with section[2]:
        parent_images = ['images/family.png', 'images/psy4.jpg', 'images/parent1.jpg']
        parent_quotes = [
            "Your child's mental health starts with a caring home.",
            "Listening is the first step to supporting your child.",
            "Together, we can create a safe environment for your family."]
        js_slider(parent_images, parent_quotes, target_page="parents", role="Parents")


def display_coming_soon(role):
    st.markdown(f"""
    <div style="text-align: center; margin-top: 100px;">
        <h2>Resources page for {role} coming soon...</h2>
        <br>
        <button onclick="window.parent.postMessage({{func:'navigate', page:'home'}}, '*')" 
                style="
                    background-color: green;
                    color: white;
                    padding: 12px 28px;
                    border-radius: 25px;
                    border: none;
                    font-size: 16px;
                    font-weight: bold;
                    box-shadow: 0 3px 8px rgba(0, 0, 0, 0.2);
                    cursor: pointer;
                    transition: all 0.3s ease;
                ">
            ⬅ Back to Home
        </button>
    </div>
    """, unsafe_allow_html=True)

# def main():
#     set_default_page()

#     current_page = st.session_state.current_page

#     # Header is shown only on home page
#     if current_page == "home":
#         st.markdown("""
#         <div style="
#             background: linear-gradient(to right, #b2dfdb, #e1bee7);
#             padding: 50px;
#             text-align: center;
#             color: #2c3e50;
#             font-size: 30px;
#             font-weight: bold;
#             border-radius: 10px;
#             box-shadow: 0 4px 12px rgba(0,0,0,0.1);
#             font-family: 'Segoe UI', sans-serif;
#         ">
#             🧠 Mental Health Hub for Students, Teachers & Parents
#             <br>
#             <span style="font-size: 18px; font-weight: normal;">
#                 A safe space to connect, understand your feelings, and seek help with compassion and care.
#             </span>
#         </div>
#         """, unsafe_allow_html=True)

#     # Listen for navigation events from JS iframe slider button
#     msg = st_javascript("""
#     window.addEventListener('message', event => {
#         if(event.data.func === 'navigate'){
#             window.streamlitWebsocket.emit('navigate', event.data.page);
#         }
#     });
#     """)

#     if msg and msg.get('type') == 'event' and msg.get('event') == 'navigate':
#         new_page = msg.get('data')
#         if new_page in ['home', 'parents', 'students', 'teachers']:
#             st.session_state.current_page = new_page
#             st.rerun()

#     # Render the correct page
#     if current_page == "home":
#         home_page()
#     elif current_page == "parents":
#         display_coming_soon(role="Parents")
#     elif current_page == "students":
#         display_coming_soon(role="Students")
#     elif current_page == "teachers":
#         display_coming_soon(role="Teachers")
def main():
    set_default_page()

    current_page = st.session_state.current_page

    # JavaScript listener to capture message from iframe and update Streamlit state
    msg = st_javascript("""
    window.addEventListener('message', event => {
        if(event.data.func === 'navigate'){
            window.streamlitWebsocket.emit('navigate', event.data.page);
        }
    });
    """)

    if msg and msg.get('type') == 'event' and msg.get('event') == 'navigate':
        new_page = msg.get('data')
        if new_page in ['home', 'parents', 'students', 'teachers']:
            st.session_state.current_page = new_page
            st.rerun()

    # Conditional rendering of pages
    if current_page == "home":
        st.markdown("""
        <div style="
            background: linear-gradient(to right, #b2dfdb, #e1bee7);
            padding: 50px;
            text-align: center;
            color: #2c3e50;
            font-size: 30px;
            font-weight: bold;
            border-radius: 10px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            font-family: 'Segoe UI', sans-serif;
        ">
            🧠 Mental Health Hub for Students, Teachers & Parents
            <br>
            <span style="font-size: 18px; font-weight: normal;">
                A safe space to connect, understand your feelings, and seek help with compassion and care.
            </span>
        </div>
        """, unsafe_allow_html=True)
        home_page()

    elif current_page == "parents":
        display_coming_soon(role="Parents")
    elif current_page == "students":
        display_coming_soon(role="Students")
    elif current_page == "teachers":
        display_coming_soon(role="Teachers")


if __name__ == "__main__":
    main()
