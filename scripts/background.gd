class_name Background
extends Node2D
## Fondo del nivel: calle andaluza de noche, estilo ochentero (assets/backgrounds/calle_tajo.png, 1280x224).
## Se regenera con tools/make_background.py. 1 píxel del fondo = 1 píxel del juego, igual que los personajes.

const TEXTURE := preload("res://assets/backgrounds/calle_tajo.png")

## x de las farolas encendidas (misma lista que LAMPS en tools/night_pass.py).
const LAMPS := [90, 330, 580, 820, 1020, 1240]
const NIGHT := Color(0.52, 0.56, 0.82) ## Tinte de los luchadores lejos de las farolas.
const LAMP_LIGHT := Color(1.0, 0.92, 0.75) ## Tinte bajo la luz de una farola.
const LAMP_RADIUS := 130.0


func _ready() -> void:
	z_index = -10
	var s := Sprite2D.new()
	s.texture = TEXTURE
	s.centered = false
	add_child(s)


## Color con el que se dibuja un luchador situado en x: oscuro de noche, más claro cerca de una farola.
static func night_tint(x: float) -> Color:
	var nearest := LAMP_RADIUS
	for lamp in LAMPS:
		nearest = minf(nearest, absf(x - float(lamp)))
	var k := 1.0 - nearest / LAMP_RADIUS
	return NIGHT.lerp(LAMP_LIGHT, k * k)
