class_name Player
extends Fighter
## Controles: WASD / flechas = mover, J / Z = golpear (3 seguidos = combo), K / X = saltar.

var auto_walk := false ## Al acabar la misión: camina solo hacia la derecha y el jugador pierde el control.
var exit_x := 0.0 ## x a partir de la cual ya ha salido de la pantalla.
var specials := 3 ## Especiales que le quedan (tecla L / C): onda que derriba a los rivales cercanos.
var specials_used := 0 ## Cuántos ha gastado en esta misión.
signal specials_changed(left: int, used: int)

const SPECIAL_RANGE_X := 100.0
const SPECIAL_RANGE_Y := 60.0
const SPECIAL_DAMAGE := 30


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


func _process(delta: float) -> void:
	if not auto_walk and Input.is_action_just_pressed("special") and specials > 0 \
			and (state == "idle" or state == "walk" or state == "jump"):
		_use_special()
	super._process(delta)


## Especial: onda de choque a tu alrededor. Derriba a los enemigos y hace daño al jefe.
func _use_special() -> void:
	specials -= 1
	specials_used += 1
	specials_changed.emit(specials, specials_used)
	Sfx.play("thunder", -2.0, 1.2, 0.02)
	var blast := SpecialBlast.new()
	blast.position = position
	get_parent().add_child(blast)
	for t in get_targets():
		var f := t as Fighter
		if f == null or f.state == "dead" or f.state == "down":
			continue
		if absf(f.position.x - position.x) < SPECIAL_RANGE_X + f.body_radius \
				and absf(f.position.y - position.y) < SPECIAL_RANGE_Y:
			if f is Boss:
				f.take_damage(SPECIAL_DAMAGE, self, true)
			else:
				f.knock_down(self, SPECIAL_DAMAGE * 2)


## Anillo que se expande y se desvanece al usar el especial.
class SpecialBlast extends Node2D:
	var t := 0.0

	func _process(delta: float) -> void:
		t += delta
		queue_redraw()
		if t > 0.45:
			queue_free()

	func _draw() -> void:
		var k := t / 0.45
		var a := 1.0 - k
		draw_set_transform(Vector2.ZERO, 0.0, Vector2(1.0, 0.45))
		draw_arc(Vector2.ZERO, 10.0 + 90.0 * k, 0.0, TAU, 40, Color(1.0, 0.9, 0.3, a), 3.0)
		draw_arc(Vector2.ZERO, 4.0 + 70.0 * k, 0.0, TAU, 32, Color(1.0, 1.0, 1.0, a * 0.8), 2.0)
