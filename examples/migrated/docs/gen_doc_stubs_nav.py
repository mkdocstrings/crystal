# Generate virtual doc files for the mkdocs site.
# You can also run this script directly to actually write out those files, as a preview.

import mkdocs_gen_files

# Get the documentation root object
root = mkdocs_gen_files.config["plugins"]["mkdocstrings"].get_handler("crystal").collector.root

# Start a navigation collection (to be filled as we go along)
nav = mkdocs_gen_files.Nav()

# For each type (e.g. "Foo::Bar")
for typ in root.walk_types():
    # Use the file name "Foo/Bar.md"
    filename = "/".join(typ.abs_id.split("::")) + ".md"
    # Make a file with the content "# ::: Foo::Bar\n"
    with mkdocs_gen_files.open(filename, "w") as f:
        print(f"# ::: {typ.abs_id}", file=f)

    # Link to the type itself when clicking the "edit" button on the page
    if typ.locations:
        mkdocs_gen_files.set_edit_path(filename, typ.locations[0].url)

    # Append to the nav: "    * [Bar](Foo/Bar.md)"
    nav[typ.abs_id.split("::")] = filename

# Append the nav to a "literate nav" file
with mkdocs_gen_files.open("SUMMARY.md", "a") as nav_file:
    nav_file.writelines(nav.build_literate_nav())
