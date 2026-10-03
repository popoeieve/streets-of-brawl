class_name Player
extends Fighter
## Controles: WASD / flechas = mover, J / Z = golpear (3 seguidos = combo), K / X = saltar.


func _ready() -> void:
	super._ready()
	add_to_group("players")


func get_move_input() -> Vector2:
	var v := Input.get_vector("move_left", "move_right", "move_up", "move_down")
	if v.x != 0.0:
		facing = 1 if v.x > 0.0 else -1
	return v


func wants_attack() -> bool:
	return Input.is_action_just_pressed("attack")


func wants_jump() -> bool:
	return Input.is_action_just_pressed("jump")


func get_targets() -> Array:
	return get_tree().get_nodes_in_group("enemies")
