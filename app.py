import streamlit as st
import google.generativeai as genai
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time 

# Configure API key
os.environ["API_KEY"] = "AIzaSyAlzvE1sWUf_Ivlr3pfaEMW6wV_7PIRCVA"
genai.configure(api_key=os.environ["API_KEY"])

class Course:
    def __init__(self, title, rating, reviews, level, duration, link):
        self.title = title
        self.rating = rating
        self.reviews = reviews
        self.level = level
        self.duration = duration
        self.link = link

    def to_dict(self):
        return {
            "title": self.title,
            "rating": self.rating,
            "reviews": self.reviews,
            "level": self.level,
            "duration": self.duration,
            "link": self.link
        }

def extract_keywords(user_input):
    """Extract keywords from user input using Gemini"""
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = (
        "Extract topics from the following user input to query Coursera search and display only the topics. "
        "The format should be: (all the topics separated by commas). For example, input: I want to learn machine learning and python. Output: machine learning, python. "
        "Here is the input: " + user_input
    )
    response = model.generate_content(prompt)
    if response and response.text:
        keywords = response.text.strip()  # Ensure no extra spaces or newlines
        return keywords.replace(",", " ")  # Replace commas with spaces for URL compatibility
    return ""


# def fetch_courses(keywords, max_scroll=3):
#     """Fetch courses from Coursera"""
#     driver = webdriver.Chrome()
#     search_query = "+".join(keywords.split())  # Convert spaces to '+' for URL
#     driver.get(f"https://www.coursera.org/search?query={search_query}")
    
#     try:
#         WebDriverWait(driver, 20).until(
#             EC.presence_of_all_elements_located((By.XPATH, "//div[@data-testid='product-card-cds']"))
#         )

#         # Scroll to load more courses
#         for _ in range(max_scroll):
#             driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)
#             WebDriverWait(driver, 5).until(
#                 lambda d: d.execute_script("return document.readyState") == "complete"
#             )

#         # Find course cards
#         course_cards = driver.find_elements(By.XPATH, "//div[@data-testid='product-card-cds']")
#         courses = []

#         # Extract details
#         for card in course_cards:
#             try:
#                 title = card.find_element(By.CLASS_NAME, "cds-CommonCard-title").text
#                 rating = card.find_element(By.CSS_SELECTOR, ".cds-RatingStat-meter .css-6ecy9b").text
#                 reviews = card.find_element(By.CSS_SELECTOR, ".cds-RatingStat-sizeLabel .css-vac8rf:last-child").text
#                 metadata = card.find_element(By.CSS_SELECTOR, ".cds-CommonCard-metadata p").text.split("·")
#                 level = metadata[0].strip() if metadata else None
#                 duration = metadata[2].strip() if len(metadata) > 2 else None
#                 link = "https://www.coursera.org" + card.find_element(By.CSS_SELECTOR, "a.cds-CommonCard-titleLink").get_attribute("data-track-href")
#                 courses.append(Course(title, rating, reviews, level, duration, link))
#             except Exception as e:
#                 print(f"Error extracting course details: {e}")
#                 continue

#         return courses
#     finally:
#         driver.quit()
def fetch_courses(keywords, max_courses=20):
    """
    Fetch courses from Coursera with smooth scrolling and course limit
    
    Args:
        keywords (str): Search keywords
        max_courses (int): Maximum number of courses to fetch (default: 20)
    """
    driver = webdriver.Chrome()
    search_query = "+".join(keywords.split())
    driver.get(f"https://www.coursera.org/search?query={search_query}")
    
    try:
        # Wait for initial course cards to load
        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.XPATH, "//div[@data-testid='product-card-cds']"))
        )
        
        courses = []
        last_course_count = 0
        scroll_attempts = 0
        max_scroll_attempts = 10  # Maximum number of scroll attempts
        
        # Scroll until we have enough courses or reach max attempts
        while len(courses) < max_courses and scroll_attempts < max_scroll_attempts:
            # Get current course cards
            course_cards = driver.find_elements(By.XPATH, "//div[@data-testid='product-card-cds']")
            
            # If no new courses loaded after scrolling, break
            if len(course_cards) == last_course_count:
                scroll_attempts += 1
            else:
                scroll_attempts = 0
                
            last_course_count = len(course_cards)
            
            # Smooth scrolling
            current_height = driver.execute_script("return window.pageYOffset")
            scroll_height = current_height + 500 # Scroll by 500px each time
            driver.execute_script(f"window.scrollTo(0, {scroll_height})")
            
            # Wait for new content to load
            time.sleep(2)  # Give time for new courses to load
            
            # Extract course details from visible cards
            courses = []
            for card in course_cards:
                try:
                    title = card.find_element(By.CLASS_NAME, "cds-CommonCard-title").text
                    
                    # Handle cases where rating might not exist
                    try:
                        rating = card.find_element(By.CSS_SELECTOR, ".cds-RatingStat-meter .css-6ecy9b").text
                        reviews = card.find_element(By.CSS_SELECTOR, ".cds-RatingStat-sizeLabel .css-vac8rf:last-child").text
                    except:
                        rating = "N/A"
                        reviews = "0"
                    
                    metadata = card.find_element(By.CSS_SELECTOR, ".cds-CommonCard-metadata p").text.split("·")
                    level = metadata[0].strip() if metadata else None
                    duration = metadata[2].strip() if len(metadata) > 2 else None
                    link = "https://www.coursera.org" + card.find_element(By.CSS_SELECTOR, "a.cds-CommonCard-titleLink").get_attribute("data-track-href")
                    
                    courses.append(Course(title, rating, reviews, level, duration, link))
                    
                    # Break if we have enough courses
                    if len(courses) >= max_courses:
                        break
                        
                except Exception as e:
                    print(f"Error extracting course details: {e}")
                    continue
            
            # Break if we have enough courses
            if len(courses) >= max_courses:
                break
                
    finally:
        driver.quit()
    
    # Return only the requested number of courses
    return courses[:max_courses]

def get_top_recommendations(courses, user_input):
    """Get top 3 course recommendations using Gemini"""
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    # Convert courses to a format suitable for the prompt
    courses_data = [course.to_dict() for course in courses]
    
    prompt = f"""
    Based on the user's requirements: "{user_input}"
    
    And the following list of courses: {str(courses_data)}
    
    Please recommend the top 5 most suitable courses. Consider the course ratings, reviews, and how well they match the user's requirements.
    Format your response as:
    1. [Course Title] - [Link]
    2. [Course Title] - [Link]
    3. [Course Title] - [Link]

    along with the course can you also recommend a project problem statement 
    
    Only include these 5 courses with their titles and links, no other text.
    """
    
    response = model.generate_content(prompt)
    return response.text if response else "No recommendations found."

# Streamlit UI
st.title("Smart Coursera Course Recommender")

user_input = st.text_area(
    "What would you like to learn?",
    placeholder="Example: I want to learn Machine Learning with a focus on practical applications. I prefer intermediate level courses with hands-on projects."
)

if st.button("Find Best Courses"):
    with st.spinner("Processing your request..."):
        # Step 1: Extract keywords
        st.subheader("🔍 Extracted Keywords")
        keywords = extract_keywords(user_input)
        st.write("Keywords:", keywords)
        
        # Step 2: Fetch courses using all keywords in a single query
        courses = fetch_courses(keywords)
        
        # Step 3: Display fetched courses
        st.write(f"Total Number of courses are {len(courses)}")
        st.subheader("📚 Courses Found")
        if courses:
            for course in courses:
                st.write(f"**{course.title}** ({course.rating}⭐ - {course.reviews} reviews)")
                st.write(f"Level: {course.level} | Duration: {course.duration}")
                st.write(f"[Link to course]({course.link})")
        else:
            st.write("No courses found for the given keywords.")
        
        # Step 4: Get top recommendations
        recommendations = get_top_recommendations(courses, user_input)
        st.subheader("🎯 Top Recommendations")
        st.write(recommendations)