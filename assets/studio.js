(() => {
  const form = document.querySelector('#article-form');
  if (!form) return;
  document.querySelector('#studio').hidden = false;
  const $ = id => document.getElementById(id);
  const site = new URL('../', document.currentScript.src);
  const repository = 'https://github.com/FRYMASTERCHEESE/fieldnotes-journal';
  const fields = ['article-title','article-description','article-category','article-body','cover-kind','cover-url','cover-credit','cover-license','cover-source','cover-alt'];
  let picture;
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
    $('preview-image').src=custom && safe ? imageURL : new URL('assets/cover-coast.jpg',site).href;
    $('preview-image').alt=custom && safe ? $('cover-alt').value : 'AI-created coastal landscape illustration';
    $('facebook-caption').value=`${$('article-title').value || 'Your headline'}\n\n${$('article-description').value}\n\nRead the full story after the editor publishes it. Use the article’s Facebook share button for its final link.`;
    $('submission-ready').hidden=true;
  }
  form.addEventListener('input',update);
  function payload() {
    return {title:$('article-title').value.trim(),description:$('article-description').value.trim(),category:$('article-category').value,body:$('article-body').value.trim(),slug:slug(),image:$('cover-kind').value==='custom'?$('cover-url').value.trim():'assets/cover-coast.jpg',image_alt:$('cover-kind').value==='custom'?$('cover-alt').value.trim():'AI-created coastal path and sea in morning light',image_credit:$('cover-kind').value==='custom'?$('cover-credit').value.trim():'Original AI-created illustration for Fieldnotes',image_license:$('cover-kind').value==='custom'?$('cover-license').value:'AI-generated illustration; reviewed by editor',image_source:$('cover-kind').value==='custom'?$('cover-source').value.trim():'',rights_confirmed:$('rights-check').checked};
  }
  form.addEventListener('submit',event=>{
    event.preventDefault();
    const p=payload();
    if(p.image.startsWith('https:')&&!/^https:\/\/github\.com\/user-attachments\/assets\/[a-zA-Z0-9-]+$/.test(p.image)) { $('studio-status').textContent='Use a public GitHub image attachment URL for your cover.'; $('cover-url').focus(); return; }
    const body='<!-- fieldnotes-submission -->\n```json\n'+JSON.stringify(p,null,2)+'\n```';
    $('submission-data').value=body;
    const link=repository+'/issues/new?title='+encodeURIComponent('[Article] '+p.title)+'&body='+encodeURIComponent(body);
    $('submit-link').href=link.length<7500?link:repository+'/issues/new?title='+encodeURIComponent('[Article] '+p.title);
    $('submission-ready').hidden=false;
    $('studio-status').textContent=link.length<7500?'Draft ready. Open the GitHub submission for your final review.':'Draft ready. Copy the submission backup into the GitHub issue description before submitting.';
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
  update();
})();
