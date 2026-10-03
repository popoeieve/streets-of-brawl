extends Node2D
## Nivel principal: crea fondo, jugador, cámara, HUD y gestiona las oleadas de enemigos.
## Edita WAVES para cambiar el diseño del nivel.

const LEVEL_W := 1280
const VIEW_W := 320
const PlayerScene := preload("res://scenes/player.tscn")
const EnemyScene := preload("res://scenes/enemy.tscn")

## x = posición del jugador que dispara la oleada; enemies = cuántos salen.
const WAVES := [
	{"x": 320, "enemies": 2},
	{"x": 600, "enemies": 3},
	{"x": 900, "enemies": 4},
	{"x": 1120, "enemies": 5},
]

var player: Player
var camera: Camera2D
var actors: Node2D
var hud: HUD
var score := 0
var wave_index := 0
var wave_active := false
var cam_max := float(LEVEL_W - VIEW_W / 2)
var finished := false


func _ready() -> void:
	add_child(Background.new())

	actors = Node2D.new()
	actors.y_sort_enabled = true
	add_child(actors)

	player = PlayerScene.instantiate()
	player.position = Vector2(60, 175)
	actors.add_child(player)

	camera = Camera2D.new()
	camera.position = Vector2(VIEW_W / 2.0, 112)
	add_child(camera)

	hud = HUD.new()
	add_child(hud)
	player.health_changed.connect(hud.set_health)
	player.died.connect(_on_player_died)
	hud.set_health(player.health, player.max_health)


func _process(_delta: float) -> void:
	if finished:
		if Input.is_action_just_pressed("ui_accept"):
			get_tree().reload_current_scene()
		return

	var cam_x := clampf(player.position.x, VIEW_W / 2.0, cam_max)
	camera.position.x = cam_x
	player.min_x = cam_x - VIEW_W / 2.0 + 10.0
	player.max_x = (cam_x + VIEW_W / 2.0 - 10.0) if wave_active else float(LEVEL_W - 10)

	if not wave_active and wave_index < WAVES.size() \
			and player.position.x >= WAVES[wave_index]["x"]:
		_start_wave(WAVES[wave_index])
	elif wave_active and get_tree().get_nodes_in_group("enemies").is_empty():
		_end_wave()


func _start_wave(wave: Dictionary) -> void:
	wave_active = true
	cam_max = float(wave["x"])
	hud.set_message("")
	for i in int(wave["enemies"]):
		var e: Enemy = EnemyScene.instantiate()
		var side := -1 if i % 2 == 0 else 1
		e.position = Vector2(cam_max + side * 190.0, randf_range(140.0, 210.0))
		e.died.connect(_on_enemy_died)
		actors.add_child(e)


func _end_wave() -> void:
	wave_active = false
	wave_index += 1
	cam_max = float(LEVEL_W - VIEW_W / 2)
	if wave_index >= WAVES.size():
		finished = true
		hud.set_message("STAGE CLEAR  (Enter)")
	else:
		hud.set_message("GO ->", true)


func _on_enemy_died(_f: Fighter) -> void:
	score += 100
	hud.set_score(score)


func _on_player_died(_f: Fighter) -> void:
	finished = true
	hud.set_message("GAME OVER  (Enter)")
