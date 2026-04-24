// =====================================================================
// Aura Retail OS — runtime client.  Talks to Flask JSON API.
// Highlights pattern chips in the left rail when each pattern fires.
// =====================================================================
const KT = window.KIOSK_TYPE;
const $  = (q) => document.querySelector(q);
const $$ = (q) => document.querySelectorAll(q);

let state = {cart:[], payment:'card', dispenserActive:'spiral', modules:[], admin: false};

function flashPattern(...names){
  names.forEach(n=>{
    const li = document.querySelector(`.rail-list li[data-p="${n}"]`);
    if(!li) return;
    li.classList.add('active');
    clearTimeout(li._t);
    li._t = setTimeout(()=>li.classList.remove('active'), 1600);
  });
}

function toast(msg, bad=false){
  const t = $('#toast'); t.textContent = msg;
  t.classList.toggle('bad', bad); t.classList.add('show');
  clearTimeout(t._t); t._t = setTimeout(()=>t.classList.remove('show'), 2400);
}

async function api(path, opts={}){
  const r = await fetch(path, {
    method: opts.method || 'GET',
    headers: {'Content-Type':'application/json'},
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  });
  return r.json();
}

async function renameItem(id, currentName, type='product'){
  const newName = prompt(`Rename ${type}:`, currentName);
  if(!newName || newName === currentName) return;
  flashPattern('proxy');
  const j = await api('/api/admin/rename', {method:'POST', body:{kiosk_type:KT, id:id, name:newName, item_type:type}});
  if(j.ok){ toast('Renamed successfully'); refresh(); }
  else toast(j.message, true);
}

async function updatePrice(id, currentPrice, currentEPrice, type='product'){
  const newPrice = prompt(`Enter Standard Price (₹) for product #${id}:`, currentPrice);
  if(newPrice === null) return;
  const newEPrice = prompt(`Enter Emergency Price (₹) for product #${id}:`, currentEPrice);
  if(newEPrice === null) return;
  
  flashPattern('proxy');
  const j = await api('/api/admin/price', {method:'POST', body:{
    kiosk_type:KT, id:id, price:parseFloat(newPrice), emergency_price:parseFloat(newEPrice), item_type:type
  }});
  if(j.ok){ toast('Prices updated'); refresh(); }
  else toast(j.message, true);
}

// ---------------------------------------------------------------------
async function refresh(){
  flashPattern('singleton','facade');
  const s = await api(`/api/state/${KT}`);
  $('#dispenserName').textContent = s.diagnostics.dispenser;
  $('#policyName').textContent    = s.diagnostics.policy;
  $('#catalogPolicy').textContent = `policy=${s.diagnostics.policy}`;
  $('#emergencyBadge').classList.toggle('hidden', !s.emergency);
  $('#adminBadge').classList.toggle('hidden', !s.admin);
  state.dispenserActive = s.dispenser;
  state.admin = s.admin;
  renderProducts(s.products, s.admin);
  renderBundles(s.bundles, s.admin);
  renderTxns(s.transactions, s.admin);
  renderEvents(s.events);
  syncAdminUi(s.admin);
  // sync dispenser segment
  $$('#dispenserSeg button').forEach(b=>b.classList.toggle('active', b.dataset.d===s.dispenser));
  renderCart();
}

function renderProducts(products, admin){
  flashPattern('proxy','composite');
  const g = $('#productGrid'); g.innerHTML = '';
  products.forEach(p=>{
    const stockClass = p.stock===0 ? 'stock-out' : (p.stock<10 ? 'stock-low' : '');
    const el = document.createElement('div');
    el.className='prod';
    el.innerHTML = `
      ${p.requires_refrigeration?'<span class="refr-badge">❄ COLD</span>':''}
      <div class="pname ${admin?'editable':''}" data-id="${p.id}">${p.name}</div>
      <div class="pmeta">
        <span class="price ${admin?'editable':''}">₹${p.price.toFixed(2)}</span>
        <span class="${stockClass}">stock: ${p.stock}</span>
      </div>
      ${admin?`<div class="admin-actions">
        <button class="del-btn" data-id="${p.id}">delete</button>
        <div class="rs-group">
          <input type="number" value="10" id="rs-val-${p.id}">
          <button class="rs-btn" data-id="${p.id}">restock</button>
        </div>
      </div>`:''}
    `;
    
    // Rename listener
    if(admin){
      el.querySelector('.pname').onclick = (e) => { e.stopPropagation(); renameItem(p.id, p.name, 'product'); };
      el.querySelector('.price').onclick = (e) => { e.stopPropagation(); updatePrice(p.id, p.base_price, p.emergency_price, 'product'); };
    }

    el.addEventListener('click', (e)=>{
      if(e.target.closest('.admin-actions') || e.target.classList.contains('editable')) return;
      if(p.stock===0){ toast('Out of stock', true); return; }
      addToCart(p);
    });
    g.appendChild(el);
  });

  // admin button hooks
  if(admin){
    g.querySelectorAll('.del-btn').forEach(b=>{
      b.onclick = async ()=>{
        flashPattern('proxy');
        const r = await fetch(`/api/admin/product/${b.dataset.id}?kiosk_type=${KT}`, {method:'DELETE'});
        const j = await r.json();
        toast(j.ok?'Deleted':j.message||'Denied', !j.ok);
        refresh();
      };
    });
    g.querySelectorAll('.rs-btn').forEach(b=>{
      b.onclick = async ()=>{
        const id = b.dataset.id;
        const qty = $(`#rs-val-${id}`).value;
        flashPattern('command','proxy');
        const j = await api('/api/restock', {method:'POST', body:{kiosk_type:KT, product_id:id, qty:parseInt(qty)}});
        toast(j.ok?`Restocked +${qty}`:j.message, !j.ok);
        refresh();
      };
    });
  }
}

function renderBundles(bundles, admin){
  const head = $('#bundleHeader'); const g = $('#bundleGrid');
  g.innerHTML = '';
  if(!bundles.length){ head.style.display='none'; return; }
  flashPattern('composite');
  head.style.display='block';
  bundles.forEach(b=>{
    const el = document.createElement('div'); el.className='bundle';
    el.innerHTML = `
      <div class="bname ${admin?'editable':''}" data-id="${b.id}">
        <span>📦 ${b.name}</span>
        <span class="price ${admin?'editable':''}">₹${b.price.toFixed(2)}</span>
      </div>
      <small class="dim mono">composite · ${b.children.length} items · ${b.available?'available':'partial'}</small>
      <ul>${b.children.map(c=>`<li>${c.qty}× ${c.name} <span class="muted">(stock ${c.stock})</span></li>`).join('')}</ul>
      ${admin?`<div class="admin-actions" style="margin-top:10px">
        <button class="del-bundle-btn" data-id="${b.id}">delete bundle</button>
      </div>`:''}
    `;

    if(admin){
      el.querySelector('.bname').onclick = (e) => { 
        if(e.target.classList.contains('price')) return;
        e.stopPropagation(); 
        renameItem(b.id, b.name, 'bundle'); 
      };
      el.querySelector('.price').onclick = (e) => { 
        e.stopPropagation(); 
        updatePrice(b.id, b.base_price, b.emergency_price, 'bundle'); 
      };
      el.querySelector('.del-bundle-btn').onclick = async (e) => {
        e.stopPropagation();
        flashPattern('proxy');
        const r = await fetch(`/api/admin/bundle/${b.id}?kiosk_type=${KT}`, {method:'DELETE'});
        const j = await r.json();
        toast(j.ok?'Bundle Deleted':j.message, !j.ok);
        refresh();
      };
    }

    el.addEventListener('click', (e)=>{
      if(e.target.closest('.admin-actions') || e.target.closest('.bname')) return;
      if(!b.available){ toast('Incomplete bundle (stock low)', true); return; }
      addToCart(b);
    });
    g.appendChild(el);
  });
}

// ---------------- CART LOGIC (MacroCommand Ready) ----------------
function addToCart(item){
  const type = item.type || 'product';
  const existing = state.cart.find(x => x.id === item.id && x.type === type);
  if(existing){
    if(existing.qty < item.stock) existing.qty++;
    else toast('Stock limit reached', true);
  } else {
    state.cart.push({
      id: item.id, 
      name: item.name, 
      price: item.price, 
      qty: 1, 
      stock: item.stock,
      type: type
    });
    toast(`Added ${item.name}`);
  }
  renderCart();
}

function updateQty(idx, delta){
  const it = state.cart[idx];
  if(delta > 0 && it.qty >= it.stock){ toast('Stock limit reached', true); return; }
  it.qty += delta;
  if(it.qty <= 0) state.cart.splice(idx, 1);
  renderCart();
}

function removeFromCart(idx){
  state.cart.splice(idx, 1);
  renderCart();
}

function renderCart(){
  const box = $('#cartBox');
  if(state.cart.length === 0){
    box.className = 'cart-empty';
    box.textContent = 'Cart is empty. Select products.';
    return;
  }
  box.className = 'cart';
  let total = 0;
  let itemsHtml = state.cart.map((it, idx) => {
    total += it.price * it.qty;
    return `
      <div class="cart-item">
        <div class="ci-top">
          <span class="ci-name">${it.name}</span>
          <span class="ci-sub">₹${(it.price * it.qty).toFixed(2)}</span>
        </div>
        <div class="ci-bot">
          <div class="ci-qty">
            <button onclick="updateQty(${idx},-1)">−</button>
            <span class="mono">${it.qty}</span>
            <button onclick="updateQty(${idx},1)">+</button>
          </div>
          <button class="ci-del" onclick="removeFromCart(${idx})">remove</button>
        </div>
      </div>
    `;
  }).join('');

  box.innerHTML = `
    <div class="cart-list">${itemsHtml}</div>
    <div class="row total"><span>TOTAL</span><span>₹${total.toFixed(2)}</span></div>
    <div class="row"><span>PAYMENT</span><span>${state.payment.toUpperCase()}</span></div>
    <button class="buy ${state.admin?'disabled':''}" id="buyBtn" ${state.admin?'disabled':''}>
      ${state.admin ? '🔒 ADMIN MODE (NO PURCHASE)' : '▶ DISPENSE CART'}
    </button>
  `;
  $('#buyBtn').onclick = doPurchase;
}

async function doPurchase(){
  if(state.admin) { toast('Admins cannot purchase in admin mode', true); return; }
  if(state.cart.length === 0) return;
  flashPattern('command','adapter','strategy','facade','proxy');
  
  const items = state.cart.map(it => ({
    product_id: it.id,
    qty: it.qty,
    item_type: it.type
  }));

  const j = await api('/api/purchase', {method:'POST', body:{
    kiosk_type:KT, 
    items: items,
    payment: state.payment
  }});

  if(j.ok){
    toast(j.dispense);
    state.cart = [];
    renderCart();
  } else {
    toast(j.message, true);
  }
  refresh();
}

function renderTxns(txns, admin){
  const list = $('#txnList'); list.innerHTML = '';
  txns.forEach(t=>{
    const el = document.createElement('div');
    el.className = `txn ${t.status}`;
    el.innerHTML = `
      <span class="l">[#${t.id}] ${t.command} · ${t.message||''}</span>
      ${(t.status==='OK' && t.command==='PURCHASE' && admin)?`<button class="refund" data-id="${t.id}">refund</button>`:''}
    `;
    list.appendChild(el);
  });
  list.querySelectorAll('.refund').forEach(b=>{
    b.onclick = async ()=>{
      flashPattern('command');
      const j = await api('/api/refund', {method:'POST', body:{kiosk_type:KT, txn_id:b.dataset.id}});
      toast(j.ok?`Refunded ₹${j.amount}`:j.message, !j.ok);
      refresh();
    };
  });
}

function renderEvents(events){
  const log = $('#eventLog'); log.innerHTML='';
  events.slice().reverse().forEach(e=>{
    const div = document.createElement('div');
    div.className='e'; div.dataset.lvl = e.level;
    div.innerHTML = `<span class="t">${e.ts}</span><span class="lvl">${e.level}</span><span>${e.message}</span>`;
    log.appendChild(div);
  });
}

function syncAdminUi(admin){
  $('#adminLogin').classList.toggle('hidden', admin);
  $('#adminPanel').classList.toggle('hidden', !admin);
}

// =================== EVENT BINDINGS ===================
$$('.payopt').forEach(b=>{
  b.onclick = ()=>{
    $$('.payopt').forEach(x=>x.classList.remove('active'));
    b.classList.add('active');
    state.payment = b.dataset.pay;
    flashPattern('adapter');
    renderCart();
  };
});

$('#loginBtn').onclick = async ()=>{
  flashPattern('proxy','singleton');
  const j = await api('/api/admin/login', {method:'POST', body:{pin:$('#pinInput').value}});
  toast(j.ok?'Admin authenticated':'Invalid PIN', !j.ok);
  if(j.ok) { $('#pinInput').value=''; refresh(); }
};
$('#logoutBtn').onclick = async ()=>{
  await api('/api/admin/logout', {method:'POST'});
  state.admin = false;
  refresh();
};

$$('#dispenserSeg button').forEach(b=>{
  b.onclick = async ()=>{
    flashPattern('strategy','factory');
    const j = await api('/api/admin/dispenser', {method:'POST', body:{kiosk_type:KT, name:b.dataset.d}});
    toast(j.ok?`Dispenser → ${j.dispenser}`:j.message, !j.ok);
    refresh();
  };
});

$$('.modseg input[type=checkbox]').forEach(c=>{
  c.onchange = async ()=>{
    flashPattern('decorator');
    const mods = Array.from($$('.modseg input:checked')).map(x=>x.dataset.mod);
    const j = await api('/api/admin/modules', {method:'POST', body:{kiosk_type:KT, modules:mods}});
    toast(j.ok?'Modules updated':j.message, !j.ok);
    refresh();
  };
});

$('#emergencyBtn').onclick = async ()=>{
  flashPattern('singleton','strategy');
  const cur = !$('#emergencyBadge').classList.contains('hidden');
  const j = await api('/api/admin/emergency', {method:'POST', body:{on: !cur}});
  toast(j.ok?(j.emergency?'⚠ EMERGENCY MODE ON':'Emergency cleared'):j.message, !j.ok);
  refresh();
};

$('#addBtn').onclick = async ()=>{
  flashPattern('proxy');
  const j = await api('/api/admin/product', {method:'POST', body:{
    kiosk_type:KT,
    name:$('#newName').value, price:$('#newPrice').value,
    emergency_price: $('#newEPrice').value,
    stock:$('#newStock').value, requires_refrigeration:$('#newRefr').checked
  }});
  toast(j.ok?'Product added':j.message, !j.ok);
  if(j.ok){ $('#newName').value=$('#newPrice').value=$('#newEPrice').value=$('#newStock').value=''; $('#newRefr').checked=false; }
  refresh();
};

$('#fetchCartBtn').onclick = () => {
  if(state.cart.length === 0){ toast('Add items to cart first', true); return; }
  let total = 0;
  state.cart.forEach(it => total += it.price * it.qty);
  $('#newBPrice').value = total.toFixed(2);
  $('#newBEPrice').value = (total * 0.9).toFixed(2); 
  toast('Prices fetched: Normal=Total, Emergency=10% Off');
};

$('#addBundleBtn').onclick = async () => {
  flashPattern('proxy','composite');
  if(state.cart.length === 0){ toast('Cart is empty', true); return; }
  const name = $('#newBName').value;
  if(!name){ toast('Enter bundle name', true); return; }

  const items = state.cart.map(it => ({
    product_id: it.id,
    qty: it.qty
  }));

  const j = await api('/api/admin/bundle', {method:'POST', body:{
    kiosk_type: KT,
    name: name,
    items: items,
    price: $('#newBPrice').value || 0,
    emergency_price: $('#newBEPrice').value || 0
  }});

  if(j.ok){
    toast(`Bundle "${name}" created!`);
    $('#newBName').value = $('#newBPrice').value = $('#newBEPrice').value = '';
    state.cart = [];
    renderCart();
    refresh();
  } else {
    toast(j.message, true);
  }
};

// rail toggle
$('#railToggle').onclick = () => {
  $('body.runtime').classList.toggle('collapsed');
};

// boot
refresh();
setInterval(refresh, 7000);
