SCRAPERS = {}

def register(name: str):
    def decorator(cls):
        SCRAPERS[name] = cls
        return cls
    return decorator

