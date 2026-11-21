"""Loop timing for the v3 animations.

A movement is posed at a small set of unique phases (each rendered once) and
played back as a frame sequence with per-frame durations, so the loop gets
24 frames / 2.4 s with eased motion, short holds at both ends and a slower
lowering than lifting where the load is lowered under control.

Tempo kinds
  rep    start -> end -> start.  `first` says which half is the lowering
         (eccentric) one: "ecc" (e.g. bench press: lockout -> chest),
         "con" (e.g. curl: arms down -> curled) or "even".
  alt    alternating sides: one rep right, one rep left (template reads
         row["_side"]).
  cycle  periodic motion (running, jacks, ropes): phase 0..1 wraps, 24
         uniform frames.
  hold   isometric hold: a small brace / breathing movement between the
         start and end key poses, slow and even.
  flight jumps: like rep, but the take-off half is fast and the landing
         half settles, with no ease at take-off.

Phase values are eased with a cosine profile (zero velocity at both key
poses) unless the template asks for linear phases.
"""
import math

LOOP_MS = 2400
N_REP = 13          # unique phases in a rep (0..12)
N_ALT = 7           # unique phases per side in an alternating rep
N_CYCLE = 24


def set_frames(n):
    """24 (v3) or 36 (v4) frames per loop: rep / hold / flight 2*(N_REP-1),
    alternating 4*(N_ALT-1), cycles N_CYCLE."""
    global N_REP, N_ALT, N_CYCLE
    N_REP = n // 2 + 1
    N_ALT = n // 4 + 1
    N_CYCLE = n


def ease(u):
    """Cosine ease-in-out, 0..1 -> 0..1 with zero slope at both ends."""
    return 0.5 - 0.5 * math.cos(math.pi * min(max(u, 0.0), 1.0))


def ease_out(u):
    return math.sin(0.5 * math.pi * min(max(u, 0.0), 1.0))


class Timeline:
    """unique: list of (key, phase, side); frames: list of (unique index, ms)."""

    def __init__(self, unique, frames, kind):
        self.unique = unique
        self.frames = frames
        self.kind = kind

    @property
    def total_ms(self):
        return sum(ms for _, ms in self.frames)

    def mid_index(self):
        """Unique index of the middle (most displaced) pose."""
        if self.kind == "cycle":
            return len(self.unique) // 4
        if self.kind == "alt":
            return N_ALT - 1
        return len(self.unique) // 2

    def sheet_indices(self):
        """start, middle, end unique indices for contact sheets."""
        if self.kind == "cycle":
            n = len(self.unique)
            return [0, n // 4, n // 2]
        if self.kind == "alt":
            return [0, N_ALT - 1, 2 * N_ALT - 2]
        n = len(self.unique)
        return [0, n // 2, n - 1]


def _split_ms(total, n_ecc, n_con, ratio):
    """Durations of eccentric / concentric frames so that the eccentric half
    lasts `ratio` times the concentric half."""
    con = total / (n_con + n_ecc * ratio)
    return con * ratio, con


def timeline(kind="rep", first="ecc", hold_a=200, hold_b=200, ratio=1.45, linear=False, n=None):
    """Build the unique phases and the frame sequence for one loop."""
    E = (lambda u: u) if linear else ease
    if kind == "cycle":
        k = n or N_CYCLE
        uniq = [(f"c{i}", i / k, None) for i in range(k)]
        frames = [(i, LOOP_MS // k) for i in range(k)]
        return Timeline(uniq, frames, kind)
    if kind == "alt":
        m = n or N_ALT
        uniq = [("a0", 0.0, "R")]
        for i in range(1, m):
            uniq.append((f"r{i}", E(i / (m - 1)), "R"))
        for i in range(1, m):
            uniq.append((f"l{i}", E(i / (m - 1)), "L"))
        iR = list(range(1, m))
        iL = list(range(m, 2 * m - 1))
        seq = [0] + iR + iR[-2::-1] + [0] + iL + iL[-2::-1]
        move = LOOP_MS - 2 * 120 - 2 * 100
        ms = move / (len(seq) - 4)
        frames = []
        for j, u in enumerate(seq):
            if u == 0:
                frames.append((u, 120))
            elif u in (iR[-1], iL[-1]):
                frames.append((u, 100))
            else:
                frames.append((u, ms))
        return Timeline(uniq, _round(frames), kind)
    m = n or N_REP
    if kind == "hold":
        m = n or N_REP
        uniq = [(f"h{i}", ease(i / (m - 1)), None) for i in range(m)]
        seq = list(range(m)) + list(range(m - 2, 0, -1))
        frames = [(u, LOOP_MS / len(seq)) for u in seq]
        return Timeline(uniq, _round(frames), kind)
    if kind == "flight":
        # take-off and flight on the way out (fast, linear-ish), landing and
        # reset on the way back (eased)
        uniq = [(f"p{i}", i / (m - 1), None) for i in range(m)]
        seq = list(range(m)) + list(range(m - 2, 0, -1))
        frames = []
        for j, u in enumerate(seq):
            frames.append((u, hold_a if j == 0 else (hold_b if u == m - 1 else 0)))
        rest = LOOP_MS - hold_a - hold_b
        n_mov = len(seq) - 2
        for j in range(len(frames)):
            if frames[j][1] == 0:
                frames[j] = (frames[j][0], rest / n_mov)
        return Timeline(uniq, _round(frames), kind)
    # rep
    uniq = [(f"p{i}", E(i / (m - 1)), None) for i in range(m)]
    down = list(range(1, m - 1))            # moving frames start -> end
    up = list(range(m - 2, 0, -1))          # moving frames end -> start
    rest = LOOP_MS - hold_a - hold_b
    if first == "even":
        a = b = rest / (len(down) + len(up))
    elif first == "ecc":
        a, b = _split_ms(rest, len(down), len(up), ratio)
    else:  # concentric first: the way back is the lowering
        b, a = _split_ms(rest, len(up), len(down), ratio)
    frames = [(0, hold_a)] + [(u, a) for u in down] + [(m - 1, hold_b)] + [(u, b) for u in up]
    return Timeline(uniq, _round(frames), "rep")


def _round(frames):
    """Integer milliseconds (multiples of 1 ms) keeping the loop total."""
    out, acc, err = [], 0.0, 0.0
    for u, ms in frames:
        v = ms + err
        r = int(round(v))
        err = v - r
        out.append((u, max(r, 20)))
    return out


if __name__ == "__main__":
    for k in ("rep", "alt", "cycle", "hold", "flight"):
        tl = timeline(k)
        print(k, len(tl.unique), "unique", len(tl.frames), "frames", tl.total_ms, "ms",
              [ms for _, ms in tl.frames][:14])
