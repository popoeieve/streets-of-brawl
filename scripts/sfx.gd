class_name Sfx
extends RefCounted
## Efectos de sonido (WAV sintetizados por tools/make_sfx.py). Uso: Sfx.play("hit")

const SOUNDS := {
	"swing": preload("res://assets/sfx/swing.wav"),
	"hit": preload("res://assets/sfx/hit.wav"),
	"hit_heavy": preload("res://assets/sfx/hit_heavy.wav"),
	"grunt_enemy": preload("res://assets/sfx/grunt_enemy.wav"),
	"grunt_player": preload("res://assets/sfx/grunt_player.wav"),
	"ko": preload("res://assets/sfx/ko.wav"),
	"thunder": preload("res://assets/sfx/thunder.wav"),
	"slot_tick": preload("res://assets/sfx/slot_tick.wav"),
	"slot_win": preload("res://assets/sfx/slot_win.wav"),
}


## Reproduce un efecto una vez (con un pequeño cambio de tono aleatorio) y se limpia solo al acabar.
static func play(sound: String, volume_db := 0.0, pitch := 1.0, jitter := 0.06) -> void:
	var tree := Engine.get_main_loop() as SceneTree
	if tree == null or not SOUNDS.has(sound):
		return
	var p := AudioStreamPlayer.new()
	p.stream = SOUNDS[sound]
	p.volume_db = volume_db
	p.pitch_scale = pitch * randf_range(1.0 - jitter, 1.0 + jitter)
	tree.root.add_child(p)
	p.finished.connect(p.queue_free)
	p.play()
