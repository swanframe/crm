# utilities/formatting.py
from decimal import Decimal, InvalidOperation

def _to_decimal(value):
    try:
        return Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        try:
            return Decimal(str(value))
        except:
            return None

def format_number_id(value, decimals=2):
    """
    Format angka ke style Indonesia/Europe:
    1234.5 -> "1.234,50"
    """
    d = _to_decimal(value)
    if d is None:
        return ''
    sign = '-' if d < 0 else ''
    d = abs(d)
    q = f"{d:,.{decimals}f}"        # -> "1,234.50" (US)
    # swap separators: ',' -> temporary, '.' -> ',', temp -> '.'
    s = q.replace(',', 'X').replace('.', ',').replace('X', '.')
    return sign + s

def format_currency_id(value, symbol='Rp '):
    s = format_number_id(value, 2)
    if s == '':
        return f"{symbol}0,00"
    return f"{symbol}{s}"

def parse_number_id(s):
    """
    Parse input numeric string in Indonesian format to float:
    '1.234,56' -> 1234.56
    Also accepts '1234.56' (US) and numeric types.
    Returns float or raises ValueError.
    """
    if s is None or s == '':
        raise ValueError("Empty number")
    if isinstance(s, (int, float, Decimal)):
        return float(s)
    t = str(s).strip()
    # remove thousand separators (.) and convert decimal separator to '.'
    t = t.replace('.', '').replace(',', '.')
    return float(t)