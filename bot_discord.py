import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import calendar
from datetime import datetime, timezone, timedelta
import json
import asyncio
import io
import os
import math
import time
from PIL import Image, ImageDraw, ImageFont

try:
    from dotenv import load_dotenv
    load_dotenv()  # baca DISCORD_TOKEN dari file .env (tidak ikut di-upload ke GitHub)
except ImportError:
    pass

# Waktu bot pertama kali dijalankan
START_TIME = time.time()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# ==========================================
# ⚙️ CONFIGURATION & CUSTOM EMOJIS
# ==========================================
GUILD_ID             = 1499785130183491684  # 👑 ID Server Discord
CATEGORY_MARKET_ID   = 1499815599650377850  # 🛒 ID Kategori MARKET
VOUCH_CHANNEL_ID     = 1516750837706129448  # 💬 ID Channel Vouch / Testimoni Form
ORDER_LOG_CHANNEL_ID = 1517536348301688872  # 📜 ID Channel History / Order Log
TESTIMONY_CHANNEL_ID = 1499815827015471195  # 📸 ID Channel Upload Testimoni Slash Command
ORDER_CHANNEL_ID     = 1504385232776728646  # 🎯 ID Channel Order Market

# 📦 Custom Emoji Stock System
EMOJI_STOCK_BOX   = "<:stock_box:1544710766093926491>"
EMOJI_STOCK_READY = "<:stock_ready:1544710782296526850>"
EMOJI_STOCK_EMPTY = "<:stock_empty:1544710796624396499>"
EMOJI_RATE_TAG    = "<:rate_tag:1544710812843778138>"

# 🎨 Custom Emoji Static IDs (Order Logs & Testi)
EMOJI_USER      = "<:user:1542204894914805760>"
EMOJI_PRODUCT   = "<:product:1542204911096303716>"
EMOJI_STATUS    = "<:status:1542204878074552430>"
EMOJI_PRICE     = "<:price:1542204860999672019>"
EMOJI_CATEGORY  = "<:category:1542204841550413844>"
EMOJI_RATING    = "<:rating:1542387435701534830>"   
EMOJI_STAR      = "<:star:1542377983279632434>"     

# 📊 Custom Emoji Stats Panel
EMOJI_TOP_BUYER    = "<:topbuyer:1542547531198767144>"
EMOJI_STATS        = "<:stats:1542547549544783973>"
EMOJI_TOTAL_ORDER  = "<:totalorder:1542547566116474940>"
EMOJI_TOTAL_PROFIT = "<:totalprofit:1542547583547998269>"
EMOJI_BUYER_TOTAL  = "<:buyertotal:1542547603395313704>"

# 💎 Custom Emoji Panel & Buttons
EMOJI_ROBUX     = "<:robux:1542377946352713810>"
EMOJI_PRICELIST = "<:pricelist:1542377965386735647>"
EMOJI_MIDDLEMAN = "<:middleman:1542381608588550144>"
EMOJI_ASK       = "<:ask:1563152771274776627>"       # ❓ logo tanda tanya (Ask)
EMOJI_EWALLET   = "<:ewallet:1563153701726715984>"   # 💳 logo e-wallet (QRIS / All Payment)

# 🎬 Custom GIF Emoji Status IDs
EMOJI_CENTANG   = "<:centang:1563228621508841543>"
EMOJI_REFRESH   = "<a:refresh:1563429260184653834>"
EMOJI_SPARKLES  = "<:sparkles:1563228787825713173>"
EMOJI_KLAIM     = "<:klaim:1563231044692349009>"
EMOJI_TUTUP     = "<:tutup:1563231172673146960>"
EMOJI_SERU      = "<:seru:1563231356123611136>"
EMOJI_PASIR    = "<:pasir:1563237494508490822>"
EMOJI_GEMBOK   = "<:gembok:1563237478230524144>"
STATUS_FAILED   = "<a:failed:1542206572208332870>"
STATUS_PENDING  = "<a:pending:1542206602898051102>"
STATUS_SUCCESS  = "<a:success:1542206629380890685>"


# ==========================================
# HELPER: DATABASE STOK ROBUX
# ==========================================
def get_stock():
    file_path = "stock_data.json"
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            data = json.load(f)
            return data.get("robux_stock", 0)
    return 0

def update_stock(amount: int, is_set: bool = False):
    file_path = "stock_data.json"
    current = get_stock() if not is_set else 0
    new_stock = amount if is_set else current + amount
    if new_stock < 0:
        new_stock = 0
    with open(file_path, "w") as f:
        json.dump({"robux_stock": new_stock}, f, indent=4)
    return new_stock


# ==========================================
# HELPER: DATABASE & GENERATOR STATISTIK (BLUE THEME)
# ==========================================
def update_store_stats(user_id: str, username: str, amount: int):
    file_path = "stats_data.json"
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            data = json.load(f)
    else:
        data = {"total_orders": 0, "total_profit": 0, "buyers": {}}

    data["total_orders"] += 1
    data["total_profit"] += amount

    if user_id not in data["buyers"]:
        data["buyers"][user_id] = {"username": username, "total_spent": 0, "tx_count": 0}

    data["buyers"][user_id]["username"] = username
    data["buyers"][user_id]["total_spent"] += amount
    data["buyers"][user_id]["tx_count"] += 1

    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)


def _stats_font(size: int):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def format_rupiah(amount: int) -> str:
    return f"Rp {amount:,}".replace(",", ".")


async def generate_stats_image(rows, page, total_pages, total_profit, total_orders, buyer_count):
    """Gambar leaderboard bergaya kartu (tema biru). rows = list dict rank/username/total_spent/tx_count/avatar_url."""
    W, H = 700, 540
    BG = (219, 234, 254)
    HEAD = (30, 64, 175)
    SUB = (59, 130, 246)
    CARD = (255, 255, 255)
    EDGE = (147, 197, 253)
    NAME = (15, 23, 42)
    MUTED = (100, 116, 139)
    PILL = (239, 246, 255)
    IDR = (37, 99, 235)
    BADGE = [
        ((37, 99, 235), (255, 255, 255)),
        ((59, 130, 246), (255, 255, 255)),
        ((96, 165, 250), (255, 255, 255)),
        ((147, 197, 253), (15, 23, 42)),
        ((191, 219, 254), (15, 23, 42)),
    ]

    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    f_title, f_sub = _stats_font(28), _stats_font(16)
    f_name, f_small = _stats_font(18), _stats_font(14)

    d.text((30, 20), "Top Buyer Spending", font=f_title, fill=HEAD)
    d.text((30, 60), f"Total Profit {format_rupiah(total_profit)}", font=f_sub, fill=SUB)

    pill_txt = f"{total_orders} orders | {buyer_count} buyers"
    pw = d.textlength(pill_txt, font=f_sub)
    d.rounded_rectangle((W - 30 - pw - 24, 22, W - 30, 58), radius=18, fill=PILL, outline=EDGE)
    d.text((W - 30 - 12 - pw, 30), pill_txt, font=f_sub, fill=HEAD)

    y = 100
    async with aiohttp.ClientSession() as session:
        for row in rows:
            d.rounded_rectangle((30, y, W - 30, y + 64), radius=14, fill=CARD, outline=EDGE, width=1)

            badge_bg, badge_fg = BADGE[min(row["rank"], 5) - 1]
            d.rounded_rectangle((44, y + 17, 112, y + 47), radius=10, fill=badge_bg)
            d.text((56, y + 21), f"#{row['rank']}", font=f_name, fill=badge_fg)

            av = None
            if row.get("avatar_url"):
                try:
                    async with session.get(row["avatar_url"]) as resp:
                        if resp.status == 200:
                            av = Image.open(io.BytesIO(await resp.read())).convert("RGBA").resize((46, 46))
                except Exception:
                    av = None
            if av is None:
                av = Image.new("RGBA", (46, 46), EDGE + (255,))
            mask = Image.new("L", (46, 46), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, 45, 45), fill=255)
            img.paste(av, (128, y + 9), mask)

            d.text((188, y + 10), (row["username"] or "Unknown")[:18], font=f_name, fill=NAME)
            d.text((188, y + 36), f"IDR {row['total_spent']:,}".replace(",", "."), font=f_small, fill=IDR)

            tx = f"{row['tx_count']} transaksi"
            tw = d.textlength(tx, font=f_small)
            d.rounded_rectangle((W - 50 - tw - 24, y + 20, W - 50, y + 44), radius=12, fill=PILL)
            d.text((W - 50 - 12 - tw, y + 25), tx, font=f_small, fill=HEAD)

            y += 74

    d.text((30, H - 34), f"Halaman {page}/{total_pages}", font=f_small, fill=MUTED)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


async def _avatar_url(client, uid: int):
    try:
        user = client.get_user(uid) or await client.fetch_user(uid)
        return user.display_avatar.url
    except Exception:
        return None


STATS_PER_PAGE = 5


async def build_stats_panel(client, data: dict, page: int = 1):
    """Panel top buyer: judul, galeri gambar, statistik, dan navigasi halaman. Mengembalikan (layout, file)."""
    buyers = data.get("buyers", {})
    total_buyers = len(buyers)
    total_profit = data.get("total_profit", 0)
    total_orders = data.get("total_orders", 0)

    sorted_items = sorted(buyers.items(), key=lambda kv: kv[1]["total_spent"], reverse=True)
    total_pages = max(1, (total_buyers + STATS_PER_PAGE - 1) // STATS_PER_PAGE)
    page = min(max(page, 1), total_pages)

    start = (page - 1) * STATS_PER_PAGE
    rows = []
    for offset, (uid, bdata) in enumerate(sorted_items[start:start + STATS_PER_PAGE]):
        rows.append({
            "rank": start + offset + 1,
            "username": bdata.get("username", "Unknown"),
            "total_spent": bdata.get("total_spent", 0),
            "tx_count": bdata.get("tx_count", 0),
            "avatar_url": await _avatar_url(client, int(uid)),
        })

    img_buf = await generate_stats_image(rows, page, total_pages, total_profit, total_orders, total_buyers)
    file = discord.File(fp=img_buf, filename="top_buyer.png")

    layout = discord.ui.LayoutView(timeout=None)
    container = discord.ui.Container()
    container.add_item(discord.ui.TextDisplay(f"## {EMOJI_TOP_BUYER} TOP BUYER SPENDING"))
    container.add_item(discord.ui.Separator())
    container.add_item(discord.ui.MediaGallery(discord.MediaGalleryItem(media="attachment://top_buyer.png")))
    container.add_item(discord.ui.Separator())
    container.add_item(discord.ui.TextDisplay(
        f"### {EMOJI_STATS} STATISTIK KENKAISUU STORE\n"
        f"{EMOJI_TOTAL_ORDER} **Total Order :** {total_orders}\n"
        f"{EMOJI_TOTAL_PROFIT} **Total Profit :** `{format_rupiah(total_profit)}`\n"
        f"{EMOJI_BUYER_TOTAL} **Buyer Total :** {total_buyers}"
    ))
    container.add_item(discord.ui.Separator())

    prev_btn = discord.ui.Button(label="◀", style=discord.ButtonStyle.secondary, disabled=page <= 1)
    mid_btn = discord.ui.Button(label=f"{page}/{total_pages}", style=discord.ButtonStyle.secondary, disabled=True)
    next_btn = discord.ui.Button(label="▶", style=discord.ButtonStyle.secondary, disabled=page >= total_pages)
    prev_btn.callback = _stats_nav_callback(page - 1)
    next_btn.callback = _stats_nav_callback(page + 1)
    container.add_item(discord.ui.ActionRow(prev_btn, mid_btn, next_btn))

    layout.add_item(container)
    return layout, file


def _stats_nav_callback(target_page: int):
    async def callback(interaction: discord.Interaction):
        await interaction.response.defer()
        data = load_stats_data()
        layout, file = await build_stats_panel(interaction.client, data, target_page)
        await interaction.edit_original_response(view=layout, attachments=[file])
    return callback


def load_stats_data() -> dict:
    if os.path.exists("stats_data.json"):
        with open("stats_data.json", "r") as f:
            return json.load(f)
    return {"total_orders": 0, "total_profit": 0, "buyers": {}}


async def refresh_stats_panel(client, guild):
    """Update pesan statistik (halaman 1). Kalau pesan lama tidak bisa diedit, kirim panel baru dan simpan ID-nya."""
    data = load_stats_data()
    channel_id = data.get("stats_channel_id")
    msg_id = data.get("stats_msg_id")
    if not channel_id or not msg_id:
        return

    channel = guild.get_channel(channel_id)
    if not channel:
        raise RuntimeError("Channel statistik tidak ditemukan")

    layout, file = await build_stats_panel(client, data, 1)
    try:
        msg = await channel.fetch_message(msg_id)
        await msg.edit(content=None, embeds=[], attachments=[file], view=layout)
    except discord.HTTPException:
        file.reset()
        new_msg = await channel.send(view=layout, file=file)
        data["stats_msg_id"] = new_msg.id
        with open("stats_data.json", "w") as f:
            json.dump(data, f, indent=4)


async def auto_update_stats(bot_obj, guild):
    await refresh_stats_panel(bot_obj, guild)


# ==========================================
# MODAL POP-UP & VIEW VOUCH UNTUK DM PEMBELI
# ==========================================
# ==========================================
# HELPER COMPONENTS V2 (TAMPILAN PANEL: LOG, TESTI, VOUCH)
# ==========================================
def build_panel(title: str, body: str) -> discord.ui.LayoutView:
    """Panel kotak: judul, garis, isi, garis."""
    view = discord.ui.LayoutView(timeout=None)
    container = discord.ui.Container()
    container.add_item(discord.ui.TextDisplay(f"## {title}"))
    container.add_item(discord.ui.Separator())
    container.add_item(discord.ui.TextDisplay(body))
    view.add_item(container)
    return view


TICKET_CLAIMS_FILE = "ticket_claims.json"


def load_ticket_claims() -> dict:
    try:
        with open(TICKET_CLAIMS_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_ticket_claims(data: dict):
    with open(TICKET_CLAIMS_FILE, "w") as f:
        json.dump(data, f)


def quote_text(text: str) -> str:
    """Ubah teks user jadi blockquote (setiap baris diawali '> ')."""
    lines = [f"> {line}" if line.strip() else ">" for line in text.splitlines()]
    return "\n".join(lines) or ">"


def build_notice_layout(text: str) -> discord.ui.LayoutView:
    """Pesan konfirmasi sederhana dalam satu panel."""
    view = discord.ui.LayoutView(timeout=None)
    container = discord.ui.Container()
    container.add_item(discord.ui.TextDisplay(text))
    view.add_item(container)
    return view


def build_order_log_layout(log_num, buyer_mention, buyer_avatar, product,
                           status_text, status_emoji, price, category) -> discord.ui.LayoutView:
    """Log order: judul, garis, detail + foto profil buyer di kanan, garis, footer."""
    details = (
        f"{EMOJI_USER} **User :** {buyer_mention}\n"
        f"{EMOJI_PRODUCT} **Product :** `{product}`\n"
        f"{EMOJI_STATUS} **Status :** `{status_text}` {status_emoji}\n"
        f"{EMOJI_PRICE} **Price :** `{price}`\n"
        f"{EMOJI_CATEGORY} **Category :** `{category}`"
    )
    view = discord.ui.LayoutView(timeout=None)
    container = discord.ui.Container()
    container.add_item(discord.ui.TextDisplay(f"## 🛒 ORDER LOGS 🛒\nOrder logs ke #{log_num}"))
    container.add_item(discord.ui.Separator())
    body = discord.ui.TextDisplay(details)
    if buyer_avatar:
        container.add_item(discord.ui.Section(body, accessory=discord.ui.Thumbnail(buyer_avatar)))
    else:
        container.add_item(body)
    container.add_item(discord.ui.Separator())
    container.add_item(discord.ui.TextDisplay("Thankyou for shopping in KENKAISUU STORE!"))
    view.add_item(container)
    return view


async def refresh_order_log(log_channel, msg_id, view):
    """Edit log order yang sudah ada. Kalau gagal (misalnya log lama masih berformat embed,
    atau pesan sudah terhapus), kirim log baru dan kembalikan pesan barunya."""
    try:
        msg = await log_channel.fetch_message(msg_id)
        return await msg.edit(content=None, embeds=[], view=view)
    except discord.HTTPException:
        return await log_channel.send(view=view)


def build_vouch_layout(vouch_num, user, product, stars_str, review) -> discord.ui.LayoutView:
    """Post ulasan di channel vouch: header + foto profil di kanan, garis, isi ulasan."""
    head = discord.ui.TextDisplay(
        f"## {EMOJI_STAR} BUYER VOUCH! #{vouch_num}\n"
        f"{EMOJI_USER} **User :** {user.mention}\n"
        f"{EMOJI_PRODUCT} **Product :** `{product}`\n"
        f"{EMOJI_RATING} **Rating :** {stars_str}"
    )
    view = discord.ui.LayoutView(timeout=None)
    container = discord.ui.Container()
    container.add_item(discord.ui.Section(head, accessory=discord.ui.Thumbnail(user.display_avatar.url)))
    container.add_item(discord.ui.Separator())
    container.add_item(discord.ui.TextDisplay(quote_text(review)))
    view.add_item(container)
    return view


class VouchModal(discord.ui.Modal, title="⭐ Form Ulasan Pembeli"):
    product_name = discord.ui.TextInput(
        label="Nama Produk / Layanan",
        placeholder="Contoh: Robux Visend / Jasa Middleman",
        required=True
    )
    rating = discord.ui.TextInput(
        label="Rating (1 - 5 Bintang)",
        placeholder="5",
        min_length=1,
        max_length=1,
        required=True
    )
    review = discord.ui.TextInput(
        label="Ulasan Anda",
        style=discord.TextStyle.paragraph,
        placeholder="Tuliskan pengalaman belanja/rekber kamu di sini...",
        required=True
    )

    def __init__(self, guild_id: int):
        super().__init__()
        self.guild_id = guild_id

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.client.get_guild(self.guild_id)
        if not guild:
            await interaction.response.send_message("❌ Server tidak ditemukan.", ephemeral=True)
            return

        vouch_channel = guild.get_channel(VOUCH_CHANNEL_ID)

        try:
            with open("vouch_counter.json", "r") as f:
                v_data = json.load(f)
                vouch_num = v_data.get("count", 4048)
        except FileNotFoundError:
            vouch_num = 4048

        r_val = self.rating.value.strip()
        num_stars = int(r_val) if r_val.isdigit() and 1 <= int(r_val) <= 5 else 5
        stars_str = EMOJI_STAR * num_stars

        layout_vouch = build_vouch_layout(
            vouch_num, interaction.user, self.product_name.value, stars_str, self.review.value
        )
        if vouch_channel:
            await vouch_channel.send(view=layout_vouch)

        with open("vouch_counter.json", "w") as f:
            json.dump({"count": vouch_num + 1}, f)

        await interaction.response.send_message(
            view=build_notice_layout("## ✅ Terima kasih!\nUlasan kamu berhasil dikirim ke server. 🎉"),
            ephemeral=True
        )


class DMVouchLayout(discord.ui.LayoutView):
    """Panel DM setelah transaksi selesai. Tombol ulasan ada di dalam panel."""
    def __init__(self, guild_id: int):
        super().__init__(timeout=None)
        self.guild_id = guild_id

        btn = discord.ui.Button(
            label="Beri Ulasan / Feedback",
            style=discord.ButtonStyle.primary,
            emoji="📝",
            custom_id="btn_dm_vouch"
        )
        btn.callback = self.on_vouch

        container = discord.ui.Container()
        container.add_item(discord.ui.TextDisplay("## 💬 Terima kasih telah berbelanja!"))
        container.add_item(discord.ui.Separator())
        container.add_item(discord.ui.TextDisplay(
            "Transaksi kamu telah selesai. Silakan klik tombol di bawah ini untuk memberikan ulasan kamu ya: ✨"
        ))
        container.add_item(discord.ui.Separator())
        container.add_item(discord.ui.ActionRow(btn))
        self.add_item(container)

    async def on_vouch(self, interaction: discord.Interaction):
        await interaction.response.send_modal(VouchModal(guild_id=self.guild_id))


# ==========================================
# 🆕 KONTROL TIKET (KLAIM & TUTUP TIKET)
# ==========================================
def ticket_welcome(tipe: str, mention: str):
    """(judul, isi) panel sambutan untuk tiap jenis tiket."""
    if tipe == "middleman":
        return (
            "🤝 TIKET JASA MIDDLEMAN / REKBER",
            f"Halo {mention}!\n"
            "Silakan cantumkan format transaksi di bawah ini:\n\n"
            "• **Penjual & Pembeli:**\n"
            "• **Barang / Nominal:**\n"
            "• **Nominal Transaksi:**\n\n"
            "Admin / Middleman akan segera merespons."
        )
    if tipe == "ask":
        return (
            f"{EMOJI_ASK} TIKET ASK / TANYA PRODUK",
            f"Halo {mention}!\n"
            "Silakan tulis pertanyaanmu seputar produk **Kenkaisuu Store** di sini. "
            "Admin akan segera merespons."
        )
    return (
        "🎫 TIKET ORDER ROBUX VISEND",
        f"Halo {mention}!\n"
        "Silakan ketik **Username Roblox** dan nominal Robux yang ingin kamu beli di sini. "
        "Admin akan segera merespons."
    )


class TicketPanelLayout(discord.ui.LayoutView):
    """Panel di dalam tiket: sambutan, status klaim, dan tombol klaim/tutup di dalam kotak."""
    def __init__(self, tipe: str = "visend", buyer_mention: str = "", claimed_by: int = None):
        super().__init__(timeout=None)
        title, body = ticket_welcome(tipe, buyer_mention)

        if claimed_by:
            status = f"**Ditangani oleh** <@{claimed_by}>"
            claim_label, claim_style = "Lepas Klaim", discord.ButtonStyle.secondary
        else:
            status = f"{EMOJI_PASIR} **Status:** Belum diklaim, menunggu admin."
            claim_label, claim_style = "Klaim Tiket", discord.ButtonStyle.success

        claim_btn = discord.ui.Button(
            label=claim_label, style=claim_style, emoji=EMOJI_KLAIM, custom_id="btn_claim_ticket"
        )
        claim_btn.callback = self.on_claim

        close_btn = discord.ui.Button(
            label="Tutup Tiket", style=discord.ButtonStyle.danger, emoji=EMOJI_TUTUP, custom_id="btn_close_ticket"
        )
        close_btn.callback = self.on_close

        container = discord.ui.Container()
        container.add_item(discord.ui.TextDisplay(f"## {title}\n{body}"))
        container.add_item(discord.ui.Separator())
        container.add_item(discord.ui.TextDisplay(status))
        container.add_item(discord.ui.Separator())
        container.add_item(discord.ui.TextDisplay(f"{EMOJI_SERU} *Gunakan tombol di bawah untuk Mengklaim atau Menutup Tiket.*"))
        container.add_item(discord.ui.ActionRow(claim_btn, close_btn))
        self.add_item(container)

    @staticmethod
    def _rebuild(rec: dict) -> discord.ui.LayoutView:
        return TicketPanelLayout(
            tipe=rec.get("tipe", "visend"),
            buyer_mention=f"<@{rec.get('buyer_id')}>",
            claimed_by=rec.get("claimed_by"),
        )

    async def on_claim(self, interaction: discord.Interaction):
        claims = load_ticket_claims()
        key = str(interaction.channel.id)
        rec = claims.get(key)
        user = interaction.user

        if not rec:
            await interaction.response.send_message("❌ Data tiket ini tidak ditemukan.", ephemeral=True)
            return

        if rec.get("claimed_by") is None:
            # Klaim: hanya staff/admin
            if not user.guild_permissions.manage_channels:
                await interaction.response.send_message("❌ Hanya Admin atau Staff yang dapat mengklaim tiket!", ephemeral=True)
                return
            rec["claimed_by"] = user.id
            claims[key] = rec
            save_ticket_claims(claims)
            await interaction.response.edit_message(view=self._rebuild(rec))
            await interaction.channel.send(f"{EMOJI_KLAIM} Tiket ini diklaim oleh {user.mention} dan akan ditangani! {EMOJI_SPARKLES}")
        else:
            # Lepas klaim: pengklaim sendiri atau admin
            if user.id != rec["claimed_by"] and not user.guild_permissions.administrator:
                await interaction.response.send_message(
                    f"❌ Tiket ini sudah ditangani oleh <@{rec['claimed_by']}>. Hanya dia atau Admin yang bisa melepas klaim.",
                    ephemeral=True
                )
                return
            rec["claimed_by"] = None
            claims[key] = rec
            save_ticket_claims(claims)
            await interaction.response.edit_message(view=self._rebuild(rec))
            await interaction.channel.send(f"{EMOJI_GEMBOK} Klaim tiket dilepas oleh {user.mention}. Tiket kembali menunggu admin.")

    async def on_close(self, interaction: discord.Interaction):
        claims = load_ticket_claims()
        key = str(interaction.channel.id)
        rec = claims.get(key, {})
        user = interaction.user
        claimed_by = rec.get("claimed_by")
        buyer_id = rec.get("buyer_id")

        # Kalau sudah diklaim: hanya pengklaim, pembeli, atau admin yang boleh menutup
        if claimed_by and user.id not in (claimed_by, buyer_id) and not user.guild_permissions.administrator:
            await interaction.response.send_message(
                f"❌ Tiket ini sedang ditangani oleh <@{claimed_by}>. Hanya dia, pembeli, atau Admin yang bisa menutupnya.",
                ephemeral=True
            )
            return

        # Tiket order: tandai Failed di log (kalau belum Success)
        await _mark_order_failed(interaction.guild, interaction.client, key)

        # Tiket order saja yang minta ulasan (tiket Ask tidak)
        if buyer_id and not rec.get("is_ask", False):
            try:
                buyer = interaction.guild.get_member(buyer_id) or await interaction.client.fetch_user(buyer_id)
                await buyer.send(view=DMVouchLayout(guild_id=interaction.guild.id))
            except discord.HTTPException:
                pass

        claims.pop(key, None)
        save_ticket_claims(claims)

        await interaction.response.send_message(f"{EMOJI_TUTUP} Tiket telah ditutup. Channel ini akan dihapus dalam 3 detik...", ephemeral=True)
        await asyncio.sleep(3)
        await interaction.channel.delete()


async def _mark_order_failed(guild, client, channel_id_str: str):
    """Kalau tiket ini order yang belum Success, ubah log-nya jadi Failed dan hapus dari daftar aktif."""
    try:
        with open("active_orders.json", "r") as f:
            active_orders = json.load(f)
    except FileNotFoundError:
        return
    if channel_id_str not in active_orders:
        return

    info = active_orders[channel_id_str]
    if info.get("status") != "Success":
        log_channel = guild.get_channel(ORDER_LOG_CHANNEL_ID)
        if log_channel:
            try:
                buyer = guild.get_member(info["buyer_id"]) or await client.fetch_user(info["buyer_id"])
                layout_failed = build_order_log_layout(
                    info["log_num"],
                    buyer.mention if buyer else f"<@{info['buyer_id']}>",
                    buyer.display_avatar.url if buyer else None,
                    info["product"], "Failed", STATUS_FAILED, "Cancelled", info["category"]
                )
                await refresh_order_log(log_channel, info["msg_id"], layout_failed)
            except Exception as e:
                print(f"Gagal update log ke Failed: {e}")

    del active_orders[channel_id_str]
    with open("active_orders.json", "w") as f:
        json.dump(active_orders, f)


# ==========================================
# KOMPONEN UI UNTUK PING & ROBLOX
# ==========================================
def ping_status(ms: int) -> str:
    if ms < 100:
        return "🟢 Sangat Lancar"
    if ms < 200:
        return "🟡 Cukup Baik"
    return "🔴 Lambat"


class PingLayout(discord.ui.LayoutView):
    """Panel !ping: latensi + tombol uji ulang di dalam kotak."""
    def __init__(self, latency_ms: int):
        super().__init__(timeout=None)
        btn = discord.ui.Button(
            label="Uji Ulang Latensi",
            style=discord.ButtonStyle.primary,
            emoji="🔄",
            custom_id="btn_ping_refresh"
        )
        btn.callback = self.on_refresh

        container = discord.ui.Container()
        container.add_item(discord.ui.TextDisplay(
            "## 🏓 Pong! Status Koneksi Bot\n"
            "Berikut adalah latensi koneksi bot secara *real-time*:"
        ))
        container.add_item(discord.ui.Separator())
        container.add_item(discord.ui.TextDisplay(
            f"⚡ **Websocket Latency**\n`{latency_ms} ms`\n\n"
            f"📡 **Status Server**\n`{ping_status(latency_ms)}`"
        ))
        container.add_item(discord.ui.Separator())
        container.add_item(discord.ui.ActionRow(btn))
        self.add_item(container)

    async def on_refresh(self, interaction: discord.Interaction):
        await interaction.response.edit_message(view=PingLayout(round(interaction.client.latency * 1000)))


# ==========================================
# PANEL PRODUK -> PRICELIST -> TIKET
# ==========================================
PANEL_COLOR = None  # 🎨 None = panel bersih tanpa garis warna di kiri. Mau garis warna? isi mis. 0x5865F2


def build_pricelist_parts(tipe: str):
    """Mengembalikan (judul, isi, petunjuk) untuk panel pricelist.
    Tiap bagian dipisah garis di dalam panel."""
    if tipe == "middleman":
        title = f"## {EMOJI_MIDDLEMAN} JASA MIDDLEMAN / REKBER"
        body = (
            f"### {EMOJI_PRICELIST} __LIST BIAYA MIDDLEMAN (FEE)__\n"
            f"**For Qris** {EMOJI_EWALLET}\n"
            "• `0 - 49K` = **1K**\n"
            "• `50 - 99K` = **2K**\n"
            "• `100 - 149K` = **3K**\n"
            "• `150 - 199K` = **4K**\n"
            "• `200 - 599K` = **5K**\n"
            "• `600K+` = **10K**\n\n"
            "**Seabank to Seabank**\n"
            "• `All Nominal` = **2K**"
        )
        hint = "-# ✦ Klik tombol di bawah untuk membuat tiket middleman"
    elif tipe == "ask":
        title = f"## {EMOJI_ASK} ASK / TANYA PRODUK"
        body = (
            "### __APA ITU ASK?__\n"
            "Ask adalah layanan tanya-jawab seputar produk **Kenkaisuu Store**. "
            "Kalau ada yang masih bingung sebelum order, tanyakan dulu di sini.\n\n"
            "**Kamu bisa bertanya tentang:**\n"
            "• Ketersediaan stok & rate Robux\n"
            "• Cara order & metode pembayaran\n"
            "• Cara kerja & biaya jasa Middleman\n"
            "• Kendala atau pertanyaan lain seputar produk store\n\n"
            "✦ *Pertanyaanmu dijawab staff langsung di tiket pribadi*\n"
            "✦ *Jam operasional: Senin - Minggu, 09:00 - 22:00 WIB*"
        )
        hint = "-# ✦ Klik tombol di bawah untuk membuat tiket ask"
    else:
        title = f"## {EMOJI_ROBUX} ROBUX VIA USERNAME"
        body = (
            f"### {EMOJI_PRICELIST} __PRICELIST ROBUX VIA USERNAME__\n"
            f"• 100 {EMOJI_ROBUX} — `Rp16.000`\n"
            f"• 200 {EMOJI_ROBUX} — `Rp32.000`\n"
            f"• 300 {EMOJI_ROBUX} — `Rp48.000`\n"
            f"• 400 {EMOJI_ROBUX} — `Rp64.000`\n"
            f"• 500 {EMOJI_ROBUX} — `Rp80.000`\n"
            f"• 1000 {EMOJI_ROBUX} — `Rp160.000`\n\n"
            "✦ *Rate 160 / Robux*\n"
            "✦ *Proses cepat, cukup cantumkan Username Roblox*"
        )
        hint = "-# ✦ Klik tombol di bawah untuk membuat tiket order"
    return title, body, hint


async def create_ticket_channel(interaction: discord.Interaction, tipe: str):
    guild = interaction.guild
    user = interaction.user
    category = guild.get_channel(CATEGORY_MARKET_ID)

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }

    if tipe == "middleman":
        channel_name = f"🤝・ticket-{user.name}-midman"
        prod_name = "Jasa Middleman"
        cat_name = "Manual"
    elif tipe == "ask":
        channel_name = f"❓・ticket-{user.name}-ask"
        prod_name = "Ask"
        cat_name = "Ask"
    else:
        channel_name = f"🛒・ticket-{user.name}-visend"
        prod_name = "Robux Visend"
        cat_name = "Manual"

    ticket_channel = await guild.create_text_channel(
        name=channel_name,
        category=category,
        overwrites=overwrites
    )

    # Catat data tiket (pembeli, jenis, pengklaim) supaya tombol tetap bisa dipakai setelah bot restart
    claims = load_ticket_claims()
    claims[str(ticket_channel.id)] = {
        "tipe": tipe,
        "buyer_id": user.id,
        "is_ask": tipe == "ask",
        "claimed_by": None,
    }
    save_ticket_claims(claims)

    await interaction.response.send_message(
        f"{EMOJI_CENTANG} Tiket berhasil dibuat! Silakan buka {ticket_channel.mention} untuk melanjutkan.",
        ephemeral=True
    )

    await ticket_channel.send(view=TicketPanelLayout(tipe=tipe, buyer_mention=user.mention))

    # Tiket Ask hanya tanya-jawab, bukan transaksi: tidak dicatat di Order Logs
    if tipe == "ask":
        return

    try:
        with open("order_log_counter.json", "r") as f:
            data = json.load(f)
            log_num = data.get("count", 4048)
    except FileNotFoundError:
        log_num = 4048

    log_channel = guild.get_channel(ORDER_LOG_CHANNEL_ID)

    layout_log = build_order_log_layout(
        log_num, user.mention, user.display_avatar.url, prod_name,
        "Pending", STATUS_PENDING, "Pending", cat_name
    )

    if log_channel:
        log_msg = await log_channel.send(view=layout_log)

        try:
            with open("active_orders.json", "r") as f:
                active_orders = json.load(f)
        except FileNotFoundError:
            active_orders = {}

        active_orders[str(ticket_channel.id)] = {
            "msg_id": log_msg.id,
            "buyer_id": user.id,
            "product": prod_name,
            "category": cat_name,
            "log_num": log_num,
            "status": "Pending"
        }

        with open("active_orders.json", "w") as f:
            json.dump(active_orders, f)

    with open("order_log_counter.json", "w") as f:
        json.dump({"count": log_num + 1}, f)


async def show_pricelist(interaction: discord.Interaction, tipe: str):
    """Tampilkan pricelist. Dari panel publik -> pesan ephemeral baru;
    dari pesan ephemeral (setelah klik 'Daftar Produk') -> edit di tempat."""
    layout = PricelistLayout(tipe)
    if interaction.message is not None and interaction.message.flags.ephemeral:
        await interaction.response.edit_message(view=layout)
    else:
        await interaction.response.send_message(view=layout, ephemeral=True)


class ProductPanelLayout(discord.ui.LayoutView):
    """Panel utama: judul + tombol produk, semuanya di dalam satu kotak.
    Tombol di sini CUMA pemicu pricelist, belum membuat tiket."""
    def __init__(self):
        super().__init__(timeout=None)
        container = discord.ui.Container(accent_colour=PANEL_COLOR)
        container.add_item(discord.ui.TextDisplay(f"## {EMOJI_ROBUX} Produk Kenkaisuu Store"))
        container.add_item(discord.ui.Separator())
        container.add_item(discord.ui.TextDisplay(
            "3 produk · Klik tombol produk untuk melihat pricelist & info order.\n\n"
            "**Cara order:**\n"
            "**1.** Pilih produk di bawah. Tombol ini **hanya membuka pricelist / info**, "
            "**belum membuat tiket**.\n"
            "**2.** Baca pricelist atau info produknya.\n"
            "**3.** Klik tombol **Buat Tiket** di halaman pricelist untuk membuka tiket."
        ))
        container.add_item(discord.ui.Separator())

        # custom_id dipertahankan dari versi lama (btn_visend / btn_middleman)
        for tipe, label, emoji, cid in (
            ("visend",    "Robux Visend", EMOJI_ROBUX,     "btn_visend"),
            ("middleman", "Middleman",    EMOJI_MIDDLEMAN, "btn_middleman"),
            ("ask",       "Ask",          EMOJI_ASK,       "btn_ask"),
        ):
            btn = discord.ui.Button(
                label=label, emoji=emoji, custom_id=cid,
                style=discord.ButtonStyle.secondary
            )
            btn.callback = self._make_callback(tipe)
            row = discord.ui.ActionRow()
            row.add_item(btn)
            container.add_item(row)

        self.add_item(container)

    @staticmethod
    def _make_callback(tipe: str):
        async def callback(interaction: discord.Interaction):
            await show_pricelist(interaction, tipe)
        return callback


class PricelistLayout(discord.ui.LayoutView):
    """Pricelist + tombol ASLI pembuat tiket, semuanya di dalam satu kotak."""
    def __init__(self, tipe: str):
        super().__init__(timeout=None)
        self.tipe = tipe

        if tipe == "middleman":
            order_label, order_emoji = "Buat Tiket Middleman", EMOJI_MIDDLEMAN
        elif tipe == "ask":
            order_label, order_emoji = "Buat Tiket Ask", EMOJI_ASK
        else:
            order_label, order_emoji = "Buat Tiket Order", EMOJI_ROBUX

        btn_order = discord.ui.Button(
            label=order_label, emoji=order_emoji,
            style=discord.ButtonStyle.primary,
            custom_id=f"create_ticket_{tipe}"
        )
        btn_order.callback = self.on_order

        btn_back = discord.ui.Button(
            label="Daftar Produk", emoji="⬅️",
            style=discord.ButtonStyle.secondary,
            custom_id=f"back_products_{tipe}"
        )
        btn_back.callback = self.on_back

        container = discord.ui.Container(accent_colour=PANEL_COLOR)
        title, body, hint = build_pricelist_parts(tipe)
        container.add_item(discord.ui.TextDisplay(title))
        container.add_item(discord.ui.Separator())
        container.add_item(discord.ui.TextDisplay(body))
        container.add_item(discord.ui.Separator())
        container.add_item(discord.ui.TextDisplay(hint))
        container.add_item(discord.ui.Separator())
        container.add_item(discord.ui.ActionRow(btn_order, btn_back))
        self.add_item(container)

    async def on_order(self, interaction: discord.Interaction):
        await create_ticket_channel(interaction, self.tipe)

    async def on_back(self, interaction: discord.Interaction):
        await interaction.response.edit_message(view=ProductPanelLayout())


# ==========================================
# EVENT, AUTO-RESPONDER & SLASH COMMAND SYNC
# ==========================================
@bot.event
async def on_ready():
    bot.add_view(ProductPanelLayout())
    bot.add_view(PricelistLayout("visend"))
    bot.add_view(PricelistLayout("middleman"))
    bot.add_view(PricelistLayout("ask"))
    bot.add_view(TicketPanelLayout())
    bot.add_view(PingLayout(0))
    try:
        guild = discord.Object(id=GUILD_ID)

        bot.tree.copy_global_to(guild=guild)
        bot.tree.clear_commands(guild=None)

        await bot.tree.sync(guild=None)
        synced = await bot.tree.sync(guild=guild)

        print(f"✅ Berhasil! {len(synced)} Slash Command aktif tepat di server! 🚀")
    except Exception as e:
        print(f"❌ Gagal Sync Slash Command: {e}")
    print(f'🤖 Bot {bot.user} berhasil online! ✨')


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    msg_lower = message.content.lower().strip()

    # 🤖 AUTO-RESPONDER FAQ SEDERHANA
    if msg_lower in ["qris", "payment", "pembayaran"]:
        await message.channel.send("💳 **Metode Pembayaran Kenkaisuu Store:**\n• QRIS All Payment (Gopay/OVO/Dana/Bank)\n• SeaBank\n\n*Nominal & QRIS akan diberikan Admin di dalam tiket!* 🛡️")
    elif msg_lower in ["buka", "jam buka", "operational"]:
        await message.channel.send("⏰ **Jam Operasional Store:**\n• Senin - Minggu: 09:00 - 22:00 WIB ⚡")

    await bot.process_commands(message)


# ==========================================
# SLASH COMMAND (/TESTI)
# ==========================================
@bot.tree.command(name="testi", description="Kirim testimoni transaksi baru ke channel testimoni")
@app_commands.describe(
    buyer="Pilih Pembeli/Customer",
    produk="Nama Produk (contoh: Robux Visend / Middleman)",
    harga="Harga (contoh: 150.000)",
    foto_1="Foto Bukti 1 (Utama)",
    foto_2="Foto Bukti 2 (Opsional)"
)
async def slash_testi(
    interaction: discord.Interaction,
    buyer: discord.Member,
    produk: str,
    harga: str,
    foto_1: discord.Attachment,
    foto_2: discord.Attachment = None
):
    await interaction.response.defer(ephemeral=True)

    testi_channel = interaction.guild.get_channel(TESTIMONY_CHANNEL_ID)
    if not testi_channel:
        await interaction.followup.send("❌ Channel testimoni tidak ditemukan! Pastikan ID channel sudah benar.", ephemeral=True)
        return

    try:
        with open("testi_data.json", "r") as f:
            testi_num = json.load(f).get("count", 1684)
    except FileNotFoundError:
        testi_num = 1684

    formatted_price = harga if harga.lower().startswith("rp") else f"Rp {harga}"
    GRID_URL = "https://discord.com"

    file1 = await foto_1.to_file(filename="bukti1.png")
    files = [file1]
    gallery_items = [discord.MediaGalleryItem(media="attachment://bukti1.png")]

    if foto_2:
        files.append(await foto_2.to_file(filename="bukti2.png"))
        gallery_items.append(discord.MediaGalleryItem(media="attachment://bukti2.png"))

    header = discord.ui.TextDisplay(
        f"## `TESTIMONI #{testi_num}`\n"
        f"{EMOJI_USER} **Buyer :** {buyer.mention}\n"
        f"{EMOJI_PRODUCT} **Product :** {produk}\n"
        f"{EMOJI_PRICE} **Price :** `{formatted_price}`\n"
        f"{EMOJI_RATING} **Reviews :** `#{testi_num}`"
    )
    layout = discord.ui.LayoutView(timeout=None)
    container = discord.ui.Container()
    container.add_item(discord.ui.Section(header, accessory=discord.ui.Thumbnail(buyer.display_avatar.url)))
    container.add_item(discord.ui.Separator())
    container.add_item(discord.ui.MediaGallery(*gallery_items))
    container.add_item(discord.ui.Separator())
    container.add_item(discord.ui.TextDisplay("Thankyou for shopping in KENKAISUU STORE!"))
    layout.add_item(container)

    await testi_channel.send(view=layout, files=files)

    with open("testi_data.json", "w") as f:
        json.dump({"count": testi_num + 1}, f)

    await interaction.followup.send(f"✅ Testimoni berhasil dikirim dengan gambar jernih ke {testi_channel.mention}! 🎉", ephemeral=True)


# ==========================================
# COMMAND MODERASI & USER/BOT INFO
# ==========================================
@bot.command(name="clear", aliases=["purge"])
@commands.has_permissions(manage_messages=True)
async def clear_command(ctx, amount: int = 10):
    """Menghapus sejumlah pesan di channel/tiket saat ini ✨"""
    if amount <= 0:
        await ctx.send("❌ Jumlah pesan yang ingin dihapus harus lebih dari 0!")
        return

    deleted = await ctx.channel.purge(limit=amount + 1)
    msg = await ctx.send(f"🧹 Berhasil menghapus **{len(deleted) - 1}** pesan!")
    await asyncio.sleep(3)
    try:
        await msg.delete()
    except discord.NotFound:
        pass


@bot.command(name="userinfo", aliases=["ui", "user"])
async def userinfo_command(ctx, member: discord.Member = None):
    """Mengecek info detail user/buyer (umur akun, join date, roles) 👤"""
    target = member or ctx.author
    roles = [role.mention for role in target.roles if role.name != "@everyone"]
    roles_str = ", ".join(roles) if roles else "Tidak ada role"

    created_at = target.created_at.strftime("%d/%m/%Y %H:%M:%S")
    joined_at = target.joined_at.strftime("%d/%m/%Y %H:%M:%S") if target.joined_at else "Tidak diketahui"

    embed = discord.Embed(
        title=f"👤 Profil Pengguna - {target.name}",
        color=0x2b2d31
    )
    embed.set_thumbnail(url=target.display_avatar.url)
    embed.add_field(name="🆔 User ID", value=f"`{target.id}`", inline=True)
    embed.add_field(name="🏷️ Display Name", value=target.display_name, inline=True)
    embed.add_field(name="📅 Akun Dibuat", value=f"`{created_at}`", inline=False)
    embed.add_field(name="📥 Bergabung Server", value=f"`{joined_at}`", inline=False)
    embed.add_field(name=f"🎭 Roles ({len(roles)})", value=roles_str, inline=False)

    await ctx.send(embed=embed)


@bot.command(name="botinfo")
async def botinfo_command(ctx):
    """Melihat statistik performa dan uptime bot 🤖"""
    uptime_seconds = int(time.time() - START_TIME)
    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    days, hours = divmod(hours, 24)

    uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"
    ws_latency = round(bot.latency * 1000)
    total_members = sum(g.member_count for g in bot.guilds)

    head = discord.ui.TextDisplay(
        f"## 🤖 Informasi & Status Bot Store\n"
        f"👑 **Nama Bot:** `{bot.user.name}`"
    )
    layout = discord.ui.LayoutView(timeout=None)
    container = discord.ui.Container()
    container.add_item(discord.ui.Section(head, accessory=discord.ui.Thumbnail(bot.user.display_avatar.url)))
    container.add_item(discord.ui.Separator())
    container.add_item(discord.ui.TextDisplay(
        f"⚡ **Latency:** `{ws_latency} ms`  •  ⏳ **Uptime:** `{uptime_str}`\n"
        f"📊 **Server:** `{len(bot.guilds)}`  •  👥 **Member:** `{total_members}`"
    ))
    layout.add_item(container)

    await ctx.send(view=layout)


# ==========================================
# /ASK - FAQ SEPUTAR ROBLOX (tanpa API, jawaban tersimpan di kode)
# ==========================================
ROBLOX_FAQ = [
    {
        "key": "limited",
        "judul": "Apa itu Limited item?",
        "kata_kunci": ["limited", "langka", "item langka", "harga item", "unique"],
        "jawaban": (
            "**Limited** adalah item langka di Roblox dengan jumlah yang terbatas. "
            "Item ini sudah tidak dijual lagi di toko, jadi hanya bisa didapat lewat pemain lain di marketplace atau trade.\n\n"
            "✦ Harganya ditentukan oleh permintaan pemain, jadi nilainya bisa naik atau turun.\n"
            "✦ Ada juga **Limited U** (Unique), yaitu Limited yang hanya dimiliki satu orang di seluruh Roblox.\n"
            "✦ Untuk cek perkiraan nilai item, pemain biasanya memakai situs komunitas pihak ketiga seperti Rolimons."
        ),
    },
    {
        "key": "robux",
        "judul": "Apa itu Robux?",
        "kata_kunci": ["robux", "rbx", "mata uang", "koin"],
        "jawaban": (
            "**Robux** adalah mata uang virtual di Roblox.\n\n"
            "✦ Dipakai untuk membeli item avatar, Game Pass, dan item di dalam game.\n"
            "✦ Dibeli dengan uang asli lewat menu Robux di Roblox.\n"
            "✦ Cek harga Robux di toko ini dengan perintah `!stock`."
        ),
    },
    {
        "key": "premium",
        "judul": "Apa itu Roblox Premium?",
        "kata_kunci": ["premium", "langganan", "membership"],
        "jawaban": (
            "**Roblox Premium** adalah langganan berbayar di Roblox.\n\n"
            "✦ Member mendapat Robux setiap bulan sesuai paket.\n"
            "✦ Member mendapat diskon dan keuntungan lain di marketplace.\n"
            "✦ Harga dan paket bisa berbeda di tiap negara, cek menu Premium di akun Roblox."
        ),
    },
    {
        "key": "devex",
        "judul": "Apa itu DevEx?",
        "kata_kunci": ["devex", "developer exchange", "cairkan", "tarik robux", "cashout"],
        "jawaban": (
            "**DevEx** (Developer Exchange) adalah program dari Roblox yang memungkinkan kreator game menukar Robux hasil penjualan menjadi uang asli.\n\n"
            "✦ Ada syarat seperti usia, jumlah minimum Robux, dan verifikasi akun.\n"
            "✦ Syarat bisa berubah, cek dokumentasi resmi Roblox sebelum mengajukan."
        ),
    },
    {
        "key": "cara_robux",
        "judul": "Cara mendapatkan Robux yang resmi?",
        "kata_kunci": ["cara dapat robux", "robux gratis", "dapat robux", "dapetin robux"],
        "jawaban": (
            "Cara resmi mendapatkan Robux:\n\n"
            "✦ Membeli Robux atau berlangganan Roblox Premium.\n"
            "✦ Menjual item di marketplace jika kamu punya item.\n"
            "✦ Membuat game dengan Game Pass atau developer product, lalu mendapat bagian dari penjualannya.\n\n"
            "⚠️ Waspada dengan janji **Robux gratis** atau *generator* Robux. Hampir selalu penipuan."
        ),
    },
    {
        "key": "gamepass",
        "judul": "Apa itu Game Pass?",
        "kata_kunci": ["gamepass", "game pass", "gp"],
        "jawaban": (
            "**Game Pass** adalah item berbayar yang dibeli sekali dengan Robux dan memberi keuntungan tetap di game tertentu. "
            "Game Pass hanya berlaku di game yang membuatnya."
        ),
    },
    {
        "key": "trading",
        "judul": "Apa itu trading di Roblox?",
        "kata_kunci": ["trade", "trading", "tukar item", "tukar"],
        "jawaban": (
            "**Trading** adalah pertukaran item antar pemain di Roblox.\n\n"
            "✦ Trade hanya bisa dilakukan jika akun memenuhi syarat tertentu, dan syaratnya bisa berubah.\n"
            "✦ Cek nilai kedua item sebelum trade, dan jangan percaya janji tukar yang tidak jelas.\n"
            "✦ Untuk transaksi besar, pakai jasa middleman / rekber."
        ),
    },
    {
        "key": "studio",
        "judul": "Apa itu Roblox Studio?",
        "kata_kunci": ["studio", "bikin game", "buat game", "membuat game", "develop"],
        "jawaban": (
            "**Roblox Studio** adalah alat gratis untuk membuat game di Roblox.\n\n"
            "✦ Kode game ditulis dengan bahasa **Luau**, turunan dari Lua.\n"
            "✦ Unduh Roblox Studio dari situs resmi Roblox."
        ),
    },
    {
        "key": "grup",
        "judul": "Apa itu Group Roblox?",
        "kata_kunci": ["grup", "group", "rank", "komunitas"],
        "jawaban": (
            "**Group** adalah komunitas di Roblox yang punya anggota, rank (peran), dan halaman sosial.\n\n"
            "✦ Grup bisa memiliki game atau item, dan penjualannya bisa masuk ke grup."
        ),
    },
    {
        "key": "verified",
        "judul": "Apa itu akun Verified?",
        "kata_kunci": ["verified", "verifikasi", "verif", "email", "2fa"],
        "jawaban": (
            "Akun **Verified** adalah akun yang sudah memverifikasi email dan identitasnya di Roblox.\n\n"
            "✦ Verifikasi dibutuhkan untuk beberapa fitur, seperti trading atau DevEx.\n"
            "✦ Aktifkan juga verifikasi dua langkah (2-Step Verification) untuk keamanan."
        ),
    },
    {
        "key": "hacked",
        "judul": "Akun Roblox saya dibajak, apa yang harus dilakukan?",
        "kata_kunci": ["hack", "dibajak", "kena hack", "hacked", "akun hilang", "password"],
        "jawaban": (
            "Kalau akunmu dibajak, lakukan ini secepatnya:\n\n"
            "1. Ganti password akun.\n"
            "2. Aktifkan verifikasi dua langkah (2-Step Verification).\n"
            "3. Cek riwayat login dan perangkat, lalu keluarkan perangkat yang tidak dikenal.\n"
            "4. Hapus aplikasi atau situs pihak ketiga yang mencurigakan dari pengaturan akun.\n"
            "5. Jika tetap tidak bisa masuk, hubungi Roblox Support lewat situs resmi."
        ),
    },
    {
        "key": "penipuan",
        "judul": "Bagaimana menghindari penipuan di Roblox?",
        "kata_kunci": ["penipuan", "scam", "tipu", "penipu", "aman"],
        "jawaban": (
            "✦ **Jangan pernah** memberikan password atau kode verifikasi ke siapa pun, termasuk yang mengaku staff Roblox.\n"
            "✦ Jangan klik link yang menjanjikan Robux gratis atau hadiah.\n"
            "✦ Untuk transaksi besar, selalu pakai jasa middleman / rekber.\n"
            "✦ Kalau ada yang minta login lewat link asing, anggap itu penipuan."
        ),
    },
    {
        "key": "error_game",
        "judul": "Game Roblox tidak bisa dibuka atau error, kenapa?",
        "kata_kunci": ["error", "tidak bisa dibuka", "gagal load", "lag", "crash", "kick"],
        "jawaban": (
            "Coba langkah umum berikut:\n\n"
            "✦ Pastikan koneksi internet stabil.\n"
            "✦ Tutup dan buka lagi aplikasi Roblox, atau restart perangkat.\n"
            "✦ Perbarui aplikasi Roblox ke versi terbaru.\n"
            "✦ Cek apakah server Roblox sedang bermasalah.\n\n"
            "Kalau masih error, cari kode error-nya di halaman bantuan resmi Roblox."
        ),
    },
    {
        "key": "order_toko",
        "judul": "Cara order Robux di toko ini?",
        "kata_kunci": ["order", "beli", "pesan", "tiket", "harga robux", "pricelist"],
        "jawaban": (
            "✦ Buka panel produk di channel order, lalu pilih produk yang kamu mau.\n"
            "✦ Baca pricelist, lalu tekan **Buat Tiket**.\n"
            "✦ Admin akan membantu di dalam tiket. Cek stok dengan `!stock`."
        ),
    },
]

ASK_FOOTER = "-# Info ini bisa berubah. Untuk memastikan, cek sumber resmi Roblox."


def _ask_choices():
    return [app_commands.Choice(name=f["judul"][:100], value=f["key"]) for f in ROBLOX_FAQ[:25]]


def _find_faq(key: str):
    return next((f for f in ROBLOX_FAQ if f["key"] == key), None)


def _search_faq(query: str):
    q = query.lower().strip()
    if not q:
        return None
    best, best_score = None, 0
    for f in ROBLOX_FAQ:
        haystack = " ".join([f["judul"].lower()] + f["kata_kunci"])
        score = sum(1 for word in q.split() if word in haystack)
        if q in haystack:
            score += 2
        if score > best_score:
            best, best_score = f, score
    return best


def _ask_layout(faq: dict, user_name: str) -> discord.ui.LayoutView:
    layout = discord.ui.LayoutView(timeout=None)
    container = discord.ui.Container()
    container.add_item(discord.ui.TextDisplay(f"## 🎮 {faq['judul']}"))
    container.add_item(discord.ui.Separator())
    container.add_item(discord.ui.TextDisplay(faq["jawaban"]))
    container.add_item(discord.ui.TextDisplay(f"{ASK_FOOTER} • Ditanya oleh {user_name}"))
    layout.add_item(container)
    return layout


@bot.tree.command(name="ask", description="Tanya seputar Roblox (jawaban sudah tersimpan di bot)")
@app_commands.describe(
    topik="Pilih pertanyaan yang sering ditanyakan",
    cari="Atau ketik kata kunci, misalnya: limited, devex, hacked",
)
@app_commands.choices(topik=_ask_choices())
async def ask_slash(
    interaction: discord.Interaction,
    topik: app_commands.Choice[str] = None,
    cari: str = None,
):
    # Tanpa pilihan: tampilkan daftar topik yang tersedia
    if topik is None and not cari:
        daftar = "\n".join(f"✦ {f['judul']}" for f in ROBLOX_FAQ)
        layout = discord.ui.LayoutView(timeout=None)
        container = discord.ui.Container()
        container.add_item(discord.ui.TextDisplay("## 🎮 Tanya Seputar Roblox"))
        container.add_item(discord.ui.Separator())
        container.add_item(discord.ui.TextDisplay(
            f"Pilih topik di kolom `topik`, atau ketik kata kunci di kolom `cari`.\n\n{daftar}"
        ))
        layout.add_item(container)
        await interaction.response.send_message(view=layout, ephemeral=True)
        return

    faq = _find_faq(topik.value) if topik else _search_faq(cari)
    if faq is None:
        await interaction.response.send_message(
            f"❌ Maaf, aku belum punya jawaban untuk `{cari}`. Coba kata kunci lain, atau pilih topik di kolom `topik`.",
            ephemeral=True,
        )
        return

    await interaction.response.send_message(view=_ask_layout(faq, interaction.user.name))


# ==========================================
# PREFIX COMMANDS (STOCK SYSTEM & CALCULATOR)
# ==========================================
@bot.command(name="rbx")
async def rbx_tax_command(ctx, robux_bersih: int = None):
    if robux_bersih is None or robux_bersih <= 0:
        await ctx.send("❌ Format salah! Gunakan: `!rbx <jumlah>` (Contoh: `!rbx 500`)")
        return

    total_kirim = math.ceil(robux_bersih / 0.7)
    formatted_bersih = f"{robux_bersih:,}".replace(",", ".")
    formatted_total = f"{total_kirim:,}".replace(",", ".")
    
    embed = discord.Embed(
        title=f"{EMOJI_ROBUX} Roblox Tax Calculator",
        description=(
            f"Untuk mendapatkan **{formatted_bersih} Robux**\n"
            f"kamu harus mengirim **{formatted_total} Robux**"
        ),
        color=0x2b2d31
    )
    
    await ctx.send(embed=embed)


@bot.command(name="stock")
async def stock_command(ctx, nominal: int = None):
    current_stock = get_stock()
    order_channel_mention = f"<#{ORDER_CHANNEL_ID}>"
    stok_str = f"{current_stock:,}".replace(",", ".")

    layout = discord.ui.LayoutView(timeout=None)
    container = discord.ui.Container()

    if nominal is None:
        status_emote = EMOJI_STOCK_READY if current_stock > 0 else EMOJI_STOCK_EMPTY
        status_text = "READY" if current_stock > 0 else "OUT OF STOCK"
        container.add_item(discord.ui.TextDisplay(
            f"## {EMOJI_STOCK_BOX} STATUS STOK\n"
            f"{status_emote} `{stok_str}` **Robux ({status_text})**"
        ))
        container.add_item(discord.ui.Separator())
        container.add_item(discord.ui.TextDisplay(
            f"### {EMOJI_RATE_TAG} RATE SAAT INI\n"
            "`1` **Robux = Rp 160 (Visend Fast Send)**"
        ))
    else:
        is_ready = current_stock >= nominal
        status_emote = EMOJI_STOCK_READY if is_ready else EMOJI_STOCK_EMPTY
        status_str = (
            f"✅ `READY!` (Sisa stok: `{stok_str}` Robux)" if is_ready
            else f"❌ `STOK TIDAK CUKUP!` (Sisa stok: `{stok_str}` Robux)"
        )
        nominal_str = f"{nominal:,}".replace(",", ".")
        container.add_item(discord.ui.TextDisplay(
            f"## {EMOJI_STOCK_BOX} CEK NOMINAL STOK\n"
            f"### 🎯 NOMINAL DICARI\n"
            f"`{nominal_str}` **Robux**"
        ))
        container.add_item(discord.ui.Separator())
        container.add_item(discord.ui.TextDisplay(
            f"### {EMOJI_STOCK_BOX} KETERSEDIAAN\n"
            f"{status_emote} {status_str}"
        ))

    container.add_item(discord.ui.Separator())
    container.add_item(discord.ui.TextDisplay(f"### 🛒 ORDER\n{order_channel_mention}"))
    container.add_item(discord.ui.Separator())
    container.add_item(discord.ui.TextDisplay(
        f"-# Diminta oleh {ctx.author.name} • {datetime.now(WIB):%d/%m/%Y %H:%M} WIB"
    ))
    layout.add_item(container)

    await ctx.send(view=layout)


@bot.command(name="addstock")
@commands.has_permissions(administrator=True)
async def addstock_command(ctx, jumlah: int = None):
    if jumlah is None or jumlah <= 0:
        await ctx.send("❌ Format salah! Gunakan: `!addstock <jumlah>` (Contoh: `!addstock 5000`)")
        return

    new_stock = update_stock(jumlah, is_set=False)
    await ctx.send(view=build_panel(
        f"{EMOJI_STOCK_BOX} UPDATE STOK ROBUX",
        f"✅ Berhasil menambahkan **+{jumlah:,}** Robux!\n📊 Total stok saat ini: **{new_stock:,}** Robux".replace(",", ".")
    ))


@bot.command(name="removestock", aliases=["minstock", "delstock"])
@commands.has_permissions(administrator=True)
async def removestock_command(ctx, jumlah: int = None):
    if jumlah is None or jumlah <= 0:
        await ctx.send("❌ Format salah! Gunakan: `!removestock <jumlah>` atau `!minstock <jumlah>` (Contoh: `!removestock 200`) ⚠️")
        return

    current_stock = get_stock()
    if jumlah > current_stock:
        await ctx.send(f"❌ Stok tidak cukup! Stok saat ini hanya **{current_stock:,}** Robux. ⚠️".replace(",", "."))
        return

    new_stock = update_stock(jumlah, is_set=False)
    await ctx.send(view=build_panel(
        f"{EMOJI_STOCK_BOX} UPDATE STOK ROBUX (MANUAL)",
        f"📉 Berhasil mengurangi **-{jumlah:,}** Robux (Penjualan Luar/WA)!\n📊 Sisa stok saat ini: **{new_stock:,}** Robux 🚀".replace(",", ".")
    ))


@bot.command(name="setstock")
@commands.has_permissions(administrator=True)
async def setstock_command(ctx, jumlah: int = None):
    if jumlah is None or jumlah < 0:
        await ctx.send("❌ Format salah! Gunakan: `!setstock <jumlah>` (Contoh: `!setstock 10000`)")
        return

    new_stock = update_stock(jumlah, is_set=True)
    await ctx.send(view=build_panel(
        f"{EMOJI_STOCK_BOX} SETTING STOK ROBUX",
        f"{EMOJI_REFRESH} Stok Robux berhasil diatur menjadi **{new_stock:,}** Robux!".replace(",", ".")
    ))


@bot.command(name="officiallink")
async def officiallink_command(ctx):
    embed = discord.Embed(
        description=(
            "**OFFICIAL LINK KENKAISUU STORE**\n"
            "https://discord.gg/e7Axhkx9cQ\n\n"
            "**SALURAN WA KENKAISUU**\n"
            "https://chat.whatsapp.com/DaYp0DuPPST2eSWVuUP2OI?s=cl&p=a&mlu=4"
        ),
        color=0x2b2d31
    )

    await ctx.send(embed=embed)
    try:
        await ctx.message.delete()
    except discord.Forbidden:
        pass


@bot.command(name="middleman")
async def middleman_command(ctx):
    embed = discord.Embed(
        title="LIST BIAYA MIDDLEMAN (FEE)",
        color=0x2b2d31
    )
    embed.add_field(
        name="__For Qris__",
        value=(
            "• `0 - 49K` = **1K**\n"
            "• `50 - 99K` = **2K**\n"
            "• `100 - 149K` = **3K**\n"
            "• `150 - 199K` = **4K**\n"
            "• `200 - 599K` = **5K**\n"
            "• `600K+` = **10K**"
        ),
        inline=False
    )
    embed.add_field(
        name="__Seabank to Seabank__",
        value="• `All Nominal` = **2K**",
        inline=False
    )

    await ctx.send(embed=embed)
    try:
        await ctx.message.delete()
    except discord.Forbidden:
        pass


@bot.command(name="setupstats")
@commands.has_permissions(administrator=True)
async def setupstats_command(ctx):
    file_path = "stats_data.json"
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            data = json.load(f)
    else:
        data = {"total_orders": 0, "total_profit": 0, "buyers": {}}

    msg = await ctx.send(view=build_panel(
        f"{EMOJI_TOP_BUYER} MEMUAT STATISTIK KENKAISUU STORE...",
        "Pesan ini akan otomatis ter-update setiap transaksi selesai. ⏳"
    ))

    data["stats_channel_id"] = ctx.channel.id
    data["stats_msg_id"] = msg.id

    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

    try:
        await ctx.message.delete()
    except discord.Forbidden:
        pass

    await auto_update_stats(bot, ctx.guild)


@bot.command(name="done")
@commands.has_permissions(administrator=True)
async def done_command(ctx, *, harga: str = None):
    if not harga:
        await ctx.send("❌ Format salah! Ketik seperti ini: `!done 16.000` atau `!done Rp 16.000` ")
        return

    channel_id_str = str(ctx.channel.id)

    try:
        with open("active_orders.json", "r") as f:
            active_orders = json.load(f)
    except FileNotFoundError:
        active_orders = {}

    if channel_id_str not in active_orders:
        await ctx.send("❌ Perintah ini hanya bisa digunakan di dalam channel tiket yang masih aktif!")
        return

    order_info = active_orders[channel_id_str]
    if order_info.get("status") == "Success":
        await ctx.send("❌ Order ini sudah pernah ditandai selesai. Statistik tidak dihitung dua kali.")
        return

    clean_price_str = "".join(filter(str.isdigit, harga))
    amount = int(clean_price_str) if clean_price_str else 0
    if amount <= 0:
        await ctx.send("❌ Nominal tidak valid. Contoh: `!done 16.000`")
        return

    log_channel = ctx.guild.get_channel(ORDER_LOG_CHANNEL_ID)
    if not log_channel:
        await ctx.send("❌ Channel Order Log tidak ditemukan!")
        return

    try:
        buyer = ctx.guild.get_member(order_info["buyer_id"]) or await bot.fetch_user(order_info["buyer_id"])
        formatted_price = harga if harga.lower().startswith("rp") else f"Rp {harga}"
        buyer_name = buyer.name if buyer else "Unknown"

        # 1. Hitung statistik DULU dan tandai Success, supaya tidak hilang walau langkah lain gagal
        update_store_stats(user_id=str(order_info["buyer_id"]), username=buyer_name, amount=amount)
        active_orders[channel_id_str]["status"] = "Success"
        with open("active_orders.json", "w") as f:
            json.dump(active_orders, f)

        # 2. Perbarui log order
        log_ok = True
        try:
            buyer_mention = buyer.mention if buyer else f"<@{order_info['buyer_id']}>"
            buyer_avatar = buyer.display_avatar.url if buyer else None
            layout_updated = build_order_log_layout(
                order_info["log_num"], buyer_mention, buyer_avatar, order_info["product"],
                "Success", STATUS_SUCCESS, formatted_price, order_info["category"]
            )
            log_msg = await refresh_order_log(log_channel, order_info["msg_id"], layout_updated)
            active_orders[channel_id_str]["msg_id"] = log_msg.id
            with open("active_orders.json", "w") as f:
                json.dump(active_orders, f)
        except Exception as e:
            log_ok = False
            print(f"Gagal memperbarui log order: {e}")

        # 3. Role pembeli
        role_name = "Verified Buyer"
        buyer_role = discord.utils.get(ctx.guild.roles, name=role_name)
        if not buyer_role:
            try:
                buyer_role = await ctx.guild.create_role(
                    name=role_name,
                    color=discord.Color.blue(),
                    reason="Otomatis dibuat oleh bot untuk pembeli sukses."
                )
            except Exception as e:
                print(f"⚠️ Gagal membuat role otomatis: {e}")
        if buyer and isinstance(buyer, discord.Member) and buyer_role:
            try:
                await buyer.add_roles(buyer_role, reason="Transaksi selesai via !done")
            except Exception as e:
                print(f"⚠️ Gagal memberikan role ke buyer: {e}")

        # 4. Panel statistik (top buyer) langsung ikut ter-update
        stats_ok = True
        try:
            await auto_update_stats(bot, ctx.guild)
        except Exception as e:
            stats_ok = False
            print(f"Gagal memperbarui statistik: {e}")

        body = f"Order log menjadi **Success** {STATUS_SUCCESS}. Role **{role_name}** diberikan. "
        body += "Statistik sudah ter-update! " if stats_ok else "Statistik GAGAL diperbarui (cek console). "
        if not log_ok:
            body += "Log order GAGAL diperbarui. "
        body += EMOJI_SPARKLES
        await ctx.send(view=build_panel(f"{EMOJI_CENTANG} Order Log Diperbarui", body))

    except Exception as e:
        await ctx.send(f"❌ Terjadi kesalahan: {e}")


@bot.command(name="stats")
async def stats_command(ctx):
    data = load_stats_data()
    if not data.get("buyers"):
        await ctx.send("❌ Belum ada data pembeli!")
        return
    layout, file = await build_stats_panel(bot, data, 1)
    await ctx.send(view=layout, file=file)


@bot.command()
async def ping(ctx):
    await ctx.send(view=PingLayout(round(bot.latency * 1000)))


WIB = timezone(timedelta(hours=7))
BULAN_ID = ["Januari", "Februari", "Maret", "April", "Mei", "Juni",
            "Juli", "Agustus", "September", "Oktober", "November", "Desember"]


def calendar_diff(start, end):
    """Selisih tahun, bulan, hari antara dua tanggal (kalender sungguhan, tanpa asumsi 365/30 hari)."""
    y = end.year - start.year
    m = end.month - start.month
    d = end.day - start.day
    if d < 0:
        m -= 1
        pm = end.month - 1 or 12
        py = end.year if end.month > 1 else end.year - 1
        d += calendar.monthrange(py, pm)[1]
    if m < 0:
        y -= 1
        m += 12
    return y, m, d


def roblox_account_age(created_raw: str, now: datetime = None):
    """Mengembalikan (usia_str, tanggal_fmt) untuk akun Roblox, dalam zona WIB."""
    if not created_raw:
        return "Tidak diketahui", "Tidak diketahui"
    created_wib = datetime.fromisoformat(created_raw.replace("Z", "+00:00")).astimezone(WIB)
    now_wib = (now or datetime.now(timezone.utc)).astimezone(WIB)
    y, m, d = calendar_diff(created_wib.date(), now_wib.date())
    usia = f"{y} Tahun {m} Bulan {d} Hari"
    tanggal = (
        f"{created_wib.day} {BULAN_ID[created_wib.month - 1]} {created_wib.year}, "
        f"{created_wib:%H:%M:%S} WIB"
    )
    return usia, tanggal


@bot.command()
async def roblox(ctx, username: str = None):
    if username is None:
        await ctx.send('❌ Harap masukkan username Roblox! Contoh: `!roblox divineakids1`')
        return

    async with aiohttp.ClientSession() as session:
        search_url = "https://users.roblox.com/v1/usernames/users"
        payload = {"usernames": [username], "excludeBannedUsers": False}
        
        async with session.post(search_url, json=payload) as resp:
            data = await resp.json()
            if not data.get("data"):
                await ctx.send(f'❌ Akun Roblox dengan username **{username}** tidak ditemukan!')
                return
            user_id = data["data"][0]["id"]

        async with session.get(f"https://users.roblox.com/v1/users/{user_id}") as resp:
            details = await resp.json()
            
        async with session.get(f"https://friends.roblox.com/v1/users/{user_id}/followers/count") as resp:
            followers = (await resp.json()).get("count", 0)
            
        async with session.get(f"https://friends.roblox.com/v1/users/{user_id}/followings/count") as resp:
            following = (await resp.json()).get("count", 0)

        async with session.get(f"https://friends.roblox.com/v1/users/{user_id}/friends/count") as resp:
            friends = (await resp.json()).get("count", 0)

        async with session.get(f"https://groups.roblox.com/v1/users/{user_id}/groups/roles") as resp:
            groups_data = await resp.json()
            groups_count = len(groups_data.get("data", []))

        thumb_url = f"https://thumbnails.roblox.com/v1/users/avatar?userIds={user_id}&size=352x352&format=Png&isCircular=false"
        async with session.get(thumb_url) as resp:
            thumb_data = await resp.json()
            avatar_url = thumb_data["data"][0]["imageUrl"] if thumb_data.get("data") else None

    name = details.get("name", username)
    display_name = details.get("displayName", name)
    bio = details.get("description", "").strip() or "Pengguna belum mengisi deskripsi."
    is_verified = details.get("hasVerifiedBadge", False)
    status_str = "✅ Verified" if is_verified else "❌ Belum Verified"

    created_raw = details.get("created", "")
    usia_str, created_fmt = roblox_account_age(created_raw)

    profile_url = f"https://www.roblox.com/users/{user_id}/profile"

    layout = discord.ui.LayoutView(timeout=None)
    container = discord.ui.Container()

    head = discord.ui.TextDisplay("## 🎮 Profil Roblox\n📋 **Informasi Akun Roblox**")
    if avatar_url:
        container.add_item(discord.ui.Section(head, accessory=discord.ui.Thumbnail(avatar_url)))
    else:
        container.add_item(head)
    container.add_item(discord.ui.Separator())

    container.add_item(discord.ui.TextDisplay(
        f"#️⃣ **Nama Pengguna:** {name}\n"
        f"🏷️ **Nama Tampilan:** {display_name}\n"
        f"🆔 **ID Pengguna:** `{user_id}`\n"
        f"✅ **Status:** {status_str}"
    ))
    container.add_item(discord.ui.Separator())

    container.add_item(discord.ui.TextDisplay(
        f"👤 **Pengikut:** {followers}  •  🤝 **Teman:** {friends}  •  ➡️ **Mengikuti:** {following}\n"
        f"🏰 **Grup:** {groups_count}  •  🥇 **Lencana:** 0"
    ))
    container.add_item(discord.ui.Separator())

    container.add_item(discord.ui.TextDisplay(
        f"⏳ **Usia Akun:** {usia_str}\n"
        f"📅 **Tanggal Dibuat:** {created_fmt}"
    ))
    container.add_item(discord.ui.Separator())

    container.add_item(discord.ui.TextDisplay(f"📝 **Deskripsi**\n{quote_text(bio)}"))
    container.add_item(discord.ui.Separator())

    container.add_item(discord.ui.TextDisplay(
        f"-# Dibuat oleh {ctx.author.name} • {datetime.now().strftime('%m/%d/%y, %I:%M %p')}"
    ))
    container.add_item(discord.ui.ActionRow(
        discord.ui.Button(label="Buka Profil", url=profile_url, emoji="🎮")
    ))
    layout.add_item(container)

    await ctx.send(view=layout)


@bot.command()
@commands.has_permissions(administrator=True)
async def setuptiket(ctx):
    await ctx.send(view=ProductPanelLayout())
    try:
        await ctx.message.delete()
    except discord.Forbidden:
        pass

# ==========================================
# MENJALANKAN BOT DISCORD
# ==========================================
# Ganti string di bawah dengan Token Bot Discord milikmu
TOKEN = os.getenv('DISCORD_TOKEN', 'TEMPEL_TOKEN_BOT_DISCORD_KAMU_DI_SINI')
bot.run(TOKEN)
