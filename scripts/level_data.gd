class_name LevelData
extends Resource

@export var level_name: String = ""
@export var starting_runes: Array[RuneData] = []
@export var target_rune: RuneData = null

# Which operations are allowed in this level
@export var allow_merge: bool = true
@export var allow_attach: bool = true
