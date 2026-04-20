import firebase_admin
from firebase_admin import credentials, db
import math, time, asyncio, re
from telethon import TelegramClient, events
from colorama import init, Fore, Style

init(autoreset=True)

# --- CONFIG ---
FIREBASE_URL = "https://shmap-8c0fa-default-rtdb.firebaseio.com" 
SERVICE_ACCOUNT_KEY = "service_key.json"
API_ID = 36568275
API_HASH = 'e04616c0b34d10516de9778f8a640a93'
BOT_TOKEN = '8134505444:AAG8Pbe6GqbKqhyR9rYb1kDX_KBlguvNgrU'
SOURCE_CHANNEL = 'odessa_osint26' 

if not firebase_admin._apps:
    try:
        cred = credentials.Certificate(SERVICE_ACCOUNT_KEY)
        firebase_admin.initialize_app(cred, {'databaseURL': FIREBASE_URL})
    except:
        print(Fore.RED + "ПОМИЛКА: Перевір файл service_key.json у папці!")

drones_ref = db.reference('drones')
client = TelegramClient('zerex_session', API_ID, API_HASH)

@client.on(events.NewMessage(chats=SOURCE_CHANNEL))
async def auto_spawn_handler(event):
    text = event.message.message.lower()
    print(Fore.YELLOW + f"[NEWS]: {text[:60]}...")

    target_type = None
    
    # Співставлення з твоїм меню (image_94c1de.png)
    if any(w in text for w in ["238", "jet", "джет"]):
        target_type = "shahed-238-standart" 
    elif any(w in text for w in ["шахед", "136", "герань"]):
        target_type = "shahed-136-standart"   
    elif any(w in text for w in ["гербера", "gerbera"]):
        target_type = "herbera-standart"    
    elif any(w in text for w in ["ракета", "калібр", "х-101", "круїзна"]):
        target_type = "kalibr-standart"     
    elif any(w in text for w in ["fpv", "фпв"]):
        target_type = "fpv-standart"        
    elif any(w in text for w in ["бпла", "розвідник", "орлан"]):
        target_type = "shahed-136-standart" # Запасний варіант

    if target_type:
        angle = 0 
        nums = re.findall(r'\d+', text)
        if nums:
            val = int(nums[0])
            if 0 <= val <= 360: angle = val

        new_target = {
            "lat": 46.48, 
            "lng": 30.72,
            "angle": angle, 
            "type": target_type,
            "dieAt": int((time.time() + 1800) * 1000)
        }
        
        try:
            drones_ref.push(new_target)
            print(Fore.GREEN + Style.BRIGHT + f"[!] ДОДАНО: {target_type} (Курс {angle}°)")
        except Exception as e:
            print(Fore.RED + f"Firebase Error: {e}")

async def engine():
    while True:
        try:
            targets = drones_ref.get()
            if targets:
                updates = {}
                for t_id, data in targets.items():
                    if not isinstance(data, dict) or 'lat' not in data: continue
                    
                    speed = 0.0018 if "kalibr" in data.get('type','') else 0.0007
                    rad = math.radians(data.get('angle', 0) - 90)
                    
                    new_lat = data['lat'] - (math.sin(rad) * speed)
                    new_lng = data['lng'] + (math.cos(rad) * speed)
                    
                    updates[f"{t_id}/lat"] = new_lat
                    updates[f"{t_id}/lng"] = new_lng
                
                if updates:
                    drones_ref.update(updates)
        except: pass
        await asyncio.sleep(2)

async def main():
    await client.start(bot_token=BOT_TOKEN)
    print(Fore.CYAN + Style.BRIGHT + "СИСТЕМА SKY DEFENSE ONLINE.")
    await asyncio.gather(client.run_until_disconnected(), engine())

if __name__ == "__main__":
    asyncio.run(main())