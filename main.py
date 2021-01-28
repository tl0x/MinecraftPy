from ursina import *
import PerlinNoise
import random
from perlin_noise import PerlinNoise

def GenerateHeightMap(seed,size):
    noise1 = PerlinNoise(octaves=8,seed=seed)
    noise2 = PerlinNoise(octaves=8,seed=seed)
    noise3 = PerlinNoise(octaves=6,seed=seed)
    Heights = []
    WaterLevel = -32

    for x in range(size):
        row = []
        for z in range(size):
            heightResult = 0
            heightLow = (noise1([x * 1.3, z * 1 / 3])*3) - 4
            heightHigh = (noise2([x * 1.3, z * 1 / 3])*12) + 6
            if noise3([x, z]) / 8 > 0:
                heightResult = heightLow
            else:
                heightResult = heightHigh
            heightResult /= 2
            if heightResult < 0:
                heightResult *= 0.8
            row.append(round(heightResult))
        Heights.append(row)
    return Heights

class FirstPersonController(Entity):
    def __init__(self, **kwargs):
        super().__init__()
        self.speed = 5
        self.origin_y = -.5
        self.camera_pivot = Entity(parent=self, y=2)
        self.cursor = Entity(parent=camera.ui, model='quad', color=color.pink, scale=.008, rotation_z=45)

        camera.parent = self.camera_pivot
        camera.position = (0, 0, 0)
        camera.rotation = (0, 0, 0)
        camera.fov = 90
        mouse.locked = True
        self.mouse_sensitivity = Vec2(40, 40)

        self.gravity = 1
        self.grounded = False
        self.jump_height = 2
        self.jump_duration = .5
        self.jumping = False
        self.air_time = 0

        for key, value in kwargs.items():
            setattr(self, key, value)

    def update(self):
        self.rotation_y += mouse.velocity[0] * self.mouse_sensitivity[1]

        self.camera_pivot.rotation_x -= mouse.velocity[1] * self.mouse_sensitivity[0]
        self.camera_pivot.rotation_x = clamp(self.camera_pivot.rotation_x, -90, 90)

        self.direction = Vec3(
            self.forward * (held_keys['w'] - held_keys['s'])
            + self.right * (held_keys['d'] - held_keys['a'])
        ).normalized()

        origin = self.world_position + (self.up * .5)
        hit_info = raycast(origin, self.direction, ignore=(self,), distance=.5, debug=False)
        if not hit_info.hit:
            self.position += self.direction * self.speed * time.dt

        if self.gravity:
            # # gravity
            ray = raycast(self.world_position + (0, 2, 0), self.down, ignore=(self,))
            # ray = boxcast(self.world_position+(0,2,0), self.down, ignore=(self,))

            if ray.distance <= 2.1:
                if not self.grounded:
                    self.land()
                self.grounded = True
                # make sure it's not a wall and that the point is not too far up
                if ray.world_normal.y > .7 and ray.world_point.y - self.world_y < .5:  # walk up slope
                    self.y = ray.world_point[1]
                return
            else:
                self.grounded = False

            # if not on ground and not on way up in jump, fall
            self.y -= min(self.air_time, ray.distance - .05)
            self.air_time += time.dt * .25 * self.gravity

    def input(self, key):
        if key == 'space':
            self.jump()

    def jump(self):
        if not self.grounded:
            return

        self.grounded = False
        self.animate_y(self.y + self.jump_height, self.jump_duration, resolution=120, curve=curve.out_expo)
        invoke(self.start_fall, delay=self.jump_duration)

    def start_fall(self):
        self.y_animator.pause()
        self.jumping = False

    def land(self):
        # print('land')
        self.air_time = 0
        self.grounded = True


app = Ursina()
grass_texture = load_texture('assets/grassblock.png')
stone_texture = load_texture('assets/stone_block.png')
brick_texture = load_texture('assets/brick_block.png')
dirt_texture = load_texture('assets/dirt_block.png')
sky_texture = load_texture('assets/skybox.png')
arm_texture = load_texture('assets/arm_texture.png')
punch_sound = Audio('assets/punch_sound', loop=False, autoplay=False)
block_pick = 1

window.fps_counter.enabled = True
window.exit_button.visible = False


def update():
    global block_pick
    if held_keys['escape']:
        exit()

    if held_keys['left mouse'] or held_keys['right mouse']:
        hand.active()
    else:
        hand.passive()

    if held_keys['1']: block_pick = 1
    if held_keys['2']: block_pick = 2
    if held_keys['3']: block_pick = 3
    if held_keys['4']: block_pick = 4


class Voxel(Button):
    def __init__(self, position=(0, 0, 0), texture=grass_texture):
        super().__init__(
            parent=scene,
            position=position,
            model='assets/block',
            origin_y=0.5,
            texture=texture,
            color=color.color(0, 0, random.uniform(0.9, 1)),
            scale=0.5)

    def input(self, key):
        if self.hovered:
            if key == 'left mouse down':
                punch_sound.play()
                destroy(self)
            if key == 'right mouse down':

                punch_sound.play()
                if block_pick == 1: voxel = Voxel(position=self.position + mouse.normal, texture=grass_texture)
                if block_pick == 2: voxel = Voxel(position=self.position + mouse.normal, texture=stone_texture)
                if block_pick == 3: voxel = Voxel(position=self.position + mouse.normal, texture=brick_texture)
                if block_pick == 4: voxel = Voxel(position=self.position + mouse.normal, texture=dirt_texture)


class Sky(Entity):
    def __init__(self):
        super().__init__(
            parent=scene,
            model='sphere',
            texture=sky_texture,
            scale=150,
            double_sided=True)


class Hand(Entity):
    def __init__(self):
        super().__init__(
            parent=camera.ui,
            model='assets/arm',
            texture=arm_texture,
            scale=0.2,
            rotation=Vec3(150, -10, 0),
            position=Vec2(0.4, -0.6))

    def active(self):
        self.position = Vec2(0.3, -0.5)

    def passive(self):
        self.position = Vec2(0.4, -0.6)


test = GenerateHeightMap(random.randint(1,10000),16)

for x in range(16):
    for z in range(16):
        voxel = Voxel(position=(x, test[x][z] - 7, z), texture=grass_texture)
        voxel = Voxel(position=(x, test[x][z] - 8, z), texture=dirt_texture)
        voxel = Voxel(position=(x, test[x][z] - 9, z), texture=dirt_texture)
        voxel = Voxel(position=(x, test[x][z] - 10, z), texture=dirt_texture)
        voxel = Voxel(position=(x, test[x][z] - 10, z), texture=dirt_texture)
        voxel = Voxel(position=(x, test[x][z] - 11, z), texture=stone_texture)
        voxel = Voxel(position=(x, test[x][z] - 12, z), texture=stone_texture)
        voxel = Voxel(position=(x, test[x][z] - 13, z), texture=stone_texture)

player = FirstPersonController()
sky = Sky()
hand = Hand()

app.run()
