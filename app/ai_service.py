"""
AI Service Module
Handles integration with different AI providers (Gemini, OpenAI, Claude)
"""

import os
from config import Config


class AIService:
    """Base class for AI service"""
    
    @staticmethod
    def get_response(user_message):
        """
        Get AI response based on configured provider
        Falls back to demo response if no API key is configured
        """
        provider = Config.AI_PROVIDER.lower()
        
        # Check if API key is available for the chosen provider
        if provider == 'gemini' and Config.GEMINI_API_KEY:
            return GeminiService.get_response(user_message)
        elif provider == 'openai' and Config.OPENAI_API_KEY:
            return OpenAIService.get_response(user_message)
        elif provider == 'claude' and Config.CLAUDE_API_KEY:
            return ClaudeService.get_response(user_message)
        else:
            # Fall back to demo response if no API key configured
            return AIService._get_demo_response(user_message)
    
    @staticmethod
    def _get_demo_response(user_message):
        """Demo response when no AI API is configured"""
        # Simple keyword matching for demo
        msg_lower = user_message.lower()
        
        if 'iphone' in msg_lower or '16 pro' in msg_lower:
            return f"""🔍 **iPhone 16 Pro Analysis**

**Current Best:** Amazon at ₹1,14,900
**Predicted Price (Oct 15):** ₹1,06,400
**Expected Saving:** ₹8,500 (7.4%)

⏳ **Verdict: WAIT 3–4 Weeks**
Historical data shows iPhone prices drop 6–10% during Diwali. Amazon and Flipkart typically offer maximum discounts. Scroll down to see the full ML forecast! 🚀"""
        
        elif 'macbook' in msg_lower:
            return f"""💻 **MacBook Air M3 (8GB/256GB) — Live Comparison**

| Store | Price | Discount |
|---|---|---|
🛒 Amazon | ₹1,09,900 | ₹10,000 off |
🏪 Flipkart | ₹1,11,499 | 8% off |
🍎 Apple | ₹1,19,900 | — |

🤖 **AI Says:** Amazon is ₹1,599 cheaper. **Best time to buy is NOW** — price trend shows an upward spike expected next month due to MacBook Pro launch."""
        
        else:
            return f"""I've analyzed your query about **{user_message}**.

📊 **Current Status:** Demo mode active
🤖 **Note:** To get real AI responses, please configure an API key in the `.env` file.

**Supported AI Providers:**
- Gemini (Google) - Free tier available
- OpenAI (GPT-4) - Requires paid account
- Claude (Anthropic) - Requires paid account

To set up AI:
1. Copy `.env.example` to `.env`
2. Add your API key
3. Set `AI_PROVIDER=gemini` (or openai/claude)
4. Restart the server"""


class GeminiService:
    """Google Gemini AI Service"""
    
    @staticmethod
    def get_response(user_message):
        """Get response from Gemini API"""
        try:
            import google.generativeai as genai
            
            # Initialize Gemini
            genai.configure(api_key=Config.GEMINI_API_KEY)
            model = genai.GenerativeModel(Config.GEMINI_MODEL)
            
            # System prompt for price comparison context
            system_prompt = """You are PriceAI, an intelligent price comparison assistant. 
            You help users find the best deals, predict price trends, and recommend when to buy products.
            Be helpful, concise, and use emojis to make responses engaging.
            Focus on Indian e-commerce platforms like Amazon, Flipkart, Croma, etc."""
            
            # Generate response
            response = model.generate_content(
                f"{system_prompt}\n\nUser: {user_message}",
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=1000,
                )
            )
            
            return response.text
            
        except Exception as e:
            print(f"Gemini API Error: {e}")
            return f"Sorry, I encountered an error with the Gemini API: {str(e)}"


class OpenAIService:
    """OpenAI GPT Service"""
    
    @staticmethod
    def get_response(user_message):
        """Get response from OpenAI API"""
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=Config.OPENAI_API_KEY)
            
            system_prompt = """You are PriceAI, an intelligent price comparison assistant. 
            You help users find the best deals, predict price trends, and recommend when to buy products.
            Be helpful, concise, and use emojis to make responses engaging.
            Focus on Indian e-commerce platforms like Amazon, Flipkart, Croma, etc."""
            
            response = client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"OpenAI API Error: {e}")
            return f"Sorry, I encountered an error with the OpenAI API: {str(e)}"


class ClaudeService:
    """Anthropic Claude Service"""
    
    @staticmethod
    def get_response(user_message):
        """Get response from Claude API"""
        try:
            import anthropic
            
            client = anthropic.Anthropic(api_key=Config.CLAUDE_API_KEY)
            
            system_prompt = """You are PriceAI, an intelligent price comparison assistant. 
            You help users find the best deals, predict price trends, and recommend when to buy products.
            Be helpful, concise, and use emojis to make responses engaging.
            Focus on Indian e-commerce platforms like Amazon, Flipkart, Croma, etc."""
            
            response = client.messages.create(
                model=Config.CLAUDE_MODEL,
                max_tokens=1000,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_message}
                ]
            )
            
            return response.content[0].text
            
        except Exception as e:
            print(f"Claude API Error: {e}")
            return f"Sorry, I encountered an error with the Claude API: {str(e)}"
