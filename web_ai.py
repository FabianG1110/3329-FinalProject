
import requests

class WebExploringAI:
    def __init__(self):
        self.base_url = "http://localhost:5000"

    def find_flag_on_about_page(self):
        try:
            res = requests.get(f"{self.base_url}/about", timeout=3)
            content = res.text
            if "flag{" in content:
                start = content.find("flag{")
                end = content.find("}", start)
                if start != -1 and end != -1:
                    return content[start:end + 1]
            return None
        except Exception as e:
            print(f"[AI ERROR] Could not fetch flag: {e}")
            return None
