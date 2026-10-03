class_name Background
extends Node2D
## Fondo de ciudad nocturna dibujado por código (placeholder).

const LEVEL_W := 1280


func _ready() -> void:
	z_index = -10


func _draw() -> void:
	for i in 9:
		draw_rect(Rect2(0, i * 14, LEVEL_W, 14), Color.from_hsv(0.75, 0.6, 0.22 + i * 0.03))
	var rng := RandomNumberGenerator.new()
	rng.seed = 1991
	var x := 0
	while x < LEVEL_W:
		var bw := rng.randi_range(30, 60)
		var bh := rng.randi_range(40, 90)
		draw_rect(Rect2(x, 120 - bh, bw, bh), Color(0.1, 0.08, 0.2))
		for wy in range(120 - bh + 6, 110, 10):
			for wx in range(x + 5, x + bw - 6, 9):
				if rng.randf() > 0.5:
					draw_rect(Rect2(wx, wy, 4, 5), Color("f5c542"))
		x += bw + rng.randi_range(0, 6)
	draw_rect(Rect2(0, 120, LEVEL_W, 14), Color("5a5a6a")) # acera
	draw_rect(Rect2(0, 132, LEVEL_W, 2), Color("3a3a48")) # bordillo
	draw_rect(Rect2(0, 134, LEVEL_W, 90), Color("2e2e3a")) # calle
	for lx in range(0, LEVEL_W, 40):
		draw_rect(Rect2(lx, 176, 20, 2), Color("6e6e7e"))
