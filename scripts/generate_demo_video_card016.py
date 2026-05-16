from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from textwrap import wrap

try:
    from PIL import Image, ImageDraw, ImageFont
except ModuleNotFoundError:
    Image = ImageDraw = ImageFont = None


ROOT = Path("/root/projetos/quarry")
VIDEO_DIR = ROOT / "docs" / "pitch" / "videos"
WORK_DIR = Path("/tmp/quarry-card016-video")
LOCAL_TTS_DIR = Path("/tmp/quarry-card016-tts")
SCREENSHOT = ROOT / "artifacts" / "public-deploy" / "quarry-public-demo-current.png"

BG = "#0B0F14"
PANEL = "#151A21"
PANEL2 = "#1E252E"
RED = "#8B0000"
RED2 = "#B32635"
WHITE = "#F7F4EF"
MUTED = "#A8B0BA"
LINE = "#343B45"
GOLD = "#D9A441"
GREEN = "#12C48B"
ORANGE = "#D98B2B"


@dataclass(frozen=True)
class Segment:
    slug: str
    start: int
    end: int
    title: str
    narration_en: str
    narration_pt: str

    @property
    def duration(self) -> int:
        return self.end - self.start


SEGMENTS = [
    Segment(
        "context",
        0,
        30,
        "Context: The Post-Mythos Clock",
        "On April seventh, twenty twenty six, Anthropic disclosed Claude Mythos Preview and Project Glasswing. The important signal is not one model name. It is that autonomous cyber capability is now credible enough to compress vulnerability discovery, exploitation, and defensive response cycles. Quarry is built for this new clock: machine-speed investigation with human governance.",
        "Em sete de abril de dois mil e vinte e seis, a Anthropic apresentou Claude Mythos Preview e Project Glasswing. O ponto importante não é o nome de um modelo. É o sinal de que capacidades cibernéticas autônomas já conseguem comprimir descoberta, exploração e resposta defensiva. O Quarry foi construído para esse novo ritmo: investigação em velocidade de máquina com governança humana.",
    ),
    Segment(
        "brief",
        30,
        60,
        "Brief: Organized Pix Fraud",
        "The analyst starts with a natural-language brief. In this demo, the case is organized Pix fraud at a fictitious Brazilian fintech called FinPlay Pagamentos. The brief describes five hundred suspicious transactions in thirty days, with newly created accounts receiving fragmented values and redistributing them to potential mule accounts.",
        "O analista começa com um briefing em linguagem natural. Nesta demonstração, o caso é uma fraude Pix organizada em uma fintech brasileira fictícia chamada FinPlay Pagamentos. O briefing descreve quinhentas transações suspeitas em trinta dias, com contas recém-criadas recebendo valores fracionados e redistribuindo para possíveis contas-laranja.",
    ),
    Segment(
        "hypotheses",
        60,
        120,
        "Hypotheses: From Brief to Investigation Plan",
        "Quarry decomposes the brief into testable hypotheses. It does not jump directly to an answer. It proposes a mule-account ring, a possible SIM-swap origin for a high-value account, anomalous Open Finance access, and a boleto fraud campaign. Each hypothesis has a confidence score, expected evidence, and the data sources that should be queried.",
        "O Quarry decompõe o briefing em hipóteses testáveis. Ele não pula direto para uma resposta. Ele propõe um anel de contas-laranja, uma possível origem de SIM swap para uma conta de alto valor, acesso anômalo via Open Finance e uma campanha de boletos fraudulentos. Cada hipótese tem score de confiança, evidência esperada e fontes de dados a consultar.",
    ),
    Segment(
        "queries",
        120,
        180,
        "Queries: Controlled Evidence Collection",
        "The agent now runs controlled queries. The important product decision is governance. Query execution is visible. Cost and token usage are visible. Read-only evaluation paths are enforced for benchmark work. The Investigation Ledger records the questions, the evidence, and the reasoning path so the analyst can challenge or reproduce the result.",
        "O agente agora executa consultas controladas. A decisão importante do produto é governança. A execução das consultas fica visível. Custo e uso de tokens ficam visíveis. Caminhos somente leitura são aplicados em avaliação. O Investigation Ledger registra perguntas, evidências e raciocínio para que o analista possa contestar ou reproduzir o resultado.",
    ),
    Segment(
        "findings",
        180,
        240,
        "Findings: Correlation and Analyst Context",
        "The system correlates events into findings. Here, the suspicious flow crosses twenty newly created accounts, ninety-six thousand Pix events, and more than two hundred fifty thousand reais in correlated value. Instead of a black-box answer, the analyst receives prioritized findings, related entities, and a graph that explains why the case deserves attention.",
        "O sistema correlaciona eventos em achados. Aqui, o fluxo suspeito atravessa vinte contas recém-criadas, noventa e seis mil eventos Pix e mais de duzentos e cinquenta mil reais em valor correlacionado. Em vez de uma resposta caixa-preta, o analista recebe achados priorizados, entidades relacionadas e um grafo que explica por que o caso merece atenção.",
    ),
    Segment(
        "report",
        240,
        270,
        "Report: Evidence-Backed Output",
        "Quarry then generates an analyst-ready report. The report is not just prose. It is backed by the ledger: hypotheses, queries, findings, timeline, MITRE context where relevant, and a defensible conclusion. This is the output a security leader can review, improve, and send forward.",
        "Depois, o Quarry gera um relatório pronto para o analista. O relatório não é apenas texto. Ele é sustentado pelo ledger: hipóteses, consultas, achados, linha do tempo, contexto MITRE quando aplicável e uma conclusão defensável. É o tipo de saída que uma liderança de segurança consegue revisar, melhorar e encaminhar.",
    ),
    Segment(
        "cost",
        270,
        300,
        "Reveal: Cost vs Human Analyst",
        "The final reveal is cost and time. In the demo, Quarry shows machine cost next to an estimated human analyst cost and hours saved. The claim is not that humans disappear. The claim is that senior investigation capacity becomes measurable, repeatable, and dramatically faster under human control.",
        "A revelação final é custo e tempo. Na demonstração, o Quarry mostra o custo da máquina ao lado de uma estimativa de custo de analista humano e horas economizadas. A tese não é que humanos desaparecem. A tese é que a capacidade de investigação sênior se torna mensurável, repetível e muito mais rápida sob controle humano.",
    ),
]


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    if ImageFont is None:
        return None
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/Library/Fonts/Arial Unicode.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


F_TITLE = font(68, True)
F_SUB = font(32)
F_BODY = font(28)
F_SMALL = font(22)
F_TINY = font(18)
F_MONO = font(24)


def rounded(draw: ImageDraw.ImageDraw, xy, fill, outline=LINE, radius=22, width=2):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def text(draw: ImageDraw.ImageDraw, xy, value: str, fill=WHITE, font_obj=F_BODY, anchor=None):
    draw.text(xy, value, fill=fill, font=font_obj, anchor=anchor)


def multiline(draw: ImageDraw.ImageDraw, xy, value: str, width_chars: int, fill=WHITE, font_obj=F_BODY, leading=42):
    x, y = xy
    for line in wrap(value, width_chars):
        draw.text((x, y), line, fill=fill, font=font_obj)
        y += leading
    return y


def logo(draw: ImageDraw.ImageDraw):
    rounded(draw, (70, 62, 130, 122), fill=RED, outline=RED, radius=16, width=0)
    text(draw, (100, 92), "Q", fill=WHITE, font_obj=font(28, True), anchor="mm")
    text(draw, (152, 78), "QUARRY", fill=WHITE, font_obj=font(24, True))
    text(draw, (152, 108), "Autonomous Threat Hunting", fill=MUTED, font_obj=F_TINY)


def frame_base(title: str, section: str, progress: float) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (1920, 1080), BG)
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, 1920, 12), fill=RED)
    logo(draw)
    text(draw, (70, 174), section.upper(), fill=GOLD, font_obj=F_TINY)
    text(draw, (70, 215), title, fill=WHITE, font_obj=F_TITLE)
    draw.rounded_rectangle((70, 1000, 1850, 1012), radius=6, fill=PANEL2)
    draw.rounded_rectangle((70, 1000, 70 + int(1780 * progress), 1012), radius=6, fill=RED2)
    text(draw, (70, 1030), "Confidential demo package | no customer data | no third-party logos", fill=MUTED, font_obj=F_TINY)
    return img, draw


def add_screenshot(draw: ImageDraw.ImageDraw, x: int, y: int, w: int):
    if not SCREENSHOT.exists():
        return
    shot = Image.open(SCREENSHOT).convert("RGB")
    ratio = shot.height / shot.width
    h = int(w * ratio)
    shot = shot.resize((w, h))
    rounded(draw, (x - 8, y - 8, x + w + 8, y + h + 8), fill=PANEL2, outline=LINE, radius=18)
    # Paste through image object by accessing underlying base.


def paste_screenshot(img: Image.Image, draw: ImageDraw.ImageDraw, x: int, y: int, w: int):
    if not SCREENSHOT.exists():
        return
    shot = Image.open(SCREENSHOT).convert("RGB")
    ratio = shot.height / shot.width
    h = int(w * ratio)
    shot = shot.resize((w, h), Image.Resampling.LANCZOS)
    rounded(draw, (x - 8, y - 8, x + w + 8, y + h + 8), fill=PANEL2, outline=LINE, radius=18)
    img.paste(shot, (x, y))


def draw_card(draw, xy, title, body, accent=RED2, score=None):
    x1, y1, x2, y2 = xy
    rounded(draw, xy, fill=PANEL, outline=LINE, radius=18)
    draw.rectangle((x1, y1, x1 + 6, y2), fill=accent)
    text(draw, (x1 + 26, y1 + 24), title, fill=WHITE, font_obj=font(28, True))
    multiline(draw, (x1 + 26, y1 + 72), body, 31, fill=MUTED, font_obj=F_SMALL, leading=31)
    if score:
        rounded(draw, (x2 - 120, y1 + 22, x2 - 28, y1 + 58), fill="#103D32", outline="#103D32", radius=10, width=0)
        text(draw, (x2 - 74, y1 + 32), score, fill=GREEN, font_obj=font(18, True), anchor="ma")


def make_context(path: Path):
    img, draw = frame_base("Autonomous cyber changed the clock.", "0-30s | Mythos context", 0.10)
    multiline(draw, (76, 340), "The post-Mythos era is not about one model. It is about a shorter clock for discovery, exploitation, and response.", 55, fill=WHITE, font_obj=F_SUB, leading=48)
    for i, item in enumerate([
        ("April 7, 2026", "Claude Mythos Preview and Project Glasswing disclosed."),
        ("Regulated finance", "Treasury and Fed attention moves AI cyber risk into board-level discussion."),
        ("Quarry thesis", "Machine-speed investigation, governed by auditability and human control."),
    ]):
        x = 100 + i * 570
        draw_card(draw, (x, 580, x + 500, 830), item[0], item[1], accent=[RED2, GOLD, GREEN][i])
    img.save(path)


def make_brief(path: Path, phase: int):
    img, draw = frame_base("The analyst starts with a brief.", "30-60s | Brief being typed", 0.20)
    rounded(draw, (120, 330, 1800, 850), fill=PANEL, outline=LINE, radius=24)
    text(draw, (160, 380), "Investigation brief", fill=GOLD, font_obj=font(26, True))
    full = "Investigate possible organized Pix fraud at FinPlay Pagamentos: 500 suspicious transactions in 30 days, newly created accounts receiving fragmented values and redistributing funds to potential mule accounts."
    visible = full[: int(len(full) * phase / 6)]
    y = multiline(draw, (160, 450), visible + ("|" if phase < 6 else ""), 78, fill=WHITE, font_obj=font(34), leading=54)
    rounded(draw, (160, 725, 480, 790), fill=RED, outline=RED, radius=18, width=0)
    text(draw, (320, 750), "Start Hunt", fill=WHITE, font_obj=font(28, True), anchor="ma")
    img.save(path)


def make_hypotheses(path: Path, phase: int):
    img, draw = frame_base("Quarry decomposes the brief into hypotheses.", "1-2min | Hypotheses", 0.40)
    items = [
        ("Money mule ring", "20 newly created accounts receive values near the distribution mean and redistribute within minutes.", "92%"),
        ("SIM swap origin", "A high-value account changes device, biometrics, and operator before the Pix sequence.", "88%"),
        ("Open Finance scraping", "Consent access pattern shows abnormal frequency and account breadth.", "81%"),
    ]
    for i, item in enumerate(items[:phase]):
        draw_card(draw, (120 + i * 575, 370, 620 + i * 575, 760), item[0], item[1], accent=[GREEN, ORANGE, RED2][i], score=item[2])
    text(draw, (120, 825), "The agent creates a plan before it asks the data to prove or disprove it.", fill=MUTED, font_obj=F_BODY)
    img.save(path)


def make_queries(path: Path, phase: int):
    img, draw = frame_base("Controlled queries collect evidence.", "2-3min | Queries", 0.60)
    paste_screenshot(img, draw, 95, 315, 730)
    query_lines = [
        "SELECT account_id, SUM(amount), COUNT(*) FROM pix_events",
        "WHERE account_age_days < 14 AND event_time BETWEEN t0 AND t1",
        "GROUP BY account_id HAVING COUNT(*) > threshold;",
        "JOIN device_changes, biometric_events, open_finance_access;",
    ]
    rounded(draw, (900, 320, 1780, 785), fill="#070A12", outline=LINE, radius=20)
    text(draw, (930, 360), "Evidence query plan", fill=GOLD, font_obj=font(28, True))
    for i, line in enumerate(query_lines[:phase]):
        text(draw, (930, 430 + i * 66), line, fill=GREEN if i == phase - 1 else WHITE, font_obj=F_MONO)
    pct = [25, 51, 76, 100][phase - 1]
    rounded(draw, (930, 710, 1700, 735), fill=PANEL2, outline=PANEL2, radius=10)
    rounded(draw, (930, 710, 930 + int(770 * pct / 100), 735), fill=GREEN, outline=GREEN, radius=10, width=0)
    text(draw, (1715, 705), f"{pct}%", fill=WHITE, font_obj=font(24, True))
    img.save(path)


def make_findings(path: Path, phase: int):
    img, draw = frame_base("Findings become analyst context.", "3-4min | Findings and correlation", 0.80)
    findings = [
        ("Critical", "R$ 257,600 correlated cash-out flow across 20 newly created accounts."),
        ("High", "SIM swap behavior precedes the high-value Pix origin account."),
        ("Medium", "Open Finance access pattern matches anomalous scraping behavior."),
    ]
    for i, item in enumerate(findings[:phase]):
        draw_card(draw, (105, 320 + i * 185, 760, 475 + i * 185), item[0], item[1], accent=[RED2, ORANGE, GOLD][i])
    # Graph panel
    rounded(draw, (880, 320, 1780, 850), fill=PANEL, outline=LINE, radius=22)
    text(draw, (920, 360), "Correlation graph", fill=GOLD, font_obj=font(28, True))
    center = (1330, 595)
    nodes = [(1100, 460), (1530, 465), (1120, 725), (1530, 735), (1330, 595)]
    for x, y in nodes[: phase + 2]:
        draw.line((center[0], center[1], x, y), fill=LINE, width=4)
    for idx, (x, y) in enumerate(nodes[: phase + 2]):
        color = RED2 if idx == len(nodes[: phase + 2]) - 1 else PANEL2
        rounded(draw, (x - 62, y - 42, x + 62, y + 42), fill=color, outline=GREEN if color != RED2 else RED2, radius=22)
        text(draw, (x, y - 10), f"N{idx+1}", fill=WHITE, font_obj=font(24, True), anchor="ma")
    img.save(path)


def make_report(path: Path, phase: int):
    img, draw = frame_base("The report is generated from evidence.", "4-4:30min | Report", 0.90)
    rounded(draw, (150, 280, 1770, 850), fill="#F7F4EF", outline="#F7F4EF", radius=18)
    text(draw, (210, 340), "Investigation Report", fill="#0B0F14", font_obj=font(46, True))
    lines = [
        "Executive summary: organized Pix fraud pattern identified.",
        "Evidence: 20 newly created accounts; R$ 257,600 correlated value.",
        "Timeline: device change -> Pix burst -> mule distribution.",
        "Recommendation: freeze suspect accounts and escalate manual review.",
    ]
    for i, line in enumerate(lines[: 2 + phase * 2]):
        text(draw, (215, 430 + i * 62), line, fill="#151A21", font_obj=font(30))
    text(draw, (215, 780), "Backed by Investigation Ledger entries, not a black-box answer.", fill=RED, font_obj=font(26, True))
    img.save(path)


def make_cost(path: Path, phase: int):
    img, draw = frame_base("Cost and time become visible.", "4:30-5min | Cost vs human analyst", 1.0)
    values = [
        ("AI run cost", "$7.55", "tokens + orchestration"),
        ("Human analyst estimate", "$2,250", "5.4 hours modeled"),
        ("Time saved", "hours", "repeatable investigation flow"),
    ]
    for i, (label, val, sub) in enumerate(values[: 2 + phase]):
        x = 170 + i * 555
        rounded(draw, (x, 360, x + 455, 690), fill=PANEL, outline=LINE, radius=28)
        text(draw, (x + 42, 430), label.upper(), fill=GOLD, font_obj=font(22, True))
        text(draw, (x + 42, 535), val, fill=WHITE, font_obj=font(72, True))
        text(draw, (x + 42, 635), sub, fill=MUTED, font_obj=F_SMALL)
    text(draw, (170, 780), "Claim: humans stay in control; senior investigation capacity becomes faster, measurable, and repeatable.", fill=WHITE, font_obj=F_BODY)
    img.save(path)


def timestamp(seconds: float) -> str:
    ms = int(round((seconds - int(seconds)) * 1000))
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"


def sentence_chunks(text_value: str) -> list[str]:
    raw = [x.strip() for x in text_value.replace(". ", ".|").replace("? ", "?|").split("|") if x.strip()]
    chunks = []
    current = ""
    for sentence in raw:
        if len(current) + len(sentence) < 82:
            current = (current + " " + sentence).strip()
        else:
            if current:
                chunks.append(current)
            current = sentence
    if current:
        chunks.append(current)
    return chunks


def write_srt(path: Path, language: str):
    entries = []
    idx = 1
    for seg in SEGMENTS:
        content = seg.narration_pt if language == "pt-br" else seg.narration_en
        chunks = sentence_chunks(content)
        step = seg.duration / len(chunks)
        for i, chunk in enumerate(chunks):
            start = seg.start + i * step
            end = min(seg.end, seg.start + (i + 1) * step)
            entries.append(f"{idx}\n{timestamp(start)} --> {timestamp(end)}\n{chunk}\n")
            idx += 1
    path.write_text("\n".join(entries))


def write_script_docs():
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    script = ["# Quarry 5-Minute Demo Video - English Narration Script\n"]
    for seg in SEGMENTS:
        script.append(f"## {seg.start//60}:{seg.start%60:02d}-{seg.end//60}:{seg.end%60:02d} - {seg.title}\n")
        script.append(seg.narration_en + "\n")
    (VIDEO_DIR / "quarry-demo-5min-script-en.md").write_text("\n".join(script))

    script_pt = ["# Quarry 5-Minute Demo Video - PT-BR Caption Translation\n"]
    for seg in SEGMENTS:
        script_pt.append(f"## {seg.start//60}:{seg.start%60:02d}-{seg.end//60}:{seg.end%60:02d} - {seg.title}\n")
        script_pt.append(seg.narration_pt + "\n")
    (VIDEO_DIR / "quarry-demo-5min-script-pt-br.md").write_text("\n".join(script_pt))

    write_srt(VIDEO_DIR / "quarry-demo-5min.en.srt", "en")
    write_srt(VIDEO_DIR / "quarry-demo-5min.pt-br.srt", "pt-br")

    readme = """# Quarry Demo Video Package

Generated for CARD-016.

## Final video files

- `quarry-demo-5min.mp4` - full 5-minute narrated version with English captions burned in.
- `quarry-demo-2min-teaser.mp4` - 2-minute teaser cut from the full version.
- `quarry-demo-30s-social.mp4` - 30-second social cut from the full version.

## Caption files

- `quarry-demo-5min.en.srt`
- `quarry-demo-5min.pt-br.srt`

The full video has English captions burned in. The PT-BR SRT is provided as the Portuguese caption version.

## Audio and music

Narration uses a generated English voiceover for the async demo package. Replace with human studio narration before a high-stakes external launch if desired.

The background music bed is generated in-house with ffmpeg sine synthesis inside `scripts/generate_demo_video_card016.py`. It uses no third-party samples, so there is no external music license dependency.

## Vimeo hosting

Vimeo upload is not completed because the environment does not have Vimeo credentials or a configured upload token. Recommended upload mode: Vimeo unlisted/private link, downloads disabled, no public search indexing.

## Privacy controls

- No real customer data.
- No third-party company logos.
- Demo credentials are not embedded in the video or captions.
"""
    (VIDEO_DIR / "README.md").write_text(readme)


def write_frame(path: Path, maker, *args):
    maker(path, *args)


def build_frames() -> list[tuple[Path, int]]:
    frames_dir = WORK_DIR / "frames"
    if frames_dir.exists():
        shutil.rmtree(frames_dir)
    frames_dir.mkdir(parents=True, exist_ok=True)
    frame_plan: list[tuple[Path, int]] = []
    idx = 0

    def add(duration, maker, *args):
        nonlocal idx
        path = frames_dir / f"frame_{idx:03d}.png"
        maker(path, *args)
        frame_plan.append((path, duration))
        idx += 1

    add(30, make_context)
    for phase in range(1, 7):
        add(5, make_brief, phase)
    for phase in range(1, 4):
        add(20, make_hypotheses, phase)
    for phase in range(1, 5):
        add(15, make_queries, phase)
    for phase in range(1, 4):
        add(20, make_findings, phase)
    for phase in range(1, 3):
        add(15, make_report, phase)
    for phase in range(0, 2):
        add(15, make_cost, phase)
    return frame_plan


def run(cmd: list[str], cwd: Path | None = None):
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=cwd, check=True)


def prepare_tts_texts(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    for i, seg in enumerate(SEGMENTS):
        (out_dir / f"seg_{i:02d}.txt").write_text(seg.narration_en)


def build_audio(tts_dir: Path):
    audio_dir = WORK_DIR / "audio"
    if audio_dir.exists():
        shutil.rmtree(audio_dir)
    audio_dir.mkdir(parents=True, exist_ok=True)
    normalized = []
    for i, seg in enumerate(SEGMENTS):
        src = tts_dir / f"seg_{i:02d}.aiff"
        if not src.exists():
            raise FileNotFoundError(f"missing narration audio: {src}")
        dst = audio_dir / f"seg_{i:02d}.wav"
        run([
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", str(src),
            "-af", f"volume=1.35,apad,atrim=0:{seg.duration}",
            "-ar", "44100",
            "-ac", "2",
            str(dst),
        ])
        normalized.append(dst)

    concat = audio_dir / "voice.ffconcat"
    with concat.open("w") as f:
        f.write("ffconcat version 1.0\n")
        for path in normalized:
            f.write(f"file {path}\n")
    voice = audio_dir / "voice.wav"
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(concat), "-c", "copy", str(voice)])

    mixed = audio_dir / "final-audio.m4a"
    pad_expr = "aevalsrc=0.06*(sin(2*PI*55*t)+0.45*sin(2*PI*82.41*t)+0.35*sin(2*PI*110*t))*(0.65+0.35*sin(2*PI*0.045*t)):s=44100:d=300"
    run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(voice),
        "-f", "lavfi", "-i", pad_expr,
        "-filter_complex", "[1:a]afade=t=in:st=0:d=3,afade=t=out:st=296:d=4,volume=0.12[m];[0:a][m]amix=inputs=2:duration=first:dropout_transition=2,loudnorm=I=-16:TP=-1.5:LRA=11[a]",
        "-map", "[a]",
        "-c:a", "aac",
        "-b:a", "160k",
        str(mixed),
    ])
    return mixed


def build_video(tts_dir: Path):
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    write_script_docs()
    frame_plan = build_frames()
    concat = WORK_DIR / "frames.ffconcat"
    with concat.open("w") as f:
        f.write("ffconcat version 1.0\n")
        for path, duration in frame_plan:
            f.write(f"file {path}\n")
            f.write(f"duration {duration}\n")
        f.write(f"file {frame_plan[-1][0]}\n")
    audio = build_audio(tts_dir)
    full = VIDEO_DIR / "quarry-demo-5min.mp4"
    run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", str(concat),
        "-i", str(audio),
        "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=30,subtitles=quarry-demo-5min.en.srt:force_style='FontName=DejaVu Sans,FontSize=11,PrimaryColour=&H00F7F4EF,OutlineColour=&H000B0F14,BorderStyle=3,Outline=1,Shadow=0,BackColour=&HAA0B0F14,MarginV=36'",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k",
        "-shortest",
        str(full),
    ], cwd=VIDEO_DIR)

    teaser = VIDEO_DIR / "quarry-demo-2min-teaser.mp4"
    social = VIDEO_DIR / "quarry-demo-30s-social.mp4"
    for out, seconds in [(teaser, "120"), (social, "30")]:
        run([
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", str(full),
            "-t", seconds,
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
            "-c:a", "aac", "-b:a", "160k",
            str(out),
        ])

    # Keep copies alongside older demo artifacts for operational discovery.
    artifacts_dir = ROOT / "artifacts" / "demo-videos"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    for path in [full, teaser, social]:
        shutil.copy2(path, artifacts_dir / path.name)

    manifest = {
        "outputs": [str(full), str(teaser), str(social)],
        "captions": [str(VIDEO_DIR / "quarry-demo-5min.en.srt"), str(VIDEO_DIR / "quarry-demo-5min.pt-br.srt")],
        "script": str(VIDEO_DIR / "quarry-demo-5min-script-en.md"),
        "duration_seconds": 300,
        "music": "Original ffmpeg sine-synthesis ambient bed; no third-party samples.",
        "vimeo": "pending_credentials",
    }
    (VIDEO_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare-tts", action="store_true")
    parser.add_argument("--tts-dir", type=Path, default=LOCAL_TTS_DIR)
    parser.add_argument("--build", action="store_true")
    args = parser.parse_args()
    if args.prepare_tts:
        prepare_tts_texts(args.tts_dir)
    if args.build:
        build_video(args.tts_dir)


if __name__ == "__main__":
    main()
