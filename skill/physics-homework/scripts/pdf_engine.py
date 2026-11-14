from __future__ import annotations
from pathlib import Path
from urllib.parse import unquote
from io import BytesIO
from PIL import Image, ImageStat
from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
BANK_ROOT = Path('.')
BRAND_NAME = 'LauraPhysics'
BRAND_URL = 'https://github.com/Laura-LLU'
BRAND_FOOTER = 'LauraPhysics | Physics Board Homework'
CURRENT_COURSE = '9702'
PDF_FONT_NAME = 'PhysicsBankUnicode'
PDF_FONT_PATH = Path('/System/Library/Fonts/Supplemental/Arial Unicode.ttf')
if not PDF_FONT_PATH.is_file():
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    PDF_FONT_NAME = 'STSong-Light'
    pdfmetrics.registerFont(UnicodeCIDFont(PDF_FONT_NAME))
SESSION_CODES = {'Feb/Mar':'F/M','May/Jun':'M/J','Oct/Nov':'O/N'}


def as_int(value, default=0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

def effective_marks(item: dict) -> int:
    corrected = as_int(item.get("corrected_marks"))
    if corrected:
        return corrected
    marks = as_int(item.get("marks_detected"))
    if marks:
        return marks
    if item.get("kind") == "mcq":
        return 1
    return 0

def source_ref(item: dict) -> str:
    return item.get("source_ref", item.get("id", ""))


def safe_under(root: Path, relative: str) -> Path:
    candidate = (root / unquote(relative)).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError("文件路径超出允许范围。") from exc
    return candidate

def _best_cut(image: Image.Image, start: int, target: int) -> int:
    """Split only within continuous white bands; never choose a faint diagram row."""
    if target >= image.height:
        return image.height
    width = min(500, image.width)
    sample = image.convert("L").resize((width, max(1, round(image.height * width / image.width))))
    scale = image.height / sample.height
    minimum = int((start + max(80, (target-start)*0.20)) / scale)
    maximum = min(sample.height, int((target + (target-start)*0.04) / scale))
    px = sample.load()
    groups = []
    run = None
    for y in range(minimum, maximum):
        blank = all(px[x, y] >= 242 for x in range(2, width-2))
        if blank and run is None:
            run = y
        if not blank and run is not None:
            if y-run >= 4:
                groups.append((run,y))
            run = None
    if run is not None and maximum-run >= 4:
        groups.append((run,maximum))
    if not groups:
        # Preserve the whole remaining block and let page fitting scale it rather than cut a diagram.
        return image.height
    end = max(groups,key=lambda pair:pair[1])
    return min(image.height,max(start+1,int(((end[0]+end[1])/2)*scale)))


def _trim_outer_whitespace(image: Image.Image) -> Image.Image:
    """Trim the outer margin only; retain all separated text/diagram blocks."""
    gray = image.convert("L")
    ink = gray.point(lambda value: 255 if value < 246 else 0)
    box = ink.getbbox()
    if box is None:
        return image
    left, top, right, bottom = box
    return image.crop((max(0,left-8), max(0,top-8), min(image.width,right+8), min(image.height,bottom+8)))


def _crop_mcq_trailing_pages(image: Image.Image) -> Image.Image:
    """Remove page numbers, BLANK PAGE sheets, and copyright tails after Paper 1 Q40."""
    gray = image.convert("L")
    sample_width = min(500, gray.width)
    sample_height = max(1, int(gray.height * sample_width / gray.width))
    sample = gray.resize((sample_width, sample_height))
    threshold = max(3, int(sample_width * 0.006))
    active_rows = []
    for y in range(sample.height):
        row = sample.crop((0, y, sample.width, y + 1))
        if sum(pixel < 242 for pixel in row.getdata()) >= threshold:
            active_rows.append(y)
    groups: list[list[int]] = []
    join_gap = max(4, int(sample_width * 0.018))
    for y in active_rows:
        if not groups or y > groups[-1][-1] + join_gap:
            groups.append([y])
        else:
            groups[-1].append(y)
    accumulated_height = 0
    large_gap = max(180, int(sample_width * 0.42))
    for current, following in zip(groups, groups[1:]):
        accumulated_height += current[-1] - current[0] + 1
        if accumulated_height >= 12 and following[0] - current[-1] >= large_gap:
            scale = image.height / sample.height
            cutoff = min(image.height, int((current[-1] + 1) * scale) + 34)
            if cutoff < image.height * 0.82:
                return image.crop((0, 0, image.width, cutoff))
            break
    return image

def _compress_excess_vertical_whitespace(image: Image.Image) -> Image.Image:
    """Keep useful writing space while shortening oversized blank gaps in structured questions."""
    gray = image.convert("L")
    threshold = max(3, int(image.width * 0.006))
    active_rows = []
    for y in range(gray.height):
        row = gray.crop((0, y, gray.width, y + 1))
        if sum(pixel < 242 for pixel in row.getdata()) >= threshold:
            active_rows.append(y)
    if not active_rows:
        return image
    groups: list[list[int]] = []
    join_gap = max(5, int(image.width * 0.012))
    for y in active_rows:
        if not groups or y > groups[-1][-1] + join_gap:
            groups.append([y])
        else:
            groups[-1].append(y)
    max_gap = max(150, int(image.width * 0.22))
    kept_gap = max(96, int(image.width * 0.135))
    pieces: list[Image.Image] = []
    cursor = 0
    for current, following in zip(groups, groups[1:]):
        gap_start = current[-1] + 1
        gap_end = following[0]
        if gap_end - gap_start > max_gap:
            pieces.append(image.crop((0, cursor, image.width, gap_start)))
            pieces.append(Image.new("RGB", (image.width, kept_gap), "white"))
            cursor = gap_end
    pieces.append(image.crop((0, cursor, image.width, image.height)))
    if len(pieces) == 1:
        return image
    compacted = Image.new("RGB", (image.width, sum(piece.height for piece in pieces)), "white")
    y = 0
    for piece in pieces:
        compacted.paste(piece, (0, y))
        y += piece.height
    return compacted

def prepare_question_image(path: Path, item: dict) -> Image.Image:
    with Image.open(path) as opened:
        image = opened.convert("RGB")
    if item.get("kind") == "mcq" and as_int(item.get("question")) == 40:
        image = _crop_mcq_trailing_pages(image)
    elif item.get("kind") != "mcq":
        image = _compress_excess_vertical_whitespace(image)
    return _trim_outer_whitespace(image)

def _strip_trailing_table_header(image: Image.Image) -> Image.Image:
    """Drop an empty next-page mark-scheme table header left at the crop tail."""
    gray = image.convert("L")
    strong_rows = []
    for y in range(gray.height):
        row = list(gray.crop((0, y, gray.width, y + 1)).getdata())
        if sum(pixel < 130 for pixel in row) / gray.width > 0.60:
            strong_rows.append(y)
    if not strong_rows:
        return image
    groups: list[list[int]] = []
    for y in strong_rows:
        if not groups or y > groups[-1][-1] + 2:
            groups.append([y])
        else:
            groups[-1].append(y)
    last_line = groups[-1][0]
    tail_height = image.height - last_line
    if tail_height <= max(90, int(image.height * 0.14)):
        tail = gray.crop((0, min(image.height, last_line + 2), gray.width, image.height))
        if tail.height:
            preview_width = min(400, tail.width)
            preview_height = max(1, int(tail.height * preview_width / tail.width))
            preview = tail.resize((preview_width, preview_height))
            ink_ratio = sum(pixel < 225 for pixel in preview.getdata()) / (preview.width * preview.height)
            if ink_ratio > 0.012:
                return image.crop((0, 0, image.width, max(1, last_line - 6)))
    return image

def split_image(path: Path, width_points: float, max_height_points: float, item: dict, answer: bool) -> list[Image.Image]:
    if answer:
        with Image.open(path) as opened:
            image = _trim_outer_whitespace(_strip_trailing_table_header(opened.convert("RGB")))
    else:
        image = prepare_question_image(path, item)
    scaled_height = image.height * width_points / image.width
    if scaled_height <= max_height_points:
        return [image]
    max_pixels = max(300, int(max_height_points * image.width / width_points))
    slices: list[Image.Image] = []
    start = 0
    while start < image.height:
        target = min(image.height, start + max_pixels)
        end = _best_cut(image, start, target) if target < image.height else image.height
        if end <= start:
            end = target
        if image.height - end <= max_pixels * 0.13:
            end = image.height
        part = image.crop((0, start, image.width, end))
        preview_height = max(1, int(part.height * 300 / part.width))
        preview = part.convert("L").resize((300, preview_height))
        ink_ratio = sum(1 for pixel in preview.getdata() if pixel < 238) / (preview.width * preview.height)
        if ink_ratio >= 0.0018:
            slices.append(part)
        start = end
    return slices or [image]

class PdfComposer:
    def __init__(self, output: Path, title: str, metadata: dict, answer: bool):
        output.parent.mkdir(parents=True, exist_ok=True)
        self.page_width, self.page_height = A4
        self.margin = 38
        self.content_width = self.page_width - 2 * self.margin
        self.title = title
        self.metadata = metadata
        self.answer = answer
        self.pdf = canvas.Canvas(str(output), pagesize=A4)
        self.pdf.setTitle(title)
        self.pdf.setAuthor(BRAND_NAME)
        self.page_no = 0
        self.y = 0.0
        self.items_on_page = 0
        self.current_kind = ""
        try:
            pdfmetrics.getFont(PDF_FONT_NAME)
        except KeyError:
            if not PDF_FONT_PATH.is_file():
                raise RuntimeError(f"PDF 导出缺少所需字体：{PDF_FONT_PATH}")
            pdfmetrics.registerFont(TTFont(PDF_FONT_NAME, str(PDF_FONT_PATH)))

    def new_page(self) -> None:
        if self.page_no:
            self._footer()
            self.pdf.showPage()
        self.page_no += 1
        self.items_on_page = 0
        self.current_kind = ""
        self.pdf.setFillColor(HexColor("#102A43"))
        self.pdf.rect(0, self.page_height - 48, self.page_width, 48, fill=1, stroke=0)
        self.pdf.setFillColor(white)
        self.pdf.setFont(PDF_FONT_NAME, 13)
        label = "答案卷" if self.answer else "学生作业"
        self.pdf.drawString(self.margin, self.page_height - 30, f"{self.title}  -  {label}")
        self.y = self.page_height - 62
        if self.page_no == 1:
            self._metadata_block()

    def _metadata_block(self) -> None:
        self.pdf.setFillColor(HexColor("#243B53"))
        self.pdf.setFont(PDF_FONT_NAME, 9.5)
        class_name = self.metadata.get("className", "")
        student = self.metadata.get("studentName", "")
        due = self.metadata.get("dueDate", "")
        limit = self.metadata.get("timeLimit", "")
        total = self.metadata.get("totalMarks", 0)
        incomplete = self.metadata.get("marksIncomplete", 0)
        line1 = f"班级：{class_name or '________________'}    姓名：{student or '________________'}    日期：{due or '________________'}"
        total_text = f"已知总分：{total}" if total else "总分：以原题标注为准"
        if incomplete:
            total_text += f"（{incomplete}题未记录分值）"
        line2 = f"建议用时：{limit or '____'} 分钟    {total_text}"
        self.pdf.drawString(self.margin, self.y, line1)
        self.y -= 17
        self.pdf.drawString(self.margin, self.y, line2)
        self.y -= 17
        self.pdf.setStrokeColor(HexColor("#BCCCDC"))
        self.pdf.line(self.margin, self.y, self.page_width - self.margin, self.y)
        self.y -= 15

    def _footer(self) -> None:
        self.pdf.setStrokeColor(HexColor("#D9E2EC"))
        self.pdf.line(self.margin, 43, self.page_width - self.margin, 43)
        self.pdf.setFillColor(HexColor("#C9473A"))
        self.pdf.circle(self.margin + 6, 28, 6, fill=1, stroke=0)
        self.pdf.setFillColor(white)
        self.pdf.setFont("Helvetica-Bold", 7)
        self.pdf.drawCentredString(self.margin + 6, 25.5, "L")
        self.pdf.setFillColor(HexColor("#36546F"))
        self.pdf.setFont("Helvetica-Bold", 8)
        self.pdf.drawString(self.margin + 17, 25.5, BRAND_FOOTER)
        link_width = pdfmetrics.stringWidth(BRAND_FOOTER, "Helvetica-Bold", 8)
        self.pdf.linkURL(BRAND_URL, (self.margin, 21, self.margin + 19 + link_width, 36), relative=0, thickness=0)
        self.pdf.setFillColor(HexColor("#627D98"))
        self.pdf.setFont("Helvetica", 7.5)
        self.pdf.drawString(self.margin, 12, "Physics homework | " + CURRENT_COURSE + "")
        self.pdf.drawRightString(self.page_width - self.margin, 12, f"Page {self.page_no}")

    def _ensure_space(self, required: float, kind: str) -> None:
        page_bottom = 52
        if not self.page_no:
            self.new_page()
            return
        if kind == "mcq" and self.current_kind == "mcq" and self.items_on_page >= 3:
            self.new_page()
        elif kind == "structured" and self.items_on_page:
            self.new_page()
        elif self.y - required < page_bottom and self.items_on_page:
            self.new_page()

    def add_item(self, number: int, item: dict, image_path: Path) -> None:
        kind = "mcq" if item.get("kind") == "mcq" else "structured"
        if kind == "mcq" and self.answer:
            draw_max_width = min(260, self.content_width)
        elif kind == "structured":
            draw_max_width = self.content_width - 40
        else:
            draw_max_width = self.content_width
        page_bottom = 52
        max_height = self.page_height - 48 - page_bottom - 42
        if self.page_no == 0:
            self.new_page()
        available_first = self.y - page_bottom - 30
        slice_height = max(210, min(max_height, available_first if not self.items_on_page else max_height))
        images = split_image(image_path, draw_max_width, slice_height, item, self.answer)

        for part_no, image in enumerate(images, 1):
            scaled_height = image.height * draw_max_width / image.width
            required = 27 + scaled_height + 12
            part_kind = kind if part_no == 1 else "structured"
            self._ensure_space(required, part_kind)
            continuation = "（续）" if part_no > 1 else ""
            label = "答案" if self.answer else "题目"
            marks = effective_marks(item)
            marks_text = f" · {marks} marks" if marks else ""
            self.pdf.setFillColor(HexColor("#EAF2F8"))
            self.pdf.roundRect(self.margin, self.y - 20, self.content_width, 22, 5, fill=1, stroke=0)
            self.pdf.setFillColor(HexColor("#102A43"))
            self.pdf.setFont(PDF_FONT_NAME, 9.5)
            self.pdf.drawString(self.margin + 8, self.y - 14, f"{label} {number}{continuation}{marks_text}")
            if self.answer or self.metadata.get("showSource"):
                self.pdf.setFont("Helvetica", 8)
                self.pdf.drawRightString(self.page_width - self.margin - 8, self.y - 14, source_ref(item))
            self.y -= 28

            buffer = BytesIO()
            image.save(buffer, format="PNG", optimize=True)
            buffer.seek(0)
            draw_height = image.height * draw_max_width / image.width
            if self.y - draw_height < page_bottom:
                draw_height = self.y - page_bottom
            draw_width = image.width * draw_height / image.height
            x = self.margin + (self.content_width - draw_width) / 2
            self.pdf.drawImage(ImageReader(buffer), x, self.y - draw_height, draw_width, draw_height, preserveAspectRatio=True, mask="auto")
            self.y -= draw_height + 12
            self.items_on_page += 1
            self.current_kind = part_kind

    def save(self) -> None:
        if not self.page_no:
            self.new_page()
        self._footer()
        self.pdf.save()

def build_pdf(items: list[dict], output: Path, title: str, metadata: dict, answer: bool) -> None:
    composer = PdfComposer(output, title, metadata, answer)
    for number, item in enumerate(items, 1):
        relative = item["answer_image"] if answer else item["question_image"]
        composer.add_item(number, item, safe_under(BANK_ROOT, relative))
    composer.save()
