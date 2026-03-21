class_name RuneData
extends Resource

# A rune is a square "slab" containing a list of strokes.
# Each stroke is two Vector2 points (start, end) in local space
# where (0,0) is top-left and (1,1) is bottom-right (normalized).

@export var name: String = "unnamed"
@export var strokes: Array[PackedVector2Array] = []

# Returns a deep copy so mutations don't affect the original
func duplicate_rune() -> RuneData:
	var copy := RuneData.new()
	copy.name = name
	for stroke in strokes:
		copy.strokes.append(stroke.duplicate())
	return copy
