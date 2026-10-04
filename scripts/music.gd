class_name Music
extends RefCounted
## Utilidad para reproducir los temas en bucle (WAV sintetizado por tools/make_music.py).

const MENU := "res://assets/music/menu_theme.wav"
const STREET := "res://assets/music/street_theme.wav"
const CLEAR := "res://assets/music/stage_clear.wav"
const GAME_OVER := "res://assets/music/game_over.wav"


## Crea un AudioStreamPlayer hijo de `parent`, en bucle, que sube de volumen en `fade_in` segundos.
static func play(parent: Node, path: String, volume_db := -6.0, fade_in := 0.0) -> AudioStreamPlayer:
	var stream := load(path) as AudioStreamWAV
	stream.loop_mode = AudioStreamWAV.LOOP_FORWARD
	stream.loop_begin = 0
	stream.loop_end = stream.data.size() / 2 # 16 bits mono: 2 bytes por muestra
	var p := AudioStreamPlayer.new()
	p.stream = stream
	p.volume_db = -60.0 if fade_in > 0.0 else volume_db
	parent.add_child(p)
	p.play()
	if fade_in > 0.0:
		parent.create_tween().tween_property(p, "volume_db", volume_db, fade_in)
	return p


## Baja el volumen hasta silencio en `time` segundos.
static func fade_out(parent: Node, p: AudioStreamPlayer, time: float) -> void:
	if is_instance_valid(p):
		parent.create_tween().tween_property(p, "volume_db", -60.0, time)


## Reproduce un tema una sola vez (fanfarria de final, game over...).
static func play_once(parent: Node, path: String, volume_db := -4.0) -> AudioStreamPlayer:
	var p := AudioStreamPlayer.new()
	p.stream = load(path)
	p.volume_db = volume_db
	parent.add_child(p)
	p.play()
	return p
