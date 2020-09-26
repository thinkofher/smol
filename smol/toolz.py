__all__ = ('unpack',)

def unpack(mapping, *keys):
    """Returns tuple containing values stored in given mapping
    under given keys. Can be used for unpacking multiple values
    from dictionary and assigning them to multiple variables
    at once.
    """
    return (
        tuple(mapping[key] for key in mapping)
        if len(keys) > 1
        else mapping[keys[0]]
    )


