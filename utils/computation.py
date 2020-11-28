import numbers


def is_number(num):
    try:
        if isinstance(float(num), numbers.Number):
            return True
        else:
            return False
    except:
        return False

