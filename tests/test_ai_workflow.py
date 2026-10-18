import base64, importlib.util, json, unittest
from datetime import datetime, timezone
from pathlib import Path

spec=importlib.util.spec_from_file_location('ai',Path(__file__).resolve().parents[1]/'scripts/ai_workflow.py')
ai=importlib.util.module_from_spec(spec);spec.loader.exec_module(ai)
CONFIG={'text_model':'gpt-5-mini','image_model':'gpt-image-2','image_quality':'medium','daily_request_limit':3,'target_words':600}
SHA='a'*40

def topic():return {'topic':'Making a welcoming neighbourhood','angle':'A practical guide','notes':'No verified reporting supplied.','category':'Community','tone':'Clear and informative','billing_confirmed':True}
def article():return {'title':'A welcoming neighbourhood starts small','description':'Practical ways to make everyday connections in your local community.','body':'## Start with a small idea\n\n'+'An original editorial draft for review. '*30,'image_prompt':'An original editorial illustration of welcoming garden paths in a neighbourhood.','image_alt':'Illustrated garden paths and warm welcoming lights','facebook_caption':'Small steps can make a neighbourhood more welcoming.','review_notes':['Check every local factual claim.']}
def issue(number=7,login='FRYMASTERCHEESE',marker=ai.GENERATE,data=None):return {'number':number,'user':{'login':login},'created_at':datetime.now(timezone.utc).date().isoformat()+'T01:00:00Z','body':marker+'\n```json\n'+json.dumps(data if data is not None else topic())+'\n```'}

class FakeGitHub:
    repo='FRYMASTERCHEESE/fieldnotes-journal'
    def __init__(self):self.comments=[];self.calls=[];self.commits=[];self.existing=None;self.started=False;self.limit=False;self.receipt=None
    def comment(self,number,body):self.comments.append((number,body))
    def maybe(self,path):
        if '/review-receipts/' in path:return self.receipt
        return self.existing
    def api(self,method,path,data=None):
        self.calls.append((method,path,data))
        if '/comments?' in path:return [{'body':ai.STARTED}] if self.started else []
        if path.startswith('/issues?'):
            return [issue(i) for i in [1,2,3,7]] if self.limit else [issue()]
        if path.startswith('/git/ref/heads/ai-draft-'):return {'object':{'sha':SHA}}
        if path.startswith('/contents/assets/generated/'):return {'sha':'image-blob'}
        return {}
    def commit(self,branch,files,message,new=False):self.commits.append((branch,files,new));return SHA
    def json_file(self,path,revision):return {**article(),'source_issue':7,'image':'assets/generated/ai-7.jpg','metadata':ai.draft_metadata(article(),topic(),7,'FRYMASTERCHEESE',CONFIG)}

class AIWorkflowTests(unittest.TestCase):
    def test_no_key_makes_no_paid_call(self):
        gh=FakeGitHub()
        def fail(*args):self.fail('Paid provider called without credential')
        self.assertEqual(ai.prepare_generation(issue(),gh,'',CONFIG,{'frymastercheese':'Owner'},fail),'inactive')
        self.assertFalse(gh.commits)
    def test_unapproved_user_makes_no_paid_call(self):
        gh=FakeGitHub()
        self.assertEqual(ai.prepare_generation(issue(login='stranger'),gh,'test-key',CONFIG,{'frymastercheese':'Owner'},lambda *a:self.fail('Unexpected generation')),'denied')
    def test_duplicates_and_daily_limit_block_paid_calls(self):
        for flag,expected in [('started','already-attempted'),('limit','limited')]:
            gh=FakeGitHub();setattr(gh,flag,True)
            self.assertEqual(ai.prepare_generation(issue(),gh,'test-key',CONFIG,{'frymastercheese':'Owner'},lambda *a:self.fail('Unexpected generation')),expected)
    def test_generation_saves_unpublished_branch_not_main(self):
        gh=FakeGitHub()
        self.assertEqual(ai.prepare_generation(issue(),gh,'test-key',CONFIG,{'frymastercheese':'Owner'},lambda *a:(article(),b'\xff\xd8\xfffixture')),'generated')
        branch,files,new=gh.commits[0];self.assertEqual(branch,'ai-draft-7');self.assertTrue(new)
        self.assertIn('drafts/ai-7.md',files);self.assertFalse(any(p.startswith('content/') for p in files))
        self.assertTrue(json.loads(files['drafts/ai-7.md'].split('\n---\n')[0])['draft'])
        self.assertFalse(any('dispatches' in path for _,path,_ in gh.calls))
        self.assertTrue(any('studio/?review=7&revision='+SHA in body for _,body in gh.comments))
    def test_api_contract_and_image_validation(self):
        calls=[]
        def fake(key,endpoint,data):
            calls.append((endpoint,data))
            if endpoint=='responses':return {'status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':json.dumps(article())}]}]}
            return {'data':[{'b64_json':base64.b64encode(b'\xff\xd8\xfffixture').decode()}]}
        draft,image=ai.generate_content(topic(),CONFIG,'test-key',fake)
        self.assertEqual(len(calls),2);self.assertFalse(calls[0][1]['store']);self.assertEqual(calls[0][1]['text']['format']['type'],'json_schema')
        self.assertEqual(calls[1][1]['n'],1);self.assertEqual(calls[1][1]['output_format'],'jpeg');self.assertTrue(image.startswith(b'\xff\xd8\xff'))
    def approval(self):return {**article(),'source_issue':7,'source_revision':SHA,'category':'Community','rights_confirmed':True}
    def test_non_owner_cannot_publish(self):
        gh=FakeGitHub();self.assertEqual(ai.publish_review(issue(login='another-approved-author',marker=ai.APPROVE,data=self.approval()),gh,'FRYMASTERCHEESE'),'denied');self.assertFalse(gh.commits)
    def test_explicit_owner_approval_publishes_and_dispatches_ci(self):
        gh=FakeGitHub();self.assertEqual(ai.publish_review(issue(marker=ai.APPROVE,data=self.approval()),gh,'FRYMASTERCHEESE'),'approved')
        branch,files,new=gh.commits[0];self.assertEqual(branch,'main');self.assertFalse(new)
        content=next(v for k,v in files.items() if k.startswith('content/'));meta=json.loads(content.split('\n---\n')[0]);self.assertFalse(meta['draft']);self.assertTrue(meta['ai_reviewed'])
        self.assertTrue(any('dispatches' in path for _,path,_ in gh.calls));self.assertFalse(any('facebook.com' in path for _,path,_ in gh.calls))
    def test_missing_confirmation_or_stale_reference_is_rejected(self):
        for updates in [{'rights_confirmed':False},{'source_revision':'b'*40},{'source_issue':'../../bad'}]:
            gh=FakeGitHub()
            with self.subTest(updates=updates),self.assertRaises(ValueError):ai.publish_review(issue(marker=ai.APPROVE,data={**self.approval(),**updates}),gh,'FRYMASTERCHEESE')
            self.assertFalse(gh.commits)
    def test_approval_receipt_prevents_duplicate_articles(self):
        gh=FakeGitHub();gh.receipt={'content':base64.b64encode(json.dumps({'url':ai.SITE+'articles/existing/'}).encode()).decode()}
        self.assertEqual(ai.publish_review(issue(marker=ai.APPROVE,data=self.approval()),gh,'FRYMASTERCHEESE'),'already-published');self.assertFalse(gh.commits)
    def test_request_validation_and_refusal(self):
        for data in [{'topic':''},{'billing_confirmed':False},{'category':'unknown'}]:
            with self.subTest(data=data),self.assertRaises(ValueError):ai.validate_topic({**topic(),**data})
        with self.assertRaises(RuntimeError):ai.generate_content(topic(),CONFIG,'test-key',lambda *a:{'status':'incomplete','output':[]})

if __name__=='__main__':unittest.main()
