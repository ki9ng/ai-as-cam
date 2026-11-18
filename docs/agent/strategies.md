# Machining strategies (agent reference)

Read this when planning a job. Pick strategies to fit the user's machine, tools and material
from their config and post-mortems. This is a menu, not a rule set: no strategy here is
always right, and nothing here overrides the user's measured values.

**Be transparent.** In the plan, name each strategy you chose and give a one-line reason
("cutout as trochoidal loops: full-width slotting in aluminium on a light machine"). If you
rejected an obvious alternative, say why. The user can say no.

## Roughing / clearing
- **Offset (contour-parallel) pocketing:** rings stepping in or out from the wall. Even
  engagement except at corners; fewer direction changes. Corners spike load.
- **Raster (zig-zag) pocketing:** back-and-forth lanes. Simple, good for flat floors and
  terraces; mixes climb and conventional; lots of reversals. Clip lanes to stock or it cuts air.
- **Adaptive / trochoidal:** small loops or a constant-engagement path so the tool never goes
  full-width. Best for slots and hard materials on light or flexible machines; longer paths
  and more air time. Lets you use deeper DOC with light stepover.
- **Step-down (Z levels):** roughing in layers. DOC per level from tool config.
- **Rest machining:** a smaller tool only removes what a bigger one couldn't reach. Saves time
  with small tools; needs a stock model of what's left.

## Entry
- **Helical entry:** spiral down into a pocket or hole. Default where there's room.
- **Ramp entry:** descend along a line. For narrow slots where a helix won't fit.
- **Straight plunge:** only with a center-cutting tool, into air or pre-drilled holes, or when
  the user says so. The plunge gate flags it otherwise.
- **Pre-drill / peck:** drill a start hole first, or peck drilling for deep holes to clear chips.

## Direction
- **Climb milling:** better finish and less rubbing on rigid machines; can pull the tool into
  the work on machines with backlash.
- **Conventional milling:** safer on machines with backlash or flex; rougher finish.
- On machines with known slop, avoid pushing cutting force toward the loose side (check the
  user's post-mortems/config).

## Finishing
- **Rough then finish:** leave a small skin, then a light full-depth pass on walls/floors.
- **Spring pass:** repeat the finish pass at the same offset to remove deflection.
- **Ball-end / scallop finishing:** for 3D surfaces; stepover sets scallop height.
- **V-carving:** depth follows width. Feed often needs to drop as depth (engagement) rises.

## Through-cuts and workholding
- **Tabs:** small bridges hold the part to the end; need cleanup.
- **Onion skin:** leave a thin floor, break through last or remove by hand.
- **Glue / tape down, cut through:** no tabs; cut slightly into the backing.
- **Cutout last:** do every feature before the part is freed.

## Tool use
- **Batch ops by tool**, and run the riskiest or least-proven tool where a break costs least.
- **Test coupon / plug:** first use of a tool or material, cut a small sample with the same
  settings before the real part.

## When unsure
Ask the user, or propose a test coupon. Don't guess feeds, depths or stepovers; take them
from config or measure them.
