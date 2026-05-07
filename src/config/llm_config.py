"""LLM configuration using CrewAI's native LLM class for compatibility."""
import os
from dotenv import load_dotenv

load_dotenv()

def get_llm():
    """Return CrewAI-compatible LLM instance."""
    from crewai import LLM  # Import here to avoid circular imports
    
    provider = os.getenv("LLM_PROVIDER", "groq").lower()
    temperature = float(os.getenv("LLM_TEMPERATURE", "0.05"))
    
    if provider == "groq":
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not set in environment")
        return LLM(
            model="groq/llama-3.3-70b-versatile",
            temperature=temperature,
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1",
            max_tokens=4096,
            timeout=30,
            max_retries=2
        )
    
    elif provider == "gemini":
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not set in environment")
        return LLM(
            model="gemini/gemini-2.5-flash",
            temperature=temperature,
            api_key=api_key,
            max_tokens=4096,
            timeout=30,
            max_retries=2
        )
    
    raise ValueError(f"Unsupported LLM_PROVIDER: {provider}. Use 'groq' or 'gemini'")