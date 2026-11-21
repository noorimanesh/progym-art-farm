"""Equipment for machines, cardio machines and held set-ups that the older
generic frames drew wrong (posts through the athlete, missing parts).
Registered into equipment.KINDS on import."""
import math

import numpy as np

from . import equipment as EQ
from .equipment import (Geo, rx, ry, rz, upright, FRAME, PAD, DARKSTEEL, STEEL, RUBBER, GREY, SCREEN, WOOD,
                        PLATE_R, CHROME)


def row_machine(seat_h=0.5, chest=True, pivot=(0.62, 1.95), thigh=False, front_y=1.15, **_):
    """Lever row machine, user faces +Y on a seat at the origin.  Everything
    tall stands in front of the hands' reach (front_y) so nothing crosses the
    athlete: base rail, seat post, chest pad on a stem from the front (chest),
    or a knee pad over the thighs (thigh), a front column and a cross beam
    carrying the lever axle at (y, z) = pivot."""
    g = Geo()
    py, pz = pivot
    g.box(FRAME, (0, (front_y - 0.35) / 2, 0.03), (0.12, front_y + 0.35, 0.06))      # floor rail
    g.box(FRAME, (0, front_y, 0.03), (0.8, 0.12, 0.06))                              # front foot
    g.box(FRAME, (0, -0.3, 0.03), (0.6, 0.1, 0.06))                                  # rear foot
    g.box(PAD, (0, -0.02, seat_h - 0.04), (0.40, 0.38, 0.08))
    g.cyl(FRAME, (0, 0.0, seat_h - 0.08), (0, 0.0, 0.06), 0.04)
    top = max(pz, 1.0) + 0.06
    g.box(FRAME, (0, front_y, top / 2), (0.1, 0.1, top))                             # front column
    if pz > 1.2:
        # beam from the column back over the athlete to the axle, axle across
        g.box(FRAME, (0, (front_y + py) / 2, pz + 0.06), (0.09, abs(front_y - py) + 0.1, 0.09))
    else:
        g.box(FRAME, (0, (front_y + py) / 2, pz), (0.09, abs(front_y - py) + 0.1, 0.09))
    if chest:
        g.box(PAD, (0, 0.36, 1.0), (0.34, 0.09, 0.44), rx(-6))
        g.cyl(FRAME, (0, 0.42, 0.95), (0, front_y, 0.62), 0.03)                        # stem to the column
    if thigh:
        g.box(PAD, (0, 0.30, seat_h + 0.25), (0.42, 0.14, 0.09))
        g.cyl(FRAME, (0, 0.38, seat_h + 0.25), (0, front_y, seat_h + 0.25), 0.03)
    # weight horns on the front column
    for s in (-1, 1):
        g.cyl(STEEL, (s * 0.05, front_y, 0.55), (s * 0.3, front_y, 0.55), 0.025)
        g.cyl(RUBBER, (s * 0.12, front_y, 0.55), (s * 0.16, front_y, 0.55), 0.2, n=36)
    return g


def chest_pad(w=0.30, h=0.42, **_):
    """Chest pad, face toward -Y at the local origin (rides on the chest)."""
    g = Geo()
    g.box(PAD, (0, 0.045, 0), (w, 0.09, h))
    g.box(FRAME, (0, 0.11, 0), (0.12, 0.04, 0.2))
    return g


def lever_hub(**_):
    """Axle housing of a lever pair, axle along X at the origin."""
    g = Geo()
    g.cyl(STEEL, (-0.4, 0, 0), (0.4, 0, 0), 0.03)
    for s in (-1, 1):
        g.cyl(DARKSTEEL, (s * 0.4, 0, 0), (s * 0.3, 0, 0), 0.065, n=20)
    return g


def preacher_base(height=0.55, foot=0.13, foot_y=0.36, pad_y=0.5, **_):
    """Preacher bench without its arm pad: seat (user faces +Y), seat post,
    base, foot bar and the pad's column at pad_y (the pad rides on top)."""
    g = Geo()
    g.box(PAD, (0, 0.0, height), (0.32, 0.32, 0.07))
    g.cyl(FRAME, (0, 0.0, height - 0.04), (0, 0.0, 0.05), 0.035)
    g.box(FRAME, (0, pad_y / 2, 0.03), (0.5, pad_y + 0.35, 0.05))
    if foot:
        g.box(DARKSTEEL, (0, foot_y, foot), (0.42, 0.14, 0.03))
        g.cyl(FRAME, (0, foot_y, foot - 0.015), (0, foot_y, 0.05), 0.02)
    return g


def preacher_pad(length=0.36, width=0.44, th=0.07, **_):
    """Arm pad: local Y down the slope, local Z its face normal, top face
    through the origin (the pad lies under the upper arms)."""
    g = Geo()
    g.box(PAD, (0, 0, -th / 2), (width, length, th))
    g.box(FRAME, (0, 0.02, -th - 0.015), (0.16, length * 0.7, 0.03))
    return g


def pulley_block(h=0.15, **_):
    """The pulley housing and wheel of a cable column (local frame as
    cable_tower: wheel at (0, 0.12, h)); used as the in-picture marker of a
    column whose top may leave the frame."""
    g = Geo()
    g.box(DARKSTEEL, (0, 0.08, h), (0.1, 0.08, 0.14))
    g.cyl(STEEL, (-0.025, 0.12, h), (0.025, 0.12, h), 0.045, n=20)
    return g


def fixed_bar(h=1.0, width=1.2, **_):
    """Bar fixed between two uprights at height h (bar along X through the
    origin's x/y), for bar-assisted squats."""
    g = Geo()
    for x in (-width / 2, width / 2):
        upright(g, x, 0.0, h + 0.15, 0.07)
        g.box(FRAME, (x, 0.0, 0.02), (0.12, 0.5, 0.04))
    g.cyl(STEEL, (-width / 2, 0, h), (width / 2, 0, h), 0.016, n=14)
    return g


def band_post(h=0.25, **_):
    """Low anchor post (rack upright on a floor plate) with the band loop at h."""
    g = Geo()
    upright(g, 0, 0, max(h + 0.6, 1.0), 0.07)
    g.box(FRAME, (0, 0, 0.02), (0.4, 0.4, 0.04))
    g.torus(EQ.BAND, (0, 0, h), 0.05, 0.008, axis=(0, 0, 1))
    return g


def rower_frame(**_):
    """Air rower without its seat: monorail, front legs and flywheel housing,
    footplate pair, rear foot (the seat rides on the rail as its own part)."""
    g = Geo()
    g.box(FRAME, (0, -0.05, 0.2), (0.09, 2.3, 0.06))                     # monorail, top z 0.23
    g.box(FRAME, (0, -1.15, 0.1), (0.4, 0.08, 0.04))
    g.cyl(FRAME, (0, -1.15, 0.12), (0, -1.15, 0.2), 0.03)
    g.box(FRAME, (0, 1.12, 0.03), (0.55, 0.1, 0.06))
    g.cyl(FRAME, (0, 1.1, 0.06), (0, 1.0, 0.25), 0.04)
    g.cyl(DARKSTEEL, (-0.14, 1.18, 0.5), (0.14, 1.18, 0.5), 0.27, n=36)    # flywheel cage
    g.cyl(GREY, (-0.145, 1.18, 0.5), (0.145, 1.18, 0.5), 0.08, n=20)
    g.cyl(FRAME, (0, 1.0, 0.23), (0, 1.12, 0.72), 0.035)                  # neck to the monitor
    g.box(SCREEN, (0, 1.08, 0.86), (0.2, 0.05, 0.16), rx(-20))
    for x in (-0.12, 0.12):
        g.box(DARKSTEEL, (x, 0.83, 0.31), (0.13, 0.03, 0.3), rx(-40))       # footplates
        g.box(FRAME, (x, 0.9, 0.2), (0.03, 0.12, 0.08))
    g.cyl(DARKSTEEL, (-0.03, 0.98, 0.47), (0.03, 0.98, 0.47), 0.03)       # chain outlet
    return g


def rower_seat(**_):
    """Sliding seat: pad top at local z 0, carriage and rollers down to the rail (z -0.2)."""
    g = Geo()
    g.box(PAD, (0, 0, -0.03), (0.3, 0.3, 0.06))
    g.box(FRAME, (0, 0, -0.11), (0.16, 0.22, 0.1))
    for y in (-0.08, 0.08):
        g.cyl(RUBBER, (-0.07, y, -0.17), (0.07, y, -0.17), 0.03, n=16)
    return g


def row_handle(**_):
    """Rowing handle across the fists (X), chain hook at the centre toward +Y."""
    g = Geo()
    g.cyl(RUBBER, (-0.27, 0, 0), (-0.06, 0, 0), 0.018, n=14)
    g.cyl(RUBBER, (0.06, 0, 0), (0.27, 0, 0), 0.018, n=14)
    g.cyl(DARKSTEEL, (-0.06, 0, 0), (0.06, 0, 0), 0.014, n=12)
    return g


def bike_frame(crank=(0.3, 0.42), seat=(-0.2, 0.9), bars=(0.5, 1.18), **_):
    """Stationary bike: base, seat post and saddle, front column with the
    handlebar (bars = (y, z)), flywheel at the front, crank axle housing
    (crank = (y, z)); cranks and pedals are separate moving parts."""
    g = Geo()
    cy, cz = crank
    sy, sz = seat
    by, bz = bars
    g.box(FRAME, (0, 0.12, 0.03), (0.12, 1.25, 0.05))
    g.box(FRAME, (0, -0.48, 0.03), (0.55, 0.08, 0.05))
    g.box(FRAME, (0, 0.72, 0.03), (0.55, 0.08, 0.05))
    g.cyl(FRAME, (0, sy - 0.12, 0.05), (0, sy, sz - 0.04), 0.035)               # seat post
    g.box(PAD, (0, sy + 0.02, sz), (0.2, 0.28, 0.06))
    g.cyl(FRAME, (0, sy - 0.08, 0.35), (0, cy, cz), 0.03)                        # down tube to the crank
    g.cyl(FRAME, (0, 0.68, 0.05), (0, by - 0.05, bz - 0.06), 0.04)              # front column
    g.cyl(FRAME, (0, cy, cz), (0, 0.6, 0.6), 0.03)
    g.cyl(FRAME, (-0.24, by, bz), (0.24, by, bz), 0.018)                        # bar
    for s in (-1, 1):
        g.cyl(RUBBER, (s * 0.24, by, bz), (s * 0.24, by + 0.12, bz + 0.04), 0.02)
    g.cyl(DARKSTEEL, (-0.025, 0.55, 0.38), (0.025, 0.55, 0.38), 0.24, n=36)     # flywheel
    g.cyl(GREY, (-0.03, 0.55, 0.38), (0.03, 0.55, 0.38), 0.05, n=16)
    g.cyl(DARKSTEEL, (-0.06, cy, cz), (0.06, cy, cz), 0.06, n=20)               # crank housing
    g.box(SCREEN, (0, by - 0.02, bz + 0.12), (0.18, 0.04, 0.12), rx(-25))
    return g


def pedal(w=0.09, length=0.11, **_):
    """Pedal: platform along local Y (foot direction), axle along X at the origin."""
    g = Geo()
    g.box(RUBBER, (0, 0, 0), (w, length, 0.025))
    return g


def elliptical_frame(**_):
    """Elliptical: base, rear flywheel housing (crank axle at (0, -0.72, 0.38)),
    front column with console; pedal rails, pedals and handle arms move."""
    g = Geo()
    g.box(FRAME, (0, 0.0, 0.04), (0.14, 1.9, 0.07))
    g.box(FRAME, (0, -0.85, 0.03), (0.6, 0.1, 0.06))
    g.box(FRAME, (0, 0.85, 0.03), (0.6, 0.1, 0.06))
    g.cyl(DARKSTEEL, (-0.09, -0.72, 0.38), (0.09, -0.72, 0.38), 0.3, n=36)     # rear housing
    g.cyl(GREY, (-0.095, -0.72, 0.38), (0.095, -0.72, 0.38), 0.07, n=16)
    g.box(FRAME, (0, -0.72, 0.2), (0.14, 0.2, 0.32))
    g.cyl(FRAME, (0, 0.8, 0.06), (0, 0.7, 1.35), 0.045)                         # front column
    g.box(SCREEN, (0, 0.66, 1.42), (0.34, 0.08, 0.2), rx(25))
    for s in (-1, 1):
        g.box(FRAME, (s * 0.18, 0.62, 0.1), (0.05, 0.3, 0.05))                  # front ramps for the rollers
    return g


NEW = {"rower_frame": rower_frame, "rower_seat": rower_seat, "row_handle": row_handle, "bike_frame": bike_frame,
       "pedal": pedal, "elliptical_frame": elliptical_frame, "fixed_bar": fixed_bar, "band_post": band_post, "pulley_block": pulley_block, "preacher_base": preacher_base, "preacher_pad": preacher_pad, "row_machine": row_machine, "chest_pad": chest_pad, "lever_hub": lever_hub}
EQ.KINDS.update(NEW)
