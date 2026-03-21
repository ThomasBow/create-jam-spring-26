extends Node2D

@export var level_data: LevelData

var active_runes: Array[RuneNode] = []

func _ready():
	if not level_data:
		return
	# Spawn starting runes
	var x_start := 80.0
	for rd in level_data.starting_runes:
		var rn := preload("res://scenes/rune_node.tscn").instantiate()
		add_child(rn)
		rn.position = Vector2(x_start, 200)
		rn.rune_data = rd.duplicate_rune()
		rn.rune_dropped.connect(_on_rune_dropped)
		active_runes.append(rn)
		x_start += 160

	# Show target (top-right area)
	_spawn_target()

func _spawn_target():
	var target_node := preload("res://scenes/rune_node.tscn").instantiate()
	add_child(target_node)
	target_node.position = Vector2(500, 60)
	target_node.rune_data = level_data.target_rune
	target_node.modulate = Color(1, 0.8, 0.3, 0.7)  # golden tint = "goal"
	# Disable interaction on the target
	target_node.get_node("Area2D").process_mode = Node.PROCESS_MODE_DISABLED

func _on_rune_dropped(rune: RuneNode):
	_check_win()

func _check_win():
	# Simple comparison: strokes must match target exactly
	# (In a real game, you'd want a smarter equivalence check)
	for rune in active_runes:
		if _strokes_match(rune.rune_data, level_data.target_rune):
			_on_level_won()
			return

func _strokes_match(a: RuneData, b: RuneData) -> bool:
	if a.strokes.size() != b.strokes.size():
		return false
	# Sorted comparison (order-independent)
	var sa := _serialize_strokes(a)
	var sb := _serialize_strokes(b)
	return sa == sb

func _serialize_strokes(rd: RuneData) -> Array:
	var out := []
	for stroke in rd.strokes:
		out.append([stroke[0], stroke[1]])
	out.sort()
	return out

func _on_level_won():
	print("Level complete!")
	# TODO: show win UI, load next level
