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

all_sheep = [
    Sheep(p, *map(int, p.stem.split('=')))
    for p in Path(app.static_folder).glob('*.mp4')
]

next_sheep_index = {
    s.ident: []
    for s in all_sheep
}
for s in all_sheep:
    if s.start in next_sheep_index:
        next_sheep_index[s.start].append(s)


def flock_traversal() -> Iterable[Sheep]:
    """
    Random walks the sheep graph.

    Each loop is one step.
    """
    sheep = random.choice(all_sheep)
    yield sheep
    while True:
        if sheep.ident not in next_sheep_index:
            # Shouldn't happen
            sheep = random.choice(all_sheep)
        elif next_sheep_index[sheep.ident]:
            # Pick a next item
            # TODO: Preference looping
            sheep = random.choice(next_sheep_index[sheep.ident])
        else:
            # Dead end, start over
            sheep = random.choice(all_sheep)
        yield sheep


sheep_list = []


def flock_walker():
    """
    Thread to walk the graph in a timely fasion.
    """
    global sheep_list
    for seq, sheep in enumerate(flock_traversal()):
        sheep_list.append((seq, sheep))
        if len(sheep_list) > 10:
            sheep_list.pop(0)
        time.sleep(sheep.length)


threading.Thread(target=flock_walker, name='flock_walker', daemon=True).start()


@app.route('/')
def index():
    return (
        """
<!DOCTYPE html>
<video id=player controls autoplay></video>
<script src="https://cdn.jsdelivr.net/npm/hls.js@1"></script>
<script>
  var video = document.getElementById('player');
  var videoSrc = '/stream.m3u8';
  if (Hls.isSupported()) {
    var hls = new Hls({debug:true});
    hls.loadSource(videoSrc);
    hls.attachMedia(video);
  }
  else if (video.canPlayType('application/vnd.apple.mpegurl')) {
    video.src = videoSrc;
  }
  else {
    console.log("HLS failed");
  }
</script>
"""
    )


@app.route("/stream.m3u8")
def get_next_chunk():
    return (
        render_template('chunk.m3u8',
                        flock=[s for _, s in sheep_list],
                        first_seq=min(i for i, _ in sheep_list)
                        ),
        {'Content-Type': 'application/vnd.apple.mpegurl'},
    )
