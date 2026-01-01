import re

class ComplianceEngine:
    def __init__(self):
        # Règles strictes basées sur le framework de production
        self.required_format = "SYNTHESIS"
        self.citation_pattern = r'<antml:cite index=".*">.*</antml:cite>'

    def verify_response(self, content: str):
        """
        Analyse la réponse pour garantir l'adhérence aux instructions.
        """
        score = 100
        issues = []

        # 1. Vérification de la structure (Behavior Guidelines)
        if self.required_format not in content.upper():
            score -= 30
            issues.append("Structure de réponse SYNTHESIS manquante.")

        # 2. Vérification des citations (Citation Formatting Rules)
        citations = re.findall(self.citation_pattern, content)
        if not citations:
            score -= 40
            issues.append("Zéro citation source détectée (Risque d'hallucination).")

        # 3. Analyse du ton (Objective Tone Check)
        subjective_terms = ["je pense", "à mon avis", "peut-être"]
        if any(term in content.lower() for term in subjective_terms):
            score -= 30
            issues.append("Ton subjectif détecté au lieu d'un ton expert.")

        return {
            "score": max(0, score),
            "compliant": score >= 70,
            "issues": issues
        }

    def force_xml_structure(self, prompt: str):
        """Assure que le prompt système contient les balises de contrôle."""
        blocks = ["behavior_guidelines", "tool_protocols", "citation_logic"]
        for block in blocks:
            if f"<{block}>" not in prompt:
                prompt += f"\n<{block}>Force compliance for production.</{block}>"
        return prompt
