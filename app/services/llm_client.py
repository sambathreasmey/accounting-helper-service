import logging

from groq import APIConnectionError, APIError, Groq, GroqError

from app.core.config import settings

logger = logging.getLogger(__name__)

client = Groq(api_key=settings.GROQ_API_KEY)


def call_llama(
    user_prompt: str,
    system_prompt: str,
    temperature: float = 0.4,
    max_tokens: int = 1024,
) -> str:
    """
    Shared logic to interact with the Groq-hosted model.
    """
    try:
        response = client.chat.completions.create(
            model=settings.MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=1,
        )
        return response.choices[0].message.content
    except (GroqError, APIError, APIConnectionError) as e:
        logger.error(f"Groq API Error: {e}")
        return "⚠️ Sorry, I'm having trouble thinking right now. Please try again later."
