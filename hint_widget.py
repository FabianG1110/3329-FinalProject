import pygame
import os
import textwrap
from dotenv import load_dotenv
import google.generativeai as genai

# Load API Key
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Gemini AI Helper
class GeminiHelper:
    def __init__(self):
        self.model = genai.GenerativeModel("gemini-1.5-pro")
        self.chat = self.model.start_chat(history=[])

    def ask_hint(self, challenge_type):
        prompt = (
            f"You are a cybersecurity AI assistant. The user is working on a challenge of type '{challenge_type}'. "
            "Give a subtle, indirect hint under 20 words. Do NOT reveal the answer."
        )
        try:
            response = self.chat.send_message(prompt)
            return response.text.strip()
        except Exception as e:
            return "Hint unavailable right now."

# Hint Button Widget
class HintWidget:
    def __init__(self, x, y, challenge_type):
        self.x = x
        self.y = y
        self.radius = 25
        self.challenge_type = challenge_type
        self.hint = ""
        self.show_hint = False
        self.ai = GeminiHelper()
        self.font = pygame.font.Font(None, 40)
        self.small_font = pygame.font.SysFont(None, 22)

    def draw(self, screen):
        pygame.draw.circle(screen, (30, 144, 255), (self.x, self.y), self.radius)
        q_mark = self.font.render("?", True, (255, 255, 255))
        q_rect = q_mark.get_rect(center=(self.x, self.y))
        screen.blit(q_mark, q_rect)

        if self.show_hint and self.hint:
            self.draw_hint_box(screen)

    def draw_hint_box(self, screen):
        hint_text = textwrap.fill(self.hint, width=30)
        lines = hint_text.splitlines()
        box_width = 260
        box_height = 20 + len(lines) * 22
        box_x = self.x - box_width - 10
        box_y = self.y - box_height // 2

        pygame.draw.rect(screen, (173, 216, 230), (box_x, box_y, box_width, box_height), border_radius=8)
        pygame.draw.rect(screen, (30, 144, 255), (box_x, box_y, box_width, box_height), 2, border_radius=8)

        for i, line in enumerate(lines):
            line_surface = self.small_font.render(line, True, (0, 0, 0))
            screen.blit(line_surface, (box_x + 10, box_y + 10 + i * 22))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self._is_hovering(event.pos):
                if self.hint:
                    self.show_hint = not self.show_hint
                else:
                    self.hint = self.ai.ask_hint(self.challenge_type)
                    self.show_hint = True

    def _is_hovering(self, pos):
        mx, my = pos
        return (mx - self.x) ** 2 + (my - self.y) ** 2 <= self.radius ** 2
