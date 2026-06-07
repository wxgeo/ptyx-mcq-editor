import difflib


def track_cursor_1d(
    original_code: str, formatted_code: str, line_idx: int, col_idx: int, lenient: bool = False
) -> tuple[int, int]:
    """Tracks cursor position without mutating the AST."""
    lines = original_code.splitlines(keepends=True)
    if not (0 <= line_idx < len(lines)):
        if lenient:
            line_idx = max(0, min(line_idx, len(lines) - 1))
        else:
            raise ValueError("Line index out of bounds.")

    # 1. Convert 2D (line, col) to 1D absolute index
    # Ensure column doesn't exceed the specific line's length
    bounded_col = min(col_idx, len(lines[line_idx]))
    old_1d_idx = sum(len(lines[i]) for i in range(line_idx)) + bounded_col

    # 2. Diff the entire clean text
    matcher = difflib.SequenceMatcher(None, original_code, formatted_code)
    new_1d_idx = old_1d_idx

    # 3. Translate the 1D index using opcodes
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if i1 <= old_1d_idx < i2:
            if tag == "equal":
                new_1d_idx = j1 + (old_1d_idx - i1)
            elif tag in ("replace", "delete"):
                # Proportional mapping within mutated character blocks
                progress = (old_1d_idx - i1) / max(1, (i2 - i1))
                new_1d_idx = j1 + int(progress * (j2 - j1))
            break
        elif old_1d_idx >= i2:
            # Pushed forward by insertions prior to the cursor
            if tag in ("insert", "replace"):
                new_1d_idx = j2

    # 4. Convert 1D absolute index back to 2D (line, col)
    formatted_lines = formatted_code.splitlines(keepends=True)
    current_len = 0
    new_line_idx = 0

    for idx, line in enumerate(formatted_lines):
        if current_len + len(line) > new_1d_idx:
            new_line_idx = idx
            break
        current_len += len(line)
    else:
        # Fallback safeguard to EOF
        new_line_idx = max(0, len(formatted_lines) - 1)

    new_col_idx = new_1d_idx - current_len
    return new_line_idx, new_col_idx
