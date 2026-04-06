"""Simple weather tool for function-calling demos.

This module provides a deterministic, fake `get_weather` function suitable
for use as a function-callable tool in exercises and tests. It does not
call any external APIs and returns JSON-serializable data.
"""
from typing import Dict, Any

__all__ = ["get_weather"]


def get_weather(location: str, unit: str = "celsius") -> Dict[str, Any]:
	"""Return a simple deterministic fake weather for a location.

	Args:
		location: City or place name.
		unit: Desired temperature unit: "celsius", "fahrenheit", or "kelvin".

	Returns:
		A dictionary with keys: `location`, `temperature`, `unit`, `description`.

	This function is intentionally simple and deterministic so it can be used
	in tests or function-calling demos without network access.
	"""
	if not location:
		location = "Unknown"

	unit_pref = (unit or "celsius").strip().lower()

	# Deterministic pseudo-temperature based on location characters
	temp_c = (sum(ord(ch) for ch in location) % 25) + 5

	if unit_pref in ("c", "celsius"):
		temperature = round(temp_c, 1)
		out_unit = "celsius"
	elif unit_pref in ("f", "fahrenheit"):
		temperature = round(temp_c * 9.0 / 5.0 + 32.0, 1)
		out_unit = "fahrenheit"
	elif unit_pref in ("k", "kelvin"):
		temperature = round(temp_c + 273.15, 2)
		out_unit = "kelvin"
	else:
		# Fallback to celsius for unknown unit strings
		temperature = round(temp_c, 1)
		out_unit = "celsius"

	# Simple description based on Celsius value
	if temp_c >= 30:
		description = "hot"
	elif temp_c >= 20:
		description = "warm"
	elif temp_c >= 10:
		description = "mild"
	elif temp_c >= 0:
		description = "cold"
	else:
		description = "freezing"

	return {
		"location": location,
		"temperature": temperature,
		"unit": out_unit,
		"description": description,
	}
