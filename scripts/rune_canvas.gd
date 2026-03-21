class_name RuneCanvas
extends Node2D

var rune_data: RuneData = null

func refresh(data: RuneData):
	rune_data = data
	queue_redraw()

func _draw():
	if not rune_data:
		return
	for stroke in rune_data.strokes:
		if stroke.size() < 2:
			continue
		var a: Vector2 = stroke[0] * RuneNode.SLAB_SIZE
		var b: Vector2 = stroke[1] * RuneNode.SLAB_SIZE
		draw_line(a, b, Color(0.9, 0.85, 0.7), 2.5, true)
	# Draw the slab border
	draw_rect(Rect2(0, 0, RuneNode.SLAB_SIZE, RuneNode.SLAB_SIZE),
			  Color(0.6, 0.5, 0.3), false, 1.5)
