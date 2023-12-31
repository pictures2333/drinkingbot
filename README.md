# 點飲料機器人

一個可以發起表單，統整大家想點什麼飲料的機器人

# 參數說明: settings.json
``TOKEN`` - 機器人的TOKEN

``maxpeople`` - 座號上限，預設為37

``timezone`` - 機器人的時區，預設為8(UTC+8)

``Looptime`` - 機器人背景程式循環運作的頻率(預設為一秒執行一次)

``notifych`` - (勿編輯)表單提醒訊息發送的文字頻道，可使用指令``/setch``設定

# 各檔案說明

``settings.json`` - 機器人設定檔

``numbers.json`` - 程式部分資料編碼流水號儲存的位置

``data.json`` - 表單資料及綁定座號資料儲存的位置

``functions.py`` - 程式使用到的部分函式及資料格式儲存的位置

``main.py`` - 機器人主檔案

# 指令說明

## 一般指令

``/help`` - 顯示此訊息

``/response`` - 填寫訂飲料表單

``/checkresponse`` - 查看表單收到的回覆

``/delresponse <座號> <回覆編碼>`` - 刪除送出的回覆

``/bind <座號>`` - 將帳號綁定到座號

``/fbk`` - 白上吹雪，最可愛的好狐

## 管理員指令

``/sheetcontrol`` - 表單控制後台

``/setch`` - 設定表單提醒訊息發送的頻道

# 隱私權宣示

本機器人僅收集使用者提交的回覆以及座號

若不願提供這些資訊，請立即停止使用此機器人

# 資安宣導

使用者在表單提交的座號及表單回覆將會被明碼儲存於服務器

請勿提交任何私密內容給機器人

# 白上吹雪最可愛了

所以我要在這裡放一張好狐的圖

![image](https://cdn.discordapp.com/attachments/953657638749622373/1122270897978474576/20230625_050327.jpg)

# 操你媽的蘋果汁

當我下一個靶機，從你錢包偷錢出來買酒

