from collections.abc import Iterable
from dataclasses import dataclass
import mimetypes
import random
from pathlib import Path
import time
import threading

from flask import Flask, session, render_template


@dataclass
class Sheep:
    path: Path
    gen: int
    ident: int
    start: int
    end: int
    # All sheep seem to be 5 seconds?
    length: int = 5


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

all_sheep: list[Sheep]
next_sheep_index: dict[int, list[Sheep]]


def load_sheep():
    global all_sheep, next_sheep_index
    all_sheep = [
        Sheep(p, *map(int, p.stem.split('=')))
        for p in Path(app.static_folder).glob('*.mp4')
    ]

    next_sheep_index = {
        s.ident: []
        for s in all_sheep
    }
    # Technically, there's a race condition here, but if it gets hit,
    # it'll just cause a chain break
    for s in all_sheep:
        if s.start in next_sheep_index:
            next_sheep_index[s.start].append(s)


load_sheep()


def flock_traversal() -> Iterable[Sheep]:
    """
    Random walks the sheep graph.

    Each loop is one step.
    """
    global all_sheep, next_sheep_index

    def should_i(chance: float) -> bool:
        """
        Randomly decides if an action should be taken, based on the given
        probability.
        """
        return random.random() < chance

    CHANCE_OF_JUMP = 0.05  # Chance of breaking the chain
    CHANCE_OF_LOOP = 0.90  # Chance of looping, if there's a loop option
    sheep = random.choice(all_sheep)
    yield sheep
    while True:
        if sheep.ident not in next_sheep_index:
            # Shouldn't happen
            sheep = random.choice(all_sheep)
        elif next_sheep_index[sheep.ident]:
            # Pick a next item
            nexts = next_sheep_index[sheep.ident]
            if should_i(CHANCE_OF_JUMP):
                # Ignore the chain and pick something new at random
                sheep = random.choice(all_sheep)
            elif sheep in nexts and should_i(CHANCE_OF_LOOP):
                # Just keep looping
                pass
            else:
                sheep = random.choice(next_sheep_index[sheep.ident])
        else:
            # Dead end, start over
            # Only jump to a loop, not a transitory
            sheep = random.choice([s for s in all_sheep if s.start == s.end])
        yield sheep


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
