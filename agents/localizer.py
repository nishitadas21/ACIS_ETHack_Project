"""
Localization Agent — translates content for regional rollout.

Extensible via `target` codes: hi (Hindi), ta, bn, etc. Uses deep-translator when
available; always reports whether offline fallback was used for audit logs.
"""

from __future__ import annotations

# Map friendly names to deep-translator targets
LANG_MAP = {
    "hindi": "hi",
    "hi": "hi",
    "tamil": "ta",
    "bengali": "bn",
    "spanish": "es",
}


def _fallback_payload(clean: str, language: str, reason: str) -> dict:
    hi_stub = (
        "[Hindi — offline translation fallback]\n"
        "हम आपके उत्पाद अपडेट का सुरक्षित स्थानीय संस्करण यहाँ संक्षेप में दे रहे हैं। "
        "पूर्ण अनुवाद हेतु नेटवर्क जोड़कर पुनः चलाएँ या मानव समीक्षक असाइन करें।\n\n"
        f"[EN excerpt]\n{clean[:1200]}"
    )
    text = hi_stub if language.lower() in ("hindi", "hi") else f"[{language} — offline fallback]\n\n{clean[:2000]}"
    return {
        "localized_text": text,
        "language": language,
        "language_code": LANG_MAP.get(language.lower(), language.lower()),
        "used_offline_fallback": True,
        "log_message": f"Using offline translation fallback ({reason}).",
    }


def localize_content(text: str, language: str = "Hindi") -> dict:
    """
    Returns structured localization result (never throws to caller).

    Keys: localized_text, language, language_code, used_offline_fallback, log_message
    """
    clean = (text or "").strip()
    if not clean:
        return {
            "localized_text": "",
            "language": language,
            "language_code": LANG_MAP.get(language.lower(), language.lower()),
            "used_offline_fallback": True,
            "log_message": "Using offline translation fallback (empty input).",
        }

    code = LANG_MAP.get(language.lower(), "hi" if language.lower() == "hindi" else language.lower()[:2])

    try:
        from deep_translator import GoogleTranslator

        chunk_size = 4500
        chunks = [clean[i : i + chunk_size] for i in range(0, len(clean), chunk_size)]
        translated: list[str] = []
        for part in chunks:
            translated.append(GoogleTranslator(source="auto", target=code).translate(part))
        return {
            "localized_text": "\n\n".join(translated),
            "language": language,
            "language_code": code,
            "used_offline_fallback": False,
            "log_message": "Online translation succeeded.",
        }
    except Exception as exc:  # noqa: BLE001
        fb = _fallback_payload(clean, language, reason=str(exc))
        fb["log_message"] = "Using offline translation fallback."
        return fb
