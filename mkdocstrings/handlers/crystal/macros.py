def define_env(env):
    """Pluglet for mkdocs-macros plugin."""

    env.variables["crystal"] = (
        env.conf["plugins"]["mkdocstrings"].get_handler("crystal").collector.root
    )
