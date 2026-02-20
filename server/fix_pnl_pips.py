#!/usr/bin/env python3
"""One-time DB fixup: recalculate pnl_pips for existing trades and delete old test trades.

Run inside Docker:
  docker exec ict-tradebot python fix_pnl_pips.py

Or directly:
  cd server && python fix_pnl_pips.py
"""
import sqlite3
import os

DB_PATH = os.getenv("DB_PATH", "/data/trades.db")
if not os.path.exists(DB_PATH):
    DB_PATH = "data/trades.db"  # fallback for local dev

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

print(f"Connected to: {DB_PATH}")
print()

# --- Step 1: Delete old test trades (no checklist score, early February losses) ---
print("=== Step 1: Delete old test trades ===")
old_trades = conn.execute(
    """SELECT id, symbol, bias, checklist_score, outcome, pnl_pips, pnl_money, created_at
       FROM trades
       WHERE (checklist_score IS NULL OR checklist_score = '' OR checklist_score = '0')
       ORDER BY created_at ASC"""
).fetchall()

if old_trades:
    for t in old_trades:
        print(f"  Deleting: {t['id'][:8]}.. {t['symbol']} {t['bias']} "
              f"score={t['checklist_score']!r} outcome={t['outcome']} "
              f"pnl_pips={t['pnl_pips']} created={t['created_at']}")

    ids = [t["id"] for t in old_trades]
    placeholders = ",".join("?" * len(ids))
    conn.execute(f"DELETE FROM trades WHERE id IN ({placeholders})", ids)
    # Also clean up any related post-trade reviews
    conn.execute(f"DELETE FROM post_trade_reviews WHERE trade_id IN ({placeholders})", ids)
    print(f"  Deleted {len(old_trades)} trade(s).")
else:
    print("  No old test trades found.")

print()

# --- Step 2: Recalculate pnl_pips for all closed/executed trades ---
print("=== Step 2: Fix pnl_pips for existing trades ===")
trades = conn.execute(
    """SELECT id, symbol, bias, status, outcome,
              tp1_hit, tp2_hit, sl_hit,
              sl_pips, tp1_pips, tp2_pips,
              pnl_pips, pnl_money
       FROM trades
       WHERE status IN ('closed', 'executed')
       ORDER BY created_at ASC"""
).fetchall()

fixed = 0
for t in trades:
    old_pnl = t["pnl_pips"] or 0
    tp1_hit = t["tp1_hit"]
    tp2_hit = t["tp2_hit"]
    sl_hit = t["sl_hit"]
    tp1_pips = t["tp1_pips"] or 0
    tp2_pips = t["tp2_pips"] or 0
    sl_pips = t["sl_pips"] or 0

    # Recalculate correct pnl_pips based on trade state
    if tp1_hit and tp2_hit:
        correct_pnl = tp1_pips + tp2_pips
        correct_outcome = "full_win"
    elif tp1_hit and sl_hit:
        # TP1 hit, runner hit BE → partial win
        correct_pnl = tp1_pips
        correct_outcome = "partial_win"
    elif tp1_hit and not sl_hit and not tp2_hit:
        # TP1 hit, runner still active
        correct_pnl = tp1_pips
        correct_outcome = t["outcome"]  # keep current
    elif sl_hit and not tp1_hit:
        correct_pnl = -sl_pips
        correct_outcome = "loss"
    else:
        # Still open or unknown state
        continue

    if abs(old_pnl - correct_pnl) > 0.01 or (t["outcome"] != correct_outcome and correct_outcome):
        print(f"  Fixing: {t['id'][:8]}.. {t['symbol']} {t['bias']} "
              f"pnl_pips: {old_pnl} → {correct_pnl:.1f}  "
              f"outcome: {t['outcome']} → {correct_outcome}")
        conn.execute(
            "UPDATE trades SET pnl_pips = ?, outcome = ? WHERE id = ?",
            (correct_pnl, correct_outcome, t["id"])
        )
        fixed += 1

if fixed:
    print(f"  Fixed {fixed} trade(s).")
else:
    print("  All trades already have correct pnl_pips.")

conn.commit()
conn.close()
print()
print("Done! Restart not needed — changes take effect immediately.")
