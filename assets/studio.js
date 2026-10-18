(() => {
  const form = document.querySelector('#article-form');
  if (!form) return;
  document.querySelector('#studio').hidden = false;
  const $ = id => document.getElementById(id);
  const site = new URL('../', document.currentScript.src);
  const repository = 'https://github.com/FRYMASTERCHEESE/fieldnotes-journal';
  const fields = ['article-title','article-description','article-category','article-body','cover-kind','cover-url','cover-credit','cover-license','cover-source','cover-alt','review-image-alt','facebook-caption'];
  let picture;
  let reviewDraft = null;
  const slug = () => ($('article-title').value.toLowerCase().normalize('NFKD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'').slice(0,65) || 'new-story');
  function update() {
    const custom = $('cover-kind').value === 'custom';
    $('custom-cover').hidden = !custom;
    for (const id of ['cover-url','cover-credit','cover-license','cover-alt']) $(id).required = custom;
    const text=$('article-body').value.trim();
    const words=text ? text.split(/\s+/).length : 0;
    $('word-count').textContent=`${words} words · ${Math.max(1,Math.ceil(words/220))} min read`;
    $('preview-title').textContent=$('article-title').value || 'Your headline goes here';
    $('preview-description').textContent=$('article-description').value || 'Your short introduction will appear here.';
    $('preview-category').textContent=$('article-category').value;
    $('preview-body').replaceChildren();
    text.split(/\n\s*\n/).forEach(block=>{
      const heading=block.startsWith('## ');
      const el=document.createElement(heading ? 'h4':'p');
      el.textContent=heading ? block.slice(3) : block;
      $('preview-body').append(el);
    });
    const imageURL=$('cover-url').value.trim();
    const safe=/^https:\/\/github\.com\/user-attachments\/assets\/[a-zA-Z0-9-]+$/.test(imageURL);
    $('preview-image').src=reviewDraft ? reviewDraft.image_preview_url : custom && safe ? imageURL : new URL('assets/cover-coast.jpg',site).href;
    $('preview-image').alt=reviewDraft ? $('review-image-alt').value : custom && safe ? $('cover-alt').value : 'AI-created coastal landscape illustration';
    if (!reviewDraft) $('facebook-caption').value=`${$('article-title').value || 'Your headline'}\n\n${$('article-description').value}\n\nRead the full story after the editor publishes it. Use the article’s Facebook share button for its final link.`;
    $('submission-ready').hidden=true;
  }
  form.addEventListener('input',update);
  function payload() {
    if (reviewDraft) return {title:$('article-title').value.trim(),description:$('article-description').value.trim(),category:$('article-category').value,body:$('article-body').value.trim(),source_issue:reviewDraft.source_issue,source_revision:reviewDraft.source_revision,image_alt:$('review-image-alt').value.trim(),facebook_caption:$('facebook-caption').value.trim(),rights_confirmed:$('rights-check').checked};
    return {title:$('article-title').value.trim(),description:$('article-description').value.trim(),category:$('article-category').value,body:$('article-body').value.trim(),slug:slug(),image:$('cover-kind').value==='custom'?$('cover-url').value.trim():'assets/cover-coast.jpg',image_alt:$('cover-kind').value==='custom'?$('cover-alt').value.trim():'AI-created coastal path and sea in morning light',image_credit:$('cover-kind').value==='custom'?$('cover-credit').value.trim():'Original AI-created illustration for Fieldnotes',image_license:$('cover-kind').value==='custom'?$('cover-license').value:'AI-generated illustration; reviewed by editor',image_source:$('cover-kind').value==='custom'?$('cover-source').value.trim():'',rights_confirmed:$('rights-check').checked};
  }
  form.addEventListener('submit',event=>{
    event.preventDefault();
    const p=payload();
    if(!reviewDraft && p.image.startsWith('https:')&&!/^https:\/\/github\.com\/user-attachments\/assets\/[a-zA-Z0-9-]+$/.test(p.image)) { $('studio-status').textContent='Use a public GitHub image attachment URL for your cover.'; $('cover-url').focus(); return; }
    if(reviewDraft && (!$('review-image-alt').value.trim() || !$('facebook-caption').value.trim())) { $('studio-status').textContent='Add an image description and a Facebook caption before approval.';return; }
    const body=(reviewDraft?'<!-- fieldnotes-ai-approve -->':'<!-- fieldnotes-submission -->')+'\n```json\n'+JSON.stringify(p,null,2)+'\n```';
    $('submission-data').value=body;
    const prefix=reviewDraft?'[Approve AI draft] ':'[Article] ';
    const link=repository+'/issues/new?title='+encodeURIComponent(prefix+p.title)+'&body='+encodeURIComponent(body);
    $('submit-link').href=link.length<7500?link:repository+'/issues/new?title='+encodeURIComponent(prefix+p.title);
    $('submission-ready').hidden=false;
    $('studio-status').textContent=link.length<7500?(reviewDraft?'Approval request ready. Review it on GitHub and click Create to approve publication.':'Draft ready. Open the GitHub submission for your final review.'):'Request ready. Copy the submission backup into the GitHub issue description before submitting.';
  });
  function download(data,name,type) {
    const blob=data instanceof Blob?data:new Blob([data],{type});
    const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  $('download-draft').addEventListener('click',()=>{
    const p=payload(); download(JSON.stringify(p,null,2),slug()+'.json','application/json');
    $('studio-status').textContent='Draft backup downloaded.';
  });
  $('save-draft').addEventListener('click',()=>{
    try{localStorage.setItem('fieldnotes-draft',JSON.stringify(Object.fromEntries(fields.map(id=>[id,$(id).value]))));$('studio-status').textContent='Draft saved on this device.';}catch{$('studio-status').textContent='Browser storage is unavailable. Download a draft backup instead.';}
  });
  $('restore-draft').addEventListener('click',()=>{
    try{const saved=JSON.parse(localStorage.getItem('fieldnotes-draft')||'null');if(!saved){$('studio-status').textContent='No saved draft on this device.';return;}fields.forEach(id=>{if(typeof saved[id]==='string')$(id).value=saved[id];});update();$('studio-status').textContent='Saved draft restored.';}catch{$('studio-status').textContent='The saved draft could not be restored.';}
  });
  $('clear-draft').addEventListener('click',()=>{try{localStorage.removeItem('fieldnotes-draft');$('studio-status').textContent='Saved browser draft deleted. The current editor text is unchanged.';}catch{$('studio-status').textContent='Browser storage is unavailable.';}});
  $('copy-caption').addEventListener('click',async()=>{try{await navigator.clipboard.writeText($('facebook-caption').value);$('studio-status').textContent='Facebook caption copied.';}catch{$('facebook-caption').focus();$('facebook-caption').select();$('studio-status').textContent='Select and copy the caption from the text box.';}});
  $('social-file').addEventListener('change',async()=>{
    picture=null; $('download-picture').disabled=true;
    const file=$('social-file').files[0]; if(!file)return;
    if(!['image/jpeg','image/png','image/webp'].includes(file.type)||file.size>20*1024*1024){$('studio-status').textContent='Choose a JPEG, PNG or WebP smaller than 20 MB.';return;}
    const objectURL=URL.createObjectURL(file);
    try{const image=new Image();image.src=objectURL;await image.decode();const canvas=document.createElement('canvas');canvas.width=1200;canvas.height=630;const scale=Math.max(1200/image.width,630/image.height);canvas.getContext('2d').drawImage(image,(1200-image.width*scale)/2,(630-image.height*scale)/2,image.width*scale,image.height*scale);picture=await new Promise(resolve=>canvas.toBlob(resolve,'image/jpeg',.9));$('download-picture').disabled=!picture;$('studio-status').textContent='Facebook picture ready. Check the centred crop before sharing.';}catch{$('studio-status').textContent='This image could not be opened. Try another JPEG, PNG or WebP.';}finally{URL.revokeObjectURL(objectURL);}
  });
  $('download-picture').addEventListener('click',()=>{if(picture)download(picture,slug()+'-facebook.jpg');});
  $('review-image-alt').addEventListener('input',update);
  const generationForm=$('generation-form');
  let generationAvailable=false;
  fetch(new URL('generation-status.json',site),{cache:'no-store'}).then(response=>{if(!response.ok)throw new Error('Setup unavailable');return response.json();}).then(config=>{
    generationAvailable=config.available===true;
    $('generate-draft').disabled=!generationAvailable;
    $('generation-availability').textContent=generationAvailable?'AI generation is configured. Approved authors can request a draft and one cover.':'AI generation is not activated. The owner can add the API credential later; writing and image tools below are ready to use.';
  }).catch(()=>{$('generation-availability').textContent='Generation setup could not be checked. Try reloading or use the writing tools below.';});
  generationForm.addEventListener('input',()=>{$('generation-ready').hidden=true;});
  generationForm.addEventListener('submit',event=>{
    event.preventDefault();if(!generationAvailable)return;
    const data={topic:$('generation-topic').value.trim(),angle:$('generation-angle').value.trim(),notes:$('generation-notes').value.trim(),category:$('generation-category').value,tone:$('generation-tone').value,billing_confirmed:$('generation-billing').checked};
    const body='<!-- fieldnotes-ai-generate -->\n```json\n'+JSON.stringify(data,null,2)+'\n```';
    const title='[Generate article] '+data.topic.slice(0,180);
    const href=repository+'/issues/new?title='+encodeURIComponent(title)+'&body='+encodeURIComponent(body);
    $('generation-link').href=href.length<7500?href:repository+'/issues/new?title='+encodeURIComponent(title);
    $('generation-data').value=body;
    $('generation-ready').hidden=false;
    $('generation-availability').textContent=href.length<7500?'Request prepared. Open it on GitHub and click Create to start generation.':'Request prepared. Copy the request data below into the GitHub issue before clicking Create.';
  });
  async function loadReview() {
    const query=new URL(location.href).searchParams;
    if(!query.has('review')&&!query.has('revision'))return;
    $('ai-review-panel').hidden=false;
    const number=query.get('review');const revision=query.get('revision');
    if(!/^[1-9][0-9]*$/.test(number||'')||!/^[a-f0-9]{40}$/.test(revision||'')){$('ai-review-status').textContent='This review link is invalid. Open the review link from your generation request.';return;}
    $('ai-review-status').textContent='Loading your unpublished draft…';
    try {
      const raw=`https://raw.githubusercontent.com/FRYMASTERCHEESE/fieldnotes-journal/${revision}/`;
      const response=await fetch(raw+`review/ai-${number}.json`);
      if(!response.ok)throw new Error('Draft unavailable');
      const draft=await response.json();
      if(draft.source_issue!==Number(number)||draft.image!==`assets/generated/ai-${number}.jpg`||!['title','description','body','image_alt','facebook_caption'].every(field=>typeof draft[field]==='string')||!Array.isArray(draft.review_notes))throw new Error('Invalid draft');
      reviewDraft={...draft,source_revision:revision,image_preview_url:raw+draft.image};
      $('article-title').value=draft.title;$('article-description').value=draft.description;$('article-body').value=draft.body;$('article-category').value=draft.category;
      $('review-image-alt').value=draft.image_alt;
      $('facebook-caption').readOnly=false;$('facebook-caption').value=draft.facebook_caption;
      const option=document.createElement('option');option.value='generated';option.textContent='Generated cover for this draft';$('cover-kind').append(option);$('cover-kind').value='generated';$('cover-kind').disabled=true;
      $('ai-review-notes').replaceChildren();
      [...draft.review_notes,'Confirm all factual claims, originality, image suitability and social-sharing permissions.'].forEach(note=>{const li=document.createElement('li');li.textContent=String(note);$('ai-review-notes').append(li);});
      $('rights-check').checked=false;
      $('prepare-review').textContent='Prepare approval to publish ↗';
      $('submit-link').textContent='Open publication approval on GitHub ↗';
      $('submission-explanation').textContent='Only the repository owner can submit a valid publication approval. Clicking Create on GitHub explicitly approves this edited draft for publication. Build and browser checks run before the site is deployed. Facebook sharing remains manual.';
      update();
      $('ai-review-status').textContent='Draft loaded. Nothing is published yet. Edit and check it before preparing approval.';
    }catch{$('ai-review-status').textContent='The draft could not be loaded. Reopen its latest review link from the generation issue. Nothing has been published.';}
  }
  update();
  loadReview();
})();
