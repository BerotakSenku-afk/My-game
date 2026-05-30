import pygame
import sys
import math
import random
import pygame.gfxdraw
import json
import os

# --- INTERFACES GETAR ANDROID NATIVE ---
IS_ANDROID = False
try:
    from jnius import autoclass
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    activity = PythonActivity.mActivity
    Context = autoclass('android.content.Context')
    vibrator_service = activity.getSystemService(Context.VIBRATOR_SERVICE)
    IS_ANDROID = True
except ImportError:
    vibrator_service = None

pygame.init()

WIDTH, HEIGHT = 450, 750
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED | pygame.FULLSCREEN)
pygame.display.set_caption("Brick Breaker - Dynamic Island Settings")

# --- WARNA ---
BG_COLOR = (24, 34, 64)
WHITE = (255, 255, 255)
BALL_COLOR = (255, 180, 0)
RED = (231, 76, 60)
GREEN = (46, 204, 113)
BLUE = (52, 152, 219)
YELLOW = (241, 196, 15)
CYAN = (0, 200, 255)
BOMB_BG = (40, 40, 40)
SLIDER_BG = (50, 60, 90)
OVERLAY_COLOR = (15, 22, 42, 200)
BLACK = (0, 0, 0)
PURPLE = (128, 0, 128)

# --- GLOBAL SETTINGS ---
VIBRATION_ON = True
FPS_OPTIONS = [30, 60, 90, 120, "Infinite"]
FPS_INDEX = 1
TARGET_FPS = 60

UNLOCKED_ACHIEVEMENTS = []
SELECTED_SKIN_IDX = 0

SAVE_FILE = "savegame.json"

# --- ACHIEVEMENT DATA ---
ACHIEVEMENT_MILESTONES = {
    1: "Player baru",
    50: "Normal lah",
    100: "Wih keren!!",
    150: "Ngga bosen?",
    200: "Beneran nih?",
    1000: "Sesepuh"
}

def load_game_data():
    global VIBRATION_ON, FPS_INDEX, UNLOCKED_ACHIEVEMENTS, SELECTED_SKIN_IDX
    default_data = {"level": 1, "vibration": True, "fps_index": 1, "achievements": [], "skin": 0}
    
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r") as f:
                data = json.load(f)
                level = data.get("level", 1)
                VIBRATION_ON = data.get("vibration", True)
                FPS_INDEX = data.get("fps_index", 1)
                UNLOCKED_ACHIEVEMENTS = data.get("achievements", [])
                SELECTED_SKIN_IDX = data.get("skin", 0)
                if FPS_INDEX >= len(FPS_OPTIONS): FPS_INDEX = 1
                return level
        except Exception:
            return 1
    return 1

def save_game_data(level):
    data = {
        "level": level,
        "vibration": VIBRATION_ON,
        "fps_index": FPS_INDEX,
        "achievements": UNLOCKED_ACHIEVEMENTS,
        "skin": SELECTED_SKIN_IDX
    }
    try:
        with open(SAVE_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        pass

current_game_level = load_game_data()

# --- FONT ---
FONT_FILE = "GameFont.ttf"
if os.path.exists(FONT_FILE):
    FONT_MICRO = pygame.font.Font(FONT_FILE, 18)
    FONT_MINI = pygame.font.Font(FONT_FILE, 28)    
    FONT_SUB = pygame.font.Font(FONT_FILE, 32)     
    FONT_UI = pygame.font.Font(FONT_FILE, 44)      
    FONT_TITLE = pygame.font.Font(FONT_FILE, 70)   
    FONT_BUTTON = pygame.font.Font(FONT_FILE, 34)  
else:
    FONT_MINI = pygame.font.SysFont("Arial", 28, bold=True)
    FONT_SUB = pygame.font.SysFont("Arial", 32, bold=True)
    FONT_UI = pygame.font.SysFont("Arial", 44, bold=True)
    FONT_TITLE = pygame.font.SysFont("Arial", 72, bold=True)
    FONT_BUTTON = pygame.font.SysFont("Arial", 36, bold=True)

# --- LOAD ASSETS ---
def load_ui_image(filename, fallback_color, size=(32, 32)):
    if os.path.exists(filename):
        try:
            img = pygame.image.load(filename).convert_alpha()
            return pygame.transform.smoothscale(img, size)
        except Exception:
            pass
    surf = pygame.Surface(size, pygame.SRCALPHA)
    pygame.draw.circle(surf, fallback_color, (size[0]//2, size[1]//2), size[0]//2)
    return surf

IMG_SETTING = load_ui_image("ikon_setting.png", YELLOW, (36, 36))
IMG_VIBRATION = load_ui_image("vibration.png", CYAN, (32, 32))
IMG_HOME = load_ui_image("home.png", BLUE, (36, 36))
IMG_ACHIEVE = load_ui_image("ikon_achieve.png", YELLOW, (32, 32))
IMG_LEADER = load_ui_image("leader.png", CYAN, (32, 32))

SKIN_NAMES = ["Default", "pydroball.png", "Player1.png", "Player2.png", "bola.png", "Gemini.png", "Rzzky.png"]
SKIN_BALLS = [None] 
SKIN_PROFILES = [None] 

# Skin Default (Warna Oranye)
def_prof = pygame.Surface((80, 80), pygame.SRCALPHA)
pygame.draw.circle(def_prof, BALL_COLOR, (40, 40), 40)
SKIN_PROFILES[0] = def_prof

for name in SKIN_NAMES[1:]:
    SKIN_BALLS.append(load_ui_image(name, PURPLE, (12, 12)))
    SKIN_PROFILES.append(load_ui_image(name, PURPLE, (80, 80)))

COLUMNS = 7
BRICK_SIZE = WIDTH // COLUMNS  

def render_sharp_text(text, font, color, surface, position, anchor="center"):
    raw_surf = font.render(text, True, color)
    w, h = raw_surf.get_size()
    sharp_surf = pygame.transform.smoothscale(raw_surf, (w // 2, h // 2))
    rect = sharp_surf.get_rect()
    if anchor == "center": rect.center = position
    elif anchor == "midleft": rect.midleft = position
    elif anchor == "midright": rect.midright = position
    elif anchor == "midbottom": rect.midbottom = position
    surface.blit(sharp_surf, rect)

def haptic_vibrate(duration_ms):
    if VIBRATION_ON and IS_ANDROID and vibrator_service:
        try:
            vibrator_service.vibrate(duration_ms)
        except Exception:
            pass

def draw_aa_circle(surface, x, y, radius, color):
    pygame.gfxdraw.aacircle(surface, int(x), int(y), radius, color)
    pygame.gfxdraw.filled_circle(surface, int(x), int(y), radius, color)

def calculate_aim_points(start_x, start_y, angle, bricks):
    points = [(start_x, start_y)]
    x, y = float(start_x), float(start_y)
    step_size = 5.0
    dx = math.cos(angle) * step_size
    dy = math.sin(angle) * step_size
    radius = 6
    has_bounced = False  
    max_steps = 350      
    
    for _ in range(max_steps):
        x += dx
        y += dy
        if x - radius <= 0: x = radius; dx *= -1; points.append((x, y)); has_bounced = True
        elif x + radius >= WIDTH: x = WIDTH - radius; dx *= -1; points.append((x, y)); has_bounced = True
        if y - radius <= 60: y = 60 + radius; dy *= -1; points.append((x, y)); has_bounced = True

        sim_rect = pygame.Rect(x - radius, y - radius, radius * 2, radius * 2)
        hit_brick = False
        for brick in bricks:
            if sim_rect.colliderect(brick.rect):
                ol_l = (x + radius) - brick.rect.left
                ol_r = brick.rect.right - (x - radius)
                ol_t = (y + radius) - brick.rect.top
                ol_b = brick.rect.bottom - (y - radius)
                min_overlap = min(ol_l, ol_r, ol_t, ol_b)
                
                if min_overlap == ol_l: dx = -abs(dx); x = brick.rect.left - radius
                elif min_overlap == ol_r: dx = abs(dx); x = brick.rect.right + radius
                elif min_overlap == ol_t: dy = -abs(dy); y = brick.rect.top - radius
                elif min_overlap == ol_b: dy = abs(dy); y = brick.rect.bottom + radius
                
                points.append((x, y))
                hit_brick = True
                break
                
        if hit_brick: has_bounced = True
        if has_bounced and len(points) > 2: break
            
    points.append((x, y))
    return points

class Particle:
    def __init__(self, x, y, color, dx, dy, lifetime, size):
        self.x = x
        self.y = y
        self.color = color
        self.dx = dx
        self.dy = dy
        self.lifetime = lifetime
        self.size = size
    def update(self):
        self.x += self.dx
        self.y += self.dy
        self.lifetime -= 1
        self.size -= 0.1
    def draw(self, surface):
        if self.lifetime > 0 and self.size > 0:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), int(self.size))

def spawn_bomb_particles(x, y, particles_list):
    for _ in range(35):
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(2, 7)
        particles_list.append(Particle(x, y, random.choice([RED, YELLOW, (255, 120, 0)]), math.cos(angle) * speed, math.sin(angle) * speed, random.randint(20, 40), random.uniform(3, 6)))

def spawn_laser_particles(y, particles_list):
    for _ in range(50):
        speed = random.uniform(2, 6)
        particles_list.append(Particle(random.randint(0, WIDTH), y, random.choice([CYAN, WHITE, BLUE]), random.choice([-1, 1]) * speed * 2, random.uniform(-0.5, 0.5), random.randint(15, 30), random.uniform(2, 4)))

class Brick:
    def __init__(self, x, y, hp, brick_type="normal"):
        self.rect = pygame.Rect(x + 1, y + 1, BRICK_SIZE - 2, BRICK_SIZE - 2)
        self.hp = hp
        self.brick_type = brick_type
        self.update_color() 
    def update_color(self):
        if self.hp > 50: self.color = PURPLE
        elif self.hp > 25: self.color = RED
        elif self.hp > 15: self.color = YELLOW
        elif self.hp > 8: self.color = GREEN
        else: self.color = BLUE
    def draw(self, surface):
        if self.brick_type == "bomb":
            pygame.draw.rect(surface, BOMB_BG, self.rect, border_radius=4)
            pygame.draw.rect(surface, RED, self.rect, width=2, border_radius=4)
            render_sharp_text(str(self.hp), FONT_SUB, WHITE, surface, (self.rect.centerx, self.rect.centery - 6))
            render_sharp_text("BOMB", FONT_MINI, RED, surface, (self.rect.centerx, self.rect.centery + 12))
        elif self.brick_type == "laser":
            pygame.draw.rect(surface, CYAN, self.rect, border_radius=4)
            pygame.draw.rect(surface, WHITE, self.rect, width=2, border_radius=4)
            render_sharp_text(str(self.hp), FONT_SUB, BLACK, surface, (self.rect.centerx, self.rect.centery - 6))
            render_sharp_text("<-->", FONT_MINI, BLACK, surface, (self.rect.centerx, self.rect.centery + 12))
        else:
            pygame.draw.rect(surface, self.color, self.rect, border_radius=4)
            text_color = (0, 0, 0) if self.color == YELLOW else WHITE
            render_sharp_text(str(self.hp), FONT_SUB, text_color, surface, self.rect.center)

def activate_special_brick(dead_brick, bricks_list, particles_list):
    if dead_brick.brick_type == "bomb":
        haptic_vibrate(80) 
        spawn_bomb_particles(dead_brick.rect.centerx, dead_brick.rect.centery, particles_list)
        for b in bricks_list[:]:
            if math.hypot(b.rect.centerx - dead_brick.rect.centerx, b.rect.centery - dead_brick.rect.centery) <= BRICK_SIZE * 4:
                b.hp -= 1000000 
                b.update_color()
                if b.hp <= 0 and b in bricks_list:
                    bricks_list.remove(b)
                    activate_special_brick(b, bricks_list, particles_list) 
    elif dead_brick.brick_type == "laser":
        haptic_vibrate(50)
        spawn_laser_particles(dead_brick.rect.centery, particles_list)
        for b in bricks_list[:]:
            if abs(b.rect.centery - dead_brick.rect.centery) < BRICK_SIZE // 2:
                b.hp -= 1000000 
                b.update_color()
                if b.hp <= 0 and b in bricks_list:
                    bricks_list.remove(b)
                    activate_special_brick(b, bricks_list, particles_list)

class Ball:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.radius = 6 
        self.dx = 0.0
        self.dy = 0.0
        self.speed = 10.0 
        self.active = False
        self.returning = False 

    def launch(self, angle):
        angle += random.uniform(-0.005, 0.005)
        self.dx = math.cos(angle) * self.speed
        self.dy = math.sin(angle) * self.speed
        self.active = True
        self.returning = False

    def update(self, bricks, launcher_x, launcher_y, particles_list):
        if not self.active: return False

        if self.returning:
            dx = launcher_x - self.x
            dy = launcher_y - self.y
            dist = math.hypot(dx, dy)
            return_speed = 30.0  
            if dist <= return_speed:
                self.x = float(launcher_x); self.y = float(launcher_y)
                self.active = False; self.returning = False
                return True
            else:
                self.x += (dx / dist) * return_speed; self.y += (dy / dist) * return_speed
            return False

        self.x += self.dx
        if self.x - self.radius <= 0: self.x = self.radius; self.dx *= -1
        elif self.x + self.radius >= WIDTH: self.x = WIDTH - self.radius; self.dx *= -1

        ball_rect = pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius*2, self.radius*2)
        hit_x = None
        for brick in bricks[:]:
            if ball_rect.colliderect(brick.rect):
                hit_x = brick; break
                
        if hit_x:
            self.dx *= -1
            if self.dx > 0: self.x = hit_x.rect.right + self.radius
            else: self.x = hit_x.rect.left - self.radius
            self.x = max(self.radius, min(WIDTH - self.radius, self.x))
            
            hit_x.hp -= 1; hit_x.update_color(); haptic_vibrate(25) 
            if hit_x.hp <= 0: 
                bricks.remove(hit_x)
                activate_special_brick(hit_x, bricks, particles_list)

        self.y += self.dy
        if self.y - self.radius <= 60: self.y = 60 + self.radius; self.dy *= -1

        ball_rect = pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius*2, self.radius*2)
        hit_y = None
        for brick in bricks[:]:
            if ball_rect.colliderect(brick.rect):
                hit_y = brick; break
                
        if hit_y:
            self.dy *= -1
            if self.dy > 0: self.y = hit_y.rect.bottom + self.radius
            else: self.y = hit_y.rect.top - self.radius
            
            hit_y.hp -= 1; hit_y.update_color(); haptic_vibrate(25) 
            if hit_y.hp <= 0: 
                bricks.remove(hit_y)
                activate_special_brick(hit_y, bricks, particles_list)

        if self.y + self.radius >= HEIGHT - 100:
            self.active = False
            return True
        return False

    def draw(self, surface):
        if self.active or self.returning:
            if SELECTED_SKIN_IDX == 0:
                draw_aa_circle(surface, self.x, self.y, self.radius, BALL_COLOR)
            else:
                img = SKIN_BALLS[SELECTED_SKIN_IDX]
                if img:
                    surface.blit(img, (int(self.x - self.radius), int(self.y - self.radius)))
                else:
                    draw_aa_circle(surface, self.x, self.y, self.radius, BALL_COLOR)

def spawn_bricks(level):
    bricks = []
    rows = min(2 + (level // 3), 6)
    offset_x = (WIDTH % COLUMNS) // 2
    for row in range(rows):
        for col in range(COLUMNS):
            if random.random() > 0.4:  
                x = offset_x + col * BRICK_SIZE
                y = 100 + row * BRICK_SIZE
                hp = random.randint(level * 3, level * 7)
                brick_type = "normal"
                if level >= 5:
                    rand_val = random.random()
                    if rand_val < 0.08: brick_type = "bomb"
                    elif rand_val < 0.16: brick_type = "laser"
                bricks.append(Brick(x, y, hp, brick_type))
    return bricks
    
def draw_launcher_skin(surface, x, y):
      if SELECTED_SKIN_IDX == 0 or not SKIN_BALLS[SELECTED_SKIN_IDX]:
      	draw_aa_circle(surface, x, y, 6, BALL_COLOR)
      else:
      	surface.blit(SKIN_BALLS[SELECTED_SKIN_IDX], (int(x - 6), int(y - 6)))


class DynamicIslandSettings:
    def __init__(self, current_level_ref):
        self.is_open = False
        self.alpha = 0          
        self.current_alpha = 0.0
        self.level_ref = current_level_ref
        
        self.icon_x = WIDTH - 40
        self.icon_y = 30
        self.icon_rect = pygame.Rect(self.icon_x - 20, self.icon_y - 20, 40, 40)
        self.menu_center_x = WIDTH // 2
        self.menu_center_y = 135  
        
        self.min_w, self.min_h = 40, 40
        self.max_w, self.max_h = 370, 160
        self.current_w = float(self.min_w)
        self.current_h = float(self.min_h)

        self.vib_btn = pygame.Rect(0, 0, 0, 0)
        self.fps_left = pygame.Rect(0, 0, 0, 0)
        self.fps_right = pygame.Rect(0, 0, 0, 0)

    def update(self):
        target_w = self.max_w if self.is_open else self.min_w
        target_h = self.max_h if self.is_open else self.min_h
        self.alpha = 255 if self.is_open else 0
        self.current_w += (target_w - self.current_w) * 0.18
        self.current_h += (target_h - self.current_h) * 0.18
        self.current_alpha += (self.alpha - self.current_alpha) * 0.15

    def draw(self, surface):
        w = int(self.current_w); h = int(self.current_h)
        a = max(0, min(255, int(self.current_alpha)))
        factor = (w - self.min_w) / (self.max_w - self.min_w) if self.max_w != self.min_w else 1.0
        cx = self.icon_x + (self.menu_center_x - self.icon_x) * factor
        cy = self.icon_y + (self.menu_center_y - self.icon_y) * factor
        x = int(cx - w // 2); y = int(cy - h // 2)

        if self.is_open and w > 320:
            self.vib_btn = pygame.Rect(x + 250, y + 35, 80, 35)
            self.fps_left = pygame.Rect(x + 230, y + 95, 30, 35)
            self.fps_right = pygame.Rect(x + 320, y + 95, 30, 35)
        else:
            self.vib_btn = pygame.Rect(0,0,0,0)
            self.fps_left = self.fps_right = pygame.Rect(0,0,0,0)

        island_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(island_surf, (10, 15, 30, a if self.is_open else 255), (0, 0, w, h), border_radius=h//2 if h < 60 else 22)
        pygame.draw.rect(island_surf, (70, 85, 120, a if self.is_open else 255), (0, 0, w, h), width=2, border_radius=h//2 if h < 60 else 22)

        if self.is_open and a > 120 and h > 100:
            island_surf.blit(IMG_VIBRATION, (25, 35))
            render_sharp_text("Haptic Vibration", FONT_SUB, WHITE, island_surf, (70, 52), anchor="midleft")
            vib_color = GREEN if VIBRATION_ON else RED
            pygame.draw.rect(island_surf, vib_color, (250, 35, 80, 35), border_radius=8)
            render_sharp_text("ON" if VIBRATION_ON else "OFF", FONT_MINI, WHITE, island_surf, (290, 52))
            render_sharp_text("FPS Lock", FONT_SUB, WHITE, island_surf, (70, 112), anchor="midleft")
            render_sharp_text("<", FONT_SUB, YELLOW, island_surf, (245, 112))
            render_sharp_text(str(FPS_OPTIONS[FPS_INDEX]), FONT_SUB, WHITE, island_surf, (290, 112))
            render_sharp_text(">", FONT_SUB, YELLOW, island_surf, (335, 112))
        
        if not self.is_open and w < 50:
            island_surf.blit(IMG_SETTING, (w//2 - 18, h//2 - 18))
        surface.blit(island_surf, (x, y))
         
    
    def handle_click(self, pos, current_level):
        global VIBRATION_ON, FPS_INDEX
        mx, my = pos
        self.level_ref = current_level 
        if not self.is_open:
            if self.icon_rect.collidepoint(mx, my):
                self.is_open = True; haptic_vibrate(40); return True
            return False
        if self.is_open:
            if self.vib_btn.collidepoint(mx, my): VIBRATION_ON = not VIBRATION_ON; haptic_vibrate(40); return True
            elif self.fps_left.collidepoint(mx, my): FPS_INDEX = (FPS_INDEX - 1) % len(FPS_OPTIONS); haptic_vibrate(30); return True
            elif self.fps_right.collidepoint(mx, my): FPS_INDEX = (FPS_INDEX + 1) % len(FPS_OPTIONS); haptic_vibrate(30); return True

            w, h = int(self.current_w), int(self.current_h)
            factor = (w - self.min_w) / (self.max_w - self.min_w) if self.max_w != self.min_w else 1.0
            cx = self.icon_x + (self.menu_center_x - self.icon_x) * factor
            cy = self.icon_y + (self.menu_center_y - self.icon_y) * factor
            main_box = pygame.Rect(int(cx - w//2), int(cy - h//2), w, h)
            if not main_box.collidepoint(mx, my):
                self.is_open = False; haptic_vibrate(40); save_game_data(self.level_ref); return True
                return False
    


def main():
    global FPS_INDEX, current_game_level, UNLOCKED_ACHIEVEMENTS, SELECTED_SKIN_IDX
    clock = pygame.time.Clock()
    
    STATE_MENU = 0
    STATE_PLAYING = 1
    STATE_PAUSED = 2  
    STATE_CLEAR = 3
    STATE_GAMEOVER = 4
    STATE_HOME = 5
    game_state = STATE_MENU

    launcher_x = WIDTH // 2
    launcher_y = HEIGHT - 120 
    
    level = current_game_level 
    balls = []
    bricks = []
    particles = []
    new_achievements_queue = []

    island_ui = DynamicIslandSettings(level)

    aiming = True
    is_dragging = False
    slider_x = WIDTH // 2
    slider_y = HEIGHT - 40
    
    aim_angle = -math.pi / 2
    shooting = False
    shoot_delay = 0
    current_ball_idx = 0
    fast_forward = False

    # Tombol Menu
    btn_pause_rect = pygame.Rect(WIDTH - 165, 15, 70, 30)
    skip_btn_rect = pygame.Rect(WIDTH // 2 - 35, HEIGHT - 30, 70, 24)
    speed_popup_rect = pygame.Rect(WIDTH // 2 - 40, 18, 80, 24)
    home_btn_rect = pygame.Rect(20, 10, 40, 40)
    
    resume_btn = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 - 60, 200, 45)
    restart_btn = pygame.Rect(WIDTH//2 - 100, HEIGHT//2, 200, 45)
    mainmenu_btn = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 60, 200, 45)
    

    # State Home/Profil
    skin_popup_open = False
    viewing_skin_idx = 0
    show_skin_popup = False
    skin_popup_timer = 0
    skin_popup_y = -100
    new_skin_img = None
    
    
    cached_bg = pygame.Surface((WIDTH, HEIGHT))
    cached_bg.fill(BG_COLOR)
    
    # Gambar Garis Grid ke dalam cached_bg
    for x in range(0, WIDTH, 40):
        pygame.draw.line(cached_bg, (32, 44, 76), (x, 0), (x, HEIGHT), 1)
    for y in range(0, HEIGHT, 40):
        pygame.draw.line(cached_bg, (32, 44, 76), (0, y), (WIDTH, y), 1)
        
    # Gambar Efek Glow ke dalam cached_bg
    glow_surf = pygame.Surface((WIDTH, 300), pygame.SRCALPHA)
    for radius in range(250, 0, -20):
        alpha = int(25 * (1 - radius / 250))
        pygame.draw.circle(glow_surf, (0, 200, 255, alpha), (WIDTH // 2, 50), radius)
    cached_bg.blit(glow_surf, (0, 0))
    # =============================================


    while True:   
        screen.blit(cached_bg, (0, 0)) 
        
        mx, my = pygame.mouse.get_pos()

        mx, my = pygame.mouse.get_pos()
        if game_state not in (STATE_HOME,): 
            island_ui.update()

        if game_state == STATE_MENU:
            pygame.draw.circle(screen, (32, 44, 80), (80, 180), 70)
            pygame.draw.circle(screen, (32, 44, 80), (380, 580), 120)

            # Tombol Home di kiri atas
            pygame.draw.rect(screen, SLIDER_BG, home_btn_rect, border_radius=20)
            screen.blit(IMG_HOME, (home_btn_rect.x + 2, home_btn_rect.y + 2))

            title_center_y = HEIGHT // 4 - 30
            border_rect_outer = pygame.Rect(WIDTH // 2 - 179, title_center_y - 40, 360, 95)
            pygame.draw.rect(screen, SLIDER_BG, border_rect_outer, width=1, border_radius=12)
            border_rect_inner = pygame.Rect(WIDTH // 2 - 174, title_center_y - 35, 350, 85)
            pygame.draw.rect(screen, YELLOW, border_rect_inner, width=2, border_radius=15)

            render_sharp_text("BRICK BLASTER", FONT_TITLE, (12, 18, 35), screen, (WIDTH//2 + 3, title_center_y + 6))
            render_sharp_text("BRICK BLASTER", FONT_TITLE, WHITE, screen, (WIDTH//2, title_center_y))
            render_sharp_text("✦ ENDLESS BOUNCE ✦", FONT_SUB, BALL_COLOR, screen, (WIDTH//2, title_center_y + 70))

            continue_btn = pygame.Rect(WIDTH//2 - 140, HEIGHT//2 - 15, 280, 65)
            pygame.draw.rect(screen, (30, 120, 70), (continue_btn.x, continue_btn.y + 6, continue_btn.width, continue_btn.height), border_radius=20)
            pygame.draw.rect(screen, GREEN, continue_btn, border_radius=20)
            render_sharp_text(f"CONTINUE PLAYING (LV {level})", FONT_BUTTON, BG_COLOR, screen, continue_btn.center)

            new_btn = pygame.Rect(WIDTH//2 - 80, HEIGHT - 120, 160, 45)
            pygame.draw.rect(screen, (150, 40, 30), (new_btn.x, new_btn.y + 4, new_btn.width, new_btn.height), border_radius=22)
            pygame.draw.rect(screen, RED, new_btn, border_radius=22)
            
            render_sharp_text("NEW GAME", FONT_SUB, WHITE, screen, new_btn.center)
            render_sharp_text("Peringatan: Progress akan diriset", FONT_MINI, (120, 130, 160), screen, (WIDTH//2, HEIGHT - 55))
            render_sharp_text("Credit: Dr.Senku°", FONT_MICRO, (120, 130,160), screen, (WIDTH//9, HEIGHT - 10))

            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if island_ui.handle_click(event.pos, level): continue
                    if not island_ui.is_open:
                        if home_btn_rect.collidepoint(event.pos):
                            game_state = STATE_HOME
                            skin_popup_open = False
                            haptic_vibrate(40)
                        elif continue_btn.collidepoint(event.pos):
                            bricks = spawn_bricks(level); balls = [Ball(launcher_x, launcher_y) for _ in range(9 + level)]
                            particles.clear()
                            aiming = True; is_dragging = False; shooting = False; fast_forward = False; game_state = STATE_PLAYING
                        elif new_btn.collidepoint(event.pos):
                            level = 1; save_game_data(level)
                            bricks = spawn_bricks(level); balls = [Ball(launcher_x, launcher_y) for _ in range(9 + level)]
                            particles.clear()
                            aiming = True; is_dragging = False; shooting = False; fast_forward = False; game_state = STATE_PLAYING

        elif game_state == STATE_HOME:
            back_btn = pygame.Rect(20, 20, 55, 45)
            # Efek Bayangan Belakang (Shadow 3D)
            shadow_rect = pygame.Rect(back_btn.x + 3, back_btn.y + 4, back_btn.width, back_btn.height)
            pygame.draw.rect(screen, (12, 18, 36), shadow_rect, border_radius=12)
            
            # Tombol Utama (Warna Gradasi Gelap Elegan)
            pygame.draw.rect(screen, (45, 55, 85), back_btn, border_radius=12)
            # Border Kilauan Atas (Agar Terlihat Timbul)
            pygame.draw.rect(screen, CYAN, back_btn, width=2, border_radius=12)
            
            # Teks Panah Keluar
            render_sharp_text("<-", FONT_UI, WHITE, screen, back_btn.center)

            
            # --- FOTO PROFIL ---
            profile_y = 110
            prof_img = SKIN_PROFILES[SELECTED_SKIN_IDX]
            screen.blit(prof_img, (WIDTH//2 - 40, profile_y))
            
            skin_open_btn = pygame.Rect(WIDTH//2 - 25, profile_y + 85, 50, 25)
            pygame.draw.rect(screen, SLIDER_BG, skin_open_btn, border_radius=10)
            render_sharp_text("v", FONT_SUB, WHITE, screen, (skin_open_btn.centerx, skin_open_btn.centery - 2))

            # --- TABS INFO ---
            stats_y = 250
            achieve_x = WIDTH // 4
            leader_x = WIDTH * 3 // 4
            
            # Kiri: Pencapaian / Achievement
            total_ach = len(ACHIEVEMENT_MILESTONES)
            unlocked_ach = len(UNLOCKED_ACHIEVEMENTS)
            render_sharp_text(f"{unlocked_ach}/{total_ach}", FONT_SUB, WHITE, screen, (achieve_x, stats_y))
            render_sharp_text("Achievement", FONT_MINI, WHITE, screen, (achieve_x - 12, stats_y + 35))
            pygame.draw.circle(screen, WHITE, (achieve_x + 50, stats_y + 35), 10)
            
            screen.blit(pygame.transform.smoothscale(IMG_ACHIEVE, (20, 20)), (achieve_x + 40, stats_y + 25))
            
            # Kanan: Leaderboard
            leader_btn_rect = pygame.Rect(leader_x - 60, stats_y - 20, 150, 60)
            render_sharp_text("--", FONT_SUB, WHITE, screen, (leader_x - 15, stats_y))
            # Teks di sebelah kiri ikon
            render_sharp_text("Leaderboard", FONT_MINI, WHITE, screen, (leader_x - 15, stats_y + 35))
            # Background lingkaran untuk ikon
            pygame.draw.circle(screen, WHITE, (leader_x + 50, stats_y + 35), 10)
            # Ikon ditaruh di dalam lingkaran
            screen.blit(pygame.transform.smoothscale(IMG_LEADER,(18, 18)), (leader_x + 41, stats_y + 25))

            
            # --- LIST ACHIEVEMENT ---
            list_start_y = stats_y + 80
            for i, (m_lvl, m_name) in enumerate(ACHIEVEMENT_MILESTONES.items()):
                item_y = list_start_y + (i * 60)
                item_rect = pygame.Rect(30, item_y, WIDTH - 60, 50)
                
                is_unlocked = m_name in UNLOCKED_ACHIEVEMENTS
                border_col = GREEN if is_unlocked else SLIDER_BG
                bg_col = (20, 45, 30) if is_unlocked else BG_COLOR
                
                pygame.draw.rect(screen, bg_col, item_rect, border_radius=8)
                pygame.draw.rect(screen, border_col, item_rect, width=2, border_radius=8)
                screen.blit(IMG_ACHIEVE, (45, item_y + 9))
                
                text_col = WHITE if is_unlocked else (100, 100, 100)
                sub_col = YELLOW if is_unlocked else (80, 80, 80)
                render_sharp_text(m_name, FONT_SUB, text_col, screen, (90, item_y + 14), anchor="midleft")
                render_sharp_text(f"Level {m_lvl}", FONT_MINI, sub_col, screen, (90, item_y + 36), anchor="midleft")

            # --- POP UP PILIH SKIN ---
            if skin_popup_open:
                overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 180))
                screen.blit(overlay, (0, 0))
                
                popup = pygame.Rect(40, HEIGHT//2 - 120, WIDTH - 80, 240)
                pygame.draw.rect(screen, SLIDER_BG, popup, border_radius=15)
                pygame.draw.rect(screen, BLUE, popup, width=2, border_radius=15)
                
                render_sharp_text("PILIH SKIN BOLA", FONT_SUB, WHITE, screen, (WIDTH//2, popup.y + 25))
                
                left_arrow = pygame.Rect(popup.left + 15, popup.centery - 20, 40, 40)
                pygame.draw.rect(screen, BG_COLOR, left_arrow, border_radius=20)
                render_sharp_text("<", FONT_SUB, WHITE, screen, left_arrow.center)
                
                right_arrow = pygame.Rect(popup.right - 55, popup.centery - 20, 40, 40)
                pygame.draw.rect(screen, BG_COLOR, right_arrow, border_radius=20)
                render_sharp_text(">", FONT_SUB, WHITE, screen, right_arrow.center)
                
                view_prof = SKIN_PROFILES[viewing_skin_idx]
                # Logika Cek Unlocked Skin
                skin_is_unlocked = False
                if viewing_skin_idx == 0: 
                    skin_is_unlocked = True
                else:
                    req_achievement = list(ACHIEVEMENT_MILESTONES.values())[viewing_skin_idx - 1]
                    if req_achievement in UNLOCKED_ACHIEVEMENTS:
                        skin_is_unlocked = True
                
                if skin_is_unlocked:
                    screen.blit(view_prof, (WIDTH//2 - 40, popup.centery - 40))
                else:
                    view_prof_dim = view_prof.copy()
                    view_prof_dim.set_alpha(60)
                    screen.blit(view_prof_dim, (WIDTH//2 - 40, popup.centery - 40))
                    pygame.draw.rect(screen, (0, 0, 0, 120), (WIDTH//2 - 40, popup.centery - 40, 80, 80), border_radius=40)
                    
                skin_name = SKIN_NAMES[viewing_skin_idx].replace(".png", "")
                render_sharp_text(skin_name, FONT_MINI, WHITE, screen, (WIDTH//2, popup.centery + 55))
                
                action_btn = pygame.Rect(WIDTH//2 - 60, popup.bottom - 45, 120, 35)
                if not skin_is_unlocked:
                    pygame.draw.rect(screen, RED, action_btn, border_radius=8)
                    render_sharp_text("TERKUNCI", FONT_MINI, WHITE, screen, action_btn.center)
                elif viewing_skin_idx == SELECTED_SKIN_IDX:
                    pygame.draw.rect(screen, GREEN, action_btn, border_radius=8)
                    render_sharp_text("DIPILIH", FONT_MINI, BG_COLOR, screen, action_btn.center)
                else:
                    pygame.draw.rect(screen, YELLOW, action_btn, border_radius=8)
                    render_sharp_text("PILIH", FONT_MINI, BLACK, screen, action_btn.center)
                    
            if 'show_leaderboard_soon' in locals() and show_leaderboard_soon:
                overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 160))
                screen.blit(overlay, (0, 0))
                
                popup_rect = pygame.Rect(WIDTH//2 - 120, HEIGHT//2 - 40, 240, 80)
                pygame.draw.rect(screen, SLIDER_BG, popup_rect, border_radius=12)
                pygame.draw.rect(screen, YELLOW, popup_rect, width=2, border_radius=12)
                render_sharp_text("COMING SOON", FONT_SUB, YELLOW, screen, popup_rect.center)
                
                if pygame.time.get_ticks() - leaderboard_soon_timer > 1500:
                	show_leaderboard_soon = False

            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if leader_btn_rect.collidepoint(event.pos):
                        show_leaderboard_soon = True
                        leaderboard_soon_timer = pygame.time.get_ticks()
                        haptic_vibrate(40)

                    if skin_popup_open:
                        if left_arrow.collidepoint(event.pos):
                            viewing_skin_idx = (viewing_skin_idx - 1) % len(SKIN_NAMES)
                            haptic_vibrate(30)
                        elif right_arrow.collidepoint(event.pos):
                            viewing_skin_idx = (viewing_skin_idx + 1) % len(SKIN_NAMES)
                            haptic_vibrate(30)
                        elif action_btn.collidepoint(event.pos):
                            if skin_is_unlocked and viewing_skin_idx != SELECTED_SKIN_IDX:
                                SELECTED_SKIN_IDX = viewing_skin_idx
                                save_game_data(level)
                                haptic_vibrate(40)
                        elif not popup.collidepoint(event.pos):
                            skin_popup_open = False
                            haptic_vibrate(30)
                    else:
                        if back_btn.collidepoint(event.pos):
                            game_state = STATE_MENU
                            haptic_vibrate(40)
                        elif skin_open_btn.collidepoint(event.pos) or pygame.Rect(WIDTH//2 - 40, profile_y, 80, 80).collidepoint(event.pos):
                            skin_popup_open = True
                            viewing_skin_idx = SELECTED_SKIN_IDX
                            haptic_vibrate(40)
                            

        elif game_state in (STATE_PLAYING, STATE_PAUSED):
            danger_color = SLIDER_BG
            if game_state == STATE_PLAYING:
                for b in bricks:
                    if b.rect.y >= HEIGHT - 150 - BRICK_SIZE: danger_color = RED; break
            
            pygame.draw.line(screen, SLIDER_BG, (0, 60), (WIDTH, 60), 2)
            pygame.draw.line(screen, danger_color, (0, HEIGHT - 100), (WIDTH, HEIGHT - 100), 2)
            pygame.draw.line(screen, SLIDER_BG, (40, slider_y), (WIDTH - 40, slider_y), 6)
            
            render_sharp_text(f"Level {level}", FONT_UI, WHITE, screen, (20, 30), anchor="midleft")
            pygame.draw.rect(screen, SLIDER_BG, btn_pause_rect, border_radius=5)
            render_sharp_text("PAUSE", FONT_SUB, WHITE, screen, btn_pause_rect.center)

            for event in pygame.event.get():
                if event.type == pygame.QUIT: save_game_data(level); pygame.quit(); sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if island_ui.handle_click(event.pos, level): continue
                    if not island_ui.is_open:
                        if game_state == STATE_PLAYING:
                            if btn_pause_rect.collidepoint(event.pos):
                                game_state = STATE_PAUSED; is_dragging = False; fast_forward = False
                            elif not aiming and skip_btn_rect.collidepoint(event.pos):
                                shooting = False; current_ball_idx = len(balls) 
                                for ball in balls:
                                    if ball.active: ball.returning = True 
                            elif aiming:
                                is_dragging = True; slider_x = max(40, min(WIDTH - 40, mx))
                            else:
                                fast_forward = True
                        elif game_state == STATE_PAUSED:
                            if resume_btn.collidepoint(event.pos): game_state = STATE_PLAYING
                            elif restart_btn.collidepoint(event.pos):
                                bricks = spawn_bricks(level); balls = [Ball(launcher_x, launcher_y) for _ in range(9 + level)]
                                particles.clear(); aiming = True; shooting = False; fast_forward = False; game_state = STATE_PLAYING
                            elif mainmenu_btn.collidepoint(event.pos):
                                save_game_data(level); game_state = STATE_MENU

                elif event.type == pygame.MOUSEBUTTONUP:
                    if game_state == STATE_PLAYING and not island_ui.is_open:
                        if is_dragging: is_dragging = False; aiming = False; shooting = True; current_ball_idx = 0; shoot_delay = 0
                        fast_forward = False
                elif event.type == pygame.MOUSEMOTION and is_dragging and game_state == STATE_PLAYING and not island_ui.is_open:
                    slider_x = max(40, min(WIDTH - 40, mx))

            if game_state == STATE_PLAYING and not island_ui.is_open:
                loops = 2 if fast_forward and not aiming else 1
                for _ in range(loops):
                    if shooting:
                        shoot_delay += 1
                        if shoot_delay >= 3: 
                            if current_ball_idx < len(balls):
                                balls[current_ball_idx].launch(aim_angle); current_ball_idx += 1
                            shoot_delay = 0

                    all_balls_done = True
                    for ball in balls:
                        ball.update(bricks, launcher_x, launcher_y, particles) 
                        if ball.active: all_balls_done = False
                        elif not shooting: ball.x = launcher_x; ball.y = launcher_y

                    if not aiming and not shooting and all_balls_done:
                        if len(bricks) == 0:
                            # Cek Unlock Achievement Baru
                            new_achievements_queue.clear()
                            for m_lvl, m_name in ACHIEVEMENT_MILESTONES.items():
                                if level >= m_lvl and m_name not in UNLOCKED_ACHIEVEMENTS:
                                    UNLOCKED_ACHIEVEMENTS.append(m_name)
                                    new_achievements_queue.append(m_name)
                            
                            # --- TRIGGER POP-UP SKIN ---
                            if new_achievements_queue:
                                save_game_data(level)
                                show_skin_popup = True
                                skin_popup_timer = pygame.time.get_ticks()
                                skin_popup_y = -100
                                
                                # Cocokkan achievement dengan gambar skin
                                milestones_list = list(ACHIEVEMENT_MILESTONES.values())
                                try:
                                    ach_index = milestones_list.index(new_achievements_queue[-1])
                                    skin_idx = ach_index + 1 # Skin idx 1 itu untuk ach index 0
                                    if skin_idx < len(SKIN_PROFILES):
                                        new_skin_img = SKIN_PROFILES[skin_idx]
                                except Exception:
                                    new_skin_img = None
                            else:
                                show_skin_popup = False
                                
                            game_state = STATE_CLEAR
                        else:
                            for brick in bricks:
                                brick.rect.y += BRICK_SIZE
                                if brick.rect.y >= HEIGHT - 150: game_state = STATE_GAMEOVER
                            aiming = True; slider_x = WIDTH // 2; fast_forward = False
                    if shooting and current_ball_idx >= len(balls): shooting = False

            ratio = (slider_x - 40) / (WIDTH - 80)
            aim_angle = (-math.pi + 0.15) + ratio * (math.pi - 0.3)
            
            if game_state == STATE_PLAYING and is_dragging and not island_ui.is_open:
                path_points = calculate_aim_points(launcher_x, launcher_y, aim_angle, bricks)
                if len(path_points) > 1:
                    for i in range(len(path_points) - 1): pygame.draw.line(screen, BALL_COLOR, path_points[i], path_points[i+1], 2)
                    draw_aa_circle(screen, path_points[-1][0], path_points[-1][1], 4, WHITE)

            for ball in balls: ball.draw(screen)
            for brick in bricks: brick.draw(screen)
            for p in particles[:]:
                p.update()
                if p.lifetime <= 0 or p.size <= 0: particles.remove(p)
                else: p.draw(screen)

           
            if aiming and not is_dragging:
                draw_launcher_skin(screen, launcher_x, launcher_y)
                draw_aa_circle(screen, slider_x, slider_y, 10, (150, 150, 150))
            elif is_dragging:
                draw_launcher_skin(screen, launcher_x, launcher_y)
                draw_aa_circle(screen, slider_x, slider_y, 10, WHITE)


            balls_left = len(balls) if aiming else len(balls) - current_ball_idx
            render_sharp_text(f"x{balls_left}", FONT_SUB, BALL_COLOR, screen, (launcher_x, launcher_y + 30))

            if game_state == STATE_PLAYING and fast_forward and not aiming:
                pygame.draw.rect(screen, YELLOW, speed_popup_rect, border_radius=12)
                render_sharp_text("2× SPEED", FONT_MINI, BLACK, screen, speed_popup_rect.center)
            if game_state == STATE_PLAYING and not aiming:
                pygame.draw.rect(screen, RED, skip_btn_rect, border_radius=12) 
                render_sharp_text("SKIP", FONT_MINI, WHITE, screen, skip_btn_rect.center)

            if game_state == STATE_PAUSED:
                overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                overlay.fill(OVERLAY_COLOR)
                screen.blit(overlay, (0, 0))
                popup_rect = pygame.Rect(WIDTH//2 - 130, HEIGHT//2 - 130, 260, 260)
                pygame.draw.rect(screen, BG_COLOR, popup_rect, border_radius=10)
                pygame.draw.rect(screen, SLIDER_BG, popup_rect, width=3, border_radius=10)

                render_sharp_text("GAME PAUSED", FONT_UI, YELLOW, screen, (WIDTH//2, HEIGHT//2 - 95))
                pygame.draw.rect(screen, GREEN, resume_btn, border_radius=6)
                pygame.draw.rect(screen, YELLOW, restart_btn, border_radius=6)
                pygame.draw.rect(screen, BLUE, mainmenu_btn, border_radius=6)
                render_sharp_text("RESUME", FONT_SUB, WHITE, screen, resume_btn.center)
                render_sharp_text("RESTART", FONT_SUB, (0,0,0), screen, restart_btn.center)
                render_sharp_text("MAIN MENU", FONT_SUB, WHITE, screen, mainmenu_btn.center)

        elif game_state == STATE_CLEAR:
            render_sharp_text(f"LEVEL {level} CLEAR!", FONT_TITLE, YELLOW, screen, (WIDTH//2, HEIGHT//3 - 35))
            
            # --- TAMPILAN ACHIEVEMENT UNLOCKED ---
            if len(new_achievements_queue) > 0:
                render_sharp_text("Achievement Complete", FONT_UI, GREEN, screen, (WIDTH//2, HEIGHT//3 + 10))
                render_sharp_text(f"'{new_achievements_queue[-1]}'", FONT_SUB, WHITE, screen, (WIDTH//2, HEIGHT//3 + 45))

            # --- ANIMASI POP-UP SKIN UNLOCKED ---
            if show_skin_popup:
                elapsed = pygame.time.get_ticks() - skin_popup_timer
                if elapsed < 5000: # Tampil 1.5 Detik
                    # Slide down halus ke Y = 70 (atas tengah)
                    target_y = 70
                    skin_popup_y += (target_y - skin_popup_y) * 0.15
                    
                    # Memudar (Fade out) di 300ms terakhir
                    alpha = 255
                    if elapsed > 1200:
                        alpha = int(255 * (1500 - elapsed) / 300)
                    
                    popup_w, popup_h = 280, 70
                    popup_x = WIDTH // 2 - popup_w // 2
                    popup_surf = pygame.Surface((popup_w, popup_h), pygame.SRCALPHA)
                    
                    # Gambar kotak background
                    pygame.draw.rect(popup_surf, (45, 55, 85), (0, 0, popup_w, popup_h), border_radius=15)
                    pygame.draw.rect(popup_surf, CYAN, (0, 0, popup_w, popup_h), width=2, border_radius=15)
                    
                    # Render gambar skin di kiri (pakai gambar profile dari asetmu)
                    if new_skin_img:
                        img = pygame.transform.smoothscale(new_skin_img, (50, 50))
                        popup_surf.blit(img, (10, 10))
                        
                    # Teks di kanan skin
                    render_sharp_text("NEW SKIN", FONT_MINI, YELLOW, popup_surf, (70, 22), anchor="midleft")
                    render_sharp_text("UNLOCKED!", FONT_MINI, WHITE, popup_surf, (70, 48), anchor="midleft")
                    
                    # Set transparansi seluruh pop-up dan tempel ke layar
                    popup_surf.set_alpha(alpha)
                    screen.blit(popup_surf, (popup_x, int(skin_popup_y)))
                else:
                    show_skin_popup = False
                    
            next_btn = pygame.Rect(WIDTH//2 - 110, HEIGHT//2 + 10, 220, 50)
            menu_btn = pygame.Rect(WIDTH//2 - 110, HEIGHT//2 + 80, 220, 50)
            pygame.draw.rect(screen, GREEN, next_btn, border_radius=6)
            pygame.draw.rect(screen, BLUE, menu_btn, border_radius=6)
            render_sharp_text("LANJUT", FONT_SUB, WHITE, screen, next_btn.center)
            render_sharp_text("KEMBALI MENU", FONT_SUB, WHITE, screen, menu_btn.center)

            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if island_ui.handle_click(event.pos, level): continue
                    if not island_ui.is_open:
                        if next_btn.collidepoint(event.pos):
                            level += 1; save_game_data(level)
                            bricks = spawn_bricks(level); balls = [Ball(launcher_x, launcher_y) for _ in range(9 + level)]
                            particles.clear(); aiming = True; is_dragging = False; shooting = False; game_state = STATE_PLAYING
                        elif menu_btn.collidepoint(event.pos):
                            level += 1; save_game_data(level); game_state = STATE_MENU

        elif game_state == STATE_GAMEOVER:
            render_sharp_text("GAME OVER", FONT_TITLE, RED, screen, (WIDTH//2, HEIGHT//3))
            retry_btn = pygame.Rect(WIDTH//2 - 110, HEIGHT//2 - 40, 220, 50)
            pygame.draw.rect(screen, YELLOW, retry_btn, border_radius=6)
            render_sharp_text("ULANGI LEVEL", FONT_SUB, (0,0,0), screen, retry_btn.center)
            menu_go_btn = pygame.Rect(WIDTH//2 - 110, HEIGHT//2 + 30, 220, 50)
            pygame.draw.rect(screen, BLUE, menu_go_btn, border_radius=6)
            render_sharp_text("MENU UTAMA", FONT_SUB, WHITE, screen, menu_go_btn.center)

            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if island_ui.handle_click(event.pos, level): continue
                    if not island_ui.is_open:
                        if retry_btn.collidepoint(event.pos):
                            bricks = spawn_bricks(level); balls = [Ball(launcher_x, launcher_y) for _ in range(9 + level)]
                            particles.clear(); aiming = True; is_dragging = False; shooting = False; game_state = STATE_PLAYING
                        elif menu_go_btn.collidepoint(event.pos): game_state = STATE_MENU

        if game_state not in (STATE_HOME,):
            island_ui.draw(screen)
            
        pygame.display.flip()
        
        current_fps_setting = FPS_OPTIONS[FPS_INDEX]
        if current_fps_setting == "Infinite": clock.tick()
        else: clock.tick(int(current_fps_setting))

if __name__ == "__main__":
    main()
