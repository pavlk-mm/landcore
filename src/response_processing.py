import re


_CLUSTER_LINE_PATTERN = re.compile(r"^\s*m\d+\s*\(.+\)(?:\s*,\s*m\d+\s*\(.+\))*\s*$")


def _is_cluster_line(line: str) -> bool:
	return _CLUSTER_LINE_PATTERN.match(line) is not None


def _is_final_output_only(response: str) -> bool:
	if response == "":
		return True

	non_empty_lines = [line for line in response.splitlines() if line.strip() != ""]
	if not non_empty_lines:
		return True

	if any("```" in line for line in non_empty_lines):
		return False

	return all(_is_cluster_line(line) for line in non_empty_lines)


def _longest_cluster_block(text: str) -> str | None:
	best_lines: list[str] = []
	current_lines: list[str] = []

	for line in text.splitlines():
		if _is_cluster_line(line):
			current_lines.append(line.rstrip())
		else:
			if len(current_lines) > len(best_lines):
				best_lines = current_lines
			current_lines = []

	if len(current_lines) > len(best_lines):
		best_lines = current_lines

	if not best_lines:
		return None

	return "\n".join(best_lines)


def extract_final_output(response: str) -> str:
	"""Extract final cluster-only output from a possibly verbose model response.

	If the response already contains only the expected cluster lines, the original
	string is returned unchanged.
	"""
	if _is_final_output_only(response):
		return response

	marker_pattern = re.compile(r"(?is)(?:\*\*\s*final\s+output\s*\*\*|final\s+output)\s*:?\s*")
	marker_match = marker_pattern.search(response)

	if marker_match is not None:
		after_marker = response[marker_match.end():]
		fence_match = re.search(r"(?is)```(?:[a-zA-Z0-9_+-]+)?\s*\n(.*?)\n```", after_marker)
		if fence_match is not None:
			candidate = fence_match.group(1).strip("\n")
			block = _longest_cluster_block(candidate)
			if block is not None:
				return block

		block = _longest_cluster_block(after_marker)
		if block is not None:
			return block

	for fence_match in re.finditer(r"(?is)```(?:[a-zA-Z0-9_+-]+)?\s*\n(.*?)\n```", response):
		candidate = fence_match.group(1).strip("\n")
		block = _longest_cluster_block(candidate)
		if block is not None:
			return block

	block = _longest_cluster_block(response)
	if block is not None:
		return block

	return response
