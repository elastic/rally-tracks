class ReproducibleClock:
    def __init__(self, start):
        self.now = start

    def __call__(self, *args, **kwargs):
        return self.now
