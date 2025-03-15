import pygame
import math

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 1200, 800
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
        self.maxSpeed = 15 
        self.vx = 0
        self.vy = 0
        self.curSpeed = 15
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
    def mouseInRadius(self):
        mouseX, mouseY = pygame.mouse.get_pos()
        if mouseX < paddle.x + paddle.radius and mouseX > paddle.x - paddle.radius and mouseY < paddle.y + paddle.radius and mouseY > paddle.y - paddle.radius:
            return True
        else:
            return False


    def draw(self, screen):
        if self.isGrabbed:
            tempColor = []
            tempColor.append(self.color[0] * 0.8)
            tempColor.append(self.color[1] * 0.8)
            tempColor.append(self.color[2] * 0.8)
            pygame.draw.circle(screen, tuple(tempColor), (self.x, self.y), self.radius)
        else:
            pygame.draw.circle(screen, self.color, (self.x, self.y), self.radius)

class Puck:
    def __init__(self):
        self.x = WIDTH // 2
        self.y = HEIGHT // 2
        self.radius = 20
        self.color = WHITE
        self.vx = 0  # Initial velocity
        self.vy = 0
        self.friction = 0.99

    def move(self):
        self.x += self.vx
        self.y += self.vy

        # Bounce off walls
        if self.y - self.radius <= 0 or self.y + self.radius >= HEIGHT:
            self.vy = -self.vy

        if self.x - self.radius <= 0 or self.x + self.radius >= WIDTH:
            self.vx = -self.vx

        # Send to center of ice if the puck glitches outside of playing area
        if self.x < -self.radius or self.x > WIDTH + self.radius:
            self.x = WIDTH // 2 
            self.y = HEIGHT // 2 
        if self.y < 0 or self.y > HEIGHT:
            self.x = WIDTH // 2
            self.y = HEIGHT // 2 

        # Friction
        self.vx *= self.friction
        self.vy *= self.friction


    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (self.x, self.y), self.radius)


def checkCollisionPuckAndPaddle(paddle, puck):
    dist = math.hypot(paddle.x - puck.x, paddle.y - puck.y)
    if dist < paddle.radius + puck.radius:
        angle = math.atan2(puck.y - paddle.y, puck.x - paddle.x)
        puck.vx = paddle.curSpeed * math.cos(angle)
        puck.vy = paddle.curSpeed * math.sin(angle)

def checkCollisionPaddleAndPaddle(paddle1, paddle2):
    dist = math.hypot(paddle1.x - paddle2.x, paddle1.y - paddle2.y)
    if dist <= paddle1.radius * 2:
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

paddles = [
    Paddle(100, HEIGHT // 2, (0, 0, 255)),
    Paddle(WIDTH - 100, HEIGHT // 2, (255, 0, 0))
]

puck = Puck()

mousedown = False
curPaddle = None
running = True

while running:
    pygame.time.delay(15)  # Control game speed
    screen.fill(BLACK)

    keys = pygame.key.get_pressed()
    # paddle1.move(keys, pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d)
    mouseX, mouseY = pygame.mouse.get_pos()

    collisions = []

    if mousedown and curPaddle:
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_CROSSHAIR)
    else:
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

    puck.move()
    for paddle in paddles:
        checkCollisionPuckAndPaddle(paddle, puck)
        paddle.draw(screen)
        paddle.move()
        if not curPaddle and paddle.mouseInRadius():
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
        if paddle not in collisions:
            for paddle2 in paddles:
                if paddle2 != paddle:
                    collisions.append(checkCollisionPaddleAndPaddle(paddle, paddle2))

    # paddle1.draw(screen)
    # paddle2.draw(screen)
    puck.draw(screen)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                for paddle in paddles:
                    if paddle.mouseInRadius():
                        curPaddle = paddle
                        curPaddle.isGrabbed = True
                        break
                mousedown = True
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                print(curPaddle)
                if curPaddle:
                    curPaddle.isGrabbed = False
                    curPaddle = None
                mousedown = False

    pygame.display.update()

pygame.quit()

