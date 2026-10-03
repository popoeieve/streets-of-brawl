class_name Enemy
extends Fighter
## IA básica: se acerca al jugador, se coloca a su lado y ataca cada cierto tiempo.

var target: Fighter
var attack_cooldown := 1.5
var offset_y := 0.0
var _want_attack := false


func _ready() -> void:
	super._ready()
	add_to_group("enemies")
	offset_y = randf_range(-6.0, 6.0)
	attack_cooldown = randf_range(1.0, 2.0)


func _find_target() -> void:
	target = null
	for p in get_tree().get_nodes_in_group("players"):
		if (p as Fighter).state != "dead":
			target = p
			return


func get_move_input() -> Vector2:
	_want_attack = false
	if target == null or not is_instance_valid(target) or target.state == "dead":
		_find_target()
	if target == null:
		return Vector2.ZERO

	facing = 1 if target.position.x > position.x else -1
	attack_cooldown -= get_process_delta_time()

	var dx := absf(target.position.x - position.x)
	var dy := absf(target.position.y - position.y)
	if dx < 30.0 and dy < 8.0:
		if attack_cooldown <= 0.0:
			_want_attack = true
			attack_cooldown = randf_range(1.2, 2.2)
		return Vector2.ZERO

	var goal := Vector2(target.position.x - float(facing) * 22.0, target.position.y + offset_y)
	var to_goal := goal - position
	if to_goal.length() < 3.0:
		return Vector2.ZERO
	return to_goal.normalized()


func wants_attack() -> bool:
	return _want_attack


func get_targets() -> Array:
	return get_tree().get_nodes_in_group("players")
