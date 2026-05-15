// AGU Loop v0.3 — no deps. State is stored in localStorage.
// Focus: Retention Gravity + Signal Amplification + Habit Transition + Operator Leverage (Sprint 21)

const LS_KEY = 'agu_loop_v0';
const STATE_VERSION = 3;

function nowISO(){ return new Date().toISOString(); }
function nowMs(){ return Date.now(); }

function loadStateRaw(){
  try {
    const raw = localStorage.getItem(LS_KEY);
    if(!raw) return null;
    return JSON.parse(raw);
  } catch { return null; }
}

function saveState(s){
  localStorage.setItem(LS_KEY, JSON.stringify(s));
}

function defaultState(){
  return {
    state_version: STATE_VERSION,
    created_at: nowISO(),

    user: { name: '', acquisition_source: 'unknown' },
    stage: 'Explorer',

    // Minimal progress engine (5-step ladder). Not a dashboard.
    progress: {
      total_steps: 5,
      current_step: 1,
      last_completed_step: 0,
      last_session_step: 0,
      last_active_at: null,
      next_step_prepared: false,
      has_pending_next_step: false,
      intent_continue_later: false,
    },

    stats: {
      sessions: 0,
      actions_done: 0,
      competence_points: 0,
      last_seen_at: null,
      last_action_at: null,
    },

    continuity: {
      last_screen: 'entry',
      last_prompt: null,
      next_suggestion: 'Continue your next step',
    },

    memory_shelf: {
      moments: [],
    },

    identity: {
      sessions_completed: 0,
      improvement_trend: 'flat',
    },

    // Operator leverage: local event log (so the app can auto-summarize without you)
    analytics: {
      session_id: null,
      session_start_ms: null,
      first_success_ms: null, // time-to-first-success for the first successful completion
      events: [],             // capped list
    },
  };
}

function migrateState(s){
  if(!s) return defaultState();

  // v1/v2 → v3: introduce analytics block
  if(!s.state_version){
    const next = defaultState();
    next.created_at = s.created_at || next.created_at;
    next.user = s.user || next.user;
    next.stage = s.stage || next.stage;
    next.stats = s.stats || next.stats;
    next.continuity = s.continuity || next.continuity;
    next.memory_shelf = s.memory_shelf || next.memory_shelf;

    const inferredStep = Math.min(1 + Math.floor((next.stats.actions_done || 0) / 1), next.progress.total_steps);
    next.progress.current_step = inferredStep;
    next.progress.last_completed_step = Math.max(0, inferredStep - 1);

    next.state_version = STATE_VERSION;
    return next;
  }

  // future migrations
  if(s.state_version !== STATE_VERSION){
    s.state_version = STATE_VERSION;
  }

  // guards
  s.progress ||= defaultState().progress;
  s.identity ||= defaultState().identity;
  s.memory_shelf ||= { moments: [] };
  s.continuity ||= defaultState().continuity;
  s.stats ||= defaultState().stats;
  s.analytics ||= defaultState().analytics;

  return s;
}

function newSessionId(){
  return (crypto.randomUUID?.() || String(Math.random()).slice(2));
}

function logEvent(state, type, data = {}){
  const e = {
    id: (crypto.randomUUID?.() || String(Math.random()).slice(2)),
    at: nowISO(),
    session_id: state.analytics.session_id,
    type,
    data,
  };
  state.analytics.events.unshift(e);
  state.analytics.events = state.analytics.events.slice(0, 500);
}

function ensureState(){
  let s = migrateState(loadStateRaw());

  // session bump
  s.stats.sessions = (s.stats.sessions || 0) + 1;
  s.stats.last_seen_at = nowISO();

  // start a new analytics session each page load
  s.analytics.session_id = newSessionId();
  s.analytics.session_start_ms = nowMs();

  // since-last-time baseline
  s.progress.last_session_step = s.progress.last_session_step || 0;
  s.progress.last_active_at = nowISO();

  logEvent(s, 'app_open', {
    last_screen: s.continuity.last_screen,
    last_completed_step: s.progress.last_completed_step,
  });

  saveState(s);
  return s;
}

function el(html){
  const d = document.createElement('div');
  d.innerHTML = html.trim();
  return d.firstChild;
}

function setStageLabel(stage){
  document.getElementById('stageLabel').textContent = stage;
}

function escapeHtml(s){
  return String(s||'')
    .replaceAll('&','&amp;')
    .replaceAll('<','&lt;')
    .replaceAll('>','&gt;')
    .replaceAll('"','&quot;')
    .replaceAll("'",'&#39;');
}

function minutesSince(iso){
  if(!iso) return null;
  const ms = Date.now() - new Date(iso).getTime();
  return Math.floor(ms / 60000);
}

function pushMoment(state, {type, title, reflection}){
  state.memory_shelf.moments.unshift({
    id: (crypto.randomUUID?.() || String(Math.random()).slice(2)),
    at: nowISO(),
    type,
    title,
    reflection,
  });
  state.memory_shelf.moments = state.memory_shelf.moments.slice(0, 12);
}

function computeReturnGreeting(state){
  const mins = minutesSince(state.stats.last_seen_at);
  if(state.stats.sessions <= 1) return 'Welcome. Let’s begin.';
  if(mins === null) return 'Welcome back. Ready to continue?';
  if(mins < 60*24) return 'Good to see you again. Ready to continue?';
  if(mins >= 60*24*3) return 'We saved your progress. Ready to continue?';
  return 'Welcome back. Ready to continue?';
}

function hasProgress(state){
  return (state.progress.last_completed_step || 0) > 0 || (state.stats.actions_done || 0) > 0;
}

function determineNextStep(state){
  const { total_steps, current_step } = state.progress;
  if(current_step < 1) return 1;
  if(current_step > total_steps) return total_steps;
  return current_step;
}

function prepareNextStep(state){
  state.progress.next_step_prepared = true;
  state.progress.has_pending_next_step = true;
  state.continuity.next_suggestion = `Step ${determineNextStep(state)} is ready`;
}

function onCompleteStep(state){
  const prevStep = state.progress.current_step;

  state.progress.last_completed_step = Math.max(state.progress.last_completed_step, prevStep);
  state.progress.current_step = Math.min(state.progress.total_steps, prevStep + 1);

  // identity (minimal)
  state.identity.sessions_completed += 1;
  state.identity.improvement_trend = (state.progress.current_step > prevStep) ? 'up' : 'flat';

  // open loop + gravity
  prepareNextStep(state);

  // competence evidence
  state.stats.actions_done += 1;
  state.stats.competence_points += 10;
  state.stats.last_action_at = nowISO();

  // analytics: time-to-first-success (first-ever completion)
  if(state.stats.actions_done === 1){
    const t = nowMs() - (state.analytics.session_start_ms || nowMs());
    state.analytics.first_success_ms = t;
    logEvent(state, 'first_success', { ms: t });
  }

  logEvent(state, 'step_complete', {
    completed_step: prevStep,
    next_step: state.progress.current_step,
  });

  // signature moments (scarce)
  if(state.stats.sessions >= 2 && !state._first_recognition_done){
    pushMoment(state, {
      type: 'recognition',
      title: 'First recognition',
      reflection: `I came back, and it remembered me${state.user.name ? ' ('+state.user.name+')' : ''}.`,
    });
    state._first_recognition_done = true;
  }

  if(!state._first_real_win_done){
    pushMoment(state, {
      type: 'first_win',
      title: 'First challenge win',
      reflection: 'I finished a real step and proved I can follow a plan.'
    });
    state._first_real_win_done = true;
  }
}

function eventsSince(state, days){
  const cutoff = Date.now() - days*24*60*60*1000;
  return (state.analytics.events || []).filter(e => new Date(e.at).getTime() >= cutoff);
}

function computeWeeklySummary(state){
  const ev = eventsSince(state, 7);

  const counts = new Map();
  for(const e of ev){
    counts.set(e.type, (counts.get(e.type) || 0) + 1);
  }

  const firstSuccess = ev.find(e => e.type === 'first_success');
  const ttf = firstSuccess?.data?.ms ?? state.analytics.first_success_ms;

  const stepCompletes = counts.get('step_complete') || 0;
  const appOpens = counts.get('app_open') || 0;

  // Return proxy: multiple open-days inside the window.
  const uniqueDays = new Set(ev.filter(e => e.type === 'app_open').map(e => new Date(e.at).toDateString())).size;
  const returnTrend = uniqueDays >= 2 ? 'returning' : 'new/low';

  // “top hesitation point” (v0): most frequent non-core event
  const hesitationCandidates = [...counts.entries()]
    .filter(([type]) => !['app_open','step_complete','first_success','cmd_pick'].includes(type))
    .sort((a,b) => b[1]-a[1]);
  const topHesitation = hesitationCandidates[0]?.[0] || 'none';

  // Acquisition source distribution (v0): from start/resume clicks
  const sourceCounts = { unknown: 0, founder_push: 0, friend_invite: 0, organic: 0 };
  for(const e of ev){
    if(e.type === 'start_click' || e.type === 'quick_resume_click'){
      const src = e.data?.source || 'unknown';
      if(sourceCounts[src] === undefined) sourceCounts.unknown += 1;
      else sourceCounts[src] += 1;
    }
  }

  const inviteCopiesOk = ev.filter(e => e.type === 'invite_copy' && e.data?.ok === true).length;

  return {
    week_window_days: 7,
    app_opens: appOpens,
    step_completes: stepCompletes,
    unique_open_days: uniqueDays,
    return_trend: returnTrend,
    time_to_first_success_ms: ttf ?? null,
    top_hesitation_point: topHesitation,
    acquisition_sources: sourceCounts,
    invite_copies_ok: inviteCopiesOk,
  };
}

function renderEntry(state){
  state.continuity.last_screen = 'entry';
  saveState(state);

  const screen = document.getElementById('screen');

  const returning = hasProgress(state);
  const greeting = computeReturnGreeting(state);

  const prev = state.progress.last_session_step || 0;
  const cur = state.progress.last_completed_step || 0;
  const delta = Math.max(0, cur - prev);

  const anchor = state.progress.next_step_prepared
    ? `Your next step is already prepared.`
    : `Your next step will be ready as soon as you start.`;

  screen.replaceChildren(el(`
    <div>
      <div class="badge">Home • One obvious next action</div>
      <h1 class="h1">${escapeHtml(greeting)}</h1>
      <p class="p">${escapeHtml(anchor)}</p>

      <label class="p" style="margin-bottom:6px">Name (for continuity)</label>
      <input id="name" class="input" placeholder="e.g., Jane" value="${escapeHtml(state.user.name||'')}" />

      <label class="p" style="margin:12px 0 6px">How did you get here?</label>
      <select id="source" class="input">
        ${['unknown','founder_push','friend_invite','organic'].map(v => `<option value="${v}" ${state.user.acquisition_source===v?'selected':''}>${v.replaceAll('_',' ')}</option>`).join('')}
      </select>

      <div class="row" style="margin-top:12px">
        <button id="continue" class="btn primary">${returning ? 'Quick Resume' : 'Start'}</button>
        <button id="reset" class="btn warn">Reset</button>
      </div>

      ${returning ? `
        <hr />
        <div class="badge">Since last time: ${delta > 0 ? `+${delta} step${delta===1?'':'s'}` : 'progress saved'} • Next step ready</div>
      ` : ''}

      <hr />
      <div class="kpi">
        <div class="box"><div class="n">${state.progress.last_completed_step}</div><div class="l">step reached</div></div>
        <div class="box"><div class="n">${state.stats.competence_points}</div><div class="l">growth points</div></div>
        <div class="box"><div class="n">${state.stats.sessions}</div><div class="l">visits</div></div>
      </div>
    </div>
  `));

  screen.querySelector('#continue').onclick = () => {
    state.user.name = screen.querySelector('#name').value.trim();
    state.user.acquisition_source = screen.querySelector('#source').value;
    state.progress.intent_continue_later = false;
    logEvent(state, returning ? 'quick_resume_click' : 'start_click', { source: state.user.acquisition_source });
    saveState(state);

    // Habit transition: default resume behavior
    renderAction(state, { autoResume: returning });
  };

  screen.querySelector('#reset').onclick = () => {
    logEvent(state, 'reset');
    localStorage.removeItem(LS_KEY);
    location.reload();
  };

  // baseline for next "since last time"
  state.progress.last_session_step = state.progress.last_completed_step;
  saveState(state);
}

function renderAction(state, {autoResume} = {autoResume:false}){
  state.continuity.last_screen = 'action';
  state.continuity.last_prompt = 'robot_path';
  state.progress.last_active_at = nowISO();
  saveState(state);

  const name = state.user.name || 'Explorer';
  const step = determineNextStep(state);

  logEvent(state, 'action_view', { step, autoResume });

  const screen = document.getElementById('screen');
  screen.replaceChildren(el(`
    <div>
      <div class="badge">Action • Step ${step} / ${state.progress.total_steps}</div>
      <h1 class="h1">Quick Mission</h1>
      <p class="p">${autoResume ? 'Picking up exactly where you left off.' : 'Choose 3 commands.'}</p>

      <div class="row">
        <button class="btn cmd">Forward</button>
        <button class="btn cmd">Left</button>
        <button class="btn cmd">Right</button>
      </div>

      <p class="p" style="margin-top:12px">Your sequence:</p>
      <input id="seq" class="input" placeholder="e.g., Forward, Right, Forward" readonly />

      <div class="row" style="margin-top:12px">
        <button id="submit" class="btn ok" disabled>Complete Step</button>
        <button id="home" class="btn">Home</button>
      </div>

      <hr />
      <p class="p"><strong>${escapeHtml(name)}</strong>, small steps. Clean execution.</p>
    </div>
  `));

  const seq = [];
  const seqEl = screen.querySelector('#seq');
  const submit = screen.querySelector('#submit');

  screen.querySelectorAll('.cmd').forEach(b => {
    b.onclick = () => {
      if(seq.length >= 3) return;
      seq.push(b.textContent);
      seqEl.value = seq.join(', ');
      logEvent(state, 'cmd_pick', { step, cmd: b.textContent, n: seq.length });
      if(seq.length === 3) submit.disabled = false;
    };
  });

  submit.onclick = () => {
    onCompleteStep(state);
    saveState(state);
    renderFeedback(state, seq);
  };

  screen.querySelector('#home').onclick = () => {
    logEvent(state, 'home_from_action', { step });
    renderEntry(state);
  };
}

function renderFeedback(state, seq){
  state.continuity.last_screen = 'feedback';
  saveState(state);

  const stepCompleted = state.progress.last_completed_step;
  const nextStep = determineNextStep(state);

  const screen = document.getElementById('screen');
  screen.replaceChildren(el(`
    <div>
      <div class="badge">Feedback • Progress saved</div>
      <h1 class="h1">Nice.</h1>
      <p class="p">Progress saved. Next step unlocked.</p>

      <div class="badge">Sequence: ${escapeHtml((seq||[]).join(' → ') || '—')}</div>

      <hr />
      <div class="badge">Open loop: You’re ready for Step ${nextStep}.</div>

      <div class="row" style="margin-top:12px">
        <button id="continueNow" class="btn primary">Continue now</button>
        <button id="continueLater" class="btn">Continue later</button>
      </div>

      <div class="row" style="margin-top:10px">
        <button id="progress" class="btn">View Progress</button>
      </div>

      <p class="p" style="margin-top:12px">Step ${stepCompleted} complete. Keep the momentum.</p>

      <hr />
      <div class="badge">Optional</div>
      <p class="p">If someone you care about would benefit, invite them.</p>
      <div class="row">
        <button id="invite" class="btn">Copy invite text</button>
      </div>
    </div>
  `));

  screen.querySelector('#continueNow').onclick = () => {
    state.progress.intent_continue_later = false;
    logEvent(state, 'continue_now', { from: 'feedback', stepCompleted });
    saveState(state);
    renderAction(state, { autoResume: true });
  };

  screen.querySelector('#continueLater').onclick = () => {
    state.progress.intent_continue_later = true;
    logEvent(state, 'continue_later', { from: 'feedback', stepCompleted });
    saveState(state);
    renderProgress(state);
  };

  screen.querySelector('#progress').onclick = () => {
    logEvent(state, 'view_progress', { from: 'feedback' });
    renderProgress(state);
  };

  screen.querySelector('#invite').onclick = async () => {
    const text = 'Try this: it helps you keep moving without thinking. Open: http://localhost:5173';
    try {
      await navigator.clipboard.writeText(text);
      logEvent(state, 'invite_copy', { ok: true });
      pushMoment(state, { type:'growth', title:'Shared the loop', reflection:'I invited someone into my progress.' });
      saveState(state);
      alert('Invite text copied.');
    } catch {
      logEvent(state, 'invite_copy', { ok: false });
      alert(text);
    }
  };
}

function renderWeeklyReport(state){
  state.continuity.last_screen = 'weekly_report';
  saveState(state);

  const s = computeWeeklySummary(state);

  const screen = document.getElementById('screen');
  screen.replaceChildren(el(`
    <div>
      <div class="badge">Operator Report • last ${s.week_window_days} days</div>
      <h1 class="h1">Weekly Summary</h1>
      <p class="p">This is the auto-review you should see without digging.</p>

      <div class="kpi">
        <div class="box"><div class="n">${s.step_completes}</div><div class="l">step completes</div></div>
        <div class="box"><div class="n">${s.unique_open_days}</div><div class="l">active days</div></div>
        <div class="box"><div class="n">${s.time_to_first_success_ms === null ? '—' : Math.round(s.time_to_first_success_ms/1000)+'s'}</div><div class="l">time to first success</div></div>
      </div>

      <hr />
      <div class="badge">Top hesitation point (v0): ${escapeHtml(s.top_hesitation_point)}</div>
      <div class="badge" style="margin-top:8px">Return trend (v0): ${escapeHtml(s.return_trend)}</div>

      <hr />
      <div class="badge">Acquisition sources (v0):</div>
      <div class="p" style="margin-top:8px">
        unknown: <strong>${s.acquisition_sources.unknown}</strong> · founder push: <strong>${s.acquisition_sources.founder_push}</strong> · friend invite: <strong>${s.acquisition_sources.friend_invite}</strong> · organic: <strong>${s.acquisition_sources.organic}</strong>
      </div>
      <div class="badge" style="margin-top:8px">Invite copies (ok): ${s.invite_copies_ok}</div>

      <hr />
      <p class="p">Rule: ship <strong>one</strong> improvement from backlog A next.</p>

      <div class="row" style="margin-top:12px">
        <button id="back" class="btn primary">Back to Progress</button>
        <button id="home" class="btn">Home</button>
      </div>
    </div>
  `));

  screen.querySelector('#back').onclick = () => renderProgress(state);
  screen.querySelector('#home').onclick = () => renderEntry(state);
}

function renderProgress(state){
  state.continuity.last_screen = 'progress';
  saveState(state);

  const name = state.user.name || 'Explorer';
  const nextStep = determineNextStep(state);
  const moments = state.memory_shelf.moments;

  const screen = document.getElementById('screen');
  screen.replaceChildren(el(`
    <div>
      <div class="badge">Progress Memory • Belonging</div>
      <h1 class="h1">Your Progress</h1>
      <p class="p">We remember where you left off. Step ${nextStep} is ready.</p>

      <div class="kpi">
        <div class="box"><div class="n">${state.progress.last_completed_step}</div><div class="l">step reached</div></div>
        <div class="box"><div class="n">${state.stats.competence_points}</div><div class="l">growth points</div></div>
        <div class="box"><div class="n">${state.stats.sessions}</div><div class="l">visits</div></div>
      </div>

      <hr />
      <div class="badge">Next step prepared: ${state.progress.next_step_prepared ? 'yes' : 'no'}</div>

      <div class="row" style="margin-top:12px">
        <button id="quickResume" class="btn primary">Quick Resume</button>
        <button id="weekly" class="btn">Weekly Summary</button>
        <button id="home" class="btn">Home</button>
      </div>

      <h2 class="h1" style="font-size:16px;margin-top:14px">Memory Shelf (v0)</h2>
      <div id="moments"></div>

      <p class="p" style="margin-top:10px">${escapeHtml(name)}, you’re building a story of becoming.</p>
    </div>
  `));

  const list = screen.querySelector('#moments');
  if(!moments.length){
    list.appendChild(el(`<p class="p">No moments yet. Complete a step to create one.</p>`));
  } else {
    moments.slice(0, 6).forEach(m => {
      list.appendChild(el(`
        <div class="box" style="margin-bottom:8px">
          <div class="badge">${escapeHtml(m.title)}</div>
          <div class="p" style="margin-top:6px">${escapeHtml(m.reflection)}</div>
          <div class="muted" style="font-size:12px;margin-top:6px">${escapeHtml(new Date(m.at).toLocaleString())}</div>
        </div>
      `));
    });
  }

  screen.querySelector('#quickResume').onclick = () => {
    logEvent(state, 'quick_resume_click', { from: 'progress' });
    renderAction(state, { autoResume: true });
  };
  screen.querySelector('#weekly').onclick = () => {
    logEvent(state, 'weekly_report_open');
    renderWeeklyReport(state);
  };
  screen.querySelector('#home').onclick = () => renderEntry(state);
}

// boot
const state = ensureState();
setStageLabel(state.stage);

// Habit transition: if user has intent to continue later, show entry with anchor.
// Otherwise resume last screen (continuity).
const resume = state.continuity.last_screen;
if(state.progress.intent_continue_later){
  renderEntry(state);
} else {
  switch(resume){
    case 'action': renderAction(state, { autoResume: true }); break;
    case 'feedback': renderFeedback(state, []); break;
    case 'progress': renderProgress(state); break;
    default: renderEntry(state);
  }
}
