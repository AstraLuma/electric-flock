all: $(patsubst origs/%.avi,segments/%.mp4,$(wildcard origs/*.avi))

clean:
	rm segments/*.ts

.PHONY: all clean

segments/%.mp4: origs/%.avi
	ffmpeg -i $< -movflags +frag_keyframe+empty_moov+default_base_moof $@
