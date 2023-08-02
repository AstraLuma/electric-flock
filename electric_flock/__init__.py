from collections.abc import Iterable, Iterator
from dataclasses import dataclass
import mimetypes
import random
from pathlib import Path
import time
import threading

from flask import Flask, session, render_template

from .flock import Sheep, Flock


# FIXME: Take as argument
# SHEEP_ROOT = '/run/user/1000/gvfs/smb-share:server=bakery.dorper-climb.ts.net,share=electric-sheep/ts'
# SHEEP_ROOT = '/tmp/sheep'
SHEEP_ROOT = Path.cwd() / 'segments'

mimetypes.add_type('video/mp4', '.mp4')

app = Flask(
    __name__,
    static_folder=SHEEP_ROOT,
    static_url_path='/sheep',
)
app.config.from_mapping(
    SECRET_KEY="sekrit",
)
app.config.from_prefixed_env()


flock = Flock()


def load_sheep():
    flock.discard_missing()
    flock.update(Path(app.static_folder).glob('*.mp4'))


load_sheep()


def flock_traversal() -> Iterator[Sheep]:
    """
    Random walks the sheep graph.

    Each loop is one step.
    """
    global flock

    rand = random.SystemRandom()

    def should_i(chance: float) -> bool:
        """
        Randomly decides if an action should be taken, based on the given
        probability.
        """
        return rand.random() < chance

    CHANCE_OF_JUMP = 0.02  # Chance of breaking the chain
    CHANCE_OF_LOOP = 0.90  # Chance of looping, if there's a loop option
    sheep = rand.choice([*flock])
    yield sheep
    while True:
        nexts = {*flock.find_next_sheep(sheep)}
        loops = [s for s in nexts if s.is_loop]
        outs = [s for s in nexts if not s.is_loop]
        # Pick a next item
        if should_i(CHANCE_OF_JUMP):
            # Ignore the chain and pick something new at random
            sheep = rand.choice([*flock.iter_loops()])
        elif loops and should_i(CHANCE_OF_LOOP):
            # Just keep looping
            sheep = rand.choice(loops)
        elif outs:
            # Transition to another
            sheep = rand.choice(outs)
        else:
            # Dead end, start over
            # Only jump to a loop, not a transitory
            sheep = rand.choice([*flock.iter_loops()])
        yield sheep


# List of sheep in the order they were played
sheep_list: list[tuple[int, Sheep]] = []


def flock_walker():
    """
    Thread to walk the graph in a timely fasion.
    """
    global sheep_list
    for seq, sheep in enumerate(flock_traversal()):
        sheep_list.append((seq, sheep))
        if len(sheep_list) > 10:
            sheep_list.pop(0)
        if seq % 100 == 0:
            # Trigger sheep reload
            threading.Thread(target=load_sheep,
                             name="load_sheep", daemon=True).start()
        time.sleep(sheep.length)


threading.Thread(target=flock_walker, name='flock_walker', daemon=True).start()


@app.route('/')
def index():
    return render_template('index.html')


@app.route("/stream.m3u8")
def get_next_chunk():
    return (
        render_template('chunk.m3u8',
                        flock=[s for _, s in sheep_list],
                        first_seq=min(i for i, _ in sheep_list)
                        ),
        {'Content-Type': 'application/vnd.apple.mpegurl'},
    )


@app.cli.command("graph")
def graph():
    """
    Produce a graphviz graph of all the sheep in the current flock.
    """
    print("digraph {")
    for sheep in flock:
        print(f"\t{sheep.start} -> {sheep.end} [label={sheep.ident!r}]")

    print("}")
