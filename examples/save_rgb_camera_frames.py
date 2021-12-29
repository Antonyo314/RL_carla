import glob
import os
import sys

try:
    sys.path.append(glob.glob('../Carla/carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass

import carla

import random
import time


def collect_images(image, images):
    images.append(image)


def main():
    actor_list = []

    try:

        client = carla.Client('localhost', 2000)
        client.set_timeout(2.0)

        world = client.get_world()

        blueprint_library = world.get_blueprint_library()

        bp = random.choice(blueprint_library.filter('vehicle'))

        if bp.has_attribute('color'):
            color = random.choice(bp.get_attribute('color').recommended_values)
            bp.set_attribute('color', color)

        transform = random.choice(world.get_map().get_spawn_points())

        vehicle = world.spawn_actor(bp, transform)

        actor_list.append(vehicle)
        print('created %s' % vehicle.type_id)

        vehicle.set_autopilot(True)

        camera_bp = blueprint_library.find('sensor.camera.rgb')
        camera_bp.set_attribute('image_size_x', f'{2 * 640}')
        camera_bp.set_attribute('image_size_y', f'{2 * 480}')

        camera_transform = carla.Transform(carla.Location(x=2, z=3))
        camera = world.spawn_actor(camera_bp, camera_transform, attach_to=vehicle)
        actor_list.append(camera)
        print('created %s' % camera.type_id)

        images = []
        camera.listen(lambda image: collect_images(image, images))

        transform.location += carla.Location(x=0, y=-3.2)
        transform.rotation.yaw = -180.0
        for _ in range(0, 10):
            transform.location.x += 8.0

            bp = random.choice(blueprint_library.filter('vehicle'))

            npc = world.try_spawn_actor(bp, transform)
            if npc is not None:
                actor_list.append(npc)
                npc.set_autopilot()
                print('created %s' % npc.type_id)

        time.sleep(10)

    finally:
        print('destroying actors')
        camera.destroy()
        client.apply_batch([carla.command.DestroyActor(x) for x in actor_list])
        print('done.')

        print('saving images')
        for image in images:
            image.save_to_disk(f'_out/{image.frame}.png')


if __name__ == '__main__':
    main()
