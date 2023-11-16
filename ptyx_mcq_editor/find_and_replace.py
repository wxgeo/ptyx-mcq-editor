def replace_text(
    text: str, find: str, replace: str, *, is_regex: bool, whole_words: bool, caseless: bool
) -> str:
    return text.replace(find, replace)
