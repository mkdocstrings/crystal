# Managing Python dependencies

There are countless ways to do it, but this document is nice for people not familiar with Python.

This assumes you have [Python][] installed, with `pip` available.

NOTE: Of course, you can just always run a bare `pip install` (without versions), but dependencies can break from under you with upgrades.

We suggest to *lock* all dependencies' versions (recursively), so the same ones are always used.

As an example, let's use the typical list of dependencies mentioned throughout this site.
Put these into the file `requirements.in`:

```toml
--8<-- "examples/migrated/docs/requirements.in"
```

Install the [pip-compile][] tool:

```console
$ pip install pip-tools
```

NOTE: This is needed only to manage the lock files; it won't be a permanent dependency.

And run it:

```
$ pip-compile -U requirements.in
```

(also run this whenever you want to upgrade the dependencies).

It creates the file `requirements.txt`, which is what you'll be using henceforth.

??? example "Example requirements.txt"
    ```toml
    --8<-- "examples/migrated/docs/requirements.txt"
    ```

Now anyone ([including automation](ci.md)) can install the exact same dependencies, and you can be sure the site will build as intended:

```console
$ pip install -r requirements.txt
```

TIP: If you'll be maintaining several projects with different dependencies, you might want to install packages in a [virtualenv][] (effectively localized just to this project's folder).

IMPORTANT: Both `requirements.in` and `requirements.txt` should be checked into source control.

Depending on the layout of project, you have many options where to store those files:

* at the root directory (more pragmatic);
* as `docs/requirements.txt` (because, after all, this is docs' requirements, but you'll get a side effect that this file will become part of the built site);
* any other location you come up with -- just use `pip install -r any_other_location/requirements.txt`.

[python]: https://www.python.org/
[pip-compile]: https://github.com/jazzband/pip-tools#example-usage-for-pip-compile
[virtualenv]: https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/#creating-a-virtual-environment
