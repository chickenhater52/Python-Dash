# --- physics.py ---
import math

try:
    from all_objects import ALL_OBJECTS
except ImportError:
    ALL_OBJECTS = {}

class PlayerState:
    def __init__(self):
        self.reset()
        
    def reset(self):
        self.x = 0.0
        self.y = 30.0
        self.last_y = 30.0
        self.last_y_frame = 30.0
        self.y_velocity = 0.0
        self.on_ground = True
        self.on_ceiling = False
        self.can_jump = True
        self.is_jumping = False
        self.gravity_flipped = False
        self.is_dead = False
        self.rotation = 0.0
        self.up_key_down = False
        self.up_key_pressed = False
        self.is_mini = False
        self.game_mode = 0  # 0=Cube, 1=Ship, 2=Ball, 3=UFO, 4=Wave, 6=Spider
        self.was_boosted = False
        self.pending_velocity = None
        self.is_dashing = False
        self.dash_y_velocity = 0.0
        
        # Phaser discrete rotation variables 1:1
        self.rotate_action_active = False
        self.rotate_action_time = 0.0
        self.rotate_action_duration = 0.0
        self.rotate_action_start = 0.0
        self.rotate_action_total = 0.0

def precompute_objects(objects):
    """
    Caches all geometric properties and database definitions on the object dictionaries
    upon level initialization to avoid lookups in the 240Hz physics loop.
    """
    for obj in objects:
        obj_id = obj['id']
        obj_def = ALL_OBJECTS.get(str(obj_id))
        if not obj_def:
            obj['obj_def'] = None
            continue
            
        obj['obj_def'] = obj_def
        obj_type = obj_def.get("type")
        obj_scale = obj.get('scale', 1.0)
        
        if obj_type == "solid":
            grid_w = obj_def.get("gridW", 1.0)
            grid_h = obj_def.get("gridH", 1.0)
            w = grid_w * 60.0 * obj_scale
            h = grid_h * 60.0 * obj_scale
        elif obj_type == "hazard":
            sprite_w = obj_def.get("spriteW")
            sprite_h = obj_def.get("spriteH")
            scale_x = obj_def.get("hitboxScaleX")
            scale_y = obj_def.get("hitboxScaleY")
            
            if sprite_w is not None and scale_x is not None:
                w = sprite_w * scale_x * 2.0 * obj_scale
                h = sprite_h * scale_y * 2.0 * obj_scale
            else:
                grid_w = obj_def.get("gridW", 1.0)
                grid_h = obj_def.get("gridH", 1.0)
                w = grid_w * 12.0 * obj_scale
                h = grid_h * 24.0 * obj_scale
        elif obj_type == "pad":
            grid_w = obj_def.get("gridW", 1.0)
            grid_h = obj_def.get("gridH", 1.0)
            w = grid_w * 60.0 * obj_scale
            h = grid_h * 60.0 * obj_scale
        else:
            w = 60.0 * obj_scale
            h = 60.0 * obj_scale
            
        obj['w'] = w
        obj['h'] = h
        obj['half_w'] = w / 2.0
        obj['half_h'] = h / 2.0
        
        # Cache rotated bounding limits (rotated AABB)
        rad = math.radians(obj.get('rot', 0.0))
        cos_val = abs(math.cos(rad))
        sin_val = abs(math.sin(rad))
        obj['rotated_half_width'] = obj['half_w'] * cos_val + obj['half_h'] * sin_val
        obj['rotated_half_height'] = obj['half_w'] * sin_val + obj['half_h'] * cos_val

def quantize_delta(dt_ms, speed_hack=1.0):
    TIMESTEP = 1.0 / 240.0
    val = (dt_ms * speed_hack) / 1000.0
    substeps = int(round(val / TIMESTEP))
    substeps = max(0, min(substeps, 60))
    # Exactly matches Phaser quantizedDelta calculation
    quantized_delta = substeps * TIMESTEP * 60.0
    return substeps, quantized_delta

def flip_mod(state):
    return -1.0 if state.gravity_flipped else 1.0

def player_is_falling(state, p=1.916398):
    if state.gravity_flipped:
        return state.y_velocity > p
    else:
        return state.y_velocity < -p

def is_falling_past_threshold(state):
    if state.gravity_flipped:
        return state.y_velocity > 0.25
    else:
        return state.y_velocity < -0.25

def run_rotate_action(state, d=0.9):
    state.rotate_action_active = True
    state.rotate_action_time = 0.0
    mini_dur_scale = 1.0 / 1.4 if state.is_mini else 1.0
    state.rotate_action_duration = (0.39 / d) * mini_dur_scale
    state.rotate_action_start = state.rotation
    state.rotate_action_total = math.pi * flip_mod(state)

def update_rotate_action(state, dt_sec):
    if not state.rotate_action_active:
        return
    state.rotate_action_time += dt_sec
    if state.rotate_action_time >= state.rotate_action_duration:
        state.rotate_action_active = False
    t = min(state.rotate_action_time / state.rotate_action_duration, 1.0)
    state.rotation = state.rotate_action_start + state.rotate_action_total * t

def slerp_2d(start_angle, end_angle, t):
    half_start = start_angle * 0.5
    half_end = end_angle * 0.5
    cos_start = math.cos(half_start)
    sin_start = math.sin(half_start)
    cos_end = math.cos(half_end)
    sin_end = math.sin(half_end)
    
    dot = (cos_start * cos_end) + (sin_start * sin_end)
    if dot < 0.0:
        dot = -dot
        sin_end = -sin_end
        cos_end = -cos_end
        
    if 1.0 - dot > 0.0001:
        clamped_dot = max(-1.0, min(1.0, dot))
        theta = math.acos(clamped_dot)
        sin_theta = math.sin(theta)
        weight_start = math.sin(theta * (1.0 - t)) / sin_theta
        weight_end = math.sin(theta * t) / sin_theta
    else:
        weight_start = 1.0 - t
        weight_end = t
        
    interp_sin = (sin_start * weight_start) + (sin_end * weight_end)
    interp_cos = (cos_start * weight_start) + (cos_end * weight_end)
    out = math.atan2(interp_sin, interp_cos)
    return out + out

def convert_to_closest_rotation(rotation):
    half_pi = math.pi / 2.0
    return round(rotation / half_pi) * half_pi

def update_ground_rotation(state, vertical_delta):
    if state.game_mode in (2, 4, 6):  # Ball, Wave, Spider
        return
    target_rot = convert_to_closest_rotation(state.rotation)
    t = 0.4725 * vertical_delta
    state.rotation = slerp_2d(state.rotation, target_rot, t)

def apply_mode_physics(state, dt_sec, speed, solids=None, p=1.916398, d=0.9, floor_y=0.0, ceil_y=600.0):
    if state.pending_velocity is not None:
        state.y_velocity = state.pending_velocity
        state.pending_velocity = None
        
    if state.is_dashing:
        if not state.up_key_down or state.on_ground:
            state.is_dashing = False
            state.dash_y_velocity = 0.0
        else:
            state.y_velocity = state.dash_y_velocity
            rot_speed = math.pi * 6.0 * flip_mod(state)
            state.rotation += rot_speed * dt_sec
            return

    # 1. Ship Mode (isFlying)
    if state.game_mode == 1:
        _ship_mini_scale = 1.176470588 if state.is_mini else 1.0
        _0x203040 = 0.8
        if state.up_key_down:
            _0x203040 = -1.0
        if not state.up_key_down and not player_is_falling(state, p):
            _0x203040 = 1.2
        _0x2d237f = 0.4
        if state.up_key_down and player_is_falling(state, p):
            _0x2d237f = 0.5
            
        state.y_velocity -= p * dt_sec * flip_mod(state) * _0x203040 * _0x2d237f * _ship_mini_scale
        if state.up_key_down:
            state.on_ground = False
            
        if not state.was_boosted:
            if state.gravity_flipped:
                state.y_velocity = max(-16.0 * _ship_mini_scale, min(12.8 * _ship_mini_scale, state.y_velocity))
            else:
                state.y_velocity = max(-12.8 * _ship_mini_scale, min(16.0 * _ship_mini_scale, state.y_velocity))

    # 2. Wave Mode
    elif state.game_mode == 4:
        _base_speed = 22.7720072 if state.is_mini else 11.3860036
        _speed_mod = (speed / 11.540004)
        _wave_vel = _base_speed * _speed_mod
        is_pushing_up = state.up_key_down
        _wave_y_vel = (1.0 if is_pushing_up else -1.0) * flip_mod(state) * _wave_vel

        if state.on_ground or state.on_ceiling:
            moving_away_from_ceiling = state.on_ceiling and not is_pushing_up
            moving_away_from_floor = state.on_ground and is_pushing_up
            if moving_away_from_ceiling or moving_away_from_floor:
                state.on_ground = False
                state.on_ceiling = False
            else:
                _wave_y_vel = 0.0

        state.y_velocity = _wave_y_vel
        state.can_jump = False
        state.is_jumping = False
        
        _wave_angle = math.atan(0.5) if state.is_mini else math.pi / 4.0
        state.rotation = 0.0 if _wave_y_vel == 0.0 else (-_wave_angle if _wave_y_vel > 0.0 else _wave_angle)

    # 3. Ball Mode
    elif state.game_mode == 2:
        _ball_gravity = p * 0.6
        if state.up_key_pressed and state.can_jump:
            state.up_key_pressed = False
            state.y_velocity = flip_mod(state) * 22.360064 * (0.8 if state.is_mini else 1.0)
            state.gravity_flipped = not state.gravity_flipped
            state.on_ground = False
            state.can_jump = False
            state.y_velocity *= 0.6
        else:
            if player_is_falling(state, p):
                state.can_jump = False
            state.y_velocity -= _ball_gravity * dt_sec * flip_mod(state)
            if state.gravity_flipped:
                state.y_velocity = min(state.y_velocity, 30.0)
            else:
                state.y_velocity = max(state.y_velocity, -30.0)
                
            if player_is_falling(state, p):
                if (state.y_velocity > p * 2.0 if state.gravity_flipped else state.y_velocity < -(p * 2.0)):
                    state.on_ground = False
                    
        # Ball roll rotation (Using horizontal_delta of 0.225 * speed)
        ball_on_surface = state.on_ground or state.on_ceiling
        roll_dir = -1.0 if state.gravity_flipped else 1.0
        speed_factor = 0.5 if ball_on_surface else 0.35
        mini_roll_scale = 1.25 if state.is_mini else 1.0
        horizontal_delta = dt_sec / 0.9 * speed * 0.9
        state.rotation += horizontal_delta / 30.0 * roll_dir * speed_factor * mini_roll_scale

    # 4. UFO Mode
    elif state.game_mode == 3:
        _ufo_jump = 13.296 if state.is_mini else 13.742
        _ufo_threshold = 3.832796
        _ufo_fast_grav = p * (0.634524 if state.is_mini else 0.540121)
        _ufo_slow_grav = p * (0.421624 if state.is_mini else 0.359973)
        _ufo_up_vel = state.y_velocity * flip_mod(state)
        _ufo_grav = _ufo_fast_grav if _ufo_up_vel > _ufo_threshold else _ufo_slow_grav
        
        state.y_velocity -= _ufo_grav * dt_sec * flip_mod(state)
        
        if state.up_key_pressed:
            state.up_key_pressed = False
            state.y_velocity = _ufo_jump * flip_mod(state)
            state.on_ground = False
            state.can_jump = False
            state.is_jumping = True

    # 5. Spider Mode
    elif state.game_mode == 6:
        _player_size = 18.0 if state.is_mini else 30.0
        _mini_grav = 1.4 if state.is_mini else 1.0
        _grav_amt = p * 0.6 * _mini_grav
        
        if state.up_key_pressed and state.can_jump:
            state.up_key_pressed = False
            
            nearest_surface_y = float('inf')
            if not state.gravity_flipped:
                nearest_surface_y = ceil_y if ceil_y is not None else float('inf')
                if solids:
                    for obj in solids:
                        obj_def = obj.get('obj_def')
                        if not obj_def or obj_def.get("type") != "solid":
                            continue
                        h = obj['h']
                        unrotated_b = obj['y'] - h / 2.0
                        if unrotated_b > state.y and unrotated_b < nearest_surface_y:
                            nearest_surface_y = unrotated_b
                
                if math.isfinite(nearest_surface_y):
                    state.y = nearest_surface_y - _player_size
                    state.gravity_flipped = True
                    state.y_velocity = 0.0
                else:
                    state.y_velocity = speed
            else:
                nearest_surface_y = floor_y
                if solids:
                    for obj in solids:
                        obj_def = obj.get('obj_def')
                        if not obj_def or obj_def.get("type") != "solid":
                            continue
                        h = obj['h']
                        unrotated_t = obj['y'] + h / 2.0
                        if unrotated_t < state.y and unrotated_t > nearest_surface_y:
                            nearest_surface_y = unrotated_t
                
                if math.isfinite(nearest_surface_y):
                    state.y = nearest_surface_y + _player_size
                    state.gravity_flipped = False
                    state.y_velocity = 0.0
                else:
                    state.y_velocity = -speed
                    
            state.on_ground = False
            state.can_jump = False
            state.is_jumping = False
            run_rotate_action(state, d)
            return
            
        if player_is_falling(state, p):
            state.can_jump = False
            
        state.y_velocity -= _grav_amt * dt_sec * flip_mod(state)
        if state.gravity_flipped:
            state.y_velocity = min(state.y_velocity, 30.0)
        else:
            state.y_velocity = max(state.y_velocity, -30.0)
            
        if player_is_falling(state, p):
            _past_threshold = state.y_velocity > p * 2.0 if state.gravity_flipped else state.y_velocity < -(p * 2.0)
            if _past_threshold:
                state.on_ground = False

    # 6. Standard Cube Mode (game_mode = 0)
    else:
         if state.up_key_down and state.can_jump:
              state.is_jumping = True
              state.on_ground = False
              state.can_jump = False
              state.up_key_pressed = False
              state.y_velocity = flip_mod(state) * 22.360064 * (0.8 if state.is_mini else 1.0)
              run_rotate_action(state, d)
         elif state.is_jumping:
              state.y_velocity -= p * dt_sec * flip_mod(state)
              if player_is_falling(state, p):
                  state.is_jumping = False
                  state.on_ground = False
         else:
              if player_is_falling(state, p):
                  state.can_jump = False
              state.y_velocity -= p * dt_sec * flip_mod(state)
              if state.gravity_flipped:
                  state.y_velocity = min(state.y_velocity, 30.0)
              else:
                  state.y_velocity = max(state.y_velocity, -30.0)
                  
              if is_falling_past_threshold(state) and not state.rotate_action_active:
                  run_rotate_action(state, d)
                  
              if player_is_falling(state, p):
                  _past_threshold = state.y_velocity > p * 2.0 if state.gravity_flipped else state.y_velocity < -(p * 2.0)
                  if _past_threshold:
                      state.on_ground = False
                      
         # Apply Phaser slerp / rotateAction updates using correct frame-based vertical delta
         if state.on_ground:
             update_ground_rotation(state, dt_sec)
         elif state.rotate_action_active:
             update_rotate_action(state, 1.0 / 240.0)

def resolve_collisions(state, objects, floor_y=0.0, ceil_y=600.0, player_size=30.0):
    effective_size = 6.0 if state.game_mode == 4 else (18.0 if state.is_mini else player_size)
    gamemode_addition = 12.0 if state.game_mode in (1, 4, 3) else 20.0  
    tight_box = 9.0
    
    # 1. Floor & Ceiling boundaries (Floor baseline set to 0.0)
    if state.y <= floor_y + effective_size:
        state.y = floor_y + effective_size
        state.y_velocity = 0.0
        state.on_ground = True
        state.can_jump = True
        state.rotate_action_active = False
        if state.gravity_flipped:
            state.on_ceiling = True
            
    if ceil_y is not None and state.y >= ceil_y - effective_size:
        state.y = ceil_y - effective_size
        state.y_velocity = 0.0
        state.on_ground = True
        state.can_jump = True
        state.rotate_action_active = False
        state.on_ceiling = True

    # 2. Block/Solid Collisions
    for obj in objects:
        obj_def = obj.get('obj_def')
        if not obj_def:
            continue
            
        obj_type = obj_def.get("type")
        if obj_type not in ("solid", "hazard", "pad", "slope"):
            continue

        # Extract optimized cached measurements
        w = obj['w']
        h = obj['h']
        half_w = obj['half_w']
        half_h = obj['half_h']
        rotated_half_width = obj['rotated_half_width']
        rotated_half_height = obj['rotated_half_height']

        unrotated_l = obj['x'] - half_w
        unrotated_r = obj['x'] + half_w
        unrotated_t = obj['y'] + half_h # top of block (higher Y)
        unrotated_b = obj['y'] - half_h # bottom of block (lower Y)

        # Broadphase optimization check (exact playerSize vs waveHitSize)
        broad_size = 6.0 if state.game_mode == 4 else (18.0 if state.is_mini else player_size)
        
        rotated_l = obj['x'] - rotated_half_width
        rotated_r = obj['x'] + rotated_half_width
        rotated_t = obj['y'] + rotated_half_height
        rotated_b = obj['y'] - rotated_half_height

        # Phaser broadphase check
        broad_phase_hit = (state.x + broad_size > rotated_l and state.x - broad_size < rotated_r and
                           state.y + broad_size > rotated_b and state.y - broad_size < rotated_t)
        
        if not broad_phase_hit:
            continue

        # Check collision overlap (supporting circle and AABB hitboxes)
        if obj_def.get("hitbox_radius") is not None:
            obj_scale = obj.get('scale', 1.0)
            radius = obj_def["hitbox_radius"] * 2.0 * obj_scale
            dx = state.x - obj['x']
            dy = state.y - obj['y']
            is_colliding = (dx*dx + dy*dy) <= (radius + (6.0 if state.game_mode == 4 else (18.0 if state.is_mini else player_size))) ** 2
        else:
            # Use visually exact player boundary to prevent visual phasing/clipping inside any blocks or hazards [1]
            col_w = effective_size
            col_h = effective_size
            
            if obj_type == "hazard":
                # Hazards (spikes) use rotated AABB collision physically
                is_colliding = (state.x + col_w > rotated_l and state.x - col_w < rotated_r and
                                state.y + col_h > rotated_b and state.y - col_h < rotated_t)
            else:
                # Solids (blocks) use unrotated AABB checks physically
                is_colliding = (state.x + col_w > unrotated_l and state.x - col_w < unrotated_r and
                                state.y + col_h > unrotated_b and state.y - col_h < unrotated_t)
            
        if is_colliding:
            # Spike / Hazard
            if obj_type == "hazard":
                state.is_dead = True
                return
            # Yellow Jump Pad
            elif obj_type == "pad":
                state.y_velocity = flip_mod(state) * 32.0
                state.on_ground = False
                state.can_jump = False
                state.is_jumping = True
                return

            # Solid Block collision physics (bottom/top landing, side walls crash)
            _0x146a97 = state.y - effective_size + gamemode_addition
            _0x869e42 = state.last_y - effective_size + gamemode_addition
            _0x3e7199 = state.y + effective_size - gamemode_addition
            _0x135a9d = state.last_y + effective_size - gamemode_addition

            _land_bot = (state.y_velocity <= 0 or state.on_ground) and (_0x146a97 >= unrotated_t or _0x869e42 >= unrotated_t)
            _land_top = (state.y_velocity >= 0 or state.on_ground) and (_0x3e7199 <= unrotated_b or _0x135a9d <= unrotated_b)
            is_standing_on_platform = _land_top if state.gravity_flipped else _land_bot

            if not is_standing_on_platform:
                state.is_dead = True
                return

            if state.x + effective_size - 5 > unrotated_l and state.x - effective_size + 5 < unrotated_r:
                if not state.gravity_flipped and (_land_bot) and (state.y_velocity <= 0 or state.on_ground):
                    state.y = unrotated_t + effective_size
                    state.y_velocity = 0.0
                    state.on_ground = True
                    state.can_jump = True
                    state.rotate_action_active = False
                elif state.gravity_flipped and (_land_top) and (state.y_velocity >= 0 or state.on_ground):
                    state.y = unrotated_b - effective_size
                    state.y_velocity = 0.0
                    state.on_ground = True
                    state.can_jump = True
                    state.on_ceiling = True
                    state.rotate_action_active = False

def draw_temporary_cube(cr, x, y, rot, mini=False, main_color=(4/255, 255/255, 0/255), sec_color=(0, 251/255, 1.0)):
    size = 36.0 if mini else 60.0
    cr.save()
    cr.translate(x, y)
    cr.rotate(rot)

    # Shell
    cr.rectangle(-size/2, -size/2, size, size)
    cr.set_source_rgb(*main_color)
    cr.fill_preserve()
    cr.set_source_rgb(0, 0, 0)
    cr.set_line_width(4)
    cr.stroke()

    # Inner Details
    inner = size * 0.6
    cr.rectangle(-inner/2, -inner/2, inner, inner)
    cr.set_source_rgb(*sec_color)
    cr.fill_preserve()
    cr.set_source_rgb(0, 0, 0)
    cr.set_line_width(3)
    cr.stroke()

    # Face details
    ew, eh = size * 0.16, size * 0.26
    cr.rectangle(-size*0.22, -size*0.24, ew, eh)
    cr.rectangle(size*0.06, -size*0.24, ew, eh)
    cr.set_source_rgb(0, 0, 0)
    cr.fill()

    cr.set_line_width(3)
    cr.move_to(-size*0.18, size*0.16)
    cr.line_to(size*0.18, size*0.16)
    cr.stroke()

    cr.restore()