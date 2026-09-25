"""KiCad python ile çalıştır. hava.kicad_pcb -> kural ayarı -> DSN -> Freerouting (java) -> SES -> GND dolgusu -> hava_routed.kicad_pcb"""
import os
import subprocess
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
JAR = os.path.join(HERE, "..", "..", "tools", "freerouting-2.1.0.jar")
SRC = os.path.join(HERE, "hava.kicad_pcb")
DSN = os.path.join(HERE, "hava.dsn")
SES = os.path.join(HERE, "hava.ses")
OUT = os.path.join(HERE, "hava_routed.kicad_pcb")
mm = pcbnew.FromMM

board = pcbnew.LoadBoard(SRC)

# JLCPCB 2 katman için yaklaşık kurallar (üretici sayfasından doğrulanmadı)
ds = board.GetDesignSettings()
ds.m_TrackMinWidth = mm(0.15)
ds.m_MinClearance = mm(0.15)
ds.m_ViasMinSize = mm(0.5)
ds.m_MinThroughDrill = mm(0.3)
ds.m_ViasMinAnnularWidth = mm(0.13)
ds.m_HoleClearance = mm(0.19)
nc = ds.m_NetSettings.GetDefaultNetclass()
nc.SetClearance(mm(0.2))
nc.SetTrackWidth(mm(0.25))
nc.SetViaDiameter(mm(0.6))
nc.SetViaDrill(mm(0.3))

# Modül termal via'ları: 0.3 mm altındaki delikler -> 0.3 mm
fixed = 0
for p in board.FindFootprintByReference("U1").Pads():
    if p.GetDrillSizeX() and p.GetDrillSizeX() < mm(0.3):
        p.SetDrillSize(pcbnew.VECTOR2I(mm(0.3), mm(0.3)))
        fixed += 1
print("termal via deligi buyutuldu:", fixed)

pcbnew.ExportSpecctraDSN(board, DSN)
subprocess.run(["java", "-jar", JAR, "-de", DSN, "-do", SES, "-mp", "40", "--gui.enabled=false"],
               check=True, cwd=HERE)
if not os.path.exists(SES):
    raise SystemExit("SES uretilmedi")
pcbnew.ImportSpecctraSES(board, SES)

# GND dolgusu (üst + alt)
gnd = board.FindNet("GND")
bbox = board.GetBoardEdgesBoundingBox()
for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    z.SetNet(gnd)
    z.SetLocalClearance(mm(0.25))
    z.SetMinThickness(mm(0.2))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    o = z.Outline()
    o.NewOutline()
    for x, y in ((bbox.GetLeft(), bbox.GetTop()), (bbox.GetRight(), bbox.GetTop()),
                 (bbox.GetRight(), bbox.GetBottom()), (bbox.GetLeft(), bbox.GetBottom())):
        o.Append(x, y)
    board.Add(z)
# (sensor kartinda anten yok)

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(OUT, board)
tracks = sum(1 for t in board.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T)
vias = sum(1 for t in board.GetTracks() if t.Type() == pcbnew.PCB_VIA_T)
print("yazildi:", OUT, "| iz:", tracks, "| via:", vias)
