class_name Results
extends CanvasLayer
## Pantalla de resultados al acabar la misión: la pantalla se oscurece un poco, la puntuación sube desde 0
## de uno en uno con ruido de tragaperras (1 s exacto), parpadea al llegar al total y, 5 s después,
## fundido a negro. Emite `fade_started` (para parar la música) y `done` (cuando ya es negro).

signal fade_started(duration: float)
signal done

const DARK_ALPHA := 0.5 ## Cuánto se oscurece la pantalla (sin pasarse).
const DARKEN_TIME := 1.5
const COUNT_DELAY := 0.0 ## Espera antes de empezar a contar (0 = empieza en cuanto aparece la pantalla).
const COUNT_TIME := 1.0 ## La cuenta dura SIEMPRE exactamente 1 s, sea cual sea la puntuación.
const TICK_EVERY := 0.035 ## Cada cuánto suena el clic de tragaperras.
const BLINK_HOLD := 5.0 ## Segundos de parpadeo con la puntuación final antes del fundido.
const FADE_TIME := 1.5
const BLACK_HOLD := 1.0

var score := 0
var kills := 0
var mission_time := 0.0
var specials_used := 0
var _t := 0.0
var _t0_ms := -1 ## Instante (reloj real) en que empieza la cuenta.
var _count := 0.0
var _tick := 0.0
var _phase := 0 ## 0 = contando, 1 = parpadeo final, 2 = fundido a negro, 3 = negro (hecho)
var _phase_t := 0.0
var _dark: ColorRect
var _black: ColorRect
var _title: Label
var _info: Label
var _score: Label
var _extra: Array = []


func _ready() -> void:
	layer = 20
	_dark = _rect(Color(0, 0, 0, 0))
	_title = _label("STAGE CLEAR", 44.0, 16, Color("f5c542"))
	_info = _label("ENEMIES DEFEATED  %d" % kills, 78.0, 10, Color.WHITE)
	_label("SCORE", 100.0, 10, Color.WHITE)
	_score = _label("000000", 112.0, 20, Color.WHITE)
	_extra.append(_label("TIME  " + HUD.format_time(mission_time), 148.0, 10, Color.WHITE))
	_extra.append(_label("SPECIALS USED  %d" % specials_used, 162.0, 10, Color.WHITE))
	for l in _extra:
		l.visible = false
	_title.visible = false
	_info.visible = false
	_score.visible = false
	_black = _rect(Color(0, 0, 0, 0))


func _rect(c: Color) -> ColorRect:
	var r := ColorRect.new()
	r.color = c
	r.size = Vector2(320, 224)
	r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(r)
	return r


func _label(text: String, y: float, size: int, color: Color) -> Label:
	var l := Label.new()
	l.text = text
	l.position = Vector2(0, y)
	l.size = Vector2(320, 28)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", color)
	l.add_theme_color_override("font_outline_color", Color.BLACK)
	l.add_theme_constant_override("outline_size", 4)
	add_child(l)
	return l


func _process(delta: float) -> void:
	_t += delta
	_phase_t += delta
	match _phase:
		0:
			_dark.color.a = minf(_t / DARKEN_TIME, 1.0) * DARK_ALPHA
			if _t >= COUNT_DELAY:
				_title.visible = true
				_info.visible = true
				_score.visible = true
				for l in _extra:
					l.visible = true
				# Cuenta con el reloj real (no con la suma de deltas): dura COUNT_TIME segundos exactos.
				if _t0_ms < 0:
					_t0_ms = Time.get_ticks_msec()
				var elapsed := float(Time.get_ticks_msec() - _t0_ms) / 1000.0
				_count = float(score) * clampf(elapsed / COUNT_TIME, 0.0, 1.0)
				_score.text = "%06d" % int(_count)
				_tick -= delta
				if _tick <= 0.0 and int(_count) < score:
					_tick = TICK_EVERY
					Sfx.play("slot_tick", -4.0, 1.0 + 0.5 * (_count / maxf(float(score), 1.0)), 0.04)
				if elapsed >= COUNT_TIME:
					print("Cuenta de puntos terminada en %.2f s" % elapsed)
					_score.text = "%06d" % score
					_phase = 1
					_phase_t = 0.0
					Sfx.play("slot_win", -2.0, 1.0, 0.0)
		1:
			var on := int(_phase_t * 4.0) % 2 == 0 # parpadeo
			_score.visible = on
			_score.add_theme_color_override("font_color", Color("f5c542"))
			if _phase_t >= BLINK_HOLD:
				_score.visible = true
				_phase = 2
				_phase_t = 0.0
				fade_started.emit(FADE_TIME)
		2:
			_black.color.a = clampf(_phase_t / FADE_TIME, 0.0, 1.0)
			if _phase_t >= FADE_TIME:
				_phase = 3
				_phase_t = 0.0
		3:
			if _phase_t >= BLACK_HOLD:
				set_process(false)
				done.emit()
