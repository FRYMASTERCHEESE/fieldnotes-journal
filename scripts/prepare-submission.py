"""Convert an approved author's structured issue into a reviewable pull request.

Issue text is parsed as data only. No shell evaluation or execution is used.
"""
import os, json, re, base64
from pathlib import Path
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import HTTPError

def validate(payload):
    if not isinstance(payload,dict): raise ValueError('Submission must be an object')
    for field,limit in [('title',120),('description',240),('body',20000),('slug',65),('category',50),('image_alt',300),('image_credit',200),('image_license',200),('image_source',1000)]:
        value=payload.get(field,'')
        if not isinstance(value,str) or len(value)>limit: raise ValueError('Invalid '+field)
    for field in ['title','description','body','category','image_alt','image_credit','image_license']:
        if not payload.get(field,'').strip(): raise ValueError('Missing '+field)
    if len(payload['body'].strip())<80: raise ValueError('Article must contain at least 80 characters')
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',payload['slug']): raise ValueError('Invalid article slug')
    if payload.get('rights_confirmed') is not True: raise ValueError('Rights confirmation required')
    image=payload.get('image','')
    if image!='assets/cover-coast.jpg' and not re.fullmatch(r'https://github\.com/user-attachments/assets/[a-zA-Z0-9-]+',image): raise ValueError('Use the original artwork or a GitHub image attachment URL')
    source=payload.get('image_source','')
    if source and not source.startswith('https://'): raise ValueError('Source URL must use HTTPS')
    return payload

def main():
    event=json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text())
    issue=event['issue']; repo=os.environ['GITHUB_REPOSITORY']; number=issue['number']
    token=os.environ['GH_TOKEN']
    def api(method,path,data=None):
        req=Request('https://api.github.com/repos/'+repo+path,data=json.dumps(data).encode() if data is not None else None,method=method,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','Content-Type':'application/json','X-GitHub-Api-Version':'2022-11-28'})
        with urlopen(req,timeout=30) as r: return json.load(r)
    def comment(message): api('POST',f'/issues/{number}/comments',{'body':message})
    authors={k.lower():v for k,v in json.loads(Path('authors.json').read_text()).items()}
    login=issue['user']['login']
    if login.lower() not in authors:
        comment('This journal accepts submissions from approved authors. Please ask the editor to add your GitHub username to authors.json. This submission has not been published.'); return
    try:
        match=re.search(r'```json\s*\n(.*?)\n```',issue.get('body',''),re.S)
        if not match: raise ValueError('Submission JSON was not found')
        payload=validate(json.loads(match.group(1)))
    except (ValueError,TypeError,KeyError) as error:
        comment('The draft could not be prepared: '+str(error)+'. Correct it in the Author Studio and open a new submission.'); return
    branch=f'article-submission-{number}'
    existing=api('GET',f'/pulls?state=all&head={repo.split("/")[0]}:{branch}')
    if existing: comment('A review request already exists: '+existing[0]['html_url']); return
    head=api('GET','/git/ref/heads/main')['object']['sha']
    try: api('GET','/git/ref/heads/'+branch)
    except HTTPError as error:
        if error.code != 404: raise
        api('POST','/git/refs',{'ref':'refs/heads/'+branch,'sha':head})
    meta={k:payload[k] for k in ['title','description','category','image_alt','image_credit','image_license','image_source','image']}
    meta.update(date=datetime.now(timezone.utc).date().isoformat(),author=authors[login.lower()],author_login=login,draft=False,rights_confirmed=True)
    path=f'content/{payload["slug"]}-{number}.md'
    content=json.dumps(meta,ensure_ascii=False)+'\n---\n'+payload['body']+'\n'
    file_data={'message':f'Prepare article submission #{number}','branch':branch,'content':base64.b64encode(content.encode()).decode()}
    try: file_data['sha']=api('GET','/contents/'+path+'?ref='+branch)['sha']
    except HTTPError as error:
        if error.code != 404: raise
    api('PUT','/contents/'+path,file_data)
    body=f'Prepared from #{number} by approved author @{login}.\n\nEditor: verify factual claims, image permission/source, attribution, alt text and Facebook use rights. The site publishes only after this change is merged. Run the Test and publish journal workflow on this branch before merging; GitHub does not trigger another workflow from changes made with GITHUB_TOKEN.\n\nCloses #{number}'
    try:
        pr=api('POST','/pulls',{'title':payload['title'],'head':branch,'base':'main','body':body})
        comment('Your article is ready for editor review: '+pr['html_url']+'\n\nIt is not published yet. After approval and deployment, the article will be at https://frymastercheese.github.io/fieldnotes-journal/articles/'+payload['slug']+f'-{number}/')
    except Exception:
        comment('The draft branch is ready. Open its review request here: https://github.com/'+repo+'/compare/main...'+branch+'?expand=1\n\nAutomatic review-request creation is disabled in repository Actions settings. The editor can open it manually; nothing has been published.')
        return

if __name__=='__main__': main()
