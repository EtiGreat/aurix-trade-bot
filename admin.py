from database import get_admin_stats, list_users, list_transactions

def format_stats():
    s=get_admin_stats()
    return (f"🛡 AURIX TRADE ADMIN\n\n👥 Users: {s['users']}\n"
            f"💰 Confirmed deposits: ${s['deposits']:.2f}\n"
            f"💳 Deposit fees: ${s['deposit_fees']:.2f}\n"
            f"📈 Profit fees: ${s['profit_fees']:.2f}\n"
            f"💸 Withdrawals recorded: {s['withdrawals']}")

def format_users():
    rows=list_users(20)
    return "👥 USERS\n\n" + ("\n".join(
        f"• {r['telegram_id']} | @{r['username'] or '-'} | ${r['balance']:.2f}" for r in rows)
        if rows else "No users yet.")

def format_transactions():
    rows=list_transactions(30)
    return "📜 TRANSACTIONS\n\n" + ("\n".join(
        f"#{r['id']} {r['kind']} | ${r['amount']:.2f} | fee ${r['fee']:.2f} | {r['status']}" for r in rows)
        if rows else "No transactions yet.")
