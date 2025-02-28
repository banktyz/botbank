import discord
from discord.ext import commands
import aiohttp
import re
from bs4 import BeautifulSoup

TOKEN = "MTM0NDg4OTgwNjA3NzAzODYwMg.Gp9SlQ.to8gWMe6Nz2Y9I5mCJoCLReyIkTUYJzQ5UzWXE"
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

ALLOWED_USER_IDS = [1255096903184420940]

thai_years = ["2563", "2564", "2565", "2566", "2567"]
years = ["obec63", "obec64", "obec65", "obec66", "obec67"]

async def last_data(resp_text):
    soup = BeautifulSoup(resp_text, 'html.parser')
    input_element = soup.find('input', {'id': lambda x: x and x.startswith('TxStudent')})
    
    if input_element is None:
        return None
    
    data_string = input_element['id']
    data_string = data_string[len("TxStudent ["):-1]
    pairs = re.split(r",\s(?=[a-zA-Z])", data_string)
    data_dict = {}
    for pair in pairs:
        key, value = pair.split("=", 1)
        if value == "null":
            value = None
        elif re.match(r'^\d+(\.\d+)?$', value):
            value = float(value) if '.' in value else int(value)
        elif re.match(r'^.*$', value):
            value = value.strip("[]").split(",")
        data_dict[key] = value
    return data_dict

async def data_all(first_name_th: str = None, last_name_th: str = None):
    all_data = []
    async with aiohttp.ClientSession() as session:
        for thai_year, year in zip(thai_years, years):
            await session.get(f"https://portal.bopp-obec.info/{year}/auth/login")
            await session.post(
                f"https://portal.bopp-obec.info/{year}/auth/j_spring_security_check",
                data={
                    "j_username": "",
                    "j_password": "",
                    "btnSubmit": "เข้าสู่ระบบ",
                },
            )
            params = {
                "educationYear": thai_year,
                "firstNameTh": first_name_th,
                "lastNameTh": last_name_th,
                "action": "search"
            }

            async with session.get(f"https://portal.bopp-obec.info/{year}/student/", params=params) as response:
                if response.status == 200:
                    matches = re.findall(r'href="(/obec(63|64|65|66|67)/student/[^"]+)"', await response.text())
                    if matches:
                        urls = [match[0] for match in matches]
                        for url in urls:
                            async with session.get(f"https://portal.bopp-obec.info{url}") as student:
                                data = await last_data(await student.text())
                                all_data.append(data)

    return all_data

@bot.command(name="dmc1")
async def dmc1(ctx, first_name: str, last_name: str):
    await ctx.send(f"ค้นหาแปปรอก่อน . . . : {first_name} {last_name} 🔎")
    results = await data_all(first_name_th=first_name, last_name_th=last_name)

    if not results:
        await ctx.send(f"ไม่พบข้อมูล : {first_name} {last_name}")
        return

    for data in results:
        embed = discord.Embed(title=f"ข้อมูลของ {first_name} {last_name}", color=0x1D82B6)

        embed.add_field(name="📌 ข้อมูลส่วนตัว", value=f"```\n"
            f"🏫 รหัสโรงเรียน: {data.get('schoolId', '-')}\n"
            f"🎓 รหัสนักเรียน: {data.get('studentId', '-')}\n"
            f"🎂 วันเกิด: {data.get('birthDate', '-')}\n"
            f"🆔 หมายเลขบัตรประชาชน: {data.get('idCard', '-')}\n```", inline=False)

        embed.add_field(name="🏡 ข้อมูลที่อยู่", value=f"```\n"
            f"🏠 บ้านเลขที่: {data.get('houseNumber', '-')}\n"
            f"📍 หมู่: {data.get('village', '-')}\n"
            f"🛣️ ถนน: {data.get('road', '-')}\n"
            f"📌 รหัสตำบล: {data.get('subDistrictCode', '-')}\n"
            f"📌 รหัสอำเภอ: {data.get('districtCode', '-')}\n"
            f"📌 รหัสจังหวัด: {data.get('provinceCode', '-')}\n"
            f"📮 รหัสไปรษณีย์: {data.get('postalCode', '-')}\n"
            f"📞 หมายเลขโทรศัพท์: {data.get('phoneNumber', '-')}\n```", inline=False)

        embed.add_field(name="👨‍👩‍👦 ข้อมูลครอบครัว", value=f"```\n"
            f"🆔 รหัสบัตรประชาชนบิดา: {data.get('fatherIdCard', '-')}\n"
            f"📞 หมายเลขโทรศัพท์บิดา: {data.get('fatherPhone', '-')}\n"
            f"🧑 ชื่อบิดา: {data.get('fatherName', '-')}\n"
            f"👴 นามสกุลบิดา: {data.get('fatherLastName', '-')}\n"
            f"🆔 รหัสบัตรประชาชนมารดา: {data.get('motherIdCard', '-')}\n"
            f"📞 หมายเลขโทรศัพท์มารดา: {data.get('motherPhone', '-')}\n"
            f"👩 ชื่อมารดา: {data.get('motherName', '-')}\n"
            f"👵 นามสกุลมารดา: {data.get('motherLastName', '-')}\n"
            f"🆔 รหัสบัตรประชาชนผู้ปกครอง: {data.get('guardianIdCard', '-')}\n"
            f"🧑‍🏫 ชื่อผู้ปกครอง: {data.get('guardianName', '-')}\n"
            f"🏷️ นามสกุลผู้ปกครอง: {data.get('guardianLastName', '-')}\n```", inline=False)

        await ctx.send(embed=embed)

bot.run(TOKEN)