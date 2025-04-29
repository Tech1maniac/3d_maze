import math

import components_3d as com
import esper
import glm
import pygame
import pygame.locals
import resources as res

# Constants
MAX_PITCH = (math.pi - 0.2) / 2.0


def add_systems_1_to_world(world: esper.World) -> None:
    world.add_processor(GameControlSystem())


def add_systems_2_to_world(world: esper.World) -> None:
    world.add_processor(ThirdPersonCameraSystem())
    world.add_processor(FreeCamOrientation())


def clamp(value: float, m_min: float, m_max: float) -> float:
    """Clamp `value` between `m_min` and `m_max`."""
    return max(m_min, min(m_max, value))


class GameControlSystem(esper.Processor):
    def process(self) -> None:
        """Handle all control inputs and dispatch to movement/camera systems each frame."""
        # Read keyboard state once per frame
        keys = pygame.key.get_pressed()
        controls: res.GameControlState = self.world.controls

        # Camera swap
        if keys[controls.key_swap_camera] and not controls.key_swap_camera_state and controls.allow_camera_swap:
            self.world._swap_camera()
        # Reset to home
        if keys[controls.key_return_to_home] and not controls.key_return_to_home_state:
            self.world.home_entities()

        # Update previous key states
        controls.key_swap_camera_state = keys[controls.key_swap_camera]
        controls.key_return_to_home_state = keys[controls.key_return_to_home]

        # Route to appropriate control mode
        self._acknowledge_input(keys)

    def _acknowledge_input(self, keys) -> None:
        controls: res.GameControlState = self.world.controls
        if controls.control_mode == res.GameControlState.PLAYER_MODE:
            self._wasd_movement(
                self.world.player_object,
                controls.player_speed,
                vertical_movement=False,
                vertical_speed=0.0,
                keys=keys
            )
            self._arrow_key_rotation(
                entity_id=self.world.player_object,
                enable_pitch=False,
                keys=keys
            )
            self._mouse_control(
                entity_id=self.world.player_object,
                enable_pitch=False
            )
        else:
            self._wasd_movement(
                self.world.free_cam,
                controls.free_camera_speed,
                vertical_movement=True,
                vertical_speed=controls.free_camera_vertical_speed,
                keys=keys
            )
            self._arrow_key_rotation(
                entity_id=self.world.free_cam,
                keys=keys
            )
            self._mouse_control(
                entity_id=self.world.free_cam
            )

    def _wasd_movement(
        self,
        entity_id: int,
        speed: float,
        vertical_movement: bool,
        vertical_speed: float,
        keys
    ) -> None:
        """Move entity with WASD (and optional vertical movement)."""
        velocity = self.world.component_for_entity(entity_id, com.Velocity)
        direction = glm.vec3()

        if keys[pygame.locals.K_w]: direction.y += 1
        if keys[pygame.locals.K_s]: direction.y -= 1
        if keys[pygame.locals.K_a]: direction.x += 1
        if keys[pygame.locals.K_d]: direction.x -= 1

        if glm.length(direction) > 0.001:
            norm = glm.normalize(direction) * speed
            velocity.value.x, velocity.value.y = norm.x, norm.y
        else:
            velocity.value.x = velocity.value.y = 0.0

        if vertical_movement:
            velocity.value.z = 0.0
            if keys[pygame.locals.K_SPACE]: velocity.value.z += vertical_speed
            if keys[pygame.locals.K_LSHIFT]: velocity.value.z -= vertical_speed

        # Debug print
        if keys[pygame.locals.K_p]:
            tra = self.world.component_for_entity(entity_id, com.Transformation)
            print(f"Transformation(Position: {tra.position}, Rotation: {tra.rotation})")

    def _mouse_control(self, entity_id: int, enable_pitch: bool = True) -> None:
        """Rotate entity based on mouse movement when left button is held."""
        controls: res.GameControlState = self.world.controls
        # Request 5-button tuple, but we only need the left button
        buttons = pygame.mouse.get_pressed(5)
        is_pressed = buttons[0]

        # Get relative movement since last frame
        rel_x, rel_y = pygame.mouse.get_rel()

        if is_pressed:
            tra = self.world.component_for_entity(entity_id, com.Transformation)
            # Horizontal (yaw)
            tra.rotation.x += rel_x * controls.mouse_sensitivity

            # Vertical (pitch)
            if enable_pitch:
                change = -rel_y * controls.mouse_sensitivity
                tra.rotation.y = clamp(
                    tra.rotation.y + change,
                    -MAX_PITCH,
                    MAX_PITCH
                )

    def _arrow_key_rotation(
        self,
        entity_id: int,
        enable_pitch: bool = True,
        keys=None
    ) -> None:
        """Rotate entity using arrow keys."""
        if keys is None:
            keys = pygame.key.get_pressed()
        tra = self.world.component_for_entity(entity_id, com.Transformation)

        if enable_pitch:
            pitch_delta = 0.0
            if keys[pygame.locals.K_UP]: pitch_delta += 0.1
            if keys[pygame.locals.K_DOWN]: pitch_delta -= 0.1
            tra.rotation.y = clamp(tra.rotation.y + pitch_delta, -MAX_PITCH, MAX_PITCH)

        if keys[pygame.locals.K_LEFT]: tra.rotation.x += 0.1
        if keys[pygame.locals.K_RIGHT]: tra.rotation.x -= 0.1

    def _player_jump(self) -> None:
        """Apply jump impulse if player is colliding with ground."""
        col = self.world.component_for_entity(self.world.player_object, com.CollisionComponent)
        if col.is_colliding_z and pygame.key.get_pressed()[pygame.locals.K_SPACE]:
            v = self.world.component_for_entity(self.world.player_object, com.Velocity)
            v.value.z += self.world.controls.player_jump_height

    def _change_light(self, entity_id: int) -> None:
        """Adjust light color and attenuation with keys T/G, Z/H, U/J, I/K, O/L, P/; respectively."""
        keys = pygame.key.get_pressed()
        light: com.Light = self.world.component_for_entity(entity_id, com.Light)

        # Color adjustments
        if keys[pygame.locals.K_t]: light.color.x += 0.01
        if keys[pygame.locals.K_g]: light.color.x -= 0.01  # red
        if keys[pygame.locals.K_z]: light.color.y += 0.01
        if keys[pygame.locals.K_h]: light.color.y -= 0.01  # green
        if keys[pygame.locals.K_u]: light.color.z += 0.01
        if keys[pygame.locals.K_j]: light.color.z -= 0.01  # blue

        # Attenuation adjustments
        if keys[pygame.locals.K_i]: light.attenuation.x += 0.01
        if keys[pygame.locals.K_k]: light.attenuation.x -= 0.01
        if keys[pygame.locals.K_o]: light.attenuation.y += 0.01
        if keys[pygame.locals.K_l]: light.attenuation.y -= 0.01
        if keys[pygame.locals.K_p]: light.attenuation.z += 0.01
        # semicolon key for decrement
        if keys[pygame.locals.K_SEMICOLON]: light.attenuation.z -= 0.01

        if keys[pygame.locals.K_p]:
            print(f"Light(color: {light.color}, attenuation: {light.attenuation})")


class ThirdPersonCameraSystem(esper.Processor):
    def process(self) -> None:
        """Position the third-person camera based on target's transform."""
        for ent, (tra, ori, cam) in self.world.get_components(
            com.Transformation, com.CameraOrientation, com.ThirdPersonCamera
        ):
            target_tra = self.world.component_for_entity(cam.target, com.Transformation)
            ori.look_at = target_tra.position

            yaw = target_tra.rotation.x
            pitch = cam.pitch
            height = math.sin(pitch)
            dir_vec = glm.vec3(
                math.cos(yaw) * (1.0 - abs(height)),
                math.sin(yaw) * (1.0 - abs(height)),
                height
            )
            tra.position = target_tra.position - (dir_vec * cam.distance)


class FreeCamOrientation(esper.Processor):
    def process(self) -> None:
        """Orient the free camera based on its transform."""
        for ent, (tra, ori, _) in self.world.get_components(
            com.Transformation, com.CameraOrientation, com.FreeCamera
        ):
            height = math.sin(tra.rotation.y)
            ori.look_at = tra.position + glm.vec3(
                math.cos(tra.rotation.x) * (1.0 - abs(height)),
                math.sin(tra.rotation.x) * (1.0 - abs(height)),
                height
            )
