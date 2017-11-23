from copy import copy

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph

"""
SDX Cora PDF Transformer styles.
"""


class CoraPdfTransformerStyle:

    def __init__(self):
        styles = getSampleStyleSheet()

        # Basic text style
        self.style_n = copy(styles["BodyText"])
        self.style_n.alignment = TA_LEFT

        # Answer Style
        self.style_answer = ParagraphStyle(name='BodyText', parent=styles['Normal'], spaceBefore=6)
        self.style_answer.alignment = TA_LEFT
        self.style_answer.fontName = "Helvetica-Bold"
        self.style_answer.textColor = colors.red
        self.style_answer.fontSize = 15
        self.style_answer.leading = 20
        self.style_answer.spaceAfter = 20

        # Subheading style
        self.style_sh = styles["Heading2"]
        self.style_sh.alignment = TA_LEFT

        # Sub-subheading style (questions)
        self.style_ssh = styles["Heading3"]
        self.style_ssh.alignment = TA_LEFT

        # Main heading style
        self.style_h = styles['Heading1']
        self.style_h.alignment = TA_CENTER

    def get_heading_data(self, title, collection_instrument_id, ru_ref, submitted_at):
        heading_data = [[Paragraph(title, self.style_h)]]
        heading_data.append(['Form Type', collection_instrument_id])
        heading_data.append(['Respondent', ru_ref[:11]])
        heading_data.append(['Submitted At', submitted_at])
        return heading_data
