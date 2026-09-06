/* SPDX-License-Identifier: Apache-2.0 */
const $ = (id) => document.getElementById(id);
let discovery = {cameras: [], labels: []};
let rules = [];

function token() { return localStorage.getItem('frigatespotter-token') || ''; }
async function api(path, options = {}) {
  const headers = {'Content-Type': 'application/json', ...(options.headers || {})};
  if (token()) headers.Authorization = `Bearer ${token()}`;
  const response = await fetch(path, {...options, headers});
  if (response.status === 204) return null;
  let body = null;
  try { body = await response.json(); } catch (_) { body = {}; }
  if (!response.ok) throw new Error(body.detail || `${response.status} ${response.statusText}`);
  return body;
}
function toast(message, error=false) {
  const el = $('toast'); el.textContent = message; el.className = `toast${error ? ' error' : ''}`; el.hidden = false;
  clearTimeout(el._timer); el._timer = setTimeout(() => el.hidden = true, 3500);
}
function option(value, text=value) { const el=document.createElement('option'); el.value=value; el.textContent=text; return el; }
function cameraByName(name) { return discovery.cameras.find(c => c.name === name); }
function renderSources(selectedCamera, selectedZone) {
  const select=$('sourceCamera'); select.innerHTML=''; discovery.cameras.forEach(c => select.append(option(c.name, c.friendly_name ? `${c.friendly_name} (${c.name})` : c.name)));
  if (selectedCamera && cameraByName(selectedCamera)) select.value=selectedCamera;
  renderZones(selectedZone);
}
function renderZones(selected) {
  const cam=cameraByName($('sourceCamera').value); const select=$('sourceZone'); select.innerHTML=''; select.append(option('*','Whole camera'));
  (cam?.zones || []).forEach(z => select.append(option(z)));
  if (selected && [...select.options].some(o => o.value===selected)) select.value=selected;
  renderLabels();
}
function renderTargets(selectedCamera, selectedPreset, selectedReturn) {
  const ptz=discovery.cameras.filter(c => c.ptz && (c.ptz.presets || []).length);
  const target=$('targetCamera'); target.innerHTML=''; ptz.forEach(c => target.append(option(c.name, c.ptz.name ? `${c.name} — ${c.ptz.name}` : c.name)));
  if (selectedCamera && ptz.some(c => c.name===selectedCamera)) target.value=selectedCamera;
  renderPresets(selectedPreset, selectedReturn);
}
function renderPresets(selected, selectedReturn) {
  const cam=cameraByName($('targetCamera').value); const presets=cam?.ptz?.presets || [];
  const target=$('targetPreset'); const ret=$('returnPreset'); target.innerHTML=''; ret.innerHTML=''; ret.append(option('','Stay at target preset'));
  presets.forEach(p => { target.append(option(p)); ret.append(option(p)); });
  if (selected && presets.includes(selected)) target.value=selected;
  if (selectedReturn && presets.includes(selectedReturn)) ret.value=selectedReturn;
}
function renderLabels(selected) {
  const cam=cameraByName($('sourceCamera').value); const labels=(cam?.labels?.length ? cam.labels : discovery.labels);
  const wanted=new Set(selected || [...document.querySelectorAll('#labels input:checked')].map(x=>x.value));
  $('labels').innerHTML=''; labels.forEach(label => { const wrap=document.createElement('label'); const box=document.createElement('input'); box.type='checkbox'; box.value=label; box.checked=wanted.has(label) || (!selected && ['dog','person'].includes(label)); wrap.append(box, document.createTextNode(label)); $('labels').append(wrap); });
}
function timeoutText(rule) {
  if (rule.timeout_mode==='never') return 'stay at preset';
  const ret=rule.return_preset ? ` → ${rule.return_preset}` : ' → stay';
  return rule.timeout_mode==='fixed' ? `fixed ${rule.timeout_seconds}s${ret}` : `clear + ${rule.timeout_seconds}s${ret}`;
}
function renderRules() {
  $('ruleCount').textContent=`${rules.length} rule${rules.length===1?'':'s'}`; $('rules').innerHTML='';
  if (!rules.length) { $('rules').innerHTML='<p>No rules yet. Create one above.</p>'; return; }
  rules.forEach(rule => { const el=document.createElement('article'); el.className=`rule${rule.enabled?'':' disabled'}`;
    const body=document.createElement('div'); body.innerHTML=`<div class="route"></div><div class="meta"></div>`; body.querySelector('.route').textContent=`${rule.source_camera} / ${rule.source_zone} / ${rule.labels.join(', ')} → ${rule.target_camera} / ${rule.target_preset}`; body.querySelector('.meta').textContent=`${rule.name || 'Unnamed'} · ${timeoutText(rule)} · priority ${rule.priority}`;
    const actions=document.createElement('div'); actions.className='rule-actions';
    const test=document.createElement('button'); test.className='secondary'; test.textContent='Test'; test.onclick=()=>testRoute(rule);
    const edit=document.createElement('button'); edit.className='secondary'; edit.textContent='Edit'; edit.onclick=()=>editRule(rule);
    const del=document.createElement('button'); del.className='danger'; del.textContent='Delete'; del.onclick=()=>deleteRule(rule);
    actions.append(test,edit,del); el.append(body,actions); $('rules').append(el);
  });
}
async function loadDiscovery(refresh=false) {
  discovery=await api(`/api/discovery${refresh?'?refresh=true':''}`); renderSources(); renderTargets(); if (!discovery.cameras.some(c=>c.ptz?.presets?.length)) toast('No PTZ presets discovered. Check ONVIF/PTZ configuration in Frigate.', true);
}
async function loadRules() { rules=await api('/api/rules'); renderRules(); }
async function loadStatus() {
  try { const s=await api('/api/status'); $('mqttDot').className=`dot ${s.mqtt_connected?'ok':'bad'}`; $('statusText').textContent=s.mqtt_connected?'MQTT connected':(s.mqtt_error || 'MQTT disconnected'); $('lastEvent').textContent=s.last_event_at?new Date(s.last_event_at*1000).toLocaleString():'—'; $('lastAction').textContent=s.last_action || '—'; } catch (e) { $('mqttDot').className='dot bad'; $('statusText').textContent=e.message; }
}
function formPayload() { return { name:$('name').value.trim(), enabled:$('enabled').checked, source_camera:$('sourceCamera').value, source_zone:$('sourceZone').value, labels:[...document.querySelectorAll('#labels input:checked')].map(x=>x.value), target_camera:$('targetCamera').value, target_preset:$('targetPreset').value, return_preset:$('returnPreset').value || null, timeout_mode:$('timeoutMode').value, timeout_seconds:Number($('timeoutSeconds').value), extend_on_activity:$('extend').checked, priority:Number($('priority').value) }; }
async function saveRule(event) { event.preventDefault(); try { const id=$('ruleId').value; const payload=formPayload(); if (!payload.labels.length) throw new Error('Select at least one object label'); if (!payload.target_camera || !payload.target_preset) throw new Error('No PTZ camera/preset selected'); await api(id?`/api/rules/${id}`:'/api/rules',{method:id?'PUT':'POST',body:JSON.stringify(payload)}); toast(id?'Rule updated':'Rule created'); resetForm(); await loadRules(); } catch(e) { toast(e.message,true); } }
function editRule(rule) { $('ruleId').value=rule.id; $('name').value=rule.name; $('enabled').checked=rule.enabled; renderSources(rule.source_camera,rule.source_zone); renderLabels(rule.labels); renderTargets(rule.target_camera,rule.target_preset,rule.return_preset); $('timeoutMode').value=rule.timeout_mode; $('timeoutSeconds').value=rule.timeout_seconds; $('extend').checked=rule.extend_on_activity; $('priority').value=rule.priority; $('cancelEdit').hidden=false; window.scrollTo({top:0,behavior:'smooth'}); }
function resetForm() { $('ruleId').value=''; $('name').value=''; $('enabled').checked=true; $('timeoutMode').value='after_clear'; $('timeoutSeconds').value=15; $('extend').checked=true; $('priority').value=50; $('cancelEdit').hidden=true; renderSources(); renderTargets(); }
async function deleteRule(rule) { if (!confirm(`Delete ${rule.name || 'this rule'}?`)) return; try { await api(`/api/rules/${rule.id}`,{method:'DELETE'}); await loadRules(); toast('Rule deleted'); } catch(e) { toast(e.message,true); } }
async function testRoute(rule) { try { await api('/api/ptz/test',{method:'POST',body:JSON.stringify({camera:rule.target_camera,preset:rule.target_preset})}); toast(`Sent ${rule.target_camera} → ${rule.target_preset}`); } catch(e) { toast(e.message,true); } }
async function testCurrent() { const camera=$('targetCamera').value,preset=$('targetPreset').value; if (!camera||!preset) return; await testRoute({target_camera:camera,target_preset:preset}); }
async function init() { try { const client=await api('/api/config/client'); $('authCard').hidden=!client.token_required; await loadDiscovery(); await loadRules(); await loadStatus(); setInterval(loadStatus,5000); } catch(e) { if (e.message.includes('invalid API token')) $('authCard').hidden=false; toast(e.message,true); } }
$('sourceCamera').addEventListener('change',()=>renderZones()); $('targetCamera').addEventListener('change',()=>renderPresets()); $('ruleForm').addEventListener('submit',saveRule); $('cancelEdit').addEventListener('click',resetForm); $('testPreset').addEventListener('click',()=>testCurrent().catch(e=>toast(e.message,true))); $('refreshDiscovery').addEventListener('click',()=>loadDiscovery(true).then(()=>toast('Discovery refreshed')).catch(e=>toast(e.message,true))); $('saveToken').addEventListener('click',()=>{ localStorage.setItem('frigatespotter-token',$('apiToken').value.trim()); location.reload(); });
init();
