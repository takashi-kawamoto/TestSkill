const list = document.querySelector('#list');
const message = document.querySelector('#message');
const form = document.querySelector('#form');
const editor = document.querySelector('#editor');
const add = document.querySelector('#add');
let editingId = null;
let busy = false;

function node(tag, text, className) {
  const item = document.createElement(tag);
  if (text !== undefined) item.textContent = text;
  if (className) item.className = className;
  return item;
}
async function api(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(typeof data.detail === 'string' ? data.detail : '入力内容を確認してください。');
  }
  return response.status === 204 ? null : response.json();
}
function notify(text, failed = false) {
  message.textContent = text;
  message.className = failed ? 'status wrong' : 'status';
}
function setBusy(value) {
  busy = value;
  document.querySelectorAll('button, input, textarea, select').forEach(item => { item.disabled = value; });
}
async function load() {
  list.setAttribute('aria-busy', 'true');
  try {
    const data = await api('/api/admin/questions');
    list.replaceChildren();
    document.querySelector('#total').textContent = '(' + data.questions.length + ' / 5)';
    if (!data.questions.length) list.append(node('p', '問題が未登録です。最初の問題を追加しましょう。'));
    data.questions.forEach(question => {
      const row = node('article', undefined, 'review');
      row.append(node('strong', question.text), node('p', '正解：' + question.choices[question.correct]), node('p', question.explanation));
      const actions = node('div', undefined, 'actions');
      const edit = node('button', '編集');
      edit.addEventListener('click', () => openEditor(question));
      const remove = node('button', '削除', 'danger');
      remove.addEventListener('click', async () => {
        if (busy || !window.confirm('次の問題を削除しますか？\n\n' + question.text)) return;
        setBusy(true);
        try { await api('/api/admin/questions/' + question.id, {method: 'DELETE'}); editor.hidden = true; notify('問題を削除しました。'); }
        catch (error) { notify(error.message, true); }
        finally { setBusy(false); await load(); }
      });
      actions.append(edit, remove);
      row.append(actions);
      list.append(row);
    });
    add.disabled = data.questions.length >= data.max_questions || busy;
  } catch (error) { notify(error.message || '一覧の取得に失敗しました。', true); add.disabled = true; }
  finally { list.setAttribute('aria-busy', 'false'); }
}
function openEditor(question = null) {
  if (busy) return;
  editingId = question ? question.id : null;
  form.reset();
  document.querySelector('#editor-title').textContent = question ? '問題を編集' : '問題を追加';
  for (const field of ['text', 'explanation']) document.querySelector('#' + field).value = question ? question[field] : '';
  for (let index = 0; index < 4; index += 1) document.querySelector('#choice-' + index).value = question ? question.choices[index] : '';
  document.querySelector('#correct').value = question ? question.correct : 0;
  editor.hidden = false;
  document.querySelector('#text').focus();
}
add.addEventListener('click', () => openEditor());
document.querySelector('#cancel').addEventListener('click', () => { editor.hidden = true; add.focus(); });
document.querySelector('#reload').addEventListener('click', load);
form.addEventListener('submit', async event => {
  event.preventDefault();
  if (busy) return;
  const fields = [...form.querySelectorAll('input,textarea')];
  fields.forEach(item => item.setCustomValidity(item.value.trim() ? '' : '空白のみの入力はできません。'));
  if (!form.reportValidity()) return;
  const data = {
    text: document.querySelector('#text').value.trim(),
    choices: [0, 1, 2, 3].map(index => document.querySelector('#choice-' + index).value.trim()),
    correct: Number(document.querySelector('#correct').value),
    explanation: document.querySelector('#explanation').value.trim()
  };
  setBusy(true);
  try {
    await api('/api/admin/questions' + (editingId === null ? '' : '/' + editingId), {
      method: editingId === null ? 'POST' : 'PUT',
      headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data)
    });
    editor.hidden = true;
    notify(editingId === null ? '問題を追加しました。' : '問題を更新しました。');
  } catch (error) { notify(error.message || '保存に失敗しました。', true); }
  finally { setBusy(false); await load(); }
});
form.addEventListener('input', event => { if (event.target.setCustomValidity) event.target.setCustomValidity(''); });
load();
