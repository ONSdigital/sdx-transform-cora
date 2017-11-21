import arrow

from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.platypus.flowables import HRFlowable

__doc__ = """
SDX PDF Transformer.
This is a general purpose image transformer that uses a style class to encapsulate differences between uses .

AFTER Success on Cora it could be used in the CS and MWSS transformers ? This would then be a precursor to
a single transform service possibly with pluggable extensions ?
"""


class InMemoryPDFTransformer:

    def __init__(self, survey, response_data, style):
        """
        Sets up variables needed to write out a pdf
        uses a style class to handle differences between types of transformer
        """
        self.survey = survey
        self.response = response_data
        self.style = style

    def render(self):
        """Get the pdf data in memory"""
        return self.render_pages()[0]

    def render_pages(self):
        """Return both the in memory pdf data and a count of the pages"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        doc.build(self._get_elements())

        pdf = buffer.getvalue()

        buffer.close()

        return pdf, doc.page

    def _get_elements(self):

        elements = []
        table_style_data = [('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                            ('LINEBELOW', (0, 0), (-1, -1), 1, colors.black),
                            ('BOX', (0, 0), (-1, -1), 1, colors.black),
                            ('BOX', (0, 0), (0, -1), 1, colors.black),
                            ('BACKGROUND', (0, 0), (1, 0), colors.lightblue)]

        table_style = TableStyle(table_style_data)
        table_style.spaceAfter = 25

        heading_style = TableStyle(table_style_data)
        heading_style.spaceAfter = 25
        heading_style.add('SPAN', (0, 0), (1, 0))
        heading_style.add('ALIGN', (0, 0), (1, 0), 'CENTER')

        localised_date_str = self.get_localised_date(self.response['submitted_at'])

        heading_data = self.style.get_heading_data(self.survey['title'], self.response['collection']['instrument_id'],
                                                   self.response['metadata']['ru_ref'], localised_date_str)

        heading = Table(heading_data, style=heading_style, colWidths='*')

        elements.append(heading)

        for question_group in filter(lambda x: 'title' in x, self.survey['question_groups']):

            section_heading = True

            for question in filter(lambda x: 'text' in x, question_group['questions']):
                if question['question_id'] in self.response['data']:
                    try:
                        answer = str(self.response['data'][question['question_id']])
                    except KeyError:
                        answer = ''

                    # Output the section header if we haven't already
                    # Checking here so that whole sections are suppressed
                    # if they have no answers.
                    if section_heading:
                        elements.append(HRFlowable(width="100%"))
                        elements.append(Paragraph(question_group['title'], self.style.style_sh))
                        section_heading = False

                    # Question not output if answer is empty
                    text = question.get("text")
                    if not text[0].isdigit():
                        text = " ".join((question.get("number", ""), text))
                    elements.append(Paragraph(text, self.style.style_n))
                    elements.append(Paragraph(answer, self.style.style_answer))

        return elements

    @staticmethod
    def get_localised_date(date_to_transform, timezone='Europe/London'):
        return arrow.get(date_to_transform).to(timezone).format("DD MMMM YYYY HH:mm:ss")

