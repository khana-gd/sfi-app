import os
import logging
import httpx
import base64
from typing import Dict, Any, Generator
from app.core.config import settings

logger = logging.getLogger("kanha.image_provider")

class FashionImageProvider:
    """Interface abstraction for AI concept generation and sketch analysis."""
    
    def generate_concept(self, prompt: str, silhouette: str) -> str:
        """Generates a fashion design concept image URL from text prompt/params."""
        raise NotImplementedError
        
    def analyze_sketch(self, image_content: bytes) -> Dict[str, Any]:
        """Performs multimodal analysis of a pencil sketch image."""
        raise NotImplementedError

class GeminiImageProvider(FashionImageProvider):
    """Google Gemini implementation for fashion illustration and multimodal sketch analysis."""

    def generate_concept(self, prompt: str, silhouette: str) -> str:
        """Generates concept image. Uses configurable GEMINI_IMAGE_MODEL if present,

        otherwise returns beautifully pre-rendered static mock concepts.
        """
        api_key = settings.GEMINI_API_KEY
        # If API key is dummy/missing, return static mock asset matching the silhouette
        if not api_key or api_key == "dummy_gemini_key_for_dev":
            return self._get_mock_concept_url(silhouette)

        # Let's perform a live call using Google's recommended image generation model if set
        image_model = os.getenv("GEMINI_IMAGE_MODEL", "imagen-3.0-generate-002")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{image_model}:predict?key={api_key}"
        
        payload = {
            "instances": [
                {"prompt": prompt}
            ],
            "parameters": {
                "sampleCount": 1,
                "aspectRatio": "3:4",
                "outputMimeType": "image/jpeg"
            }
        }
        try:
            with httpx.Client(timeout=30.0) as client:
                res = client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    predictions = data.get("predictions", [])
                    if predictions:
                        image_b64 = predictions[0].get("bytesBase64Encoded")
                        if image_b64:
                            # Save generated image to static fashion_ai folder
                            import uuid
                            filename = f"gen_{uuid.uuid4().hex[:8]}.jpg"
                            static_dir = os.path.join(
                                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                                "static", "fashion_ai"
                            )
                            os.makedirs(static_dir, exist_ok=True)
                            filepath = os.path.join(static_dir, filename)
                            with open(filepath, "wb") as f:
                                f.write(base64.b64decode(image_b64))
                            return f"/static/fashion_ai/{filename}"
        except Exception as e:
            logger.warning(f"Gemini live image generation failed: {e}. Using mock assets.")
            
        return self._get_mock_concept_url(silhouette)

    def analyze_sketch(self, image_content: bytes) -> Dict[str, Any]:
        """Analyzes a sketch image using Gemini multimodal vision models."""
        api_key = settings.GEMINI_API_KEY
        model_name = settings.GEMINI_MODEL or "gemini-3.6-flash"
        
        prompt = (
            "You are a professional fashion tutor analyzing a student's design sketch. "
            "Identify the silhouette (e.g. Lehenga, Gown, Sherwani), necklines, style lines, "
            "and structural elements. Recommend suitable fabrics (e.g. organza, velvet), "
            "color palettes (e.g. Gold, Crimson), and regional embroidery techniques (e.g. Zardozi, Chikankari)."
        )
        
        if not api_key or api_key == "dummy_gemini_key_for_dev":
            return self._get_mock_sketch_analysis()

        # Call Gemini multimodal endpoint
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        
        image_b64 = base64.b64encode(image_content).decode("utf-8")
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inlineData": {
                                "mimeType": "image/jpeg",
                                "data": image_b64
                            }
                        }
                    ]
                }
            ]
        }
        try:
            with httpx.Client(timeout=20.0) as client:
                res = client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    analysis_text = data["candidates"][0]["content"]["parts"][0]["text"]
                    return {
                        "analysis": analysis_text,
                        "silhouette": "Detected from sketch",
                        "neckline": "Identified from sketch",
                        "fabrics": ["Silk", "Organza", "Linen"],
                        "colors": ["Ivory", "Crimson", "Gold"],
                        "embroidery": "Zardozi / Chikankari"
                    }
        except Exception as e:
            logger.warning(f"Gemini multimodal sketch analysis failed: {e}")
            
        return self._get_mock_sketch_analysis()

    def _get_mock_concept_url(self, silhouette: str) -> str:
        """Returns static path to one of our gorgeous mock design board sketches."""
        sil = silhouette.lower()
        if "lehenga" in sil:
            return "/static/fashion_ai/concept_lehenga.jpg"
        elif "anarkali" in sil or "gown" in sil:
            return "/static/fashion_ai/concept_anarkali.jpg"
        return "/static/fashion_ai/concept_lehenga.jpg"

    def _get_mock_sketch_analysis(self) -> Dict[str, Any]:
        """Returns rich, highly detailed offline fashion design suggestions."""
        return {
            "analysis": (
                "### KANHA Technical Sketch Analysis\n\n"
                "1.  **Silhouette**: Flared Kalidar silhouette with panels.\n"
                "2.  **Style & Neckline**: Deep V-neckline with structured shoulder seams.\n"
                "3.  **Material Recommendations**:\n"
                "    *   *Fabrics*: Raw Silk or Velvet to support structured pleating.\n"
                "    *   *Embroidery*: Gold Zardozi border embellishments on cuffs and hem.\n"
                "    *   *Colors*: Curated SFI Palette (Navy blue base with accents of Gold and Soft Pink)."
            ),
            "silhouette": "Flared Kalidar Gown",
            "neckline": "Deep V-neckline",
            "fabrics": ["Raw Silk", "Velvet", "Organza"],
            "colors": ["Royal Navy", "Gold Accent", "Soft Pink Accent"],
            "embroidery": "Zardozi hand-embroidery borders"
        }
