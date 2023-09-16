# Requirements: discord.py 2.x
# 匯入模組
import discord, json, datetime, asyncio
from datetime import timedelta, timezone
from discord.ext import commands, tasks
from discord import app_commands
from discord.ui import Button, Select, View, Modal
from functions import *

# 變數
color = 0x48d1f8
color_running = 0xffa6e6

# 讀取資料
with open("settings.json", "r", encoding="utf8") as f: globaldata = json.load(f)

# 機器人建置
bot = commands.Bot(command_prefix="!", help_command=None, intents = discord.Intents.all())
# CommandTree建置
try: tree = app_commands.CommandTree(bot)
except: tree = bot.tree

# Bot on ready event
@bot.event
async def on_ready():
    print(f"［！］Bot is on ready. Logged as {str(bot.user)}")
    # 同步斜線指令
    autoupdate.start()
    try: 
        await bot.tree.sync()
        print("［！］CommandTree Synced!")
    except: print("［！］Failed to Sync CommandTree")

# 背景執行
@tasks.loop(seconds = globaldata['Looptime'])
async def autoupdate():
    try:
        data = READDATAJSON()
        if len(data['sheet']) != 0:
            start, end = 0, 0
            if len(data['sheet']) <= 3: start, end = 0, 3
            else: start, end = len(data['sheet'])-3, len(data['sheet'])
            for i, s in enumerate(data['sheet'][start:end]):
                if s['open'] == True:
                    # 檢查時間
                    with open("settings.json", "r", encoding="utf8") as f: globaldata = json.load(f)
                    thetime = float(datetime.datetime.strptime(str(s['endtime']), '%Y%m%d%H%M%S').timestamp())
                    timenow = float(datetime.datetime.now().timestamp())
                    # 確認是否時間到
                    if thetime <= timenow:
                        if len(data['sheet']) <= 3: data["sheet"][i]['open'] = False
                        else: data["sheet"][len(data['sheet'])-3+i]['open'] = False
                        if s['notify'] == True:
                            try: await bot.get_channel(globaldata['notifych']).send("🔒飲料訂購表單已關閉填寫")
                            except: pass
            DUMPDATAJSON(data)
    except Exception as e: print(f"［！］Error: {str(e)}")
@autoupdate.before_loop
async def autou_before():
    await bot.wait_until_ready()
    await asyncio.sleep(1)
    print("［！］Loop start!")

# 綁定座號和Discord帳號
@tree.command(name = "bind", description="綁定座號和Discord帳號")
@app_commands.describe(seat_number = "請輸入座號")
async def bind(interaction: discord.Interaction, seat_number:int):
    if seat_number > 0: 
        with open("settings.json", "r", encoding="utf8") as f: globaldata = json.load(f)
        if seat_number <= globaldata['maxpeople']:
            data = READDATAJSON()
            data['seatnum'][str(interaction.user.id)] = int(seat_number)
            DUMPDATAJSON(data)
            await interaction.response.send_message(embed = discord.Embed(color = color).add_field(name = "座號綁定成功", value=f"已綁定座號``{str(seat_number)}``至帳號{str(interaction.user.mention)}").set_footer(text = "請注意: 系統並沒有將座號與姓名對照"), ephemeral=True)
        else: await interaction.response.send_message(content = f"參數錯誤: 座號超過服務器設置的上限({globaldata['maxpeople']})", ephemeral=True)
    else: await interaction.response.send_message(content = "參數錯誤: 座號不得小於0", ephemeral=True)

# 表單管理後臺
@tree.command(name = "sheetcontrol", description="表單控制面板")
@app_commands.checks.has_permissions(administrator = True)
async def sheetcontrol(interaction: discord.Interaction): 
    # 暫存-新建表單-結束時間、是否提醒
    class EndTime_test():
        def __init__(self, endtime): 
            self.endtime = endtime
            self.notify = True
        def edittime(self, time): self.endtime = time
        def editnotify(self, notify:bool): self.notify = notify
    endtime = EndTime_test("")
    # 暫存-編輯表單-被編輯項目
    class EditIndex():
        def __init__(self, editindex): self.editindex = editindex
        def edit(self, i): self.editindex = i
    editindex = EditIndex(-1)
    # 函式區
    # 新建表單_設定結束時間
    class new_settime(Modal, title = "設定表單結束時間"):
        answer = discord.ui.TextInput(label = "格式: 年年年年月月日日時時分分秒秒 | 共14位數 | 時間請使用24時制", style=discord.TextStyle.short, required=True, max_length=14, min_length=14)
        async def on_submit(self, interaction: discord.Interaction):
            try:
                thetime = datetime.datetime.strptime(str(self.answer.value), '%Y%m%d%H%M%S') # 將答案轉換時間格式
                data = READDATAJSON() # 讀取資料
                # 確認最近一筆的表單的開關
                con = True
                if len(data['sheet']) == 0: con = False
                elif data['sheet'][len(data['sheet'])-1]['open'] == False: con = False
                # 如果有表單正在進行
                if con == True: await interaction.response.send_message(content = "無法進行新建表單相關設定: 已有表單正在進行", ephemeral=True)
                # 如果沒有表單正在進行
                else: 
                    embed, view = await new_mainmenu(interaction, self.answer.value)
                    await interaction.response.edit_message(embed = embed)
            except: await interaction.response.send_message(content = '執行錯誤: 請確認是否為正確時間格式!若確認為正確，請聯絡機器人管理者', ephemeral=True)
    async def new_settime_modal(interaction:discord.Interaction): await interaction.response.send_modal(new_settime())
    # 新建表單_主介面
    async def new_mainmenu(interaction: discord.Interaction, endtime2):
        if endtime2 != None: endtime.edittime(endtime2)
        embed = discord.Embed(color = color, title = "表單控制面板", description="目前沒有進行中的表單")
        if endtime.endtime == "": embed.add_field(name = "新建表單", value = f"設定結束時間: ``未設定``\n訊息提醒: {str(endtime.notify)}", inline = False)
        else: embed.add_field(name = "新建表單", value = f"設定結束時間: ``{datetime.datetime.strptime(str(endtime.endtime), '%Y%m%d%H%M%S')}``\n訊息提醒: {str(endtime.notify)}", inline = False)
        embed.set_footer(text = "此面板若5分鐘無操作將會自動失效")

        view = View(timeout = 600)
        button1 = Button(label = "發起表單", style = discord.ButtonStyle.green)
        button1.callback = new_raise
        view.add_item(button1)
        button2 = Button(label = "設定結束時間", style = discord.ButtonStyle.blurple)
        button2.callback = new_settime_modal
        view.add_item(button2)
        if endtime.notify == True: button3 = Button(label = "訊息提醒: 開啟", style = discord.ButtonStyle.green)
        else: button3 = Button(label = "訊息提醒: 關閉", style = discord.ButtonStyle.danger)
        button3.callback = new_notify
        view.add_item(button3)

        return embed, view
    # 新建表單_修改訊息提醒
    async def new_notify(interaction: discord.Interaction):
        try:
            data = READDATAJSON() # 讀取資料
            # 確認最近一筆的表單的開關
            con = True
            if len(data['sheet']) == 0: con = False
            elif data['sheet'][len(data['sheet'])-1]['open'] == False: con = False
            # 如果有表單正在進行
            if con == True: await interaction.response.send_message(content = "無法進行新建表單相關設定: 已有表單正在進行", ephemeral=True)
            # 如果沒有表單正在進行
            else: 
                # 修改訊息提醒選項
                if endtime.notify == True: endtime.editnotify(False)
                else: endtime.editnotify(True)
                embed, view = await new_mainmenu(interaction, None)
                await interaction.response.edit_message(embed = embed, view = view)
        except: await interaction.response.send_message(content = '執行錯誤: 請聯絡機器人管理者', ephemeral=True)
    # 新建表單_發起
    async def new_raise(interaction: discord.Interaction):
        data = READDATAJSON() # 讀取資料
        # 確認最近一筆的表單的開關
        con = True
        if len(data['sheet']) == 0: con = False
        elif data['sheet'][len(data['sheet'])-1]['open'] == False: con = False
        # 如果有表單正在進行
        if con == True: await interaction.response.send_message(content = "無法新建表單: 已有表單正在進行", ephemeral=True)
        # 如果沒有表單正在進行
        else: 
            # 檢查時間
            if endtime.endtime != "":
                with open("settings.json", "r", encoding="utf8") as f: globaldata = json.load(f)
                thetime = float(datetime.datetime.strptime(str(endtime.endtime), '%Y%m%d%H%M%S').timestamp())
                timenow = float(datetime.datetime.now().timestamp())
                if thetime > timenow:
                    # 資料傳入檔案
                    data["sheet"].append({"open":True, "endtime":endtime.endtime, "responses":[], "notify":endtime.notify}) # 表單資料格式+上傳至data.json
                    DUMPDATAJSON(data)
                    embed, view = await edit_mainmenu(interaction)
                    # 訊息提醒
                    if endtime.notify:
                        try: await bot.get_channel(globaldata['notifych']).send("🔥飲料訂購表單開放填寫\n📝使用``/response``指令填寫表單\n🔧查看更多資訊，請使用``/help``指令")
                        except: pass
                    # 訊息傳送
                    await interaction.response.edit_message(embed = embed, view = view)
                else: await interaction.response.send_message(content = "參數錯誤: 結束時間需比現在時間晚", ephemeral=True)
            else: await interaction.response.send_message(content = "參數錯誤: 結束時間尚未設定", ephemeral=True)
    
    # 編輯表單_主介面
    async def edit_mainmenu(interaction: discord.Interaction):
        data = READDATAJSON() # 讀取資料
        editindex.edit(len(data['sheet'])-1)

        embed = discord.Embed(color = color_running, title = "表單控制面板", description="表單填答進行中")
        embed.add_field(name = "表單詳情", value = f"結束時間: ``{datetime.datetime.strptime(str(data['sheet'][editindex.editindex]['endtime']), '%Y%m%d%H%M%S')}``\n已收到回覆數: ``{len(data['sheet'][editindex.editindex]['responses'])}``\n訊息提醒: {data['sheet'][editindex.editindex]['notify']}", inline = False)
        embed.set_footer(text = "此面板若5分鐘無操作將會自動失效")

        view = View(timeout = 600)
        button1 = Button(label = "結束表單", style = discord.ButtonStyle.danger)
        button1.callback = edit_endsheet
        view.add_item(button1)
        button2 = Button(label = "編輯結束時間", style = discord.ButtonStyle.blurple)
        button2.callback = edit_settime_modal
        view.add_item(button2)
        if data['sheet'][editindex.editindex]['notify'] == True: button3 = Button(label = "訊息提醒: 開啟", style = discord.ButtonStyle.green)
        else: button3 = Button(label = "訊息提醒: 關閉", style = discord.ButtonStyle.danger)
        button3.callback = edit_notify
        view.add_item(button3)

        return embed, view
    # 編輯表單_結束表單
    async def edit_endsheet(interaction: discord.Interaction): 
        data = READDATAJSON() # 讀取資料
        if data['sheet'][editindex.editindex]['open'] == True:
            with open("settings.json", "r", encoding="utf8") as f: globaldata = json.load(f)
            tz = timezone(timedelta(hours=globaldata['timezone']))
            timenow = int(str(datetime.datetime.now().astimezone(tz).strftime("%Y%m%d%H%M%S")))

            # 將表單的資料修改為"已關閉"並修改結束時間
            data["sheet"][editindex.editindex]['open'] = False
            data["sheet"][editindex.editindex]['endtime'] = timenow
            DUMPDATAJSON(data)

            # 寄送表單關閉訊息
            if data["sheet"][editindex.editindex]['notify'] == True:
                try: await bot.get_channel(globaldata['notifych']).send("🔒飲料訂購表單已關閉填寫")
                except: pass

            await interaction.response.edit_message(embed = discord.Embed(title = "表單強制結束完成", color = color), view = None)
        else: await interaction.response.send_message(content = "執行錯誤: 表單先前已經結束", ephemeral=True)
    # 編輯表單_修改結束時間
    class edit_settime(Modal, title = "編輯表單結束時間"):
        answer = discord.ui.TextInput(label = "格式: 年年年年月月日日時時分分秒秒 | 共14位數 | 時間請使用24時制", style=discord.TextStyle.short, required=True, max_length=14, min_length=14)
        async def on_submit(self, interaction: discord.Interaction):
            try:
                thetime = datetime.datetime.strptime(str(self.answer.value), '%Y%m%d%H%M%S') # 將答案轉換時間格式
                data = READDATAJSON() # 讀取資料
                if data['sheet'][editindex.editindex]['open'] == True:
                    # 檢查時間
                    with open("settings.json", "r", encoding="utf8") as f: globaldata = json.load(f)
                    thetime = float(datetime.datetime.strptime(str(self.answer.value), '%Y%m%d%H%M%S').timestamp())
                    timenow = float(datetime.datetime.now().timestamp())
                    if thetime > timenow:
                        # 修改結束時間
                        data["sheet"][editindex.editindex]['endtime'] = int(self.answer.value)
                        DUMPDATAJSON(data)
                        embed, view = await edit_mainmenu(interaction)
                        await interaction.response.edit_message(embed = embed, view = view)
                    else: await interaction.response.send_message(content = "參數錯誤: 結束時間需比現在時間晚", ephemeral=True)
                else: await interaction.response.send_message(content = "執行錯誤: 表單先前已經結束", ephemeral=True)
            except: await interaction.response.send_message(content = '執行錯誤: 請確認是否為正確時間格式!若確認為正確，請聯絡機器人管理者', ephemeral=True)
    async def edit_settime_modal(interaction:discord.Interaction): await interaction.response.send_modal(edit_settime())
    # 編輯表單_修改訊息提醒
    async def edit_notify(interaction: discord.Interaction):
        try:
            data = READDATAJSON() # 讀取資料
            if data['sheet'][editindex.editindex]['open'] == True:
                # 修改訊息提醒選項
                if data["sheet"][editindex.editindex]['notify'] == True: data["sheet"][editindex.editindex]['notify'] = False
                else: data["sheet"][editindex.editindex]['notify'] = True
                DUMPDATAJSON(data)
                embed, view = await edit_mainmenu(interaction)
                await interaction.response.edit_message(embed = embed, view = view)
            else: await interaction.response.send_message(content = "執行錯誤: 表單先前已經結束", ephemeral=True)
        except: await interaction.response.send_message(content = '執行錯誤: 若確認為正確，請聯絡機器人管理者', ephemeral=True)

    # 主頁面程式區
    # 讀取資料
    data = READDATAJSON()

    # 確認最近一筆的表單的開關
    con = True
    if len(data['sheet']) == 0: con = False
    elif data['sheet'][len(data['sheet'])-1]['open'] == False: con = False
    # 如果表單是開放的
    if con == True: embed, view = await edit_mainmenu(interaction)
    # 如果表單是關閉的
    else: embed, view = await new_mainmenu(interaction, None)
    
    await interaction.response.send_message(embed = embed, view = view, ephemeral=True)
# sheetcontrol()錯誤處理
@sheetcontrol.error
async def sheetcontrol_error(interaction: discord.Interaction, error):
    if isinstance(error, discord.app_commands.errors.MissingPermissions): await interaction.response.send_message(content="執行錯誤: 你缺失權限``管理者Administrator``", ephemeral=True)
    else: await interaction.response.send_message(content = "執行錯誤: 請聯繫機器人管理者", ephemeral=True)

# 填寫表單
@tree.command(name = "response", description="填寫表單")
async def response(interaction: discord.Interaction):
    data = READDATAJSON() # 讀取資料
    # 暫存-填寫表單-填寫項目
    class Responses():
        def __init__(self, editwhat): 
            self.seatnum = -1
            self.name = None
            self.sugar = None
            self.ice = None
            self.note = None
            self.editwhat = editwhat
        def editseatnum(self, i): self.seatnum = int(i)
        def editname(self, i): self.name = i
        def editsugar(self, i): self.sugar = i
        def editice(self, i): self.ice = i
        def editnote(self, i): self.note = i
    r = Responses(len(data['sheet'])-1)
    # 主介面
    async def mainmenu(interaction: discord.Interaction):
        embed = discord.Embed(color = color_running, title = "填寫飲料訂購表單")
        if r.seatnum != -1: embed.add_field(name = "座號", value=f"{r.seatnum}")
        else: embed.add_field(name = "座號", value="(尚未選擇)")
        if r.name != None: embed.add_field(name = "品項", value=r.name)
        else: embed.add_field(name = "品項", value="(尚未填寫)")
        if r.sugar != None: embed.add_field(name = "甜度", value=r.sugar)
        else: embed.add_field(name = "甜度", value="(尚未選擇)")
        if r.ice != None: embed.add_field(name = "冰塊", value=r.ice)
        else: embed.add_field(name = "冰塊", value="(尚未選擇)")
        if r.note != None: embed.add_field(name = "備註", value=r.note)
        else: embed.add_field(name = "備註", value="(無)")
        embed.set_footer(text = "此面板若5分鐘無操作將會自動失效")

        view = View(timeout = 600)
        sugar = Select(row = 1, placeholder="甜度", max_values=1, options=[discord.SelectOption(label="全糖", value="全糖"), discord.SelectOption(label="少糖", value="少糖"), discord.SelectOption(label="半糖", value="半糖"), discord.SelectOption(label="微糖", value="微糖"), discord.SelectOption(label="無糖", value="無糖")])
        ice = Select(row = 2, placeholder="冰塊", max_values=1, options=[discord.SelectOption(label="正常", value="正常"), discord.SelectOption(label="少冰", value="少冰"), discord.SelectOption(label="半冰", value="半冰"), discord.SelectOption(label="微冰", value="微冰"), discord.SelectOption(label="去冰", value="去冰")])
        seatnum = Button(row = 0, label = "設定座號", style = discord.ButtonStyle.green)
        name = Button(row = 0, label = "設定品項", style = discord.ButtonStyle.blurple)
        note = Button(row = 0, label = "備註", style = discord.ButtonStyle.gray)
        submitit = Button(row = 3, label = "提交", style = discord.ButtonStyle.green)
        sugar.callback = setsugar
        ice.callback = setice
        name.callback = setname_modal
        note.callback = setnote_modal
        seatnum.callback = setseatnum_modal
        submitit.callback = submitans
        view.add_item(sugar)
        view.add_item(ice)
        view.add_item(seatnum)
        view.add_item(name)
        view.add_item(note)
        view.add_item(submitit)

        return embed, view, sugar, ice
    # 設定甜度
    async def setsugar(interaction: discord.Interaction):
        data = READDATAJSON() # 讀取資料
        # 確認表單的開關
        con = True
        if len(data['sheet']) == 0: con = False
        elif data['sheet'][r.editwhat]['open'] == False: con = False
        # 如果表單是開放的
        if con == True:
            # 檢查傳回的值
            if sugar.values[0] == "全糖" or "少糖" or "半糖" or "微糖" or "無糖":
                # 將甜度寫入物件
                r.editsugar(sugar.values[0])
                # 訊息寄送
                embed, view, n1, n2 = await mainmenu(interaction)
                await interaction.response.edit_message(embed = embed)
            else: await interaction.response.send_message(content = "參數錯誤: 傳回非規定的數值", ephemeral=True)
        # 如果表單是關閉的
        else: await interaction.response.send_message(content = "執行錯誤: 目前沒有表單開放", ephemeral=True)
    # 設定冰塊
    async def setice(interaction: discord.Interaction):
        data = READDATAJSON() # 讀取資料
        # 確認表單的開關
        con = True
        if len(data['sheet']) == 0: con = False
        elif data['sheet'][r.editwhat]['open'] == False: con = False
        # 如果表單是開放的
        if con == True:
            # 檢查傳回的值
            if ice.values[0] == "正常" or "少冰" or "半冰" or "微冰" or "去冰":
                # 將冰塊寫入物件
                r.editice(ice.values[0])
                # 訊息寄送
                embed, view, n1, n2 = await mainmenu(interaction)
                await interaction.response.edit_message(embed = embed)
            else: await interaction.response.send_message(content = "參數錯誤: 傳回非規定的數值", ephemeral=True)
        # 如果表單是關閉的
        else: await interaction.response.send_message(content = "執行錯誤: 目前沒有表單開放", ephemeral=True)
    # 設定座號
    class setseatnum(Modal, title = "編輯座號"):
        answer = discord.ui.TextInput(label = "格式: 二位數字", style=discord.TextStyle.short, required=True, max_length=2, min_length=1)
        async def on_submit(self, interaction: discord.Interaction):
            data = READDATAJSON() # 讀取資料
            try:
                # 確認表單的開關
                con = True
                if len(data['sheet']) == 0: con = False
                elif data['sheet'][r.editwhat]['open'] == False: con = False
                # 如果表單是開放的
                if con == True:
                    if len(str(self.answer.value)) > 0:
                        data = READDATAJSON() # 讀取資料
                        int(self.answer.value)

                        # 檢查數字
                        if int(self.answer.value) > 0: 
                            with open("settings.json", "r", encoding="utf8") as f: globaldata = json.load(f)
                            if int(self.answer.value) <= globaldata['maxpeople']:
                                # 寫入資料
                                r.editseatnum(int(self.answer.value))
                                embed, view, n1, n2 = await mainmenu(interaction)
                                await interaction.response.edit_message(embed = embed)
                            else: await interaction.response.send_message(content = f"參數錯誤: 座號超過服務器設置的上限({globaldata['maxpeople']})", ephemeral=True)
                        else: await interaction.response.send_message(content = "參數錯誤: 座號不得小於0", ephemeral=True)
                    else: await interaction.response.send_message(content = "參數錯誤: 收到不符限制的回應", ephemeral=True)
                # 如果表單是關閉的
                else: await interaction.response.send_message(content = "執行錯誤: 目前沒有表單開放", ephemeral=True)
            except: await interaction.response.send_message(content = '執行錯誤: 請確認是否為整數格式!若確認為正確，請聯絡機器人管理者', ephemeral=True)
    async def setseatnum_modal(interaction:discord.Interaction): await interaction.response.send_modal(setseatnum())
    # 設定品項
    class setname(Modal, title = "設定品項"):
        answer = discord.ui.TextInput(label = "請輸入欲訂購的飲料品項(上限15字)", style=discord.TextStyle.short, required=True, max_length=15)
        async def on_submit(self, interaction: discord.Interaction):
            data = READDATAJSON() # 讀取資料
            # 確認表單的開關
            con = True
            if len(data['sheet']) == 0: con = False
            elif data['sheet'][r.editwhat]['open'] == False: con = False
            # 如果表單是開放的
            if con == True:
                if len(str(self.answer.value)) <= 15 and len(str(self.answer.value)) > 0: # 檢查收到的回覆是否正確
                    data = READDATAJSON() # 讀取資料
                    # 寫入資料
                    r.editname(str(self.answer.value))
                    embed, view, n1, n2 = await mainmenu(interaction)
                    await interaction.response.edit_message(embed = embed)
                else: await interaction.response.send_message(content = "參數錯誤: 收到不符限制的回應", ephemeral=True)
            # 如果表單是關閉的
            else: await interaction.response.send_message(content = "執行錯誤: 目前沒有表單開放", ephemeral=True)
    async def setname_modal(interaction:discord.Interaction): await interaction.response.send_modal(setname())
    # 設定備註
    class setnote(Modal, title = "設定備註"):
        answer = discord.ui.TextInput(label = "上限50字，留空可清除備註", style=discord.TextStyle.short, required=False, max_length=50)
        async def on_submit(self, interaction: discord.Interaction):
            data = READDATAJSON() # 讀取資料
            # 確認表單的開關
            con = True
            if len(data['sheet']) == 0: con = False
            elif data['sheet'][r.editwhat]['open'] == False: con = False
            # 如果表單是開放的
            if con == True:
                if len(str(self.answer.value)) <= 50 and len(str(self.answer.value)) > 0: # 檢查收到的回覆是否正確
                    data = READDATAJSON() # 讀取資料
                    # 寫入資料
                    if str(self.answer.value) != "": r.editnote(str(self.answer.value))
                    else: r.editnote(None)
                    embed, view, n1, n2 = await mainmenu(interaction)
                    await interaction.response.edit_message(embed = embed)
                else: await interaction.response.send_message(content = "參數錯誤: 收到不符限制的回應", ephemeral=True)
            # 如果表單是關閉的
            else: await interaction.response.send_message(content = "執行錯誤: 目前沒有表單開放", ephemeral=True)
    async def setnote_modal(interaction:discord.Interaction): await interaction.response.send_modal(setnote())
    # 提交回應
    async def submitans(interaction: discord.Interaction):
        data = READDATAJSON() # 讀取資料
        with open("settings.json", "r", encoding="utf8") as f: globaldata = json.load(f) # 讀取settings.json
        # 確認表單的開關
        con = True
        if len(data['sheet']) == 0: con = False
        elif data['sheet'][r.editwhat]['open'] == False: con = False
        # 如果表單是開放的
        if con == True:
            # 錯誤檢查
            con2 = True
            errmsg = ""
            # 檢查品項
            if r.name == None: 
                con2 = False
                errmsg += "- 品項未填寫\n"
            # 檢查座號
            if r.seatnum == None:
                con2 = False
                errmsg += "- 座號未填寫\n"
            else: 
                try:
                    if int(r.seatnum) <= 0 or int(r.seatnum) > globaldata['maxpeople']:
                        con2 = False
                        errmsg += f"- 座號小於1，或是大於服務器設置的上限({globaldata['maxpeople']})\n"
                except: "- 請確認填入的座號是否為整數\n"
            # 檢查備註
            if r.note != None:
                if len(str(r.note)) > 50: 
                    con2 = False
                    errmsg += "- 收到的備註不符合限制\n"
            # 檢查甜度
            if r.sugar == None:
                con2 = False
                errmsg += "- 甜度未填寫\n"
            else: 
                if str(r.sugar) == "全糖" or r.sugar == "少糖" or r.sugar == "半糖" or r.sugar == "微糖" or r.sugar == "無糖": pass
                else:
                    con2 = False
                    errmsg += "- 收到的甜度為選單選項之外的內容\n"
            # 檢查冰塊
            if r.ice == None:
                con2 = False
                errmsg += "- 冰塊未填寫\n"
            else: 
                if r.ice == "正常" or r.ice == "少冰" or r.ice == "半冰" or r.ice == "微冰" or r.ice == "去冰": pass
                else:
                    con2 = False
                    errmsg += "- 收到的冰塊為選單選項之外的內容\n"
            # 如果檢查通過
            if con2 == True:
                # 取得流水號
                numdata = READNUMBERS()
                # 寫入資料
                redata = {"name": str(r.name), "sugar": str(r.sugar), "ice": str(r.ice), "seatnum": int(r.seatnum), "index":numdata['response']}
                if r.note != None: redata['note'] = str(r.note)
                else: redata['note'] = None

                thedata = READDATAJSON()
                thedata['sheet'][r.editwhat]['responses'].append(redata)
                DUMPDATAJSON(thedata)
                await interaction.response.edit_message(embed = discord.Embed(color = color, title = "已送出回覆").add_field(name = "座號", value = r.seatnum).add_field(name = "品項", value=r.name).add_field(name = "甜度", value=r.sugar).add_field(name = "冰塊", value = r.ice).add_field(name = "備註", value = str(r.note)).set_image(url = "https://cdn.discordapp.com/attachments/1014110583756439643/1122515235987787796/7.gif").add_field(name = "回覆編碼", value = numdata['response']).set_footer(text = f"若要刪除回應，請在表單關閉前執行"), view = None)
            # 如果檢查沒過
            else: await interaction.response.send_message(embed = discord.Embed(color = color, title = "參數錯誤: 錯誤列表如下", description=errmsg), ephemeral = True)
        # 如果表單是關閉的
        else: await interaction.response.send_message(content = "執行錯誤: 目前沒有表單開放", ephemeral=True)
    
    # 主程式區
    # 確認最近一筆的表單的開關
    con = True
    if len(data['sheet']) == 0: con = False
    elif data['sheet'][r.editwhat]['open'] == False: con = False
    # 如果表單是開放的
    if con == True:
        # 取得綁定的座號
        seatn = -1
        try: seatn = int(data['seatnum'][str(interaction.user.id)])
        except: pass
        r.editseatnum(seatn)
        # 訊息寄送
        embed, view, sugar, ice = await mainmenu(interaction)
        await interaction.response.send_message(embed = embed, view = view, ephemeral=True)
    # 如果表單是關閉的
    else: await interaction.response.send_message(content = "執行錯誤: 目前沒有表單開放", ephemeral=True)

# 刪除回應
@tree.command(name = "delresponse", description="刪除回應")
@app_commands.describe(seatnum = "請輸入座號", reindex = "請輸入欲刪除的回應的編碼")
async def delresponse(interaction: discord.Interaction, seatnum:int, reindex: int):
    try:
        # 檢查參數
        if int(seatnum) > 0: 
            if int(reindex) > 0: 
                data = READDATAJSON() # 讀取資料
                
                editwhat = len(data['sheet'])-1
                # 確認最近一筆的表單的開關
                con = True
                if len(data['sheet']) == 0: con = False
                elif data['sheet'][editwhat]['open'] == False: con = False
                # 如果表單是開放的
                if con == True:
                    # 尋找回應編碼對應的回應
                    find = None
                    for d in data['sheet'][editwhat]['responses']:
                        if d['index'] == reindex:
                            find = d
                            break
                    if find == None: await interaction.response.send_message(content="參數錯誤: 表單回應中無此回應編碼", ephemeral=True) # 如果找不到
                    else:
                        # 如果座號可以對應上
                        if find['seatnum'] == seatnum: 
                            theindex = data['sheet'][editwhat]['responses'].index(find)
                            del data['sheet'][editwhat]['responses'][theindex]
                            DUMPDATAJSON(data)
                            await interaction.response.send_message(embed = discord.Embed(title = "回應刪除完成", color = color).add_field(name = "座號", value=seatnum).add_field(name = "回應編碼", value = reindex).add_field(name = "品項/甜度/冰塊", value = f"{find['name']}/{find['sugar']}/{find['ice']}").add_field(name = "備註", value=find['note']).set_footer(text = "若要重新送出回應，請在表單結束前完成"), ephemeral=True)
                        else: await interaction.response.send_message(content = "參數錯誤: 此回應編碼的座號和輸入的不同", ephemeral=True) # 如果座號無法對應上
                # 如果表單是關閉的
                else: await interaction.response.send_message(content = "執行錯誤: 目前沒有表單開放", ephemeral=True)
            else: await interaction.response.send_message(content="參數錯誤: 回應編碼不得小於0", ephemeral=True)
        else: await interaction.response.send_message(content = "參數錯誤: 座號不得小於0", ephemeral=True)
    except: await interaction.response.send_message(content = "執行錯誤: 請聯繫機器人管理者", ephemeral=True)

# 查看所有回應
@tree.command(name = "checkresponse", description="查看最近25筆表單的回應")
async def checkresponse(interaction: discord.Interaction):
    # 查詢指定的表單
    async def sheetcheck(interaction: discord.Interaction):
        data = READDATAJSON() # 讀取資料
        data['sheet'].reverse()
        try:
            thedata = data['sheet'][int(select.values[0])]

            rs = "```\n"
            for i in thedata['responses']: rs += f"| 回覆編{i['index']} | 座號{i['seatnum']} | {i['name']} | {i['sugar']} | {i['ice']} | 備註: {i['note']}\n\n"
            rs += "```"

            if thedata['open'] == True: embed = discord.Embed(color = color, title = "[🔥填答進行中]表單詳細資訊", description=f"將在 {datetime.datetime.strptime(str(s['endtime']), '%Y%m%d%H%M%S')} 結束 | 回覆數: {len(s['responses'])} | 訊息提醒: {s['notify']}").add_field(name = "回覆資料", value = rs)
            else: embed = discord.Embed(title = "[表單已結束]表單詳細資訊", color = color, description=f"已於 {datetime.datetime.strptime(str(s['endtime']), '%Y%m%d%H%M%S')} 結束 | 回覆數: {len(s['responses'])} | 訊息提醒: {s['notify']}").add_field(name = "回覆資料", value = rs)
            await interaction.response.send_message(embed = embed, ephemeral=True)
        except: await interaction.response.send_message(content = "執行錯誤: 請聯繫機器人管理者", ephemeral=True)

    data = READDATAJSON() # 讀取資料
    if len(data['sheet']) != 0: 
        # 回應查詢主程式
        data['sheet'].reverse()
        if len(data['sheet']) <= 25: shdata = data['sheet']
        else: shdata = data['sheet'][:25]
        view = View(timeout = None)
        selectoptions = []
        for i, s in enumerate(shdata):
            if s['open']: selectoptions.append(discord.SelectOption(label = "表單填答進行中", emoji = "🔥", value = i, description=f"結束時間: {datetime.datetime.strptime(str(s['endtime']), '%Y%m%d%H%M%S')} | 回覆數: {len(s['responses'])}"))
            else: selectoptions.append(discord.SelectOption(label = f"表單已結束", value = i, description=f"結束於: {datetime.datetime.strptime(str(s['endtime']), '%Y%m%d%H%M%S')} | 回覆數: {len(s['responses'])}"))
        select = Select(placeholder="請選擇一個表單", options=selectoptions)
        select.callback = sheetcheck
        view.add_item(select)
        await interaction.response.send_message(view = view, embed = discord.Embed(title = "請在下方選單選取一個表單", color = color))
    else: await interaction.response.send_message(embed = discord.Embed(title = "請在下方選單選取一個表單", color = color), view = View().add_item(Select(options=[discord.SelectOption(label="null", value="null")], disabled=True, placeholder="沒有表單可供選擇")))

# 設定表單提醒頻道
@tree.command(name = "setch", description="設定表單的訊息提醒頻道")
@app_commands.describe(channel = "指定提醒訊息出現的頻道")
@app_commands.checks.has_permissions(administrator = True)
async def setch(interaction: discord.Interaction, channel: discord.TextChannel):
    with open("settings.json", "r", encoding="utf8") as f: globaldata = json.load(f)
    globaldata['notifych'] = channel.id
    with open("settings.json", "w", encoding="utf8") as f: json.dump(globaldata, f, ensure_ascii=False)
    await interaction.response.send_message(embed = discord.Embed(title = "提醒訊息頻道設定完成", description=f"表單提醒訊息會被寄送到{channel.mention}", color = color))
# setch()錯誤處理
@setch.error
async def setch_error(interaction: discord.Interaction, error):
    if isinstance(error, discord.app_commands.errors.MissingPermissions): await interaction.response.send_message(content="執行錯誤: 你缺失權限``管理者Administrator``", ephemeral=True)
    else: await interaction.response.send_message(content = "執行錯誤: 請聯繫機器人管理者", ephemeral=True)

# 機器人資訊
@tree.command(name = "help", description="查看機器人相關資訊")
async def help(interaction: discord.Interaction): 
    embed = discord.Embed(title = "點飲料機器人", color = color_running)
    embed.add_field(name = "📜指令說明", value = """``/help`` - 顯示此訊息
``/response`` - 填寫訂飲料表單
``/checkresponse`` - 查看表單收到的回覆
``/delresponse <座號> <回覆編碼>`` - 刪除送出的回覆
``/bind <座號>`` - 將帳號綁定到座號
``/fbk`` - 白上吹雪，最可愛的好狐""", inline = False)
    embed.add_field(name = "🔐管理員指令", value="``/sheetcontrol`` - 表單控制後台\n``/setch`` - 設定表單提醒訊息發送的頻道", inline = False)
    embed.add_field(name = "📢隱私權宣示", value="本機器人僅收集使用者提交的回覆以及座號\n若不願提供這些資訊，請立即停止使用此機器人", inline = False)
    embed.add_field(name = "📢資安宣導", value="使用者在表單提交的座號及表單回覆將會被明碼儲存於服務器\n請勿提交任何私密內容給機器人", inline = False)
    embed.add_field(name = "🕵️保密防諜", value="若有抓耙子要點飲料\n請確保群組資訊不被外洩及群組成員之人身安全", inline = False)
    embed.set_footer(text = "點飲料機器人 | 機器人資訊")
    await interaction.response.send_message(embed = embed)
@bot.command()
async def drink(ctx): await ctx.send("機器人採用斜線指令\n> 使用``/help``指令查看機器人相關資訊")

# 白上吹雪，最可愛的好狐
@tree.command(name = "fbk", description="白上吹雪，最可愛的好狐!")
async def fbk(interaction: discord.Interaction): await interaction.response.send_message(content = "https://tenor.com/view/fox-girl-shirakami-fubuki-fubukishirakami-gif-19974362")

# 啟動機器人
bot.run(globaldata["TOKEN"])