* Make better error messages. Probably should do this TDD-style. But, the
  current errors suck and be made friendlier.

  Turns out the error messages for argparse type parsing suck, so let's not use
  those.

  Abort early when trying to do something that will fail. e.g. invalid hash
  methods, modifying YAML config.
