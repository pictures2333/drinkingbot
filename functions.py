# 此區存放程式會使用到的資料格式，以及常用函式

# data.json讀取/寫入
def READDATAJSON(): 
    import json
    with open("data.json", "r", encoding="utf8") as f: return json.load(f)
def DUMPDATAJSON(data: dict): 
    import json
    with open("data.json", "w", encoding="utf8") as f: json.dump(data, f, ensure_ascii=False)

# 讀取numbers.json並遞增號碼
def READNUMBERS():
    import json
    with open("numbers.json", "r", encoding="utf8") as f: data = json.load(f)
    data['response'] += 1
    with open("numbers.json", "w", encoding="utf8") as f: json.dump(data, f, ensure_ascii=False)
    return data