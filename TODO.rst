 * Make better error messages. Probably should do this TDD-style. But, the
   current errors suck and be made friendlier.

   What kind of errors are there? invalid json is a thing and schemata should
   be checked for sanity too.

   Man it's a pain validating every bit of user input though. Maybe argparse
   types can help. Then the only validation would be for config files.

   Abort early when trying to do something that will fail. e.g. invalid hash
   methods, modifying YAML config.

 * ssh-agent handling? I'm no longer convinced it's a good idea actually. It
   kind of goes against the idea of 'no persistence', and your ssh key should
   be passworded anyway, ...

   ssh-agent also isn't a particularly secure protocol, but one probably
   wouldn't want to run passacre on an untrusted system anyway.

 * Factor out some common arguments, maybe. I think I've already done this a
   bit. Necessary to do it more? Password prompts already got factored out, at
   least, and site hashing should probably be next.
