from flask import Blueprint, request, jsonify, render_template
from app.ai_service import AIService

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    """Serve the chatbot webpage"""
    return render_template('index.html')

@main_bp.route('/api/chat', methods=['POST'])
def chat():
    """
    This endpoint receives user messages from the frontend
    and returns AI-powered responses.
    """
    data = request.get_json()
    user_message = data.get('message', '')
    
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400
    
    # Get AI response
    ai_reply = AIService.get_response(user_message)
    
    response = {
        'reply': ai_reply
    }
    
    return jsonify(response)
