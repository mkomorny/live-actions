"""Creative applications -- Book 2.

Book 3 is the reference of what to type. This is the argument for what to try:
workflows where handing the job to Genius changes what you'd actually attempt,
not just how fast you'd do it.
"""
from __future__ import annotations

# (title, the idea, how to run it, which actions carry it)
Idea = tuple[str, str, str, list[str]]

THEMES: list[tuple[str, str, list[Idea]]] = [

    ("Beating the blank page",
     "The most expensive moment in music production is the one before anything exists. "
     "Genius is unusually good here because it costs you nothing to throw away.",
     [
      ("Ten starts before breakfast",
       "Ask for ten completely different 4-bar loops -- different tempo, different key, "
       "different genre -- each in its own scene. Then delete nine. The value isn't in "
       "the generation, it's in discovering which one you reach for without thinking.",
       "“Build me ten 4-bar starting points in ten scenes. Vary the tempo, key and "
       "style widely. Name each scene after its genre.” Then listen once through and "
       "keep whichever one you're still humming.",
       ["live_create_scene", "live_create_track", "live_write_notes", "live_update_set"]),
      ("The constraint generator",
       "Ask for something deliberately restrictive -- five notes only, one chord, no "
       "kick drum, everything in 7/8. Constraints are the oldest trick for forcing "
       "originality, and Genius will follow one rigidly where you'd cheat.",
       "“Write me a full 8-bar idea using only five different pitches, ever, across "
       "all tracks.” Then try to finish it without breaking the rule.",
       ["live_write_notes", "live_create_chord_progression", "live_update_set"]),
      ("Steal from yourself",
       "Point it at a folder of unfinished projects and have it rank them by how close "
       "to done they are. The one you abandoned eighteen months ago is often two hours "
       "from finished -- you just can't remember which one that is.",
       "“Scan every .als in this folder, rank them by how finished they are, and tell "
       "me which three are worth reopening.” Ableton doesn't even need to be running.",
       ["als_summary", "als_find_unfinished", "als_list_tracks"]),
      ("Genre transplant",
       "Take a loop you already have and ask for it rebuilt in a completely different "
       "style -- same chords, drum'n'bass tempo; same melody, as a bossa nova. Familiar "
       "material in unfamiliar clothes is a reliable way to hear it fresh.",
       "“Read the chords in track 3, then rebuild that progression at 174 BPM with a "
       "breakbeat feel in scene 4.”",
       ["live_read_clip", "live_detect_key", "live_create_chord_progression", "live_create_scene"]),
     ]),

    ("Delegating the tedious half",
     "Every producer has a list of jobs that are trivially easy and unbearably boring. "
     "This is the least glamorous use of Genius and probably the highest value.",
     [
      ("Session hygiene on demand",
       "Default track names, unlabelled clips, no colour coding, twelve things soloed "
       "from three days ago. Ten minutes of tidying you'll never voluntarily do.",
       "“Rename every default-named track based on what's actually on it, colour-code "
       "by instrument family, and unsolo everything.”",
       ["live_read_set", "live_update_track", "live_batch_tracks"]),
      ("Arrangement scaffolding",
       "Laying out a 64-bar structure by dragging clips is pure mechanical labour. "
       "Describe the structure in one sentence and go make coffee.",
       "“8-bar intro, 16 verse, 16 chorus, 8 breakdown, 16 outro. Build it from my "
       "session clips and add locators for each section.”",
       ["live_duplicate_to_arrangement", "live_update_set", "live_read_arrangement_length"]),
      ("Variation farming",
       "You need eight subtly different hi-hat patterns. Generating them by hand is "
       "twenty minutes; asking for them is twenty seconds and they'll be more different "
       "from each other than yours would have been.",
       "“Give me eight hat variations in slots 1-8 on track 2, each a different "
       "Euclidean pattern, from sparse to busy.”",
       ["live_generate_euclidean", "live_create_drum_pattern"]),
      ("The pre-mix checklist",
       "Before you start mixing, someone should check for the obvious problems. That "
       "someone has historically been nobody.",
       "“Audit my mix: flag low-end clashes, anything clipping, missing limiter, "
       "lopsided panning. Just the list, don't fix anything yet.”",
       ["live_analyze_mix", "live_read_set", "live_read_meter"]),
     ]),

    ("Learning while you work",
     "The knowledge base is local and the Set is right there, which makes it possible "
     "to ask a theory question and immediately hear the answer in your own project.",
     [
      ("Explain, then demonstrate",
       "The single best pattern for learning anything musical. Don't just ask what "
       "negative harmony is -- ask for it applied to the chords already in your Set.",
       "“Explain modal interchange, then take my progression in track 3 and show me "
       "three borrowed-chord variations in slots 2, 3 and 4.”",
       ["library_db_search", "live_read_clip", "live_create_chord_progression"]),
      ("Reverse-engineer your own instincts",
       "Ask it to analyse something you wrote by feel and tell you what you actually "
       "did. Finding out your favourite progression is a deceptive cadence you've been "
       "using unconsciously for years is genuinely useful.",
       "“Detect the key of track 3, analyse the progression, and tell me what I've "
       "done in theory terms and why it works.”",
       ["live_detect_key", "live_read_clip", "library_db_search"]),
      ("Read the manual without reading the manual",
       "Put the manuals you own into your Knowledge folder as PDFs. Then ask the "
       "specific question instead of scrolling.",
       "“How do I set up a custom mode on my controller? Check the manual in my "
       "Knowledge folder.”",
       ["library_search", "library_read", "library_db_search"]),
      ("Deliberate practice generator",
       "Ask for exercises targeted at a specific weakness, written into your Set as "
       "real MIDI you can play along with.",
       "“I'm weak on jazz voicings. Write me five ii-V-I exercises in different keys, "
       "one per scene, with rootless voicings.”",
       ["live_generate_chords", "live_create_scene", "library_db_search"]),
     ]),

    ("Things that are impractical by hand",
     "Some ideas are musically interesting but too fiddly to be worth the effort "
     "manually. Those are exactly the ones worth delegating.",
     [
      ("Procedural movement everywhere",
       "Shaped automation is cheap to generate and tedious to draw. Put slow, "
       "differently-phased LFOs on six parameters across four tracks and the whole "
       "track breathes in a way that's very hard to achieve by hand.",
       "“Put slow sine automation on the filter cutoff of tracks 2, 3 and 5, each at "
       "a different cycle count so they drift against each other.”",
       ["live_add_shaped_automation", "live_read_device", "live_read_param_range"]),
      ("Polyrhythm without the arithmetic",
       "5-against-4 across three instruments with the phase relationship you actually "
       "want is an afternoon of counting. Or one sentence.",
       "“Write a 5-against-4 polyrhythm between the kick and hats, and put a 7-step "
       "Euclidean pattern on the percussion so all three phase against each other.”",
       ["live_create_drum_pattern", "live_generate_euclidean"]),
      ("Rhythm-locked automation",
       "Volume automation shaped to follow the actual note positions of your kick "
       "pattern -- real sidechain-style pumping without a compressor, precisely locked "
       "to the notes rather than approximated.",
       "“Read the kick pattern in track 1, then shape volume automation on track 3 "
       "that ducks exactly where those kicks land.”",
       ["live_read_clip", "live_add_shaped_automation"]),
      ("Classical transformations on modern material",
       "Retrograde, inversion, augmentation -- centuries-old techniques that are "
       "annoying to do by hand and often sound superb on electronic material.",
       "“Take my lead in track 5 and give me four variations in slots 2-5: "
       "retrograde, inverted, augmented, and inverted-retrograde.”",
       ["live_transform_clip", "live_read_clip"]),
     ]),

    ("Closing the loop",
     "The most genuinely novel capability here: Genius can change something, measure "
     "the actual audio result, and adjust based on what happened. Nothing else in this "
     "guide is as close to having an assistant.",
     [
      ("Tune to a target, automatically",
       "Give it a measurable goal and let it iterate. Each pass costs real wall-clock "
       "time because the recording is real time, so cap the attempts -- but the result "
       "is objectively verified rather than asserted.",
       "“Adjust the limiter until a 10-second capture measures between -15 and -13 "
       "LUFS. Maximum five attempts, and show me the number after each one.”",
       ["live_record_and_analyze", "live_update_device", "live_read_param_range"]),
      ("Prove the tweak worked",
       "Record before, make the change, record after, compare. It converts 'I think "
       "that helped' into a number.",
       "“Record 10 seconds, make the EQ change, record another 10, then tell me "
       "measurably what changed.”",
       ["live_record_audio", "live_update_device", "live_compare_audio"]),
      ("The receipt pattern",
       "Snapshot, do the risky thing, diff. Use it around anything you wouldn't want to "
       "reconstruct by hand -- especially recipes, which change a lot at once.",
       "“Snapshot the session, apply the recipe, then diff it and list in plain "
       "English everything that changed.”",
       ["live_session_snapshot", "live_apply_recipe", "live_session_diff"]),
      ("Structural prediction versus measured reality",
       "Run the structural mix audit and a real recorded analysis, then look at where "
       "they disagree. The gap between what the Set looks like and what it measures is "
       "usually where the interesting problem is hiding.",
       "“Run a mix audit, then record 20 seconds and analyse it. Tell me where the "
       "two disagree and what you think that means.”",
       ["live_analyze_mix", "live_record_and_analyze", "live_compare_audio"]),
     ]),

    ("Performance and playability",
     "Most Genius use is compositional, but the Session View tools make it a "
     "surprisingly good stage-prep assistant.",
     [
      ("Make a static Set performable",
       "Launch modes, quantization and legato settings across dozens of clips is exactly "
       "the kind of consistent, boring configuration work that gets skipped.",
       "“Set every clip in scenes 1-4 to toggle mode with 1-bar quantization, and "
       "make the pad clips legato.”",
       ["live_read_scene", "live_set_clip_launch_mode", "live_read_set"]),
      ("Build the breakdown versions",
       "For every scene you have, create a stripped-back counterpart to drop into. Doing "
       "this by hand for eight scenes is an evening.",
       "“For each of scenes 1-4, create a stripped-back version in scenes 5-8 with "
       "the drums thinned out and the bass removed.”",
       ["live_read_scene", "live_create_scene", "live_duplicate", "live_remove_notes"]),
      ("Crossfader-ready staging",
       "Assign tracks to crossfader sides by role so you can actually DJ between "
       "sections of your own track.",
       "“Put my drum and bass tracks on crossfader A, the melodic tracks on B, and "
       "centre the crossfader.”",
       ["live_read_set", "live_update_track", "live_set_crossfader"]),
      ("Capture the happy accident",
       "You improvise a good combination of clips and then lose it. One prompt freezes "
       "it permanently before it evaporates.",
       "“Capture whatever's playing right now into a new scene and name it.”",
       ["live_create_scene", "live_get_selected", "live_update_scene"]),
     ]),
]
