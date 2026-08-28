# Bonus: the gallery wall prompt

Once `generations/` has real output in it, hand your agent this prompt
verbatim (outside of a /generate run — it's a one-time build, not part of
the skill's own behavior) to get a local, single-file gallery page for
everything the skill has made.

```
build me a single web page that shows every image and video my ai
generates, all in one place, like a bento wall.
- it reads one folder on my computer called generations and shows
  everything sitting in it, newest at the top
- lay it out as a masonry wall - tiles keep their own shape, nothing gets
  cropped or squashed, rounded cards with even gaps, 4 columns wide and
  fewer as the window gets smaller
- videos start playing quietly when i hover over them and stop when i move
  away, images just sit there
- click any tile and it opens up big in the middle of the screen, click
  outside to close
- no search, no filters, no tabs, no side panels - just the wall of
  everything

keep it to one file so it runs by opening it, and make it feel like a
proper finished gallery, not a rough draft.

when the page is done, add a line to my CLAUDE.md so that from now on
anything the /generate skill makes gets saved straight into that same
generations folder, so it turns up on this page automatically. don't make
the page pop open every time, just save the file there.
```

Why this works: `/generate` already saves flat into one folder (see
SKILL.md's Output section), so the wall never needs updating — new
generations just appear on next page load.
