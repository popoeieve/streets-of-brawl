class_name Fighter
extends Node2D
## Base de cualquier luchador (jugador y enemigos).
## Modelo "falso 3D" de beat 'em up: position.x/y es el suelo y `z` es la altura del salto.
## Los gráficos son placeholders dibujados por código: sustituir por AnimatedSprite2D más adelante.

signal health_changed(hp: int, max_hp: int)
signal died(fighter: Fighter)

const GRAVITY := 600.0
const JUMP_SPEED := 230.0
const WALK_MIN_Y := 138.0
const WALK_MAX_Y := 214.0

@export var max_health := 100
@export var move_speed := 70.0
@export var attack_damage := 10
@export var hit_time := 0.1 ## Segundos desde que empieza el ataque hasta que golpea.
@export var free_on_death := false
@export var show_health_bar := false
@export_group("Colores placeholder")
@export var shirt_color := Color("3b6fd4")
@export var pants_color := Color("2a2a55")
@export var skin_color := Color("f0b27a")
@export var hair_color := Color("3b2a1a")

var health := 100
var facing := 1
var z := 0.0
var vz := 0.0
var knock := 0.0
var state := "idle" # idle, walk, jump, attack, hurt, dead
var state_time := 0.0
var anim_time := 0.0
var combo := 0
var min_x := -1000.0
var max_x := 100000.0
var _last_attack_ms := -10000
var _hit_done := false


func _ready() -> void:
	health = max_health


# --- Para sobrescribir en Player / Enemy ---
func get_move_input() -> Vector2:
	return Vector2.ZERO

func wants_attack() -> bool:
	return false

func wants_jump() -> bool:
	return false

func get_targets() -> Array:
	return []
# -------------------------------------------


func set_state(new_state: String) -> void:
	if state != new_state:
		state = new_state
		state_time = 0.0


func _process(delta: float) -> void:
	state_time += delta
	anim_time += delta

	match state:
		"idle", "walk", "jump":
			var mv := get_move_input()
			if wants_attack():
				start_attack()
			elif wants_jump() and z <= 0.0:
				vz = JUMP_SPEED
				z = 0.01
				set_state("jump")
			else:
				position += mv * Vector2(move_speed, move_speed * 0.6) * delta
				if z <= 0.0:
					set_state("walk" if mv != Vector2.ZERO else "idle")
		"attack":
			if not _hit_done and state_time >= hit_time:
				do_hit()
			if state_time >= hit_time + 0.2:
				set_state("jump" if z > 0.0 else "idle")
		"hurt":
			position.x += knock * delta
			knock = move_toward(knock, 0.0, 400.0 * delta)
			if state_time >= 0.4:
				set_state("jump" if z > 0.0 else "idle")
		"dead":
			position.x += knock * delta
			knock = move_toward(knock, 0.0, 400.0 * delta)
			if free_on_death and state_time > 1.5:
				queue_free()
				return

	# Física vertical (salto)
	if z > 0.0 or vz > 0.0:
		vz -= GRAVITY * delta
		z += vz * delta
		if z <= 0.0:
			z = 0.0
			vz = 0.0
			if state == "jump":
				set_state("idle")

	position.x = clampf(position.x, min_x, max_x)
	position.y = clampf(position.y, WALK_MIN_Y, WALK_MAX_Y)

	if state == "hurt":
		modulate = Color(1.0, 0.6, 0.6)
	elif state == "dead" and free_on_death:
		modulate = Color(1, 1, 1, clampf(1.5 - state_time, 0.0, 1.0))
	else:
		modulate = Color.WHITE
	queue_redraw()


func start_attack() -> void:
	var now := Time.get_ticks_msec()
	if now - _last_attack_ms < 600 and combo < 3:
		combo += 1
	else:
		combo = 1
	_last_attack_ms = now
	_hit_done = false
	set_state("attack")


func do_hit() -> void:
	_hit_done = true
	var strong := combo == 3
	var dmg := attack_damage * (2 if strong else 1)
	for t in get_targets():
		var target := t as Fighter
		if target == null or target.state == "dead":
			continue
		var dx := (target.position.x - position.x) * facing
		if dx > -4.0 and dx < 26.0 \
				and absf(target.position.y - position.y) < 12.0 \
				and absf(target.z - z) < 24.0:
			target.take_damage(dmg, self, strong)


func take_damage(amount: int, from: Fighter, strong := false) -> void:
	if state == "dead":
		return
	health = maxi(health - amount, 0)
	health_changed.emit(health, max_health)
	var dir := signf(position.x - from.position.x)
	if dir == 0.0:
		dir = 1.0
	knock = dir * (140.0 if strong else 50.0)
	if strong and z <= 0.0:
		vz = 120.0
		z = 0.01
	if health <= 0:
		die()
	else:
		state = "hurt"
		state_time = 0.0


func die() -> void:
	state = "dead"
	state_time = 0.0
	for g in ["enemies", "players"]:
		if is_in_group(g):
			remove_from_group(g)
	died.emit(self)


func _draw() -> void:
	# Sombra en el suelo
	draw_set_transform(Vector2.ZERO, 0.0, Vector2(1, 0.35))
	draw_circle(Vector2.ZERO, 11.0, Color(0, 0, 0, 0.35))
	draw_set_transform(Vector2.ZERO, 0.0, Vector2(facing, 1))

	if state == "dead":
		draw_rect(Rect2(-18, -8, 22, 8), shirt_color)
		draw_rect(Rect2(4, -8, 14, 8), pants_color)
		draw_rect(Rect2(-24, -9, 8, 8), skin_color)
		draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
		return

	var oy := -z
	var step := 0.0
	if state == "walk":
		step = sin(anim_time * 14.0) * 3.0
	# piernas
	draw_rect(Rect2(-6 + step, oy - 16, 5, 16), pants_color)
	draw_rect(Rect2(1 - step, oy - 16, 5, 16), pants_color)
	# torso
	draw_rect(Rect2(-7, oy - 32, 14, 17), shirt_color)
	# cabeza
	draw_rect(Rect2(-5, oy - 42, 10, 10), skin_color)
	draw_rect(Rect2(-5, oy - 44, 10, 4), hair_color)
	# brazo / patada
	if state == "attack":
		if combo == 3:
			draw_rect(Rect2(4, oy - 17, 22, 6), pants_color)
		else:
			draw_rect(Rect2(4, oy - 30, 20, 5), skin_color)
	else:
		draw_rect(Rect2(4, oy - 30, 4, 12), skin_color)

	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)

	if show_health_bar and health < max_health:
		var w := 20.0 * float(health) / float(max_health)
		draw_rect(Rect2(-10, oy - 52, 20, 3), Color.BLACK)
		draw_rect(Rect2(-10, oy - 52, w, 3), Color("e04040"))
