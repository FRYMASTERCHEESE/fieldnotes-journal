import unittest, importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('submission',Path(__file__).resolve().parents[1]/'scripts/prepare-submission.py')
submission=importlib.util.module_from_spec(spec);spec.loader.exec_module(submission)

class SubmissionTests(unittest.TestCase):
    def draft(self):
        return {'title':'Original story','description':'An introduction','body':'Original writing. '*12,'slug':'original-story','category':'Everyday','image':'assets/cover-coast.jpg','image_alt':'A coastal scene','image_credit':'Fieldnotes','image_license':'Original illustration','rights_confirmed':True}
    def test_original_artwork_submission(self):
        self.assertEqual(submission.validate(self.draft())['slug'],'original-story')
    def test_rights_and_path_validation(self):
        for update in [{'rights_confirmed':False},{'slug':'../../x'},{'image':'javascript:alert(1)'},{'image':'https://example.com/photo.jpg'},{'image_source':'http://example.com'},{'title':['invalid']},{'image_alt':''}]:
            with self.subTest(update=update),self.assertRaises(ValueError):submission.validate({**self.draft(),**update})
    def test_github_image_with_credit_is_supported(self):
        draft={**self.draft(),'image':'https://github.com/user-attachments/assets/abc-123','image_source':'https://example.com/licence'}
        self.assertEqual(submission.validate(draft)['image'],draft['image'])

if __name__=='__main__':unittest.main()
