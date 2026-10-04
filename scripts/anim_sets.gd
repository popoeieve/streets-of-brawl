# GENERADO por tools/build_atlas.py: no editar a mano (vuelve a ejecutar el script).
# Configuración de las hojas de sprites: una fila por animación.
class_name AnimSets

const SETS := {
	"mage": {
		"cols": 24, "rows": 2,
		"faces_right": false,
		"frame": Vector2i(64, 60), "feet": Vector2(32, 59),
		"anims": {
			"idle": {"row": 0, "n": 10, "fps": 8.0, "loop": true},
			"walk": {"row": 1, "n": 24, "fps": 20.0, "loop": true},
			"jump": {"row": 0, "n": 1, "fps": 0.0, "loop": false},
			"attack1": {"row": 0, "n": 2, "fps": 0.0, "loop": false, "impact": 1, "fx": "punch"},
			"attack2": {"row": 0, "n": 2, "fps": 0.0, "loop": false, "impact": 1, "fx": "punch"},
			"attack3": {"row": 0, "n": 2, "fps": 0.0, "loop": false, "impact": 1, "fx": "kick"},
			"hurt": {"row": 0, "n": 1, "fps": 0.0, "loop": false, "fx": "hurt"},
			"dead": {"row": 0, "n": 1, "fps": 0.0, "loop": false, "fx": "dead"},
		},
	},
	"hero": {
		"cols": 4, "rows": 5,
		"faces_right": false,
		"frame": Vector2i(96, 63), "feet": Vector2(48, 62),
		"anims": {
			"idle": {"row": 0, "n": 4, "fps": 6.0, "loop": true},
			"walk": {"row": 1, "n": 4, "fps": 8.0, "loop": true},
			"attack1": {"row": 2, "n": 3, "fps": 0.0, "loop": false, "impact": 1},
			"hurt": {"row": 3, "n": 2, "fps": 0.0, "loop": false},
			"dead": {"row": 4, "n": 2, "fps": 0.0, "loop": false},
			"attack2": {"alias": "attack1"},
			"attack3": {"alias": "attack1"},
			"jump": {"alias": "idle"},
		},
	},
	"brawler": {
		"cols": 10, "rows": 10,
		"faces_right": true,
		"frame": Vector2i(96, 63), "feet": Vector2(48, 62),
		"anims": {
			"idle": {"row": 0, "n": 4, "fps": 6.0, "loop": true},
			"walk": {"row": 1, "n": 10, "fps": 14.0, "loop": true},
			"jump": {"row": 2, "n": 4, "fps": 8.0, "loop": false},
			"attack1": {"row": 3, "n": 3, "fps": 0.0, "loop": false, "impact": 1},
			"attack2": {"row": 4, "n": 3, "fps": 0.0, "loop": false, "impact": 1},
			"attack3": {"row": 5, "n": 5, "fps": 0.0, "loop": false, "impact": 3},
			"hurt": {"row": 6, "n": 2, "fps": 0.0, "loop": false},
			"dead": {"row": 7, "n": 3, "fps": 0.0, "loop": false},
			"jump_kick": {"row": 8, "n": 3, "fps": 0.0, "loop": false, "impact": 1},
			"dive_kick": {"row": 9, "n": 5, "fps": 0.0, "loop": false, "impact": 3},
		},
	},
	"punk": {
		"cols": 4, "rows": 5,
		"faces_right": false,
		"frame": Vector2i(96, 63), "feet": Vector2(48, 62),
		"anims": {
			"idle": {"row": 0, "n": 4, "fps": 6.0, "loop": true},
			"walk": {"row": 1, "n": 4, "fps": 8.0, "loop": true},
			"attack1": {"row": 2, "n": 3, "fps": 0.0, "loop": false, "impact": 1},
			"hurt": {"row": 3, "n": 2, "fps": 0.0, "loop": false},
			"dead": {"row": 4, "n": 2, "fps": 0.0, "loop": false},
			"attack2": {"alias": "attack1"},
			"attack3": {"alias": "attack1"},
			"jump": {"alias": "idle"},
		},
	},
}
