class_name Fighter
extends Node2D
## Base de cualquier luchador (jugador y enemigos).
## Modelo "falso 3D" de beat 'em up: position.x/y es el suelo y `z` es la altura del salto.
## Los gráficos son sprites pixel art (assets/sprites); la sombra y la barra de vida se dibujan por código.

signal health_changed(hp: int, max_hp: int)
signal died(fighter: Fighter)

const GRAVITY := 600.0
const JUMP_SPEED := 230.0
const WALK_MIN_Y := 142.0
const WALK_MAX_Y := 214.0

const DOWN_TIME := 2.0 ## Segundos que un derribado tarda en levantarse.
const KICK_WINDUP := 1.8 ## La patada (3er golpe del combo) tarda más en conectar que los puñetazos.

@export var max_health := 100
@export var move_speed := 70.0
@export var attack_damage := 10
@export var hit_time := 0.1 ## Segundos desde que empieza el ataque hasta que golpea.
@export var hit_reach := 42.0 ## Alcance horizontal del golpe (px por delante del luchador).
@export var hit_depth := 26.0 ## Tolerancia en profundidad (eje Y): cuánto puede estar el rival por encima/debajo.
@export var free_on_death := false
@export var show_health_bar := false
@export var hurt_time := 0.4 ## Segundos que dura el tambaleo al recibir un golpe normal.
@export var body_radius := 0.0 ## Cuerpo extra del luchador: los rivales le alcanzan desde más lejos (el boss es grande).
@export var shadow_radius := 11.0 ## Tamaño de la sombra en el suelo (el boss la tiene mayor).
@export_group("Sprites")
@export var sprite_sheet: Texture2D ## Hoja de sprites (una fila por animación).
@export var anim_set := "brawler" ## Clave en scripts/anim_sets.gd ("brawler", "punk"...).

var health := 100
var facing := 1
var z := 0.0
var vz := 0.0
var knock := 0.0
var state := "idle" # idle, walk, jump, attack, hurt, down (derribado), dead
var state_time := 0.0
var anim_time := 0.0
var combo := 0
var score_value := 100 ## Puntos que da al morir (el boss da más).
var special_anim := "idle" ## Animación que se reproduce en el estado "special" (ataques especiales de un boss).
var special_frame := 0 ## Frame de esa animación (lo fija el boss cada fotograma).
var min_x := -1000.0
var max_x := 100000.0
var _last_attack_ms := -10000
var _hit_done := false
var _kicked: Array = [] ## Rivales ya derribados por la patada voladora actual.
var _air_attack := false ## Golpe dado en el aire: patada voladora que conserva el impulso del salto.
var _sprite: Sprite2D
var _fw := 1.0 ## Tamaño de un fotograma en la hoja de sprites.
var _fh := 1.0
var _cfg: Dictionary
var _feet := Vector2.ZERO
var _atk_hit_time := 0.1


func _ready() -> void:
	health = max_health
	_atk_hit_time = hit_time
	_cfg = AnimSets.SETS[anim_set]
	_feet = _cfg["feet"]
	_sprite = Sprite2D.new()
	_sprite.texture = sprite_sheet
	# Se recorta cada fotograma con una región y se activa el recorte del filtro: así, aunque el sprite se
	# tambalee, gire o quede a medio píxel, no se cuelan líneas del fotograma vecino de la hoja.
	_fw = float(sprite_sheet.get_width()) / float(_cfg["cols"])
	_fh = float(sprite_sheet.get_height()) / float(_cfg["rows"])
	_sprite.region_enabled = true
	_sprite.region_filter_clip_enabled = true
	_sprite.centered = false
	_sprite.offset = -_feet # el origen del nodo = los pies, así las rotaciones giran sobre ellos
	add_child(_sprite)


# --- Para sobrescribir en Player / Enemy ---
func get_move_input() -> Vector2:
	return Vector2.ZERO

func wants_attack() -> bool:
	return false

func wants_jump() -> bool:
	return false

func get_targets() -> Array:
	return []

## Estado "special": lo implementa el boss (ataques con animación y movimiento propios).
func _special_process(_delta: float) -> void:
	set_state("idle")
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
			if _air_attack:
				# en el aire no se frena: sigue moviéndose y mantiene la patada hasta aterrizar
				position += get_move_input() * Vector2(move_speed, move_speed * 0.6) * delta
			if _air_attack and state_time >= _atk_hit_time:
				_flying_kick_sweep()
			elif not _hit_done and state_time >= _atk_hit_time:
				do_hit()
			if _air_attack:
				if z <= 0.0 and state_time > 0.05:
					set_state("idle")
			elif state_time >= _atk_hit_time + 0.2:
				set_state("jump" if z > 0.0 else "idle")
		"hurt":
			position.x += knock * delta
			knock = move_toward(knock, 0.0, 400.0 * delta)
			if state_time >= hurt_time:
				set_state("jump" if z > 0.0 else "idle")
		"down":
			# derribado: sale despedido, cae al suelo y se levanta (no muere)
			position.x += knock * delta
			knock = move_toward(knock, 0.0, 300.0 * delta)
			if state_time >= DOWN_TIME and z <= 0.0:
				set_state("idle")
		"special":
			_special_process(delta)
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

	# Ambiente nocturno: los luchadores se oscurecen y se iluminan al pasar junto a una farola.
	var base := Background.night_tint(position.x)
	if state == "hurt":
		# destello blanco en el impacto y luego tinte rojizo
		modulate = (Color(2.0, 2.0, 2.0) if state_time < 0.06 else Color(1.0, 0.65, 0.65)) * base
	elif state == "dead" and free_on_death:
		modulate = Color(base.r, base.g, base.b, clampf(1.5 - state_time, 0.0, 1.0))
	else:
		modulate = base
	_update_sprite()
	queue_redraw()


## Devuelve la configuración de una animación resolviendo alias (p. ej. attack2 -> attack1).
func _anim(name: String) -> Dictionary:
	var a: Dictionary = _cfg["anims"].get(name, _cfg["anims"]["idle"])
	if a.has("alias"):
		a = _cfg["anims"][a["alias"]]
	return a


func _update_sprite() -> void:
	var a := _anim("idle")
	var frame := 0
	var k := 0.0 # intensidad del movimiento por código en ataques sin frames propios
	match state:
		"walk":
			a = _anim("walk")
			frame = int(anim_time * a["fps"]) % int(a["n"])
		"jump":
			a = _anim("jump")
			# el frame sale de la velocidad vertical: subiendo -> arriba -> cayendo
			# La animación va al doble de rápido: los primeros frames durante la subida y el
			# último frame (cayendo) se queda la segunda mitad del salto.
			var p := clampf((JUMP_SPEED - vz) / (2.0 * JUMP_SPEED), 0.0, 1.0)
			var n_j := int(a["n"])
			frame = n_j - 1 if p >= 0.5 else mini(int(p / 0.5 * (n_j - 1)), n_j - 1)
		"attack":
			var atk_name := "attack%d" % clampi(combo, 1, 3)
			if _air_attack:
				atk_name = "dive_kick" if _cfg["anims"].has("dive_kick") else "attack3"
			a = _anim(atk_name)
			var n := int(a["n"])
			var impact := int(a.get("impact", 1))
			if state_time < _atk_hit_time:
				k = -0.35 * state_time / _atk_hit_time # se echa atrás al preparar el golpe
				# preparación: reparte los frames previos al impacto
				frame = mini(int(state_time / _atk_hit_time * impact), maxi(impact - 1, 0))
			elif state_time < _atk_hit_time + 0.1:
				k = 1.0
				frame = impact # golpe
			elif _air_attack:
				k = 1.0
				frame = impact # patada voladora: pierna extendida hasta aterrizar
			else:
				# recuperación: reparte los frames posteriores
				var rest := n - 1 - impact
				var t := (state_time - _atk_hit_time - 0.1) / 0.1
				k = maxf(1.0 - t * 0.7, 0.0)
				frame = mini(impact + 1 + int(t * rest), n - 1) if rest > 0 else impact
		"hurt":
			a = _anim("hurt")
			frame = mini(int(state_time / 0.4 * int(a["n"])), int(a["n"]) - 1)
		"special":
			a = _anim(special_anim)
			frame = clampi(special_frame, 0, int(a["n"]) - 1)
		"dead", "down":
			a = _anim("dead")
			frame = mini(int(state_time / 0.15), int(a["n"]) - 1)
		_:
			a = _anim("idle")
			frame = int(anim_time * a["fps"]) % int(a["n"])
	var fi := int(a["row"]) * int(_cfg["cols"]) + int(a.get("start", 0)) + frame
	var ncols := int(_cfg["cols"])
	_sprite.region_rect = Rect2(float(fi % ncols) * _fw, float(floori(float(fi) / float(ncols))) * _fh, _fw, _fh)
	_sprite.flip_h = (facing < 0) == bool(_cfg.get("faces_right", true))
	_sprite.position = Vector2(0.0, -z)
	_sprite.rotation = 0.0
	# Poses por código para animaciones que el sprite sheet no trae (campo "fx" en anim_sets.gd).
	match String(a.get("fx", "")):
		"punch":
			_sprite.position.x += facing * 9.0 * k
			_sprite.rotation = facing * 0.2 * k
		"kick":
			_sprite.position.x += facing * 12.0 * k
			_sprite.position.y -= 5.0 * maxf(k, 0.0)
			_sprite.rotation = facing * 0.3 * k
		"hurt":
			var back := clampf(1.0 - state_time / 0.4, 0.0, 1.0)
			_sprite.position.x -= facing * 3.0 * back
			_sprite.rotation = -facing * 0.22 * back
		"dead", "down":
			var fall := clampf(state_time / 0.25, 0.0, 1.0)
			if state == "down":
				fall *= 1.0 - clampf((state_time - (DOWN_TIME - 0.2)) / 0.2, 0.0, 1.0) # se incorpora al final
			_sprite.rotation = -facing * (PI / 2.0) * fall
			_sprite.position.y -= 10.0 * fall
	if state == "hurt":
		# temblor breve: alterna a izquierda/derecha y se amortigua
		var amp := 2.0 * clampf(1.0 - state_time / 0.3, 0.0, 1.0)
		var shake_dir := 1.0 if int(state_time * 40.0) % 2 == 0 else -1.0
		_sprite.position.x += shake_dir * amp
		_sprite.position.y += (-0.5 if shake_dir > 0.0 else 0.5) * amp


func start_attack() -> void:
	var now := Time.get_ticks_msec()
	if now - _last_attack_ms < 600 and combo < 3:
		combo += 1
	else:
		combo = 1
	_hit_done = false
	_kicked.clear()
	_air_attack = z > 0.0
	if _air_attack:
		combo = 1 # la patada voladora no cuenta para el combo
		_atk_hit_time = 0.12
	else:
		_last_attack_ms = now
		_atk_hit_time = hit_time * (KICK_WINDUP if combo == 3 else 1.0)
	Sfx.play("swing", -4.0 if combo < 3 and not _air_attack else 0.0, 1.0 if combo < 3 else 0.8)
	set_state("attack")


func do_hit() -> void:
	_hit_done = true
	var strong := combo == 3 or _air_attack
	var dmg := attack_damage * (2 if strong else 1)
	for t in get_targets():
		var target := t as Fighter
		if target == null or target.state == "dead" or target.state == "down":
			continue
		var dx := (target.position.x - position.x) * facing
		if dx > -6.0 - target.body_radius and dx < hit_reach + target.body_radius \
				and absf(target.position.y - position.y) < hit_depth \
				and absf(target.z - z) < (50.0 if _air_attack else 30.0):
			target.take_damage(dmg, self, strong)


## Patada voladora: mientras la pierna está extendida, cualquier rival que toque al luchador
## cae al suelo; si el daño le deja sin vida, muere.
func _flying_kick_sweep() -> void:
	# La patada voladora también desvía las dagas del boss (suenan metálicas y caen al suelo).
	for pr in get_tree().get_nodes_in_group("boss_projectiles"):
		var d: float = (pr.position.x - position.x) * facing
		if d > -16.0 and d < hit_reach and absf(pr.position.y - position.y) < hit_depth \
				and absf(pr.z - (z + 14.0)) < 28.0:
			pr.deflect(float(facing))
	for t in get_targets():
		var target := t as Fighter
		if target == null or target in _kicked or target.state == "dead" or target.state == "down":
			continue
		var dx := (target.position.x - position.x) * facing
		if dx > -16.0 - target.body_radius and dx < hit_reach + target.body_radius \
				and absf(target.position.y - position.y) < hit_depth \
				and absf(target.z - z) < 50.0:
			_kicked.append(target)
			target.knock_down(self, attack_damage * 2)


func knock_down(from: Fighter, amount: int) -> void:
	if state == "dead" or state == "down":
		return
	health = maxi(health - amount, 0)
	health_changed.emit(health, max_health)
	_play_hit_sounds(true)
	var dir := signf(position.x - from.position.x)
	if dir == 0.0:
		dir = float(from.facing)
	knock = dir * 150.0
	vz = 110.0
	z = 0.01
	if health <= 0:
		die() # si el daño de la patada alcanza, el rival muere
	else:
		state = "down"
		state_time = 0.0


func take_damage(amount: int, from: Fighter, strong := false) -> void:
	if state == "dead" or state == "down": # un luchador en el suelo es intocable
		return
	health = maxi(health - amount, 0)
	health_changed.emit(health, max_health)
	_play_hit_sounds(strong)
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


## Sonidos del golpe recibido: impacto (ligero o fuerte) y quejido (distinto en el jugador y los enemigos).
func _play_hit_sounds(strong: bool) -> void:
	Sfx.play("hit_heavy" if strong else "hit", 0.0)
	Sfx.play("grunt_player" if is_in_group("players") else "grunt_enemy", -2.0)


func die() -> void:
	Sfx.play("ko", -2.0)
	state = "dead"
	state_time = 0.0
	for g in ["enemies", "players"]:
		if is_in_group(g):
			remove_from_group(g)
	died.emit(self)


func _draw() -> void:
	# Sombra en el suelo (el sprite se dibuja encima, como nodo hijo)
	draw_set_transform(Vector2.ZERO, 0.0, Vector2(1, 0.35))
	draw_circle(Vector2.ZERO, shadow_radius, Color(0, 0, 0, 0.35))
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)

	if show_health_bar and health < max_health and state != "dead":
		var w := 20.0 * float(health) / float(max_health)
		draw_rect(Rect2(-10, -56, 20, 3), Color.BLACK)
		draw_rect(Rect2(-10, -56, w, 3), Color("e04040"))
