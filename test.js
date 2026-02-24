
            const token = "{token}";
            let currentTab = 'dashboard';
            function showTab(t, el) {{
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
                document.getElementById('tab-'+t).classList.add('active');
                if(el) el.classList.add('active');
                currentTab = t;
                if(t==='canais') loadCanais(); if(t==='keywords') loadKeywords();
                if(t==='admins') loadAdmins(); if(t==='sorteios') loadSorteios();
                if(t==='settings') loadSettings(); if(t==='dashboard') loadStatus();
                if(t==='logs') fetchLogs(); if(t==='moldura') loadWatermark();
                if(t==='enviar') backToStep(1);
            }}
            function loadWatermark() {{
                const img = document.getElementById('wm-current-img');
                img.src = '/api/watermark?token=' + token + '&t=' + Date.now();
            }}
            async function uploadWatermark() {{
                const fileInput = document.getElementById('wm-file');
                if(!fileInput.files[0]) return Telegram.WebApp.showAlert("Selecione um arquivo primeiro!");
                
                const formData = new FormData();
                formData.append('file', fileInput.files[0]);
                
                try {{
                    const r = await fetch(`/api/watermark?token=${{token}}`, {{
                        method: 'POST',
                        body: formData
                    }});
                    const res = await r.json();
                    if(res.success) {{
                        Telegram.WebApp.showAlert("Moldura atualizada com sucesso!");
                        loadWatermark();
                    }} else {{
                        Telegram.WebApp.showAlert("Erro: " + res.error);
                    }}
                }} catch(e) {{
                    Telegram.WebApp.showAlert("Erro ao subir arquivo.");
                }}
            }}
            async function api(p, m='GET', b=null) {{
                const s = p.includes('?') ? '&' : '?';
                const r = await fetch(`/api/${{p}}${{s}}token=${{token}}`, {{ method: m, body: b ? JSON.stringify(b) : null, headers: {{'Content-Type':'application/json'}} }});
                return await r.json();
            }}
            async function loadStatus() {{
                const d = await api('status');
                document.getElementById('status-container').innerHTML = `
                    <p>Monitorando: <b>${{d.canais_count}} canais</b></p>
                    <p>Keywords: <b>${{d.kw_count}}</b> (+) / <b>${{d.nkw_count}}</b> (-)</p>
                    <p>Bot: <b>${{d.pausado==='1' ? '⏸️ PAUSADO' : '▶️ ATIVO'}}</b></p>
                `;
                document.getElementById('btn-pausa').textContent = d.pausado==='1' ? '▶️ RETOMAR BOT' : '⏸️ PAUSAR BOT';
                document.getElementById('check-only-admins').checked = d.only_admins==='1';
                document.getElementById('check-aprovacao').checked = d.aprovacao==='1';
            }}
            async function restartBot() {{
                Telegram.WebApp.showConfirm("Deseja reiniciar o bot? O painel ficará offline por alguns segundos.", async (ok) => {{
                    if(ok) {{
                        await api('restart', 'POST'); 
                        Telegram.WebApp.showAlert("Solicitação enviada! O bot irá reiniciar em instantes.");
                        setTimeout(() => Telegram.WebApp.close(), 2000);
                    }}
                }});
            }}
            async function toggleOnlyAdmins() {{
                const v = document.getElementById('check-only-admins').checked ? '1' : '0';
                await api('settings', 'POST', {{ chave: 'only_admins', valor: v }});
            }}
            async function toggleAprovacao() {{
                const v = document.getElementById('check-aprovacao').checked ? '1' : '0';
                await api('settings', 'POST', {{ chave: 'aprovacao_manual', valor: v }});
            }}
            async function togglePausa() {{
                const d = await api('status');
                const v = d.pausado==='1' ? '0' : '1';
                await api('settings', 'POST', {{ chave: 'pausado', valor: v }});
                loadStatus();
            }}

            // Fluxo Enviar Promoção
            let scrapeData = {{}};
            function backToStep(s) {{
                document.querySelectorAll('#tab-enviar .card').forEach(c => c.style.display = 'none');
                document.getElementById('step-'+s).style.display = 'block';
            }}
            async function startScrape() {{
                const url = document.getElementById('promo-url').value;
                if(!url) return Telegram.WebApp.showAlert("Cole um link!");
                
                Telegram.WebApp.MainButton.setText("🔍 Buscando dados...").show();
                try {{
                    const d = await api('scrape', 'POST', {{ url: url }});
                    if(d.error) throw new Error(d.error);
                    
                    scrapeData = d;
                    document.getElementById('preview-title').value = d.title || "";
                    document.getElementById('preview-price').value = d.price || "";
                    document.getElementById('preview-img').src = d.image || "";
                    
                    backToStep(2);
                }} catch(e) {{
                    Telegram.WebApp.showAlert("Erro ao buscar dados: " + e.message);
                }} finally {{
                    Telegram.WebApp.MainButton.hide();
                }}
            }}
            async function generateText() {{
                Telegram.WebApp.MainButton.setText("✨ Gerando texto...").show();
                try {{
                    const d = await api('generate_text', 'POST', {{
                        url: document.getElementById('promo-url').value,
                        title: document.getElementById('preview-title').value,
                        price: document.getElementById('preview-price').value,
                        coupon: document.getElementById('preview-coupon').value,
                        observation: document.getElementById('preview-obs').value
                    }});
                    document.getElementById('final-text').value = d.text;
                    updatePreview();
                    previewLinks(); // Chama preview de links em background
                    backToStep(3);
                }} catch(e) {{
                    Telegram.WebApp.showAlert("Erro ao gerar texto: " + e.message);
                }} finally {{
                    Telegram.WebApp.MainButton.hide();
                }}
            }}

            function updatePreview() {{
                const text = document.getElementById('final-text').value;
                // Renderiza HTML básico interpretando as tags suportadas pelo Telegram (<b>, <i>, <a>, <code>, <pre>)
                const preview = document.getElementById('html-render-preview');
                preview.innerHTML = text.replace(/\n/g, '<br>');
            }}

            async function previewLinks() {{
                const container = document.getElementById('processed-links-container');
                container.style.display = 'block';
                container.innerHTML = "⌛ Processando links finais...";
                try {{
                    const d = await api('preview_links', 'POST', {{
                        text: document.getElementById('final-text').value,
                        url: document.getElementById('promo-url').value
                    }});
                    if(d.placeholders) {{
                        let html = "<b>Links Finais Detectados:</b><ul style='margin:5px 0; padding-left:15px;'>";
                        for(let k in d.placeholders) {{
                            if(d.placeholders[k]) {{
                                html += `<li style='word-break:break-all;'>${{k}} ➔ ${{d.placeholders[k]}}</li>`;
                            }}
                        }}
                        html += "</ul>";
                        container.innerHTML = html;
                    }}
                }} catch(e) {{
                    container.innerHTML = "⚠️ Erro ao validar links.";
                }}
            }}

            async function postOffer() {{
                const btn = document.getElementById('btn-post');
                btn.disabled = true;
                btn.textContent = "⌛ Postando...";
                try {{
                    const d = await api('post_offer', 'POST', {{
                        url: document.getElementById('promo-url').value,
                        text: document.getElementById('final-text').value,
                        image_path: scrapeData.local_image_path // Corrigido: scraper usa local_image_path
                    }});
                    if(d.success) {{
                        let msg = "🚀 Promoção postada!";
                        if(d.link) {{
                             Telegram.WebApp.showConfirm("Postado com sucesso! Deseja ver o post agora?", (ok) => {{
                                 if(ok) Telegram.WebApp.openTelegramLink(d.link);
                                 resetEnviar();
                             }});
                        }} else {{
                            Telegram.WebApp.showAlert(msg);
                            resetEnviar();
                        }}
                    }} else {{
                        throw new Error(d.error);
                    }}
                }} catch(e) {{
                    Telegram.WebApp.showAlert("Erro ao postar: " + e.message);
                }} finally {{
                    btn.disabled = false;
                    btn.textContent = "POSTAR AGORA 🚀";
                }}
            }}
            function resetEnviar() {{
                document.getElementById('promo-url').value = "";
                backToStep(1);
                showTab('dashboard');
            }}
            async function loadCanais() {{
                const d = await api('canais');
                const l = document.getElementById('list-canais');
                let h = "";
                d.canais.forEach(c => {{ h += `<li>${{c}} <button class="danger" onclick="delCanal('${{c}}')">x</button></li>`; }});
                l.innerHTML = h || "<li>Nenhum canal monitorado.</li>";
            }}
            async function addCanal() {{ const i=document.getElementById('new-canal'); await api('canais','POST',{{canal:i.value}}); i.value=""; loadCanais(); }}
            async function delCanal(c) {{ await api('canais','DELETE',{{canal:c}}); loadCanais(); }}
            async function loadKeywords() {{
                const k = await api('keywords'); const n = await api('neg_keywords');
                const lk = document.getElementById('list-keywords');
                const ln = document.getElementById('list-neg-keywords');
                let hk = "", hn = "";
                k.keywords.forEach(x => {{ hk += `<li>${{x}} <button class="danger" onclick="delKw('kw','${{x}}')">x</button></li>`; }});
                n.keywords.forEach(x => {{ hn += `<li>${{x}} <button class="danger" onclick="delKw('nkw','${{x}}')">x</button></li>`; }});
                lk.innerHTML = hk || "<li>Nenhuma keyword (+)</li>";
                ln.innerHTML = hn || "<li>Nenhuma keyword (-)</li>";
            }}
            async function delKw(t,x) {{ await api(t==='kw'?'keywords':'neg_keywords','DELETE',{{keyword:x}}); loadKeywords(); }}
            async function addKeyword(t) {{ const i=document.getElementById(t==='kw'?'new-kw':'new-nkw'); await api(t==='kw'?'keywords':'neg_keywords','POST',{{keyword:i.value}}); i.value=""; loadKeywords(); }}
            async function loadAdmins() {{
                const d = await api('admins'); const l = document.getElementById('list-admins');
                let h = "";
                d.admins.forEach(a => {{ h += `<li>${{a[1]}} (${{a[0]}}) <button class="danger" onclick="delAdmin('${{a[0]}}')">x</button></li>`; }});
                l.innerHTML = h || "<li>Apenas você.</li>";
            }}
            async function addAdmin() {{ await api('admins','POST',{{user_id:document.getElementById('new-admin-id').value, username:document.getElementById('new-admin-name').value}}); loadAdmins(); }}
            async function delAdmin(id) {{ await api('admins','DELETE',{{user_id:id}}); loadAdmins(); }}
            async function loadSorteios() {{
                const d = await api('sorteios'); const l = document.getElementById('list-sorteios');
                let h = "";
                d.sorteios.forEach(s => {{ h += `<li>${{s[1]}} <button onclick="closeSorteio('${{s[0]}}')">Encerrar</button></li>`; }});
                l.innerHTML = h || "<li>Nenhum sorteio ativo.</li>";
            }}
            async function addSorteio() {{ await api('sorteios','POST',{{premio:document.getElementById('new-premio').value}}); loadSorteios(); }}
            async function closeSorteio(id) {{ await api('sorteios','PATCH',{{id:id, winner_id:0, winner_name:'Ganhador'}}); loadSorteios(); }}
            async function loadSettings() {{
                const f = [{{k:'delay_minutos',l:'Delay'}},{{k:'preco_minimo',l:'Preço'}},{{k:'assinatura',l:'Assinatura'}},{{k:'webapp_url',l:'WebApp URL'}}];
                const c = document.getElementById('settings-form');
                c.innerHTML = "Carregando...";
                let html = "";
                for(const x of f) {{
                    const v = await api('settings?key='+x.k);
                    const isA = x.k==='assinatura';
                    html += `
                        <p style="margin-bottom:5px; font-weight:bold; font-size:13px;">${{x.l}}:</p>
                        ${{isA ? `
                                 <div id="editor-toolbar" style="margin-bottom:5px; display:flex; gap:5px">
                                    <button type="button" onclick="tag('b')" style="padding:2px 8px; font-size:12px"><b>B</b></button>
                                    <button type="button" onclick="tag('i')" style="padding:2px 8px; font-size:12px"><i>I</i></button>
                                    <button type="button" onclick="tag('u')" style="padding:2px 8px; font-size:12px"><u>U</u></button>
                                    <button type="button" onclick="tag('a')" style="padding:2px 8px; font-size:12px">Link</button>
                                    <button type="button" onclick="tag('code')" style="padding:2px 8px; font-size:12px">&lt;&gt;</button>
                                 </div>
                                 <textarea id="set-${{x.k}}" oninput="updatePreview(this.value)" style="height:120px; font-family:monospace; font-size:12px;">${{v.valor}}</textarea>
                                 <div id="html-preview" style="background:#000; padding:10px; border-radius:4px; margin:5px 0; font-size:12px; border:1px dashed var(--border)">
                                    <small style="color:var(--text-dim);display:block;margin-bottom:5px">Preview Visual (Telegram HTML):</small>
                                    <div id="preview-content" style="white-space: pre-wrap;">${{v.valor}}</div>
                                 </div>` 
                               : `<input id="set-${{x.k}}" value="${{v.valor}}">`
                        }}
                        <button onclick="saveSet('${{x.k}}')" class="primary" style="margin-top:5px;width:100%">Salvar</button>
                        <hr style="border:0; border-top:1px solid var(--border); margin:15px 0;">
                    `;
                }}
                c.innerHTML = html;
            }}
            function updatePreview(val) {{
                const p = document.getElementById('preview-content');
                if(p) p.innerHTML = val;
            }}
            function tag(t) {{
                const i = document.getElementById('set-assinatura');
                const s = i.selectionStart, e = i.selectionEnd;
                const txt = i.value;
                const sel = txt.substring(s, e);
                let rep = "";
                if(t==='a') rep = `<a href="URL_AQUI">${{sel || "texto"}}</a>`;
                else rep = `<${{t}}>${{sel}}</${{t}}>`;
                i.value = txt.substring(0, s) + rep + txt.substring(e);
                updatePreview(i.value);
                i.focus();
            }}
            async function saveSet(k) {{ 
                const val = document.getElementById('set-'+k).value;
                await api('settings','POST',{{chave:k, valor:val}}); 
                Telegram.WebApp.showAlert("Configuração '"+k+"' salva com sucesso!"); 
            }}
            async function fetchLogs() {{ 
                const term = document.getElementById('terminal');
                const timeStr = document.getElementById('log-time');
                if(!term.textContent) term.textContent = "Carregando logs...";
                const d = await api('logs'); 
                if(d.logs) {{
                    term.textContent = d.logs; 
                    term.scrollTop = term.scrollHeight;
                    const now = new Date();
                    timeStr.textContent = "Sincronizado: " + now.toLocaleDateString('pt-BR') + " " + now.toLocaleTimeString('pt-BR');
                }} else if(d.error) {{
                    term.textContent = "Erro: " + d.error;
                }}
            }}
            function toggleExpandLog() {{
                const t = document.getElementById('terminal');
                const b = document.getElementById('btn-expand');
                t.classList.toggle('expanded');
                b.textContent = t.classList.contains('expanded') ? '↕️ Reduzir' : '↕️ Expandir';
            }}
            if(window.Telegram && window.Telegram.WebApp) {{ Telegram.WebApp.ready(); Telegram.WebApp.expand(); }}
            setInterval(()=>{{ if(currentTab==='logs') fetchLogs(); if(currentTab==='dashboard') loadStatus(); }}, 2000);
            loadStatus();
        