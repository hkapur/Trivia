import streamlit as st
import random
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI()

def chatGPT_prompt(paragraph):
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an educator and help in making quizzes"},
            {
                "role": "user",
                "content": f"Based on the following paragraph: '{paragraph}' "
                           "Provide 5 multiple-choice questions with four options, and indicate the correct answer clearly. Format your response as follows:\n"
                           "Example Question: What is the nickname of Manchester United Football Club?\n"
                           "Options:\n"
                           "a) The Red Devils\n"
                           "b) The Blues\n"
                           "c) The Gunners\n"
                           "d) The Citizens\n"
                           "Answer: a)"
            }
        ]
    )

    return completion.choices[0].message.content


# Function to parse questions from the string
def parse_questions_from_string(quiz_string):
    quiz_data = []

    # Split by lines
    lines = quiz_string.strip().split('\n')

    # Validate the number of lines
    if len(lines) < 6:  # We expect at least 6 lines: 1 question + 4 options + 1 answer line
        st.error("Received an unexpected quiz format. Please try again.")
        return []

    # Extract the question
    question = lines[0].replace("Example Question:", "").strip()

    # Extract options and remove any empty strings
    options = [line.strip() for line in lines[2:6] if line.strip()]

    # Check that we have exactly 4 options
    if len(options) != 4:
        st.error("Expected exactly 4 options, but got: {}".format(len(options)))
        return []

    # Extract the correct answer
    answer_line = lines[6].strip() if len(lines) > 6 else ""

    # Validate answer line format
    if answer_line.startswith("Answer:"):
        correct_answer_letter = answer_line.split(": ")[1].strip().lower()

        # Find the correct answer text
        correct_answer = next((opt for opt in options if opt.startswith(correct_answer_letter)), None)

        if correct_answer:
            correct_answer_text = correct_answer.replace(f"{correct_answer_letter}) ", "").strip()
            quiz_data.append((question, options, correct_answer_text))
        else:
            st.error("Could not find the correct answer in the options.")
            return []
    else:
        st.error("Answer format is incorrect. Please check the response format.")
        return []

    random.shuffle(quiz_data)  # Shuffle questions randomly
    return quiz_data


# Initialize session state variables
if 'quiz_data' not in st.session_state:
    st.session_state.quiz_data = []
    st.session_state.current_question_index = 0
    st.session_state.score = 0
    st.session_state.selected_answer = None
    st.session_state.feedback = ""
    st.session_state.is_quiz_finished = False


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


# Function to end the quiz and show the final score
def end_quiz():
    st.write("### Quiz Over!")
    st.write(f"Your final score: {st.session_state.score}/{len(st.session_state.quiz_data)}")


# Main Quiz Display
st.title("Quiz Game")

# User input for paragraph
user_paragraph = st.text_area("Enter a paragraph of your choice:", height=200)

if st.button("Generate Quiz"):
    if user_paragraph:
        # Get questions from the chatGPT_prompt function
        quiz_string = chatGPT_prompt(user_paragraph)
        st.session_state.quiz_data = parse_questions_from_string(quiz_string)
        st.session_state.current_question_index = 0
        st.session_state.score = 0
        st.session_state.selected_answer = None
        st.session_state.feedback = ""
        st.session_state.is_quiz_finished = False
    else:
        st.error("Please enter a paragraph before generating the quiz.")

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
        if st.button("Submit"):
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

                # Reset feedback and selected answer for the next question
                st.session_state.selected_answer = None  # Reset to None
                st.session_state.feedback = ""
        else:
            st.button("Next Question", disabled=True)  # Keep button disabled
