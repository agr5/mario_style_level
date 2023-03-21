import pygame

from support import import_csv_layout, import_cut_graphics
from settings import tile_size, screen_height, screen_width
from tiles import Tile, StaticTile, Crate, AnimatedTile, Coin, Palm
from decoration import Sky, Water, Cloud
from enemy import Enemy
from player import Player
from particles import ParticleEffect

class Level:
    def __init__(self, level_data, surface):
        # general setup
        self.display_surface = surface
        self.world_shift = -0
        self.current_x = None


        # player setup
        player_layout = import_csv_layout(level_data.get('player'))
        self.player = pygame.sprite.GroupSingle()
        self.goal = pygame.sprite.GroupSingle()
        self.player_setup(player_layout)

        # dust
        self.dust_sprite = pygame.sprite.GroupSingle()
        self.player_on_ground = False

        # terrain setup
        terrain_layout = import_csv_layout(level_data.get('terrain'))
        self.terrain_sprites = self.create_tile_group(terrain_layout, 'terrain')

        # grass setup
        grass_layout = import_csv_layout(level_data.get('grass'))
        self.grass_sprites = self.create_tile_group(grass_layout, 'grass')

        # crates
        crate_layout = import_csv_layout(level_data.get('crates'))
        self.crates_sprites = self.create_tile_group(crate_layout, 'crates')

        # coins
        coin_layout = import_csv_layout(level_data.get('coins'))
        self.coins_sprites = self.create_tile_group(coin_layout, 'coins')

        # foreground palmtrees
        fg_palms_layout = import_csv_layout(level_data.get('fg_palms'))
        self.fg_palms_sprites = self.create_tile_group(fg_palms_layout, 'fg_palms')

        # background palms
        bg_palms_layout = import_csv_layout(level_data.get('bg_palms'))
        self.bg_palms_sprites = self.create_tile_group(bg_palms_layout, 'bg_palms')

        # enemy
        enemy_layout = import_csv_layout(level_data.get('enemies'))
        self.enemy_sprites = self.create_tile_group(enemy_layout, 'enemies')

        # constraint
        constraint_layout = import_csv_layout(level_data.get('constraints'))
        self.constraint_sprites = self.create_tile_group(constraint_layout, 'constraints')

        # decoration
        self.sky = Sky(8)
        level_width = len(terrain_layout[0])*tile_size
        self.water = Water(screen_height - 40, level_width)
        self.clouds = Cloud(400, level_width, 25)
        
        pass
    
    
    def create_tile_group(self, layout, type) -> pygame.sprite.Group:
        sprite_group = pygame.sprite.Group()

        for row_index, row in enumerate(layout):
            for col_index, val in enumerate(row):
                if val != '-1':
                    x = col_index * tile_size
                    y = row_index * tile_size

                    if type == 'terrain':
                        terrain_tile_list = import_cut_graphics(r'graphics\terrain\terrain_tiles.png')
                        tile_surface = terrain_tile_list[int(val)]
                        sprite = StaticTile(tile_size, x, y, tile_surface)

                    elif type == 'grass':
                        grass_tile_list = import_cut_graphics(r'graphics\decoration\grass\grass.png')
                        tile_surface = grass_tile_list[int(val)]
                        sprite = StaticTile(tile_size, x, y, tile_surface)
                    
                    elif type == 'crates':
                        sprite = Crate(tile_size, x, y)
                    
                    elif type == 'coins':
                        if val == '0':
                            sprite = Coin(tile_size, x, y, r'graphics\coins\gold')
                        elif val == '1':
                            sprite = Coin(tile_size, x, y, r'graphics\coins\silver')

                    elif type == 'fg_palms':
                        if val == '0':
                            sprite = Palm(tile_size, x, y, r'graphics\terrain\palm_small', 38)
                        if val == '1':
                            sprite = Palm(tile_size, x, y, r'graphics\terrain\palm_large', 64)
                        if val == '2':
                            sprite = Palm(tile_size, x, y, r'graphics\terrain\palm_bg', 64)
                    
                    elif type == 'bg_palms':
                        sprite = Palm(tile_size, x, y, r'graphics\terrain\palm_bg', 64)

                    elif type == 'enemies':
                        sprite = Enemy(tile_size, x, y)

                    elif type == 'constraints':
                        sprite = Tile(tile_size, x, y)

                    
                    sprite_group.add(sprite) # Risky if all 'ifs' fail...

        return sprite_group
    
    
    def create_jump_particles(self, pos):
        if self.player.sprite.facing_right:
            pos -= pygame.math.Vector2(10, 5)
        else:
            pos += pygame.math.Vector2(10, -5)

        jump_particle_sprite = ParticleEffect(pos, 'jump')
        self.dust_sprite.add(jump_particle_sprite)
    
    
    def player_setup(self, layout):
        for row_index, row in enumerate(layout):
            for col_index, val in enumerate(row):
                x = col_index * tile_size
                y = row_index * tile_size
                if val == '0':
                    # player
                    sprite = Player((x,y), self.display_surface, self.create_jump_particles)
                    self.player.add(sprite)
                if val == '1':
                    hat_surface = pygame.image.load(r'graphics\character\hat.png').convert_alpha()
                    sprite = StaticTile(tile_size, x, y, hat_surface)
                    self.goal.add(sprite)
    

    def enemy_collision_reverse(self):
        for enemy in self.enemy_sprites.sprites():
            if pygame.sprite.spritecollide(enemy, self.constraint_sprites, False):
                enemy.reverse()


    def get_player_on_ground(self):
        if self.player.sprite.on_ground:
            self.player_on_ground = True
        else:
            self.player_on_ground = False

    def create_landing_dust(self):
        if not self.player_on_ground and self.player.sprite.on_ground and not self.dust_sprite.sprites():
            if self.player.sprite.facing_right:
                offset = pygame.math.Vector2(10,15)
            else:
                offset = pygame.math.Vector2(-10,15)
            fall_dust_particle = ParticleEffect(self.player.sprite.rect.midbottom - offset, type='land')
            self.dust_sprite.add(fall_dust_particle)


    def scroll_x(self):
        player = self.player.sprite
        player_x = player.rect.centerx
        direction_x = player.direction.x

        if player_x < screen_width//4 and direction_x < 0:
            self.world_shift = 8
            player.speed = 0
        elif player_x > screen_width*3//4 and direction_x > 0:
            self.world_shift = -8
            player.speed = 0
        else:
            self.world_shift = 0
            player.speed = 8


    def run(self):
        # run entire game/level

        # sky
        self.sky.draw(self.display_surface)
        self.clouds.draw(self.display_surface, self.world_shift)

        # bg_palms
        self.bg_palms_sprites.update(self.world_shift)
        self.bg_palms_sprites.draw(self.display_surface)

        # terrain
        self.terrain_sprites.update(self.world_shift)
        self.terrain_sprites.draw(self.display_surface)
        
        # enemy
        self.enemy_sprites.update(self.world_shift)
        self.constraint_sprites.update(self.world_shift)
        self.enemy_collision_reverse()
        self.enemy_sprites.draw(self.display_surface)
        
        # crate
        self.crates_sprites.update(self.world_shift)
        self.crates_sprites.draw(self.display_surface)

        # grass
        self.grass_sprites.update(self.world_shift)
        self.grass_sprites.draw(self.display_surface)

        # coins
        self.coins_sprites.update(self.world_shift)
        self.coins_sprites.draw(self.display_surface)

        # fg_palms
        self.fg_palms_sprites.update(self.world_shift)
        self.fg_palms_sprites.draw(self.display_surface)

        # dust particles
        self.dust_sprite.update(self.world_shift)
        self.dust_sprite.draw(self.display_surface)
        
        # player sprites
        self.player.update()
        self.horizontal_movement_collision()
        
        self.get_player_on_ground()
        self.vertical_movement_collision()
        self.create_landing_dust()
        
        self.scroll_x()
        self.player.draw(self.display_surface)
        self.goal.update(self.world_shift)
        self.goal.draw(self.display_surface)

        # water
        self.water.draw(self.display_surface, self.world_shift)
        

        
        pass


    def horizontal_movement_collision(self):
        player = self.player.sprite
        # player = Player() # for dev
        player.rect.x += player.direction.x * player.speed
        collidable_sprites = self.terrain_sprites.sprites() + self.crates_sprites.sprites() + self.fg_palms_sprites.sprites()
        for sprite in collidable_sprites:
            if sprite.rect.colliderect(player.rect):
                if player.direction.x > 0:
                    player.rect.right = sprite.rect.left
                    player.on_right = True
                    self.current_x = player.rect.right
                elif player.direction.x < 0:
                    player.rect.left = sprite.rect.right
                    player.on_left = True
                    self.current_x = player.rect.left
        

        if player.on_left and (player.rect.left< self.current_x or player.direction.x >=0):
            player.on_left = False
        
        if player.on_right and (player.rect.right> self.current_x or player.direction.x <=0):
            player.on_right = False


    def vertical_movement_collision(self):
        player = self.player.sprite
        # player = Player() # for dev
        player.apply_gravity()
        # player.rect.y += player.direction.x * player.speed
        collidable_sprites = self.terrain_sprites.sprites() + self.crates_sprites.sprites() + self.fg_palms_sprites.sprites()
        for sprite in collidable_sprites:
            if sprite.rect.colliderect(player.rect):
                if player.direction.y > 0:
                    player.rect.bottom = sprite.rect.top
                    player.direction.y = 0
                    player.on_ground = True
                elif player.direction.y < 0:
                    player.rect.top = sprite.rect.bottom
                    player.direction.y = 0
                    player.on_ceiling = True
        
        if player.on_ground and (player.direction.y < 0 or player.direction.y > 1):
            player.on_ground = False
        if player.on_ceiling and player.direction.y > 1: 
            player.on_ceiling = False

