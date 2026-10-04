class_name Enemy
extends Fighter
## IA agresiva: se acerca rápido al jugador, se coloca a su lado y ataca sin parar (cada ~0,5-1 s).

var target: Fighter
var attack_cooldown := 0.6
var offset_y := 0.0
var _want_attack := false


func _ready() -> void:
	super._ready()
	add_to_group("enemies")
	offset_y = randf_range(-6.0, 6.0)
	attack_cooldown = randf_range(0.3, 0.8)


func _find_target() -> void:
	target = null
	for p in get_tree().get_nodes_in_group("players"):
		if (p as Fighter).state != "dead":
			target = p
			return


## Puesto que ocupa este enemigo alrededor del jugador (0 = el más antiguo vivo).
func _slot() -> int:
	var rank := 0
	for other in get_tree().get_nodes_in_group("enemies"):
		if other != self and other.get_instance_id() < get_instance_id():
			rank += 1
	return rank


func get_move_input() -> Vector2:
	_want_attack = false
	if target == null or not is_instance_valid(target) or target.state == "dead":
		_find_target()
	if target == null:
		return Vector2.ZERO

	facing = 1 if target.position.x > position.x else -1
	attack_cooldown -= get_process_delta_time()

	# Cada enemigo ocupa un puesto distinto para no agruparse y que el jugador no los golpee a la vez:
	# los puestos pares van a la izquierda y los impares a la derecha; los que no caben en la primera
	# fila esperan más lejos y en otra "calle" (distinta altura).
	var slot := _slot()
	var side := -1.0 if slot % 2 == 0 else 1.0
	var ring := slot >> 1
	var lanes := [0.0, 30.0, -30.0]
	var goal := Vector2(target.position.x + side * (22.0 + ring * 52.0),
			target.position.y + float(lanes[ring % 3]) + offset_y)

	var dx := absf(target.position.x - position.x)
	var dy := absf(target.position.y - position.y)
	if ring == 0 and dx < 30.0 and dy < 8.0 and signf(position.x - target.position.x) == side:
		if attack_cooldown <= 0.0:
			_want_attack = true
			attack_cooldown = randf_range(0.45, 1.0)
		return Vector2.ZERO

	# Separación: se apartan de los enemigos que tengan encima.
	var push := Vector2.ZERO
	for other in get_tree().get_nodes_in_group("enemies"):
		if other == self:
			continue
		var d: Vector2 = position - (other as Node2D).position
		if absf(d.x) < 34.0 and absf(d.y) < 18.0:
			if d == Vector2.ZERO:
				d = Vector2(randf_range(-1.0, 1.0), randf_range(-1.0, 1.0))
			push += Vector2(d.x / 34.0, d.y / 18.0)

	var to_goal := goal - position
	var heading := Vector2.ZERO if to_goal.length() < 3.0 else to_goal.normalized()
	return (heading + push * 1.6).limit_length(1.0)


func wants_attack() -> bool:
	return _want_attack


func get_targets() -> Array:
	return get_tree().get_nodes_in_group("players")
