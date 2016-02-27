#!/usr/bin/python3

import pygame
import math
import os
import sys



def load_png(folder, filename):
	image = pygame.image.load(os.path.join("graphics", folder, filename));
	if image.get_alpha() is None:
		image = image.convert()
	else:
		image = image.convert_alpha()
	return image
	
class Bullet:
	def __init__(self, spritefile, position, direction, speed, damage, is_enemy):
		self.sprite = load_png("sprites", spritefile)
		self.image = pygame.transform.rotate(self.sprite, direction - 90)
		self.position = [(position[0] - self.image.get_width() / 2), (position[1] - self.image.get_height() / 2)]
		self.vector = [math.cos(math.radians(direction)), -math.sin(math.radians(direction))]
		#print("bullet vector", self.vector)
		self.speed = speed
		self.damage = damage
		self.is_enemy = is_enemy
		self.hitboxes = []
		for i in range(3):
			hbox = pygame.Rect(int(self.position[0] - 1 - 3 * i * self.vector[0]), int(self.position[1] - 1 - 3 * i * self.vector[1]), 3, 3)
			self.hitboxes.append(hbox)
	
	def draw(self, dest):
		dest.blit(self.image, (self.position[0], self.position[1]))
	
	def update(self, delta_time):
		motion_vector = [self.vector[0] * self.speed * delta_time, self.vector[1] * self.speed * delta_time]
		#print("moving by", motion_vector)
		#print("old pos", self.position)
		self.position[0] += motion_vector[0]
		self.position[1] += motion_vector[1]
		#print("new pos", self.position)
		for i in range(len(self.hitboxes)):
			self.hitboxes[i].left = (int)(self.position[0] - 1 - 3 * i * self.vector[0])
			self.hitboxes[i].top = (int)(self.position[1] - 1 - 3 * i * self.vector[1])
	
	def check_collision(self, rect):
		collided = False
		for i in self.hitboxes:
			collided = collided or i.colliderect(rect)
		return collided
	
	def is_outside_screen(self):
		#print("outside screen:", self.position[0] < -8 or self.position[1] < -8 or self.position[0] > 264 or self.position[1] > 232)
		return self.position[0] < -8 or self.position[1] < -8 or self.position[0] > 264 or self.position[1] > 232
	
	def scroll(self, y):
		self.position[1] += y
		

class Animation(pygame.sprite.Sprite):
	def __init__(self, spritefile, frames, directions, name):
		pygame.sprite.Sprite.__init__(self)
		self.name = name
		self.frames = frames
		self.directions = directions
		self.sprite = load_png("sprites", spritefile)
		self.image = self.sprite
		self.w = 16
		self.h = 24
		self.rect = pygame.Rect(0, 0, self.w, self.h);
		self.spriterect = pygame.Rect(0, 0, self.w, self.h)
		self.position = [0.0, 0.0]
		self.playing = True
		self.direction = 0
		self.frame = 0
		self.frametime = 5/36
		self.framecounter = 0
		screen = pygame.display.get_surface()
		self.area = screen.get_rect()
	
	def move(self, x_amt, y_amt):
		self.position[0] += x_amt
		self.position[1] += y_amt
		#self.rect.move_ip(x_amt, y_amt)
	
	def moveto(self, xpos, ypos):
		#print(xpos)
		self.position = [xpos, ypos]
		#self.rect.topleft = (xpos, ypos)
	
	def update_anim(self, delta_time):
		if(self.playing):
			self.framecounter += delta_time
			if(self.framecounter > self.frametime):
				self.framecounter -= self.frametime
				self.frame += 1
				if self.frame >= self.frames:
					self.frame = 0
		else:
			self.frame = 0
			self.framecounter == 0
		self.spriterect = pygame.Rect(self.frame * self.w, self.direction * self.h, self.w, self.h)
				
	
	def draw(self, dest):
		dest.blit(self.image, (int(self.position[0]), int(self.position[1])), self.spriterect)

class AnimationGroup:
	def __init__(self):
		self.animations = []
		self.curr_animation = 0
	
	def add_animation(self, animation):
		self.animations.append(animation)
	
	def set_animation(self, name):
		j = 0
		for i in self.animations:
			if(i.name == name):
				self.curr_animation = j
				return
			else:
				j += 1
		errstring = "Error: animation \""
		errstring += name
		errstring += "\" not present in animation list."
		raise LookupError(errstring)
	
	def play(self):
		for i in self.animations:
			i.playing = True
	
	def stop(self):
		for i in self.animations:
			i.playing = False
		
	def set_direction(self, direction):
		for i in self.animations:
			i.direction = direction
	
	def move(self, velocity, delta_time):
		#print(velocity[0] * delta_time, velocity[1] * delta_time)
		for i in self.animations:
			i.move(velocity[0] * delta_time, velocity[1] * delta_time)	
	
	def moveto(self, x, y):
		for i in self.animations:
			i.moveto(x, y)
	
	def set_framerate(self, framerate):
		if framerate < 1:
			return
		frametime = 1/framerate
		self.animations[self.curr_animation].frametime = frametime
	
	def draw(self, dest):
		self.animations[self.curr_animation].draw(dest)
	
	def update(self, delta_time):
		for i in self.animations:
			i.update_anim(delta_time)
	
	def get_position(self):
		#print("player pos", self.animations[0].position)
		return self.animations[0].position

class AimCursor:
	def __init__(self, position):
		self.image = load_png("sprites", "aim-indicator.png")
		self.position = position
		self.direction = 90
		self.vector = [1, 0]
		self.update_vector()
		self.showing = False
	
	def update_vector(self):
		self.vector = [math.cos(math.radians(self.direction)), -math.sin(math.radians(self.direction))]
	
	def change_direction(self, delta):
		self.direction += delta
		self.update_vector()
	
	def draw(self, dest):
		if not self.showing:
			return
		#print("yay cursor draw!")
		curr_position = [self.position[0], self.position[1]]
		curr_position[0] += self.vector[0] * 12
		curr_position[1] += self.vector[1] * 12
		while(curr_position[0] > -8 and curr_position[1] > -8 and curr_position[0] < 264 and curr_position[1] < 232):
			curr_position[0] += self.vector[0] * 12
			curr_position[1] += self.vector[1] * 12
			dest.blit(self.image, (int(curr_position[0]), int(curr_position[1])))
			#print("blit!", curr_position)

class TilemapHandler:
	def __init__(self, tileset, tilemap, collision_map):
		self.tileset = load_png("tiles", tileset)
		self.tilemap = load_hex_map(tilemap)
		self.collision_map = load_hex_map(collision_map)
		self.scroll_position = (len(self.tilemap) - 14) * 16
		#print("map_len", len(self.tilemap))
		#print("scroll at", self.scroll_position)
	
	def draw_ground(self, dest):
		starting_pos = int(self.scroll_position / 16)
		current_pos = starting_pos
		while(current_pos < len(self.tilemap) and (current_pos - starting_pos) < 16):
			for i in range(16):
				tileset_x = (self.tilemap[current_pos][i] % 16) * 16
				tileset_y = self.tilemap[current_pos][i] - tileset_x / 16
				dest.blit(self.tileset, (i * 16, current_pos * 16 - self.scroll_position), pygame.Rect(tileset_x, tileset_y, 16, 16))
			current_pos += 1
	
	#def collide_vecproj(self, hitbox):
		#TODO
		
	
def load_hex_map(filename):
	path = os.path.join("data", filename)
	with open(path, "r") as mapfile:
		mapstrs = mapfile.readlines()
		strmap = []
		for i in mapstrs:
			strmap.append(i.split())
		maparray = []
		for line in strmap:
			tileline = []
			#print(line)
			for tile in line:
				tileline.append(int(tile, 16)) # converts the hex value to an integer
			if(not len(tileline) == 16):
				raise RuntimeError("The map file is invalid or has been corrupted. (line length should be 16)")
			maparray.append(tileline)
		return maparray


class Player:
	def __init__(self):
		self.animations = AnimationGroup()
		self.animations.add_animation(Animation("alice-9mm.png", 6, 8, "9mm"))
		self.velocity = [0, 0]
		self.acceleration = [0, 0]
		self.accel_coef = 80 
		self.drag_coef = 2 # each tick, vel = (vel + acceleration) / drag_coef
		self.shot_timer = 0.0
		self.shot_interval = 0.2
		self.shoot_button_state = False
		self.rapid_fire = True
		self.gun_speed = 320
		self.gun_damage = 40
		self.state = 0 # States: 0 = idle, 1 = moving, 2 = running, 3 = aiming, 4 = hiding, 5 = hiding and aiming, 6 = reloading, 7 = automatic reload
		self.aim_cursor = AimCursor(self.animations.get_position())
		self.aim_tick_count = 0
		
	def update(self, delta_time):
		# Get keyboard presses por movement and compute acceleration
		keys = pygame.key.get_pressed()
		if(self.state == 0):
			if not (self.velocity[0] == 0 and self.velocity[1] == 0):
				self.state = 1
		elif(self.state == 1):
			if self.velocity[0] == 0 and self.velocity[1] == 0:
				self.state = 0
		if((self.state == 0 or self.state == 1) and keys[pygame.K_z]):
			self.acceleration = [0, 0]
			self.state = 3 # Aiming
		if(self.state == 3 and (not keys[pygame.K_z])):
			self.state = 0 # Stop aiming
		if(self.state == 0 or self.state == 1 or self.state == 2 or self.state == 7):
			if keys[pygame.K_UP]:
				if not keys[pygame.K_DOWN]:
					self.acceleration[1] = -self.accel_coef
				else:
					self.acceleration[1] = 0
			elif keys[pygame.K_DOWN]:
				self.acceleration[1] = self.accel_coef
			else:
				self.acceleration[1] = 0
			if keys[pygame.K_LEFT]:
				if not keys[pygame.K_RIGHT]:
					self.acceleration[0] = -self.accel_coef
				else:
					self.acceleration[0] = 0
			elif keys[pygame.K_RIGHT]:
				self.acceleration[0] = self.accel_coef
			else:
				self.acceleration[0] = 0
		# Now, compute velocity
		for i in range(2):
			self.velocity[i] += self.acceleration[i]
			self.velocity[i] /= self.drag_coef
			if(self.velocity[i] < 0.1 and self.velocity[i] > -0.1):
				self.velocity[i] = 0
		#print(self.velocity)
		# Set framerate of animation according to velocity
		abs_vel = math.sqrt(self.velocity[0] ** 2 + self.velocity[1] ** 2)
		if(abs_vel > 0):
			self.animations.play()
			self.animations.set_framerate(abs_vel / 7)
		else:
			self.animations.stop()
		# Compute direction
		direction = compute_direction(self.velocity)
		if(direction > -1):
			self.animations.set_direction(direction)
		# Move character
		self.animations.move(self.velocity, delta_time)
		# Update animation
		self.animations.update(delta_time)
			
		if(self.state == 3): # If aiming:
			self.aim_cursor.showing = True # Show aim cursor
			#print("Cursor on")
			if keys[pygame.K_LEFT]: # Rotate aim cursor using left and right keys
				if not keys[pygame.K_RIGHT]:
					if(self.aim_tick_count > 0):
						self.aim_tick_count = 0
					self.aim_cursor.change_direction((40 - self.aim_tick_count * 15) * delta_time)
					if(self.aim_tick_count >= -30):
						self.aim_tick_count -= 1
				else:
					self.aim_tick_count = 0
			elif keys[pygame.K_RIGHT]:
				if(self.aim_tick_count < 0):
					self.aim_tick_count = 0
				self.aim_cursor.change_direction((-40 - self.aim_tick_count * 15) * delta_time)
				if(self.aim_tick_count <= 30):
					self.aim_tick_count += 1
			else:
				self.aim_tick_count = 0
		else: # Else:
			self.aim_cursor.showing = False # Hide aim cursor
		
		self.aim_cursor.position = [self.animations.get_position()[0] + 12, self.animations.get_position()[1] + 8]
		
		# Update shot timer
		if self.shot_timer > 0:
			self.shot_timer -= delta_time
			#print("shot_timer", self.shot_timer)
		else:
			self.shot_timer = 0
	
	def draw(self, dest):
		self.animations.draw(dest)
		self.aim_cursor.draw(dest)
	
	def moveto(self, x, y):
		self.animations.moveto(x, y)
		self.aim_cursor.position = [self.animations.get_position()[0] + 12, self.animations.get_position()[1] + 8]
	
	def scroll(self, y):
		self.animations.move(0, y)
	
	def shoot_ifbuttonpressed(self, bullet_controller):
		if self.shot_timer > 0:
			return
		keys = pygame.key.get_pressed()
		if(self.state == 3):
			angle = self.aim_cursor.direction
		else:
			angle = 90
		button_state = keys[pygame.K_x]
		if(button_state and (self.rapid_fire or not self.shoot_button_state)):
			bullet_controller.player_shoot([self.animations.get_position()[0] + 12, self.animations.get_position()[1] + 8], angle, self.gun_speed, self.gun_damage)
			self.shot_timer = self.shot_interval
		self.shoot_button_state = button_state

class BulletController:
	def __init__(self):
		self.player_bullets = []
		self.enemy_bullets = []
	
	def player_shoot(self, position, direction, speed, damage):
		self.player_bullets.append(Bullet("shot.png", position, direction, speed, damage, False))
	
	def enemy_shoot(self, position, direction, speed, damage):
		self.enemy_bullets.append(Bullet("shot.png", position, direction, speed, damage, True))
	
	def update_all(self, delta_time):
		#print(len(self.player_bullets), len(self.enemy_bullets))
		for i in self.player_bullets:
			i.update(delta_time)
			if i.is_outside_screen():
				self.player_bullets.remove(i)
		for i in self.enemy_bullets:
			i.update(delta_time)
			if i.is_outside_screen():
				self.enemy_bullets.remove(i)
	
	def check_collision_withenemybul(self, rect):
		bullets = []
		for i in self.enemy_bullets:
			if i.check_collision(rect):
				bullets.append(i)
		return bullets
	
	def check_collision_withplayerbul(self, rect):
		bullets = []
		for i in self.player_bullets:
			if i.check_collision(rect):
				bullets.append(i)
		return bullets
	
	def destroy(self, bullets):
		for i in bullets:
			if i.is_enemy:
				self.enemy_bullets.remove(i)
			else:
				self.player_bullets.remove(i)
	
	def draw_all(self, dest):
		for i in self.enemy_bullets:
			i.draw(dest)
		for i in self.player_bullets:
			i.draw(dest)
	
	
		
# compute_direction: Computes the direction of a velocity vector
def compute_direction(velocity):
	if(velocity[0] == 0 and velocity[1] < 0):
		return 0
	elif(velocity[0] > 0 and velocity[1] < 0):
		return 1
	elif(velocity[0] > 0 and velocity[1] == 0):
		return 2
	elif(velocity[0] > 0 and velocity[1] > 0):
		return 3
	elif(velocity[0] == 0 and velocity[1] > 0):
		return 4
	elif(velocity[0] < 0 and velocity[1] > 0):
		return 5
	elif(velocity[0] < 0 and velocity[1] == 0):
		return 6
	elif(velocity[0] < 0 and velocity[1] < 0):
		return 7
	else:
		return -1

def main():
	pygame.init() # initialize pygame
	clock = pygame.time.Clock() # create a Clock object for timing
	window = pygame.display.set_mode((768, 672)) # create our window
	pygame.display.set_caption("Alice no País de Bolsotaurus")
	imgbuffer = pygame.Surface((256, 224)) # this is where we are going to draw the graphics
	tilemap = TilemapHandler("tilemap-1-0.png", "map-1-0.hmf", "tileset_collision-1-0.hmf")
	alice = Player()
	alice.moveto(120, 100)
	bullet_con = BulletController()
	while(True):
		delta_time = clock.tick(60) / 1000.0 # grab the time passed since last frame
		bullet_con.update_all(delta_time)
		alice.update(delta_time)
		alice.shoot_ifbuttonpressed(bullet_con)
		imgbuffer.fill((0, 0, 0)) # fill the buffer with black pixels
		tilemap.draw_ground(imgbuffer) # draw the ground tile layer
		alice.draw(imgbuffer) # draw the character
		bullet_con.draw_all(imgbuffer)
		window.blit(pygame.transform.scale(imgbuffer, (768, 672)), (0, 0)) # blit our buffer to the main window
		pygame.display.update() # flip the display, showing the graphics
		for event in pygame.event.get(): # check if the window has been closed
			if(event.type == pygame.QUIT):
				pygame.quit() # quit the game
				sys.exit()
	
if __name__ == '__main__': main()