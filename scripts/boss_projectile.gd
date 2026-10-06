class_name BossProjectile
extends Node2D
## Daga lanzada por el boss: vuela en línea recta a la altura del pecho y daña al jugador.

var vel := Vector2(120, 0)
var z := 30.0
var damage := 10
var owner_boss: Fighter
var _t := 0.0
var _fallen := false ## Desviada por una patada voladora: cae al suelo sin hacer daño.
var _vz := 0.0
var _ang := 0.0


func _ready() -> void:
	add_to_group("boss_projectiles")
	_ang = vel.angle()


## Una patada voladora la golpea: suena metálico, rebota hacia atrás y cae al suelo sin dañar.
func deflect(from_dir: float) -> void:
	if _fallen:
		return
	_fallen = true
	_vz = 70.0
	vel = Vector2(from_dir * 55.0, 0.0)
	_t = 0.0
	Sfx.play("clang", 0.0)


func _process(delta: float) -> void:
	_t += delta
	position += vel * delta
	if _fallen:
		vel.x = move_toward(vel.x, 0.0, 120.0 * delta)
		_vz -= 500.0 * delta
		z = maxf(z + _vz * delta, 1.0)
		if z <= 1.0:
			vel.x = 0.0
			_ang = lerp_angle(_ang, 0.0, 0.3)
		else:
			_ang += 14.0 * delta * signf(vel.x if vel.x != 0.0 else 1.0)
		if _t > 0.9:
			queue_free()
		queue_redraw()
		return
	for p in get_tree().get_nodes_in_group("players"):
		var f := p as Fighter
		if f == null or f.state == "dead" or f.state == "down":
			continue
		if absf(f.position.x - position.x) < 9.0 and absf(f.position.y - position.y) < 12.0 \
				and f.z < z + 14.0 and f.z > z - 44.0:
			f.take_damage(damage, owner_boss if is_instance_valid(owner_boss) else f, false)
			queue_free()
			return
	var cam := get_viewport().get_camera_2d()
	if position.y < 120.0 or position.y > 230.0 or _t > 4.0 \
			or (cam != null and absf(position.x - cam.position.x) > 190.0):
		queue_free()
	queue_redraw()


func _draw() -> void:
	draw_set_transform(Vector2.ZERO, 0.0, Vector2(1, 0.35))
	draw_circle(Vector2.ZERO, 3.0, Color(0, 0, 0, 0.3)) # sombra en el suelo
	# la daga apunta en la dirección del vuelo (píxeles enteros)
	draw_set_transform(Vector2(0, -z), _ang, Vector2.ONE)
	draw_rect(Rect2(-9, -1, 3, 2), Color("5a3a2a"))     # empuñadura
	draw_rect(Rect2(-6, -3, 2, 6), Color("c8a040"))     # guarda
	draw_rect(Rect2(-4, -1, 11, 2), Color("d8e0ea"))    # hoja
	draw_rect(Rect2(-4, 0, 10, 1), Color("8a96a8"))     # filo en sombra
	draw_rect(Rect2(7, -1, 2, 2), Color("eef4fa"))      # punta
	draw_rect(Rect2(9, 0, 1, 1), Color("eef4fa"))
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
