import os
import math
import cadquery as cq

# ==============================================================================
# SECTION 1 — GLOBAL PARAMETERS
# ==============================================================================

# ── Enclosure outer envelope ──────────────────────────────────────────────────
L, W, H         = 135.0, 95.0, 38.0     # outer dims (X, Y, Z) — origin at geometric centre, floor Z=0
T               = 2.5                    # uniform wall + floor thickness
INT_H           = H - T                 # interior clear height = 35.5 mm (floor=T, top open)
R_OUTER         = 6.0                   # outer vertical edge fillet
R_INNER         = 4.0                   # inner cavity vertical edge fillet
FIT_SLIDE       = 0.5                   # clearance for lid inset lip

# ── MCU zone — Arduino Uno R4 in acrylic snap-case (back-left) ───────────────
# All coordinates in centre-origin system (X=0,Y=0 = enclosure footprint centre)
MCU_ORIG        = (-15.0, 10.0)         # bay centre (X, Y) — shifted in Y to fit
MCU_CASE        = (88.0, 68.0, 28.0)   # ROTATED 90 DEG: X=88.0 (long), Y=68.0 (short)
                                         # Fits inside enclosure, ports face left wall
MCU_BOSS_POS    = [                     # retention boss positions (X,Y) relative to rotated bay centre
    (-30.0, 24.0),                      # rear-left boss
    ( 30.0, 24.0),                      # rear-right boss
]
MCU_LIP_T       = T                    # lip wall thickness (= enclosure wall thickness)
MCU_LIP_H       = 3.0                  # lip wall height — locates case laterally
MCU_BOSS_H      = 5.0                  # retention boss height above floor
MCU_BOSS_R      = 4.0                  # retention boss outer radius
MCU_PILOT_R     = 1.5                  # M3 pilot hole radius (∅3 mm)

# ── TFT display zone (front-left) ─────────────────────────────────────────────
TFT_ORIG        = (-20.0, -22.0)       # bezel centre (X, Y)
TFT_BEZEL       = (70.0, 46.0, 2.0)   # bezel footprint + thickness
TFT_VIEWPORT    = (68.0, 44.0)         # lid cutout aperture — rx=1.5 mm

# ── GSM zone — SIM800L — REPOSITIONED to front of sensor dock (FIX 6) ─────────
# GSM cannot fit between MCU bay right edge (+19) and dock left wall (+34): only 15mm gap.
# Solution: place GSM in front-right sub-quadrant, centred on dock X.
# Relocated to X=48.0 to completely clear the divider wall.
GSM_ORIG        = (48.0, -28.0)        # CHANGED from (42,-28) to clear divider wall
GSM_BOARD       = (25.0, 23.0, 1.6)   # PCB dims
GSM_PEG_H      = 4.0
GSM_PEG_R      = 2.5
GSM_PILOT_R    = 1.0                   # M2 pilot hole radius (∅2 mm)
GSM_PEG_INSET  = 3.0
# GSM extents: X [29.5, 54.5], Y [-39.5, -16.5] — clear of dock and enclosure walls ✓

# ── Sensor pocket — fixed, open-top (back-right) ──────────────────────────────
DOCK_ORIG       = (50.0, 12.0)         # pocket centre (X, Y)
DOCK_INNER      = (32.0, 48.0, 35.5)  # pocket interior dims (X × Y × depth)
DOCK_DIV_T      = 2.5                  # divider wall thickness
HDR_FIXED       = (12.0, 5.0, 4.0)    # fixed female header (W × D × H), recessed in floor
# Dock left wall at X = DOCK_ORIG[0] - DOCK_INNER[0]/2 = 50 - 16 = +34.0
# MCU bay right edge at X = MCU_ORIG[0] + MCU_CASE[0]/2 = -15 + 34 = +19.0
# Gap = 34.0 - 19.0 = 15.0 mm — divider wall 2.5mm fits with 12.5mm clearance ✓

# ── Pocket rim rebate (for flush vent door) ────────────────────────────────────
DOOR_OUTER      = (34.0, 50.0, 3.0)   # vent door plate (L × W × H)
DOOR_FIT        = 0.3                  # clearance per side in rebate
REBATE_OPEN     = (                    # rebate opening in top face of enclosure
    DOOR_OUTER[0] + DOOR_FIT * 2,     # = 34.6 mm
    DOOR_OUTER[1] + DOOR_FIT * 2      # = 50.6 mm
)
REBATE_DEPTH    = 3.0                  # door sits flush with enclosure top face
REBATE_RX       = 3.0                  # corner radius of rebate opening

# ── Bayonet J-slot receivers in pocket rim (2×, on Y-axis walls) ──────────────
BAY_SLOT_W      = 4.5                  # slot mouth width
BAY_SLOT_H      = 2.2                  # slot vertical travel + tab thickness
BAY_SLOT_D      = 2.0                  # slot depth into pocket wall
BAY_SLOT_ROT    = 25.0                 # degrees of rotation to lock
BAY_PUSH        = 1.0                  # mm push-down before rotate

# ── Vent door (PART C) ────────────────────────────────────────────────────────
DOOR_T          = 3.0                  # door plate thickness
DOOR_RX         = 3.0                  # door corner radius
DOOR_EDGE_MARGIN = 4.0                 # clear border before vent cells start
DOOR_VENT_R     = 2.5                  # door hex cell circumradius
DOOR_VENT_GAP   = 1.0                  # min wall between cells

# Bayonet tabs on door underside
BAY_TAB_L       = 4.0
BAY_TAB_W       = 2.0
BAY_TAB_H       = 1.5
BAY_TAB_INSET   = 3.0

# Finger-lift notch + lock boss
NOTCH_W         = 8.0
NOTCH_D         = 3.0
NOTCH_SIDE      = 'minus_y'
BOSS_SIZE       = (3.0, 1.5, 1.0)

# ── Top lid (PART B) ──────────────────────────────────────────────────────────
LID_T           = 3.0
LID_LIP         = 2.0
LID_SNAP_CNT    = 4
LID_SNAP_L      = 6.0
LID_SNAP_T      = 1.0
LID_SNAP_HOOK   = 1.0
LID_MCU_VENT_R  = 3.8
LID_MCU_VENT_GAP = 1.0

# ── Exterior port cutouts ──────────────────────────────────────────────────────
USB_C_CUT       = (12.0, 6.5)          # USB-C port opening (W × H)
USB_C_POS       = (15.0, -8.0)         # centre (Y, Z) on left wall — Z from mid-height
USB_A_CUT       = (15.5, 8.0)          # USB-A port opening (W × H)
USB_A_POS       = (0.0, -8.0)          # centre (Y, Z) on left wall
DC_CUT_R        = 7.0                  # DC barrel jack radius
DC_POS          = (-15.0, -8.0)        # centre (Y, Z) on left wall
GSM_ANT_R       = 3.25                 # GSM SMA antenna port radius (∅6.5 mm)
BTN_CUT         = (16.0, 10.0)         # power button opening (W × H)
BTN_POS         = (20.0, 0.0)          # centre (X, Z) on front wall — shifted to clear TFT bezel
BTN_RX          = 2.0
SIM_CUT         = (15.0, 3.5)          # SIM card slot
SIM_POS         = (48.0, -11.0)        # UPDATED X to match new GSM_ORIG

# ── Front wall ventilation ─────────────────────────────────────────────────────
VENT_FRONT_R    = 3.5                  # circle vent radius
VENT_FRONT_GAP  = 3.0                  # min wall between vents


# ==============================================================================
# SECTION 2 — HELPER FUNCTIONS
# ==============================================================================

def hex_grid(centre_x, centre_y, area_w, area_h, cell_r, gap, margin=0):
    """
    Returns list of (x, y) hex cell centres (pointy-top orientation)
    that fit entirely inside the rectangle:
        [centre_x - area_w/2 + margin,  centre_x + area_w/2 - margin]
        [centre_y - area_h/2 + margin,  centre_y + area_h/2 - margin]
    cell_r  = circumradius of hex
    gap     = minimum wall between adjacent cells
    A cell is included only if its entire bounding circle fits inside
    the clipped area.
    """
    x_min = centre_x - area_w / 2.0 + margin + cell_r
    x_max = centre_x + area_w / 2.0 - margin - cell_r
    y_min = centre_y - area_h / 2.0 + margin + cell_r
    y_max = centre_y + area_h / 2.0 - margin - cell_r

    if x_min > x_max or y_min > y_max:
        return []

    # Pointy-top hex dimensions
    w_hex = math.sqrt(3.0) * cell_r
    h_hex = 2.0 * cell_r

    dx = w_hex + gap
    dy = 1.5 * cell_r + gap * (math.sqrt(3.0) / 2.0)

    # Let's cover a grid and filter
    centres = []
    # Approximate row/col bounds
    col_range = range(-int(area_w / dx) - 2, int(area_w / dx) + 2)
    row_range = range(-int(area_h / dy) - 2, int(area_h / dy) + 2)

    for r in row_range:
        y = centre_y + r * dy
        for c in col_range:
            # Shift every other row
            x = centre_x + c * dx + (0.5 * dx if r % 2 != 0 else 0)
            # Check if entire bounding circle of radius cell_r is within bounds
            if (x_min <= x <= x_max) and (y_min <= y <= y_max):
                centres.append((x, y))

    return centres


def make_peg(workplane, cx, cy, peg_r, pilot_r, peg_h):
    """
    From a workplane on the interior floor, add one standoff peg at (cx, cy):
      - Solid cylinder radius=peg_r, height=peg_h
      - Axial pilot hole radius=pilot_r through full peg height
    Returns updated workplane.
    """
    # Create the solid boss
    workplane = workplane.center(cx, cy).circle(peg_r).extrude(peg_h)
    # Cut the pilot hole
    workplane = workplane.faces(">Z").circle(pilot_r).cutThruAll()
    # Return to previous coordinates
    return workplane.center(-cx, -cy)


def cut_hex_array(solid, centres, cell_r, depth):
    """
    Given a CQ solid and a list of (x, y) hex centres (in the top-face
    plane), cut pointy-top hexagonal prisms of given depth through the
    solid at each centre. Returns the cut solid.
    """
    if not centres:
        return solid

    # Define a single pointy-top hexagon wire
    # Vertices of a pointy-top hex: 0, 60, 120, 180, 240, 300 degrees rotated to pointy-top
    # A pointy top means vertices are at (0, R), (w/2, R/2), etc.
    # Vertex angles: 90, 150, 210, 270, 330, 30 degrees.
    hex_pts = []
    for i in range(6):
        angle = math.radians(30.0 + 60.0 * i)
        hex_pts.append((cell_r * math.cos(angle), cell_r * math.sin(angle)))

    # We will create a sketch or a series of extrude-cuts on the face
    # Let's use the local face workplane
    loc_wp = solid.faces(">Z").workplane()
    for cx, cy in centres:
        # Instead of moving the coordinate system center, we can just use points offset by (cx, cy)
        translated_hex = [(x + cx, y + cy) for x, y in hex_pts]
        loc_wp = loc_wp.polyline(translated_hex).close().cutBlind(-depth)
    
    # Return a Workplane containing only the resulting solid
    return cq.Workplane("XY").newObject([loc_wp.findSolid()])


def j_slot_profile(push_depth, rot_deg, inner_r, tab_w):
    # This helper is kept as a placeholder since we will use the simpler,
    # more numerically stable dual-cut approach specified in Section 6, Rule 7.
    pass


# ==============================================================================
# SECTION 3 — BUILD SEQUENCE
# ==============================================================================

# Note: We use sequential rectangular cuts for J-slots (Section 6, Rule 7)
# for numerical stability.

def build_main_enclosure() -> cq.Workplane:
    print("Building PART A — main_enclosure...")

    # A1 — Outer shell
    print("  A1 shell...")
    # Base box centered at (0, 0) with floor at Z = 0
    box = cq.Workplane("XY").box(L, W, H, centered=(True, True, False))
    # Fillet outer vertical edges (vertical edges are parallel to Z)
    box = box.edges("|Z").fillet(R_OUTER)

    # Inner cavity: L-2T x W-2T x H-T, starting at Z=T
    inner_cavity = cq.Workplane("XY").workplane(offset=T).box(
        L - 2.0*T, W - 2.0*T, H - T + 1.0, centered=(True, True, False)
    )
    inner_cavity = inner_cavity.edges("|Z").fillet(R_INNER)

    enclosure = box.cut(inner_cavity)
    assert enclosure.val() is not None and enclosure.val().isValid(), "Step A1 failed validation"
    print("  A1 shell... ok")

    # A2 — MCU bay (Arduino pre-assembled acrylic case tray)
    # Spec:
    #   • Flat-floored rectangular bay MCU_CASE (68×88mm footprint) at MCU_ORIG, floor at Z=T
    #   • 3 locating lip walls: 3mm tall × T thick on back (+Y) and both long sides (±X)
    #   • Front face (port side, minus_y) stays open — aligns to left-wall inner face
    #   • 2 M3 retention boss pegs at MCU_BOSS_POS: h=5mm, r=4mm, pilot ∅3mm
    #   • Assert: bay port face aligns with USB_POS / DC_POS left-wall cutouts
    print("  A2 MCU bay...")

    bay_cx = MCU_ORIG[0]
    bay_cy = MCU_ORIG[1]
    bay_w  = MCU_CASE[0]   # 68 mm — X (width)
    bay_d  = MCU_CASE[1]   # 88 mm — Y (depth)

    # ── Step 1: cut flat-floored bay into interior ──────────────────────────────────
    # The inner cavity already opens the interior, but we cut explicitly to
    # ensure a clean, perfectly flat bay floor at Z=T with exact footprint.
    bay_cut = (
        cq.Workplane("XY")
        .workplane(offset=T)
        .box(bay_w, bay_d, INT_H + 1.0, centered=(True, True, False))
        .translate((bay_cx, bay_cy, 0))
    )
    enclosure = enclosure.cut(bay_cut)

    # ── Step 2: 3 locating lip walls (3mm tall × T thick) ────────────────────────
    # Lips sit on the bay floor (Z=T) and rise MCU_LIP_H=3mm to grip the case sides.

    # Left lip wall — plus-X side of bay
    left_lip = (
        cq.Workplane("XY").workplane(offset=T)
        .box(MCU_LIP_T, bay_d, MCU_LIP_H, centered=(False, True, False))
        .translate((bay_cx + bay_w / 2.0, bay_cy, 0))
    )
    enclosure = enclosure.union(left_lip)

    # Right lip wall — minus-X side of bay
    right_lip = (
        cq.Workplane("XY").workplane(offset=T)
        .box(MCU_LIP_T, bay_d, MCU_LIP_H, centered=(False, True, False))
        .translate((bay_cx - bay_w / 2.0 - MCU_LIP_T, bay_cy, 0))
    )
    enclosure = enclosure.union(right_lip)

    # Back lip wall — plus-Y side, spans full bay width including side lips
    back_lip = (
        cq.Workplane("XY").workplane(offset=T)
        .box(bay_w + 2.0 * MCU_LIP_T, MCU_LIP_T, MCU_LIP_H, centered=(True, False, False))
        .translate((bay_cx, bay_cy + bay_d / 2.0, 0))
    )
    enclosure = enclosure.union(back_lip)
    # ── 2× retention bosses on floor (engage Arduino case rear bosses) ────────
    for bx_rel, by_rel in MCU_BOSS_POS:
        boss_cx = bay_cx + bx_rel
        boss_cy = bay_cy + by_rel
        # Assert boss stays within bay footprint
        assert abs(bx_rel) < bay_w / 2.0 - MCU_BOSS_R, "MCU boss outside bay X!"
        assert by_rel < bay_d / 2.0 - MCU_BOSS_R,       "MCU boss outside bay Y!"
        # Build boss cylinder
        boss = cq.Workplane("XY").workplane(offset=T).cylinder(
            MCU_BOSS_H, MCU_BOSS_R, centered=(True, True, False)
        ).translate((boss_cx, boss_cy, 0))
        # Drill M3 pilot hole through boss
        boss = boss.faces(">Z").workplane().circle(MCU_PILOT_R).cutBlind(-MCU_BOSS_H)
        enclosure = enclosure.union(boss)

    # Front face (minus-Y side) is intentionally left OPEN for port access.

    # ── Step 4: port-face alignment assertion ─────────────────────────────────
    # USB-C and DC jack are at Z=+8mm from the case floor inside the acrylic case.
    # Case floor sits at Z=T. So absolute port Z = T + 8.0 mm.
    # USB_POS and DC_POS give (Y, Z) offsets from enclosure mid-height on left wall:
    #   abs_z = H/2 + POS[1]
    # Tolerance ±2mm is acceptable for the Z alignment check.
    case_port_z = T + 8.0                    # = 2.5 + 8.0 = 10.5 mm
    usb_abs_z   = H / 2.0 + USB_C_POS[1]    # = 19.0 + (-8.0) = 11.0 mm
    dc_abs_z    = H / 2.0 + DC_POS[1]       # = 19.0 + (-8.0) = 11.0 mm
    assert abs(case_port_z - usb_abs_z) <= 2.0, (
        f"USB-C Z misalignment: case port at {case_port_z:.1f}mm, "
        f"left-wall cutout at {usb_abs_z:.1f}mm (delta={case_port_z-usb_abs_z:.1f})"
    )
    assert abs(case_port_z - dc_abs_z) <= 2.0, (
        f"DC jack Z misalignment: case port at {case_port_z:.1f}mm, "
        f"left-wall cutout at {dc_abs_z:.1f}mm (delta={case_port_z-dc_abs_z:.1f})"
    )

    assert enclosure.val() is not None and enclosure.val().isValid(), "Step A2 failed validation"
    print(f"  A2 MCU bay... ok  [port Z={case_port_z:.1f}mm, USB cutout Z={usb_abs_z:.1f}mm ✓]")

    # A3 — GSM motherboard pegs (4×)
    print("  A3 GSM pegs...")
    dx_gsm = GSM_BOARD[0]/2.0 - GSM_PEG_INSET
    dy_gsm = GSM_BOARD[1]/2.0 - GSM_PEG_INSET
    gsm_pegs = [
        (GSM_ORIG[0] - dx_gsm, GSM_ORIG[1] - dy_gsm),
        (GSM_ORIG[0] + dx_gsm, GSM_ORIG[1] - dy_gsm),
        (GSM_ORIG[0] + dx_gsm, GSM_ORIG[1] + dy_gsm),
        (GSM_ORIG[0] - dx_gsm, GSM_ORIG[1] + dy_gsm)
    ]

    gsm_pegs_solid = cq.Workplane("XY").workplane(offset=T)
    gsm_pegs_solid = gsm_pegs_solid.pushPoints(gsm_pegs).circle(GSM_PEG_R).extrude(GSM_PEG_H)
    gsm_pegs_solid = gsm_pegs_solid.faces(">Z").circle(GSM_PILOT_R).cutThruAll()

    for px, py in gsm_pegs:
        # Ensure it doesn't intersect walls or dock
        assert abs(px) < (L/2.0 - T - GSM_PEG_R), "GSM peg intersects outer walls!"
        assert abs(py) < (W/2.0 - T - GSM_PEG_R), "GSM peg intersects outer walls!"

    enclosure = enclosure.union(gsm_pegs_solid)
    assert enclosure.val() is not None and enclosure.val().isValid(), "Step A3 failed validation"
    print("  A3 GSM pegs... ok")

    # A4 — Sensor pocket + divider wall
    # FIX 4: build order is critical:
    #   1. Cut the pocket interior first (removes dock volume)
    #   2. THEN union the divider wall (so pocket cut does NOT erase it)
    print("  A4 Sensor pocket...")

    # 4a: Cut the pocket interior. Centred at DOCK_ORIG, full INT_H depth.
    pocket_cut = (
        cq.Workplane("XY").workplane(offset=T)
        .box(DOCK_INNER[0], DOCK_INNER[1], INT_H + 1.0, centered=(True, True, False))
        .translate((DOCK_ORIG[0], DOCK_ORIG[1], 0))
    )
    enclosure = enclosure.cut(pocket_cut)

    # 4b: Union divider wall AFTER pocket cut so it survives.
    # Divider is placed directly to the LEFT of the pocket (X range: [31.5, 34.0]).
    # Spans from pocket front (Y = -12.0) to back wall (Y = 45.0) to avoid intersecting
    # the GSM board in the front-right zone.
    # Height goes from floor (Z = T) to top (Z = H = T + INT_H).
    div_cx = DOCK_ORIG[0] - DOCK_INNER[0] / 2.0 - DOCK_DIV_T / 2.0  # = 32.75 mm (outside pocket)
    div_cy = (45.0 - 12.0) / 2.0                                    # = 16.5 mm
    div_dy = 45.0 - (-12.0)                                         # = 57.0 mm Y length
    divider = (
        cq.Workplane("XY")
        .box(DOCK_DIV_T, div_dy, INT_H, centered=(True, True, False))
        .translate((div_cx, div_cy, T))                              # Z-translate by T = 2.5 mm
    )
    assert divider.val() is not None and divider.val().isValid(), "Divider wall invalid!"
    enclosure = enclosure.union(divider)

    # 4c: Recess female header into pocket floor (centred at DOCK_ORIG, Z=T)
    header_cut = (
        cq.Workplane("XY").workplane(offset=T - 1.0)
        .box(HDR_FIXED[0], HDR_FIXED[1], HDR_FIXED[2] + 1.0, centered=(True, True, False))
        .translate((DOCK_ORIG[0], DOCK_ORIG[1], 0))
    )

    enclosure = enclosure.cut(header_cut)
    assert enclosure.val() is not None and enclosure.val().isValid(), "Step A4 failed validation"
    print("  A4 Sensor pocket... ok")

    # A5 — Pocket rim rebate (flush door seat)
    print("  A5 Pocket rim rebate...")
    # On the top face of the enclosure (Z=H), cut a rebate of REBATE_OPEN, depth REBATE_DEPTH, fillet corner radius REBATE_RX
    rebate = cq.Workplane("XY").workplane(offset=H - REBATE_DEPTH).box(
        REBATE_OPEN[0], REBATE_OPEN[1], REBATE_DEPTH + 1.0, centered=(True, True, False)
    )
    # Fillet rebate vertical edges
    rebate = rebate.edges("|Z").fillet(REBATE_RX)
    rebate = rebate.translate((DOCK_ORIG[0], DOCK_ORIG[1], 0))

    enclosure = enclosure.cut(rebate)
    assert enclosure.val() is not None and enclosure.val().isValid(), "Step A5 failed validation"
    print("  A5 Pocket rim rebate... ok")

    # A6 — Bayonet J-slot receivers (2×)
    print("  A6 Bayonet J-slots...")
    # Location: midpoint of each Y-axis pocket rim wall (y = DOCK_ORIG[1] +/- DOCK_INNER[1]/2)
    # Midpoint coordinates: (DOCK_ORIG[0], DOCK_ORIG[1] - DOCK_INNER[1]/2) and (DOCK_ORIG[0], DOCK_ORIG[1] + DOCK_INNER[1]/2)
    # 4 mm below pocket top edge (which is at Z = H - REBATE_DEPTH = 35.0 mm). Slot is 2.2 mm tall. Z range is 32.8 to 35.0 mm.
    # Let's perform two cuts per slot:
    # 1. Vertical entry slot (from Z = H - REBATE_DEPTH down by BAY_PUSH + BAY_SLOT_H = 3.2 mm)
    # 2. Horizontal ledge slot (extending in the clockwise direction, i.e., rotating 25 degrees on the circle)
    # We can model these as boxes cutting into the pocket walls.
    # The inner pocket Y-walls are at Y = DOCK_ORIG[1] - DOCK_INNER[1]/2 and Y = DOCK_ORIG[1] + DOCK_INNER[1]/2
    # Pocket width along Y is 48 mm. So Y walls are at y = 12 - 24 = -12 and y = 12 + 24 = 36.
    # Tab drops in at the midpoint: X = DOCK_ORIG[0] = 50.0.
    
    # We cut into the walls (depth BAY_SLOT_D = 2.0 mm)
    # For minus-Y wall (y = -12): we cut in -Y direction: depth from y = -12 is to y = -14.
    # For plus-Y wall (y = 36): we cut in +Y direction: depth from y = 36 is to y = 38.

    # 1. Vertical entry cuts:
    # Width along X = BAY_SLOT_W (4.5)
    # Height Z: from Z = H - REBATE_DEPTH = 35.0 down to 35.0 - (BAY_PUSH + BAY_SLOT_H) = 31.8
    # Depth Y: cut 2.0 mm deep
    v_cut_my = cq.Workplane("XY").workplane(offset=35.0 - (BAY_PUSH + BAY_SLOT_H)).box(
        BAY_SLOT_W, BAY_SLOT_D + 0.1, BAY_PUSH + BAY_SLOT_H + 0.1, centered=(True, False, False)
    ).translate((DOCK_ORIG[0], DOCK_ORIG[1] - DOCK_INNER[1]/2.0 - 0.05, 0))

    v_cut_py = cq.Workplane("XY").workplane(offset=35.0 - (BAY_PUSH + BAY_SLOT_H)).box(
        BAY_SLOT_W, BAY_SLOT_D + 0.1, BAY_PUSH + BAY_SLOT_H + 0.1, centered=(True, False, False)
    ).translate((DOCK_ORIG[0], DOCK_ORIG[1] + DOCK_INNER[1]/2.0 - BAY_SLOT_D - 0.05, 0))

    enclosure = enclosure.cut(v_cut_my).cut(v_cut_py)

    # 2. Horizontal ledge cuts:
    # Starting from the entry mouth, extending clockwise.
    # Looking from top, clockwise rotation moves the door.
    # On minus-Y wall (bottom wall, looking from top), a clockwise rotation rotates the tab to the LEFT (minus X).
    # On plus-Y wall (top wall, looking from top), a clockwise rotation rotates the tab to the RIGHT (plus X).
    # Arc length for rotation: we'll estimate the arc length as: L_arc = (DOCK_INNER[1]/2.0) * radians(25) = 24 * 0.436 = 10.46 mm.
    # Let's make the horizontal cut box length along X matching this.
    arc_len = (DOCK_INNER[1]/2.0) * math.radians(BAY_SLOT_ROT) # ~10.47 mm

    # Ledge height Z: from Z = 35.0 - (BAY_PUSH + BAY_SLOT_H) to 35.0 - BAY_PUSH = 34.0 (thickness 2.2 mm)
    # Ledge X range:
    # For minus-Y wall: starts at X=50 and goes to X = 50 - arc_len
    # For plus-Y wall: starts at X=50 and goes to X = 50 + arc_len
    h_cut_my = cq.Workplane("XY").workplane(offset=35.0 - (BAY_PUSH + BAY_SLOT_H)).box(
        arc_len + BAY_SLOT_W/2.0, BAY_SLOT_D + 0.1, BAY_SLOT_H, centered=(False, False, False)
    ).translate((DOCK_ORIG[0] - arc_len, DOCK_ORIG[1] - DOCK_INNER[1]/2.0 - 0.05, 0))

    h_cut_py = cq.Workplane("XY").workplane(offset=35.0 - (BAY_PUSH + BAY_SLOT_H)).box(
        arc_len + BAY_SLOT_W/2.0, BAY_SLOT_D + 0.1, BAY_SLOT_H, centered=(False, False, False)
    ).translate((DOCK_ORIG[0] - BAY_SLOT_W/2.0, DOCK_ORIG[1] + DOCK_INNER[1]/2.0 - BAY_SLOT_D - 0.05, 0))

    enclosure = enclosure.cut(h_cut_my).cut(h_cut_py)
    assert enclosure.val() is not None and enclosure.val().isValid(), "Step A6 failed validation"
    print("  A6 Bayonet J-slots... ok")

    # A7 — Lid snap receiver slots (4×)
    print("  A7 Lid snap slots...")
    # Outer box was L x W x H. Inner walls are at +/- (L/2 - T) and +/- (W/2 - T)
    # Snap receivers: one per wall, centered on wall, at upper rim
    # Slot size: W_slot = LID_SNAP_L + 0.3, H_slot = LID_SNAP_T + 0.3, depth = T
    slot_w_val = LID_SNAP_L + 0.3
    slot_h_val = LID_SNAP_T + 0.3
    
    # Left slot: on wall X = -L/2 + T. Cut into the wall.
    slot_l = cq.Workplane("XY").workplane(offset=H - slot_h_val - 1.0).box(
        T + 0.2, slot_w_val, slot_h_val, centered=(False, True, False)
    ).translate((-L/2.0 - 0.1, 0, 0))

    # Right slot: on wall X = L/2 - T
    slot_r = cq.Workplane("XY").workplane(offset=H - slot_h_val - 1.0).box(
        T + 0.2, slot_w_val, slot_h_val, centered=(False, True, False)
    ).translate((L/2.0 - T - 0.1, 0, 0))

    # Front slot: on wall Y = -W/2 + T
    slot_f = cq.Workplane("XY").workplane(offset=H - slot_h_val - 1.0).box(
        slot_w_val, T + 0.2, slot_h_val, centered=(True, False, False)
    ).translate((0, -W/2.0 - 0.1, 0))

    # Back slot: on wall Y = W/2 - T
    slot_b = cq.Workplane("XY").workplane(offset=H - slot_h_val - 1.0).box(
        slot_w_val, T + 0.2, slot_h_val, centered=(True, False, False)
    ).translate((0, W/2.0 - T - 0.1, 0))

    enclosure = enclosure.cut(slot_l).cut(slot_r).cut(slot_f).cut(slot_b)
    assert enclosure.val() is not None and enclosure.val().isValid(), "Step A7 failed validation"
    print("  A7 Lid snap slots... ok")

    # A8 — Exterior port cutouts
    # We model cutouts as stable YZ/XZ solid bodies and cut them from the enclosure.
    print("  A8 Port cutouts...")

    # 1. USB-C port on left wall (X = -L/2)
    #   USB_C_POS = (Y=15.0, Z=-8.0) relative to mid-height
    #   Absolute Z = 11.0 mm
    usb_c_cut = (
        cq.Workplane("YZ").workplane(offset=-L/2.0 - 0.1)
        .box(USB_C_CUT[0], USB_C_CUT[1], T + 0.5, centered=(True, True, False))
        .translate((0, USB_C_POS[0], H/2.0 + USB_C_POS[1]))
    )
    enclosure = enclosure.cut(usb_c_cut)

    # 2. USB-A port on left wall (X = -L/2)
    #   USB_A_POS = (Y=0.0, Z=-8.0) relative to mid-height
    #   Absolute Z = 11.0 mm
    usb_a_cut = (
        cq.Workplane("YZ").workplane(offset=-L/2.0 - 0.1)
        .box(USB_A_CUT[0], USB_A_CUT[1], T + 0.5, centered=(True, True, False))
        .translate((0, USB_A_POS[0], H/2.0 + USB_A_POS[1]))
    )
    enclosure = enclosure.cut(usb_a_cut)

    # 3. DC barrel jack circular hole on left wall (X = -L/2)
    #   DC_POS = (Y=-15.0, Z=-8.0) relative to mid-height
    #   Absolute Z = 11.0 mm
    dc_cut_body = (
        cq.Workplane("YZ").workplane(offset=-L/2.0 - 0.1)
        .cylinder(T + 0.5, DC_CUT_R, centered=(True, True, False))
        .translate((0, DC_POS[0], H/2.0 + DC_POS[1]))
    )
    enclosure = enclosure.cut(dc_cut_body)

    # 4. GSM SMA Antenna port on right wall (X = L/2 = 67.5 mm)
    #   Antenna is centered on the GSM board Y position (Y = -28.0)
    #   Absolute Z = 11.0 mm
    gsm_ant_cut = (
        cq.Workplane("YZ").workplane(offset=L/2.0 - T - 0.1)  # offset inside the wall
        .cylinder(T + 0.5, GSM_ANT_R, centered=(True, True, False))
        .translate((0, GSM_ORIG[1], H/2.0 - 8.0))
    )
    enclosure = enclosure.cut(gsm_ant_cut)

    # Front wall (Y = -W/2) cutouts — unchanged
    # Power button: rect BTN_CUT, filleted r=BTN_RX, centre at BTN_POS (X, Z)
    btn_cut_body = cq.Workplane("XZ").workplane(offset=-W/2.0 - 0.1).box(
        BTN_CUT[0], BTN_CUT[1], T + 0.5, centered=(True, True, False)
    )
    btn_cut_body = btn_cut_body.edges("|Y").fillet(BTN_RX)
    btn_cut_body = btn_cut_body.translate((BTN_POS[0], 0, H/2.0 + BTN_POS[1]))
    enclosure = enclosure.cut(btn_cut_body)

    # SIM slot: rect SIM_CUT, centre at SIM_POS
    sim_cut_body = cq.Workplane("XZ").workplane(offset=-W/2.0 - 0.1).box(
        SIM_CUT[0], SIM_CUT[1], T + 0.5, centered=(True, True, False)
    ).translate((SIM_POS[0], 0, H/2.0 + SIM_POS[1]))
    enclosure = enclosure.cut(sim_cut_body)
    assert enclosure.val() is not None and enclosure.val().isValid(), "Step A8 failed validation"
    print("  A8 Port cutouts... ok")

    # A9 — Front wall circular vents
    print("  A9 Front vents...")
    # Single row of circles r=VENT_FRONT_R, Z-centred at INT_H / 2 (approx 17.75 mm)
    # Span the sensor dock X-range (DOCK_ORIG[0] +/- DOCK_INNER[0]/2) -> [34, 66]
    # Minimum wall between circles: VENT_FRONT_GAP (3.0 mm)
    # Center-to-center spacing = 2 * VENT_FRONT_R + VENT_FRONT_GAP = 7.0 + 3.0 = 10.0 mm
    # X centers: 34 + 3.5 = 37.5, 47.5, 57.5, 65.0? Let's fit them symmetrically about DOCK_ORIG[0] (50.0)
    # 50.0, 40.0, 60.0. (Next would be 30.0 and 70.0 which are outside [34, 66]).
    vent_xs = [40.0, 50.0, 60.0]
    for vx in vent_xs:
        vent_circle = cq.Workplane("XZ").workplane(offset=-W/2.0 - 0.1).cylinder(
            T + 0.5, VENT_FRONT_R, centered=(True, True, False)
        ).translate((vx, 0, INT_H / 2.0))
        enclosure = enclosure.cut(vent_circle)
    assert enclosure.val() is not None and enclosure.val().isValid(), "Step A9 failed validation"
    print("  A9 Front vents... ok")

    # A10 — GSM floor vents
    # 3 circular vents (∅4 mm) on the floor of the enclosure underneath the GSM module
    # to allow bottom-to-top convection air current.
    print("  A10 GSM floor vents...")
    for vy in [-34.0, -28.0, -22.0]:
        floor_vent = cq.Workplane("XY").cylinder(T + 1.0, 2.0, centered=(True, True, True)).translate((48.0, vy, T / 2.0))
        enclosure = enclosure.cut(floor_vent)
    assert enclosure.val() is not None and enclosure.val().isValid(), "Step A10 failed validation"
    print("  A10 GSM floor vents... ok")

    return enclosure


def build_top_lid() -> cq.Workplane:
    print("Building PART B — top_lid...")

    # B1 — Lid plate
    print("  B1 Lid plate...")
    # Lid thickness is LID_T, top of lid at Z=H + LID_T. Let's model it at Z=0 and translate later.
    lid = cq.Workplane("XY").box(L, W, LID_T, centered=(True, True, False))
    lid = lid.edges("|Z").fillet(R_OUTER)

    # Mill inset lip on underside perimeter: recess LID_LIP deep x T wide, FIT_SLIDE clearance
    # Inner lip outer dims: (L - 2*T - 2*FIT_SLIDE) x (W - 2*T - 2*FIT_SLIDE)
    lip_w = L - 2.0*T - 2.0*FIT_SLIDE
    lip_h = W - 2.0*T - 2.0*FIT_SLIDE
    
    # Create outer lip solid
    lip_outer = cq.Workplane("XY").workplane(offset=-LID_LIP).box(
        lip_w, lip_h, LID_LIP + 0.1, centered=(True, True, False)
    ).edges("|Z").fillet(R_INNER)
    
    # Create inner cutout to make it a hollow rim (wall thickness T = 2.5 mm)
    lip_inner = cq.Workplane("XY").workplane(offset=-LID_LIP - 0.1).box(
        lip_w - 2.0*T, lip_h - 2.0*T, LID_LIP + 0.3, centered=(True, True, False)
    ).edges("|Z").fillet(max(1.0, R_INNER - T))
    
    lip = lip_outer.cut(lip_inner)

    # Combine lip with lid plate
    lid = lid.union(lip)
    assert lid.val() is not None and lid.val().isValid(), "Step B1 failed validation"
    print("  B1 Lid plate... ok")

    # B2 — TFT viewport cutout
    print("  B2 TFT viewport...")
    tft_cut = cq.Workplane("XY").box(
        TFT_VIEWPORT[0], TFT_VIEWPORT[1], LID_T + LID_LIP + 1.0, centered=(True, True, True)
    )
    tft_cut = tft_cut.edges("|Z").fillet(1.5)
    tft_cut = tft_cut.translate((TFT_ORIG[0], TFT_ORIG[1], 0))
    lid = lid.cut(tft_cut)
    assert lid.val() is not None and lid.val().isValid(), "Step B2 failed validation"
    print("  B2 TFT viewport... ok")

    # B3 — Sensor pocket aperture (FIX 5)
    # Full through-cut through the lid plate, centred on DOCK_ORIG.
    # Fillet inner vertical edges r=REBATE_RX after cut.
    print("  B3 Sensor aperture...")
    sensor_ap = (
        cq.Workplane("XY")
        .box(REBATE_OPEN[0], REBATE_OPEN[1], LID_T + LID_LIP + 1.0, centered=(True, True, True))
        .translate((DOCK_ORIG[0], DOCK_ORIG[1], 0))
    )
    sensor_ap = sensor_ap.edges("|Z").fillet(REBATE_RX)
    lid = lid.cut(sensor_ap)
    # Verify aperture area matches spec: 34.6 × 50.6 mm centred at (+50, +12)
    assert abs(REBATE_OPEN[0] - 34.6) < 0.01, f"Aperture X mismatch: {REBATE_OPEN[0]}"
    assert abs(REBATE_OPEN[1] - 50.6) < 0.01, f"Aperture Y mismatch: {REBATE_OPEN[1]}"
    assert lid.val() is not None and lid.val().isValid(), "Step B3 failed validation"
    print(f"  B3 Sensor aperture... ok  [{REBATE_OPEN[0]:.1f}×{REBATE_OPEN[1]:.1f}mm @ ({DOCK_ORIG[0]},{DOCK_ORIG[1]}) ✓]")

    # B4 — Lid snap clips (4×)
    print("  B4 Snap clips...")
    # Tab dims: LID_SNAP_T x 4 mm x LID_SNAP_L extending downward from lid underside (Z=-LID_LIP)
    # Hook: LID_SNAP_HOOK outward at free end.
    # One clip per wall, centered.
    # Let's model clips relative to the inner walls:
    # Left clip (inside left lip wall at X = -lip_w/2)
    clip_l = cq.Workplane("XY").workplane(offset=-LID_LIP - LID_SNAP_L).box(
        LID_SNAP_T, 4.0, LID_SNAP_L, centered=(False, True, False)
    ).translate((-lip_w/2.0, 0, 0))
    # Hook for left clip (pointing left: -X direction)
    hook_l = cq.Workplane("XY").workplane(offset=-LID_LIP - LID_SNAP_L).box(
        LID_SNAP_HOOK, 4.0, 1.0, centered=(False, True, False)
    ).translate((-lip_w/2.0 - LID_SNAP_HOOK, 0, 0))

    # Right clip (inside right lip wall at X = lip_w/2)
    clip_r = cq.Workplane("XY").workplane(offset=-LID_LIP - LID_SNAP_L).box(
        LID_SNAP_T, 4.0, LID_SNAP_L, centered=(False, True, False)
    ).translate((lip_w/2.0 - LID_SNAP_T, 0, 0))
    hook_r = cq.Workplane("XY").workplane(offset=-LID_LIP - LID_SNAP_L).box(
        LID_SNAP_HOOK, 4.0, 1.0, centered=(False, True, False)
    ).translate((lip_w/2.0 - LID_SNAP_T + LID_SNAP_T, 0, 0))

    # Front clip (inside front lip wall at Y = -lip_h/2)
    clip_f = cq.Workplane("XY").workplane(offset=-LID_LIP - LID_SNAP_L).box(
        4.0, LID_SNAP_T, LID_SNAP_L, centered=(True, False, False)
    ).translate((0, -lip_h/2.0, 0))
    hook_f = cq.Workplane("XY").workplane(offset=-LID_LIP - LID_SNAP_L).box(
        4.0, LID_SNAP_HOOK, 1.0, centered=(True, False, False)
    ).translate((0, -lip_h/2.0 - LID_SNAP_HOOK, 0))

    # Back clip (inside back lip wall at Y = lip_h/2)
    clip_b = cq.Workplane("XY").workplane(offset=-LID_LIP - LID_SNAP_L).box(
        4.0, LID_SNAP_T, LID_SNAP_L, centered=(True, False, False)
    ).translate((0, lip_h/2.0 - LID_SNAP_T, 0))
    hook_b = cq.Workplane("XY").workplane(offset=-LID_LIP - LID_SNAP_L).box(
        4.0, LID_SNAP_HOOK, 1.0, centered=(True, False, False)
    ).translate((0, lip_h/2.0 - LID_SNAP_T + LID_SNAP_T, 0))

    lid = lid.union(clip_l).union(hook_l).union(clip_r).union(hook_r).union(clip_f).union(hook_f).union(clip_b).union(hook_b)
    assert lid.val() is not None and lid.val().isValid(), "Step B4 failed validation"
    print("  B4 Snap clips... ok")

    # B5 — MCU zone honeycomb vents
    print("  B5 Honeycomb vents...")
    # Area centered on MCU_ORIG with dimensions MCU_CASE[0]-8, MCU_CASE[1]-8
    centres = hex_grid(
        MCU_ORIG[0], MCU_ORIG[1], MCU_CASE[0] - 8.0, MCU_CASE[1] - 8.0,
        LID_MCU_VENT_R, LID_MCU_VENT_GAP, margin=4.0
    )
    # Exclude any cells crossing the lid apertures (TFT viewport and sensor pocket)
    valid_centres = []
    for cx, cy in centres:
        # TFT viewport footprint check
        tft_overlap = (TFT_ORIG[0] - TFT_VIEWPORT[0]/2.0 - 2.0 <= cx <= TFT_ORIG[0] + TFT_VIEWPORT[0]/2.0 + 2.0) and \
                      (TFT_ORIG[1] - TFT_VIEWPORT[1]/2.0 - 2.0 <= cy <= TFT_ORIG[1] + TFT_VIEWPORT[1]/2.0 + 2.0)
        # Sensor aperture footprint check
        sensor_overlap = (DOCK_ORIG[0] - REBATE_OPEN[0]/2.0 - 2.0 <= cx <= DOCK_ORIG[0] + REBATE_OPEN[0]/2.0 + 2.0) and \
                         (DOCK_ORIG[1] - REBATE_OPEN[1]/2.0 - 2.0 <= cy <= DOCK_ORIG[1] + REBATE_OPEN[1]/2.0 + 2.0)
        if not tft_overlap and not sensor_overlap:
            valid_centres.append((cx, cy))

    # Cut the honeycomb vents through the lid plate
    lid = cut_hex_array(lid, valid_centres, LID_MCU_VENT_R, LID_T + 1.0)
    assert lid.val() is not None and lid.val().isValid(), "Step B5 failed validation"
    print("  B5 Honeycomb vents... ok")

    # B6 — Lid pry notch
    # A small notch is cut on the back edge (Y = W/2) of the lid top face
    # so a flathead tool or fingernail can pry the snap-fit lid open.
    print("  B6 Lid pry notch...")
    pry_notch = cq.Workplane("XY").workplane(offset=LID_T - 1.5).box(
        12.0, 3.5, 2.0, centered=(True, False, False)
    ).translate((0, W/2.0 - 2.0, 0))
    lid = lid.cut(pry_notch)
    assert lid.val() is not None and lid.val().isValid(), "Step B6 failed validation"
    print("  B6 Lid pry notch... ok")

    # B7 — TFT display mounting bosses (4x) on lid underside
    # These allow mounting the TFT display module to the lid with M2 screws.
    # Spaced at 66mm × 42mm, height 2.5mm, pilot holes ∅2mm.
    print("  B7 TFT mounting bosses...")
    tft_boss_h = 2.5
    tft_boss_r = 2.5
    tft_pilot_r = 1.0
    tft_dx = TFT_VIEWPORT[0] / 2.0 - 1.0  # = 33.0 mm
    tft_dy = TFT_VIEWPORT[1] / 2.0 - 1.0  # = 21.0 mm
    tft_pegs = [
        (TFT_ORIG[0] - tft_dx, TFT_ORIG[1] - tft_dy),
        (TFT_ORIG[0] + tft_dx, TFT_ORIG[1] - tft_dy),
        (TFT_ORIG[0] + tft_dx, TFT_ORIG[1] + tft_dy),
        (TFT_ORIG[0] - tft_dx, TFT_ORIG[1] + tft_dy)
    ]
    # Create bosses on the lid underside plate plane (Z = -LID_LIP = -2.0)
    tft_bosses = cq.Workplane("XY").workplane(offset=-LID_LIP - tft_boss_h)
    tft_bosses = tft_bosses.pushPoints(tft_pegs).circle(tft_boss_r).extrude(tft_boss_h)
    tft_bosses = tft_bosses.faces(">Z").circle(tft_pilot_r).cutThruAll()
    lid = lid.union(tft_bosses)
    assert lid.val() is not None and lid.val().isValid(), "Step B7 failed validation"
    print("  B7 TFT mounting bosses... ok")

    # B8 — MCU hold-down ribs (2x) on lid underside
    # These extend down from the lid plate underside to Z = 30.7 mm (local Z = -7.3 mm)
    # to hold the Arduino pre-assembled case securely on the floor retention bosses.
    # Placed on the left and right margins of the case to avoid blocking honeycomb vents.
    print("  B8 MCU hold-down ribs...")
    rib_h = 7.3  # extends from plate underside (Z = 0) down to Z = 30.7 mm
    rib1 = cq.Workplane("XY").workplane(offset=-rib_h).box(3.0, 15.0, rib_h, centered=(True, True, False)).translate((-55.0, 10.0, 0))
    rib2 = cq.Workplane("XY").workplane(offset=-rib_h).box(3.0, 15.0, rib_h, centered=(True, True, False)).translate((25.0, 10.0, 0))
    lid = lid.union(rib1).union(rib2)
    assert lid.val() is not None and lid.val().isValid(), "Step B8 failed validation"
    print("  B8 MCU hold-down ribs... ok")

    return lid


def build_vent_door() -> cq.Workplane:
    print("Building PART C — vent_door...")

    # C1 — Door plate
    print("  C1 Door plate...")
    door = cq.Workplane("XY").box(DOOR_OUTER[0], DOOR_OUTER[1], DOOR_T, centered=(True, True, False))
    door = door.edges("|Z").fillet(DOOR_RX)
    assert door.val() is not None and door.val().isValid(), "Step C1 failed validation"
    print("  C1 Door plate... ok")

    # C2 — Honeycomb vent array
    print("  C2 Honeycomb vents...")
    # Hex cells on the full face with margin DOOR_EDGE_MARGIN (4 mm) from edges
    # Exclude central 6x4 mm zone (space for the lock boss)
    centres = hex_grid(0, 0, DOOR_OUTER[0], DOOR_OUTER[1], DOOR_VENT_R, DOOR_VENT_GAP, margin=DOOR_EDGE_MARGIN)
    valid_centres = []
    for cx, cy in centres:
        if abs(cx) <= 3.0 and abs(cy) <= 2.0:
            continue
        valid_centres.append((cx, cy))

    door = cut_hex_array(door, valid_centres, DOOR_VENT_R, DOOR_T + 1.0)
    assert door.val() is not None and door.val().isValid(), "Step C2 failed validation"
    print("  C2 Honeycomb vents... ok")

    # C3 — Bayonet tabs (2×, on underside)
    print("  C3 Bayonet tabs...")
    # One tab at each Y-axis midpoint of the door underside (Y = -DOOR_OUTER[1]/2 + BAY_TAB_INSET and Y = DOOR_OUTER[1]/2 - BAY_TAB_INSET)
    # L-shaped extrusion:
    # Stem: BAY_TAB_W (along X) x BAY_TAB_H (along Y) x (BAY_PUSH + 0.5) mm tall
    # Foot: BAY_TAB_L (along Y) x BAY_TAB_W (along X) x BAY_TAB_H (vertical) extending perpendicular to stem in X-direction.
    # Important: foot must point CLOCKWISE when viewed from above so counter-clockwise rotation unlocks, clockwise locks.
    # Looking from above:
    # For minus-Y wall tab (midpoint bottom): clockwise rotation moves it to the LEFT (minus X). So foot points to the left (-X).
    # For plus-Y wall tab (midpoint top): clockwise rotation moves it to the RIGHT (plus X). So foot points to the right (+X).

    # Stem height needs to create a gap for the slot wall.
    # Gap = BAY_PUSH + 0.2 mm clearance = 1.2 mm.
    # Total stem height = Gap + Foot Height (BAY_TAB_H) = 2.7 mm.
    stem_h = BAY_PUSH + BAY_TAB_H + 0.2

    # Minus-Y tab:
    stem_my = cq.Workplane("XY").workplane(offset=-stem_h).box(
        BAY_TAB_W, BAY_TAB_W, stem_h, centered=(True, True, False)
    ).translate((0, -DOOR_OUTER[1]/2.0 + BAY_TAB_INSET, 0))
    # Foot points to -X (length BAY_TAB_L)
    foot_my = cq.Workplane("XY").workplane(offset=-stem_h).box(
        BAY_TAB_L, BAY_TAB_W, BAY_TAB_H, centered=(True, True, False)
    ).translate((-BAY_TAB_L/2.0, -DOOR_OUTER[1]/2.0 + BAY_TAB_INSET, 0))

    # Plus-Y tab:
    stem_py = cq.Workplane("XY").workplane(offset=-stem_h).box(
        BAY_TAB_W, BAY_TAB_W, stem_h, centered=(True, True, False)
    ).translate((0, DOOR_OUTER[1]/2.0 - BAY_TAB_INSET, 0))
    # Foot points to +X (length BAY_TAB_L)
    foot_py = cq.Workplane("XY").workplane(offset=-stem_h).box(
        BAY_TAB_L, BAY_TAB_W, BAY_TAB_H, centered=(True, True, False)
    ).translate((BAY_TAB_L/2.0, DOOR_OUTER[1]/2.0 - BAY_TAB_INSET, 0))

    door = door.union(stem_my).union(foot_my).union(stem_py).union(foot_py)
    assert door.val() is not None and door.val().isValid(), "Step C3 failed validation"
    print("  C3 Bayonet tabs... ok")

    # C4 — Finger-lift notch
    print("  C4 Finger-lift notch...")
    # On the minus-Y short edge of the door top face: carve a half-ellipse notch 8 mm wide, 3 mm deep, 1.5 mm tall.
    # Center of notch is at X=0, Y=-DOOR_OUTER[1]/2. Z is at top face: Z = DOOR_T - 1.5
    notch = cq.Workplane("XY").workplane(offset=DOOR_T - 1.5).box(
        NOTCH_W, NOTCH_D * 2.0, 1.6, centered=(True, True, False)
    ).translate((0, -DOOR_OUTER[1]/2.0, 0))
    door = door.cut(notch)
    assert door.val() is not None and door.val().isValid(), "Step C4 failed validation"
    print("  C4 Finger-lift notch... ok")

    # C5 — Lock indicator boss
    print("  C5 Lock boss...")
    # Small equilateral triangle 1 mm tall. Base = 3 mm, height = 1.5 mm.
    # Let's define the points of a triangle pointing in +Y direction (or lock direction)
    tri_pts = [(0.0, 1.0), (-1.5, -0.5), (1.5, -0.5)]
    boss = cq.Workplane("XY").workplane(offset=DOOR_T).polyline(tri_pts).close().extrude(BOSS_SIZE[2])
    door = door.union(boss)
    assert door.val() is not None and door.val().isValid(), "Step C5 failed validation"
    print("  C5 Lock boss... ok")

    return door


def build_demo_boards() -> dict[str, cq.Workplane]:
    print("Building PART D — demo boards...")
    arduino_board = cq.Workplane("XY").box(MCU_CASE[0], MCU_CASE[1], MCU_CASE[2], centered=(True, True, False))
    gsm_board = cq.Workplane("XY").box(GSM_BOARD[0], GSM_BOARD[1], GSM_BOARD[2], centered=(True, True, False))
    sensor_board = cq.Workplane("XY").box(30.0, 30.0, 5.0, centered=(True, True, False))
    return {
        "arduino_board": arduino_board,
        "gsm_board": gsm_board,
        "sensor_board": sensor_board
    }


# ==============================================================================
# SECTION 4 — ASSEMBLY + VALIDATION
# ==============================================================================

def main():
    # Build parts
    main_enclosure = build_main_enclosure()
    top_lid = build_top_lid()
    vent_door = build_vent_door()
    demo_boards = build_demo_boards()

    # ── Correct Z translation matching centered=(True, True, False) local origins ──
    # Since boxes are built with Z bottom at 0, we translate by exactly target Z bottom.

    # R1: arduino_board — floor at Z=T=2.5
    arduino_board_asm = demo_boards["arduino_board"].translate((MCU_ORIG[0], MCU_ORIG[1], T))

    # R5: gsm_board — floor at Z=T+GSM_PEG_H=6.5
    gsm_board_asm = demo_boards["gsm_board"].translate((GSM_ORIG[0], GSM_ORIG[1], T + GSM_PEG_H))

    # R5: sensor_board — floor at Z=T=2.5
    sensor_board_asm = demo_boards["sensor_board"].translate((DOCK_ORIG[0], DOCK_ORIG[1], T))

    # R3: top_lid — plate bottom sits flush on enclosure top face (Z=H=38.0)
    # The inset lip drops 2mm below Z=38.0 into the inner cavity.
    top_lid_asm = top_lid.translate((0, 0, H))

    # R2: vent_door — sits in rebate (rebate floor at Z = H - REBATE_DEPTH = 35.0)
    vent_door_asm = vent_door.translate((DOCK_ORIG[0], DOCK_ORIG[1], H - REBATE_DEPTH))

    # Build Assembly
    assembly = cq.Assembly(name="AirQuest_v3_Assembly")
    assembly.add(main_enclosure, name="main_enclosure", color=cq.Color(0.8, 0.8, 0.8))
    assembly.add(top_lid_asm, name="top_lid", color=cq.Color(0.7, 0.7, 0.7))
    assembly.add(vent_door_asm, name="vent_door", color=cq.Color(0.9, 0.9, 0.9))
    assembly.add(arduino_board_asm, name="arduino_board", color=cq.Color(0.12, 0.73, 0.50)) # #1EB980
    assembly.add(gsm_board_asm, name="gsm_board", color=cq.Color(0.0, 0.44, 0.70))        # #0071B2
    assembly.add(sensor_board_asm, name="sensor_board", color=cq.Color(0.91, 0.39, 0.0))    # #E86300

    # Print Validation Table
    print("\nPart name          | BBox (X×Y×Z mm)         | Volume mm³  | isValid")
    print("───────────────────┼─────────────────────────┼─────────────┼─────────")

    parts_positioned = {
        "main_enclosure": main_enclosure,
        "top_lid": top_lid,
        "vent_door": vent_door,
        "arduino_board": demo_boards["arduino_board"],
        "gsm_board": demo_boards["gsm_board"],
        "sensor_board": demo_boards["sensor_board"]
    }
    for name, part in parts_positioned.items():
        bbox = part.val().BoundingBox()
        dx = bbox.xlen
        dy = bbox.ylen
        dz = bbox.zlen
        vol = part.val().Volume()
        valid = part.val().isValid()
        print(f"{name:<18} | {dx:>5.1f}×{dy:>5.1f}×{dz:>4.1f}          | {vol:>11.1f} | {valid}")

    # FIX 7 — Bounding-box overlap validation
    def validate_no_overlap(parts: dict) -> bool:
        """Check each pair of assembled parts for 3D bounding-box overlap."""
        names = list(parts.keys())
        all_pass = True
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                a_name, b_name = names[i], names[j]
                a_bb = parts[a_name].val().BoundingBox()
                b_bb = parts[b_name].val().BoundingBox()
                ox = (a_bb.xmin < b_bb.xmax) and (b_bb.xmin < a_bb.xmax)
                oy = (a_bb.ymin < b_bb.ymax) and (b_bb.ymin < a_bb.ymax)
                oz = (a_bb.zmin < b_bb.zmax) and (b_bb.zmin < a_bb.zmax)
                if ox and oy and oz:
                    print(f"  FAIL ✗  {a_name} ↔ {b_name}")
                    print(f"         {a_name}: X[{a_bb.xmin:.1f},{a_bb.xmax:.1f}] Y[{a_bb.ymin:.1f},{a_bb.ymax:.1f}] Z[{a_bb.zmin:.1f},{a_bb.zmax:.1f}]")
                    print(f"         {b_name}: X[{b_bb.xmin:.1f},{b_bb.xmax:.1f}] Y[{b_bb.ymin:.1f},{b_bb.ymax:.1f}] Z[{b_bb.zmin:.1f},{b_bb.zmax:.1f}]")
                    all_pass = False
                else:
                    print(f"  PASS ✓  {a_name} ↔ {b_name}")
        return all_pass

    # Validate overlap using the corrected Z_bottom positions (no H/2 offset needed since centered=(True, True, False))
    asm_arduino  = demo_boards["arduino_board"].translate((MCU_ORIG[0],  MCU_ORIG[1],  T))
    asm_gsm      = demo_boards["gsm_board"].translate(    (GSM_ORIG[0],  GSM_ORIG[1],  T + GSM_PEG_H))
    asm_sensor   = demo_boards["sensor_board"].translate( (DOCK_ORIG[0], DOCK_ORIG[1], T))

    print("\nOverlap check (assembled board positions, centre-origin Z):")
    boards_asm = {
        "arduino_board": asm_arduino,
        "gsm_board":     asm_gsm,
        "sensor_board":  asm_sensor,
    }
    ok = validate_no_overlap(boards_asm)
    if not ok:
        raise ValueError("Board overlap detected — fix component positions before exporting!")

    # ==============================================================================
    # SECTION 5 — EXPORT
    # ==============================================================================
    out_dir = "/Users/bhavya_agarwal/Desktop/models"
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    print("\nExporting parts...")
    # Export individual parts
    cq.exporters.export(main_enclosure, os.path.join(out_dir, "main_enclosure.step"))
    cq.exporters.export(main_enclosure, os.path.join(out_dir, "main_enclosure.stl"), tolerance=0.05)
    
    cq.exporters.export(top_lid, os.path.join(out_dir, "top_lid.step"))
    cq.exporters.export(top_lid, os.path.join(out_dir, "top_lid.stl"), tolerance=0.05)
    
    cq.exporters.export(vent_door, os.path.join(out_dir, "vent_door.step"))
    cq.exporters.export(vent_door, os.path.join(out_dir, "vent_door.stl"), tolerance=0.05)

    cq.exporters.export(demo_boards["arduino_board"], os.path.join(out_dir, "arduino_board.step"))
    cq.exporters.export(demo_boards["gsm_board"], os.path.join(out_dir, "gsm_board.step"))
    cq.exporters.export(demo_boards["sensor_board"], os.path.join(out_dir, "sensor_board.step"))

    # Save Assembly
    assembly.save(os.path.join(out_dir, "airquest_v3_assembly.step"))
    print("Export complete.")

if __name__ == "__main__":
    main()
