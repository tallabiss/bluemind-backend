import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERTICALS_DIR = os.path.join(BASE_DIR, "app", "verticals")

class PromptManager:
    def __init__(self):
        if not os.path.exists(VERTICALS_DIR):
            os.makedirs(VERTICALS_DIR)

    def get_prompt(self, vertical: str):
        file_path = os.path.join(VERTICALS_DIR, f"{vertical}.txt")
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        return f"<behavior_guidelines>\n- Nouveau profil pour {vertical}\n</behavior_guidelines>"

    def update_prompt(self, vertical: str, content: str):
        file_path = os.path.join(VERTICALS_DIR, f"{vertical}.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
