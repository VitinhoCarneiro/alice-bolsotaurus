#!/usr/bin/python3

import pygame
import math
import os
import sys
import random



def load_png(folder, filename):
	#print("Loading PNG @ sprites -", folder, "-", filename) #DBG!
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
		self.direction = direction
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
		self.w = int(self.image.get_width() / frames)
		self.h = int(self.image.get_height() / directions)
		self.rect = pygame.Rect(0, 0, self.w, self.h);
		self.spriterect = pygame.Rect(0, 0, self.w, self.h)
		self.position = [0.0, 0.0]
		self.playing = True
		self.looping = True
		self.direction = 0
		self.frame = 0
		self.frametime = 5/36
		self.framecounter = 0
		screen = pygame.display.get_surface()
		self.area = screen.get_rect()
		self.offsetx = 0
		self.returns = True
	
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
					if(self.returns):
						self.frame = 0
					else:
						self.frame -= 1
					if not self.looping:
						self.playing = False
		else:
			if(self.returns):
				self.frame = 0
			self.framecounter = 0
		self.spriterect = pygame.Rect(self.frame * self.w, self.quantize_direction(self.direction) * self.h, self.w, self.h)
	
	def quantize_direction(self, direction):
		step = 360 / self.directions
		return int((direction + step / 2) / step) % self.directions
	
	def set_offsetx(self, offset):
		self.offsetx = offset
	
	def draw(self, dest):
		dest.blit(self.image, (int(self.position[0] + self.offsetx), int(self.position[1])), self.spriterect)

class AnimationGroup:
	def __init__(self):
		self.animations = []
		self.curr_animation = 0
		
	
	def add_animation(self, animation):
		self.animations.append(animation)
		return animation
	
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
	
	def get_animation(self, name):
		j = 0
		for i in self.animations:
			if(i.name == name):
				return i
			else:
				j += 1
		errstring = "Error: animation \""
		errstring += name
		errstring += "\" not present in animation list."
		raise LookupError(errstring)
		
	def play(self):
		self.animations[self.curr_animation].playing = True
	
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
	
	def move_absolute(self, amount):
		for i in self.animations:
			i.move(amount[0], amount[1])
	
	def moveto(self, x, y):
		for i in self.animations:
			i.moveto(x, y)
	
	def set_framerate(self, framerate):
		if framerate < 1:
			return
		frametime = 1/framerate
		self.animations[self.curr_animation].frametime = frametime
	
	def set_offsetx(self, offset):
		self.animations[self.curr_animation].set_offsetx(offset)
	
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
		self.collision_map = load_hex_array(collision_map)
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
	
	# collide_vecproj: Checks collision on the map and returns a correction vector
	def collide_vecproj(self, hitbox, motion_vector):
		map_pos = [int(hitbox.centerx / 16), int((hitbox.centery + self.scroll_position) / 16)]
		correction_vector = [0, 0]
		collided = False
		
		# Handle horizontal collision
		if(self.collide_to_tile(hitbox, [map_pos[0] + 1, map_pos[1]])):
			# Collision on the right
			collided = True
			correction_vector[0] -= hitbox.right - (map_pos[0] + 1) * 16
		elif(self.collide_to_tile(hitbox, [map_pos[0] - 1, map_pos[1]])):
			# Collision on the left
			collided = True
			#print("hitbox left", hitbox.left, "tile right", ((map_pos[0] - 1) * 16 + 15))
			correction_vector[0] -= hitbox.left - ((map_pos[0] - 1) * 16 + 16)
			
		# Handle vertical collision
		if(self.collide_to_tile(hitbox, [map_pos[0], map_pos[1] - 1])):
			# Collision on the top
			collided = True
			correction_vector[1] -= hitbox.top - ((map_pos[1] - 1) * 16 + 16 - self.scroll_position)
		elif(self.collide_to_tile(hitbox, [map_pos[0], map_pos[1] + 1])):
			# Collision on the bottom
			collided = True
			correction_vector[1] -= hitbox.bottom - ((map_pos[1] + 1) * 16 - self.scroll_position)
		if(collided):
			#print(correction_vector)
			return correction_vector
			
		# We have not collided yet, so check diagonals
		if(self.collide_to_tile(hitbox, [map_pos[0] + 1, map_pos[1] + 1])):
			# Collision on bottom-right
			tile_top = (map_pos[1] + 1) * 16 - self.scroll_position
			tile_left = (map_pos[0] + 1) * 16
			#print("collided bottom-right - tiletop", tile_top, "tileleft", tile_left, "hitboxbottom", hitbox.bottom, "hitboxright", hitbox.right)
			if((hitbox.bottom - motion_vector[1]) < tile_top):
				if((hitbox.right - motion_vector[0]) < tile_left):
					# The entity came from the diagonal
					correction_vector[0] -= hitbox.right - tile_left
					correction_vector[1] -= hitbox.bottom - tile_top
				else:
					# The entity came from the top
					correction_vector[1] -= hitbox.bottom - tile_top
			elif((hitbox.right - motion_vector[0]) < tile_left):
				# The entity came from the right
				correction_vector[0] -= hitbox.right - tile_left
			else:
				# Worst case: things simply don't make sense
				if(math.fabs(motion_vector[1]) > math.fabs(motion_vector[0])):
					correction_vector[1] -= hitbox.bottom - tile_top
				elif(math.fabs(motion_vector[1]) < math.fabs(motion_vector[0])):
					correction_vector[0] -= hitbox.right - tile_left
				else:
					correction_vector[0] -= 1
					correction_vector[1] -= 1
			
				
		elif(self.collide_to_tile(hitbox, [map_pos[0] - 1, map_pos[1] + 1])):
			# Collision on bottom-left
			tile_top = (map_pos[1] + 1) * 16 - self.scroll_position
			tile_right = (map_pos[0] - 1) * 16 + 16
			#print("collided bottom-left - tiletop", tile_top, "tileright", tile_right, "hitboxbottom", hitbox.bottom, "hitboxleft", hitbox.left)
			if((hitbox.bottom - motion_vector[1]) < tile_top):
				if((hitbox.left - motion_vector[0]) > tile_right):
					# The entity came from the diagonal - worst case!
					#print("diagonal - mv", motion_vector)
					correction_vector[0] -= hitbox.left - tile_right
					correction_vector[1] -= hitbox.bottom - tile_top
				else:
					#print("top - mv", motion_vector)
					# The entity came from the top
					correction_vector[1] -= hitbox.bottom - tile_top
			elif((hitbox.left - motion_vector[0]) > tile_right):
				# The entity came from the right
				#print("right - mv", motion_vector)
				correction_vector[0] -= hitbox.left - tile_right
			else:
				# Worst case: things simply don't make sense
				#print("snafu - mv", motion_vector)
				if(math.fabs(motion_vector[1]) > math.fabs(motion_vector[0])):
					correction_vector[1] -= hitbox.bottom - tile_top
				elif(math.fabs(motion_vector[1]) < math.fabs(motion_vector[0])):
					correction_vector[0] -= hitbox.left - tile_right
				else:
					correction_vector[0] += 1
					correction_vector[1] -= 1
				
		elif(self.collide_to_tile(hitbox, [map_pos[0] - 1, map_pos[1] - 1])):
			# Collision on top-left
			tile_bottom = (map_pos[1] - 1) * 16 - self.scroll_position + 15
			tile_right = (map_pos[0] - 1) * 16 + 16
			#print("collided top-left - tilebottom", tile_bottom, "tileright", tile_right, "hitboxtop", hitbox.top, "hitboxleft", hitbox.left)
			if((hitbox.top - motion_vector[1]) > tile_bottom):
				if((hitbox.left - motion_vector[0]) > tile_right):
					# The entity came from the diagonal - worst case!
					correction_vector[0] -= hitbox.left - tile_right
					correction_vector[1] -= hitbox.top - tile_bottom
				else:
					# The entity came from the top
					correction_vector[1] -= hitbox.top - tile_bottom
			elif((hitbox.left - motion_vector[0]) > tile_right):
				# The entity came from the right
				correction_vector[0] -= hitbox.left - tile_right
			else:
				# Worst case: things simply don't make sense
				if(math.fabs(motion_vector[1]) > math.fabs(motion_vector[0])):
					correction_vector[1] -= hitbox.top - tile_bottom
				elif(math.fabs(motion_vector[1]) < math.fabs(motion_vector[0])):
					correction_vector[0] -= hitbox.left - tile_right
				else:
					correction_vector[0] += 1
					correction_vector[1] += 1
				
		elif(self.collide_to_tile(hitbox, [map_pos[0] + 1, map_pos[1] - 1])):
			# Collision on top-right
			tile_bottom = (map_pos[1] - 1) * 16 - self.scroll_position + 15
			tile_left = (map_pos[0] + 1) * 16
			#print("collided top-right - tilebottom", tile_bottom, "tileleft", tile_left, "hitboxtop", hitbox.top, "hitboxright", hitbox.right)
			if((hitbox.top - motion_vector[1]) > tile_bottom):
				if((hitbox.right - motion_vector[0]) < tile_left):
					# The entity came from the diagonal - worst case!
					correction_vector[0] -= hitbox.right - tile_left
					correction_vector[1] -= hitbox.top - tile_bottom
				else:
					# The entity came from the top
					correction_vector[1] -= hitbox.top - tile_bottom
			elif((hitbox.right - motion_vector[0]) < tile_left):
				# The entity came from the right
				correction_vector[0] -= hitbox.right - tile_left
			else:
				# Worst case: things simply don't make sense
				if(math.fabs(motion_vector[1]) > math.fabs(motion_vector[0])):
					correction_vector[1] -= hitbox.top - tile_bottom
				elif(math.fabs(motion_vector[1]) < math.fabs(motion_vector[0])):
					correction_vector[0] -= hitbox.right - tile_left
				else:
					correction_vector[0] -= 1
					correction_vector[1] += 1
				
		#print(correction_vector)
		return correction_vector
		# Ufa!
		
	def collide_check(self, hitbox):
		map_pos = [int(hitbox.centerx / 16), int((hitbox.centery + self.scroll_position) / 16)]
		collided = False
		for i in range(3):
			for j in range(3):
				if(i == 1 and j == 1):
					continue
				else:
					collided = collided or self.collide_to_tile(hitbox, [map_pos[0] - 1 + i, map_pos[1] - 1 + i])
		return collided
		
	def collide_check_high(self, hitbox):
		map_pos = [int(hitbox.centerx / 16), int((hitbox.centery + self.scroll_position) / 16)]
		collided = False
		for i in range(3):
			for j in range(3):
				if(i == 1 and j == 1):
					continue
				else:
					collided = collided or self.collide_to_tile_high(hitbox, [map_pos[0] - 1 + i, map_pos[1] - 1 + i])
		return collided
		
	def collide_to_tile(self, hitbox, tile):
		#print("tile", tile)
		if(tile[0] < 0 or tile[0] > 15 or tile[1] < 0 or tile[1] >= len(self.tilemap)):
			return hitbox.colliderect(pygame.Rect(tile[0] * 16, tile[1] * 16 - self.scroll_position, 16, 16))
		if(self.collision_map[self.tilemap[tile[1]][tile[0]]] == 0):
			#print("0")
			return False
		#print(self.collision_map[self.tilemap[tile[1]][tile[0]]])
		return hitbox.colliderect(pygame.Rect(tile[0] * 16, tile[1] * 16 - self.scroll_position, 16, 16))
		
	def collide_to_tile_high(self, hitbox, tile):
		#print("tile", tile)
		if(tile[0] < 0 or tile[0] > 15 or tile[1] < 0 or tile[1] >= len(self.tilemap)):
			return False
		if(self.collision_map[self.tilemap[tile[1]][tile[0]]] == 2):
			#print("0")
			return hitbox.colliderect(pygame.Rect(tile[0] * 16, tile[1] * 16 - self.scroll_position, 16, 16))
		#print(self.collision_map[self.tilemap[tile[1]][tile[0]]])
		return False
	
	def get_obstacle_value(self, hitbox):
		tile = [int(hitbox.centerx / 16), int((hitbox.centery + self.scroll_position) / 16) - 1]
		close_enough = (hitbox.top - tile[1] * 16 + 16 - self.scroll_position) < 2 and (hitbox.left - tile[0] * 16) > -2 and (hitbox.right - tile[0] * 16 - 16) < 2
		#print("close enough?", close_enough, hitbox.top - tile[1] * 16 + 16, hitbox.left - tile[0] * 16, hitbox.right - tile[0] * 16 + 16)
		if(tile[0] < 0 or tile[0] > 15 or tile[1] < 0 or tile[1] >= len(self.tilemap)):
			return -1, False
		return (self.collision_map[self.tilemap[tile[1]][tile[0]]], close_enough)
	
	def get_map_obstacle_value(self, tile):
		#print("close enough?", close_enough, hitbox.top - tile[1] * 16 + 16, hitbox.left - tile[0] * 16, hitbox.right - tile[0] * 16 + 16)
		if(tile[0] < 0 or tile[0] > 15 or tile[1] < 0 or tile[1] >= len(self.tilemap)):
			return -1
		return self.collision_map[self.tilemap[tile[1]][tile[0]]]
	
	def scroll(self, y):
		self.scroll_position -= y
	
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

def load_hex_array(filename):
	path = os.path.join("data", filename)
	with open(path, "r") as mapfile:
		mapstrs = mapfile.readlines()
		strmap = []
		for i in mapstrs:
			strmap.append(i.split())
		maparray = []
		for line in strmap:
			for tile in line:
				maparray.append(int(tile, 16)) # converts the hex value to an integer
		return maparray

class Enemy:
	def __init__(self):
		self.animations = AnimationGroup()
		self.health = 90
		self.shot_timer = 0.0
		self.shot_interval = 0.4
		self.gun_speed = 180
		self.gun_damage = 20
		self.dead = False
		self.deadanim = False
		self.deathtimer = 1.5
		self.blink_state = False
		self.blink_rate = 1/24
		self.blink_timer = 0.6
		self.taking_damage = False
	
	def update(self, delta_time, bullet_controller, particle_controller):
		if(self.dead):
			if(not self.deadanim):
				self.animations.set_animation("dead")
				self.animations.play()
			if(self.deathtimer > 0):
				self.deathtimer -= delta_time
			else:
				self.deathtimer = 0
			if(self.blink_timer > 0):
				self.blink_timer -= delta_time
			else:
				self.blink_timer = self.blink_rate
				if(self.blink_state):
					self.blink_state = False
				else:
					self.blink_state = True
			self.animations.update(delta_time)
			return
		if(self.taking_damage):
			self.taking_damage = False
			self.animations.set_animation("walk")
		self.check_for_damage(bullet_controller, particle_controller)
		self.shot_timer -= delta_time
		if(self.shot_timer <= 0):
			self.shot_timer = 0
		
	
	def get_hitbox(self):
		topleft = self.animations.get_position()
		return pygame.Rect(topleft[0] + 1, topleft[1] + 1, 14, 22)
		
	def get_coll_hitbox(self):
		topleft = self.animations.get_position()
		return pygame.Rect(topleft[0] + 15, topleft[1] + 1, 16, 9)
		
	def take_damage(self, damage, particle_controller):
		if(self.dead):
			return
		self.health -= damage
		self.animations.set_animation("damage")
		self.taking_damage = True
		if(damage < 50):
			particle_controller.spawn_particle("blood-small", [self.animations.get_position()[0], self.animations.get_position()[1] + 4])
		else:
			#particle_controller.spawn_particle("blood-large", [self.animations.get_position()[0], self.animations.get_position()[1] + 4]) #TODO: Uncomment this and remove below after implementing large blood particles
			particle_controller.spawn_particle("blood-small", [self.animations.get_position()[0], self.animations.get_position()[1] + 4])
		if(self.health <= 0):
			self.die()
	
	def die(self):
		if(self.dead):
			return
		self.dead = True
		
	def is_onscreen(self):
		#print("is_onscreen called, ypos =", self.animations.get_position()[1])
		return self.animations.get_position()[1] > -24 and (not self.is_offscreen())
		
	
	def is_offscreen(self):
		return self.animations.get_position()[1] > 224
	
	
	def check_for_damage(self, bullet_controller, particle_controller):
		if(self.dead):
			return
		hitbox = self.get_hitbox()
		bullets = bullet_controller.collide_player(hitbox)
		for bullet in bullets:
			self.take_damage(bullet.damage, particle_controller)
		melee = bullet_controller.collide_melee_player(hitbox)
		for m in melee:
			self.take_damage(m, particle_controller)
		bullet_controller.destroy(bullets)
	
	def scroll(self, y):
		self.animations.move_absolute([0, y])
	
	def draw(self, dest):
		if self.is_onscreen() and not self.blink_state:
			#print("roar")
			self.animations.draw(dest)

# -- Enemy classes - subclasses of Enemy -- #

class Guard(Enemy):
	def __init__(self, xpos, ypos, scroll_pos, aitype="normal"):
		Enemy.__init__(self)
		self.animations.add_animation(Animation("guard.png", 4, 4, "walk"))
		self.animations.add_animation(Animation("guard-damage.png", 1, 1, "damage"))
		anim = self.animations.add_animation(Animation("guard-die.png", 3, 1, "dead"))
		anim.looping = False
		anim.returns = False
		anim.frametime = 1/8
		#print("new guard at", xpos * 16, ypos * 16 - scroll_pos)
		self.animations.moveto(xpos * 16, ypos * 16 - 8 - scroll_pos)
		self.aitype = aitype
		if not(aitype == "normal" or aitype == "camper"):
			print("Error: Invalid ai type", aitype, "for enemy type \"guard\", defaulting to \"normal\"")
			self.aitype = "normal"
		self.current_tile = [xpos, ypos]
		self.intended_path = [xpos, ypos]
		self.walk_speed = 30
		self.walking_speed = 30
		self.running_speed = 15
		self.running = False
		self.walk_frame_count = 0
		self.velocity = [0, 0]
		self.movement_stack = []
		self.moving = False
		self.stuck_offscreen = False
		
		self.ai_state = 0
		self.cyclic_ai_states = 1
		self.ai_timer = 180 + int(random.random() * 240)
		self.pathfind_range = 3
		
		self.item_drops = [["ammo9mm", 0.14]]
	
	def is_onscreen(self):
		return self.animations.get_position()[1] > -24 and (not self.is_offscreen()) and (not self.stuck_offscreen)
	
	def set_ai_state(self, state, timer = 180, deviation = 240):
		self.ai_timer = timer + int(random.random() * deviation)
		self.ai_state = state
	
	def set_item_drops(self, dropslist):
		self.item_drops = dropslist
		
	def update(self, delta_time, bullet_controller, tilemap, enemy_controller, player, particle_controller):
		Enemy.update(self, delta_time, bullet_controller, particle_controller)
		if(self.dead):
			return
		if(not self.is_onscreen()):
			return
		# -- AI -- #
		if(self.ai_timer > 0):
			self.ai_timer -= 1
		else:
			self.ai_timer = 180 + int(random.random() * 240)
			self.ai_state += 1
			if(self.ai_state >= self.cyclic_ai_states):
				self.ai_state = 0
		if(self.aitype == "normal"):
			if(not self.moving):
				if(self.stuck_offscreen):
					self.stuck_offscreen = False
				if(player.dead):
					self.set_ai_state(1, 180, 45)
				playerpos = player.animations.get_position()
				if(self.ai_state == 0): # Attack
					if(self.animations.get_position()[1] < 0): # Off-screen - get into the screen area
						if not(self.try_movement([0, 1], tilemap, enemy_controller)):
							self.stuck_offscreen = True
					elif(playerpos[1] - self.animations.get_position()[1] > 96): # Too far away from player - try to get close
						if(random.random() < 0.05 and playerpos[1] - self.animations.get_position()[1] < 144):
							self.set_ai_state(2, 120, 90)
						# Intent: move down
						#print("{ai-move}", self, "Trying move down")
						self.try_movement([0, 1], tilemap, enemy_controller)
						#print("{ai-moved}", self, "intended_path =", self.intended_path)
							
					elif(playerpos[1] - self.animations.get_position()[1] > 24): # Close enough
						if(abs(playerpos[0] - self.animations.get_position()[0]) > 48): # Too far away in the X direction
							if(playerpos[0] - self.animations.get_position()[0] > 0): # Player is to the right
								# Intent: move right
								#print("{ai-move}", self, "Trying move right")
								self.try_movement([1, 0], tilemap, enemy_controller)
								#print("{ai-moved}", self, "intended_path =", self.intended_path)
							else:
								# Intent: move left
								#print("{ai-move}", self, "Trying move left")
								self.try_movement([-1, 0], tilemap, enemy_controller)
								#print("{ai-moved}", self, "intended_path =", self.intended_path)
								
						else: # We are going to try to shoot.
							if(random.random() < 0.08):
								self.set_ai_state(1, 90, 60)
							if(self.shot_timer == 0):
								shoot_vector = [playerpos[0] - self.animations.get_position()[0], playerpos[1] - self.animations.get_position()[1]]
								gun_pos = [self.animations.get_position()[0] + 8, self.animations.get_position()[1] + 20]
								bullet_controller.enemy_shoot(gun_pos, compute_direction(shoot_vector) + random.random() * 30 - 15, self.gun_speed, self.gun_damage)
								self.shot_timer = self.shot_interval
								
					else: # Too close or below the player - we don't want that
						# Intent: move up
						self.try_movement([0, -1], tilemap, enemy_controller)
						if(self.animations.get_position()[1] > 160):
							self.running = True
							
						
						
				elif(self.ai_state == 1): # Retreat {non-cyclic}
					if(playerpos[1] - self.animations.get_position()[1] > 80 or playerpos[1] - self.animations.get_position()[1] < 24):
						self.set_ai_state(0)
						
					elif(abs(playerpos[0] - self.animations.get_position()[0]) < 80):
						if(playerpos[0] - self.animations.get_position()[0] < 0): # Player is to the left
							# Intent: move right
							#print("{ai-move}", self, "Trying move right")
							self.try_movement([1, 0], tilemap, enemy_controller)
							#print("{ai-moved}", self, "intended_path =", self.intended_path)
							
						else:
							# Intent: move left
							#print("{ai-move}", self, "Trying move left")
							self.try_movement([-1, 0], tilemap, enemy_controller)
							#print("{ai-moved}", self, "intended_path =", self.intended_path)
				
				
				elif(self.ai_state == 2): # Shoot from far away {non-cyclic}
					if(self.shot_timer == 0):
						shoot_vector = [playerpos[0] - self.animations.get_position()[0], playerpos[1] - self.animations.get_position()[1]]
						gun_pos = [self.animations.get_position()[0] + 8, self.animations.get_position()[1] + 20]
						bullet_controller.enemy_shoot(gun_pos, compute_direction(shoot_vector) + random.random() * 12 - 6, self.gun_speed, self.gun_damage)
						self.shot_timer = self.shot_interval
							
		# -- Handle movement -- #
		if(not self.intended_path == []):
			if(not self.moving):
				self.moving = True
				if(self.running):
					self.walk_speed = self.running_speed
				else:
					self.walk_speed = self.walking_speed
				self.walk_frame_count = self.walk_speed
			if(self.walk_frame_count > 0):
				xpos = (((self.current_tile[0] * self.walk_frame_count) + (self.intended_path[0] * (self.walk_speed - self.walk_frame_count))) / self.walk_speed) * 16 
				ypos = (((self.current_tile[1] * self.walk_frame_count) + (self.intended_path[1] * (self.walk_speed - self.walk_frame_count))) / self.walk_speed) * 16 - tilemap.scroll_position - 8
				#print(self, xpos, ypos)
				self.animations.moveto(xpos, ypos)
				self.walk_frame_count -= 1
			else:
				self.moving = False
				self.running = False
				self.current_tile = self.intended_path
				self.intended_path = []
			
		#TODO - Remove this junk
		"""
		current_pos = self.animations.get_position()
		actual_tile = [(current_pos[0] + 8 - ((current_pos[0] + 8) % 16)) / 16, (current_pos[1] + 8 - ((current_pos[1] + 8) % 16)) / 16] 
		#print(self, "path length =", len(self.intended_path))
		if(not self.intended_path == []):
			if(not self.moving):
				self.moving = True
				if(not self.intended_path == self.current_tile):
					#print(self, "tile", self.current_tile, "path", self.intended_path, "|")
					if(self.current_tile[0] > self.intended_path[0]):
						self.velocity[0] = -self.walk_speed
					elif(self.current_tile[0] < self.intended_path[0]):
						self.velocity[0] = self.walk_speed
					else:
						self.velocity[0] = 0
					if(self.current_tile[1] > self.intended_path[1]):
						self.velocity[1] = -self.walk_speed
					elif(self.current_tile[1] < self.intended_path[1]):
						self.velocity[1] = self.walk_speed
					else:
						self.velocity[1] = 0
					
					
				correction_vector = tilemap.collide_vecproj(self.get_coll_hitbox(), self.velocity)
				if(not correction_vector == [0, 0]):
					self.velocity = [0, 0]
					self.animations.move_absolute(correction_vector)
					self.moving = False
				
			
			if(abs(((current_pos[0] + 8) % 16) - 8) < 1 and abs(((current_pos[1] + 16) % 16) - 8) < 1):
				#self.current_tile = [int((current_pos[0] + 8 - ((current_pos[0] + 8) % 16)) / 16), int((current_pos[1] + 8 + tilemap.scroll_position - ((current_pos[1] + 8) % 16)) / 16)]
				self.current_tile = [int((current_pos[0] + 8) / 16), int((current_pos[1] + 8 + tilemap.scroll_position) / 16)]
				if(self.current_tile == self.intended_path):
					print(self, "hit waypoint", self.intended_path)
					self.velocity = [0, 0]
					self.moving = False
					self.intended_path = []
		
			if(self.moving):
				self.animations.move(self.velocity, delta_time)
		"""
			
			
	
	def lookat_tile(self, delta, tilemap, enemy_controller):
		#print(self, "lookingat", self.current_tile[0] + delta[0], self.current_tile[1] + delta[1])
		e = 0
		if(enemy_controller.check_tile_for_enemy([self.current_tile[0] + delta[0], self.current_tile[1] + delta[1]])):
			e = -1024
		#print(tilemap.get_map_obstacle_value([self.current_tile[0] + delta[0], self.current_tile[1] + delta[1]]) + e)
		return tilemap.get_map_obstacle_value([self.current_tile[0] + delta[0], self.current_tile[1] + delta[1]]) + e
	
	def try_movement(self, delta, tilemap, enemy_controller):
		if(len(self.movement_stack) == 0):
			delta_temp = delta
			while(not self.lookat_tile(delta_temp, tilemap, enemy_controller) == 0):
				self.movement_stack.append(delta_temp)
				delta_temp = self.rotate_delta_cw(delta)
				if(len(self.movement_stack) > 4):
					#print(self, "stuck")
					return False
			self.intended_path = [self.current_tile[0] + delta_temp[0], self.current_tile[1] + delta_temp[1]]
			if(not (tilemap.get_map_obstacle_value(self.intended_path) == 0)):
				print("{try_movement} Oops! intended_path", self.intended_path, "is blocked but was chosen as unblocked (???)")
			return True
		else:
			if(not delta == self.movement_stack[0]):
				self.movement_stack = []
				return self.try_movement(delta, tilemap, enemy_controller)
			delta_temp = self.movement_stack[len(self.movement_stack) - 1]
			while(not self.lookat_tile(delta_temp, tilemap, enemy_controller) == 0):
				delta_temp = self.rotate_delta_cw(delta)
				if(len(self.movement_stack) > 4):
					#print(self, "stuck")
					return False
				self.movement_stack.append(delta_temp)
			self.intended_path = [self.current_tile[0] + delta_temp[0], self.current_tile[1] + delta_temp[1]]
			self.movement_stack.pop()
			return True
				
			
	
	def rotate_delta_cw(self, delta):
		return [-delta[1], delta[0]]
	
	#TODO - Remove this junk
	"""
	def get_path(self, intent, tilemap, enemy_controller):
		if(intent == [0, 1]):
			search_delta_list = [[0, 3], [1, 2], [1, 3], [-1, 2], [-1, 3], [0, 2], [2, 2], [2, 3], [-2, 2], [-2, 3], [3, 2], [3, 3], [-3, 2], [-3, 3]]
		elif(intent == [0, -1]):
			search_delta_list = [[0, -3], [1, -2], [1, -3], [-1, -2], [-1, -3], [0, -2], [2, -2], [2, -3], [-2, -2], [-2, -3], [3, -2], [3, -3], [-3, -2], [-3, -3]]
		elif(intent == [1, 0]):
			search_delta_list = [[3, 0], [2, 1], [3, 1], [2, -1], [3, -1], [2, 0], [2, 2], [3, 2], [2, -2], [3, -2], [2, 3], [3, 3], [2, -3], [3, -3]]
		elif(intent == [-1, 0]):
			search_delta_list = [[-3, 0], [-2, 1], [-3, 1], [-2, -1], [-3, -1], [-2, 0], [-2, 2], [-3, 2], [-2, -2], [-3, -2], [-2, 3], [-3, 3], [-2, -3], [-3, -3]]
		else:
			return []
		if(self.lookat_tile(intent, tilemap, enemy_controller)): # If the intended tile is free:
			return [[self.current_tile[0] + intent[0], self.current_tile[1] + intent[1]]]
		else:
			mapgraph = MapGraph(tilemap, enemy_controller, self.current_tile, self.pathfind_range)
			for tile in search_delta_list:
				path = mapgraph.get_path_to_delta(tile)
				if(len(path) > 0):
					print(self, "at position", self.current_tile, "generated path", path)
					return path
	"""

		
			
		
		

# -- End -- #

#TODO - Remove this junk
"""
class MapGraph:
	def __init__(self, tilemap, enemy_controller, centerpos, radius):
		print("Building graph", self)
		self.graph_size = radius * 2 + 1
		self.radius = radius
		self.graph = []
		self.start_node = radius + 1 + self.graph_size * radius - 1
		self.map_centerpos = centerpos
		# Build the map graph
		for i in range(self.graph_size):
			for j in range(self.graph_size): # Search the area around the center position
				delta = [i - radius, j - radius]
				node = []
				if(tilemap.get_map_obstacle_value([centerpos[0] + delta[0], centerpos[1] + delta[1]]) == 0): # If the node is not an obstacle:
					ds = [[1, 0], [-1, 0], [0, 1], [0, -1]]
					diagonalchecking = [[1, 3], [1, 2], [0, 2], [0, 3]]
					diagonals = [[-1, -1], [-1, 1], [1, 1], [1, -1]]
					marked = []
					for n in range(len(ds)):
						if(not abs(delta[0] + ds[n][0]) > radius and not abs(delta[1] + ds[n][1]) > radius): # If it's not outside the search area
							if(tilemap.get_map_obstacle_value([centerpos[0] + delta[0] + ds[n][0], centerpos[1] + delta[1] + ds[n][1]]) == 0 
							and not enemy_controller.check_tile_for_enemy([centerpos[0] + delta[0] + ds[n][0], centerpos[1] + delta[1] + ds[n][1]])): # If this neighbor is not an obstacle:
								node.append(i + ds[n][0] + (j + ds[n][1]) * (self.graph_size)) # Add this neighbour to the current node
					for d in diagonalchecking:
						if(d[0] in marked and d[1] in marked):
							if(tilemap.get_map_obstacle_value([centerpos[0] + delta[0] + diagonals[d][0], centerpos[1] + delta[1] + diagonals[d][1]]) == 0
							and not enemy_controller.check_tile_for_enemy([centerpos[0] + delta[0] + diagonals[d][0], centerpos[1] + delta[1] + diagonals[d][1]])): # If this neighbor is not an obstacle:
								node.append(i + diagonals[d][0] + (j + diagonals[d][1]) * (self.graph_size)) # Add this neighbour to the current node
				self.graph.append(node)
		self.best_paths = self.build_paths()

	
	# build_paths: Uses Djikstra's algorithm to find the best paths from the center of the graph to any node
	def build_paths(self):
		distance = [32677] * len(self.graph) # Distance from that node to start node - initialized as "infinity" (an impossible large number)
		prev_node = [-1] * len(self.graph)
		unvisited_nodes = []
		for n in range(len(self.graph)):
			unvisited_nodes.append(n)
		
		distance[self.start_node] = 0
		prev_node[self.start_node] = -1
		
		while(len(unvisited_nodes) > 0):
			min_distance = 32677
			current_node = -1
			for n in unvisited_nodes: # Choose the node with the lowest distance value (in the beginning, that will be the start node)
				if(distance[n] < min_distance):
					current_node = n
			if(current_node == -1):
				break # This means there are no more nodes to search, because only obstacles are left.
			unvisited_nodes.remove(current_node)
			
			for nn in self.graph[current_node]:
				alt = distance[current_node] + self.get_length(current_node, nn)
				if(alt < distance[nn]):
					distance[nn] = alt
					prev_node[nn] = current_node
		
		return prev_node
	
	def get_path_to_delta(self, delta):
		node = delta[0] + self.radius + (delta[1] + self.radius) * self.graph_size
		current_node = node
		path = [self.convert_node_to_coord(current_node)]
		while(self.best_paths[current_node] > -1):
			path.insert(0, self.convert_node_to_coord(self.best_paths[current_node]))
			current_node = self.best_paths[current_node]
		return path
	
	def convert_node_to_coord(self, node):
		dx = node % self.graph_size - self.radius
		dy = int((node - dx) / self.graph_size - self.radius)
		print("graph: node", node, "generated delta", dx, dy, "and coord", [self.map_centerpos[0] + dx, self.map_centerpos[1] + dy])
		return [self.map_centerpos[0] + dx, self.map_centerpos[1] + dy]
		
	def get_length(self, node_a, node_b):
		ax = node_a % self.graph_size
		ay = node_a - ax / self.graph_size
		bx = node_b % self.graph_size
		by = node_b - bx / self.graph_size
		if((abs(ax - bx) == 1 and abs(ay - by) == 0) or (abs(ax - bx) == 0 and abs(ay - by) == 1)):
			return 2
		elif (abs(ax - bx) == 1 and abs(ay - by) == 1):
			return 3
		else:
			return 2 * math.sqrt((ax - bx) ** 2 + (ay - by) ** 2)

"""
		
				

class EnemyController:
	def __init__(self, enemyfile, map_scroll):
		self.enemies = []
		self.load_enemy_file(enemyfile, map_scroll)
		self.itemdict = dict()
		self.itemdict["ammo9mm"] = AmmoBox9mm
		self.itemdict["ammo762"] = AmmoBox762
		self.itemdict["medkit"] = Medkit
		self.itemdict["medpack"] = Medpack
		self.itemdict["syringe"] = Syringe
		
	
	def load_enemy_file(self, enemyfile, map_scroll):
		enemydict = dict()
		path = os.path.join("data", enemyfile)
		f = open(path)
		l = f.readline()
		while(not l == ""):
			#print(l)
			if(l == "enemy:\n"):
				l = f.readline()
				while(not l == ":end\n"):
					if not l:
						raise ValueError("The enemy file is invalid.")
					l_keyvalue = l.split("=")
					#print(l_keyvalue)
					enemydict[l_keyvalue[0]] = l_keyvalue[1]
					l = f.readline()
				if(enemydict["type"] == "guard\n"):
					#print("guard")
					self.enemies.append(Guard(int(enemydict["xpos"]), int(enemydict["ypos"]), map_scroll))
				l = f.readline()
			else:
				l = f.readline()
			
	
	def update_all(self, delta_time, bullet_controller, tilemap, player, item_controller, particle_controller):
		for enemy in self.enemies:
			if enemy.is_offscreen():
				self.enemies.remove(enemy)
				#print("enemy disposed")
			else:
				if(enemy.dead and enemy.deathtimer == 0):
					for i in enemy.item_drops:
						if(random.random() < i[1]):
							item_controller.add_item(self.itemdict[i[0]](enemy.current_tile, tilemap.scroll_position))
					self.enemies.remove(enemy)
				elif enemy.is_onscreen():
					#print("updating enemy onscreen @ y =", enemy.animations.get_position()[1])
					enemy.update(delta_time, bullet_controller, tilemap, self, player, particle_controller)
	
	def count_enemies_onscreen(self):
		count = 0
		for enemy in self.enemies:
			if(enemy.is_onscreen()):
				count += 1
		#print("Enemies on screen:", count)
		return count
	
	def draw_all(self, dest):
		for enemy in self.enemies:
			enemy.draw(dest)
	
	def scroll_all(self, amount):
		for enemy in self.enemies:
			enemy.scroll(amount)
	
	def check_tile_for_enemy(self, tile):
		for enemy in self.enemies:
			if(enemy.current_tile == tile or enemy.intended_path == tile):
				return True
		return False
	
	def collide_all(self, hitbox):
		for enemy in self.enemies:
			if(enemy.is_onscreen()):
				if(hitbox.colliderect(enemy.get_coll_hitbox())):
					return True
		return False
			
class Weapon:
	def __init__(self):
		self.shot_interval = 0.25 # The maximum fire rate of the gun (the minimum delay after each shot)
		self.spread_interval = 0.5 # The interval for the spread angle to go from max to min after shooting
		self.spread_angle_min = 3 # The minimum spread angle, in degrees
		self.spread_angle_max = 30 # Max spread angle
		self.walk_spread = 0.4 # From 0.0 to 1.0, how shooting while walking affects the spread angle
		self.rapid_fire = False # True for an automatic weapon, false for a semi-automatic weapon
		self.gun_speed = 360 # The speed at which the bullet travels in pixels/sec
		self.gun_damage = 0 # The damage inflicted by the bullet
		self.gun_ammo = 0 # The amount of rounds currently inside the magazine
		self.gun_capacity = 1 # The amount of rounds the gun can hold in its magazine
		self.ammo_type = 0 # Ammo type - 0 = 9mm, 1 = 7.62 (ammo is shared across guns that use the same ammo type)
		self.reload_time = 1.5
		self.gun_name = "Undefined"
		self.gun_hud_icon = "hud/blank.png"
		#print("Ammo:", self.gun_ammo)
	
	def shoot(self):
		if(self.gun_ammo > 0):
			self.gun_ammo -= 1
			print("Ammo:", self.gun_ammo)
			return True
		else:
			return False
	
	def reload_gun(self, ammo_ptr):
		if(self.gun_ammo >= self.gun_capacity):
			return 0
		if(ammo_ptr[self.ammo_type] == 0):
			if(self.gun_ammo == 0):
				return -1
			else:
				return 0
		if (ammo_ptr[self.ammo_type] > (self.gun_capacity - self.gun_ammo)):
			ammo_ptr[self.ammo_type] -= self.gun_capacity - self.gun_ammo
			self.gun_ammo = self.gun_capacity
		else:
			self.gun_ammo += ammo_ptr[self.ammo_type]
			ammo_ptr[self.ammo_type] = 0
		print("Reloading... Bullets left:", ammo_ptr[self.ammo_type])
		return 1
	
	def is_empty(self):
		return self.gun_ammo <= 0

class Pistol(Weapon):
	def __init__(self):
		Weapon.__init__(self)
		self.shot_interval = 0.25 # The maximum fire rate of the gun (the minimum delay after each shot)
		self.spread_interval = 0.5 # The interval for the spread angle to go from max to min after shooting
		self.spread_angle_min = 3 # The minimum spread angle, in degrees
		self.spread_angle_max = 30 # Max spread angle
		self.walk_spread = 0.4 # From 0.0 to 1.0, how shooting while walking affects the spread angle
		self.rapid_fire = False # True for an automatic weapon, false for a semi-automatic weapon
		self.gun_speed = 360 # The speed at which the bullet travels in pixels/sec
		self.gun_damage = 35 # The damage inflicted by the bullet
		self.gun_ammo = 13 # The amount of rounds currently inside the magazine
		self.gun_capacity = 13 # The amount of rounds the gun can hold in its magazine
		self.ammo_type = 0 # Ammo type - 0 = 9mm, 1 = 7.62 (ammo is shared across guns that use the same ammo type)
		self.reload_time = 1.4
		self.gun_name = "Pistola 9mm"
		self.gun_hud_icon = "hud/pistol_icon.png"
		

class AssaultRifle(Weapon):
	def __init__(self):
		Weapon.__init__(self)
		self.shot_interval = 0.15 # The maximum fire rate of the gun (the minimum delay after each shot)
		self.spread_interval = 0.34 # The interval for the spread angle to go from max to min after shooting
		self.spread_angle_min = 2 # The minimum spread angle, in degrees
		self.spread_angle_max = 40 # Max spread angle
		self.walk_spread = 0.32 # From 0.0 to 1.0, how shooting while walking affects the spread angle
		self.rapid_fire = True # True for an automatic weapon, false for a semi-automatic weapon
		self.gun_speed = 400 # The speed at which the bullet travels in pixels/sec
		self.gun_damage = 42 # The damage inflicted by the bullet
		self.gun_ammo = 30 # The amount of rounds currently inside the magazine
		self.gun_capacity = 30 # The amount of rounds the gun can hold in its magazine
		self.ammo_type = 1 # Ammo type - 0 = 9mm, 1 = 7.62 (ammo is shared across guns that use the same ammo type)
		self.reload_time = 1.8
		self.gun_name = "Rifle de Assalto"
		self.gun_hud_icon = "hud/ar_icon.png"

class M1Garand(Weapon):
	def __init__(self):
		Weapon.__init__(self)
		self.shot_interval = 0.40 # The maximum fire rate of the gun (the minimum delay after each shot)
		self.spread_interval = 0.8 # The interval for the spread angle to go from max to min after shooting
		self.spread_angle_min = 2 # The minimum spread angle, in degrees
		self.spread_angle_max = 25 # Max spread angle
		self.walk_spread = 0.4 # From 0.0 to 1.0, how shooting while walking affects the spread angle
		self.rapid_fire = False # True for an automatic weapon, false for a semi-automatic weapon
		self.gun_speed = 500 # The speed at which the bullet travels in pixels/sec
		self.gun_damage = 108 # The damage inflicted by the bullet
		self.gun_ammo = 8 # The amount of rounds currently inside the magazine
		self.gun_capacity = 8 # The amount of rounds the gun can hold in its magazine
		self.ammo_type = 1 # Ammo type - 0 = 9mm, 1 = 7.62 (ammo is shared across guns that use the same ammo type)
		self.reload_time = 2.1
		self.gun_name = "M1 Garand"
		self.gun_hud_icon = "hud/m1_icon.png"

class SMG(Weapon):
	def __init__(self):
		Weapon.__init__(self)
		self.shot_interval = 0.09 # The maximum fire rate of the gun (the minimum delay after each shot)
		self.spread_interval = 0.26 # The interval for the spread angle to go from max to min after shooting
		self.spread_angle_min = 5 # The minimum spread angle, in degrees
		self.spread_angle_max = 32 # Max spread angle
		self.walk_spread = 0.35 # From 0.0 to 1.0, how shooting while walking affects the spread angle
		self.rapid_fire = True # True for an automatic weapon, false for a semi-automatic weapon
		self.gun_speed = 360 # The speed at which the bullet travels in pixels/sec
		self.gun_damage = 29 # The damage inflicted by the bullet
		self.gun_ammo = 50 # The amount of rounds currently inside the magazine
		self.gun_capacity = 50 # The amount of rounds the gun can hold in its magazine
		self.ammo_type = 0 # Ammo type - 0 = 9mm, 1 = 7.62 (ammo is shared across guns that use the same ammo type)
		self.reload_time = 1.3
		self.gun_name = "Submetralhadora"
		self.gun_hud_icon = "hud/smg_icon.png"

class WeaponController:
	def __init__(self):
		self.weapons = [Pistol(), AssaultRifle(), M1Garand(), SMG()]
		self.owned_weapons = [True, False, False, False] # For debug only! #TODO Uncomment this after debugging
		#self.owned_weapons = [True, True, True, True] # For debug only! #TODO Remove this after debugging
		self.current_weapon = 0
		self.grenades = 0
		self.switch_timer = 0
		self.switch_time = 0.3
		self.ammo = [0, 0] # Indicates the amount of bullets in the inventory (for each type of bullet) #TODO Uncomment this after debugging
		#self.ammo = [800, 800] #TODO Remove this after debugging
		self.no_bullets = False
	
	def shoot(self):
		if(self.switch_timer > 0):
			return False
		else:
			return self.weapons[self.current_weapon].shoot()
	
	def reload_gun(self):
		reload_result = self.weapons[self.current_weapon].reload_gun(self.ammo)
		if(reload_result == 1):
			return 1
		elif(reload_result == 0):
			return 0
		else:
			for i in range(len(self.owned_weapons)):
				weapon_id = 3 - i
				if(self.switch_to(weapon_id)):
					return -1
			self.no_bullets = True
			return -2
	
	def switch_to(self, weapon_index):
		if(self.owned_weapons[weapon_index] and (self.weapons[weapon_index].gun_ammo > 0 or self.ammo[self.weapons[weapon_index].ammo_type] > 0)):
			self.current_weapon = weapon_index
			self.switch_timer = self.switch_time
			print(self.weapons[weapon_index].gun_name, "-", self.weapons[weapon_index].gun_ammo, "/", self.ammo[self.weapons[weapon_index].ammo_type])
			return True
		return False
	
	def add_weapon(self, weapon_index):
		if(self.owned_weapons[weapon_index]):
			return False
		else:
			self.owned_weapons[weapon_index] = True
			self.current_weapon = weapon_index
			return True
	
	def get_current_weapon(self):
		return self.weapons[self.current_weapon]
	
	def is_current_weapon_empty(self):
		return not(self.weapons[self.current_weapon].gun_ammo > 0)
	
	def update(self, delta_time):
		if(self.switch_timer > 0):
			self.switch_timer -= delta_time
		else:
			self.switch_timer = 0
	
	def add_ammo(self, ammo_type, amount):
		self.ammo[ammo_type] += amount
		if(self.no_bullets):
			self.no_bullets = False
			for i in range(len(self.owned_weapons)):
				weapon_id = 3 - i
				if(self.switch_to(weapon_id)):
					return
			print("[Warning] Oops! Player picked up " + amount + "x ammo of type " + ammo_type + ", but could not switch to a weapon for some reason! ammo:", self.ammo)
	
	
	
class Player:
	def __init__(self):
		self.animations = AnimationGroup()
		self.animations.add_animation(Animation("alice-9mm.png", 6, 8, "9mm"))
		anim = self.animations.add_animation(Animation("alice-9mm-shoot.png", 3, 1, "9mm-shoot"))
		anim.playing = False
		anim.looping = False
		anim.frametime = 1/16
		anim = self.animations.add_animation(Animation("alice-9mm-aimshoot.png", 3, 8, "9mm-aimshoot"))
		anim.playing = False
		anim.looping = False
		anim.frametime = 1/16
		anim = self.animations.add_animation(Animation("alice-9mm-hide-low.png", 1, 1, "9mm-hide-low"))
		anim.playing = False
		anim.looping = False
		anim = self.animations.add_animation(Animation("alice-9mm-hide-high.png", 1, 1, "9mm-hide-high"))
		anim.playing = False
		anim.looping = False
		anim = self.animations.add_animation(Animation("alice-9mm-hideaim-low.png", 3, 8, "9mm-hideaim-low"))
		anim.playing = False
		anim.looping = False
		anim.frametime = 1/16
		anim = self.animations.add_animation(Animation("alice-9mm-hideaim-high.png", 3, 8, "9mm-hideaim-high"))
		anim.playing = False
		anim.looping = False
		anim.frametime = 1/16
		anim = self.animations.add_animation(Animation("alice-damage.png", 1, 1, "damage"))
		anim = self.animations.add_animation(Animation("alice-die.png", 3, 1, "dead"))
		anim.looping = False
		anim.returns = False
		anim.frametime = 1/8
		self.weapons = WeaponController()
		self.velocity = [0, 0]
		self.acceleration = [0, 0]
		self.accel_coef = 80
		self.accel_coef_run = 180
		self.accel_coef_reload = 45
		self.drag_coef = 2 # each tick, vel = (vel + acceleration) / drag_coef
		self.shot_timer = 0.0
		self.shot_interval = 0.25
		self.knife_slash_interval = 0.4
		self.spread_timer = 0.0 # Holds the timer for the gun spread
		self.spread_interval = 0.5 # The interval for the spread angle to go from max to min after shooting
		self.spread_angle_min = 3 # The minimum spread angle, in degrees
		self.spread_angle_max = 30 # Max spread angle
		self.walk_spread = 0.4 # From 0.0 to 1.0, how shooting while walking affects the spread angle
		self.shoot_button_state = False # This is used to avoid automatic fire in non-automatic weapons
		self.shoot_buffer = False # This holds a buffer - if you press the shoot key in rapid succession, this ensures the character will shoot at max rate and not stutter
		self.rapid_fire = False
		self.gun_speed = 360
		self.gun_damage = 35
		self.state = 0 # States: 0 = idle, 1 = moving, 2 = running, 3 = aiming, 4 = hiding low, 5 = hiding and aiming low, 6 = hiding high, 7 = hiding and aiming high, 8 = reloading, 9 = automatic reload, 10 = shooting while standing
		self.aim_cursor = AimCursor(self.animations.get_position())
		self.aim_tick_count = 0
		self.health = 100
		self.max_health = 100
		self.syringe_count = 0
		self.syringe_timer = 0
		self.syringe_interval = 0.6
		self.taking_damage = False
		self.lives = 3
		self.dead = False
		self.death_counter = 0
		self.death_time = 90
		self.blink_state = False
		self.blink_rate = 1/24
		self.blink_timer = 0
		self.invincible = False
		self.invincible_timer = 0
		self.invincibility_time = 240
		self.reload_timer = 0
		self.state_before_reload = 0
		
	def update(self, delta_time, tilemap, bullet_controller, particle_controller, enemy_controller):
		if(self.dead):
			if(self.lives == 0):
				return
			if(self.death_counter > 0):	
				self.death_counter -= 1
			else:
				self.death_counter = 0
				self.revive()
			return
				
		if(self.invincible):
			if(self.invincible_timer > 0):
				self.invincible_timer -= 1
			else:
				self.invincible = False
			if(self.blink_timer > 0):
				self.blink_timer -= delta_time
			else:
				self.blink_timer = self.blink_rate
				if(self.blink_state):
					self.blink_state = False
				else:
					self.blink_state = True
		else:
			self.blink_state = False
		
		if(self.taking_damage):
			self.taking_damage = False
			self.set_animation()
		
		if(self.weapons.is_current_weapon_empty()):
			self.reload_automatic()
		
		self.weapons.update(delta_time)
					
		#print("state", self.state)
		# Get keyboard presses for movement and compute acceleration
		keys = pygame.key.get_pressed()
		if(self.state == 0 or self.state == 10):
			if not (self.velocity[0] == 0 and self.velocity[1] == 0):
				self.state = 1
		elif(self.state == 1):
			if self.velocity[0] == 0 and self.velocity[1] == 0:
				self.state = 0
		if(self.state == 1 and keys[pygame.K_c]):
			self.state = 2
		elif(self.state == 2 and (not keys[pygame.K_c] or not (self.velocity[0] == 0 and self.velocity[1] == 0))):
			self.state = 1
		if((self.state == 4 or self.state == 6) and keys[pygame.K_z]):
			self.state += 1 # Aim from obstacle
			self.set_animation()
		if((self.state == 5 or self.state == 7) and (not keys[pygame.K_z])):
			self.state -= 1 # Return to obstacle
			self.set_animation()
		if((self.state == 0 or self.state == 1 or self.state == 10) and keys[pygame.K_z]):
			self.acceleration = [0, 0]
			obstacle = tilemap.get_obstacle_value(pygame.Rect(self.animations.get_position()[0], self.animations.get_position()[1] + 15, 16, 9))
			if(obstacle[1]): # If behind the zone for an obstacle...
				if(obstacle[0] == 1): # If it's low
					self.state = 4
					self.set_animation()
				elif(obstacle[0] == 2): # If it's high
					self.state = 6
					self.set_animation()
				else: # If it's not an obstacle
					self.state = 3 # Aiming
			else:
				self.state = 3 # Aiming
		if(self.state == 3 and (not keys[pygame.K_z])):
			self.state = 0 # Stop aiming
		if((self.state == 4 or self.state == 6) and (keys[pygame.K_LEFT] or keys[pygame.K_RIGHT] or keys[pygame.K_DOWN])):
			self.state = 0 # Get out of obstacle
		
		if(self.state == 8 or self.state == 9):
			self.reload_timer -= delta_time
			if(self.reload_timer <= 0):
				reload_timer = 0
				self.state = self.state_before_reload
				print("Ready")
		
		if(self.syringe_timer > 0):
			self.syringe_timer -= delta_time
		else:
			self.syringe_timer = 0
		
		# Compute acceleration
		if(self.state == 0 or self.state == 1 or self.state == 2 or self.state == 9 or self.state == 10):
			if(self.state == 2):
				accel_coef = self.accel_coef_run
			elif(self.state == 9):
				accel_coef = self.accel_coef_reload
			else:
				accel_coef = self.accel_coef
			if keys[pygame.K_UP]:
				if not keys[pygame.K_DOWN]:
					self.acceleration[1] = -accel_coef
				else:
					self.acceleration[1] = 0
			elif keys[pygame.K_DOWN]:
				self.acceleration[1] = accel_coef
			else:
				self.acceleration[1] = 0
			if keys[pygame.K_LEFT]:
				if not keys[pygame.K_RIGHT]:
					self.acceleration[0] = -accel_coef
				else:
					self.acceleration[0] = 0
			elif keys[pygame.K_RIGHT]:
				self.acceleration[0] = accel_coef
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
		if(self.state == 0 or self.state == 1 or self.state == 2 or self.state == 9):
			self.set_animation()
			abs_vel = math.sqrt(self.velocity[0] ** 2 + self.velocity[1] ** 2)
			if(abs_vel > 0):
				self.animations.play()
				self.animations.set_framerate(abs_vel / 7)
			else:
				self.animations.stop()
			# Compute direction
			direction = compute_direction(self.velocity)
			#print("playerdir -", direction)
			if(direction > -1):
				self.animations.set_direction(direction)
		# Move character
		self.animations.move(self.velocity, delta_time)
		# Check collision with enemies and cancel movement in case it occurs
		if(enemy_controller.collide_all(self.get_hitbox())):
			self.animations.move([-self.velocity[0], -self.velocity[1]], delta_time)
		# Avoid character from going below the screen
		if(self.animations.get_position()[1] > 200):
			self.animations.move_absolute([0, -(self.animations.get_position()[1] - 200)])
		# Avoid character from going above the screen
		if(self.animations.get_position()[1] < -8):
			self.animations.move_absolute([0, -(self.animations.get_position()[1] + 8)])
		# Check and correct for collision on the map
		motion_vector = [self.velocity[0] * delta_time, self.velocity[1] * delta_time]
		hitbox = pygame.Rect(self.animations.get_position()[0], self.animations.get_position()[1] + 15, 16, 9)
		correction_vector = tilemap.collide_vecproj(hitbox, motion_vector)
		self.animations.move_absolute(correction_vector)
		# Update aim
		self.aim_cursor.position = [self.animations.get_position()[0] + 12, self.animations.get_position()[1] + 8]
		# Update animation
		self.animations.update(delta_time)
		
		if(self.state == 6):
			self.animations.set_offsetx(0)
		
			
		if(self.state == 3 or self.state == 5 or self.state == 7): # If aiming:
			self.set_animation()
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
			self.animations.set_direction(self.aim_cursor.direction % 360)
			if(not self.state == 7):
				self.aim_cursor.position = [self.animations.get_position()[0] + 12, self.animations.get_position()[1] + 8]
			else:
				if((self.aim_cursor.direction % 360) >= 90 and (self.aim_cursor.direction % 360) < 180):
					self.aim_cursor.position = [self.animations.get_position()[0] - 4, self.animations.get_position()[1] + 8]
					self.animations.set_offsetx(-8)
				elif((self.aim_cursor.direction % 360) < 90 and (self.aim_cursor.direction % 360) > 0):
					self.aim_cursor.position = [self.animations.get_position()[0] + 22, self.animations.get_position()[1] + 8]
					self.animations.set_offsetx(8)
				else:
					self.aim_cursor.position = [self.animations.get_position()[0] + 8, self.animations.get_position()[1] + 24]
					self.animations.set_offsetx(0)
		else: # Else:
			self.aim_cursor.showing = False # Hide aim cursor
		
		
		
		# Update shot and spread timer
		if self.shot_timer > 0:
			self.shot_timer -= delta_time
			#print("shot_timer", self.shot_timer)
		else:
			self.shot_timer = 0
		
		if self.spread_timer > 0:
			self.spread_timer -= delta_time
		else:
			self.spread_timer = 0
		
		self.check_for_damage(bullet_controller)
		
	
	def set_animation(self):
		if(self.state == 0 or self.state == 1):
			self.animations.set_animation("9mm")
		elif(self.state == 3):
			self.animations.set_animation("9mm-aimshoot")
		elif(self.state == 4):
			self.animations.set_animation("9mm-hide-low")
		elif(self.state == 5):
			self.animations.set_animation("9mm-hideaim-low")
		elif(self.state == 6):
			self.animations.set_animation("9mm-hide-high")
		elif(self.state == 7):
			self.animations.set_animation("9mm-hideaim-high")
		elif(self.state == 10):
			self.animations.set_animation("9mm-shoot")
		elif(self.state == 8 or self.state == 9):
			self.set_animation_forced(self.state_before_reload)
	
	def set_animation_forced(self, state):
		if(state == 0 or state == 1):
			self.animations.set_animation("9mm")
		elif(state == 3):
			self.animations.set_animation("9mm-aimshoot")
		elif(state == 4):
			self.animations.set_animation("9mm-hide-low")
		elif(state == 5):
			self.animations.set_animation("9mm-hideaim-low")
		elif(state == 6):
			self.animations.set_animation("9mm-hide-high")
		elif(state == 7):
			self.animations.set_animation("9mm-hideaim-high")
		elif(state == 10):
			self.animations.set_animation("9mm-shoot")
	
	def draw(self, dest):
		if(not self.blink_state):
			self.animations.draw(dest)
		if(not self.dead):
			self.aim_cursor.draw(dest)
			pygame.draw.line(dest, pygame.Color(240, 0, 0, 0), (self.animations.get_position()[0], self.animations.get_position()[1] - 2), (self.animations.get_position()[0] + int(16 * (self.health / 100)), self.animations.get_position()[1] - 2))
	
	def get_hitbox(self):
		topleft = self.animations.get_position()
		return pygame.Rect(topleft[0] + 1, topleft[1] + 1, 14, 22)
	
	def get_coll_hitbox(self):
		topleft = self.animations.get_position()
		return pygame.Rect(topleft[0], topleft[1] + 15, 16, 9)
		
	def check_for_damage(self, bullet_controller):
		if(self.dead):
			return
		hitbox = self.get_hitbox()
		bullets = bullet_controller.collide_enemy(hitbox)
		if(not self.invincible):
			if not(self.state == 4 or self.state == 6 or ((self.state == 8 or self.state == 9) and (self.state_before_reload == 4 or self.state_before_reload == 6))):
				for bullet in bullets:
					self.take_damage(bullet.damage)
			else:
				if(self.state == 6 or self.state_before_reload == 6):
					for bullet in bullets:
						if(bullet.direction > 30 and bullet.direction < 150):
							self.take_damage(bullet.damage)
				else:
					for bullet in bullets:
						if(bullet.direction > 10 and bullet.direction < 170):
							self.take_damage(bullet.damage)
		bullet_controller.destroy(bullets)
		
	def take_damage(self, damage):
		if(self.dead):
			return
		self.health -= damage
		print("Health:", self.health)
		self.animations.set_animation("damage")
		self.taking_damage = True
		if(self.health <= 0):
			self.die()
	
	def die(self):
		print("YOU ARE DEAD!!!")
		self.dead = True
		self.death_counter = self.death_time
		self.animations.set_animation("dead")
		self.animations.play()
	
	def revive(self):
		if(self.lives <= 0):
			return
		self.lives -= 1
		self.health = self.max_health
		self.invincible = True
		self.invincible_timer = self.invincibility_time
		self.dead = False
		self.state = 0
		self.animations.set_animation("9mm")
		print("Health:", self.health, "  Lives:", self.lives)
		
	
	def moveto(self, x, y):
		self.animations.moveto(x, y)
		self.aim_cursor.position = [self.animations.get_position()[0] + 12, self.animations.get_position()[1] + 8]
	
	def scroll(self, y):
		self.animations.move_absolute([0, y])
	
	def shoot_ifbuttonpressed(self, bullet_controller, particle_controller):
		if(self.weapons.no_bullets):
			keys = pygame.key.get_pressed()
			button_state = keys[pygame.K_x]
			if(self.shot_timer > 0):
				if(button_state and not self.shoot_button_state):
					self.shoot_buffer = True
				self.shoot_button_state = button_state
				return
			else:
				if(button_state and not self.shoot_button_state) or (self.shoot_buffer):
					bullet_controller.player_melee_attack(pygame.Rect(self.animations.get_position()[0] - 5, self.animations.get_position()[1] - 6, 29, 24), int(35 + (random.random() * 20)))
					particle_controller.spawn_particle("knife-slash", (self.animations.get_position()[0] - 8, self.animations.get_position()[1] - 8))
					self.shot_timer = self.knife_slash_interval
					if(self.shoot_buffer):
						self.shoot_buffer = False
					
		else:
			if(self.state == 2 or self.state == 4 or self.state == 6 or self.state == 8 or self.state == 9):
				return
			weapon = self.weapons.get_current_weapon()
			keys = pygame.key.get_pressed()
			button_state = keys[pygame.K_x]
			if(self.shot_timer > 0):
				if(button_state and (not weapon.rapid_fire and not self.shoot_button_state)):
					self.shoot_buffer = True
				self.shoot_button_state = button_state
				return
			else:
				if(self.state == 3 or self.state == 5 or self.state == 7):
					angle = self.aim_cursor.direction
				else:
					angle = 90
				# Spread
				if(self.state == 1):
					spread_coeff = max(weapon.walk_spread, (self.spread_timer / weapon.spread_interval))
				else:
					spread_coeff = (self.spread_timer / weapon.spread_interval)
				spread_range = ((weapon.spread_angle_min * (1 - spread_coeff)) + (weapon.spread_angle_max * spread_coeff))
				angle += (random.random() - 0.5) * spread_range
		
			
				if(button_state and (weapon.rapid_fire or not self.shoot_button_state)) or (self.shoot_buffer):
					if(self.weapons.shoot()):
						bullet_controller.player_shoot(self.aim_cursor.position, angle, weapon.gun_speed, weapon.gun_damage)
						self.spread_timer += weapon.spread_interval * 0.8
						if(self.spread_timer > weapon.spread_interval):
							self.spread_timer = weapon.spread_interval
						if(self.state == 0):
							self.state = 10
							self.set_animation()
						if(not self.state == 1):
							self.animations.play()
						self.shot_timer = weapon.shot_interval
						if(self.shoot_buffer):
							self.shoot_buffer = False
					
		self.shoot_button_state = button_state
	
	def reload_ifbuttonpressed(self):
		keys = pygame.key.get_pressed()
		button_state = keys[pygame.K_d]
		if(button_state):
			reload_result = self.weapons.reload_gun()
			if(reload_result == 1):
				self.reload_timer = self.weapons.get_current_weapon().reload_time
				self.state_before_reload = self.state
				self.state = 9
	
	def reload_automatic(self):
		reload_result = self.weapons.reload_gun()
		if(reload_result == 1):
			self.reload_timer = self.weapons.get_current_weapon().reload_time
			self.state_before_reload = self.state
			self.state = 9
	
	def change_weapon_ifbuttonpressed(self):
		if(self.reload_timer > 0):
			return
		keys = pygame.key.get_pressed()
		if(keys[pygame.K_4]):
			self.weapons.switch_to(3)			
		elif(keys[pygame.K_3]):
			self.weapons.switch_to(2)
		elif(keys[pygame.K_2]):
			self.weapons.switch_to(1)
		elif(keys[pygame.K_1]):
			self.weapons.switch_to(0)
	
	def use_syringe_ifbuttonpressed(self):
		keys = pygame.key.get_pressed()
		if(keys[pygame.K_s]):
			if(self.syringe_count > 0 and self.syringe_timer == 0):
				if(self.heal(15)):
					self.syringe_count -= 1
					print("Used a syringe. Syringes left:", self.syringe_count)
					self.syringe_timer = self.syringe_interval
	
	def add_ammo(self, ammo_type, amount):
		self.weapons.add_ammo(ammo_type, amount)
	
	def heal(self, amount):
		if(self.health >= self.max_health):
			self.health = self.max_health
			return False
		elif((self.health + amount) > self.max_health):
			self.health = self.max_health
			return True
		else:
			self.health += amount
			return True
	
	def add_syringe(self):
		self.syringe_count += 1

class Item:
	def __init__(self, spritefile, tile, map_scroll, destroy_timer = 10):
		self.image = load_png("sprites", spritefile)
		self.position = [tile[0] * 16, (tile[1] * 16) - map_scroll]
		self.w = 16
		self.h = 16
		self.destroy_timer = destroy_timer
		self.blink_state = False
		self.blink_rate = 1/24
		self.blink_timer = 0
	
	def update(self, delta_time):
		if(self.destroy_timer <= 1.5):
			if(self.blink_timer > 0):
				self.blink_timer -= delta_time
			else:
				self.blink_timer = self.blink_rate
				if(self.blink_state):
					self.blink_state = False
				else:
					self.blink_state = True
					
		if not(self.destroy_timer > 3600):
			if(self.destroy_timer < 0):
				self.destroy_timer = 0
			else:
				self.destroy_timer -= delta_time
	
	def draw(self, dest):
		if not(self.blink_state or self.destroy_timer <= 0):
			dest.blit(self.image, (self.position[0], self.position[1]))
	
	def is_onscreen(self):
		return (self.position[1] > -16 and self.position[1] < 240)
	
	def is_offscreen(self):
		return self.position[1] >= 240
	
	def get_hitbox(self):
		return pygame.Rect(self.position[0] - 1, self.position[1] - 1, self.w + 2, self.h + 2)
	
	def pickup_action(self, player):
		print("An undefined item has been picked up at", self.position)
		return True
	
	def scroll(self, y):
		self.position[1] += y
		#print(self, "position:", self.position)

class AmmoBox9mm(Item):
	def __init__(self, tile, map_scroll, ammo = 26, destroy_timer = 10):
		Item.__init__(self, "item-ammo9mm.png", tile, map_scroll, destroy_timer)
		self.ammo = ammo
	
	def pickup_action(self, player):
		player.add_ammo(0, self.ammo)
		# play_sfx("item-ammo.ogg")
		print("9mm ammo: +", self.ammo)
		return True

class AmmoBox762(Item):
	def __init__(self, tile, map_scroll, ammo = 45, destroy_timer = 10):
		Item.__init__(self, "item-ammo762.png", tile, map_scroll, destroy_timer)
		self.ammo = ammo
	
	def pickup_action(self, player):
		player.add_ammo(1, self.ammo)
		# play_sfx("item-ammo.ogg")
		print(".762 ammo: +", self.ammo)
		return True

class Medkit(Item):
	def __init__(self, tile, map_scroll, health = 20, destroy_timer = 15):
		Item.__init__(self, "item-medkit_small.png", tile, map_scroll, destroy_timer)
		self.health = health
	
	def pickup_action(self, player):
		if(player.heal(self.health)):
			# play_sfx("item-health.ogg")
			print("Medkit picked up; HP +", self.health)
			return True
		else:
			return False

class Medpack(Item):
	def __init__(self, tile, map_scroll, health = 60, destroy_timer = 15):
		Item.__init__(self, "item-medkit_large.png", tile, map_scroll, destroy_timer)
		self.health = health
	
	def pickup_action(self, player):
		if(player.heal(self.health)):
			# play_sfx("item-health.ogg")
			print("Medpack picked up; HP +", self.health)
			return True
		else:
			return False

class Syringe(Item):
	def __init__(self, tile, map_scroll, destroy_timer = 8):
		Item.__init__(self, "item-syringe.png", tile, map_scroll, destroy_timer)
	
	def pickup_action(self, player):	
		player.add_syringe()
		# play_sfx("item-health.ogg")
		print("Syringe +1")
		return True



class ItemController:
	def __init__(self, itemfile = "", map_scroll = 0):
		self.items = []
		if(itemfile):
			self.load_item_file(itemfile, map_scroll)
			#print(self.items)
	
	def add_item(self, item):
		self.items.append(item)
	
	def load_item_file(self, itemfile, map_scroll):
		itemdict = dict()
		path = os.path.join("data", itemfile)
		f = open(path)
		l = f.readline()
		while(not l == ""):
			#print(l)
			if(l == "item:\n"):
				l = f.readline()
				while(not l == ":end\n"):
					if not l:
						raise ValueError("The item file is invalid.")
					l_keyvalue = l.split("=")
					#print(l_keyvalue)
					itemdict[l_keyvalue[0]] = l_keyvalue[1]
					l = f.readline()
				if(itemdict["type"] == "dummy\n"):
					self.items.append(Item("item-dummy.png", [int(itemdict["xpos"]), int(itemdict["ypos"])], map_scroll, 3600))
				elif(itemdict["type"] == "ammo9mm\n"):
					self.items.append(AmmoBox9mm([int(itemdict["xpos"]), int(itemdict["ypos"])], map_scroll, int(itemdict["ammo"]), 3600))
				elif(itemdict["type"] == "ammo762\n"):
					self.items.append(AmmoBox762([int(itemdict["xpos"]), int(itemdict["ypos"])], map_scroll, int(itemdict["ammo"]), 3600))
				elif(itemdict["type"] == "medkit\n"):
					self.items.append(Medkit([int(itemdict["xpos"]), int(itemdict["ypos"])], map_scroll, 20, 3600))
				elif(itemdict["type"] == "medpack\n"):
					self.items.append(Medpack([int(itemdict["xpos"]), int(itemdict["ypos"])], map_scroll, 60, 3600))
				elif(itemdict["type"] == "syringe\n"):
					self.items.append(Syringe([int(itemdict["xpos"]), int(itemdict["ypos"])], map_scroll, 3600))
				l = f.readline()
			else:
				l = f.readline()
	
	
	def draw_all(self, dest):
		for item in self.items:
			if item.is_onscreen():
				#print("drawing", item)
				item.draw(dest)		
	
	def update_all(self, delta_time):
		for item in self.items:
			if(item.is_offscreen() or item.destroy_timer == 0):
				self.items.remove(item)
			else:
				if item.is_onscreen():
					item.update(delta_time)
	
	def scroll_all(self, y):
		for item in self.items:
			item.scroll(y)
	
	def check_collision(self, hitbox, player):
		for item in self.items:
			if item.is_onscreen():
				if(hitbox.colliderect(item.get_hitbox())):
					if(item.pickup_action(player)):
						self.items.remove(item)
	

class BulletController:
	def __init__(self):
		self.player_bullets = []
		self.enemy_bullets = []
		self.player_melee = []
	
	def player_shoot(self, position, direction, speed, damage):
		self.player_bullets.append(Bullet("shot.png", position, direction, speed, damage, False))
	
	def player_melee_attack(self, rect, damage, timeout = 1):
		self.player_melee.append([rect, damage, timeout])
	
	def enemy_shoot(self, position, direction, speed, damage):
		self.enemy_bullets.append(Bullet("shot.png", position, direction, speed, damage, True))
	
	def update_all(self, delta_time, tilemap):
		#print(len(self.player_bullets), len(self.enemy_bullets))
		for i in self.player_bullets:
			i.update(delta_time)
			if i.is_outside_screen():
				self.player_bullets.remove(i)
				continue
			for h in i.hitboxes:
				if tilemap.collide_check_high(h):
					self.player_bullets.remove(i)
					break
		for i in self.enemy_bullets:
			i.update(delta_time)
			if i.is_outside_screen():
				self.enemy_bullets.remove(i)
				continue
			for h in i.hitboxes:
				if tilemap.collide_check_high(h):
					self.enemy_bullets.remove(i)
					break
		for i in self.player_melee:
			i[2] -= 1
			if not(i[2]) > 0:
				self.player_melee.remove(i)
	
	def collide_enemy(self, rect):
		bullets = []
		for i in self.enemy_bullets:
			if i.check_collision(rect):
				bullets.append(i)
		return bullets
	
	def collide_player(self, rect):
		bullets = []
		for i in self.player_bullets:
			if i.check_collision(rect):
				bullets.append(i)
		return bullets
	
	def collide_melee_player(self, rect):
		damage = []
		for i in self.player_melee:
			if rect.colliderect(i[0]):
				damage.append(i[1])
		return damage
	
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
	
	def scroll(self, y):
		for i in self.player_bullets:
			i.scroll(y)
		for i in self.enemy_bullets:
			i.scroll(y)

class Particle:
	def __init__(self, animation, position, lifetime, speed = [0, 0]):
		self.animation = animation
		self.name = animation.name
		self.animation.moveto(position[0], position[1])
		self.life_timer = lifetime
		self.speed = speed
	
	def update(self, delta_time):
		if(self.life_timer > 0):
			self.life_timer -= delta_time
			self.animation.move(self.speed[0] * delta_time, self.speed[1] * delta_time)
			self.animation.update_anim(delta_time)
		else:
			self.life_timer = 0
	
	def draw(self, dest):
		if(self.life_timer > 0):
			self.animation.draw(dest)
	
	def scroll(self, y):
		self.animation.move(0, y)
	
	def name_is(self, name):
		return self.name == name
	
	def move(self, motion_vector):
		self.animations.move(motion_vector[0], motion_vector[1])

class Particle_KnifeSlash(Particle):
	def __init__(self, position, direction = 90):
		Particle.__init__(self, Animation("knife-slash.png", 3, 8, "knife-slash"), position, 6/60)
		self.animation.looping = False
		self.animation.returns = False
		self.animation.frametime = 2/60
		self.animation.direction = direction
		self.animation.update_anim(0)

class Particle_BloodSmall(Particle):
	def __init__(self, position, speed = [0, 0]):
		Particle.__init__(self, Animation("blood-small.png", 4, 3, "blood-small"), position, 10/60, speed)
		self.animation.looping = False
		self.animation.returns = False
		self.animation.frametime = 10/180
		self.animation.direction = int(random.random() * 360)
		self.animation.update_anim(0)
	

class ParticleController:
	def __init__(self):
		self.particles = []
		self.particle_dict = dict()
		self.particle_dict["knife-slash"] = Particle_KnifeSlash
		self.particle_dict["blood-small"] = Particle_BloodSmall
		
	
	def update_all(self, delta_time):
		for p in self.particles:
			p.update(delta_time)
			if(p.life_timer <= 0):
				self.particles.remove(p)
	
	def draw_all(self, dest):
		for p in self.particles:
			p.draw(dest)
	
	def spawn_particle(self, name, position, *args):
		self.particles.append(self.particle_dict[name](position, *args))

	def scroll_all(self, y):
		for p in self.particles:
			p.scroll(y)
	
	def move_particles_by_name(self, name, motion_vector):
		for p in self.particles:
			if(p.name_is(name)):
				p.move(motion_vector)

	
	
# compute_direction: Computes the direction of a velocity vector
def compute_direction(velocity):
	if(velocity[0] == 0 and velocity[1] == 0):
		return -1
	else:
		vec = pygame.math.Vector2(velocity[0], -velocity[1])
		if(vec.length_squared() > 0.05):
			return int(vec.as_polar()[1]) % 360
		else:
			return -1

def int_dither(value):
	intvalue = int(value)
	if(intvalue == value):
		return intvalue
	else:
		if(random.random() < (value - intvalue)):
			return intvalue + 1
		else:
			return intvalue

def get_scroll_amount(player, tilemap):
	playerpos = player.animations.get_position()[1]
	#print(playerpos, tilemap.scroll_position)
	if(playerpos < 120 and tilemap.scroll_position > 0):
		if(tilemap.scroll_position > playerpos - 120):
			if(abs(playerpos - 120) < 2):
				return (-(playerpos - 120))
			else:
				return min(max(1, int_dither(-(playerpos - 120) / 10)), 3)
		else:
			return int(tilemap.scroll_position)
	else:
		return 0

def main():
	pygame.init() # initialize pygame
	clock = pygame.time.Clock() # create a Clock object for timing
	window = pygame.display.set_mode((768, 672)) # create our window
	pygame.display.set_caption("Alice no País de Bolsotaurus")
	imgbuffer = pygame.Surface((256, 224)) # this is where we are going to draw the graphics
	tilemap = TilemapHandler("tilemap-1-0.png", "map-1-0.hmf", "tileset_collision-1-0.hmf")
	uppermap = TilemapHandler("tilemap-1-0.png", "uppermap-1-0.hmf", "tileset_collision-1-0.hmf")
	alice = Player()
	alice.moveto(120, 100)
	bullet_con = BulletController()
	enemy_con = EnemyController("enemies-1-0.dat", tilemap.scroll_position)
	#item_con = ItemController() #TODO: Debugging only - uncomment this and remove line below
	item_con = ItemController("items-1-0.dat", tilemap.scroll_position)
	particle_con = ParticleController()
	scroll_lock = False
	random.seed()
	while(True):
		# Update
		delta_time = clock.tick(60) / 1000.0 # grab the time passed since last frame
		enemy_con.update_all(delta_time, bullet_con, tilemap, alice, item_con, particle_con)
		item_con.update_all(delta_time)
		bullet_con.update_all(delta_time, tilemap)
		particle_con.update_all(delta_time)
		alice.update(delta_time, tilemap, bullet_con, particle_con, enemy_con)
		alice.shoot_ifbuttonpressed(bullet_con, particle_con)
		alice.reload_ifbuttonpressed()
		alice.change_weapon_ifbuttonpressed()
		alice.use_syringe_ifbuttonpressed()
		item_con.check_collision(alice.get_coll_hitbox(), alice)
		if(not scroll_lock):
			if(enemy_con.count_enemies_onscreen() >= 4):
				scroll_lock = True
		else:
			if(enemy_con.count_enemies_onscreen() == 0):
				scroll_lock = False
		if(not scroll_lock):
			scroll = get_scroll_amount(alice, tilemap)
		else:
			scroll = 0
		if(scroll > 0):
			bullet_con.scroll(scroll)
			alice.scroll(scroll)
			tilemap.scroll(scroll)
			uppermap.scroll(scroll)
			enemy_con.scroll_all(scroll)
			item_con.scroll_all(scroll)
			particle_con.scroll_all(scroll)
		# Draw
		imgbuffer.fill((0, 0, 0)) # fill the buffer with black pixels
		tilemap.draw_ground(imgbuffer) # draw the ground tile layer
		item_con.draw_all(imgbuffer)
		enemy_con.draw_all(imgbuffer)
		alice.draw(imgbuffer) # draw the character
		particle_con.draw_all(imgbuffer)
		bullet_con.draw_all(imgbuffer)
		uppermap.draw_ground(imgbuffer)
		window.blit(pygame.transform.scale(imgbuffer, (768, 672)), (0, 0)) # blit our buffer to the main window
		pygame.display.update() # flip the display, showing the graphics
		for event in pygame.event.get(): # check if the window has been closed
			if(event.type == pygame.QUIT):
				pygame.quit() # quit the game
				sys.exit()


if __name__ == '__main__': main()