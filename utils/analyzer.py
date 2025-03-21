import google.generativeai as genai
import re
import json
import os
from dotenv import load_dotenv
from utils.document_parser import extract_qa_pairs
load_dotenv()

# Configure Gemini AI
API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)

def analyze_answers(document_text):
    """
    Analyze the document content to check if answers are correct.
    
    Args:
        document_text (str): The extracted text from the document
        
    Returns:
        list: List of dictionaries containing analysis results
    """
    # Extract question-answer pairs
    qa_pairs = extract_qa_pairs(document_text)
    
    if not qa_pairs:
        return [{"error": "No question-answer pairs found in the document"}]
    
    # Initialize Gemini model
    model = genai.GenerativeModel("gemini-1.5-pro-latest")  # Updated model

    results = []

    for qa_pair in qa_pairs:
        question = qa_pair['question']
        user_answer = qa_pair['answer']
        question_num = qa_pair['question_num']
        
        # Create prompt for Gemini
        prompt = f"""
        Evaluate if the following answer to the question is correct. If not, provide a suggestion.

        Question: {question}
        Answer: {user_answer}

        Please respond in this JSON format:
        {{
            "is_correct": true/false,
            "correct_answer": "the correct answer",
            "explanation": "explanation of why the answer is correct or incorrect",
            "suggestion": "suggestion for improvement if the answer is incorrect"
        }}

        Be lenient with minor spelling or grammatical errors if the core concept is correct.
        """

        try:
            response = model.generate_content(prompt)
            response_text = response.text
            
            # Extract JSON from response (handle cases where the model adds extra text)
            json_match = re.search(r'({.*})', response_text.replace('\n', ' '), re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group(1))
            else:
                analysis = {
                    "is_correct": None,
                    "correct_answer": "Unable to determine",
                    "explanation": "Error processing the response",
                    "suggestion": "Please try again"
                }
                
            # Add original question and answer to the result
            result = {
                "question_num": question_num,
                "question": question,
                "user_answer": user_answer,
                "is_correct": analysis.get("is_correct", False),
                "correct_answer": analysis.get("correct_answer", ""),
                "explanation": analysis.get("explanation", ""),
                "suggestion": analysis.get("suggestion", "")
            }
            
            results.append(result)
            
        except Exception as e:
            results.append({
                "question_num": question_num,
                "question": question,
                "user_answer": user_answer,
                "error": f"Failed to analyze: {str(e)}"
            })

    return results

