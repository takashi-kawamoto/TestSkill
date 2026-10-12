const setup = document.querySelector('#setup');
const quiz = document.querySelector('#quiz');
const result = document.querySelector('#result');
const error = document.querySelector('#error');
const content = document.querySelector('#content');
let questions = [], answers = [], current = 0;

function showError() {
  error.textContent = '通信に失敗しました。接続を確認して、もう一度お試しください。';
  error.hidden = false;
}
async function request(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) throw new Error('Request failed');
  return response.json();
}
function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}
document.querySelector('#start').addEventListener('click', async (event) => {
  const button = event.currentTarget;
  button.disabled = true;
  error.hidden = true;
  content.setAttribute('aria-busy', 'true');
  try {
    const data = await request('/api/questions?count=' + document.querySelector('#count').value);
    questions = data.questions;
    answers = []; current = 0;
    setup.hidden = true; result.hidden = true; quiz.hidden = false;
    renderQuestion();
  } catch { showError(); }
  finally { button.disabled = false; content.setAttribute('aria-busy', 'false'); }
});
function renderQuestion() {
  quiz.replaceChildren();
  const q = questions[current];
  const progress = element('div', 'QUESTION ' + (current + 1) + ' / ' + questions.length, 'progress');
  const bar = element('div', undefined, 'bar');
  const fill = element('span'); fill.style.width = ((current + 1) / questions.length * 100) + '%';
  bar.append(fill);
  const title = element('h2', q.text);
  title.tabIndex = -1;
  const choices = element('div', undefined, 'choices');
  choices.setAttribute('role', 'group'); choices.setAttribute('aria-label', '回答の選択肢');
  const next = element('button', current === questions.length - 1 ? '結果を見る →' : '次の問題へ →', 'primary');
  next.disabled = answers[current] === undefined;
  q.choices.forEach((text, index) => {
    const button = element('button', undefined, 'choice');
    button.append(element('b', String.fromCharCode(65 + index)), document.createTextNode(text));
    button.setAttribute('aria-pressed', String(answers[current] === index));
    if (answers[current] === index) button.classList.add('selected');
    button.addEventListener('click', () => {
      answers[current] = index;
      choices.querySelectorAll('button').forEach((item, i) => {
        item.classList.toggle('selected', i === index);
        item.setAttribute('aria-pressed', String(i === index));
      });
      next.disabled = false;
    });
    choices.append(button);
  });
  next.addEventListener('click', async () => {
    error.hidden = true;
    if (current < questions.length - 1) { current++; renderQuestion(); return; }
    next.disabled = true; content.setAttribute('aria-busy', 'true');
    try {
      const data = await request('/api/submit', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({answers: questions.map((item, index) => ({question_id: item.id, choice: answers[index]}))})
      });
      renderResult(data);
    } catch { showError(); next.disabled = false; }
    finally { content.setAttribute('aria-busy', 'false'); }
  });
  quiz.append(progress, bar, title, choices, next);
  title.focus();
}
function renderResult(data) {
  quiz.hidden = true; result.hidden = false; result.replaceChildren();
  const title = element('h2', 'チャレンジ完了！'); title.tabIndex = -1;
  const score = element('div', String(data.score), 'score');
  score.append(element('small', ' / ' + data.total + ' 問正解'));
  result.append(element('span', 'YOUR RESULT', 'tag'), title, score,
    element('p', data.score === data.total ? '全問正解、お見事です！' : 'おつかれさまでした。解説で新しい発見を。'));
  data.results.forEach((item, index) => {
    const review = element('div', undefined, 'review');
    review.append(element('strong', (index + 1) + '. ' + item.text),
      element('span', item.is_correct ? '✓ 正解' : '✕ 不正解', item.is_correct ? 'status' : 'status wrong'),
      element('p', 'あなたの回答：' + item.selected_answer),
      element('p', '正解：' + item.correct_answer),
      element('p', item.explanation));
    result.append(review);
  });
  const retry = element('button', 'もう一度チャレンジ →', 'primary');
  retry.addEventListener('click', () => {
    result.hidden = true; setup.hidden = false; error.hidden = true;
    document.querySelector('#start').focus();
  });
  result.append(retry); title.focus();
}
