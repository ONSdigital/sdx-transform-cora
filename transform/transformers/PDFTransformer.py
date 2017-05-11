#!/usr/bin/env python
#   coding: UTF-8

import argparse
from copy import copy
from io import BytesIO
import json
import os
import sys
import uuid


import arrow
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSamplestyle_sheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.enums import TA_LEFT, TA_CENTER

__doc__ = """
SDX PDF Transformer.

Example:

python transform/transformers/PDFTransformer.py --survey transform/surveys/144.0001.json \\
< tests/replies/ukis-01.json > output.pdf

"""

styles = getSamplestyle_sheet()

# Basic text style
style_n = copy(styles["BodyText"])
style_n.alignment = TA_LEFT

# Answer Style
style_answer = copy(styles["BodyText"])
style_answer.alignment = TA_LEFT
style_answer.fontName = "Helvetica-Bold"
style_answer.textColor = colors.red
style_answer.fontSize = 15
style_answer.leading = 20
style_answer.spaceAfter = 20

# Subheading style
style_sh = styles["Heading2"]
style_sh.alignment = TA_LEFT

# Sub-subheading style (questions)
style_ssh = styles["Heading3"]
style_ssh.alignment = TA_LEFT

# Main heading style
style_h = styles['Heading1']
style_h.alignment = TA_CENTER

MAX_ANSWER_CHARACTERS_PER_LINE = 35


class PDFTransformer(object):

    def __init__(self, survey, response_data):
        '''
        Sets up variables needed to write out a pdf
        '''
        self.survey = survey
        self.response = response_data

    def render(self):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        doc.build(self.get_elements())

        pdf = buffer.getvalue()
        buffer.close()

        return pdf

    def render_to_file(self):
        randomName = uuid.uuid4()

        os.makedirs("./tmp/%s" % randomName)

        tmpName = "./tmp/%s/%s.pdf" % (randomName, randomName)
        doc = SimpleDocTemplate(tmpName, pagesize=A4)
        doc.build(self.get_elements())

        return os.path.realpath(tmpName)

    def get_elements(self):

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

        heading_data = [[Paragraph(self.survey['title'], style_h)]]
        heading_data.append(['Form Type', self.response['collection']['instrument_id']])
        heading_data.append(['Respondent', self.response['metadata']['ru_ref'][:11]])
        heading_data.append(['Submitted At', localised_date_str])

        heading = Table(heading_data, style=heading_style, colWidths='*')

        elements.append(heading)

        for question_group in filter(lambda x: 'title' in x, self.survey['question_groups']):

            has_section_heading_output = False

            for question in filter(lambda x: 'text' in x, question_group['questions']):
                try:
                    answer = self.response['data'][question['question_id']]
                except KeyError:
                    answer = ''

                if question['question_id'] in self.response['data']:
                    answer = self.response['data'][question['question_id']]

                    # Output the section header if we haven't already
                    # Checking here so that whole sections are suppressed
                    # if they have no answers.
                    if not has_section_heading_output:
                        elements.append(HRFlowable(width="100%"))
                        elements.append(Paragraph(question_group['title'], style_sh))
                        has_section_heading_output = True

                    # Question not output if answer is empty
                    text = question.get("text")
                    if not text[0].isdigit():
                        text = " ".join((question.get("number", ""), text))
                    elements.append(Paragraph(text, style_n))
                    elements.append(Paragraph(answer, style_answer))

        return elements

    def get_localised_date(self, date_to_transform, timezone='Europe/London'):
        return arrow.get(date_to_transform).to(timezone).format("DD MMMM YYYY HH:mm:ss")


def parser(description=__doc__):
    rv = argparse.ArgumentParser(
        description,
    )
    rv.add_argument(
        "--survey", required=True,
        help="Set a path to the survey JSON file.")
    return rv


def main(args):
    fp = os.path.expanduser(os.path.abspath(args.survey))
    with open(fp, "r") as f_obj:
        survey = json.load(f_obj)

        data = json.load(sys.stdin)
        tx = PDFTransformer(survey, data)
        output = tx.render()
        sys.stdout.write(output.decode("utf-8"))
        return 0


def run():
    p = parser()
    args = p.parse_args()
    rv = main(args)
    sys.exit(rv)

if __name__ == "__main__":
    run()
