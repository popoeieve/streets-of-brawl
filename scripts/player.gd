class_name Player
extends Fighter
## Controles: WASD / flechas = mover, J / Z = golpear (3 seguidos = combo), K / X = saltar.

var auto_walk := false ## Al acabar la misión: camina solo hacia la derecha y el jugador pierde el control.
var exit_x := 0.0 ## x a partir de la cual ya ha salido de la pantalla.


func _ready() -> void:
	super._ready()
	add_to_group("players")


func get_move_input() -> Vector2:
	if auto_walk:
		facing = 1
		return Vector2.ZERO if position.x >= exit_x else Vector2(0.5, 0.0) # camina despacio
	var v := Input.get_vector("move_left", "move_right", "move_up", "move_down")
	if v.x != 0.0:
		facing = 1 if v.x > 0.0 else -1
	return v


func wants_attack() -> bool:
	return not auto_walk and Input.is_action_just_pressed("attack")


func wants_jump() -> bool:
	return not auto_walk and Input.is_action_just_pressed("jump")


func get_targets() -> Array:
	return get_tree().get_nodes_in_group("enemies")
