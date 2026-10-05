extends Node2D
## Nivel principal: crea fondo, jugador, cámara, HUD y gestiona las oleadas de enemigos.
## Edita WAVES para cambiar el diseño del nivel.

const LEVEL_W := 1280
const VIEW_W := 320
const CAM_FOLLOW_NORMAL := 8.0
const CAM_FOLLOW_RECENTER := 1.4 ## Al terminar una oleada, la cámara vuelve a centrar al jugador despacio.
const CAM_FOLLOW_RAMP := 1.6 ## Cuánto sube la rapidez por segundo hasta volver a la normal.
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
var cam_follow := CAM_FOLLOW_NORMAL ## Rapidez con la que la cámara alcanza su objetivo (más baja = más suave).
var finished := false
var can_timer := 5.0
var rolling_can: RollingCan
var music: AudioStreamPlayer
var clear_active := false ## Secuencia de final de misión en marcha (el jugador ya no controla).
var cam_end_x := 0.0
var kills := 0


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

	music = Music.play(self, Music.STREET, -8.0, 2.0)

	# Apertura de la escena desde negro (viene del fundido a negro del menú).
	var fade_layer := CanvasLayer.new()
	fade_layer.layer = 100
	add_child(fade_layer)
	var black := ColorRect.new()
	black.color = Color.BLACK
	black.size = Vector2(VIEW_W, 224)
	black.mouse_filter = Control.MOUSE_FILTER_IGNORE
	fade_layer.add_child(black)
	var tw := create_tween()
	tw.tween_property(black, "color:a", 0.0, 1.2)
	tw.tween_callback(fade_layer.queue_free)


func _process(delta: float) -> void:
	if finished:
		if clear_active:
			# La cámara se centra despacio donde estaba el personaje y NO le sigue mientras sale andando.
			camera.position.x = maxf(camera.position.x, lerpf(camera.position.x, cam_end_x, 1.0 - exp(-CAM_FOLLOW_RECENTER * delta)))
			if player.position.x >= player.exit_x:
				player.visible = false
		elif Input.is_action_just_pressed("ui_accept"):
			get_tree().reload_current_scene()
		return

	var cam_target := clampf(player.position.x, VIEW_W / 2.0, cam_max)
	cam_follow = move_toward(cam_follow, CAM_FOLLOW_NORMAL, CAM_FOLLOW_RAMP * delta)
	# La cámara solo avanza: nunca vuelve hacia atrás (izquierda).
	var cam_x := maxf(camera.position.x, lerpf(camera.position.x, cam_target, 1.0 - exp(-cam_follow * delta)))
	camera.position.x = cam_x
	_update_can(delta)
	player.min_x = cam_x - VIEW_W / 2.0 + 10.0
	player.max_x = (cam_x + VIEW_W / 2.0 - 10.0) if wave_active else float(LEVEL_W - 10)

	if not wave_active and wave_index < WAVES.size() \
			and player.position.x >= WAVES[wave_index]["x"]:
		_start_wave(WAVES[wave_index])
	elif wave_active and get_tree().get_nodes_in_group("enemies").is_empty():
		_end_wave()


func _start_wave(wave: Dictionary) -> void:
	wave_active = true
	cam_follow = CAM_FOLLOW_NORMAL
	cam_max = float(wave["x"])
	hud.set_message("")
	for i in int(wave["enemies"]):
		var e: Enemy = EnemyScene.instantiate()
		var side := -1 if i % 2 == 0 else 1
		var lane_y := [150.0, 180.0, 208.0] # tres "calles" para que no salgan en fila
		e.position = Vector2(cam_max + side * (190.0 + float(i >> 1) * 40.0), float(lane_y[i % 3]) + randf_range(-4.0, 4.0))
		e.died.connect(_on_enemy_died)
		actors.add_child(e)


func _end_wave() -> void:
	wave_active = false
	cam_follow = CAM_FOLLOW_RECENTER
	wave_index += 1
	cam_max = float(LEVEL_W - VIEW_W / 2)
	if wave_index >= WAVES.size():
		finished = true
		_switch_music(Music.CLEAR)
		# Fin de misión: el jugador pierde el control, el personaje sale despacio por la derecha sin que la
		# cámara le siga, la pantalla se oscurece y se cuentan los puntos (scripts/results.gd).
		clear_active = true
		cam_end_x = maxf(camera.position.x, clampf(player.position.x, VIEW_W / 2.0, float(LEVEL_W - VIEW_W / 2)))
		player.max_x = 100000.0
		player.exit_x = cam_end_x + VIEW_W / 2.0 + 30.0
		player.auto_walk = true
		var results := Results.new()
		results.score = score
		results.kills = kills
		results.fade_started.connect(_on_results_fade)
		results.done.connect(_on_results_done)
		add_child(results)
		hud.set_message("")
	else:
		hud.set_message("GO ->", true)


## Corta la música del nivel y pone el tema especial del final (fanfarria o game over).
func _switch_music(path: String) -> void:
	if is_instance_valid(music):
		music.stop()
		music.queue_free()
	music = Music.play_once(self, path)


func _on_results_fade(duration: float) -> void:
	if is_instance_valid(music):
		var tw := create_tween()
		tw.tween_property(music, "volume_db", -60.0, duration)
		tw.tween_callback(music.stop)


func _on_results_done() -> void:
	get_tree().change_scene_to_file("res://scenes/menu.tscn")


func _on_enemy_died(_f: Fighter) -> void:
	score += 100
	kills += 1
	hud.set_score(score)


func _on_player_died(_f: Fighter) -> void:
	finished = true
	_switch_music(Music.GAME_OVER)
	hud.set_message("GAME OVER  (Enter)")


## Cada cierto tiempo aparece una lata tumbada que el viento empuja a rachas hacia abajo hasta salir de la pantalla.
func _update_can(delta: float) -> void:
	if is_instance_valid(rolling_can):
		if rolling_can.position.y > 240.0 or rolling_can.position.x < camera.position.x - VIEW_W / 2.0 - 30.0:
			rolling_can.queue_free()
		return
	can_timer -= delta
	if can_timer > 0.0:
		return
	can_timer = randf_range(8.0, 16.0)
	var c := RollingCan.new()
	# Se crea fuera de la pantalla (borde derecho) para que entre rodando, nunca aparezca de la nada.
	c.position = Vector2(camera.position.x + VIEW_W / 2.0 + 14.0, randf_range(132.0, 170.0))
	var sp := randf_range(10.0, 12.0)
	c.velocity = Vector2(-sp, sp) # rueda a 45º respecto de la horizontal, hacia abajo-izquierda
	actors.add_child(c)
	rolling_can = c
