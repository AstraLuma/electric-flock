all: $(patsubst origs/%.avi,segments/%.ts,$(wildcard origs/*.avi))

clean:
	rm segments/*.ts

.PHONY: all clean

segments/%.ts: origs/%.avi
	ffmpeg -i $< -movflags +frag_keyframe+empty_moov+default_base_moof $@
