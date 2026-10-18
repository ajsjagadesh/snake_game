import pygame
import time
import random
import json
import os

# --- Configuration & Constants ---
pygame.init()
pygame.mixer.init() # Initialize the mixer for sound

# Colors (Neon Palette)
BG_COLOR = (10, 10, 25)
SNAKE_COLOR = (0, 255, 200)
SNAKE_HEAD_COLOR = (255, 255, 255)
FOOD_COLOR = (255, 0, 150)
TEXT_COLOR = (255, 255, 255)
UI_ACCENT = (100, 100, 255)

# Screen Settings
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("NEON SNAKE - SOUND EDITION")
clock = pygame.time.Clock()
font_main = pygame.font.SysFont("Segoe UI", 30, bold=True)
font_small = pygame.font.SysFont("Segoe UI", 18)

# File for High Score
SCORE_FILE = "highscore.json"

# --- Sound Loading Function ---
def load_sounds():
    sounds = {}
    try:
        # Replace these filenames with your actual files
        sounds['eat'] = pygame.mixer.Sound("eat.wav")
        sounds['die'] = pygame.mixer.Sound("die.wav")
        sounds['click'] = pygame.mixer.Sound("click.wav")
        print("Sounds loaded successfully.")
    except pygame.error as e:
        print(f"Warning: Could not load sounds. ({e}) - Make sure .wav files are in the folder.")
    return sounds

# Global sound dictionary
SOUNDS = load_sounds()

def load_highscore():
    if os.path.exists(SCORE_FILE):
        try:
            with open(SCORE_FILE, "r") as f:
                return json.load(f).get("highscore", 0)
        except:
            return 0
    return 0

def save_highscore(score):
    current_high = load_highscore()
    if score > current_high:
        with open(SCORE_FILE, "w") as f:
            json.dump({"highscore": score}, f)

def draw_rounded_rect(surface, color, rect, radius=10):
    pygame.draw.rect(surface, color, rect, border_radius=radius)

def show_message(text, y_offset=0, color=TEXT_COLOR):
    surf = font_main.render(text, True, color)
    rect = surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + y_offset))
    screen.blit(surf, rect)

# --- Game Classes ---
class Snake:
    def __init__(self):
        self.reset()

    def reset(self):
        self.body = [[WIDTH // 2, HEIGHT // 2], 
                      [WIDTH // 2 - 10, HEIGHT // 2], 
                      [WIDTH // 2 - 20, HEIGHT // 2]]
        self.direction = pygame.Vector2(10, 0)
        self.current_speed = 15

    def move(self):
        new_x = self.body[0][0] + self.direction.x
        new_y = self.body[0][1] + self.direction.y
        new_head = [int(new_x), int(new_y)]
        
        if new_head[0] < 0 or new_head[0] >= WIDTH or new_head[1] < 0 or new_head[1] >= HEIGHT:
            return False
        
        if new_head in self.body:
            return False
            
        self.body.insert(0, new_head)
        self.body.pop()
        return True

    def draw(self):
        for i, segment in enumerate(self.body):
            color = SNAKE_HEAD_COLOR if i == 0 else SNAKE_COLOR
            size = 10 if i == 0 else 9
            draw_rounded_rect(screen, color, (segment[0], segment[1], size, size), 5)

class Game:
    def __init__(self):
        self.snake = Snake()
        self.food = self.spawn_food()
        self.score = 0
        self.state = "START_MENU" 
        self.high_score = load_highscore()
        self.speed = 8
        self.count = 0

    def spawn_food(self):
        while True:
            x = random.randint(0, (WIDTH - 20) // 10) * 10
            y = random.randint(0, (HEIGHT - 20) // 10) * 10
            if [x, y] not in self.snake.body:
                return [x, y]

    def update(self):
        if self.state == "PLAYING":
            if self.snake.move():
                if self.snake.body[0] == self.food:
                    self.score += 10
                    # Play Eat Sound
                    if 'eat' in SOUNDS: SOUNDS['eat'].play()
                    self.count +=1
                    if self.count > 3 :
                        self.speed += 1
                        self.count = 0
                    
                    self.snake.current_speed = min(30, self.snake.current_speed + 0.3)
                    self.food = self.spawn_food()
                    
                    new_tail = [self.snake.body[-1][0] - self.snake.direction.x, 
                                 self.snake.body[-1][1] - self.snake.direction.y]
                    self.snake.body.insert(0, self.snake.body[0])
                    self.snake.body.pop()
                    self.snake.body.append(new_tail)
                
            else:
                # Play Die Sound
                if 'die' in SOUNDS: SOUNDS['die'].play()
                self.state = "GAME_OVER"
                save_highscore(self.score)

    def draw(self):
        screen.fill(BG_COLOR)
        
        if self.state == "START_MENU":
            show_message("NEON SNAKE", -50)
            show_message("PRESS SPACE TO START", 50, UI_ACCENT)
            show_message(f"High Score: {self.high_score}", 150, (150, 150, 150))
            
        elif self.state == "PLAYING":
            self.snake.draw()
            draw_rounded_rect(screen, FOOD_COLOR, (self.food[0], self.food[1], 10, 10), 3)
            score_surf = font_small.render(f"Score: {self.score}", True, TEXT_COLOR)
            screen.blit(score_surf, (20, 20))

        elif self.state == "GAME_OVER":
            show_message("GAME OVER", -30, (255, 0, 150))
            show_message(f"Final Score: {self.score}", 30, TEXT_COLOR)
            show_message("Press R to Restart or Q to Quit", 100, UI_ACCENT)

        pygame.display.update()

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                if event.type == pygame.KEYDOWN:
                    # Selection Sounds (Click)
                    if 'click' in SOUNDS: SOUNDS['click'].play()

                    if self.state == "START_MENU":
                        if event.key == pygame.K_SPACE:
                            self.state = "PLAYING"
                    
                    elif self.state == "PLAYING":
                        if event.key == pygame.K_UP and self.snake.direction.y == 0:
                            self.snake.direction = pygame.Vector2(0, -10)
                        elif event.key == pygame.K_DOWN and self.snake.direction.y == 0:
                            self.snake.direction = pygame.Vector2(0, 10)
                        elif event.key == pygame.K_LEFT and self.snake.direction.x == 0:
                            self.snake.direction = pygame.Vector2(-10, 0)
                        elif event.key == pygame.K_RIGHT and self.snake.direction.x == 0:
                            self.snake.direction = pygame.Vector2(10, 0)
                            
                    elif self.state == "GAME_OVER":
                        if event.key == pygame.K_r:
                            self.snake.reset()
                            self.score = 0
                            self.state = "PLAYING"
                        if event.key == pygame.K_q:
                            running = False

            self.update()
            self.draw()
            print(f"Current speed: {self.speed}")
            clock.tick(self.speed)

        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()
