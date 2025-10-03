def to_bytes(data, length=1):
    if isinstance(data, int):
        return data.to_bytes(length, byteorder="big")
    elif isinstance(data, str):
        return data.encode("utf-8")
    elif isinstance(data, bytes):
        return data
    raise TypeError(f"No se puede convertir el tipo {type(data)} a bytes")
