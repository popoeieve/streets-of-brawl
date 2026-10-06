class_name Boss
extends Fighter
## Jefe: EL BRUTO. Más vida y más daño que un enemigo normal, con ataques especiales:
##  - BARRIDO DE COLA (cuerpo a cuerpo, derriba)       - EMBESTIDA (si está cerca se aleja primero a media pantalla; se carga, recorre la pantalla y queda aturdido)
##  - LANZAMIENTO DE DAGAS (1 daga; 5 en abanico en furia)  - RUGIDO: al bajar al 50% de vida entra en furia.
## Reacción a los golpes: un golpe normal lo deja tambaleándose 0,5 s; la patada del combo y la patada voladora lo derriban.

const Projectile := preload("res://scripts/boss_projectile.gd")
const STAGGER_TIME := 0.5
const ARMOR_AFTER_DOWN := 0.3 ## Sin aguante al levantarse: puede ser golpeado y tambalearse en cuanto se pone en pie.
const BODY_HEIGHT := 90.0 ## Altura del cuerpo del boss durante la embestida: no se le puede saltar por encima.
const CHARGE_MIN_DIST := 160.0 ## Media pantalla: la embestida solo arranca con esta distancia al jugador.
const RETREAT_SPEED := 320.0 ## Velocidad con la que se aleja antes de embestir.
const SPIT_LANE := 14.0 ## Diferencia máxima de fila con el jugador para lanzar una daga (fuera de furia).
const RAGE_SPEED := 1.5 ## En furia se mueve un 50% más rápido.
const RAGE_TINT := Color(1.22, 0.78, 0.78) ## En furia sus texturas se vuelven algo más rojas.

var arena_l := 0.0 ## Límites de movimiento una vez dentro de la pantalla (los pone main.gd).
var arena_r := 100000.0
var target: Fighter
var rage := false
var _act := "approach"
var _t := 0.0
var _cd := 0.8
var _last := ""
var _fired := false
var _hit_b := false
var _entered := false
var _flash := 0.0
var _armor := 0.0
var _was_down := false
var _downs := 0 ## Derribos recibidos desde la última embestida forzada.
var _force_charge := false ## Cada 2 derribos, el siguiente ataque es una embestida.
var _rdir := 0.0 ## Dirección de la carrera previa a la embestida (0 = aún sin decidir).


func _ready() -> void:
	super._ready()
	add_to_group("enemies")
	score_value = 1500
	state = "special"
	special_anim = "walk"
	hurt_time = STAGGER_TIME


## El aguante empieza EN EL MISMO INSTANTE en que sale del estado "down" (así una patada voladora que llega
## justo en ese fotograma, antes de que el boss procese el suyo, ya lo encuentra protegido).
func set_state(new_state: String) -> void:
	if state == "down" and new_state != "down":
		_armor = ARMOR_AFTER_DOWN
	super.set_state(new_state)


func _find_target() -> void:
	if target == null or not is_instance_valid(target) or target.state == "dead":
		target = null
		for p in get_tree().get_nodes_in_group("players"):
			if (p as Fighter).state != "dead":
				target = p
				return


func get_targets() -> Array:
	return get_tree().get_nodes_in_group("players")


func _process(delta: float) -> void:
	if state == "idle" or state == "walk" or state == "jump":
		_act = "approach"
		_t = 0.0
		set_state("special")
	if not _entered and position.x <= arena_r - 6.0:
		_entered = true
		min_x = arena_l
		max_x = arena_r
	_flash = maxf(_flash - delta, 0.0)
	_armor = maxf(_armor - delta, 0.0)
	if state == "down":
		_was_down = true
	elif _was_down:
		_was_down = false
		_armor = ARMOR_AFTER_DOWN # acaba de levantarse
		_find_target()
		if target != null and absf(target.position.x - position.x) < 55.0 and absf(target.position.y - position.y) < 10.0 \
				and target.state != "down" and target.state != "dead":
			set_state("special")
			Sfx.play("boss_yell", 0.0)
			_go("punch") # al levantarse con el jugador pegado, le suelta un puñetazo al instante
	super._process(delta)
	if _flash > 0.0 and state == "special":
		modulate = Color(1.9, 1.9, 1.9) * Background.night_tint(position.x)
	if rage:
		modulate *= RAGE_TINT


func _go(act: String) -> void:
	_act = act
	_t = 0.0
	_fired = false
	_hit_b = false
	_rdir = 0.0


func _anim_loop(name: String, fps: float) -> void:
	special_anim = name
	special_frame = int(anim_time * fps) % int(_anim(name)["n"])


func _special_process(delta: float) -> void:
	_find_target()
	_t += delta
	if target == null:
		_anim_loop("idle", 7.0)
		return
	var dx := target.position.x - position.x
	var dy := target.position.y - position.y
	var spd := move_speed * (RAGE_SPEED if rage else 1.0)

	match _act:
		"approach":
			facing = 1 if dx > 0.0 else -1
			_cd -= delta
			var side := -1.0 if dx > 0.0 else 1.0 # se queda en su lado del jugador
			var goal := Vector2(target.position.x + side * 38.0, target.position.y)
			var to_goal := goal - position
			var mv := Vector2.ZERO if to_goal.length() < 4.0 else to_goal.normalized()
			position += mv * Vector2(spd, spd * 0.6) * delta
			if mv == Vector2.ZERO:
				_anim_loop("idle", 7.0)
			else:
				_anim_loop("walk", 8.0 * (RAGE_SPEED if rage else 1.0))
			if not _entered:
				return # todavía entrando en pantalla
			if not rage and health <= max_health / 2:
				Sfx.play("boss_roar", 2.0, 0.9, 0.02)
				_go("roar")
			elif _cd <= 0.0:
				_choose(absf(dx), absf(dy))
		"roar":
			_anim_loop("idle2", 10.0)
			if _t > 1.1:
				rage = true
				_cd = 0.3
				_go("approach")
		"sweep":
			# barrido de cola: prepara (0.3 s), golpea y se recupera
			if _t < 0.3:
				facing = 1 if dx > 0.0 else -1
			special_anim = "attack1"
			special_frame = 0 if _t < 0.12 else 1 if _t < 0.3 else 2 if _t < 0.65 else 0
			if _t >= 0.3 and not _hit_b:
				_hit_b = true
				Sfx.play("swing", 2.0, 0.65)
				var ddx := (target.position.x - position.x) * facing
				if ddx > -12.0 and ddx < 54.0 and absf(dy) < 20.0 and target.z < 30.0:
					target.take_damage(attack_damage + 6, self, true)
			if _t > 0.85:
				_end_attack(0.7)
		"punch":
			# puñetazo instantáneo al levantarse: golpea en el primer fotograma y derriba
			facing = 1 if dx > 0.0 else -1
			special_anim = "attack1"
			special_frame = 2 if _t < 0.35 else 0
			if not _hit_b:
				_hit_b = true
				Sfx.play("swing", 2.0, 0.8)
				var pdx := (target.position.x - position.x) * facing
				if pdx > -24.0 and pdx < 55.0 and absf(dy) < 10.0 and target.z < 70.0:
					target.knock_down(self, attack_damage)
					if target.state == "down":
						target.knock = float(facing) * 340.0 # sale despedido bastante lejos
						target.vz = 150.0
			if _t > 0.5:
				_end_attack(0.5)
		"spit":
			if _t < 0.4:
				facing = 1 if dx > 0.0 else -1
			special_anim = "attack1"
			special_frame = 0 if _t < 0.2 else 1 if _t < 0.5 else 2 if _t < 0.8 else 0
			if _t >= 0.5 and not _fired:
				_fired = true
				Sfx.play("swing", 2.0, 1.4)
				var shots := [0.0] if not rage else [-48.0, -24.0, 0.0, 24.0, 48.0]
				for vy in shots:
					var p := Projectile.new()
					p.position = position + Vector2(facing * 38.0, 0.0)
					p.z = 30.0
					p.vel = Vector2(facing * 150.0, vy)
					p.damage = attack_damage
					p.owner_boss = self
					get_parent().add_child(p)
			if _t > 1.0:
				_end_attack(0.6)
		"retreat":
			# corre a gran velocidad hasta quedar a media pantalla del jugador. Si por su lado no hay sitio
			# (arrinconado), cruza corriendo hacia el otro lado de la pantalla.
			if _rdir == 0.0:
				var away := -1.0 if dx > 0.0 else 1.0
				var room_away := (arena_r - target.position.x) if away > 0.0 else (target.position.x - arena_l)
				var room_other := (target.position.x - arena_l) if away > 0.0 else (arena_r - target.position.x)
				_rdir = away if (room_away >= CHARGE_MIN_DIST + 4.0 or room_away >= room_other) else -away
			facing = int(_rdir)
			_anim_loop("walk", 22.0)
			position.x += _rdir * RETREAT_SPEED * delta
			position.y = move_toward(position.y, target.position.y, 55.0 * delta)
			var at_edge := (_rdir > 0.0 and position.x >= arena_r - 1.0) or (_rdir < 0.0 and position.x <= arena_l + 1.0)
			if absf(dx) >= CHARGE_MIN_DIST + 4.0 or at_edge or _t > 2.0:
				_go("charge_tell") # ya hay distancia (o no se puede más): aviso y embestida
		"charge_tell":
			# se agacha y brama antes de embestir (aviso para el jugador)
			facing = 1 if dx > 0.0 else -1
			_anim_loop("walk", 18.0)
			position.x += randf_range(-0.6, 0.6)
			position.y = move_toward(position.y, target.position.y, 55.0 * delta) # se alinea con el jugador; al embestir ya no corrige
			if _t > (1.1 if rage else 1.6):
				_go("charge")
		"charge":
			special_anim = "attack1"
			special_frame = 2
			position.x += facing * 195.0 * (RAGE_SPEED if rage else 1.0) * delta
			var ddx := (target.position.x - position.x) * facing
			if not _hit_b and ddx > -24.0 and ddx < 36.0 and absf(dy) < 10.0 and target.z < BODY_HEIGHT:
				_hit_b = true
				target.knock_down(self, attack_damage * 2)
				Sfx.play("boss_laugh", 0.0) # ha acertado la embestida: se rie
			var wall := (facing > 0 and position.x >= max_x - 1.0) or (facing < 0 and position.x <= min_x + 1.0)
			if wall or _t > 1.6 or _hit_b and _t > 0.2:
				if not _hit_b:
					Sfx.play("boss_laugh", 0.0) # ha fallado la embestida: tambien se rie mientras esta aturdido
				_go("stun")
		"stun":
			# tras la embestida queda aturdido: ventana para castigarla
			_anim_loop("idle2", 8.0)
			if _t > (0.9 if rage else 1.3):
				_end_attack(0.4)


func _choose(dist: float, dy: float) -> void:
	var near := dist < 66.0 and dy < 18.0
	var pick := ""
	var r := randf()
	if near:
		pick = "sweep" if r < 0.85 else "charge_tell"
	elif dist > 120.0:
		pick = "charge_tell" if r < 0.5 else "spit"
	else:
		pick = "spit" if r < 0.5 else ""
	if _force_charge:
		pick = "charge_tell" # tras 2 derribos, intenta una embestida (la distancia se la da el desplazamiento previo)
		_force_charge = false
	elif pick == _last and pick != "sweep":
		pick = "spit" if pick == "charge_tell" else "charge_tell"
	# Las dagas vuelan rectas: solo las lanza si el jugador está justo enfrente (en su misma fila); en furia, siempre.
	if pick == "spit" and not rage and dy > SPIT_LANE:
		pick = ""
	if pick == "":
		_cd = 0.25 # se recoloca (se alinea con el jugador) y vuelve a decidir
		return
	_last = pick
	if pick == "sweep" or pick == "spit":
		Sfx.play("boss_yell", 0.0)                                # grito al atacar
	if pick == "charge_tell":
		Sfx.play("boss_roar", 0.0)
		# sin distancia suficiente, primero se aleja a toda velocidad (mientras ruge) y luego embiste
		if dist < CHARGE_MIN_DIST:
			pick = "retreat"
	_go(pick)


func _end_attack(cooldown: float) -> void:
	_cd = cooldown * (0.6 if rage else 1.0) + randf_range(0.0, 0.4)
	_go("approach")


## Daño recibido. Golpe normal -> tambaleo de 0,5 s; golpe fuerte (patada del combo) -> derribo.
func take_damage(amount: int, from: Fighter, strong := false) -> void:
	if state == "dead" or state == "down":
		return
	if rage and _act == "charge":
		return # en furia, mientras embiste es intocable: ni daño, ni tambaleo, ni derribo
	health = maxi(health - amount, 0)
	health_changed.emit(health, max_health)
	_play_hit_sounds(strong)
	if health <= 0:
		die()
		return
	_flash = 0.1
	if _armor > 0.0:
		return
	_go("approach")
	_cd = 0.4
	if strong:
		_fall(from)
	else:
		knock = signf(position.x - from.position.x) * 50.0
		state = "hurt"
		state_time = 0.0


## La patada voladora lo derriba igual que la patada del combo.
func knock_down(from: Fighter, amount: int) -> void:
	if state == "dead" or state == "down":
		return
	if rage and _act == "charge":
		return # en furia, mientras embiste es intocable: ni daño, ni tambaleo, ni derribo
	health = maxi(health - amount, 0)
	health_changed.emit(health, max_health)
	_play_hit_sounds(true)
	if health <= 0:
		die()
		return
	_flash = 0.1
	if _armor > 0.0:
		return
	_go("approach")
	_cd = 0.4
	_fall(from)


func _fall(from: Fighter) -> void:
	_downs += 1
	if _downs >= 2:
		_downs = 0
		_force_charge = true
	var dir := signf(position.x - from.position.x)
	knock = (dir if dir != 0.0 else float(from.facing)) * 150.0
	vz = 110.0
	z = 0.01
	state = "down"
	state_time = 0.0
