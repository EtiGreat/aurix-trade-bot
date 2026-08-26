import logging, math, time, os, threading, hmac, hashlib, json
from urllib.parse import parse_qsl
from decimal import Decimal, InvalidOperation
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from database import init_db, get_user, create_user, get_balance, adjust_balance, lock_balance, release_trade_balance, create_request, get_requests, update_request, add_transaction, get_transactions, get_stats, create_demo_trade, get_demo_trades, get_demo_trade, close_demo_trade, get_users, get_user_controls, set_user_status, set_user_risk, add_admin_audit, get_admin_audit, add_notification, get_notifications, mark_notifications_read, count_unread_notifications, get_operational_report, get_onboarding, set_onboarding, get_onboarding_summary
from config import BOT_TOKEN, ADMIN_TELEGRAM_ID, MIN_DEPOSIT_USD, DEPOSIT_FEE_RATE, SUPPORT_USERNAME, PUBLIC_BASE_URL, OFFICIAL_CHANNEL_URL

logging.basicConfig(level=logging.INFO)
pending = {}

def money(v): return f"${Decimal(str(v)):,.2f}"
def is_admin(uid): return str(uid) == str(ADMIN_TELEGRAM_ID)
def tier(balance):
    b=Decimal(str(balance))
    if b >= 1000: return "Elite"
    if b >= 500: return "Pro"
    if b >= 250: return "Advanced"
    if b >= 100: return "Standard"
    return "Starter"

def market_price(symbol):
    base = 2400.0 if symbol == "XAU/USD" else 105000.0
    t = time.time()/60
    wave = math.sin(t/9.0)*0.006 + math.sin(t/31.0)*0.004
    return round(base*(1+wave), 2)

def menu():
    rows = [
        [InlineKeyboardButton("📊 Dashboard", callback_data="dashboard"), InlineKeyboardButton("💰 Deposit", callback_data="deposit")],
        [InlineKeyboardButton("📈 Demo Trading", callback_data="trading"), InlineKeyboardButton("💵 Withdraw", callback_data="withdraw")],
        [InlineKeyboardButton("📜 Transactions", callback_data="transactions"), InlineKeyboardButton("👥 Referral", callback_data="referral")],
        [InlineKeyboardButton("🔔 Notifications", callback_data="notifications"), InlineKeyboardButton("📊 Report", callback_data="report")],
        [InlineKeyboardButton("🆘 Support", callback_data="support"), InlineKeyboardButton("⚠️ Risk", callback_data="risk")],
        [InlineKeyboardButton("🔐 Account & Security", callback_data="account")],
        [InlineKeyboardButton("🌐 Web Dashboard", web_app=WebAppInfo(url=f"{PUBLIC_BASE_URL.rstrip('/')}/app"))] if PUBLIC_BASE_URL else [InlineKeyboardButton("🌐 Web Dashboard", callback_data="web_dashboard")],
        [InlineKeyboardButton("📜 Legal & Risk", callback_data="legal")],
        [InlineKeyboardButton("📢 Official Channel", url=OFFICIAL_CHANNEL_URL)] if OFFICIAL_CHANNEL_URL else [InlineKeyboardButton("📢 Official Channel", callback_data="channel")]
    ]
    return InlineKeyboardMarkup(rows)

def back(): return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Main Menu", callback_data="dashboard")]])

def trading_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🥇 XAU/USD", callback_data="asset:XAU/USD"), InlineKeyboardButton("₿ BTC/USDT", callback_data="asset:BTC/USDT")],
        [InlineKeyboardButton("📂 Open Positions", callback_data="positions"), InlineKeyboardButton("📊 Performance", callback_data="performance")],
        [InlineKeyboardButton("🔙 Main Menu", callback_data="dashboard")]
    ])

def side_menu(symbol):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🟢 LONG", callback_data=f"side:{symbol}:LONG"), InlineKeyboardButton("🔴 SHORT", callback_data=f"side:{symbol}:SHORT")],
        [InlineKeyboardButton("🔙 Trading", callback_data="trading")]
    ])

async def start(update, context):
    u=update.effective_user
    if not get_user(u.id): create_user(u.id,u.username or "",u.first_name or "")
    o=get_onboarding(u.id)
    onboarding_note = "\n🔐 Setup: Demo account onboarding not yet completed. Tap Account & Security to review." if not o["terms_accepted"] else ""
    await update.message.reply_text(
        "🟡 AURIX TRADE\n\nTrade Smarter. Grow With Discipline.\n\n"
        "🤖 Automated Gold & Crypto Trading\n🥇 XAU/USD  •  ₿ BTC/USDT\n\n"
        f"💰 Minimum demo deposit: {money(MIN_DEPOSIT_USD)}\n\n"
        "🧪 DEMO / PAPER-TRADING MODE\nNo real deposits, custody, broker orders or withdrawals are processed by this build.\n\n"
        f"🔔 Notifications: {count_unread_notifications(u.id)} unread" + onboarding_note + "\n\n"
        "⚠️ Trading involves substantial risk. Returns are not guaranteed.", reply_markup=menu())

async def admin(update, context):
    if not is_admin(update.effective_user.id): return await update.message.reply_text("⛔ Admin access only.")
    users,pending_count,volume=get_stats()
    await update.message.reply_text(f"🛡 AURIX TRADE ADMIN\n\n👥 Users: {users}\n⏳ Pending requests: {pending_count}\n💵 Demo transaction volume: {money(volume)}\n\nUse the controls below to monitor users, requests, risk settings and admin activity.", reply_markup=admin_menu())

def admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 Users",callback_data="admin_users")],
        [InlineKeyboardButton("💰 Deposit Requests",callback_data="admin_deposits"),InlineKeyboardButton("💵 Withdrawal Requests",callback_data="admin_withdrawals")],
        [InlineKeyboardButton("🛡 Risk Controls",callback_data="admin_risk"),InlineKeyboardButton("📜 Audit Log",callback_data="admin_audit")],
        [InlineKeyboardButton("📊 Operations Report",callback_data="admin_report")],
        [InlineKeyboardButton("🔄 Refresh",callback_data="admin_home")]
    ])


async def notify(update, context):
    if not is_admin(update.effective_user.id): return await update.message.reply_text("⛔ Admin access only.")
    raw=" ".join(context.args).strip()
    if "|" not in raw: return await update.message.reply_text("Usage: /notify Title | Message")
    title,message=[x.strip() for x in raw.split("|",1)]
    users=get_users(10000); sent=0
    for u in users:
        add_notification(u["telegram_id"],title,message,"admin")
        try:
            await context.bot.send_message(chat_id=u["telegram_id"], text=f"🔔 {title}\n\n{message}")
            sent += 1
        except Exception:
            pass
    add_admin_audit(update.effective_user.id,"broadcast_notification",None,f"recipients={len(users)},sent={sent}")
    await update.message.reply_text(f"🔔 Notification created for {len(users)} users; Telegram delivery succeeded for {sent}.",reply_markup=admin_menu())

async def handle_text(update, context):
    uid=update.effective_user.id; state=pending.get(uid)
    if not state: return
    text=update.message.text.strip()
    if state[0] == "deposit" or state[0] == "withdraw":
        try: amount=Decimal(text)
        except InvalidOperation: return await update.message.reply_text("Enter a valid USD amount, e.g. 50 or 100.")
        if amount <= 0: return await update.message.reply_text("Amount must be greater than zero.")
        if state[0] == "deposit":
            if amount < MIN_DEPOSIT_USD: return await update.message.reply_text(f"Minimum demo deposit is {money(MIN_DEPOSIT_USD)}.")
            fee=(amount*DEPOSIT_FEE_RATE).quantize(Decimal("0.01")); total=amount+fee
            ref=create_request(uid,"deposit",float(amount),float(fee),f"DEP-{uid}-{int(time.time())}"); pending.pop(uid,None)
            await update.message.reply_text(f"💰 DEMO DEPOSIT REQUEST\n\nTrading capital: {money(amount)}\nPlatform fee: {money(fee)}\nTotal shown: {money(total)}\n\nReference: {ref}\n\n⚠️ DEMO ONLY — do not send funds.",reply_markup=menu())
        else:
            balance=Decimal(str(get_balance(uid)))
            if amount > balance:
                pending.pop(uid,None); return await update.message.reply_text(f"Insufficient demo balance. Available: {money(balance)}",reply_markup=menu())
            ref=create_request(uid,"withdrawal",float(amount),0.0,f"WDR-{uid}-{int(time.time())}"); pending.pop(uid,None)
            await update.message.reply_text(f"💵 DEMO WITHDRAWAL REQUEST\n\nAmount: {money(amount)}\nReference: {ref}\n\n⚠️ DEMO ONLY — no funds are transferred.",reply_markup=menu())
        return
    if state[0] == "trade_stake":
        symbol,side=state[1],state[2]
        try: stake=Decimal(text)
        except InvalidOperation: return await update.message.reply_text("Enter a valid demo stake, e.g. 10 or 25.")
        balance=Decimal(str(get_balance(uid)))
        open_stake=sum(Decimal(str(t["stake"])) for t in get_demo_trades(uid,"open"))
        if stake <= 0: return await update.message.reply_text("Stake must be greater than zero.")
        controls=get_user_controls(uid)
        if controls["status"] != "active": return await update.message.reply_text("⛔ Your demo account is currently restricted. Contact support.")
        if stake > Decimal(str(controls["max_trade_stake"])): return await update.message.reply_text(f"Risk limit: maximum demo stake is {money(controls['max_trade_stake'])}.")
        if len(get_demo_trades(uid,"open")) >= int(controls["max_open_positions"]): return await update.message.reply_text(f"Risk limit: maximum open positions is {controls['max_open_positions']}.")
        if stake > balance-open_stake: return await update.message.reply_text(f"Stake exceeds available demo capital. Available: {money(balance-open_stake)}")
        if not lock_balance(uid, float(stake)): return await update.message.reply_text("Unable to reserve that demo stake. Please try again.")
        entry=market_price(symbol); trade_id=create_demo_trade(uid,symbol,side,float(stake),entry); pending.pop(uid,None)
        await update.message.reply_text(f"📈 DEMO POSITION OPENED\n\n{symbol} • {side}\nStake: {money(stake)}\nEntry: {entry:,.2f}\nTrade ID: #{trade_id}\n\nThis is simulated paper trading only; no broker/exchange order was sent.",reply_markup=trading_menu())

async def admin_users(update,context):
    q=update.callback_query; await q.answer()
    if not is_admin(q.from_user.id): return await q.edit_message_text("⛔ Admin access only.")
    rows=get_users(20)
    if not rows: return await q.edit_message_text("No users yet.",reply_markup=admin_menu())
    lines=["👥 USER MANAGEMENT\n"]; buttons=[]
    for u in rows:
        c=get_user_controls(u["telegram_id"]); lines.append(f"• {u['telegram_id']} — {u.get('first_name') or 'User'} — {c['status']} — max stake {money(c['max_trade_stake'])} — open {c['max_open_positions']}")
        buttons.append([InlineKeyboardButton(f"{'🔴 Suspend' if c['status']=='active' else '🟢 Activate'} {u['telegram_id']}",callback_data=f"userstatus:{u['telegram_id']}:{'suspended' if c['status']=='active' else 'active'}")])
    buttons.append([InlineKeyboardButton("🔙 Admin",callback_data="admin_home")])
    await q.edit_message_text("\n".join(lines),reply_markup=InlineKeyboardMarkup(buttons))

async def admin_risk(update,context):
    q=update.callback_query; await q.answer()
    if not is_admin(q.from_user.id): return await q.edit_message_text("⛔ Admin access only.")
    rows=get_users(10); lines=["🛡 RISK CONTROLS\n\nPreset limits currently applied to users:"]; buttons=[]
    for u in rows:
        c=get_user_controls(u["telegram_id"]); lines.append(f"• {u['telegram_id']}: {money(c['max_trade_stake'])} max stake / {c['max_open_positions']} open")
        buttons.append([InlineKeyboardButton(f"Conservative {u['telegram_id']}",callback_data=f"risk:{u['telegram_id']}:25:1"),InlineKeyboardButton(f"Standard {u['telegram_id']}",callback_data=f"risk:{u['telegram_id']}:100:3")])
    buttons.append([InlineKeyboardButton("🔙 Admin",callback_data="admin_home")])
    await q.edit_message_text("\n".join(lines),reply_markup=InlineKeyboardMarkup(buttons))

async def admin_audit(update,context):
    q=update.callback_query; await q.answer()
    if not is_admin(q.from_user.id): return await q.edit_message_text("⛔ Admin access only.")
    rows=get_admin_audit(20)
    lines=["📜 ADMIN AUDIT LOG\n"] + [f"• {r['created_at']} — admin {r['admin_id']} — {r['action']} — {r['target_id'] or '-'}\n  {r['details']}" for r in rows]
    await q.edit_message_text("\n".join(lines) if rows else "📜 ADMIN AUDIT LOG\n\nNo admin actions recorded yet.",reply_markup=admin_menu())

async def admin_list(update,context):
    q=update.callback_query; await q.answer()
    if not is_admin(q.from_user.id): return await q.edit_message_text("⛔ Admin access only.")
    kind="deposit" if q.data=="admin_deposits" else "withdrawal"; rows=get_requests("pending",kind)
    if not rows: return await q.edit_message_text(f"No pending {kind} requests.",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin",callback_data="admin_home")]]))
    lines=[f"📋 PENDING {kind.upper()}S\n"]; buttons=[]
    for r in rows[:20]:
        lines.append(f"#{r['id']} • User {r['telegram_id']} • {money(r['amount'])} • {r['reference']}")
        buttons.append([InlineKeyboardButton(f"✅ Approve #{r['id']}",callback_data=f"approve:{r['id']}"),InlineKeyboardButton(f"❌ Reject #{r['id']}",callback_data=f"reject:{r['id']}")])
    buttons.append([InlineKeyboardButton("🔙 Admin",callback_data="admin_home")]); await q.edit_message_text("\n".join(lines),reply_markup=InlineKeyboardMarkup(buttons))

async def admin_decision(update,context):
    q=update.callback_query; await q.answer()
    if not is_admin(q.from_user.id): return await q.edit_message_text("⛔ Admin access only.")
    action,rid=q.data.split(":"); req=update_request(int(rid),"confirmed" if action=="approve" else "rejected")
    if not req: return await q.edit_message_text("Request not found or already processed.")
    if action=="approve":
        if req["kind"]=="deposit": adjust_balance(req["telegram_id"],req["amount"]); add_transaction(req["telegram_id"],"deposit",req["amount"],req["fee"],req["reference"],"Demo deposit approved")
        elif req["kind"]=="withdrawal":
            balance=Decimal(str(get_balance(req["telegram_id"]))); amount=Decimal(str(req["amount"]))
            if amount > balance: update_request(int(rid),"rejected"); return await q.edit_message_text("❌ Withdrawal rejected: insufficient demo balance at approval time.")
            adjust_balance(req["telegram_id"],-req["amount"]); add_transaction(req["telegram_id"],"withdrawal",req["amount"],0,req["reference"],"Demo withdrawal approved")
    await q.edit_message_text(f"{'✅ APPROVED' if action=='approve' else '❌ REJECTED'}\n\nRequest #{rid}\nUser: {req['telegram_id']}\nAmount: {money(req['amount'])}\nReference: {req['reference']}\n\n⚠️ Demo accounting only; no real funds moved.")

def trade_pnl(trade):
    current=market_price(trade["symbol"]); entry=Decimal(str(trade["entry_price"])); stake=Decimal(str(trade["stake"])); move=(Decimal(str(current))-entry)/entry; sign=Decimal("1") if trade["side"]=="LONG" else Decimal("-1"); pnl=(stake*move*sign).quantize(Decimal("0.01")); return current,pnl

async def admin_report(update,context):
    q=update.callback_query; await q.answer()
    if not is_admin(q.from_user.id): return await q.edit_message_text("⛔ Admin access only.")
    r=get_operational_report()
    await q.edit_message_text(
        "📊 OPERATIONS REPORT\n\n"
        f"👥 Total users: {r['users']}\n🟢 Active: {r['active']}\n🔴 Suspended: {r['suspended']}\n"
        f"📈 Open demo trades: {r['open_trades']}\n📜 Closed demo trades: {r['closed_trades']}\n"
        f"💹 Realized demo P/L: {money(r['demo_pnl'])}\n"
        f"⏳ Pending deposits: {r['pending_deposits']}\n💵 Pending withdrawals: {r['pending_withdrawals']}\n"
        f"🔔 Unread notifications: {r['unread']}\n\n🧪 Demo/paper-trading environment only.", reply_markup=admin_menu())

async def account_screen(update, context):
    q=update.callback_query; await q.answer(); uid=q.from_user.id
    o=get_onboarding(uid)
    u=get_user(uid) or {}
    terms="✅ Accepted" if o["terms_accepted"] else "⏳ Pending"
    privacy="✅ Acknowledged" if o["privacy_acknowledged"] else "⏳ Pending"
    risk="✅ Acknowledged" if o["risk_acknowledged"] else "⏳ Pending"
    profile="✅ Complete" if o["profile_completed"] else "⏳ Basic profile only"
    verification=o["verification_status"].replace("_"," ").title()
    text=(f"🔐 ACCOUNT & SECURITY\n\n👤 Telegram ID: {uid}\n"
          f"📛 Username: @{u.get('username') or 'not set'}\n"
          f"📅 Account created: {u.get('created_at','—')}\n\n"
          f"📜 Terms: {terms}\n🔏 Privacy: {privacy}\n⚠️ Risk disclosure: {risk}\n"
          f"👤 Profile: {profile}\n🪪 Verification status: {verification}\n\n"
          "🧪 Demo account: no live-money access is enabled.\n"
          "🔒 Telegram identity is the current sign-in mechanism. Never share your Telegram login codes with anyone.")
    buttons=[]
    if not o["terms_accepted"] or not o["privacy_acknowledged"] or not o["risk_acknowledged"]:
        buttons.append([InlineKeyboardButton("✅ Review & Accept Demo Terms", callback_data="onboard_accept")])
    if not o["profile_completed"]:
        buttons.append([InlineKeyboardButton("👤 Complete Basic Profile", callback_data="onboard_profile")])
    buttons.append([InlineKeyboardButton("🪪 Verification Status", callback_data="verification")])
    buttons.append([InlineKeyboardButton("🔙 Main Menu", callback_data="dashboard")])
    await q.edit_message_text(text,reply_markup=InlineKeyboardMarkup(buttons))

async def accept_demo_terms(update, context):
    q=update.callback_query; await q.answer(); uid=q.from_user.id
    set_onboarding(uid,terms_accepted=1,privacy_acknowledged=1,risk_acknowledged=1,last_security_check=time.strftime('%Y-%m-%d %H:%M:%S'))
    add_admin_audit(uid,"demo_terms_accepted",None,"terms=1,privacy=1,risk=1") if is_admin(uid) else None
    await q.edit_message_text("✅ DEMO TERMS ACCEPTED\n\nYou acknowledged the Terms, Privacy Notice and Risk Disclosure for the AURIX TRADE demo environment.\n\nThis does not authorize real-money deposits, custody, withdrawals or live trading.",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👤 Complete Basic Profile",callback_data="onboard_profile")],[InlineKeyboardButton("🪪 Verification Status",callback_data="verification")],[InlineKeyboardButton("🔙 Main Menu",callback_data="dashboard")]]))

async def complete_profile(update, context):
    q=update.callback_query; await q.answer(); uid=q.from_user.id
    u=get_user(uid) or {}
    set_onboarding(uid,profile_completed=1,last_security_check=time.strftime('%Y-%m-%d %H:%M:%S'))
    await q.edit_message_text(f"👤 BASIC PROFILE\n\nName: {u.get('first_name') or 'Not set'}\nUsername: @{u.get('username') or 'not set'}\nTelegram ID: {uid}\n\nNo sensitive identity documents are collected by this demo build.\n\nFor any future live-money service, a separate compliant KYC process must be implemented before access is granted.",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🪪 Verification Status",callback_data="verification")],[InlineKeyboardButton("🔙 Account & Security",callback_data="account")]]))

async def verification_screen(update, context):
    q=update.callback_query; await q.answer(); uid=q.from_user.id
    o=get_onboarding(uid)
    status=o["verification_status"].replace("_"," ").title()
    await q.edit_message_text(f"🪪 VERIFICATION STATUS\n\nCurrent status: {status}\n\n🧪 This is a demo/paper-trading environment, so identity-document submission is disabled.\n\nBefore any real-money service is enabled, AURIX TRADE should implement the required KYC/AML, sanctions screening, data-protection and regulatory controls for the jurisdictions in which it operates.",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Account & Security",callback_data="account")]]))

async def callback(update,context):
    q=update.callback_query; await q.answer(); uid=q.from_user.id
    if q.data=="account": return await account_screen(update,context)
    if q.data=="onboard_accept": return await accept_demo_terms(update,context)
    if q.data=="onboard_profile": return await complete_profile(update,context)
    if q.data=="verification": return await verification_screen(update,context)
    if q.data=="admin_home":
        if is_admin(uid):
            users,pending_count,volume=get_stats(); await q.edit_message_text(f"🛡 AURIX TRADE ADMIN\n\n👥 Users: {users}\n⏳ Pending requests: {pending_count}\n💵 Demo transaction volume: {money(volume)}",reply_markup=admin_menu())
        return
    if q.data=="admin_users": return await admin_users(update,context)
    if q.data=="admin_risk": return await admin_risk(update,context)
    if q.data=="admin_audit": return await admin_audit(update,context)
    if q.data=="admin_report": return await admin_report(update,context)
    if q.data.startswith("userstatus:"):
        if not is_admin(uid): return await q.edit_message_text("⛔ Admin access only.")
        _,target,status=q.data.split(":"); set_user_status(int(target),status); add_admin_audit(uid,"user_status",int(target),f"status={status}"); return await admin_users(update,context)
    if q.data.startswith("risk:"):
        if not is_admin(uid): return await q.edit_message_text("⛔ Admin access only.")
        _,target,max_stake,max_open=q.data.split(":"); set_user_risk(int(target),float(max_stake),int(max_open)); add_admin_audit(uid,"risk_update",int(target),f"max_stake={max_stake},max_open={max_open}"); return await admin_risk(update,context)
    if q.data in ("admin_deposits","admin_withdrawals"): return await admin_list(update,context)
    if q.data.startswith(("approve:","reject:")): return await admin_decision(update,context)
    if q.data=="deposit": pending[uid]=( "deposit", ); return await q.edit_message_text(f"💰 DEPOSIT\n\nEnter USD amount.\nMinimum: {money(MIN_DEPOSIT_USD)}\nDemo fee: {DEPOSIT_FEE_RATE*100}%\n\n⚠️ DEMO ONLY — do not send money.",reply_markup=back())
    if q.data=="withdraw": pending[uid]=( "withdraw", ); return await q.edit_message_text("💵 WITHDRAW\n\nEnter USD amount to create a demo withdrawal request.\nNo real funds are transferred.",reply_markup=back())
    if q.data=="trading": return await q.edit_message_text("📈 DEMO TRADING\n\nSelect a market. Prices are simulated for paper-trading demonstrations only.",reply_markup=trading_menu())
    if q.data.startswith("asset:"):
        symbol=q.data.split(":",1)[1]; return await q.edit_message_text(f"{symbol}\n\nSimulated price: {market_price(symbol):,.2f}\n\nChoose a paper-trading direction:",reply_markup=side_menu(symbol))
    if q.data.startswith("side:"):
        _,symbol,side=q.data.split(":",2); pending[uid]=( "trade_stake",symbol,side); bal=Decimal(str(get_balance(uid))); open_stake=sum(Decimal(str(t["stake"])) for t in get_demo_trades(uid,"open")); avail=bal-open_stake
        return await q.edit_message_text(f"{symbol} • {side}\n\nAvailable demo capital: {money(avail)}\nEnter your simulated stake in USD.",reply_markup=trading_menu())
    if q.data=="positions":
        rows=get_demo_trades(uid,"open");
        if not rows: return await q.edit_message_text("📂 OPEN POSITIONS\n\nNo open demo positions.",reply_markup=trading_menu())
        lines=["📂 OPEN DEMO POSITIONS\n"]; buttons=[]
        for t in rows:
            cur,pnl=trade_pnl(t); lines.append(f"#{t['id']} • {t['symbol']} • {t['side']}\nStake {money(t['stake'])} • Entry {t['entry_price']:,.2f} • Now {cur:,.2f} • P/L {money(pnl)}")
            buttons.append([InlineKeyboardButton(f"🔒 Close #{t['id']}",callback_data=f"close:{t['id']}")])
        buttons.append([InlineKeyboardButton("🔙 Trading",callback_data="trading")]); return await q.edit_message_text("\n\n".join(lines),reply_markup=InlineKeyboardMarkup(buttons))
    if q.data.startswith("close:"):
        tid=int(q.data.split(":")[1]); t=get_demo_trade(tid,uid)
        if not t or t["status"]!="open": return await q.edit_message_text("Position is no longer open.",reply_markup=trading_menu())
        cur,pnl=trade_pnl(t);
        if not release_trade_balance(uid, float(t["stake"]), float(pnl)): return await q.edit_message_text("Unable to settle this demo position safely. Please contact support.",reply_markup=trading_menu())
        close_demo_trade(tid,uid,cur,float(pnl)); return await q.edit_message_text(f"🔒 DEMO POSITION CLOSED\n\n#{tid} • {t['symbol']} • {t['side']}\nExit: {cur:,.2f}\nSimulated P/L: {money(pnl)}\n\nNo real funds were moved.",reply_markup=trading_menu())
    if q.data=="performance":
        rows=get_demo_trades(uid); closed=[r for r in rows if r["status"]=="closed"]; pnl=sum(Decimal(str(r["pnl"] or 0)) for r in closed); wins=sum(1 for r in closed if Decimal(str(r["pnl"] or 0))>0); losses=sum(1 for r in closed if Decimal(str(r["pnl"] or 0))<0); win_rate=(Decimal(wins)/Decimal(len(closed))*100 if closed else Decimal(0)); volume=sum(Decimal(str(r["stake"])) for r in closed); return await q.edit_message_text(f"📊 DEMO PERFORMANCE\n\nClosed trades: {len(closed)}\nWinning trades: {wins}\nLosing trades: {losses}\nWin rate: {win_rate:.1f}%\nDemo volume: {money(volume)}\nRealized simulated P/L: {money(pnl)}\n\n⚠️ These are simulated results only and do not represent live performance.",reply_markup=trading_menu())
    u=get_user(uid); bal=Decimal(str(u["balance"] if u else 0)); locked=Decimal(str(u["locked_balance"] if u and "locked_balance" in u else 0)); equity=bal+locked
    if q.data=="notifications":
        rows=get_notifications(uid,10)
        mark_notifications_read(uid)
        text="🔔 NOTIFICATIONS\n\n"+("\n\n".join([f"{r['title']}\n{r['message']}\n{r['created_at'][:19]} UTC" for r in rows]) if rows else "No notifications yet.")
    elif q.data=="report":
        rows=get_demo_trades(uid)
        closed=[r for r in rows if r["status"]=="closed"]
        pnl=sum(Decimal(str(r["pnl"] or 0)) for r in closed)
        open_count=sum(1 for r in rows if r["status"]=="open")
        text=f"📊 ACCOUNT REPORT\n\nClosed demo trades: {len(closed)}\nOpen demo trades: {open_count}\nRealized simulated P/L: {money(pnl)}\n\n🧪 Demo results only."
    elif q.data=="dashboard": text=f"📊 DASHBOARD\n\n💵 Available demo balance: {money(bal)}\n🔒 Locked in open trades: {money(locked)}\n💎 Demo equity: {money(equity)}\n🏷 Account tier: {tier(equity)}\n\n📈 Trading status: DEMO / PAPER\n🥇 XAU/USD: simulated\n₿ BTC/USDT: simulated\n\nUse Demo Trading to open and close paper positions and view simulated P/L."
    elif q.data=="transactions":
        rows=get_transactions(uid); text="📜 TRANSACTIONS\n\n"+("\n".join([f"• {r['kind'].title()} {money(r['amount'])} — {r['reference'] or '—'}" for r in rows]) if rows else "No completed demo transactions yet.")
    elif q.data=="referral": text=f"👥 REFERRAL\n\nYour referral code: {u['referral_code'] if u else '—'}\n\nReferral analytics are included in the v4 account model. Reward terms should be published only after the commercial/legal model is finalized."
    elif q.data=="support": text=f"🆘 SUPPORT\n\n{('@'+SUPPORT_USERNAME) if SUPPORT_USERNAME else 'Configure SUPPORT_USERNAME in Railway Variables.'}"
    elif q.data=="channel": text="📢 OFFICIAL CHANNEL\n\nConfigure OFFICIAL_CHANNEL_URL in Railway Variables before publishing this button."
    elif q.data=="web_dashboard":
        base=PUBLIC_BASE_URL or "your Railway public URL"
        text=f"🌐 WEB DASHBOARD\n\nOpen: {base}/app\n\nIf the dashboard is opened inside Telegram, your demo account can be shown securely.\n\n🧪 Demo / paper trading only."
    elif q.data=="legal":
        base=PUBLIC_BASE_URL or "your Railway public URL"
        text=f"📜 LEGAL & RISK\n\nTerms: {base}/terms\nPrivacy: {base}/privacy\nRisk Disclosure: {base}/risk\n\n🧪 Current mode: DEMO / PAPER TRADING"
    else: text="⚠️ RISK DISCLOSURE\n\nTrading Forex/CFDs, cryptocurrencies and other financial instruments involves substantial risk and may result in loss of capital. Past performance does not guarantee future results. AURIX TRADE does not guarantee profits or specific returns."
    await q.edit_message_text(text,reply_markup=menu())

def run_web_server():
    from flask import Flask, jsonify, render_template_string, request
    app = Flask(__name__)

    def page(title, body, scripts=""):
        return render_template_string("""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{{title}}</title><style>
        :root{--black:#080808;--gold:#D4AF37;--gold2:#F5C542;--silver:#C7CBD1;--green:#19B879;--line:#292f35}*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at top,#1b1b18 0,#080808 48%);color:#f5f5f5;font-family:Inter,Arial,sans-serif}.wrap{max-width:1120px;margin:auto;padding:24px}.top{display:flex;justify-content:space-between;align-items:center;gap:16px;margin-bottom:22px}.brand{font-weight:900;letter-spacing:.04em;font-size:25px;color:var(--gold)}.tag{color:var(--silver);font-size:13px}.pill{padding:8px 12px;border:1px solid #4b3e16;border-radius:999px;color:var(--gold2);background:#16140d;font-size:12px}.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}.card{border:1px solid var(--line);border-radius:18px;padding:20px;background:linear-gradient(145deg,#151a20,#0d0f12);box-shadow:0 10px 30px #0006}.label{color:var(--silver);font-size:12px;text-transform:uppercase;letter-spacing:.08em}.value{font-size:28px;font-weight:800;margin-top:7px}.gold{color:var(--gold2)}.green{color:var(--green)}.section{margin-top:18px}.section h2{font-size:17px;margin:0 0 12px;color:var(--gold)}table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:11px 8px;border-bottom:1px solid var(--line);font-size:13px}th{color:var(--silver)}.muted{color:#9aa1a9}.notice{border-left:3px solid var(--gold);padding:12px 14px;background:#17140d;border-radius:8px;color:#d7d7d7}.btn{display:inline-block;padding:12px 15px;border-radius:10px;background:var(--gold);color:#090909;text-decoration:none;font-weight:800}.hero{padding:28px;border-radius:22px;border:1px solid #3b321a;background:linear-gradient(135deg,#17150e,#101214)}@media(max-width:800px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:520px){.wrap{padding:14px}.grid{grid-template-columns:1fr}.value{font-size:24px}}
        </style></head><body><div class="wrap"><div class="top"><div><div class="brand">🟡 AURIX TRADE</div><div class="tag">Trade Smarter. Grow With Discipline.</div></div><div class="pill">DEMO / PAPER TRADING</div></div>{{body|safe}}<div class="section muted" style="font-size:12px">Automated Gold & Crypto Trading · XAU/USD · BTC/USDT · No real deposits, custody, withdrawals or broker/exchange orders are processed by this build.</div></div>{{scripts|safe}}</body></html>""", title=title, body=body, scripts=scripts)

    @app.get('/')
    def home():
        return page('AURIX TRADE', '<div class="hero"><h1 style="color:#F5C542;margin-top:0">Professional trading dashboard</h1><p>Monitor your AURIX demo account, simulated positions, performance and onboarding status from one place.</p><p class="notice">🧪 This environment is paper trading only. No real money is accepted or moved.</p><p><a class="btn" href="/app">Open Dashboard</a></p></div>')

    @app.get('/app')
    def app_page():
        body="""<div id="loading" class="card">Loading secure Telegram session…</div><div id="dash" style="display:none"><div class="hero"><h1 id="welcome" style="color:#F5C542;margin-top:0">AURIX TRADE</h1><p id="status" class="muted"></p></div><div class="section grid"><div class="card"><div class="label">Available balance</div><div class="value" id="balance">—</div></div><div class="card"><div class="label">Locked capital</div><div class="value" id="locked">—</div></div><div class="card"><div class="label">Demo equity</div><div class="value gold" id="equity">—</div></div><div class="card"><div class="label">Account tier</div><div class="value" id="tier">—</div></div></div><div class="section grid"><div class="card"><div class="label">Open positions</div><div class="value" id="open">—</div></div><div class="card"><div class="label">Closed trades</div><div class="value" id="closed">—</div></div><div class="card"><div class="label">Win rate</div><div class="value green" id="winrate">—</div></div><div class="card"><div class="label">Realized P/L</div><div class="value" id="pnl">—</div></div></div><div class="section card"><h2>Open Positions</h2><div id="positions" class="muted">—</div></div><div class="section card"><h2>Recent Activity</h2><div id="activity" class="muted">—</div></div><div class="section card"><h2>Account & Security</h2><div id="onboarding" class="muted">—</div></div></div>"""
        scripts="""<script src="https://telegram.org/js/telegram-web-app.js"></script><script>const tg=window.Telegram&&window.Telegram.WebApp?window.Telegram.WebApp:null;if(tg){tg.ready();tg.expand();}const initData=tg?tg.initData:"";async function load(){if(!initData){document.getElementById("loading").innerHTML='<div class="notice">Open this dashboard from the <b>🌐 Web Dashboard</b> button inside the AURIX TRADE Telegram bot. Your account data is not exposed through a public login.</div>';return;}const r=await fetch('/api/me',{headers:{'X-Telegram-Init-Data':initData}});const d=await r.json();if(!r.ok){document.getElementById("loading").innerHTML='<div class="notice">Unable to verify the Telegram session. Please reopen the dashboard from Telegram.</div>';return;}document.getElementById('loading').style.display='none';document.getElementById('dash').style.display='block';document.getElementById('welcome').textContent='Welcome, '+(d.user.first_name||'Trader');document.getElementById('status').textContent='Account: '+(d.user.username?'@'+d.user.username:'Telegram user')+' · DEMO / PAPER';const m=x=>'$'+Number(x).toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:2});document.getElementById('balance').textContent=m(d.account.balance);document.getElementById('locked').textContent=m(d.account.locked);document.getElementById('equity').textContent=m(d.account.equity);document.getElementById('tier').textContent=d.account.tier;document.getElementById('open').textContent=d.stats.open;document.getElementById('closed').textContent=d.stats.closed;document.getElementById('winrate').textContent=d.stats.win_rate.toFixed(1)+'%';document.getElementById('pnl').textContent=m(d.stats.pnl);document.getElementById('positions').innerHTML=d.positions.length?'<table><tr><th>Market</th><th>Side</th><th>Stake</th><th>Entry</th><th>Now</th><th>P/L</th></tr>'+d.positions.map(t=>'<tr><td>'+t.symbol+'</td><td>'+t.side+'</td><td>'+m(t.stake)+'</td><td>'+Number(t.entry_price).toLocaleString()+'</td><td>'+Number(t.current_price).toLocaleString()+'</td><td class="'+(t.pnl>=0?'green':'')+'">'+m(t.pnl)+'</td></tr>').join('')+'</table>':'No open demo positions.';document.getElementById('activity').innerHTML=d.recent.length?'<table><tr><th>Market</th><th>Side</th><th>Status</th><th>P/L</th></tr>'+d.recent.map(t=>'<tr><td>'+t.symbol+'</td><td>'+t.side+'</td><td>'+t.status+'</td><td>'+m(t.pnl||0)+'</td></tr>').join('')+'</table>':'No demo trades yet.';document.getElementById('onboarding').innerHTML='Terms: '+(d.onboarding.terms?'✅':'❌')+' · Privacy: '+(d.onboarding.privacy?'✅':'❌')+' · Risk: '+(d.onboarding.risk?'✅':'❌')+' · Profile: '+(d.onboarding.profile?'✅':'❌')+' · Verification: '+d.onboarding.verification;}load();</script>"""
        return page('AURIX Web Dashboard', body, scripts)

    def validate_init_data(init_data):
        if not BOT_TOKEN or not init_data: return None
        try:
            pairs=dict(parse_qsl(init_data,keep_blank_values=True)); received=pairs.pop('hash',None)
            if not received: return None
            data_check='\\n'.join(f'{k}={v}' for k,v in sorted(pairs.items()))
            secret=hmac.new(b'WebAppData',BOT_TOKEN.encode(),hashlib.sha256).digest()
            calc=hmac.new(secret,data_check.encode(),hashlib.sha256).hexdigest()
            if not hmac.compare_digest(calc,received): return None
            if int(time.time())-int(pairs.get('auth_date','0'))>86400: return None
            return json.loads(pairs.get('user','{}'))
        except Exception: return None

    def current_user(): return validate_init_data(request.headers.get('X-Telegram-Init-Data',''))
    def serialize_trade(t):
        cur,pnl=trade_pnl(t) if t['status']=='open' else (t.get('exit_price') or t['entry_price'], t.get('pnl') or 0)
        return {'id':t['id'],'symbol':t['symbol'],'side':t['side'],'stake':float(t['stake']),'entry_price':float(t['entry_price']),'current_price':float(cur),'pnl':float(pnl),'status':t['status']}

    @app.get('/api/me')
    def api_me():
        tg_user=current_user()
        if not tg_user: return jsonify(error='unauthorized'),401
        uid=int(tg_user['id']); u=get_user(uid)
        if not u: return jsonify(error='account_not_found'),404
        bal=Decimal(str(u.get('balance',0))); locked=Decimal(str(u.get('locked_balance',0))); equity=bal+locked
        rows=get_demo_trades(uid); closed=[r for r in rows if r['status']=='closed']; pnl=sum(Decimal(str(r.get('pnl') or 0)) for r in closed); wins=sum(1 for r in closed if Decimal(str(r.get('pnl') or 0))>0); wr=float(Decimal(wins)/Decimal(len(closed))*100) if closed else 0.0
        return jsonify(user={'id':uid,'first_name':tg_user.get('first_name',''),'username':tg_user.get('username','')},account={'balance':float(bal),'locked':float(locked),'equity':float(equity),'tier':tier(equity)},stats={'open':sum(1 for r in rows if r['status']=='open'),'closed':len(closed),'win_rate':wr,'pnl':float(pnl)},positions=[serialize_trade(r) for r in rows if r['status']=='open'],recent=[serialize_trade(r) for r in rows[:10]],onboarding=get_onboarding_summary(uid))

    @app.get('/health')
    def health(): return jsonify(status='ok', mode='demo', service='aurix-trade', dashboard='enabled')
    @app.get('/terms')
    def terms(): return page('Terms','<div class="card"><h2>Terms of Use</h2><p>AURIX TRADE is currently provided as a demonstration and paper-trading environment. No real-money investment, custody, withdrawal, or execution service is offered by this build.</p><p>Users are responsible for understanding financial-market risks. No profit or return is guaranteed.</p></div>')
    @app.get('/privacy')
    def privacy(): return page('Privacy','<div class="card"><h2>Privacy Notice</h2><p>The demo may process Telegram account identifiers, usernames and activity required to operate the service. Do not submit passwords, payment credentials, private keys or other sensitive financial information through the demo bot.</p></div>')
    @app.get('/risk')
    def risk(): return page('Risk Disclosure','<div class="card"><h2>Risk Disclosure</h2><p>Trading Forex/CFDs, cryptocurrencies and other financial instruments involves substantial risk and may result in loss of capital. Past performance does not guarantee future results. AURIX TRADE does not guarantee profits or specific returns.</p><p>This build uses simulated paper trading only.</p></div>')
    port=int(os.getenv('PORT','8080'));app.run(host='0.0.0.0',port=port,debug=False,use_reloader=False)

def main():
    threading.Thread(target=run_web_server, daemon=True).start()
    if not BOT_TOKEN: raise RuntimeError("BOT_TOKEN is missing")
    init_db(); app=Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start",start)); app.add_handler(CommandHandler("admin",admin)); app.add_handler(CommandHandler("notify",notify)); app.add_handler(CommandHandler("notify",notify)); app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,handle_text)); app.add_handler(CallbackQueryHandler(callback)); app.run_polling()

if __name__=="__main__": main()
