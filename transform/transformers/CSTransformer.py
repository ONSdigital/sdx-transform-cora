import zipfile
import os
from io import BytesIO
from .ImageTransformer import ImageTransformer
from jinja2 import Environment, PackageLoader
import dateutil.parser
import shutil

env = Environment(loader=PackageLoader('transform', 'templates'))


class CSTransformer(object):
    def __init__(self, logger, survey, response_data, batch_number=False, sequence_no=1000):
        self.logger = logger
        self.survey = survey
        self.response = response_data
        self.path = ""
        self.images = []
        self.index = None
        # A list of (dest, file) tuples
        self.files_to_archive = []
        self.batch_number = batch_number
        self.sequence_no = sequence_no

    def create_formats(self, numberSeq=None):
        itransformer = ImageTransformer(
            self.logger, self.survey, self.response, sequence_no=self.sequence_no
        )

        path = itransformer.create_pdf(self.survey, self.response)
        self.images = list(itransformer.create_image_sequence(path, numberSeq))
        self.index = itransformer.create_image_index(self.images)

        self.path, baseName = os.path.split(path)
        self.rootname, _ = os.path.splitext(baseName)

        self.create_idbr()
        return path

    def prepare_archive(self):
        '''
        Prepare a list of files to save
        '''
        self.files_to_archive.append(("EDC_QReceipts", self.idbr_file))

        for image in self.images:
            fN = os.path.basename(image)
            self.files_to_archive.append(("EDC_QImages/Images", fN))

        if self.index is not None:
            fN = os.path.basename(self.index)
            self.files_to_archive.append(("EDC_QImages/Index", fN))

    def create_idbr(self):
        template = env.get_template('idbr.tmpl')
        template_output = template.render(response=self.response)
        submission_date = dateutil.parser.parse(self.response['submitted_at'])
        submission_date_str = submission_date.strftime("%d%m")

        # Format is RECddMM_batchId.DAT
        # e.g. REC1001_30000.DAT for 10th January, batch 30000
        self.idbr_file = "REC%s_%04d.DAT" % (submission_date_str, self.sequence_no)

        with open(os.path.join(self.path, self.idbr_file), "w") as fh:
            fh.write(template_output)

    def create_zip(self):
        '''
        Create a in memory zip from a renumbered sequence
        '''
        in_memory_zip = BytesIO()

        with zipfile.ZipFile(in_memory_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for dest, file in self.files_to_archive:
                zipf.write(os.path.join(self.path, file), arcname="%s/%s" % (dest, file))

        # Return to beginning of file
        in_memory_zip.seek(0)

        return in_memory_zip

    def cleanup(self, locn=None):
        locn = locn or self.path
        shutil.rmtree(locn)
