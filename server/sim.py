'''
sim.py

This file handles simulation logic to run on the server side
It is very similar to what happens on the client side, but
does not render anything, just handles updates to positions/velocities/scores

Paddle/puck/goal should be abstracted into their own classes outside of this file
and the client side but whatever
'''

import os

import pygame
import math

# Constants
WIDTH, HEIGHT = 1280, 720

client_dir = os.path.dirname(os.path.abspath(__file__)) + "../client/"

class Simulator:
    def __init__(self):
        self.paddles = {}
        self.paddle_ids = []
        self.puck = Puck() 
        self.goals = [Goal('left'), Goal('right')]
        self.score = {"left": 0, "right": 0}

    # Simulate current game with new information from server
    def simulate(self, action, simDelta):
        game_state = {
            "paddles": {},
            "puck": {"position": [self.puck.x, self.puck.y], "velocity": [self.puck.vx, self.puck.vy]},
            "score": self.score
        }

        collisions = [] 

        for paddle_id in self.paddles:
            paddle = self.paddles[paddle_id]
            paddle.curSpeed = math.sqrt(paddle.vy**2 + paddle.vx**2)
            paddle.move()
            checkCollisionPuckAndPaddle(paddle, self.puck)
            
            if paddle not in collisions:
                for paddle2 in self.paddles.values():
                    if paddle2 != paddle:
                        collisions.append(checkCollisionPaddleAndPaddle(paddle, paddle2))

            game_state['paddles'][paddle_id] = {
                'position': [paddle.x, paddle.y],
                'velocity': [paddle.vx, paddle.vy],
                'isGrabbed': paddle.isGrabbed
            }


        if action:
            for action_type in action.keys():
                action = action[action_type]
                if action_type == 'join':
                    paddle_id = action['paddle_id']
                    self.paddle_ids.append(paddle_id)
                    x, y = tuple(action['position'])
                    new_paddle = Paddle(x, y, paddle_id)
                    self.paddles[paddle_id] = new_paddle
                elif action_type == 'update_position':
                    paddle_id = action['paddle_id']
                    x, y = tuple(action['position'])
                    vx, vy = tuple(action['velocity'])
                    paddle = self.paddles[paddle_id]
                    paddle.update(x, y, vx, vy)
                elif action_type == 'grab':
                    paddle_info = action
                    if paddle_info.get('success'):
                        print(paddle_info.get('paddle'))
                        self.paddles[paddle_info.get('paddle')].isGrabbed = True
                elif action_type == 'release':
                    self.paddles[action].isGrabbed = False 

        self.puck.move(simDelta)
        for goal in self.goals:
            if goal.checkCollisionWithPuck(self.puck):
                self.score[goal.side] += 1 
                self.puck.x = WIDTH // 2
                self.puck.y = HEIGHT // 2
                self.puck.vx, self.puck.vy = (0, 0)
        
        game_state['score'] = {'left': self.score['left'], 'right': self.score['right']}

        game_state['puck'] = {
            'position': [self.puck.x, self.puck.y],
            'velocity': [self.puck.vx, self.puck.vy]
        }

        return game_state


class Paddle:
    def __init__(self, x, y, paddle_id, vx=0, vy=0):
        self.x = x
        self.y = y
        self.radius = 40
        self.maxSpeed = 22 
        self.vx = vx 
        self.vy = vy
        self.curSpeed = 0 
        self.friction = 0.97
        self.isGrabbed = False
        self.paddleID = paddle_id

    def update(self, x, y, vx, vy):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        
    def move(self):
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

class Puck:
    def __init__(self):
        self.x = WIDTH // 2
        self.y = HEIGHT // 2
        self.radius = 30
        self.color = tuple([0, 220, 50])
        self.vx = 0
        self.vy = 0
        self.friction = 0.99
        self.maxSpeed = 25

    def move(self, delta):
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
        self.side = side
        if side == "left":
            self.x = 0 
        elif side == "right":
            self.x = WIDTH - self.width

    def checkCollisionWithPuck(self, puck):
        puckDistanceX = abs(puck.x - self.x)
        return puckDistanceX - puck.radius <= 0 and puck.y - puck.radius > self.y and puck.y + puck.radius < 2 * self.y
            

collisionDamper = 0.8

def checkCollisionPuckAndPaddle(paddle, puck):
    dist = math.hypot(paddle.x - puck.x, paddle.y - puck.y)
    if dist < paddle.radius + puck.radius:
        if dist == 0:
            dist = 10e-6 # prevent division by 0

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
            puck.vx += paddle.curSpeed * math.cos(angle) * collisionDamper
            puck.vy += paddle.curSpeed * math.sin(angle) * collisionDamper
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
        # distances between paddles
        dx = paddle1.x - paddle2.x
        dy = paddle1.y - paddle2.y
        
        # avoid division by 0
        if dx == 0 or dy == 0:
            return

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
