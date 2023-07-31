from dataclasses import dataclass
import mimetypes
import random
from pathlib import Path

from flask import Flask, session, url_for


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

all_sheep = [
    Sheep(p, *map(int, p.stem.split('=')))
    for p in Path(SHEEP_ROOT).glob('*.ts')
]

next_sheep_index = {
    s.ident: []
    for s in all_sheep
}
for s in all_sheep:
    if s.start in next_sheep_index:
        next_sheep_index[s.start].append(s)

mimetypes.add_type('video/MP2T', '.ts')

app = Flask(
    __name__,
    static_folder=SHEEP_ROOT,
    static_url_path='/sheep',
)
app.secret_key = 'sekrit',


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
    if 'sheep' not in session or 'seq' not in session:
        # New one
        next_sheep = random.choice(all_sheep)
        next_seq = 1
    else:
        # Next in sequence
        if session['sheep'] not in next_sheep_index:
            next_sheep = random.choice(all_sheep)
        elif next_sheep_index[session['sheep']]:
            next_sheep = random.choice(next_sheep_index[session['sheep']])
        else:
            next_sheep = random.choice(all_sheep)
        next_seq = session['seq'] + 1

    print(next_seq, next_sheep)

    session['sheep'] = next_sheep.ident
    session['seq'] = next_seq
    return (f"""#EXTM3U
#EXT-X-TARGETDURATION:{next_sheep.length}
#EXT-X-VERSION:7
#EXT-X-MEDIA-SEQUENCE:{next_seq}
#EXTINF:{next_sheep.length},
{url_for('static', filename=next_sheep.path.name)}
""", {'Content-Type': 'application/vnd.apple.mpegurl'})
