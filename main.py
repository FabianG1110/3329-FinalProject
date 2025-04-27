import pygame
import hashlib
import base64
from cryptography.fernet import Fernet
from hint_widget import HintWidget
from web_ai import WebExploringAI
import threading
import time
import textwrap

# Initialize Pygame
pygame.init()

# Screen settings
WIDTH, HEIGHT = 1000, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("CyberGuard: CTF Edition")

# Load and scale background image
background = pygame.image.load("interactivebackground1.png")
background = pygame.transform.scale(background, (WIDTH, HEIGHT))

# Load and slice sprite sheet for character animation
sprite_sheet = pygame.image.load("character_spritesheet.png")
SPRITE_WIDTH, SPRITE_HEIGHT = 50, 50
frames = [sprite_sheet.subsurface(pygame.Rect(i * SPRITE_WIDTH, 0, SPRITE_WIDTH, SPRITE_HEIGHT)) for i in range(4)]

# Character settings
character_x = WIDTH // 2 - 25
character_y = HEIGHT - 100
speed = 1
frame_index = 0
FPS = 10
clock = pygame.time.Clock()

# Colors and Fonts
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
ORANGE = (255, 165, 0)
font = pygame.font.Font(None, 40)
pause_font = pygame.font.Font(None, 80)

# Hint Button Setup
hint_widget = HintWidget(WIDTH - 50, HEIGHT - 50, "ctf_web_inspection")

paused = False

class Player:
    def __init__(self, name):
        self.name = name
        self.score = 0

    def update_score(self, points):
        self.score += points

    def get_score(self):
        return self.score

class TextInputChallenge:
    def __init__(self, prompt, correct_answer):
        self.prompt = prompt
        self.correct_answer = correct_answer
        self.user_input = ""
        self.cursor_visible = True
        self.cursor_timer = 0

    def present(self):
        running = True
        while running:
            screen.blit(background, (0, 0))
            wrapped_prompt = textwrap.wrap(self.prompt, width=50)
            for i, line in enumerate(wrapped_prompt):
                line_surface = font.render(line, True, WHITE)
                screen.blit(line_surface, (50, 40 + i * 40))

            input_y = 60 + len(wrapped_prompt) * 40
            input_text = f"Your Input: {self.user_input}"
            if self.cursor_visible:
                input_text += "|"
            input_surface = font.render(input_text, True, WHITE)
            screen.blit(input_surface, (50, input_y))

            hint_widget.draw(screen)
            pygame.display.flip()

            self.cursor_timer += 1
            if self.cursor_timer % 30 == 0:
                self.cursor_visible = not self.cursor_visible

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pause_menu()
                    elif event.key == pygame.K_RETURN:
                        return self.user_input.lower() == self.correct_answer.lower()
                    elif event.key == pygame.K_BACKSPACE:
                        self.user_input = self.user_input[:-1]
                    else:
                        self.user_input += event.unicode
                hint_widget.handle_event(event)
        return False

class Question:
    def __init__(self, question, options, correct_option):
        self.question = question
        self.options = options
        self.correct_option = correct_option
        self.option_positions = [(100, 200 + i * 60) for i in range(len(options))]

    def present(self):
        global character_x, character_y
        running = True
        while running:
            screen.blit(background, (0, 0))
            screen.blit(frames[frame_index], (character_x, character_y))
            question_surface = font.render(self.question, True, WHITE)
            screen.blit(question_surface, (50, 50))

            for i, option in enumerate(self.options):
                y_pos = self.option_positions[i][1]
                pygame.draw.rect(screen, ORANGE, (100, y_pos, 800, 50))
                option_surface = font.render(option, True, WHITE)
                screen.blit(option_surface, (110, y_pos + 10))

            hint_widget.draw(screen)
            pygame.display.flip()

            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]:
                character_x = max(0, character_x - speed)
            if keys[pygame.K_RIGHT]:
                character_x = min(WIDTH - SPRITE_WIDTH, character_x + speed)
            if keys[pygame.K_UP]:
                character_y = max(0, character_y - speed)
            if keys[pygame.K_DOWN]:
                character_y = min(HEIGHT - SPRITE_HEIGHT, character_y + speed)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pause_menu()
                    elif event.key == pygame.K_RETURN:
                        for i, pos in enumerate(self.option_positions):
                            if pos[0] <= character_x <= pos[0] + 800 and pos[1] <= character_y <= pos[1] + 50:
                                return i == self.correct_option
                hint_widget.handle_event(event)
        return False

class CyberGuardGame:
    def __init__(self, versus_ai=False):
        self.player = Player("Player 1")
        self.versus_ai = versus_ai
        self.ai = WebExploringAI() if versus_ai else None
        self.challenges = [
            TextInputChallenge("Open your browser and go to http://localhost:5000/about. View Page Source to find the flag.", "flag{test_flag_hidden_in_html}"),
            Question("You receive an email saying you've won a lottery. What should you do?", ["Click the link and claim prize", "Report it as phishing", "Reply for details"], 1),
            TextInputChallenge("Crack this password hash: 5e884898da280471", "password"),
            TextInputChallenge("Decode this Base64 string: U3RheV9jdXJpb3VzIQ==", "Stay_curious!"),
            TextInputChallenge("Reverse this output to get the flag: jgct345", "hear123"),
            TextInputChallenge("Decrypt this message: 'CyberSecurity!'", "CyberSecurity!")
        ]

    def start(self):
        for challenge in self.challenges:
            ai_answer = None
            if self.versus_ai:
                ai_answer = self.run_ai(challenge)

            player_correct = challenge.present()
            if player_correct:
                self.player.update_score(10)
            elif ai_answer:
                self.player.update_score(0)

        screen.blit(background, (0, 0))
        score_surface = font.render(f"Final Score: {self.player.get_score()} points", True, WHITE)
        screen.blit(score_surface, (250, 300))
        pygame.display.flip()
        pygame.time.wait(5000)
        pygame.quit()

    def run_ai(self, challenge):
        if isinstance(challenge, TextInputChallenge):
            if "http://localhost:5000/about" in challenge.prompt:
                flag = self.ai.find_flag_on_about_page()
                if flag and flag.lower() == challenge.correct_answer.lower():
                    return True
        return False

# Pause and menus

def pause_menu():
    global paused
    paused = True
    while paused:
        screen.fill(BLACK)
        pause_text_big = pause_font.render("Paused", True, ORANGE)
        resume_button = font.render("Resume", True, WHITE)
        menu_button = font.render("Return to Menu", True, WHITE)
        screen.blit(pause_text_big, (WIDTH // 2 - 150, 100))
        screen.blit(resume_button, (WIDTH // 2 - 80, 300))
        screen.blit(menu_button, (WIDTH // 2 - 120, 400))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                if WIDTH // 2 - 80 <= mx <= WIDTH // 2 + 80 and 300 <= my <= 340:
                    paused = False
                elif WIDTH // 2 - 120 <= mx <= WIDTH // 2 + 120 and 400 <= my <= 440:
                    paused = False
                    home_screen()

def home_screen():
    running = True
    while running:
        screen.fill(BLACK)
        title_surface = font.render("CyberGuard: CTF Edition", True, WHITE)
        quiz_button = font.render("CTF Quiz", True, ORANGE)
        ctf_button = font.render("CTF Challenge", True, ORANGE)
        screen.blit(title_surface, (WIDTH // 2 - 200, 100))
        screen.blit(quiz_button, (WIDTH // 2 - 100, 250))
        screen.blit(ctf_button, (WIDTH // 2 - 120, 350))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                if WIDTH // 2 - 100 <= mx <= WIDTH // 2 + 100 and 250 <= my <= 290:
                    game = CyberGuardGame(versus_ai=False)
                    game.start()
                    running = False
                elif WIDTH // 2 - 120 <= mx <= WIDTH // 2 + 120 and 350 <= my <= 390:
                    mode_select_screen()
                    running = False

def mode_select_screen():
    running = True
    while running:
        screen.fill(BLACK)
        solo_button = font.render("Solo Mode", True, ORANGE)
        versus_ai_button = font.render("Versus AI Mode", True, ORANGE)
        screen.blit(solo_button, (WIDTH // 2 - 100, 250))
        screen.blit(versus_ai_button, (WIDTH // 2 - 150, 350))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                if WIDTH // 2 - 100 <= mx <= WIDTH // 2 + 100 and 250 <= my <= 290:
                    game = CyberGuardGame(versus_ai=False)
                    game.start()
                    running = False
                elif WIDTH // 2 - 150 <= mx <= WIDTH // 2 + 150 and 350 <= my <= 390:
                    countdown_screen()
                    game = CyberGuardGame(versus_ai=True)
                    game.start()
                    running = False

def countdown_screen():
    for i, word in enumerate(["Ready", "Set", "Go!"]):
        screen.fill(BLACK)
        text_surface = font.render(word, True, ORANGE)
        screen.blit(text_surface, (WIDTH // 2 - 50, HEIGHT // 2 - 20))
        pygame.display.flip()
        pygame.time.delay(1000)

if __name__ == "__main__":
    home_screen()
