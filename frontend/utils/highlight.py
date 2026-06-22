import re


def highlight_text(
    text,
    query
):
    if not query:
        return text

    pattern = re.compile(
        re.escape(query),
        re.IGNORECASE
    )

    return pattern.sub(
        lambda match:
        f"<mark>{match.group(0)}</mark>",
        text
    )
