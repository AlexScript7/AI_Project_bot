import asyncio
import aiosqlite
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bot.database_create import save_program_to_db
from bot.links import links

async def parse_program_page(link, program_name):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    try:
        driver.get(link)
        driver.implicitly_wait(10)
        description_element = driver.find_element(By.XPATH, "//div[@class='post__content']")
        description = description_element.text.strip() if description_element else "Описание не найдено"
        
        await save_program_to_db(program_name, description, link)

    except Exception as e:
        print(f"Ошибка при парсинге {link}: {e}")
    finally:
        driver.quit()

async def parse_all_programs():
    tasks = [parse_program_page(link, program_name) for link, program_name in links]
    await asyncio.gather(*tasks)
