class_name HUD
extends CanvasLayer

var _bar_fill: ColorRect
var _score: Label
var _msg: Label
var _blink := false
var _bar_w := 80.0


func _ready() -> void:
	layer = 10
	var back := ColorRect.new()
	back.color = Color.BLACK
	back.position = Vector2(7, 7)
	back.size = Vector2(_bar_w + 2, 8)
	add_child(back)
	_bar_fill = ColorRect.new()
	_bar_fill.color = Color("f5c542")
	_bar_fill.position = Vector2(8, 8)
	_bar_fill.size = Vector2(_bar_w, 6)
	add_child(_bar_fill)
	_score = _make_label(Vector2(100, 4), 120, HORIZONTAL_ALIGNMENT_LEFT)
	_msg = _make_label(Vector2(0, 90), 320, HORIZONTAL_ALIGNMENT_CENTER)
	_msg.add_theme_font_size_override("font_size", 16)
	_msg.visible = false
	set_score(0)


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


func set_health(hp: int, max_hp: int) -> void:
	_bar_fill.size.x = _bar_w * float(hp) / float(max_hp)


func set_score(value: int) -> void:
	_score.text = "SCORE %06d" % value


func set_message(text: String, blink := false) -> void:
	_msg.text = text
	_blink = blink
	_msg.visible = text != ""


func _process(_delta: float) -> void:
	if _blink:
		_msg.visible = (Time.get_ticks_msec() / 400) % 2 == 0
