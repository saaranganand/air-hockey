import pygame
import math
import json
import os

client_dir = os.path.dirname(os.path.abspath(__file__))


# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 1280, 720
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Create game window
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Air Hockey")

class Paddle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.radius = 40
        self.color = color
        self.maxSpeed = 22 
        self.vx = 0
        self.vy = 0
        self.curSpeed = 0 
        self.friction = 0.97
        self.isGrabbed = False
    
    def move(self):
        if not self.isGrabbed:
            self.x += self.vx
            self.y += self.vy
            self.vx *= self.friction
            self.vy *= self.friction

            # Bounce off walls
            if self.y - self.radius <= 0 or self.y + self.radius >= HEIGHT:
                self.vy = -self.vy
            if self.x - self.radius <= 0 or self.x + self.radius >= WIDTH:
                self.vx = -self.vx

            # Prevent clipping into walls
            self.x = max(self.radius, min(self.x, WIDTH - self.radius))
            self.y = max(self.radius, min(self.y, HEIGHT - self.radius))
        else:
            mouseX, mouseY = pygame.mouse.get_pos()
            dist = -math.hypot(self.x - mouseX, self.y - mouseY)
            angle = math.atan2(self.y - mouseY, self.x - mouseX)

            self.vx =  dist * math.cos(angle)
            self.vy = dist * math.sin(angle)
            velocity = math.sqrt(self.vx**2 + self.vy**2)

            if velocity > self.maxSpeed:
                self.vx = (self.vx / velocity) * self.maxSpeed
                self.vy = (self.vy / velocity) * self.maxSpeed

            self.x += self.vx
            self.y += self.vy

            self.curSpeed = math.sqrt(self.vx ** 2 + self.vy ** 2)

    # returns True if the mouse is inside the paddle's radius
    def mouseInRadius(self, paddle):
        mouseX, mouseY = pygame.mouse.get_pos()
        if mouseX < self.x + self.radius and mouseX > self.x - self.radius and mouseY < paddle.y + self.radius and mouseY > self.y - paddle.radius:
            return True
        else:
            return False


    def draw(self, screen):
        if self.isGrabbed:
            # Make the color darker to indicate to all players that the paddle has been grabbed
            tempColor = []
            tempColor.append(self.color[0] * 0.5)
            tempColor.append(self.color[1] * 0.5)
            tempColor.append(self.color[2] * 0.5)
            pygame.draw.circle(screen, tuple(tempColor), (self.x, self.y), self.radius)
        else:
            pygame.draw.circle(screen, self.color, (self.x, self.y), self.radius)

class Puck:
    def __init__(self):
        self.x = WIDTH // 2
        self.y = HEIGHT // 2
        self.radius = 30
        self.color = tuple([0, 220, 50])
        self.vx = 0  # Initial velocity
        self.vy = 0
        self.friction = 0.99
        self.maxSpeed = 25

    def move(self):
        self.x += self.vx
        self.y += self.vy
        

        # Bounce off walls
        if self.y - self.radius <= 0 or self.y + self.radius >= HEIGHT:
            self.vy = -self.vy

        if self.x - self.radius <= 0 or self.x + self.radius >= WIDTH:
            self.vx = -self.vx

        # Prevent clipping with walls
        self.x = max(self.radius, min(self.x, WIDTH - self.radius))
        self.y = max(self.radius, min(self.y, HEIGHT - self.radius))

        # Friction
        self.vx *= self.friction
        self.vy *= self.friction

        velocity = math.sqrt(self.vx**2 + self.vy**2)
        if velocity > self.maxSpeed:
            self.vx = (self.vx / velocity) * self.maxSpeed
            self.vy = (self.vy / velocity) * self.maxSpeed


    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (self.x, self.y), self.radius)

class Goal:
    def __init__(self, side):
        self.width = 10 
        self.height = HEIGHT // 3 
        self.y = HEIGHT // 3
        if side == "left":
            self.x = 0 
        elif side == "right":
            self.x = WIDTH - self.width

    def draw(self):
        goal = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(screen, WHITE, goal)

    def goal(self):
        goalHornSoundEffect.play()
        goalHornSoundEffect.fadeout(2500)

    def checkCollisionWithPuck(self, puck):
        puckDistanceX = abs(puck.x - self.x)
        return puckDistanceX - puck.radius <= 0 and puck.y - puck.radius > self.y and puck.y + puck.radius < 2 * self.y
            

def checkCollisionPuckAndPaddle(paddle, puck):
    dist = math.hypot(paddle.x - puck.x, paddle.y - puck.y)
    if dist < paddle.radius + puck.radius:
        if dist == 0:
            dist = 10e-6 # prevent division by 0
        print(dist)
        if puckCollisionSound.get_num_channels() == 0:
            puckCollisionSound.play(maxtime=500)

        angle = math.atan2(puck.y - paddle.y, puck.x - paddle.x)

        # distances between paddles
        dx = paddle.x - puck.x
        dy = paddle.y - puck.y

        # normal vector
        nx = dx / dist
        ny = dy / dist

        # tangent vector
        tx = -ny
        ty = nx

        # dot product tangent
        dpTan1 = paddle.vx * tx + paddle.vy * ty
        dpTan2 = puck.vx * tx + puck.vy * ty

        # dot product normal
        dpNorm1 = paddle.vx * nx + paddle.vy * ny
        dpNorm2 = puck.vx * nx + puck.vy * ny
        if paddle.isGrabbed:
            puck.vx += paddle.curSpeed * math.cos(angle)
            puck.vy += paddle.curSpeed * math.sin(angle)
        else:
            # Swap normal velocities
            paddle.vx = tx * dpTan1 + nx * dpNorm2
            paddle.vy = ty * dpTan1 + ny * dpNorm2
            puck.vx = tx * dpTan2 + nx * dpNorm1
            puck.vy = ty * dpTan2 + ny * dpNorm1

        # prevent sticking together
        overlap = (paddle.radius + puck.radius) - dist
        if overlap < 0:
            separation = (overlap / 2) + 0.5
            paddle.x += nx * separation 
            paddle.y += ny * separation 
            puck.x -= nx * separation 
            puck.y -= ny * separation 

def checkCollisionPaddleAndPaddle(paddle1, paddle2):
    dist = math.hypot(paddle1.x - paddle2.x, paddle1.y - paddle2.y)
    if dist <= paddle1.radius * 2:
        if paddleCollisionSound.get_num_channels() == 0:
            paddleCollisionSound.play(maxtime=500)

        # distances between paddles
        dx = paddle1.x - paddle2.x
        dy = paddle1.y - paddle2.y

        # normal vector
        nx = dx / dist
        ny = dy / dist

        # tangent vector
        tx = -ny
        ty = nx

        # dot product tangent
        dpTan1 = paddle1.vx * tx + paddle1.vy * ty
        dpTan2 = paddle2.vx * tx + paddle2.vy * ty

        # dot product normal
        dpNorm1 = paddle1.vx * nx + paddle1.vy * ny
        dpNorm2 = paddle2.vx * nx + paddle2.vy * ny

        angle = math.atan2(paddle1.y - paddle2.y, paddle1.x - paddle2.x)
        if (paddle1.isGrabbed and paddle2.isGrabbed) or (not paddle1.isGrabbed and not paddle2.isGrabbed):
            # Swap normal velocities
            paddle1.vx = tx * dpTan1 + nx * dpNorm2
            paddle1.vy = ty * dpTan1 + ny * dpNorm2
            paddle2.vx = tx * dpTan2 + nx * dpNorm1
            paddle2.vy = ty * dpTan2 + ny * dpNorm1
            
            # make both players drop their paddle if they collide
            paddle1.isGrabbed = False
            paddle2.isGrabbed = False
        elif paddle1.isGrabbed and not paddle2.isGrabbed:
            paddle2.vx += paddle1.curSpeed * -math.cos(angle) * 0.9
            paddle2.vy += paddle1.curSpeed * -math.sin(angle) * 0.9
        elif paddle2.isGrabbed and not paddle1.isGrabbed:
            paddle1.vx += paddle2.curSpeed * math.cos(angle) * 0.9
            paddle1.vy += paddle2.curSpeed * math.sin(angle) * 0.9

        # prevent sticking together
        overlap = paddle1.radius * 2 - dist
        if overlap < 0:
            separation = (overlap / 2) + 0.5
            paddle1.x -= nx * separation 
            paddle1.y -= ny * separation 
            paddle2.x += nx * separation 
            paddle2.y += ny * separation 
        return paddle1, paddle2
    return None


puckCollisionSound = pygame.mixer.Sound(os.path.join(client_dir, "./sounds/puck-sound.wav"))
paddleCollisionSound = pygame.mixer.Sound(os.path.join(client_dir, "./sounds/paddle-sound.wav"))
goalHornSoundEffect = pygame.mixer.Sound(os.path.join(client_dir, "./sounds/goalhorn.mp3"))

font = pygame.font.SysFont(pygame.font.get_default_font(), 40)
txtsurface = font.render("0:0", True, (255, 255, 255))

class Game:
    def __init__(self, serverSocket):
        self.paddles = [
            Paddle(100, HEIGHT // 2, (0, 0, 255)),
            Paddle(WIDTH - 100, HEIGHT // 2, (255, 0, 0))
        ]

        if serverSocket is None:
            raise Exception("Server socket is None")

        self.serverSocket = serverSocket
        self.puck = Puck()

        self.mousedown = False
        self.curPaddle = None
        self.running = False 

        self.rightScore = 0
        self.rightGoal = Goal("right")
        self.leftScore = 0
        self.leftGoal = Goal("left")

        pygame.font.init()
        pygame.mixer.init()

    def run(self):
        self.running = True
        while self.running:
            pygame.time.delay(30)  # Control game speed
            screen.fill(BLACK)
            txtsurface = font.render(f"{self.leftScore}:{self.rightScore}", False, (255, 255, 255))
            screen.blit(txtsurface, (WIDTH // 2 - txtsurface.get_width() // 2, 20 - txtsurface.get_height() // 2))

            # keys = pygame.key.get_pressed()
            # mouseX, mouseY = pygame.mouse.get_pos()

            collisions = []

            if self.mousedown and self.curPaddle:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_CROSSHAIR)
            else:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

            self.puck.move()
            for paddle in self.paddles:
                checkCollisionPuckAndPaddle(paddle, self.puck)
                paddle.draw(screen)
                paddle.move()
                if not self.curPaddle and paddle.mouseInRadius(paddle):
                    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
                if paddle not in collisions:
                    for paddle2 in self.paddles:
                        if paddle2 != paddle:
                            collisions.append(checkCollisionPaddleAndPaddle(paddle, paddle2))

            # paddle1.draw(screen)
            # paddle2.draw(screen)
            self.puck.draw(screen)
            self.leftGoal.draw()
            self.rightGoal.draw()

            if self.leftGoal.checkCollisionWithPuck(self.puck):
                self.leftGoal.goal()
                self.puck.x = WIDTH // 2
                self.puck.y = HEIGHT // 2
                self.puck.vx = 0
                self.puck.vy = 0
                self.rightScore += 1
            if self.rightGoal.checkCollisionWithPuck(self.puck):
                self.rightGoal.goal()
                self.puck.x = WIDTH // 2
                self.puck.y = HEIGHT // 2
                self.puck.vx = 0
                self.puck.vy = 0
                self.leftScore += 1

            if self.curPaddle:
                packet = json.dumps({
                    "type": "Paddle",
                    "position": [self.curPaddle.x, self.curPaddle.y]
                })
                self.serverSocket.send(str.encode(packet))

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        for paddle in self.paddles:
                            if paddle.mouseInRadius(paddle):
                                self.curPaddle = paddle
                                self.curPaddle.isGrabbed = True
                                break
                        self.mousedown = True
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        print(self.curPaddle)
                        if self.curPaddle:
                            self.curPaddle.isGrabbed = False
                            self.curPaddle = None
                        self.mousedown = False

            pygame.display.update()

