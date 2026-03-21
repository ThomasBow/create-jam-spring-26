extends Node2D

var points_this_stroke: Array[Vector2] = []
var all_strokes: Array[PackedVector2Array] = []
const GRID := 32  # snap grid in pixels
const SLAB := 128.0

func _input(event):
	if event is InputEventMouseButton and event.pressed:
		var snapped := (get_local_mouse_position() / GRID).floor() * GRID
		if event.button_index == MOUSE_BUTTON_LEFT:
			points_this_stroke.append(snapped / SLAB)  # normalize
			if points_this_stroke.size() == 2:
				var stroke := PackedVector2Array(points_this_stroke)
				all_strokes.append(stroke)
				points_this_stroke.clear()
				queue_redraw()
		elif event.button_index == MOUSE_BUTTON_RIGHT:
			# Undo last stroke
			if all_strokes.size() > 0:
				all_strokes.pop_back()
				queue_redraw()

func _draw():
	# Grid
	for gx in range(0, int(SLAB)+1, GRID):
		draw_line(Vector2(gx,0), Vector2(gx,SLAB), Color(0.3,0.3,0.3), 0.5)
	for gy in range(0, int(SLAB)+1, GRID):
		draw_line(Vector2(0,gy), Vector2(SLAB,gy), Color(0.3,0.3,0.3), 0.5)
	# Drawn strokes
	for stroke in all_strokes:
		draw_line(stroke[0]*SLAB, stroke[1]*SLAB, Color.WHITE, 2.5)
	# In-progress stroke
	if points_this_stroke.size() == 1:
		draw_circle(points_this_stroke[0]*SLAB, 4, Color.YELLOW)

func save_rune(rune_name: String):
	var rd := RuneData.new()
	rd.name = rune_name
	rd.strokes = all_strokes.duplicate(true)
	ResourceSaver.save(rd, "res://runes/" + rune_name + ".tres")
	print("Saved: ", rune_name)
