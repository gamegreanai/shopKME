from django import template
import re

register = template.Library()


@register.filter(name="mask_phone")
def mask_phone(value: str) -> str:
    """
    Mask a Thai 10-digit phone number into the pattern 099-99X-XX99.
    - Keep first 5 digits as 099-99
    - Mask digit 6 as X
    - Mask digits 7-8 as XX
    - Keep last 2 digits visible

    Fallback for non-10 digits: keep first 3 and last 2, mask the middle with Xs
    and separate segments with hyphens when reasonable.
    """
    if not value:
        return ""

    s = str(value)
    digits = re.sub(r"\D", "", s)

    if len(digits) == 10:
        a = digits[:3]
        b = digits[3:6]
        c = digits[6:]

        # b = D4 D5 D6  -> show D4 D5 X
        b_mask = (b[:2] + "X") if len(b) == 3 else (b + "X")

        # c = D7 D8 D9 D10 -> mask D7 D8, show D9 D10
        if len(c) >= 4:
            c_mask = "XX" + c[-2:]
        elif len(c) == 3:
            c_mask = "XX" + c[-1]
        elif len(c) == 2:
            c_mask = "X" + c[-1]
        else:
            c_mask = "X"

        return f"{a}-{b_mask}-{c_mask}"

    # Fallback for non-10 digits
    if len(digits) >= 5:
        first = digits[:3]
        last = digits[-2:]
        mid_len = len(digits) - 5
        mid_mask = "X" * mid_len
        return f"{first}-{mid_mask}{last if mid_len == 0 else ''}-{last}" if mid_len else f"{first}-{last}"

    # Very short numbers: mask all
    return "X" * len(digits)
