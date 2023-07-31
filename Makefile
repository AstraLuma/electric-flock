all: $(patsubst origs/%.avi,segments/%.ts,$(wildcard origs/*.avi))

.PHONY: all

segments/%.ts: origs/%.avi
	ffmpeg -i $< -movflags +frag_keyframe+empty_moov $@
