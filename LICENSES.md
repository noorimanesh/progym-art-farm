# Third-party assets

Only CC0 / public-domain inputs are used. Nothing is bundled in this branch:
`tools/fetch_assets.py` downloads the files below at the pinned commit into
`assets/mh/` (ignored by git). Everything else in the renders (equipment,
clothing, hair, shoes, lighting, background) is generated procedurally by the
code in this branch. No image textures, HDRIs or photographs are used.

## MakeHuman base assets (CC0 1.0)

Repository: https://github.com/makehumancommunity/makehuman
Pinned commit: `a8bc2d54ff0ac92e78ff71431b1023eda42bf482`
Base URL: `https://raw.githubusercontent.com/makehumancommunity/makehuman/a8bc2d54ff0ac92e78ff71431b1023eda42bf482/makehuman/data/`

License: CC0 1.0 Universal, per section C ("The license for the bundled
assets") of
https://github.com/makehumancommunity/makehuman/blob/a8bc2d54ff0ac92e78ff71431b1023eda42bf482/LICENSE.md
and the full text in
https://github.com/makehumancommunity/makehuman/blob/a8bc2d54ff0ac92e78ff71431b1023eda42bf482/LICENSE.ASSETS.md
(CC0 legal code: https://creativecommons.org/publicdomain/zero/1.0/legalcode).
The rig and weight files additionally carry `"license": "CC0"` in their headers,
and each target file states it was released as CC0.

| File (relative to base URL) | Use |
|---|---|
| `3dobjs/base.obj` | base body mesh (body group only) and joint helper vertices |
| `rigs/default.mhskel` | default skeleton (bone heads/tails from joint helpers) |
| `rigs/default_weights.mhw` | default skin weights |
| `targets/macrodetails/universal-{male,female}-young-{averagemuscle,maxmuscle}-{minweight,averageweight}.target` | gender / muscle / weight body shape |
| `targets/macrodetails/proportions/{male,female}-young-{averagemuscle,maxmuscle}-{minweight,averageweight}-idealproportions.target` | body proportions |
| `targets/macrodetails/{african,asian,caucasian}-{male,female}-young.target` | neutral averaged ethnicity blend (1/3 each) |
| `targets/torso/torso-vshape-incr.target` | athletic torso |
| `targets/torso/torso-muscle-pectoral-incr.target` | chest muscle |
| `targets/torso/torso-muscle-dorsi-incr.target` | lat muscle |
| `targets/stomach/stomach-pregnant-decr.target` | flat stomach |
| `targets/buttocks/buttocks-volume-incr.target` | female glutes |
| `targets/bodyshapes/bodyshapes-elvs-man-invert-triangle.target` | male body shape |
| `targets/bodyshapes/bodyshapes-elvs-fem-neat-hourglass.target` | female body shape |
| `targets/armslegs/{l,r}-upperarm-muscle-incr.target` | arm muscle |
| `targets/armslegs/{l,r}-upperarm-shoulder-muscle-incr.target` | shoulder muscle |
| `targets/armslegs/{l,r}-lowerarm-muscle-incr.target` | forearm muscle |
| `targets/armslegs/{l,r}-upperleg-muscle-incr.target` | thigh muscle |
| `targets/armslegs/{l,r}-lowerleg-muscle-incr.target` | calf muscle |

## Software (not redistributed)

- Blender as a Python module (`bpy` from PyPI), GPL, used only as a renderer.
- NumPy (BSD), Pillow (MIT-CMU).

## Input metadata

`data/worklist.csv` is derived only from exercise names, muscle groups and
equipment words of a temporary metadata list (no images, videos or text
bodies from it are used). It is replaced by the real ProGym exercise table
when available.
