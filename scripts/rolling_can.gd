class_name RollingCan
extends Node2D
## Lata tumbada en el suelo (eje horizontal) que el viento empuja a rachas rodando hacia abajo-izquierda (decoración).
## Mientras avanza se anima el rodar: la etiqueta da la vuelta al cilindro. Orientación fija.
## La crea main.gd. Sprites: tools/make_can_roll.py -> assets/sprites/can_roll.png (8 frames de 13x6)

const SHEET := preload("res://assets/sprites/can_roll.png")
const FRAMES := 8
const FRAMES_PER_PX := 0.65 ## frames de giro por píxel recorrido (radio ~1.9 px -> 8 frames por vuelta).

var velocity := Vector2(-11.0, 11.0) ## px/s mientras sopla el viento (diagonal de 45º hacia abajo-izquierda).
var _moving := true
var _phase_t := 0.0
var _phase_len := 1.0
var _roll := 0.0
var _sprite: Sprite2D


func _ready() -> void:
	_sprite = Sprite2D.new()
	_sprite.texture = SHEET
	_sprite.hframes = FRAMES
	_sprite.centered = true
	_sprite.offset = Vector2(0, -3) # tumbada en el suelo: el origen del nodo es el punto de contacto
	add_child(_sprite)
	_new_phase(true)


func _new_phase(moving: bool) -> void:
	_moving = moving
	_phase_t = 0.0
	_phase_len = randf_range(0.8, 1.4) if moving else randf_range(3.0, 6.0)


func _process(delta: float) -> void:
	_phase_t += delta
	if _phase_t >= _phase_len:
		_new_phase(not _moving)
	if _moving:
		# racha: arranca y se frena suavemente
		var k := sin(PI * clampf(_phase_t / _phase_len, 0.0, 1.0))
		var step := velocity * k * 1.5 * delta
		position += step
		_roll += step.length() * FRAMES_PER_PX
		_sprite.frame = posmod(int(_roll), FRAMES)
	modulate = Background.night_tint(position.x)
	queue_redraw()


func _draw() -> void:
	draw_set_transform(Vector2(0, 0), 0.0, Vector2(1.0, 0.3))
	draw_circle(Vector2(0, 0), 4.5, Color(0, 0, 0, 0.25))
