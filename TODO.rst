* Make better error messages. Probably should do this TDD-style. But, the
  current errors suck and be made friendlier.

  What kind of errors are there? invalid json is a thing and schemata should be
  checked for sanity too.

  Man it's a pain validating every bit of user input though. Maybe argparse
  types can help. Then the only validation would be for config files.

  Abort early when trying to do something that will fail. e.g. invalid hash
  methods, modifying YAML config.

  Idea: use decorators on action methods to indicate what kind of config it
  requires.

  * Don't show tracebacks by default. There's something for this stashed.

  * Catch KeyboardInterrupt.
