class_name HUD
extends CanvasLayer
## Panel superior estilo Streets of Rage: marco amarillo, retrato + barra de vida del jugador 1 (izquierda),
## hueco del jugador 2 (derecha, con el retrato a la derecha de su barra), especiales y tiempo de misión al centro
## y barra del jefe debajo. No hay cuenta atrás: el tiempo solo cuenta lo que llevas en la misión.

const FACE_P1 := preload("res://assets/ui/hud_face_p1.png")
const PANEL_H := 40.0
const BAR_W := 72.0
const BOSS_W := 184.0
const YELLOW := Color("f8d820")
const YELLOW_D := Color("a07808")
const NAVY := Color("0a0a1c")
const WHITE := Color("ececf0")
const RED := Color("d02020")
const ORANGE := Color("e87010")

var _canvas: _Canvas
var _score: Label
var _score2: Label
var _time: Label
var _spec_count: Label
var _spec_used: Label
var _spec_icon: Label
var _msg: Label
var _boss_name: Label
var _blink := false
var _hp := 1.0
var _boss_hp := 1.0
var _boss_on := false


class _Canvas extends Node2D:
	var hud: HUD

	func _draw() -> void:
		hud._paint(self)


func _ready() -> void:
	layer = 10
	_canvas = _Canvas.new()
	_canvas.hud = self
	add_child(_canvas)
	_score = _make_label(Vector2(40, 1), 110, HORIZONTAL_ALIGNMENT_LEFT)
	_score2 = _make_label(Vector2(170, 1), 110, HORIZONTAL_ALIGNMENT_RIGHT)
	_score2.text = "2UP-000000"
	_score2.modulate = Color(1, 1, 1, 0.4)
	_time = _make_label(Vector2(110, 1), 100, HORIZONTAL_ALIGNMENT_CENTER)
	_spec_icon = _make_label(Vector2(119, 13), 12, HORIZONTAL_ALIGNMENT_CENTER)
	_spec_icon.text = "S"
	_spec_icon.add_theme_color_override("font_color", Color("6a1008"))
	_spec_icon.add_theme_constant_override("outline_size", 0)
	_spec_icon.add_theme_font_size_override("font_size", 9)
	_spec_icon.position = Vector2(119, 12)
	_spec_count = _make_label(Vector2(134, 12), 24, HORIZONTAL_ALIGNMENT_LEFT)
	_spec_used = _make_label(Vector2(152, 12), 60, HORIZONTAL_ALIGNMENT_LEFT)
	_msg = _make_label(Vector2(0, 90), 320, HORIZONTAL_ALIGNMENT_CENTER)
	_msg.add_theme_font_size_override("font_size", 16)
	_msg.visible = false
	_boss_name = _make_label(Vector2(40, 24), 56, HORIZONTAL_ALIGNMENT_LEFT)
	hide_boss()
	set_score(0)
	set_time(0.0)
	set_specials(0, 0)


func _make_label(pos: Vector2, width: float, align: HorizontalAlignment) -> Label:
	var l := Label.new()
	l.position = pos
	l.size = Vector2(width, 12)
	l.horizontal_alignment = align
	l.add_theme_font_size_override("font_size", 10)
	l.add_theme_color_override("font_color", Color.WHITE)
	l.add_theme_color_override("font_outline_color", Color.BLACK)
	l.add_theme_constant_override("outline_size", 3)
	add_child(l)
	return l


func _bar(c: Node2D, x: float, y: float, w: float, frac: float, col: Color) -> void:
	c.draw_rect(Rect2(x - 1, y - 1, w + 2, 8), Color.BLACK)
	c.draw_rect(Rect2(x, y, w, 6), WHITE)
	c.draw_rect(Rect2(x, y + 3, w, 3), Color("b8b8c4")) # sombra de la parte vacía
	if frac > 0.0:
		var fw := maxf(1.0, w * frac)
		c.draw_rect(Rect2(x, y, fw, 6), col)
		c.draw_rect(Rect2(x, y, fw, 2), col.lightened(0.35))
		c.draw_rect(Rect2(x, y + 4, fw, 2), col.darkened(0.35))


func _paint(c: Node2D) -> void:
	c.draw_rect(Rect2(0, 0, 320, PANEL_H), NAVY)
	c.draw_rect(Rect2(1, 1, 318, PANEL_H - 2), YELLOW, false, 2.0)
	c.draw_rect(Rect2(3, 3, 314, PANEL_H - 6), YELLOW_D, false, 1.0)
	# retrato del jugador 1 (izquierda de su barra)
	c.draw_rect(Rect2(4, 4, 32, 32), Color.BLACK)
	c.draw_texture_rect(FACE_P1, Rect2(4, 4, 32, 32), false)
	c.draw_rect(Rect2(4, 4, 32, 32), YELLOW_D, false, 1.0)
	# retrato del jugador 2 (derecha de su barra): vacío, no hay segundo jugador
	c.draw_rect(Rect2(284, 4, 32, 32), Color("12122a"))
	c.draw_rect(Rect2(284, 4, 32, 32), Color("5a4a10"), false, 1.0)
	for i in 4:
		c.draw_rect(Rect2(292 + i * 4, 12 + i * 4, 4, 4), Color("2a2a4a"))
	_bar(c, 40, 14, BAR_W, _hp, RED)
	_bar(c, 208, 14, BAR_W, 0.0, RED)
	# icono de especial (estrella roja y amarilla)
	c.draw_rect(Rect2(118, 11, 14, 14), Color("8a1c10"))
	c.draw_rect(Rect2(119, 12, 12, 12), Color("f8d830"))
	c.draw_rect(Rect2(119, 12, 12, 2), Color("fff0a0"))
	for p in [Vector2(117, 10), Vector2(131, 10), Vector2(117, 24), Vector2(131, 24)]:
		c.draw_rect(Rect2(p.x, p.y, 2, 2), Color("e04820"))
	if _boss_on:
		_bar(c, 100, 28, BOSS_W, _boss_hp, ORANGE)


func set_health(hp: int, max_hp: int) -> void:
	_hp = clampf(float(hp) / float(max_hp), 0.0, 1.0)
	_canvas.queue_redraw()


func show_boss(title: String) -> void:
	_boss_name.text = title
	_boss_name.visible = true
	_boss_on = true
	_boss_hp = 1.0
	_canvas.queue_redraw()


func set_boss_health(hp: int, max_hp: int) -> void:
	_boss_hp = clampf(float(hp) / float(max_hp), 0.0, 1.0)
	_canvas.queue_redraw()


func hide_boss() -> void:
	_boss_name.visible = false
	_boss_on = false
	if _canvas:
		_canvas.queue_redraw()


func set_score(value: int) -> void:
	_score.text = "1UP-%06d" % value


## Tiempo total que llevas en la misión (mm:ss).
func set_time(seconds: float) -> void:
	_time.text = "TIME " + format_time(seconds)


## Especiales que te quedan y cuántos has usado ya.
func set_specials(left: int, used: int) -> void:
	_spec_count.text = "x%d" % left
	_spec_used.text = "USED %d" % used


static func format_time(seconds: float) -> String:
	var s := int(seconds)
	return "%02d:%02d" % [s / 60, s % 60]


func set_message(text: String, blink := false) -> void:
	_msg.text = text
	_blink = blink
	_msg.visible = text != ""


func _process(_delta: float) -> void:
	if _blink:
		_msg.visible = (Time.get_ticks_msec() / 400) % 2 == 0
