# ProGym exercise art render farm

Original, procedurally generated 3D exercise illustrations for the ProGym exercise library. Everything visible is made
by this code from CC0 inputs (the MakeHuman base mesh and its CC0 shape targets in `assets/mh`, equipment modelled from
primitives); see `LICENSES.md`.

- `artgen/`: the generator (Blender `bpy`), `tools/`: helpers, `data/v5/all-moves.csv`: the library.
- `.github/workflows/farm.yml`: renders the library in 40 parallel slices (style v5: 900x600 H.264 video, a 600x400
  animated WebP and a still for each exercise, male and female). Each slice publishes to the branch `out/slice-N`.
- Start: change `farm/go` and push, or run the workflow by hand (optionally only some keys).
