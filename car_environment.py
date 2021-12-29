import glob
import os
import sys

try:
    sys.path.append(glob.glob('Carla/carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass

import carla
import random
import math
import time

class CarEnvironment:

    def __init__(self):
        self.client = carla.Client('localhost', 2000)
        self.client.set_timeout(2.0)
        self.world = self.client.get_world()

        self.blueprint_library = self.world.get_blueprint_library()
        self.car = self.blueprint_library.filter('model3')[0]

        self.collisions = []
        self.actors = []
        self.front_camera = None
        self.SECONDS_PER_EPISODE = 30

        self.IMG_WIDTH = 640
        self.IMG_HEIGHT = 480

    def process_img(self, image):
        self.front_camera = image

    def collision_data(self, event):
        self.collisions.append(event)

    def reset(self):
        self.transform = random.choice(self.world.get_map().get_spawn_points())
        self.vehicle = self.world.spawn_actor(self.tesla_model3, self.transform)
        self.actor_list.append(self.vehicle)

        self.rgb_camera = self.blueprint_library.find('sensor.camera.rgb')
        self.rgb_camera.set_attribute('image_size_x', f'{self.IMG_WIDTH}')
        self.rgb_camera.set_attribute('image_size_y', f'{self.IMG_HEIGHT}')

        transform = carla.Transform(carla.Location(x=2, z=3))
        self.sensor = self.world.spawn_actor(self.rgb_camera, transform, attach_to=self.vehicle)
        self.actor_list.append(self.sensor)
        self.sensor.listen(lambda data: self.process_img(data))
        self.vehicle.apply_control(carla.VehicleControl(throttle=0.0, brake=0.0))

        collision_sensor = self.world.get_blueprint_library().find('sensor.other.collision')
        self.collision_sensor = self.world.spawn_actor(collision_sensor, transform, attach_to=self.vehicle)
        self.actor_list.append(self.collision_sensor)
        self.collision_sensor.listen(lambda event: self.collision_data(event))

        return self.front_camera

    def step(self, action):
        if action == 0:
            self.vehicle.apply_control(carla.VehicleControl(throttle=1.0, steer=-1.0))
        elif action == 1:
            self.vehicle.apply_control(carla.VehicleControl(throttle=1.0, steer=0.0))
        elif action == 2:
            self.vehicle.apply_control(carla.VehicleControl(throttle=1.0, steer=1.0))

        v = self.vehicle.get_velocity()

        kmh = int(3.6 * math.sqrt(v.x ** 2 + v.y ** 2 + v.z ** 2))

        if len(self.collision_hist) != 0:
            done = True
            reward = -100
        elif kmh < 50:
            done = False
            reward = -1
        else:
            done = False
            reward = 1

        if self.episode_start + self.SECONDS_PER_EPISODE < time.time():
            done = True

        return self.front_camera, reward, done, None
