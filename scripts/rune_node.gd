class_name RuneNode
extends Node2D

const SLAB_SIZE := 128.0

@onready var canvas: Node2D = $Canvas
@onready var slab: ColorRect = $ColorRect

@export var rune_data: RuneData:
	set(v):
		rune_data = v
		if canvas:
			canvas.queue_redraw()  # triggers _draw()

var is_dragging := false
var drag_offset := Vector2.ZERO

# Called when this rune is connected to another on an edge
# direction: Vector2i — e.g. Vector2i(1,0) = right edge
var connections: Dictionary = {}  # direction → RuneNode

signal rune_dropped(rune_node: RuneNode)
signal merge_requested(rune_a: RuneNode, rune_b: RuneNode)

func _ready():
	$Area2D.input_event.connect(_on_input_event)
	canvas.draw.connect(_draw_strokes)

func _draw_strokes():
	if not rune_data:
		return
	for stroke in rune_data.strokes:
		if stroke.size() < 2:
			continue
		# stroke points are normalized 0..1, scale to SLAB_SIZE
		var a: Vector2 = stroke[0] * SLAB_SIZE
		var b: Vector2 = stroke[1] * SLAB_SIZE
		canvas.draw_line(a, b, Color.WHITE, 2.0, true)

func _on_input_event(_viewport, event: InputEvent, _shape_idx):
	if event is InputEventMouseButton:
		if event.button_index == MOUSE_BUTTON_LEFT:
			is_dragging = event.pressed
			drag_offset = global_position - get_global_mouse_position()

func _process(_delta):
	if is_dragging:
		global_position = get_global_mouse_position() + drag_offset

static func merge(a: RuneData, b: RuneData) -> RuneData:
	var result := RuneData.new()
	result.name = a.name + "+" + b.name
	# Copy all strokes from both runes
	for stroke in a.strokes:
		result.strokes.append(stroke.duplicate())
	for stroke in b.strokes:
		result.strokes.append(stroke.duplicate())
	return result
	
static func attach(a: RuneData, b: RuneData, direction: Vector2i) -> RuneData:
	var result := RuneData.new()
	result.name = a.name + "|" + b.name
	var offset := Vector2(direction)  # e.g. (1,0) or (0,1)
	for stroke in a.strokes:
		result.strokes.append(stroke.duplicate())
	for stroke in b.strokes:
		var shifted := PackedVector2Array()
		for pt in stroke:
			shifted.append(pt + offset)
		result.strokes.append(shifted)
	return result
