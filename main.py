import pygame
import sys
import time
import os
import math

# Constants
pygame.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
PLAYER_SPEED = 5
PLAYER_WIDTH = 32
PLAYER_HEIGHT = 48
INTERACTION_RADIUS = 50
ROOM_WIDTH = 800

# Nostalgic Colors
PASTEL_PINK = (255, 192, 203)
BABY_BLUE = (137, 207, 240)
LIME_GREEN = (173, 255, 47)
CORAL = (255, 127, 80)
DARK_CORAL = (240, 128, 128)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (51, 255, 51)
DARK_GREEN = (0, 180, 0)

# Game states
GAME_RUNNING = 0
GAME_OVER = 1

# Helper Functions
def load_image(filepath, width=0, height=0):
    """Loads an image, handles errors, and optionally resizes it."""
    try:
        image = pygame.image.load(filepath).convert_alpha()
        if width > 0 and height > 0:
            image = pygame.transform.scale(image, (width, height))
        return image
    except pygame.error as message:
        print(f"Cannot load image: {filepath}")
        raise SystemExit(message)

def wrap_text(text, font, max_width):
    """Wraps text to fit within a specified width."""
    words = text.split(' ')
    lines = []
    current_line = []
    for word in words:
        test_line = ' '.join(current_line + [word])
        width = font.size(test_line)[0]
        if width <= max_width:
            current_line.append(word)
        else:
            lines.append(' '.join(current_line))
            current_line = [word]
    if current_line:
        lines.append(' '.join(current_line))
    return lines

# Classes
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, image):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.x = float(x)
        self.y = float(y)

    def move(self, dx, dy):
        self.x += dx
        self.y += dy
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)

class InteractionPoint:
    def __init__(self, x, y, name, text, options):
        self.x = x
        self.y = y
        self.name = name
        self.text = text
        self.options = options

class Room:
    def __init__(self, name, title, x):
        self.name = name
        self.title = title
        self.x = x
        self.interaction_points = []

    def add_interaction_point(self, x, y, name, text, options):
        self.interaction_points.append(InteractionPoint(x, y, name, text, options))

class Game:
    def __init__(self):
        # Initialization
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Eco Pixel Life")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.typewriter_font = pygame.font.Font(None, 24)
        self.game_state = GAME_RUNNING
        self.show_end_game_dialog = False

        # Load resources
        self.load_images()

        # Create rooms
        self.rooms = [
            Room("bedroom", "Bedroom", 0),
            Room("bathroom", "Bathroom", ROOM_WIDTH),
            Room("kitchen", "Kitchen", ROOM_WIDTH * 2),
            Room("living_room", "Living Room", ROOM_WIDTH * 3)
        ]

        # Create player
        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, self.player_img)

        # Game variables
        self.current_room_index = 0
        self.camera_offset_x = 0
        self.target_camera_offset_x = 0
        self.eco_score = 100
        self.day_stage = 0
        self.day_stages = ["Morning", "Afternoon", "Evening"]
        self.active_bubble = None
        self.typing_text = ""
        self.target_text = ""
        self.typing_speed = 0.05
        self.last_char_time = 0
        self.typing_index = 0
        self.selected_option = 0
        self.completed_interactions = []

        # Create interaction points
        self.create_interaction_points()

    def load_images(self):
        # Load player image
        try:
            self.player_img = load_image('player_character.png', PLAYER_WIDTH, PLAYER_HEIGHT)
        except:
            self.player_img = pygame.Surface((PLAYER_WIDTH, PLAYER_HEIGHT), pygame.SRCALPHA)
            pygame.draw.rect(self.player_img, LIME_GREEN, (0, 0, PLAYER_WIDTH, PLAYER_HEIGHT))
        
        # Room images
        self.room_imgs = {}
        room_names = ["bedroom", "bathroom", "kitchen", "living_room"]
        for room_name in room_names:
            try:
                self.room_imgs[room_name] = load_image(f'{room_name}.png', ROOM_WIDTH, SCREEN_HEIGHT)
            except:
                self.room_imgs[room_name] = pygame.Surface((ROOM_WIDTH, SCREEN_HEIGHT))
                self.room_imgs[room_name].fill(PASTEL_PINK)

        # Interaction point indicator
        self.interaction_img = pygame.Surface((16, 16), pygame.SRCALPHA)
        pygame.draw.circle(self.interaction_img, WHITE, (8, 8), 8)


    def create_interaction_points(self):
        # Bedroom interactions
        self.rooms[0].add_interaction_point(600, 100, "blinds", "Your bedroom blinds are closed. What would you like to do?", [
            {"text": "Open blinds (use natural light)", "score": 10, "next_stage": True},
            {"text": "Keep blinds closed & turn on light", "score": -10, "next_stage": True}
        ])

        self.rooms[0].add_interaction_point(300, 200, "lamp", "Your bedside lamp is off. What would you like to do?", [
            {"text": "Leave it off (if it's daytime)", "score": 5, "next_stage": False},
            {"text": "Turn it on", "score": -5, "next_stage": False}
        ])

        # Bathroom interactions
        self.rooms[1].add_interaction_point(600, 200, "shower", "Time to take a shower. What's your preference?", [
            {"text": "Quick 5-minute shower", "score": 10, "next_stage": False},
            {"text": "Long, hot 20-minute shower", "score": -15, "next_stage": False}
        ])

        # Kitchen interactions
        self.rooms[2].add_interaction_point(600, 200, "fridge", "You're hungry. What will you do?", [
            {"text": "Take what you need & close quickly", "score": 5, "next_stage": False},
            {"text": "Browse with door open for a while", "score": -5, "next_stage": False}
        ])

        # Living room interactions
        self.rooms[3].add_interaction_point(600, 150, "bookshelf", "You want to read a book. What will you do?", [
            {"text": "Read by natural light near the window", "score": 5, "next_stage": False},
            {"text": "Turn on multiple lights to read", "score": -5, "next_stage": False}
        ])

    def apply_crt_effect(self, surface):
        """Apply a simplified CRT screen effect that's more performance-friendly"""
        width, height = surface.get_width(), surface.get_height()
        
        # Create a scanline overlay
        scanlines = pygame.Surface((width, height), pygame.SRCALPHA)
        scanlines.fill((0, 0, 0, 0))  # Transparent black
        
        # Draw scanlines (every 3 pixels)
        for y in range(0, height, 3):
            pygame.draw.line(scanlines, (0, 0, 0, 30), (0, y), (width, y), 1)
        
        # Create a vignette overlay (darkened corners)
        vignette = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # Draw a radial gradient for the vignette
        center = (width // 2, height // 2)
        max_radius = math.sqrt((width // 2)**2 + (height // 2)**2)
        
        # Draw the vignette with a series of circles
        for radius in range(int(max_radius), 0, -20):
            alpha = int(120 * (1 - radius / max_radius))
            pygame.draw.circle(vignette, (0, 0, 0, alpha), center, radius, 20)
        
        # Apply the effects
        surface.blit(scanlines, (0, 0))
        surface.blit(vignette, (0, 0))
        
        return surface


    def draw_end_game_dialog(self):
        # Create dialog box
        dialog_width = 400
        dialog_height = 150
        dialog_x = (SCREEN_WIDTH - dialog_width) // 2
        dialog_y = (SCREEN_HEIGHT - dialog_height) // 2
        
        # Draw dialog background with nostalgic colors
        pygame.draw.rect(self.screen, BABY_BLUE, (dialog_x, dialog_y, dialog_width, dialog_height))
        pygame.draw.rect(self.screen, WHITE, (dialog_x, dialog_y, dialog_width, dialog_height), 3)
        
        # Draw text
        title_surf = self.font.render("End Game?", True, BLACK)
        self.screen.blit(title_surf, (SCREEN_WIDTH//2 - title_surf.get_width()//2, dialog_y + 30))
        
        prompt_surf = self.font.render("Are you sure you want to end the game? (Y/N)", True, BLACK)
        self.screen.blit(prompt_surf, (SCREEN_WIDTH//2 - prompt_surf.get_width()//2, dialog_y + 70))
        
        # Draw pixel-style buttons
        yes_surf = self.font.render("Y - Yes", True, BLACK)
        no_surf = self.font.render("N - No", True, BLACK)
        
        pygame.draw.rect(self.screen, CORAL, (dialog_x + 80, dialog_y + 100, 100, 30))
        pygame.draw.rect(self.screen, WHITE, (dialog_x + 80, dialog_y + 100, 100, 30), 2)
        self.screen.blit(yes_surf, (dialog_x + 100, dialog_y + 105))
        
        pygame.draw.rect(self.screen, LIME_GREEN, (dialog_x + 220, dialog_y + 100, 100, 30))
        pygame.draw.rect(self.screen, WHITE, (dialog_x + 220, dialog_y + 100, 100, 30), 2)
        self.screen.blit(no_surf, (dialog_x + 240, dialog_y + 105))
     
    def check_room_boundaries(self):
            # Keep player within vertical boundaries
            if self.player.y < 0:
                self.player.y = 0
                self.player.rect.y = 0
            elif self.player.y > SCREEN_HEIGHT - PLAYER_HEIGHT:
                self.player.y = SCREEN_HEIGHT - PLAYER_HEIGHT
                self.player.rect.y = int(self.player.y)
            
            # Check horizontal room boundaries
            total_x = self.player.x + (self.current_room_index * ROOM_WIDTH)
            if total_x < 0:
                self.player.x = 0
                self.player.rect.x = 0
            elif total_x > (self.current_room_index * ROOM_WIDTH) + ROOM_WIDTH - PLAYER_WIDTH:
                if self.current_room_index < len(self.rooms) - 1:
                    # Move to next room
                    self.current_room_index += 1
                    self.player.x = 0
                    self.target_camera_offset_x = self.current_room_index * ROOM_WIDTH
                else:
                    # Stay in current room
                    self.player.x = ROOM_WIDTH - PLAYER_WIDTH
                    self.player.rect.x = int(self.player.x)
            elif total_x < self.current_room_index * ROOM_WIDTH:
                if self.current_room_index > 0:
                    # Move to previous room
                    self.current_room_index -= 1
                    self.player.x = ROOM_WIDTH - PLAYER_WIDTH
                    self.target_camera_offset_x = self.current_room_index * ROOM_WIDTH
                else:
                    # Stay in current room
                    self.player.x = 0
                    self.player.rect.x = 0
    
    def update_room_transition(self):
        # Smoothly transition camera between rooms
        if self.camera_offset_x != self.target_camera_offset_x:
            diff = self.target_camera_offset_x - self.camera_offset_x
            self.camera_offset_x += diff * 0.1
            
            # Snap to target if close enough
            if abs(diff) < 1:
                self.camera_offset_x = self.target_camera_offset_x

    def check_day_progress(self):
        # Check if all interactions for current day stage are completed
        all_completed = True
        for room in self.rooms:
            for point in room.interaction_points:
                if point.name not in self.completed_interactions:
                    all_completed = False
                    break
        
        # If all completed, advance to next day stage
        if all_completed:
            self.day_stage += 1
            if self.day_stage >= len(self.day_stages):
                return True  # Game over, day complete
        
        return False
    
    def check_interaction(self):
        if self.active_bubble:
            return
        
        # Get player's global position
        player_global_x = self.player.x + (self.current_room_index * ROOM_WIDTH)
        
        # Check for nearby interaction points
        current_room = self.rooms[self.current_room_index]
        for point in current_room.interaction_points:
            if point.name in self.completed_interactions:
                continue
                
            point_x = current_room.x + point.x
            distance = ((player_global_x + PLAYER_WIDTH/2) - point_x)**2 + ((self.player.y + PLAYER_HEIGHT/2) - point.y)**2
            
            if distance <= INTERACTION_RADIUS**2:
                self.active_bubble = point
                self.target_text = point.text
                self.typing_text = ""
                self.typing_index = 0
                self.last_char_time = time.time()
                self.selected_option = 0
                break

    def update_typing_text(self):
        # Typewriter effect for text bubbles
        current_time = time.time()
        if self.typing_index < len(self.target_text) and current_time - self.last_char_time >= self.typing_speed:
            self.typing_text += self.target_text[self.typing_index]
            self.typing_index += 1
            self.last_char_time = current_time

    def select_option(self):
        if not self.active_bubble:
            return
            
        # Apply selected option effects
        option = self.active_bubble.options[self.selected_option]
        self.eco_score += option["score"]
        
        # Clamp eco score between 0 and 100
        self.eco_score = max(0, min(100, self.eco_score))
        
        # Mark interaction as completed
        self.completed_interactions.append(self.active_bubble.name)
        
        # Advance day stage if needed
        if option.get("next_stage", False):
            self.day_stage += 1
            if self.day_stage >= len(self.day_stages):
                self.game_state = GAME_OVER
        
        # Clear active bubble
        self.active_bubble = None

    def draw_bubble(self):
        # Draw text bubble for interaction
        bubble_width = 500
        bubble_height = 200
        bubble_x = (SCREEN_WIDTH - bubble_width) // 2
        bubble_y = (SCREEN_HEIGHT - bubble_height) // 2
        
        # Draw bubble background
        pygame.draw.rect(self.screen, BABY_BLUE, (bubble_x, bubble_y, bubble_width, bubble_height))
        pygame.draw.rect(self.screen, WHITE, (bubble_x, bubble_y, bubble_width, bubble_height), 2)
        
        # Draw text
        text_lines = wrap_text(self.typing_text, self.typewriter_font, bubble_width - 40)
        for i, line in enumerate(text_lines):
            text_surf = self.typewriter_font.render(line, True, BLACK)
            self.screen.blit(text_surf, (bubble_x + 20, bubble_y + 20 + i * 30))
        
        # Draw options if text is fully typed
        if len(self.typing_text) == len(self.target_text):
            options_y = bubble_y + 100
            for i, option in enumerate(self.active_bubble.options):
                # Highlight selected option
                if i == self.selected_option:
                    pygame.draw.rect(self.screen, LIME_GREEN, (bubble_x + 15, options_y + i * 30 - 5, bubble_width - 30, 25))
                
                option_surf = self.font.render(option["text"], True, BLACK)
                self.screen.blit(option_surf, (bubble_x + 20, options_y + i * 30))

    def draw_game_over(self):
        # Create pixel-style overlay with scanlines effect
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill(BABY_BLUE)
        
        # Add scanlines for retro CRT effect
        for y in range(0, SCREEN_HEIGHT, 4):
            pygame.draw.line(overlay, BLACK, (0, y), (SCREEN_WIDTH, y), 1)
        
        overlay.set_alpha(180)
        self.screen.blit(overlay, (0, 0))
        
        # Get score interpretation
        score_info = self.interpret_score()
        
        # Draw pixel-style border around the entire game over screen
        border_width = 600
        border_height = 400
        border_x = (SCREEN_WIDTH - border_width) // 2
        border_y = (SCREEN_HEIGHT - border_height) // 2
        
        # Draw outer border
        pygame.draw.rect(self.screen, WHITE, (border_x-5, border_y-5, border_width+10, border_height+10), 5)
        pygame.draw.rect(self.screen, BLACK, (border_x, border_y, border_width, border_height), 3)
        
        # Draw title
        title_font = pygame.font.Font(None, 48)
        title_surf = title_font.render("GAME OVER", True, WHITE)
        self.screen.blit(title_surf, (SCREEN_WIDTH//2 - title_surf.get_width()//2, border_y + 30))
        
        # Draw score title with nostalgic color
        score_title_surf = title_font.render(score_info["title"], True, score_info["color"])
        self.screen.blit(score_title_surf, (SCREEN_WIDTH//2 - score_title_surf.get_width()//2, border_y + 80))
        
        # Draw final score
        score_text = f"Final Eco Score: {self.eco_score}"
        score_surf = self.font.render(score_text, True, WHITE)
        self.screen.blit(score_surf, (SCREEN_WIDTH//2 - score_surf.get_width()//2, border_y + 130))
        
        # Draw badge
        badge_surf = self.font.render(f"Achievement: {score_info['badge']}", True, score_info["color"])
        self.screen.blit(badge_surf, (SCREEN_WIDTH//2 - badge_surf.get_width()//2, border_y + 160))
        
        # Draw description (wrapped text)
        desc_lines = wrap_text(score_info["description"], self.font, border_width - 80)
        for i, line in enumerate(desc_lines):
            desc_surf = self.font.render(line, True, WHITE)
            self.screen.blit(desc_surf, (SCREEN_WIDTH//2 - desc_surf.get_width()//2, border_y + 200 + i * 25))
        
        # Draw instructions with pixel-style buttons
        restart_text = "Press ENTER to play again"
        restart_surf = self.font.render(restart_text, True, BLACK)
        
        # Create button background
        button_width = restart_surf.get_width() + 20
        button_height = restart_surf.get_height() + 10
        button_x = SCREEN_WIDTH//2 - button_width//2
        button_y = border_y + 280
        
        pygame.draw.rect(self.screen, LIME_GREEN, (button_x, button_y, button_width, button_height))
        pygame.draw.rect(self.screen, WHITE, (button_x, button_y, button_width, button_height), 2)
        self.screen.blit(restart_surf, (button_x + 10, button_y + 5))
        
        # Quit button
        quit_text = "Press ESC to quit"
        quit_surf = self.font.render(quit_text, True, BLACK)
        
        button_width = quit_surf.get_width() + 20
        button_height = quit_surf.get_height() + 10
        button_x = SCREEN_WIDTH//2 - button_width//2
        button_y = border_y + 330
        
        pygame.draw.rect(self.screen, CORAL, (button_x, button_y, button_width, button_height))
        pygame.draw.rect(self.screen, WHITE, (button_x, button_y, button_width, button_height), 2)
        self.screen.blit(quit_surf, (button_x + 10, button_y + 5))      

    def reset_game(self):
        # Reset game state
        self.game_state = GAME_RUNNING
        self.eco_score = 100
        self.day_stage = 0
        self.active_bubble = None
        self.completed_interactions = []
        
        # Reset player position
        self.player.x = SCREEN_WIDTH // 2
        self.player.y = SCREEN_HEIGHT // 2
        self.player.rect.x = int(self.player.x)
        self.player.rect.y = int(self.player.y)
        
        # Reset camera
        self.current_room_index = 0
        self.camera_offset_x = 0
        self.target_camera_offset_x = 0
    
    def interpret_score(self):
        """Returns a detailed interpretation of the player's eco score"""
        if self.eco_score >= 90:
            title = "ECO SUPERHERO!"
            color = GREEN
            description = "You're a true environmental champion! Your eco-friendly choices have made a huge impact."
            pixel_badge = "Platinum Pixel Badge"
        elif self.eco_score >= 85:
            title = "ECO WARRIOR"
            color = LIME_GREEN
            description = "Great job! Your planet-friendly decisions have really paid off."
            pixel_badge = "Gold Pixel Badge"
        elif self.eco_score >= 75:
            title = "ECO APPRENTICE"
            color = BABY_BLUE
            description = "You're on the right track! A few more eco-conscious choices and you'll be a true eco warrior."
            pixel_badge = "Silver Pixel Badge"
        elif self.eco_score >= 65:
            title = "ECO NOVICE"
            color = CORAL
            description = "You're making some good choices, but there's room for improvement in your eco habits."
            pixel_badge = "Bronze Pixel Badge"
        else:
            title = "ECO BEGINNER"
            color = DARK_CORAL
            description = "Time to brush up on your eco knowledge! Small changes can make a big difference."
            pixel_badge = "Plastic Pixel Badge"
        
        return {
            "title": title,
            "color": color,
            "description": description,
            "badge": pixel_badge
        }
    
    def draw_ui(self):
    # Draw eco score with gradient color based on score
        score_text = f"Eco Score: {self.eco_score}"
        
        # Color changes based on score value
        if self.eco_score >= 90:
            score_color = GREEN
        elif self.eco_score >= 75:
            score_color = LIME_GREEN
        elif self.eco_score >= 65:
            score_color = CORAL
        else:
            score_color = DARK_CORAL
        
        score_surf = self.font.render(score_text, True, score_color)
        
        # Create a small background panel for the score
        score_panel = pygame.Surface((score_surf.get_width() + 20, score_surf.get_height() + 10))
        score_panel.fill(BABY_BLUE)
        pygame.draw.rect(score_panel, WHITE, (0, 0, score_panel.get_width(), score_panel.get_height()), 2)
        score_panel.set_alpha(220)  # Slight transparency
    
        self.screen.blit(score_panel, (SCREEN_WIDTH - score_panel.get_width() - 5, 5))
        self.screen.blit(score_surf, (SCREEN_WIDTH - score_surf.get_width() - 15, 10))

        # Draw day progress with pixel-style panel
        if self.day_stage < len(self.day_stages):
            day_text = f"Time: {self.day_stages[self.day_stage]}"
        else:
            day_text = "Time: End of Day"
        day_surf = self.font.render(day_text, True, WHITE)
        
        # Create a small background panel
        day_panel = pygame.Surface((day_surf.get_width() + 20, day_surf.get_height() + 10))
        day_panel.fill(PASTEL_PINK)
        pygame.draw.rect(day_panel, WHITE, (0, 0, day_panel.get_width(), day_panel.get_height()), 2)
        
        self.screen.blit(day_panel, (5, 5))
        self.screen.blit(day_surf, (15, 10))
        
        # Draw room name with pixel-style border
        room_name = self.rooms[self.current_room_index].title
        room_surf = self.font.render(f"Room: {room_name}", True, BLACK)
        
        # Create background panel
        room_panel = pygame.Surface((room_surf.get_width() + 20, room_surf.get_height() + 10))
        room_panel.fill(LIME_GREEN)
        pygame.draw.rect(room_panel, WHITE, (0, 0, room_panel.get_width(), room_panel.get_height()), 2)
        
        self.screen.blit(room_panel, (5, 45))
        self.screen.blit(room_surf, (15, 50))
        
        # Draw hint text with pixel-style border at bottom
        if not self.active_bubble:
            hint_text = "Press SPACE near objects to interact"
            hint_surf = self.font.render(hint_text, True, WHITE)
            
            # Create background panel
            hint_panel = pygame.Surface((hint_surf.get_width() + 20, hint_surf.get_height() + 10))
            hint_panel.fill(DARK_CORAL)
            pygame.draw.rect(hint_panel, WHITE, (0, 0, hint_panel.get_width(), hint_panel.get_height()), 2)
            
            self.screen.blit(hint_panel, (SCREEN_WIDTH//2 - hint_panel.get_width()//2, SCREEN_HEIGHT - hint_panel.get_height() - 5))
            self.screen.blit(hint_surf, (SCREEN_WIDTH//2 - hint_surf.get_width()//2, SCREEN_HEIGHT - hint_surf.get_height() - 10))

    
    def run(self):
        running = True
        while running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    self.handle_event(event)
            
            # Update game state
            self.update()
            
            # Render game
            self.render()
            
            # Cap the frame rate
            self.clock.tick(60)
        
        # Clean up when the game exits
        pygame.quit()
        sys.exit()


    def handle_event(self, event):
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        # Add this section to allow ending the game with ESC
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE and self.game_state == GAME_RUNNING:
            # Show confirmation dialog
            self.show_end_game_dialog = True
            return

        # Handle end game dialog
        if self.show_end_game_dialog:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_y:
                    self.game_state = GAME_OVER
                    self.show_end_game_dialog = False
                elif event.key == pygame.K_n:
                    self.show_end_game_dialog = False
            return

        if self.game_state == GAME_OVER:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.reset_game()
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
            return

        if self.active_bubble:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.selected_option = max(0, self.selected_option - 1)
                elif event.key == pygame.K_DOWN:
                    self.selected_option = min(len(self.active_bubble.options) - 1, self.selected_option + 1)
                elif event.key == pygame.K_RETURN and len(self.typing_text) == len(self.target_text):
                    self.select_option()
            return

        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            self.check_interaction()

    def update(self):
        if self.game_state == GAME_OVER:
            return

        if self.active_bubble:
            self.update_typing_text()
            return

        # Move player
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.player.move(-PLAYER_SPEED, 0)
        if keys[pygame.K_RIGHT]:
            self.player.move(PLAYER_SPEED, 0)
        if keys[pygame.K_UP]:
            self.player.move(0, -PLAYER_SPEED)
        if keys[pygame.K_DOWN]:
            self.player.move(0, PLAYER_SPEED)

        # Check room boundaries
        self.check_room_boundaries()

        # Update room transition
        self.update_room_transition()

        # Check day progress
        if self.check_day_progress():
            self.game_state = GAME_OVER

    def render(self):
        # Clear the screen
        self.screen.fill(PASTEL_PINK)

        # Draw rooms
        for room in self.rooms:
            room_x = room.x - self.camera_offset_x
            if -ROOM_WIDTH < room_x < SCREEN_WIDTH:
                self.screen.blit(self.room_imgs[room.name], (room_x, 0))

                # Draw interaction points
                for point in room.interaction_points:
                    if point.name not in self.completed_interactions:
                        point_x = room_x + point.x
                        pygame.draw.circle(self.screen, LIME_GREEN, (int(point_x), point.y), 8)
                        pygame.draw.circle(self.screen, WHITE, (int(point_x), point.y), 8, 2)

        # Draw player
        player_x = self.player.x + (self.current_room_index * ROOM_WIDTH) - self.camera_offset_x
        self.screen.blit(self.player.image, (int(player_x), self.player.y))

        # Draw UI
        self.draw_ui()

        # Draw active bubble
        if self.active_bubble:
            self.draw_bubble()

        # Draw game over screen
        if self.game_state == GAME_OVER:
            self.draw_game_over()
            
        # Draw end game dialog if active
        if self.show_end_game_dialog:
            self.draw_end_game_dialog()
        
        # Apply CRT effect
        self.apply_crt_effect(self.screen)
        
        # Update the display
        pygame.display.flip()



    
if __name__ == "__main__":
    game = Game()
    try:
        game.run()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        pygame.quit()
        sys.exit()
