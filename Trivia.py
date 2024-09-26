import streamlit as st
import random
from openai import OpenAI
import fitz  # PyMuPDF

# Initialize OpenAI client
client = OpenAI()

def chatGPT_prompt(paragraph, user_input):
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an educator and help in making quizzes"},
            {
                "role": "user",
                "content": f"Based on the following paragraph: '{paragraph}'. " +
                           f"Provide up to '{user_input}' " +
                           "multiple-choice questions with exactly four options, and clearly indicate the correct answer. " +
                           "Please follow this strict format:\n" +
                           "Question: <question text>\n" +
                           "a) <option a>\n" +
                           "b) <option b>\n" +
                           "c) <option c>\n" +
                           "d) <option d>\n" +
                           "Answer: <correct answer letter>"
            }
        ]
    )
    return completion.choices[0].message.content

# Function to parse questions from the string
def parse_questions_from_string(quiz_string):
    quiz_data = []

    # Split by "Question" and filter out any empty strings
    questions = [q.strip() for q in quiz_string.split("Question") if q.strip()]

    for q in questions:
        lines = q.split("\n")

        # Ensure there are at least enough lines for 1 question, 4 options, and an answer
        if len(lines) < 6:
            st.warning("Unexpected format for a question. Skipping.")
            continue

        # Extract the question text
        question = lines[0].split(":")[-1].strip()

        # Extract options, handling missing or incorrectly formatted options
        options = []
        for line in lines[1:5]:
            if ")" in line:
                options.append(line.strip())
            else:
                st.warning(f"Option format is incorrect for question '{question}'. Skipping this question.")
                continue

        # Extract and validate the correct answer
        answer_line = lines[5].strip()
        if answer_line.startswith("Answer:"):
            correct_answer_letter = answer_line.split(":")[1].strip().lower()

            # Find the corresponding option based on the answer letter
            correct_option = None
            for option in options:
                if option.lower().startswith(correct_answer_letter):
                    correct_option = option
                    break

            if correct_option:
                # Append the question, options, and correct answer to quiz_data
                quiz_data.append((question, options, correct_option))
            else:
                st.error(f"Correct answer '{correct_answer_letter}' not found in options for question '{question}'. Skipping.")
        else:
            st.error(f"Answer format is incorrect for question '{question}'. Skipping this question.")

    # Shuffle the quiz data for randomness
    random.shuffle(quiz_data)

    return quiz_data

# Initialize session state variables
if 'quiz_data' not in st.session_state:
    st.session_state.quiz_data = []
    st.session_state.current_question_index = 0
    st.session_state.score = 0
    st.session_state.selected_answer = None
    st.session_state.feedback = ""
    st.session_state.is_quiz_finished = False
    st.session_state.is_answer_submitted = False  # Track if the answer is already submitted

# Function to display the current question
def show_question():
    question, options, correct_answer = st.session_state.quiz_data[st.session_state.current_question_index]

    st.subheader(f"Question {st.session_state.current_question_index + 1}:")
    st.write(question)

    # Ensure options are not empty
    if options:
        # Create radio button options for answer selection
        st.session_state.selected_answer = st.radio("Choose an answer:", options, index=0 if st.session_state.selected_answer is None else options.index(st.session_state.selected_answer))
    else:
        st.error("No options available for this question.")

# Function to handle the answer submission
def submit_answer():
    selected_option = st.session_state.selected_answer
    question, options, correct_answer = st.session_state.quiz_data[st.session_state.current_question_index]

    # Clean the selected option
    selected_answer_cleaned = selected_option.strip().lower()

    # Prepare correct answer for comparison
    correct_answer_cleaned = correct_answer.strip().lower()

    # Compare cleaned answers
    if selected_answer_cleaned == correct_answer_cleaned:
        st.session_state.feedback = "Correct! 🎉"
        st.session_state.score += 1
    else:
        st.session_state.feedback = f"Wrong! The correct answer was: {correct_answer}"

    # Set the answer submitted flag to True to prevent further submissions for this question
    st.session_state.is_answer_submitted = True

# Function to end the quiz and show the final score
def end_quiz():
    st.write("### Quiz Over!")
    st.write(f"Your final score: {st.session_state.score}/{len(st.session_state.quiz_data)}")

# Function to read PDF content
def read_pdf(uploaded_file):
    # Open the uploaded PDF file from the file-like object
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()  # Close the document after reading
    return text

# Main Quiz Display
st.title("Quiz Game")

# User input for paragraph or file upload
user_paragraph = st.text_area("Enter a paragraph of your choice:", height=200)

# File uploader for PDF
uploaded_file = st.file_uploader("Or upload a PDF file:", type=["pdf"])

if uploaded_file is not None:
    # Read PDF content if a file is uploaded
    user_paragraph = read_pdf(uploaded_file)

# Numeric input for number of questions
num_questions = st.number_input("Enter the number of questions to generate:", min_value=1, max_value=10, value=5)

if st.button("Generate Quiz"):
    if user_paragraph:
        # Get questions from the chatGPT_prompt function
        quiz_string = chatGPT_prompt(user_paragraph, num_questions)
        st.session_state.quiz_data = parse_questions_from_string(quiz_string)
        st.session_state.current_question_index = 0
        st.session_state.score = 0
        st.session_state.selected_answer = None
        st.session_state.feedback = ""
        st.session_state.is_quiz_finished = False
        st.session_state.is_answer_submitted = False  # Reset for the new quiz
    else:
        st.error("Please enter a paragraph or upload a PDF before generating the quiz.")

# Show the current score
st.write(f"**Score:** {st.session_state.score}")

# Check if there are any questions available
if not st.session_state.quiz_data:
    st.write("No valid questions available. Please try again later.")
else:
    # Show the total questions and current question number only if quiz is ongoing
    if not st.session_state.is_quiz_finished:
        total_questions = len(st.session_state.quiz_data)
        current_question = st.session_state.current_question_index + 1
        st.write(f"**Question {current_question} of {total_questions}**")

    # Show the current question
    if st.session_state.is_quiz_finished:
        end_quiz()
    else:
        # Check if the current question index is within bounds
        if st.session_state.current_question_index < len(st.session_state.quiz_data):
            show_question()
        else:
            st.write("No more questions available.")

        # Submit button to check the answer
        if st.button("Submit", disabled=st.session_state.is_answer_submitted):
            submit_answer()

        # Display feedback
        st.write(st.session_state.feedback)

        # Enable "Next Question" button only if an answer is selected and feedback has been provided
        if st.session_state.selected_answer and st.session_state.feedback:
            if st.button("Next Question"):
                # Move to the next question
                st.session_state.current_question_index += 1

                # Check if there are more questions
                if st.session_state.current_question_index >= len(st.session_state.quiz_data):
                    st.session_state.is_quiz_finished = True

                # Reset feedback, selected answer, and submission flag for the next question
                st.session_state.selected_answer = None  # Reset to None
                st.session_state.feedback = ""
                st.session_state.is_answer_submitted = False  # Reset for the next question
        else:
            st.button("Next Question", disabled=True)  # Keep button disabled
