import venusian


def entrypoint(cmds, args=None):
    if args is None:
        args = lambda _parser: None

    def _entrypoint(wrapped):
        def callback(scanner, name, ob):
            scanner.entrypoints.append((cmds, args, ob))

        venusian.attach(wrapped, callback, category="plugnparse")
        return wrapped

    return _entrypoint


def modifier(cmds):
    def _modifier(wrapped):
        def callback(scanner, name, ob):
            scanner.modifiers.append((cmds, ob))

        venusian.attach(wrapped, callback, category="plugnparse")
        return wrapped

    return _modifier
