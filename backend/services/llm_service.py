"""
Local LLM service using Ollama with Llama 3.

Communicates with the locally running Ollama server via HTTP.
No data is sent to any external service.

PRIVACY NOTICE:
All LLM inference is performed locally via Ollama.
No prompts or responses leave the local machine.
The Ollama server runs at http://localhost:11434.
"""

import httpx
import json
import re
from typing import Optional


OLLAMA_BASE_URL = "http://localhost:11434"
MODEL_NAME = "llama3"
REQUEST_TIMEOUT = 300.0  # seconds – first call loads model into memory


async def generate(prompt: str, system_prompt: Optional[str] = None) -> str:
    """
    Send a prompt to the local Llama 3 model via Ollama and get a response.
    
    Args:
        prompt: The user/instruction prompt.
        system_prompt: Optional system-level instructions.
        
    Returns:
        The model's text response.
    """
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,  # Low temperature for structured extraction
            "num_predict": 2048,
        }
    }

    if system_prompt:
        payload["system"] = system_prompt

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        try:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
        except httpx.ConnectError:
            raise ConnectionError(
                "Cannot connect to Ollama. Make sure Ollama is running locally. "
                "Start it with: ollama serve"
            )
        except httpx.TimeoutException:
            raise TimeoutError(
                "Ollama request timed out. The model may still be loading. "
                "Try again in a moment."
            )


async def generate_json(prompt: str, system_prompt: Optional[str] = None) -> dict:
    """
    Send a prompt and parse the response as JSON.
    Handles cases where the model wraps JSON in markdown code blocks.
    
    Args:
        prompt: The prompt requesting JSON output.
        system_prompt: Optional system instructions.
        
    Returns:
        Parsed JSON dictionary.
    """
    raw_response = await generate(prompt, system_prompt)
    return _extract_json(raw_response)


def _extract_json(text: str) -> dict:
    """
    Extract JSON from LLM response text.
    Handles common LLM output patterns:
    - Raw JSON
    - JSON wrapped in ```json ... ``` code blocks
    - JSON with preamble/postamble text
    """
    # Try direct JSON parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try extracting from markdown code block
    json_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try finding JSON object in text
    brace_match = re.search(r"\{.*\}", text, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except json.JSONDecodeError:
            pass

    # Return empty dict if all parsing fails
    return {}


async def check_ollama_health() -> bool:
    """Check if Ollama is running and the model is available."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                return any(MODEL_NAME in name for name in model_names)
    except Exception:
        pass
    return False
