extends Node2D
## Menú de inicio: retrato pixel-art a media pantalla, título MYTHIC STREETS y botón START con rayos.
## Arte generado por tools/make_menu_art.py -> assets/ui/. Empieza la misión 1 (calle Tajo): scenes/main.tscn.

const MAIN_SCENE := "res://scenes/main.tscn"
const PORTRAIT := preload("res://assets/ui/portrait.png")
const TITLE := preload("res://assets/ui/title.png")
const BUTTON := preload("res://assets/ui/button.png")
const BTN_POS := Vector2(168, 128)
const BTN_SIZE := Vector2(144, 40)
const FADE_OUT := 1.0 ## segundos en fundirse a negro tras pulsar START.
const BLACK_HOLD := 1.0 ## segundos que se queda en negro antes de abrir la calle Tajo.

var _fx: Node2D
var _button: Sprite2D
var _title: Sprite2D
var _t := 0.0
var _flash := 0.0 ## 0..1: destello blanco de pantalla.
var _bolt_timer := 1.2
var _big_bolt: PackedVector2Array = PackedVector2Array()
var _big_bolt_t := 0.0
var _arcs: Array = [] ## arcos pequeños alrededor del botón (se regeneran a menudo).
var _arc_timer := 0.0
var _starting := false
var _start_t := 0.0
var _fade: ColorRect
var _music: AudioStreamPlayer


func _ready() -> void:
	var portrait := Sprite2D.new()
	portrait.texture = PORTRAIT
	portrait.centered = false
	add_child(portrait)

	_title = Sprite2D.new()
	_title.texture = TITLE
	_title.centered = false
	_title.position = Vector2(roundf((320.0 - TITLE.get_width()) / 2.0), 4)
	add_child(_title)

	_button = Sprite2D.new()
	_button.texture = BUTTON
	_button.hframes = 2
	_button.centered = false
	_button.position = BTN_POS
	add_child(_button)

	_fx = Node2D.new()
	_fx.draw.connect(_draw_fx)
	add_child(_fx)

	_music = Music.play(self, Music.MENU, -6.0, 1.5)

	var layer := CanvasLayer.new()
	layer.layer = 50
	add_child(layer)
	_fade = ColorRect.new()
	_fade.color = Color(0, 0, 0, 0)
	_fade.size = Vector2(320, 224)
	_fade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	layer.add_child(_fade)


func _bolt(from: Vector2, to: Vector2, segments: int, jitter: float) -> PackedVector2Array:
	var pts := PackedVector2Array([from])
	var dir := to - from
	var perp := Vector2(-dir.y, dir.x).normalized()
	for i in range(1, segments):
		var p := from + dir * (float(i) / float(segments))
		pts.append((p + perp * randf_range(-jitter, jitter)).round())
	pts.append(to)
	return pts


func _process(delta: float) -> void:
	_t += delta
	_flash = maxf(0.0, _flash - delta * 3.0)
	_big_bolt_t = maxf(0.0, _big_bolt_t - delta)

	if not _starting:
		_bolt_timer -= delta
		if _bolt_timer <= 0.0:
			_bolt_timer = randf_range(1.8, 3.6)
			var x := randf_range(180.0, 300.0)
			_big_bolt = _bolt(Vector2(x, -2), Vector2(randf_range(215.0, 265.0), BTN_POS.y - 2.0), 9, 12.0)
			_big_bolt_t = 0.22
			_flash = 0.45
		var hover := Rect2(BTN_POS, BTN_SIZE).has_point(get_local_mouse_position())
		_button.frame = 1 if (hover or int(_t * 2.5) % 2 == 0) else 0
		if Input.is_action_just_pressed("ui_accept") or Input.is_action_just_pressed("attack"):
			_start()
	else:
		_start_t += delta
		_button.frame = int(_start_t * 20.0) % 2 if _start_t < 0.5 else 1
		_fade.color.a = clampf(_start_t / FADE_OUT, 0.0, 1.0) # fundido a negro
		if _start_t > FADE_OUT + BLACK_HOLD:
			get_tree().change_scene_to_file(MAIN_SCENE)
			return

	_arc_timer -= delta
	if _arc_timer <= 0.0:
		_arc_timer = 0.06
		_arcs.clear()
		var c := BTN_POS + BTN_SIZE / 2.0
		for i in 3:
			var ang := randf() * TAU
			var a := c + Vector2(cos(ang) * BTN_SIZE.x * 0.55, sin(ang) * BTN_SIZE.y * 0.7)
			var b := a + Vector2(randf_range(-20.0, 20.0), randf_range(-16.0, 16.0))
			_arcs.append(_bolt(a, b, 4, 4.0))
	_title.modulate = Color(1.6, 1.6, 1.8) if (_big_bolt_t > 0.1 or _flash > 0.35) else Color.WHITE
	queue_redraw()
	_fx.queue_redraw()


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		if Rect2(BTN_POS, BTN_SIZE).has_point(get_local_mouse_position()):
			_start()


func _start() -> void:
	if _starting:
		return
	_starting = true
	_start_t = 0.0
	Music.fade_out(self, _music, FADE_OUT + 0.5)
	Sfx.play("thunder", 0.0, 1.0, 0.0) # el rayo retumba al pulsar START
	_flash = 1.0
	var c := BTN_POS + BTN_SIZE / 2.0
	_big_bolt = _bolt(Vector2(c.x, -2), c, 10, 14.0)
	_big_bolt_t = 0.5


func _draw() -> void:
	# Fondo: degradado nocturno violeta-azul por bandas, con nubes de tormenta sencillas.
	for y in range(0, 224, 4):
		var t := float(y) / 224.0
		draw_rect(Rect2(0, y, 320, 4), Color(0.06 + 0.12 * t, 0.04 + 0.05 * t, 0.16 + 0.12 * t))


func _draw_bolt(pts: PackedVector2Array, glow: Color, core: Color) -> void:
	if pts.size() < 2:
		return
	_fx.draw_polyline(pts, glow, 3.0)
	_fx.draw_polyline(pts, core, 1.0)


func _draw_fx() -> void:
	var glow := Color(0.45, 0.65, 1.0, 0.45)
	var core := Color(0.95, 0.98, 1.0)
	for a in _arcs:
		_draw_bolt(a, Color(0.5, 0.7, 1.0, 0.35), core)
	if _big_bolt_t > 0.0:
		_draw_bolt(_big_bolt, glow, core)
		# ramal secundario
		if _big_bolt.size() > 4:
			var o := _big_bolt[3]
			_draw_bolt(_bolt(o, o + Vector2(-26, 34), 4, 5.0), Color(0.45, 0.65, 1.0, 0.3), core)
	if _flash > 0.0:
		_fx.draw_rect(Rect2(0, 0, 320, 224), Color(0.8, 0.88, 1.0, _flash * 0.35))
