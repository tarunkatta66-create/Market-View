import os
import json
import time
from typing import Dict, Any

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    _vader_analyzer = SentimentIntensityAnalyzer()
except ImportError:
    _vader_analyzer = None


class GeminiSentimentClient:
    """
    Wrapper around Gemini Flash LLM for headline sentiment scoring.
    Includes memory caching, retries, and local VADER fallback.
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.client = None
        
        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
            except Exception:
                try:
                    import google.generativeai as genai_legacy
                    genai_legacy.configure(api_key=self.api_key)
                    self.client = genai_legacy.GenerativeModel('gemini-1.5-flash')
                except Exception:
                    self.client = None

    def analyze_headline(self, text: str) -> Dict[str, Any]:
        text_clean = text.strip()
        if not text_clean:
            return {"score": 0.0, "label": "neutral", "summary": "", "source": "fallback"}

        if text_clean in self.cache:
            return self.cache[text_clean]

        if self.client:
            res = self._call_gemini(text_clean)
            if res:
                self.cache[text_clean] = res
                return res

        res = self._fallback_sentiment(text_clean)
        self.cache[text_clean] = res
        return res

    def _call_gemini(self, text: str) -> Dict[str, Any]:
        prompt = (
            "Analyze financial sentiment of headline. Respond in JSON with keys:\n"
            "score (float between -1.0 to 1.0), label ('positive', 'negative', or 'neutral'), summary (short 10 word explanation).\n"
            f"Headline: {text}"
        )

        for attempt in range(2):
            try:
                if hasattr(self.client, 'models'):
                    response = self.client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=prompt,
                    )
                    content = response.text
                else:
                    response = self.client.generate_content(prompt)
                    content = response.text

                # clean json block if formatted in markdown
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()

                parsed = json.loads(content)
                return {
                    "score": float(parsed.get("score", 0.0)),
                    "label": str(parsed.get("label", "neutral")).lower(),
                    "summary": str(parsed.get("summary", text[:40])),
                    "source": "gemini_flash"
                }
            except Exception:
                time.sleep(0.5)
        return None

    def _fallback_sentiment(self, text: str) -> Dict[str, Any]:
        if _vader_analyzer:
            vs = _vader_analyzer.polarity_scores(text)
            compound = vs["compound"]
            label = "positive" if compound >= 0.05 else ("negative" if compound <= -0.05 else "neutral")
            return {
                "score": round(compound, 3),
                "label": label,
                "summary": text[:50],
                "source": "vader_fallback"
            }
        
        # Simple lexicon fallback if vader not installed
        pos_words = {"bullish", "profit", "surge", "gain", "rise", "growth", "high", "up", "record", "rally"}
        neg_words = {"bearish", "loss", "drop", "fall", "decline", "low", "down", "crash", "plunge", "slump"}
        words = set(text.lower().split())
        score = len(words & pos_words) * 0.3 - len(words & neg_words) * 0.3
        score = max(-1.0, min(1.0, score))
        label = "positive" if score > 0.1 else ("negative" if score < -0.1 else "neutral")
        return {
            "score": round(score, 3),
            "label": label,
            "summary": text[:50],
            "source": "lexicon_fallback"
        }
