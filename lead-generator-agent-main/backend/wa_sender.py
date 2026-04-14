# WhatsApp Sender — apne PC pe run karo
# pip install playwright && playwright install chromium
import time, urllib.parse
from playwright.sync_api import sync_playwright

LEADS = [
  {
    "name": "Harsh Dental Care & Aesthetic Centre",
    "phone": "+919416407274",
    "message": "Hello Harsh Dental Care & Aesthetic Centre,\n\nHEY "
  },
  {
    "name": "Malhotra Dental & Gynae Care Centre - Dental Clinic in Hisar",
    "phone": "+919416251646",
    "message": "Hello Malhotra Dental & Gynae Care Centre - Dental Clinic in Hisar,\n\nHEY "
  },
  {
    "name": "Dr. Gandhi's Dental Clinic – Best Dentist in Hisar",
    "phone": "+919996627947",
    "message": "Hello Dr. Gandhi's Dental Clinic – Best Dentist in Hisar,\n\nHEY "
  },
  {
    "name": "Sangeet Dental Care & Cosmetic Center , Hisar",
    "phone": "+918607711909",
    "message": "Hello Sangeet Dental Care & Cosmetic Center , Hisar,\n\nHEY "
  },
  {
    "name": "Sumit Dental Clinic",
    "phone": "+919812066526",
    "message": "Hello Sumit Dental Clinic,\n\nHEY "
  }
]

def send():
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context('./wa_session', headless=False)
        page = ctx.new_page()
        page.goto('https://web.whatsapp.com')
        input('WhatsApp mein QR scan karo, phir Enter dabaao...')
        for i, lead in enumerate(LEADS):
            phone = lead['phone'].replace('+','').replace(' ','')
            msg   = urllib.parse.quote(lead['message'])
            page.goto(f'https://web.whatsapp.com/send?phone={phone}&text={msg}')
            page.wait_for_selector('div[contenteditable="true"]', timeout=15000)
            page.keyboard.press('Enter')
            print(f'[{i+1}] Sent to {lead["name"]} ({lead["phone"]})')
            time.sleep(10)
        ctx.close()

send()