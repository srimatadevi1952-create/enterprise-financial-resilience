const requestForm=document.querySelector('#request-form');
const verifyForm=document.querySelector('#verify-form');
const emailInput=document.querySelector('#email');
const codeInput=document.querySelector('#code');
const notice=document.querySelector('#notice');
const developmentCode=document.querySelector('#development-code');

async function post(path,payload){
  const response=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
  const data=await response.json();
  if(!response.ok)throw new Error(data.error||'The request could not be completed');
  return data;
}
function busy(form,value){for(const element of form.elements)element.disabled=value}
requestForm.addEventListener('submit',async event=>{
  event.preventDefault();busy(requestForm,true);notice.textContent='Checking your invitation…';developmentCode.style.display='none';
  try{
    const data=await post('/api/auth/request-code',{email:emailInput.value});
    notice.textContent=data.message;requestForm.hidden=true;verifyForm.hidden=false;
    if(data.development_code){developmentCode.textContent=`Local development code: ${data.development_code}`;developmentCode.style.display='block'}
    codeInput.focus();
  }catch(error){notice.textContent=error.message}finally{busy(requestForm,false)}
});
verifyForm.addEventListener('submit',async event=>{
  event.preventDefault();busy(verifyForm,true);notice.textContent='Verifying identity and role…';
  try{await post('/api/auth/verify-code',{email:emailInput.value,code:codeInput.value});location.replace('/')}
  catch(error){notice.textContent=error.message;busy(verifyForm,false);codeInput.select()}
});
document.querySelector('#back-button').addEventListener('click',()=>{verifyForm.hidden=true;requestForm.hidden=false;developmentCode.style.display='none';notice.textContent='';codeInput.value='';emailInput.focus()});
document.querySelector('.mark').innerHTML='<i></i>'.repeat(25);

