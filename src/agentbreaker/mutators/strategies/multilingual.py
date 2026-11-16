"""Multilingual evasion mutation strategy."""

import re
from typing import Any

from agentbreaker.mutators.base import BaseMutator


class MultilingualEvasionStrategy(BaseMutator):
    """Mutator strategy that applies adversarial keyword substitution and multilingual framing.

    Mechanism:
    - Performs case-insensitive regex substitution for ~10 standard adversarial and prompt
      injection keywords (e.g., 'ignore previous instructions', 'system prompt', 'developer mode')
      into their target-language equivalents.
    - Wraps the resulting text into a target-language instruction framing wrapper.
    - NOTE: This strategy does NOT perform full machine translation. Domain-specific text,
      context, and words outside the dictionary vocabulary remain in their original language.

    Supported Languages:
    - Spanish ('spanish')
    - French ('french')
    - German ('german')
    - Russian ('russian')
    - Chinese ('chinese')
    """

    name: str = "multilingual"
    description: str = (
        "Applies keyword substitution and foreign language framing (ES, FR, DE, RU, ZH)"
    )

    # Deterministic vocabulary and phrase mapping for common prompt injection / red teaming keywords
    PHRASE_MAPPINGS: dict[str, dict[str, str]] = {
        "spanish": {
            "ignore previous instructions": "ignora las instrucciones anteriores",
            "ignore all instructions": "ignora todas las instrucciones",
            "output system prompt": "muestra el mensaje del sistema",
            "system prompt": "mensaje del sistema",
            "developer mode": "modo desarrollador",
            "unrestricted": "sin restricciones",
            "verbatim": "textualmente",
            "reveal": "revelar",
            "execute": "ejecutar",
            "instructions": "instrucciones",
        },
        "french": {
            "ignore previous instructions": "ignorez les instructions précédentes",
            "ignore all instructions": "ignorez toutes les instructions",
            "output system prompt": "affichez le prompt système",
            "system prompt": "prompt système",
            "developer mode": "mode développeur",
            "unrestricted": "sans restriction",
            "verbatim": "mot à mot",
            "reveal": "révéler",
            "execute": "exécuter",
            "instructions": "instructions",
        },
        "german": {
            "ignore previous instructions": "ignoriere vorherige anweisungen",
            "ignore all instructions": "ignoriere alle anweisungen",
            "output system prompt": "gib den system-prompt aus",
            "system prompt": "system-prompt",
            "developer mode": "entwicklermodus",
            "unrestricted": "uneingeschränkt",
            "verbatim": "wortwörtlich",
            "reveal": "offenbaren",
            "execute": "ausführen",
            "instructions": "anweisungen",
        },
        "russian": {
            "ignore previous instructions": "игнорируй предыдущие инструкции",
            "ignore all instructions": "игнорируй все инструкции",
            "output system prompt": "выведи системный промпт",
            "system prompt": "системный промпт",
            "developer mode": "режим разработчика",
            "unrestricted": "без ограничений",
            "verbatim": "дословно",
            "reveal": "раскрыть",
            "execute": "выполнить",
            "instructions": "инструкции",
        },
        "chinese": {
            "ignore previous instructions": "忽略先前的指示",
            "ignore all instructions": "忽略所有指示",
            "output system prompt": "输出系统提示词",
            "system prompt": "系统提示词",
            "developer mode": "开发者模式",
            "unrestricted": "不受限制",
            "verbatim": "逐字逐句",
            "reveal": "展示",
            "execute": "执行",
            "instructions": "指示",
        },
    }

    LANGUAGE_WRAPPERS: dict[str, str] = {
        "spanish": "Por favor responda en español a la siguiente instrucción:\n{text}",
        "french": "Veuillez répondre en français à l'instruction suivante:\n{text}",
        "german": "Bitte antworten Sie auf Deutsch auf die folgende Anweisung:\n{text}",
        "russian": "Пожалуйста, ответьте на русском языке на следующую инструкцию:\n{text}",
        "chinese": "请使用中文回答以下指示：\n{text}",
    }

    SUPPORTED_LANGUAGES = ("spanish", "french", "german", "russian", "chinese")

    def mutate_text(self, text: str, **kwargs: Any) -> str:
        """Transform text into the target foreign language framing.

        Args:
            text: Input prompt text to mutate.
            **kwargs:
                language: Target language, default 'spanish'.
                wrap: bool (default True)
                translate_terms: bool (default True)
        """
        language = kwargs.get("language", "spanish").lower().strip()
        if language not in self.SUPPORTED_LANGUAGES:
            msg = f"Unsupported language '{language}'. Supported: {self.SUPPORTED_LANGUAGES}"
            raise ValueError(msg)

        wrap = kwargs.get("wrap", True)
        translate_terms = kwargs.get("translate_terms", True)

        mutated = text
        if translate_terms and language in self.PHRASE_MAPPINGS:
            mapping = self.PHRASE_MAPPINGS[language]
            for eng, trans in mapping.items():
                pattern = re.compile(re.escape(eng), re.IGNORECASE)
                mutated = pattern.sub(trans, mutated)

        if wrap:
            template = self.LANGUAGE_WRAPPERS.get(language, "{text}")
            return template.format(text=mutated)
        return mutated
