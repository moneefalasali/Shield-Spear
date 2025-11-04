// Client-side coop play logic
// Parses server-provided context from #coop-context, connects to Socket.IO, handles UI and events
(function(){
    const raw = document.getElementById('coop-context');
    const CONTEXT = raw ? JSON.parse(raw.textContent || '{}') : {};
    const sessionCode = CONTEXT.session_code;
    const isCreator = CONTEXT.is_creator;
    const currentUserId = String(CONTEXT.current_user_id || '');

    // helper DOM references
    const eventsContainer = document.getElementById('events');
    const readyBtn = document.getElementById('readyBtn');
    const leaveBtn = document.getElementById('leaveBtn');

    // Adds a message to the live event log. Debug messages are routed to console only to
    // avoid cluttering the UI with internal developer logs.
    function addEvent(message, actor='System'){
        if(actor === 'Debug'){
            // keep debug output in browser console only
            try{ console.debug('[coop-debug]', message); }catch(e){}
            return;
        }
        if(!eventsContainer) return;
        const div = document.createElement('div');
        div.className = 'event-item';
        div.innerHTML = `<strong>${actor}:</strong> ${message}`;
        eventsContainer.appendChild(div);
        eventsContainer.scrollTop = eventsContainer.scrollHeight;
    }

    // inject a simple action panel if not present
    function injectActionPanel(){
        const panel = document.createElement('div');
        panel.id = 'actionPanel';
        panel.style.marginTop = '1rem';
        panel.style.display = 'flex';
        panel.style.gap = '0.5rem';

        const actions = [
            {k:'probe', t:'Probe'},
            {k:'exploit', t:'Exploit'},
            {k:'sanitize', t:'Sanitize'},
            {k:'monitor', t:'Monitor'},
            {k:'report', t:'Report'}
        ];

        actions.forEach(a=>{
            const btn = document.createElement('button');
            btn.className = 'btn btn-small';
            btn.textContent = a.t;
            btn.addEventListener('click', ()=>{
                doAction(a.k);
            });
            panel.appendChild(btn);
        });

        // append after the event-log
        const container = document.querySelector('.gradient-card');
        if(container) container.appendChild(panel);
    }

    // currently selected target id for attacks
    let currentTargetId = null;

    // set target when clicking on a participant card
    function setTargetFor(uid){
        currentTargetId = uid;
        // highlight selected
        document.querySelectorAll('#participantsPanel .player-card').forEach(el=>{
            if(el.dataset.userId === String(uid)) el.style.boxShadow = '0 12px 36px rgba(124,58,237,0.28), 0 0 0 3px rgba(124,58,237,0.08)';
            else el.style.boxShadow = '0 8px 30px rgba(5,5,10,0.45)';
        });
    }

    // lightweight audio engine using WebAudio; safe no-op when not supported or muted
    const audioEngine = (function(){
        let ctx = null;
        let muted = false;
        function ensure(){ if(!ctx && !muted){ try{ ctx = new (window.AudioContext || window.webkitAudioContext)(); }catch(e){ ctx = null; } } }
        function tone(freq, time=0.08, type='sine', gain=0.08){ if(muted) return; ensure(); if(!ctx) return; const o = ctx.createOscillator(); const g = ctx.createGain(); o.type = type; o.frequency.value = freq; g.gain.value = gain; o.connect(g); g.connect(ctx.destination); o.start(); o.stop(ctx.currentTime + time); }
        return {
            playAction: ()=> tone(600,0.06,'sine',0.02),
            playSuccess: ()=> { tone(900,0.12,'sine',0.03); tone(1300,0.06,'triangle',0.02); },
            playFail: ()=> tone(220,0.12,'square',0.04),
            mute: (m)=>{ muted = !!m; if(!muted) ensure(); }
        };
    })();

    function doAction(actionType){
        if(!socket || !sessionCode) return;
        // create an action toast with progress
        const panel = document.getElementById('actionPanel');
        if(!panel) return;

        // disable buttons until result
        Array.from(panel.querySelectorAll('button')).forEach(b=>b.disabled = true);

        const toast = document.createElement('div');
        toast.className = 'action-toast';
        toast.innerHTML = `<div><strong>You</strong> → ${actionType}</div><div class="action-progress"><span></span></div>`;
        panel.appendChild(toast);
        // animate progress
        const bar = toast.querySelector('.action-progress > span');
        setTimeout(()=> bar.style.width = '100%', 30);

        // emit action to server (send action type as payload so server can interpret)
    const targetPart = currentTargetId ? String(currentTargetId) : '';
    const payload = `${actionType}|${currentUserId}|${targetPart}|${new Date().toISOString()}`;
        socket.emit('play_action', { session_code: sessionCode, action: payload });
        addEvent(`Attempting: ${actionType}`, 'You');
    // play a short action sound
    try{ audioEngine.playAction(); }catch(e){}

        // safety timeout: if no server response in 4s, mark as failed
        const timeout = setTimeout(()=>{
            toast.classList.add('pulse-fail');
            toast.querySelector('.action-progress > span').style.width = '100%';
            addEvent(`${actionType} timed out`, 'System');
            // re-enable buttons
            Array.from(panel.querySelectorAll('button')).forEach(b=>b.disabled = false);
        }, 4000);

        // attach a marker so we can correlate result when server sends it
    toast.dataset.actionType = actionType;
    // store timeout id as a property (dataset coerces to string)
    toast._actionTimeout = timeout;
    }

    // Ensure any existing buttons inside #actionPanel are wired to call doAction
    function ensureActionButtons(){
        const panel = document.getElementById('actionPanel');
        if(!panel) return;
        const buttons = Array.from(panel.querySelectorAll('button'));
        buttons.forEach(btn=>{
            try{
                if(btn.dataset && btn.dataset.wired === '1') return;
                // Determine action key: prefer data-action, fallback to button text
                let actionKey = (btn.dataset && btn.dataset.action) ? btn.dataset.action : (btn.textContent || '').trim().toLowerCase();
                // normalize common labels
                actionKey = actionKey.split(/\s+/)[0];
                const valid = ['probe','exploit','sanitize','monitor','report'];
                if(!valid.includes(actionKey)) return;
                btn.addEventListener('click', (ev)=>{ ev.preventDefault(); doAction(actionKey); });
                // ensure there is a cooldown span placeholder
                if(!btn.querySelector('.btn-cd')){
                    const cd = document.createElement('span'); cd.className = 'btn-cd'; cd.style.marginLeft = '6px'; cd.style.opacity = 0.9; cd.style.fontSize = '0.8rem'; btn.appendChild(cd);
                }
                btn.dataset.wired = '1';
            }catch(e){/*ignore*/}
        });
    }

    // Periodically update button disabled state and cooldown labels from window.coop_cooldowns
    function updateActionButtonsState(){
        const panel = document.getElementById('actionPanel');
        if(!panel) return;
        const nowSec = Date.now()/1000;
        const cooldowns = window.coop_cooldowns || {};
        const buttons = Array.from(panel.querySelectorAll('button'));
        buttons.forEach(btn=>{
            const action = (btn.dataset && btn.dataset.action) ? btn.dataset.action : (btn.textContent||'').trim().split(/\s+/)[0].toLowerCase();
            const cdTs = cooldowns[action] || null;
            if(cdTs && Number(cdTs) > nowSec){
                const rem = Math.ceil(Number(cdTs) - nowSec);
                btn.disabled = true;
                const cdSpan = btn.querySelector('.btn-cd'); if(cdSpan) cdSpan.textContent = `CD ${rem}s`;
            } else {
                if(!panel.querySelector('.action-toast')) btn.disabled = false; // only enable if no active toast
                const cdSpan = btn.querySelector('.btn-cd'); if(cdSpan) cdSpan.textContent = '';
            }
        });
    }

    // keyboard shortcuts for quick actions (1-5)
    (function(){
        const keyMap = { 'Digit1':'probe','Digit2':'exploit','Digit3':'sanitize','Digit4':'monitor','Digit5':'report' };
        window.addEventListener('keydown', (e)=>{
            if(document.activeElement && (document.activeElement.tagName === 'INPUT' || document.activeElement.tagName === 'TEXTAREA' || document.activeElement.isContentEditable)) return;
            const action = keyMap[e.code];
            if(action){ e.preventDefault(); try{ doAction(action); }catch(ex){} }
        });
    })();

    // start periodic updater
    setInterval(()=>{ try{ ensureActionButtons(); updateActionButtonsState(); }catch(e){} }, 600);

    // Typed action input handling
    (function(){
        const input = document.getElementById('actionInput');
        const sendBtn = document.getElementById('sendActionBtn');
        const clearBtn = document.getElementById('clearActionBtn');
        if(!input || !sendBtn) return;

        function parseAndSend(raw){
            const text = (raw || '').trim();
            if(!text) return;
            // parse first token as action if matches known actions
            const m = text.match(/^([a-zA-Z]+)\s+(.*)$/s);
            let actionKey = 'exploit';
            let body = text;
            if(m){
                const candidate = m[1].toLowerCase();
                if(['probe','exploit','sanitize','monitor','report'].includes(candidate)){
                    actionKey = candidate;
                    body = m[2] || '';
                }
            }
            // build payload similar to doAction but include body as extra
            const targetPart = currentTargetId ? String(currentTargetId) : '';
            const payload = `${actionKey}|${currentUserId}|${targetPart}|${new Date().toISOString()}|${body}`;
            // show a toast and disable buttons while awaiting response
            try{
                const panel = document.getElementById('actionPanel');
                if(panel){
                    Array.from(panel.querySelectorAll('button')).forEach(b=>b.disabled = true);
                    const toast = document.createElement('div'); toast.className = 'action-toast';
                    toast.innerHTML = `<div><strong>You</strong> → ${actionKey}</div><div class="action-progress"><span></span></div>`;
                    panel.appendChild(toast);
                    const bar = toast.querySelector('.action-progress > span'); setTimeout(()=> bar.style.width='100%',30);
                    toast.dataset.actionType = actionKey;
                    toast._actionTimeout = setTimeout(()=>{ toast.classList.add('pulse-fail'); Array.from(panel.querySelectorAll('button')).forEach(b=>b.disabled=false); addEvent(`${actionKey} timed out`, 'System'); }, 4000);
                }
            }catch(e){}
            try{ socket.emit('play_action', { session_code: sessionCode, action: payload }); addEvent(`Attempting: ${actionKey}`, 'You'); audioEngine.playAction(); }catch(e){}
        }

        sendBtn.addEventListener('click', ()=>{ parseAndSend(input.value); });
        clearBtn.addEventListener('click', ()=>{ input.value = ''; input.focus(); });

        // Ctrl+Enter to submit
        input.addEventListener('keydown', (e)=>{
            if((e.ctrlKey || e.metaKey) && e.key === 'Enter'){
                e.preventDefault(); parseAndSend(input.value);
            }
        });
    })();

    // connect to socket.io — reuse existing connection if script re-initialized to avoid
    // duplicate sockets and duplicated event handlers when template is re-rendered.
    const socket = (function(){
        try{
            if(window.coopSocket) return window.coopSocket;
        }catch(e){}
        const s = io();
        try{ window.coopSocket = s; }catch(e){}
        return s;
    })();

    // Attach handlers only once per socket instance
    if(!socket._coopHandlersAttached){
        socket._coopHandlersAttached = true;

        socket.on('connect', ()=>{
            addEvent('Connected to server', 'System');
            console.log('[coop] socket connected');
            socket.emit('join_coop_session', { session_code: sessionCode });
        });

    socket.on('connect_response', (d)=>{
        if(d && d.user) addEvent(`Connected as ${d.user}`, 'System');
        console.log('[coop] connect_response', d);
        addEvent(`(debug) connect_response: ${d && d.user ? d.user : JSON.stringify(d)}`, 'Debug');
    });

    socket.on('user_joined', (data)=>{
        const participants = data.participants || [];
        addEvent(`${data.username} joined. Participants: ${participants.join(', ')}`, 'System');
        console.log('[coop] user_joined', data);
        addEvent(`(debug) user_joined: ${data.username} — ${participants.join(', ')}`, 'Debug');
        if(isCreator && participants.length >= 2 && readyBtn){
            readyBtn.textContent = 'Start Session';
            readyBtn.disabled = false;
        }
    });

    socket.on('session_started', (data)=>{
        addEvent('Session started. Preparing challenge...', 'System');
        console.log('[coop] session_started', data);
        // store participant id -> username mapping if provided
        if(data && data.participants){
            window.coop_results_map = Object.assign(window.coop_results_map || {}, data.participants || {});
        }
        try{
            const attempts = data.attempts || {};
            // store attempts map for reference but DO NOT redirect away from coop play page
            window.coop_attempts_map = Object.assign(window.coop_attempts_map || {}, attempts || {});
        }catch(e){ }
    // otherwise, ensure action panel exists and wire buttons
    injectActionPanel();
    try{ ensureActionButtons(); }catch(e){}
        // render participant UI panels for visual effects
        try{
            renderParticipants(window.coop_results_map || {});
            console.log('[coop] rendered participants', window.coop_results_map);
            addEvent(`(debug) participants rendered: ${Object.keys(window.coop_results_map||{}).join(', ')}`, 'Debug');
        }catch(e){/*ignore*/}
    });

    socket.on('action_result', (data)=>{
        const rec = data.record || {};
        const actor = rec.actor_name || rec.actor_id || 'Unknown';
        addEvent(`${rec.feedback || rec.payload} (score ${rec.score})`, actor);
        console.log('[coop] action_result', data);
        addEvent(`(debug) action_result actor=${rec.actor_id} target=${rec.target_id || '-'} score=${rec.score}`, 'Debug');
        // update local results map if server sent results
        if(data.results) window.coop_results_map = Object.assign(window.coop_results_map || {}, data.results || {});
        // authoritative hp and cooldowns if provided
        if(data.hp_map) window.coop_hp_map = Object.assign(window.coop_hp_map || {}, data.hp_map || {});
        if(data.cooldowns) window.coop_cooldowns = Object.assign(window.coop_cooldowns || {}, data.cooldowns || {});
        // update scoreboard if present
        updateScoreboard(data.scores || buildScoresFromResults(window.coop_results_map));

        // update HP map (simple heuristic): ensure every participant starts with 100
        window.coop_hp_map = window.coop_hp_map || {}; 
        if(rec && rec.actor_id){
            const id = String(rec.actor_id);
            if(typeof window.coop_hp_map[id] === 'undefined') window.coop_hp_map[id] = 100;
            // scoring heuristic: failures reduce HP, successes heal a bit
            if(rec.is_correct) window.coop_hp_map[id] = Math.min(100, window.coop_hp_map[id] + (rec.score? Math.min(6, rec.score):3));
            else window.coop_hp_map[id] = Math.max(0, window.coop_hp_map[id] - (rec.score? Math.min(12, Math.abs(rec.score)):10));
        }

        // play sound based on correctness
        try{ if(rec.is_correct) audioEngine.playSuccess(); else audioEngine.playFail(); }catch(e){}

        // Visual feedback: find the latest toast for this actor and animate
        try{
            const panel = document.getElementById('actionPanel');
            if(panel){
                // choose a toast that matches action type or the newest
                const toasts = Array.from(panel.querySelectorAll('.action-toast'));
                let toast = toasts.reverse().find(t=>t.dataset.actionType && (rec.payload || '').includes(t.dataset.actionType));
                if(!toast) toast = toasts.reverse()[0];
                if(toast){
                    // clear timeout if any
                    try{ if(toast._actionTimeout) clearTimeout(toast._actionTimeout); }catch(e){}
                    if(rec.is_correct){
                        toast.classList.add('pulse-success');
                    } else {
                        toast.classList.add('pulse-fail');
                    }
                    // finish progress bar
                    const bar = toast.querySelector('.action-progress > span');
                    if(bar) bar.style.width = '100%';
                    // re-enable buttons
                    Array.from(panel.querySelectorAll('button')).forEach(b=>{ b.disabled = false; });
                }
            }
        }catch(e){/*ignore*/}

        // Trigger visual attack/defend effects on scoreboard entries
        try{
            const actorId = String(rec.actor_id || '');
            const allIds = Object.keys(window.coop_results_map || {});
            const targets = allIds.filter(id=> id !== actorId && id !== undefined && id !== '');
            // helper animators
            function animateAttackOn(targetId, actorId){
                console.log('[coop] animateAttackOn', { targetId, actorId });
                const panel = document.getElementById('participantsPanel') || document.getElementById('scoreBox');
                if(!panel) return;
                const actorEl = panel.querySelector(`.player-card[data-user-id='${actorId}']`);
                const targetEl = panel.querySelector(`.player-card[data-user-id='${targetId}']`);
                if(!actorEl || !targetEl) return;

                const actorRect = actorEl.getBoundingClientRect();
                const targetRect = targetEl.getBoundingClientRect();
                const containerRect = panel.getBoundingClientRect();

                const startX = actorRect.left + actorRect.width/2 - containerRect.left;
                const startY = actorRect.top + actorRect.height/2 - containerRect.top;
                const endX = targetRect.left + targetRect.width/2 - containerRect.left;
                const endY = targetRect.top + targetRect.height/2 - containerRect.top;

                const dx = endX - startX;
                const dy = endY - startY;

                const atk = document.createElement('div');
                atk.className = 'attack-effect';
                // size variant based on distance
                const dist = Math.hypot(dx, dy);
                if(dist > 220) atk.classList.add('large');
                else if(dist < 140) atk.classList.add('small');

                // initial absolute placement
                atk.style.position = 'absolute';
                atk.style.left = startX + 'px';
                atk.style.top = startY + 'px';
                atk.style.transform = 'translate(-50%, -50%)';
                panel.appendChild(atk);

                // measure then adjust origin so animation moves from center
                const w = atk.offsetWidth || 160;
                const h = atk.offsetHeight || 28;
                atk.style.left = (startX - w/2) + 'px';
                atk.style.top = (startY - h/2) + 'px';

                // choose direction class for look-and-feel
                if(dx > 0) atk.classList.add('from-left'); else atk.classList.add('from-right');

                // animate using Web Animations API for smooth travel
                try{
                    const anim = atk.animate([
                        { transform: 'translate(0px, 0px) scaleX(0.9)', opacity: 1 },
                        { transform: `translate(${dx}px, ${dy}px) scaleX(1.05)`, opacity: 0.9 },
                        { transform: `translate(${dx*1.15}px, ${dy*1.15}px) scaleX(1.2)`, opacity: 0 }
                    ], { duration: 520, easing: 'cubic-bezier(.2,.9,.2,1)' });
                    anim.onfinish = ()=> atk.remove();
                }catch(e){
                    // fallback: remove after timeout
                    setTimeout(()=> atk.remove(), 600);
                }
            }
            function animateImpactOn(targetId){
                console.log('[coop] animateImpactOn', targetId);
                const panel = document.getElementById('participantsPanel') || document.getElementById('scoreBox');
                if(!panel) return;
                const entry = panel.querySelector(`.player-card[data-user-id='${targetId}']`) || panel.querySelector(`.score-entry[data-user-id='${targetId}']`);
                if(!entry) return;
                const rect = entry.getBoundingClientRect();
                const containerRect = panel.getBoundingClientRect();
                const cx = rect.left + rect.width/2 - containerRect.left;
                const cy = rect.top + rect.height/2 - containerRect.top;
                for(let i=0;i<4;i++){
                    const spark = document.createElement('div'); spark.className = 'impact-spark';
                    spark.style.position = 'absolute';
                    const rx = cx + (Math.random()*40 - 20);
                    const ry = cy + (Math.random()*24 - 12);
                    spark.style.left = (rx - 6) + 'px'; spark.style.top = (ry - 6) + 'px';
                    panel.appendChild(spark);
                    spark.addEventListener('animationend', ()=> spark.remove());
                }
            }
            function animateDefendOn(targetId){
                console.log('[coop] animateDefendOn', targetId);
                const panel = document.getElementById('participantsPanel') || document.getElementById('scoreBox');
                if(!panel) return;
                const entry = panel.querySelector(`.player-card[data-user-id='${targetId}']`) || panel.querySelector(`.score-entry[data-user-id='${targetId}']`);
                if(!entry) return;
                const rect = entry.getBoundingClientRect();
                const containerRect = panel.getBoundingClientRect();
                const cx = rect.left + rect.width/2 - containerRect.left;
                const cy = rect.top + rect.height/2 - containerRect.top;
                const shield = document.createElement('div'); shield.className = 'defend-effect';
                shield.style.position = 'absolute';
                shield.style.left = (cx - 60) + 'px'; shield.style.top = (cy - 60) + 'px';
                panel.appendChild(shield);
                shield.addEventListener('animationend', ()=> shield.remove());
            }
            function flashHPOn(targetId){
                console.log('[coop] flashHPOn', targetId);
                const panel = document.getElementById('participantsPanel') || document.getElementById('scoreBox');
                if(!panel) return;
                const entry = panel.querySelector(`.player-card[data-user-id='${targetId}']`) || panel.querySelector(`.score-entry[data-user-id='${targetId}']`);
                if(!entry) return;
                const flash = document.createElement('div'); flash.className = 'hp-flash';
                flash.style.position = 'absolute'; flash.style.left = 0; flash.style.top = 0; flash.style.right = 0; flash.style.bottom = 0;
                entry.appendChild(flash);
                flash.addEventListener('animationend', ()=> flash.remove());
            }

            if(rec.is_correct){
                // attack hits targets
                targets.forEach(tid=>{
                    animateAttackOn(tid, actorId);
                    setTimeout(()=> animateImpactOn(tid), 120);
                    setTimeout(()=> flashHPOn(tid), 140);
                });
            } else {
                // failed attack: flash actor and show defend on targets
                flashHPOn(actorId);
                targets.forEach(tid=> animateDefendOn(tid));
            }
        }catch(e){/*ignore*/}
    });

    socket.on('session_update', (data)=>{
        console.log('[coop] session_update', data);
        if(data && data.results) window.coop_results_map = Object.assign(window.coop_results_map || {}, data.results || {});
        if(data && data.hp_map) window.coop_hp_map = Object.assign(window.coop_hp_map || {}, data.hp_map || {});
        if(data && data.cooldowns) window.coop_cooldowns = Object.assign(window.coop_cooldowns || {}, data.cooldowns || {});
        if(data && data.scores) updateScoreboard(data.scores);
        else updateScoreboard(buildScoresFromResults(window.coop_results_map));
        if(data && data.recent){
            const r = data.recent;
            addEvent(`${r.feedback || r.payload} (score ${r.score})`, r.actor_name || r.actor_id);
        }
        // update participant panels (hp etc)
        try{ updateParticipantPanels(window.coop_results_map || {}, window.coop_hp_map || {}, window.coop_cooldowns || {}); }catch(e){}
        // If any player's HP reached zero, show final results overlay once
        try{
            if(!window._coopResultsShown){
                const hpMap = window.coop_hp_map || {};
                const anyDead = Object.keys(hpMap).some(k=> Number(hpMap[k]) <= 0);
                if(anyDead){
                    // mark shown to avoid repeated overlays
                    window._coopResultsShown = true;
                    try{ showResults(window.coop_results_map || {}); }catch(e){}
                }
            }
        }catch(e){}
        try{ addEvent(`(debug) session_update: scores=${Object.keys(data.scores||{}).join(', ')}`, 'Debug'); }catch(e){}
    });

    socket.on('solution_submitted', (d)=>{
        addEvent(`${d.username} submitted a solution — score ${d.score}`, 'System');
        console.log('[coop] solution_submitted', d);
        addEvent(`(debug) solution_submitted: ${d.username} score=${d.score}`, 'Debug');
        if(d && d.results) {
            // store mapping and build scores
            window.coop_results_map = Object.assign(window.coop_results_map || {}, d.results || {});
            const scoresFromResults = buildScoresFromResults(window.coop_results_map);
            updateScoreboard(scoresFromResults);
        }
    });

    socket.on('session_ended', (d)=>{
        addEvent('Session ended', 'System');
        console.log('[coop] session_ended', d);
        addEvent(`(debug) session_ended`, 'Debug');
        if(d && d.results){
            window.coop_results_map = Object.assign(window.coop_results_map || {}, d.results || {});
            updateScoreboard(buildScoresFromResults(window.coop_results_map));
        }
        // show final results overlay (server-declared end)
        try{
            if(!window._coopResultsShown){
                window._coopResultsShown = true;
                showResults(window.coop_results_map || {});
            }
        }catch(e){}
    });

    socket.on('error', (e)=>{ addEvent(`Error: ${e.message || e}`, 'System'); });

    // end attach-once guard
}

    function buildScoresFromResults(resultsMap){
        // resultsMap: { id: { username, score, ... } }
        const out = {};
        if(!resultsMap) return out;
        Object.keys(resultsMap).forEach(k=>{
            const v = resultsMap[k];
            out[k] = (v && (v.score || v.score === 0)) ? v.score : 0;
        });
        return out;
    }

    function updateScoreboard(scores){
        // enhanced scoreboard: shows a small box with scores, HP bars and cooldown indicators
        let box = document.getElementById('scoreBox');
        if(!box){
            box = document.createElement('div');
            box.id = 'scoreBox';
            box.style.position = 'fixed';
            box.style.right = '1rem';
            box.style.top = '6rem';
            box.style.minWidth = '200px';
            box.style.background = 'rgba(0,0,0,0.6)';
            box.style.color = '#fff';
            box.style.padding = '0.5rem';
            box.style.borderRadius = '6px';
            document.body.appendChild(box);
        }
        const map = window.coop_results_map || {};
        window.coop_hp_map = window.coop_hp_map || {};
        // ensure all players in scores have hp initialized
        Object.keys(scores || {}).forEach(k=>{ if(typeof window.coop_hp_map[k] === 'undefined') window.coop_hp_map[k] = 100; });

        box.innerHTML = '<strong>Scoreboard</strong><br/>' + Object.keys(scores || {}).map(k=>{
            const v = scores[k];
            const friendly = (map[k] && (map[k].username || map[k].actor_name)) ? (map[k].username || map[k].actor_name) : k;
            const hp = window.coop_hp_map[k] || 0;
            const hpPct = Math.max(0, Math.min(100, hp));
            // cooldown indicator (if provided as timestamp, convert to remaining seconds)
            let cdHtml = '';
            try{
                const cdTs = (window.coop_cooldowns && window.coop_cooldowns[k]) ? window.coop_cooldowns[k] : (map[k] && map[k].cooldown ? map[k].cooldown : 0);
                if(cdTs){
                    const rem = Math.max(0, Math.ceil(cdTs - (Date.now()/1000)));
                    if(rem > 0) cdHtml = `<span style="float:right;color:#ffcccb;font-size:0.8rem">CD ${rem}s</span>`;
                }
            }catch(e){ cdHtml = ''; }

            return `<div class="score-entry card-effect-anchor" data-user-id="${k}" style="margin-top:0.4rem;padding:0.25rem;background:rgba(255,255,255,0.02);border-radius:6px;position:relative;overflow:visible">
                        <div style="display:flex;justify-content:space-between"><strong>${friendly}</strong>${cdHtml}</div>
                        <div style="font-size:0.85rem">Score: <strong>${v}</strong></div>
                        <div style="height:8px;background:rgba(255,255,255,0.08);border-radius:4px;margin-top:6px;overflow:hidden">
                            <div style="height:8px;width:${hpPct}%;background:linear-gradient(90deg,#7b61ff,#c86efd);border-radius:4px"></div>
                        </div>
                    </div>`;
        }).join('');
    }

    // Render participant panels inside the page so effects attach to visible elements
    function renderParticipants(participantsMap){
        const wrap = document.getElementById('scoreboardWrap') || document.body;
        let container = document.getElementById('participantsPanel');
        if(!container){
            container = document.createElement('div');
            container.id = 'participantsPanel';
            container.style.display = 'flex';
            container.style.gap = '0.75rem';
            container.style.marginTop = '1rem';
            (document.querySelector('.gradient-card') || wrap).appendChild(container);
        }
        // Clear and recreate
        container.innerHTML = '';
        Object.keys(participantsMap || {}).forEach(uid=>{
            const name = participantsMap[uid] || uid;
            const card = document.createElement('div');
            card.className = 'player-card card-effect-anchor';
            card.dataset.userId = uid;
            card.dataset.userId = uid; // duplicate intentionally for query selectors
            card.style.minWidth = '180px';
            card.style.padding = '0.5rem';
            card.style.borderRadius = '12px';
            card.style.background = 'linear-gradient(180deg, rgba(255,255,255,0.02), rgba(0,0,0,0.03))';
            card.style.color = '#fff';
            card.style.position = 'relative';

            const title = document.createElement('div'); title.style.fontWeight = '700'; title.textContent = name;
            const scoreLine = document.createElement('div'); scoreLine.style.fontSize = '0.9rem'; scoreLine.style.marginTop = '0.25rem';
            scoreLine.innerHTML = `Score: <strong class="player-score">0</strong>`;
            const hpWrap = document.createElement('div'); hpWrap.style.marginTop = '0.6rem';
            hpWrap.innerHTML = `<div style="height:8px;background:rgba(255,255,255,0.06);border-radius:4px;overflow:hidden"><div class="player-hp" style="height:8px;width:100%;background:linear-gradient(90deg,#7b61ff,#c86efd);border-radius:4px"></div></div>`;

            card.appendChild(title);
            card.appendChild(scoreLine);
            card.appendChild(hpWrap);
            // clicking a card selects it as a target
            card.addEventListener('click', ()=> setTargetFor(uid));
            container.appendChild(card);
        });
    }

    function updateParticipantPanels(participantsMap, hpMap, cooldowns){
        try{
            Object.keys(participantsMap || {}).forEach(uid=>{
                const card = document.querySelector(`#participantsPanel .player-card[data-user-id='${uid}']`);
                if(!card) return;
                const scoreEl = card.querySelector('.player-score');
                const hpEl = card.querySelector('.player-hp');
                if(scoreEl && window.coop_results_map && window.coop_results_map[uid]){
                    scoreEl.textContent = (window.coop_results_map[uid].score || 0);
                }
                if(hpEl){
                    const hp = (hpMap && typeof hpMap[uid] !== 'undefined') ? hpMap[uid] : (window.coop_hp_map && window.coop_hp_map[uid]) || 100;
                    hpEl.style.width = Math.max(0, Math.min(100, hp)) + '%';
                }
                // optionally show cooldown overlay
                const existingCd = card.querySelector('.cooldown-badge');
                const cdTs = (cooldowns && cooldowns[uid]) ? cooldowns[uid] : null;
                if(cdTs){
                    const rem = Math.max(0, Math.ceil(cdTs - (Date.now()/1000)));
                    if(rem > 0){
                        if(!existingCd){
                            const cd = document.createElement('div'); cd.className = 'cooldown-badge';
                            cd.style.position = 'absolute'; cd.style.right = '8px'; cd.style.top = '8px'; cd.style.padding = '2px 6px'; cd.style.background = 'rgba(255,204,203,0.12)'; cd.style.borderRadius = '8px'; cd.style.fontSize = '0.8rem'; cd.textContent = `CD ${rem}s`;
                            card.appendChild(cd);
                        } else { existingCd.textContent = `CD ${rem}s`; }
                    } else if(existingCd){ existingCd.remove(); }
                } else if(existingCd){ existingCd.remove(); }
            });
        }catch(e){/*ignore*/}
    }

    // Render a full-screen results overlay showing final scores and winner(s)
    function showResults(resultsMap){
        try{
            // clear existing overlay if any
            const existing = document.getElementById('coopResultsOverlay');
            if(existing) existing.remove();

            const overlay = document.createElement('div');
            overlay.id = 'coopResultsOverlay';
            overlay.style.position = 'fixed';
            overlay.style.left = 0; overlay.style.top = 0; overlay.style.right = 0; overlay.style.bottom = 0;
            overlay.style.background = 'rgba(0,0,0,0.7)';
            overlay.style.display = 'flex';
            overlay.style.alignItems = 'center';
            overlay.style.justifyContent = 'center';
            overlay.style.zIndex = 9999;

            const box = document.createElement('div');
            box.style.background = '#0b1220';
            box.style.color = '#fff';
            box.style.padding = '1.25rem';
            box.style.borderRadius = '10px';
            box.style.minWidth = '360px';
            box.style.maxWidth = '90%';

            const title = document.createElement('h3');
            title.textContent = 'Session Results';
            title.style.marginTop = '0';
            box.appendChild(title);

            // build score list
            const list = document.createElement('div');
            list.style.marginTop = '0.5rem';
            const scores = buildScoresFromResults(resultsMap || {});
            // find top score
            const entries = Object.keys(scores).map(k=>({ id:k, score: scores[k], name: (resultsMap[k] && (resultsMap[k].username||resultsMap[k].actor_name)) ? (resultsMap[k].username||resultsMap[k].actor_name) : k }));
            entries.sort((a,b)=> b.score - a.score);

            entries.forEach((e, idx)=>{
                const row = document.createElement('div');
                row.style.display = 'flex';
                row.style.justifyContent = 'space-between';
                row.style.alignItems = 'center';
                row.style.padding = '0.45rem 0';
                row.style.borderBottom = '1px solid rgba(255,255,255,0.03)';
                const left = document.createElement('div');
                left.textContent = `${idx===0? '🏆 ': ''}${e.name}`;
                left.style.fontWeight = idx===0 ? '700' : '500';
                const right = document.createElement('div');
                right.textContent = String(e.score || 0);
                right.style.fontWeight = '700';
                row.appendChild(left);
                row.appendChild(right);
                list.appendChild(row);
            });

            if(entries.length === 0){
                const none = document.createElement('div'); none.textContent = 'No results available.'; list.appendChild(none);
            }

            box.appendChild(list);

            const actions = document.createElement('div');
            actions.style.display = 'flex';
            actions.style.justifyContent = 'flex-end';
            actions.style.marginTop = '1rem';

            const close = document.createElement('button');
            close.className = 'btn btn-primary';
            close.textContent = 'Close';
            close.addEventListener('click', ()=>{ overlay.remove(); });
            actions.appendChild(close);

            const back = document.createElement('a');
            back.className = 'btn btn-outline';
            back.style.marginLeft = '0.5rem';
            back.textContent = 'Back to Trials';
            back.href = '/trials';
            actions.appendChild(back);

            box.appendChild(actions);
            overlay.appendChild(box);
            document.body.appendChild(overlay);
            // also log to event list
            addEvent('Session ended — showing results', 'System');
        }catch(e){ console.error('showResults error', e); }
    }

    // mute button wiring (if present in template)
    const muteBtn = document.getElementById('muteBtn');
    if(muteBtn){
        muteBtn.addEventListener('click', ()=>{
            const isMuted = muteBtn.dataset.muted === '1';
            muteBtn.dataset.muted = isMuted ? '0' : '1';
            muteBtn.textContent = isMuted ? '🔊' : '🔇';
            audioEngine.mute(!isMuted);
        });
        // initialize state
        muteBtn.dataset.muted = '0';
    }

    if(readyBtn){
        readyBtn.addEventListener('click', ()=>{
            if(isCreator){
                readyBtn.disabled = true;
                readyBtn.textContent = 'Starting...';
                socket.emit('start_coop_session', { session_code: sessionCode });
            } else {
                readyBtn.disabled = true;
                readyBtn.textContent = 'Ready — waiting...';
                addEvent('You are ready. Waiting for partner...', 'You');
            }
        });
    }

    if(leaveBtn){
        leaveBtn.addEventListener('click', ()=>{
            if(confirm('Leave this session?')) window.location.reload();
        });
    }

})();
