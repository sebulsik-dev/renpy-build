from renpybuild.context import Context
from renpybuild.task import task

from pathlib import Path

@task(kind="arch", platforms="all")
def clean(c: Context):
    c.clean()


@task(kind="host", platforms="all", always=True)
def gen_static(c: Context):

    c.chdir("{{ renpy }}")
    c.env("RENPY_DEPS_INSTALL", "/usr::/usr/lib/x86_64-linux-gnu/")
    c.env("RENPY_REGENERATE_CYTHON", "1")
    c.run("uv --project renpy run setup.py generate")


@task(kind="arch", platforms="all", always=True)
def build(c: Context):

    c.env("CFLAGS", """{{ CFLAGS }} -I{{ renpy }}/src -I{{ renpy }}/tmp/gen """)
    c.env("CXXFLAGS", """{{ CXXFLAGS }} -I{{ renpy }}/src -I{{ renpy }}/tmp/gen """)

    modules: list[str] = []
    source_to_module: dict[Path, str] = {}

    def read_setup(dn, suffix=""):
        with open(dn / ("Setup" + suffix)) as f:
            for line in f:
                line = line.partition("#")[0].strip()
                if not line:
                    continue

                parts = line.split()
                module_name, *sources = parts
                modules.append(module_name)

                for p in sources:
                    source_to_module[dn / p] = module_name

    read_setup(c.renpy / "src")
    read_setup(c.root / "extensions")

    if c.platform == "android":
        read_setup(c.path("{{ pytmp }}/pyjnius"))

    if c.platform == "ios" or c.platform == "mac":
        read_setup(c.path("{{ install }}/pyobjus"))

    if c.platform == "windows" or c.platform == "mac" or c.platform == "linux":
        read_setup(c.renpy / "src", ".tfd")

    if c.platform == "web":
        read_setup(c.path("{{ install }}/emscripten_pyx"))

    read_setup(c.path("{{ source }}/brotli"))

    objects: list[str] = []

    with c.run_group() as g:
        for source, module_name in source_to_module.items():
            name = source.stem
            ext = source.suffix[1:]

            object = f"{name}.o"
            if object in objects:
                continue

            objects.append(object)

            c.var("src", source)
            c.var("object", object)

            mangled = module_name.replace(".", "_")
            short = module_name.rpartition(".")[-1]
            c.var("pyinit_define", f"-DPyInit_{short}=PyInit_{mangled}")

            if ext == "c":
                g.run("{{ CC }} {{ CFLAGS }} {{ pyinit_define }} -c {{ src }} -o {{ object }}")
            else:
                g.run("{{ CXX }} {{ CXXFLAGS }} {{ pyinit_define }} -c {{ src }} -o {{ object }}")

        c.generate("{{ runtime }}/librenpy_inittab.c", "inittab.c", modules=modules)
        g.run("{{ CC }} {{ CFLAGS }} -c inittab.c -o inittab.o")
        objects.append("inittab.o")

    c.var("objects", " ".join(objects))

    if c.platform in ("mac", "ios"):
        c.run("{{ AR }} --format=darwin crs librenpy.a {{ objects }}")
    else:
        c.run("{{ AR }} crs librenpy.a {{ objects }}")

    c.copy("librenpy.a", "{{ install }}/lib/librenpy.a")
